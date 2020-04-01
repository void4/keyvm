import pickle

from instructions import *

CELLSIZE = 256
MK_PARENT, MK_CONTROLLER, MK_RESOURCES = range(3)

class Key:
	def __init__(self, value):
		self.value = value
		self.refs = 1#increase on copy, decrease on KeyList delete

	def __str__(self):
		#[%i]" % self.refs
		return "🔑 " + str(self.__class__).split(".")[-1][:-2] + ": " + str(self.value)

	def __repr__(self):
		return str(self)

	def attenuate(self, option=None):
		return self

class PageKey(Key):
	def attenuate(self, option=None):
		if option == A_READ:
			return PageReadKey(self.value)

class PageReadKey(Key):
	pass

# Parent meter, controlling domain, resources
class MeterKey(Key):
	def use(self, amount):
		if self.value[MK_RESOURCES] >= 0 and self.value[MK_RESOURCES] < amount:
			return False
		else:
			self.value[MK_RESOURCES] -= amount
			return True

	def attenuate(self, option):
		if option == 0:
			return self#still return copy?
		else:
			return MeterKey([self, self.value[1], self.value[MK_RESOURCES]//option])

PG_DATA, PG_KEYS = range(2)

class Page:
	def __init__(self, type, parentmeter, size):
		if not parentmeter.use(size):
			raise AssertionError("NOT IMPLEMENTED")
			return None
		self.type = type
		self.meter = parentmeter
		self.data = [None for i in range(size)]

class PageContext:
	def __init__(self, page, option):
		self.page = page
		self.option = option

	def resize(self, size):

		if self.option != A_WRITE:
			raise Exception("No write permissions on page")
			return None

		if not self.page.meter.use(size):
			raise AssertionError("NOT IMPLEMENTED")
			return None

		if size < len(self.page.data):
			self.page.data = self.page.data[:size]
		else:
			self.page.data += [0 for i in range(size-len(self.page.data))]

	def __getitem__(self, key):
		return self.page.data[key]

	def __setitem__(self, key, value):

		if self.option != A_WRITE:
			raise Exception("No write permissions on page")
			return None

		if self.page.type == PG_DATA and isinstance(value, int):
			self.page.data[key] = value
		elif self.page.type == PG_KEYS and isinstance(value, Key):
			self.page.data[key] = value
		else:
			raise ValueError()

	def __repr__(self):
		return str(self.page.data)

	def __len__(self):
		return len(self.page.data)

	def __iter__(self):
		return iter(self.page.data)


class KeyVM:
	def __init__(self, timelimit=-1, memorylimit=-1):
		self.ids = 0
		self.prime_time_meter = MeterKey([None, None, timelimit])
		self.prime_memory_meter = MeterKey([None, None, memorylimit])
		self.pages = {}
		self.active = None#assume single-threaded

	def __repr__(self):
		return f"Time: {self.prime_time_meter.value[2]}\tMemory:{self.prime_memory_meter.value[2]}\tDomain:{len(self.get_page(self.active))}\tPages:{len(self.pages)}"

	def create_id(self):
		#should use dict with globally unique id, in case pages get deleted
		self.ids += 1
		return self.ids

	def create_page(self, type, memory_meter_key, pagesize):
		page = Page(type, memory_meter_key, pagesize)
		pagekey = PageKey(self.create_id())
		self.pages[pagekey.value] = page
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		page = self.pages[pagekey.value]
		if isinstance(pagekey, PageReadKey):
			option = A_READ
		else:
			option = A_WRITE

		page_context = PageContext(page, option)
		return page_context

	def domainkey_from_code(self, code):
		domainkey = self.create_page(PG_KEYS, self.prime_memory_meter, DOMAINFIELDS)
		domainpage = self.get_page(domainkey)

		domainpage[D_SELF] = domainkey

		domainpage[D_STATE] = Key(0)
		domainpage[D_TIME] = self.prime_time_meter
		domainpage[D_MEMORY] = self.prime_memory_meter
		domainpage[D_IP] = Key(0)

		codepagekey = self.create_page(PG_DATA, self.prime_memory_meter, len(code))
		self.copycode(codepagekey, code)
		domainpage[D_CODE] = codepagekey

		domainpage[D_POINTER] = Key(0)

		stackpagekey = self.create_page(PG_DATA, self.prime_memory_meter, 256)
		domainpage[D_STACK] = stackpagekey

		datapagekey = self.create_page(PG_DATA, self.prime_memory_meter, 256)
		domainpage[D_DATA] = datapagekey

		return domainkey

	def copycode(self, codepagekey, code):
		codepage = self.get_page(codepagekey)
		assert len(code) <= len(codepage)
		for i in range(len(code)):
			codepage[i] = code[i]

	def run_code(self, code, debug=False):
		domainkey = self.domainkey_from_code(code)
		self.active = domainkey
		self.run_active()
		return self.image()

	def image(self):
		return pickle.dumps([self.active, self.ids, self.pages])

	def run(self, image):
		self.active, self.ids, self.pages = pickle.loads(image)
		self.run_active()

	def run_active(self, debug=False):

		current = self.active

		while True:#current.associated(self, D_STATE).value == DS_ACTIVE:
			# do a step
			# Ascend the meter chain
			#print(self)
			# TODO investigate this
			if current is None:
				break

			domainpage = self.get_page(current)

			timekey = domainpage[D_TIME]
			chain = [timekey]

			if debug:
				self.viz(current.keylistkey)

			while True:
				parentkey = chain[-1].value[MK_PARENT]
				if parentkey is None:
					break
				chain.append(parentkey)

			#print([str(k) for k in chain])

			STEPCOST = 1
			for meterkey in chain[::-1]:
				if meterkey.value[MK_RESOURCES] <= STEPCOST:
					parentmeterkey = meterkey.value[MK_PARENT]
					if parentmeterkey is None:
						break
					current = parentmeterkey.value[MK_CONTROLLER]
					continue

			for meterkey in chain:
				meterkey.value[MK_RESOURCES] -= STEPCOST


			codepage = self.get_page(domainpage[D_CODE])
			# TODO assert datapage

			ipkey = domainpage[D_IP]
			ip = ipkey.value

			if ip >= len(codepage):
				# TODO move up
				if timekey.value[MK_PARENT] is None:
					break
				continue

			I = codepage[ip]

			stackpage = self.get_page(domainpage[D_STACK])

			pointerkey = domainpage[D_POINTER]
			pointer = pointerkey.value

			datapage = self.get_page(domainpage[D_DATA])

			print(self, INSTRUCTIONNAMES[I])

			reqs = REQUIREMENTS[I]

			jump = False

			def codearg():
				return codepage[ip+1]

			def codeargs(n):
				return codepage[ip+1:ip+1+n]

			def pop():
				if pointerkey.value == 0:
					raise Exception("StackUnderflow")
				value = stackpage[pointerkey.value]
				stackpage[pointerkey.value] = 0
				pointerkey.value -= 1

			def popn(n):
				if pointerkey.value < n:
					raise Exception("StackUnderflow")
				values = []
				for index in range(pointerkey.value-n, pointerkey.value, 1):
					values.append(stackpage[index])
					stackpage[index] = 0
				pointerkey.value -= n
				return values

			def push(v):
				if pointerkey.value + 1 >= len(stackpage):
					raise Exception("StackOverflow")
				stackpage[pointerkey.value] = v
				pointerkey.value += 1


			def pushn():
				pass

			if I == I_PUSH:
				arg = codearg()
				push(arg)

			elif I == I_ADD:
				a,b = popn(2)
				push(a+b)

			elif I == I_SUB:
				a,b = popn(2)
				push(a-b)

			elif I == I_PAGECREATE:
				targetindex, type, meterkeyindex, size = popn(4)
				domainpage[targetindex] = self.create_page(type, domainpage[meterkeyindex], size)

			elif I == I_PAGETYPE:
				sourceindex = pop()
				page = self.get_page(domainpage[sourceindex])
				push(page.type)

			elif I == I_PAGESIZEGET:
				sourceindex = pop()
				page = self.get_page(domainpage[sourceindex])
				push(len(page))

			elif I == I_PAGESIZESET:
				targetindex, size = popn(2)
				page = self.get_page(domainpage[targetindex])
				page.resize(size)

			elif I == I_COPYKEY:
				targetpagekeyindex, targetpageindex, sourcepagekeyindex, sourcepageindex = popn(4)
				sourcepage = self.get_page(domainpage[sourcepagekeyindex])
				key = sourcepage[sourcepageindex]
				targetpage = self.get_page(domainpage[targetpagekeyindex])
				targetpage[targetpageindex] = key

			elif I == I_ATTENUATE:
				targetpagekeyindex, targetpageindex, sourcepagekeyindex, sourcepageindex, type = popn(5)
				sourcepage = self.get_page(domainpage[sourcepagekeyindex])
				key = sourcepage[sourcepageindex]
				targetpage = self.get_page(domainpage[targetpagekeyindex])
				attenuated_key = key.attenuate(type)
				targetpage[targetpageindex] = attenuated_key

			elif I == I_JUMP:
				jumptarget = pop()
				ipkey.value = jumptarget
				jump = True

			elif I == I_JUMPIF:
				jumptarget, condition = popn(2)
				if condition:
					ipkey.value = jumptarget
					jump = True

			print("Stack:", stackpage[:pointerkey.value])

			if not jump:
				ipkey.value += 1 + reqs[R_CARGS]
