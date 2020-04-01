import pickle

from instructions import *

CELLSIZE = 256

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

	def __init__(self, value, parent, keeper=None):
		self.value = value
		self.parent = parent
		self.keeper = keeper
		self.refs = 1

	def use(self, amount):
		if self.value >= 0 and self.value < amount:
			return False
		else:
			self.value -= amount
			return True

	def attenuate(self, option):
		if option == 0:
			return self#still return copy?
		else:
			return MeterKey(self.value//option, self)

class Page:
	def __init__(self, type, parentmeter, size):
		if not parentmeter.use(size):
			raise AssertionError("NOT IMPLEMENTED")
			return None
		self.type = type
		self.meter = parentmeter
		self.data = [None for i in range(size)]

	def __iter__(self):
		return iter(self.data)

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

class VMException(Exception):
	pass

class KeyVM:
	def __init__(self):
		self.ids = 0
		self.prime_time_meter = MeterKey(-1, None)
		self.prime_memory_meter = MeterKey(-1, None)
		self.pages = {}
		self.active = None#assume single-threaded

	def __repr__(self):
		keypages = 0
		datapages = 0
		keys = 0
		for pageid, page in self.pages.items():
			if page.type == PG_KEYS:
				keypages += 1
				for field in page:
					if field is not None:
						keys += 1
			else:
				datapages += 1
		a = f"Time: {self.prime_time_meter.value}\tMemory:{self.prime_memory_meter.value}\t"
		#b =	f"Domain:{len(self.get_page(self.active))}\tPages:{len(self.pages)}\t"
		c =	f"DataPages:{datapages}\tKeyPages:{keypages}\tKeys:{keys}"

		return a+c

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

		self.prime_time_meter.keeper = domainkey
		self.prime_memory_meter.keeper = domainkey

		domainpage = self.get_page(domainkey)

		domainpage[D_SELF] = domainkey

		domainpage[D_STATE] = Key(S_ACTIVE)
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

	def run_code(self, code, timelimit=None, memorylimit=None, debug=False):

		if timelimit is not None:
			self.prime_time_meter.value = timelimit

		if memorylimit is not None:
			self.prime_memory_meter.value = memorylimit

		domainkey = self.domainkey_from_code(code)
		self.active = domainkey
		self.run_active()
		return self.image()

	def image(self):
		return pickle.dumps([self.active, self.ids, self.pages, self.prime_memory_meter, self.prime_time_meter])

	def run(self, image, timelimit=None, memorylimit=None):

		self.active, self.ids, self.pages, self.prime_memory_meter, self.prime_time_meter = pickle.loads(image)

		if timelimit is not None:
			self.prime_time_meter.value = timelimit

		if memorylimit is not None:
			self.prime_memory_meter.value = memorylimit

		self.run_active()
		return self.image()

	def run_active(self, debug=False):

		current = self.active

		while True:#current.associated(self, D_STATE).value == S_ACTIVE:
			# do a step
			# Ascend the meter chain
			#print(self)
			# TODO investigate this
			if current is None:
				break

			# TODO what if this fails?
			domainpage = self.get_page(current)
			domainpage[D_STATE] = Key(S_ACTIVE)

			try:
				timekey = domainpage[D_TIME]
				chain = [timekey]

				if debug:
					self.viz(current.keylistkey)

				while True:
					parentkey = chain[-1].parent
					if parentkey is None:
						break
					chain.append(parentkey)

				#print([str(k) for k in chain])
				#print(chain)
				EXIT_VM = False
				STEPCOST = 1
				for meterkey in chain[::-1]:
					if meterkey.value <= STEPCOST:
						parentmeterkey = meterkey.parent
						if parentmeterkey is None:
							EXIT_VM = True
							break
						current = parentmeterkey.keeper
						continue

				if EXIT_VM:
					break

				for meterkey in chain:
					meterkey.value -= STEPCOST


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

				print(self, ip, INSTRUCTIONNAMES[I], pointer)

				reqs = REQUIREMENTS[I]

				jump = False

				def codearg():
					return codepage[ip+1]

				def codeargs(n):
					return codepage[ip+1:ip+1+n]

				def pop():
					if pointerkey.value == 0:
						raise VMException("StackUnderflow")
					value = stackpage[pointerkey.value-1]
					stackpage[pointerkey.value-1] = 0
					pointerkey.value -= 1
					return value

				def popn(n):
					if pointerkey.value < n:
						raise VMException("StackUnderflow")
					values = []
					for index in range(pointerkey.value-n, pointerkey.value, 1):
						values.append(stackpage[index])
						stackpage[index] = 0
					pointerkey.value -= n
					return values

				def push(v):
					if pointerkey.value + 1 >= len(stackpage):
						raise VMException("StackOverflow")
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

				elif I == I_MUL:
					a,b = popn(2)
					push(a*b)

				elif I == I_DIV:
					a,b = popn(2)
					if b == 0:
						raise VMException("DivisionByZero")
					push(a//b)

				elif I == I_MOD:
					if b == 0:
						raise VMException("DivisionByZero")
					a,b = popn(2)
					push(a%b)

				elif I == I_AND:
					a,b = popn(2)
					push(a&b)

				elif I == I_OR:
					a,b = popn(2)
					push(a|b)

				elif I == I_XOR:
					a,b = popn(2)
					push(a^b)

				elif I == I_NOT:
					a = pop()
					push(~a)

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

				elif I == I_CALL:
					targetdomainkeyindex, transferkeyindex = popn(2)
					targetdomainkey = domainpage[domainkeyindex]
					targetdomain = self.get_page(targetdomainkey)
					transferkey = domainpage[transferkeyindex]
					targetdomain[D_STATE] = Key(S_ACTIVE)
					targetdomain[D_RECV] = transferkey
					# check if targetdomain is keypage!
					self.active = targetdomainkey
					current = self.active

				#print("Stack:", stackpage[:pointerkey.value])

				if not jump:
					ipkey.value += 1 + reqs[R_CARGS]

			except VMException as e:
				print(e)
				# XXX make sure this domainpage is actually the most recent one
				domainpage[D_STATE] = Key(S_ERROR)

				timekey = domainpage[D_TIME]

				EXIT_VM = False

				# check domain repair key
				# ensure control returns to caller or meter parent
				while True:

					if timekey.keeper is not None:
						keeper = self.get_page(timekey.keeper)

						if keeper[D_STATE].value != S_ERROR:
							self.active = timekey.keeper
							current = self.active
							break

					if timekey.parent is None:
						EXIT_VM = True
						break

					timekey = timekey.parent

				if EXIT_VM:
					break
