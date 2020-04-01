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

DOMAINFIELDS = 10
D_STATE, D_TIME, D_MEMORY, D_IP, D_CODE, D_POINTER, D_STACK, D_DATA, D_WORKBENCH, D_WORKBENCH2 = range(DOMAINFIELDS)
DS_ACTIVE, DS_WAITING = range(2)

class KeyVM:
	def __init__(self, timelimit=-1, memorylimit=-1):
		self.ids = 0
		self.prime_time_meter = MeterKey([None, None, timelimit])
		self.prime_memory_meter = MeterKey([None, None, memorylimit])
		self.pages = {}

	def __repr__(self):
		return f"Time: {self.prime_time_meter.value[2]}\tMemory:{self.prime_memory_meter.value[2]}\tKeylists:{len(self.keylists)}\tDomains:{len(self.domains)}\tPages:{len(self.pages)}"

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

	def domainkey_from_code(code):
		domainkey = vm.create_page(PG_KEYS, vm.prime_memory_meter, DOMAINFIELDS)
		domainpage = vm.get_page(domainkey)

		domainpage[D_STATE] = Key(0)
		domainpage[D_TIME] = time_meter_key
		domainpage[D_MEMORY] = memory_meter_key
		domainpage[D_IP] = Key(0)

		codepagekey = vm.create_page(PG_DATA, vm.prime_memory_meter, len(code))
		self.copycode(codepagekey, code)
		domainpage[D_CODE] = codepagekey

		domainpage[D_POINTER] = Key(0)

		stackpagekey = vm.create_page(PG_DATA, vm.prime_memory_meter, 256)
		domainpage[D_STACK] = stackpagekey

		datapagekey = vm.create_page(PG_DATA, vm.prime_memory_meter, 256)
		domainpage[D_DATA] = datapagekey

		domainpage[D_WORKBENCH] = domainkey
		domainpage[D_WORKBENCH2] = domainkey

		return domainkey

	def copycode(self, codepagekey, code):
		codepage = self.get_page(codepagekey)
		assert len(code) <= len(codepage)
		for i in range(len(code)):
			codepage[i] = code[i]

	def run(self, code, debug=False):
		domainkey = self.domainkey_from_code(code)
		self.run_domainkey(domainkey)

	def run_domainkey(self, domainkey, debug=False):

		while True:#current.associated(self, D_STATE).value == DS_ACTIVE:
			# do a step
			# Ascend the meter chain
			print(self)
			# TODO investigate this
			if current is None:
				break

			keys = self.get_keylist(current.keylistkey)

			timekey = keys[D_TIME]
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


			codepage = self.get_page(keys[D_CODE])
			ipkey = keys[D_IP]
			ip = ipkey.value

			if ip >= len(codepage):
				# TODO move up
				if timekey.value[MK_PARENT] is None:
					break
				continue

			instruction = codepage[ip]

			stackpage = self.get_page(keys[D_STACK])

			pointerkey = keys[D_POINTER]
			pointer = pointerkey.value

			data = self.get_page(keys[D_DATA])

			#print(data.data)

			symbol = SYMBOLS[instruction]
			print(symbol, end="")

			jump = False

					ipkey.value = current.jmpmap[ip]
					jump = True

			elif symbol == "r":
				# root, reset workbench to domain keylistkey
				keys[D_WORKBENCH] = current.keylistkey

			elif symbol == "t":
				# Traverse workbench down
				assert data[pointer] < 16
				key = keys[data[pointer]]
				assert isinstance(key, KeyListKey)
				keys[D_WORKBENCH] = key

			elif symbol == "l":
				# Create new KeyList in workbench
				assert data[pointer] < 16
				newkeylistkey = self.create_keylist()
				wb = self.get_keylist(keys[D_WORKBENCH])
				wb[data[pointer]] = newkeylistkey

			elif symbol == "c":
				# Copy key
				wb1 = self.get_keylist(keys[D_WORKBENCH])
				wb2 = self.get_keylist(keys[D_WORKBENCH2])

				indices = data[pointer]
				wb1i, wb2i = split(indices)
				#print(wb1[wb1i])
				wb2[wb2i] = wb1[wb1i]

				#include attenuate here?
			elif symbol == "d":
				# Make this also a 'm' message?
				# Create new domain
				keylistkey = keys[D_WORKBENCH2]
				wb2 = self.get_keylist(keylistkey)
				domainkey = self.create_domain(wb2[0], wb2[1], wb2[2], keylistkey)
				wb1 = self.get_keylist(keys[D_WORKBENCH])
				wb1[data[pointer]] = domainkey

			elif symbol == "f":
				keys[D_WORKBENCH], keys[D_WORKBENCH2] = keys[D_WORKBENCH2], keys[D_WORKBENCH]

			elif symbol == "a":
				# Attenuate key
				# how to weaken meter key by certain amount? if CELLSIZE=256, this might suck
				# attenuate in place or by copy/transfer?
				# for now, in place
				wb = self.get_keylist(keys[D_WORKBENCH2])
				indices = data[pointer]
				wbi = ((indices >> 4) & 0xf)
				option = (indices & 0xf)

				key = wb[wbi]

				if key is not None:
					wb[wbi] = key.attenuate(option)
				else:
					raise AssertionError("FUCK")

			elif symbol == "m":
				"""send message/key to domain"""
				# use "m" to communicate with system? or separate instruction?
				# system invocations (and their effects) have to obey resource constraints
				# SystemKey? Available anywhere? Like complete memory override? Or only local, relative effects?
				messagekeylistkey = keys[data[pointer]]
				messagekeylist = self.get_keylist(messagekeylistkey)
				domainkey = messagekeylist[0]
				if domainkey is None:
					print("System call")
					pass
				else:
					print(chain[0])
					receiver = self.get_domain(domainkey)

					# use D_WORKBENCH2 as D_INBOX!, also as outbox?
					#		keys[D_INBOX] = vm.create_keylist()
					# Allow sending only one key? or entire workbench? copy or allow access to keylistkey?
					# Allow empty message? -> Empty workbench
					receiverkeys = self.get_keylist(receiver.keylistkey)
					receiverkeys[D_WORKBENCH2] = keys[D_WORKBENCH2]
					print("SENDING")
					current = receiver

			elif symbol == "h":
				"""halt"""
				break

			elif symbol == "p":
				"""create page"""
				# only on empty keyslot?
				slotindex, meterkeyindex = split(data[pointer])
				if keys[slotindex] is None:
					keys[slotindex] = self.create_page(keys[meterkeyindex])
				else:
					#???
					pass
				pass

			if not jump:
				ipkey.value += 1
