CELLSIZE = 256
KEYLISTLEN = 16

class KeyList:
	def __init__(self):
		self.data = [None for i in range(KEYLISTLEN)]

	def __setitem__(self, key, value):
		assert isinstance(value, Key)
		self.data[key] = value

	def __getitem__(self, key):
		return self.data[key]

class Key:
	def __init__(self, value):
		self.value = value

class PageKey(Key):
	pass

class DomainKey(Key):
	pass

class KeyListKey(Key):
	pass

# Parent meter, controlling domain, resources
class MeterKey(Key):
	pass

MK_PARENT, MK_CONTROLLER, MK_RESOURCES = range(3)

PAGESIZE = 256

class Page:
	def __init__(self, parentmeter):
		self.meter = parentmeter
		self.data = [0 for i in range(PAGESIZE)]

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		self.data[key] = value

	def __len__(self):
		return len(self.data)

DK_STATE, DK_TIME, DK_IP, DK_CODE, DK_POINTER, DK_DATA = range(6)
DS_ACTIVE, DS_WAITING = range(2)

class Domain:
	def __init__(self, kf, time_meter_key, codepagekey, datapagekey):
		self.keylistkey = kf.create_keylist()#masterkey

		keys = kf.get_keylist(self.keylistkey)
		keys[DK_STATE] = Key(0)#STATE
		keys[DK_TIME] = time_meter_key
		keys[DK_IP] = Key(0)#IP
		keys[DK_CODE] = codepagekey
		keys[DK_POINTER] = Key(0)#POINTER
		keys[DK_DATA] = datapagekey

		# Assume immutable code? Or update on codepagekey change
		codepage = kf.get_page(codepagekey)

		self.jmpmap = {}
		jmplst = []
		for ci, cd in enumerate(codepage):
			c = SYMBOLS[cd]
			if c == "[":
				jmplst.append(ci)
			elif c == "]":
				if len(jmplst) == 0:
					break
				matching = jmplst.pop(-1)
				self.jmpmap[ci] = matching
				self.jmpmap[matching] = ci + 1

	def associated(self, kf, keyindex):
		keys = kf.get_keylist(self.keylistkey)
		return keys[keyindex]

class KeyFuck:
	def __init__(self):
		self.ids = 0
		self.keylists = {}
		self.domains = {}
		self.pages = {}
		self.prime_time_meter = MeterKey([None, None, -1])
		self.prime_memory_meter = MeterKey([None, None, -1])

	def create_id(self):
		#should use dict with globally unique id, in case pages get deleted
		self.ids += 1
		return self.ids

	def create_keylist(self):
		keylist = KeyList()
		keylistkey = KeyListKey(self.create_id())
		self.keylists[keylistkey.value] = keylist
		return keylistkey

	def get_keylist(self, keylistkey):
		assert isinstance(keylistkey, KeyListKey)
		return self.keylists[keylistkey.value]

	def create_page(self, memory_meter_key):
		page = Page(memory_meter_key)
		pagekey = PageKey(self.create_id())
		self.pages[pagekey.value] = page
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		return self.pages[pagekey.value]

	def create_domain(self, time_meter_key, memory_meter_key, code=None):
		codepagekey = self.create_page(memory_meter_key)
		datapagekey = self.create_page(memory_meter_key)

		if code is not None:
			codepage = self.get_page(codepagekey)
			assert len(code) <= len(codepage)
			for i in range(len(code)):
				codepage[i] = code[i]

		domain = Domain(self, time_meter_key, codepagekey, datapagekey)
		domainkey = DomainKey(self.create_id())
		self.domains[domainkey.value] = domain

		return domainkey

	def get_domain(self, domainkey):
		assert isinstance(domainkey, DomainKey)
		return self.domains[domainkey.value]

	def run(self, domainkey):

		current = self.get_domain(domainkey)

		keys = self.get_keylist(current.keylistkey)

		while current.associated(self, DK_STATE).value == DS_ACTIVE:
			# do a step
			timekey = keys[DK_TIME]
			if timekey.value[MK_RESOURCES] <= 0 and timekey.value[MK_PARENT] is not None:
				current = timekey.value[MK_PARENT]
				continue

			timekey.value[MK_RESOURCES] -= 1

			code = self.get_page(keys[DK_CODE])
			ipkey = keys[DK_IP]
			ip = ipkey.value

			if ip >= len(code):
				# TODO move up
				break
			instruction = code[ip]

			pointerkey = keys[DK_POINTER]
			pointer = pointerkey.value

			data = self.get_page(keys[DK_DATA])

			symbol = SYMBOLS[instruction]
			print(symbol)

			jump = False

			if symbol == ">":
				pointerkey.value = (pointer+1)%PAGESIZE
			elif symbol == "<":
				pointerkey.value = (pointer-1)%PAGESIZE
			elif symbol == "+":
				data[pointer] = (data[pointer]+1)%CELLSIZE
			elif symbol == "-":
				data[pointer] = (data[pointer]-1)%CELLSIZE
			elif symbol == "[":
				if data[pointer] == 0:
					#if ip in current.jmpmap:
					#try: except KeyError
					ipkey.value = current.jmpmap[ip]
					jump = True
			elif symbol == "]":
				if data[pointer] != 0:
					ipkey.value = current.jmpmap[ip]
					jump = True

			elif symbol == "m":
				# use "m" to communicate with system? or separate instruction?
				# system invocations (and their effects) have to obey resource constraints
				# SystemKey? Available anywhere? Like complete memory override? Or only local, relative effects?
				messagekeylistkey = keys[data[pointer]]
				messagekeylist = self.get_keys(messagekeylistkey)
				domainkey = messagekeylist[0]
				if domainkey is None:
					# System call
					pass
				else:
					current = self.get_domain(domainkey)

			if not jump:
				ipkey.value += 1

from random import choice

SYMBOLS = "><+-[]"

def translate(code):
	return [SYMBOLS.index(c) for c in code]

def genrandom(length=256):
	code = ""
	for i in range(length):
		code += choice(SYMBOLS)
	return code

def genstatic():
	return "+>++[-]<+"

kf = KeyFuck()
domainkey = kf.create_domain(kf.prime_time_meter, kf.prime_memory_meter, translate(genstatic()))
kf.run(domainkey)
datapagekey = kf.get_domain(domainkey).associated(kf, DK_DATA)
data = kf.get_page(datapagekey).data
print(data)
