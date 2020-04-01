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
	pass

class PageReadKey(Key):
	pass

class DomainKey(Key):
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
			return self
		else:
			return MeterKey([self, self.value[1], self.value[MK_RESOURCES]//option])

PG_DATA, PG_KEYS = range(2)

class Page:
	def __init__(self, type, parentmeter, pagesize):
		self.type = type
		self.meter = parentmeter
		self.data = [0 for i in range(pagesize)]

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		#TODO Check if writer has PageKey (not PageReadKey)
		#Create something like PageContext?
		#Cache it?
		if self.type == PG_DATA:
			if isinstance(value, int):
				self.data[key] = value
		elif self.type == PG_KEYS:
			if isinstance(value, Key):
				self.data[key] = value


	def read(self, key, value):
		self[key] = value

	def __len__(self):
		return len(self.data)

	def __iter__(self):
		return iter(self.data)

DOMAINFIELDS = 8
D_STATE, D_TIME, D_MEMORY, D_IP, D_CODE, D_POINTER, D_STACK, D_DATA = range(DOMAINFIELDS)
DS_ACTIVE, DS_WAITING = range(2)#ommit these? global active index in image?

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
		if not memory_meter_key.use(pagesize):
			raise AssertionError("NOT IMPLEMENTED")
			return None
		page = Page(type, memory_meter_key, pagesize)
		pagekey = PageKey(self.create_id())
		self.pages[pagekey.value] = page
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		return self.pages[pagekey.value]

	def domainkey_from_code(self, code):
		domainkey = self.create_page(PG_KEYS, self.prime_memory_meter, DOMAINFIELDS)
		domainpage = self.get_page(domainkey)

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

			#print(data.data)

			print(self, INSTRUCTIONNAMES[I])

			reqs = REQUIREMENTS[I]

			jump = False

			#		ipkey.value =
			#		jump = True
			"""
			extend/change page size
			getkey domainpage[targetindex] <- domainpage[keyindex]:keylistkey[secondaryindex]
			putkey reverse of ^

			pagecreate
			pagetype: domainpage[keyindex] -> stack.push(page.type)
			pagesize: domainpage[keyindex] -> stack.push(len(page))

			"""

			def codearg():
				return codepage[ip+1]

			def codeargs(n):
				return codepage[ip+1:ip+1+n]

			def pop():
				if pointerkey.value == 0:
					raise Exception("StackUnderflow")
				value = stackpage[pointerkey.value]
				pointerkey.value -= 1

			def popn(n):
				pass

			def push():
				if pointerkey.value + 1 > len(stackpage):
					raise Exception("StackOverflow")
				value = stackpage[pointerkey.value]
				pointerkey.value -= 1


			def pushn():
				pass

			if I == I_PUSH:
				arg = codearg()



			if not jump:
				ipkey.value += 1 + reqs[R_CARGS]
