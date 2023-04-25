import json
from time import sleep

from instructions import *

from visualizer import start_visualizer
from flask_socketio import SocketIO

CELLSIZE = 256

def noneid(key):
	if key is None:
		return None
	return key.keyid

class VMException(Exception):
	pass

class Key:
	def __init__(self, keyid, comment=None):
		self.keyid = keyid
		self.refs = 0#increase on copy, decrease on KeyList delete
		self.comment = comment

	def __str__(self):
		#[%i]" % self.refs
		return "🔑 " + str(self.__class__).split(".")[-1][:-2] + ": " + str(self.keyid)

	def __repr__(self):
		return str(self)

	def attenuate(self, option=None):
		return self

	def dumps(self):
		return {
			"class": "Key",#self.__class__.__name__,
			"keyid": self.keyid,
			"refs": self.refs,
			"comment": self.comment
		}

	def loads(data):
		key = Key(data["keyid"], comment=data["comment"])
		key.refs = data["refs"]
		return key

	def fixreferences(self, keys):
		pass

class DataKey(Key):
	def __init__(self, keyid, value, *args, **kwargs):
		super().__init__(keyid, *args, **kwargs)
		self.value = value

	def dumps(self):
		return {
			"class": "DataKey",
			"keyid": self.keyid,
			"value": self.value,
			"refs": self.refs,
			"comment": self.comment
		}

	def loads(data):
		key = DataKey(data["keyid"], data["value"], comment=data["comment"])
		key.refs = data["refs"]
		return key

class PageKey(Key):

	def __init__(self, keyid, secret, *args, **kwargs):
		super().__init__(keyid, *args, **kwargs)
		self.secret = secret

	def attenuate(self, vm, option=None):
		if option == A_READ:
			return vm.create_key(PageReadKey, self.secret, comment="Attenuated")

	def dumps(self):
		return {
			"class": "PageKey",#self.__class__.__name__,
			"keyid": self.keyid,
			"secret": self.secret,
			"refs": self.refs,
			"comment": self.comment
		}

	def loads(data):
		key = PageKey(data["keyid"], data["secret"], comment=data["comment"])
		key.refs = data["refs"]
		return key

class PageReadKey(Key):
	pass

# Parent meter, controlling domain, resources
class MeterKey(DataKey):

	def __init__(self, keyid, value, parent, keeper=None, *args, **kwargs):
		super().__init__(keyid, value, *args, **kwargs)
		self.parent = parent
		self.keeper = keeper

	def use(self, amount):
		if self.value >= 0 and self.value < amount:
			return False
		else:
			self.value -= amount
			return True

	def attenuate(self, vm, option):
		if option == 0:
			return self#still return copy?
		else:
			return vm.create_key(MeterKey, self.value//option, self, comment="Attenuated Meter")#XXXBULLSHIT

	def dumps(self):
		return {
			"class": "MeterKey",#"#self.__class__.__name__,
			"keyid": self.keyid,
			"value": self.value,
			"refs": self.refs,
			"parent": self.parent.keyid if self.parent else None,
			"keeper": self.keeper.keyid,
			"comment": self.comment
		}

	def loads(data):
		key = MeterKey(data["keyid"], data["value"], data["parent"], data["keeper"], comment=data["comment"])
		key.refs = data["refs"]
		return key

	def fixreferences(self, keys):
		if self.parent:
			self.parent = keys[self.parent]
		self.keeper = keys[self.keeper]

class SystemKey(DataKey):
	pass

class Page:
	def __init__(self, type, parentmeter, size, comment=None):
		if size != -1 and not parentmeter.use(size):#eh, with size == 0 could spam?
			raise AssertionError("NOT IMPLEMENTED")
			return None
		self.type = type
		self.meter = parentmeter
		self.data = [None for i in range(size)]
		self.comment = comment

	def __iter__(self):
		return iter(self.data)

	def dumps(self):
		return {
			"class": "Page",#self.__class__.__name__,
			"type": self.type,
			"meter": self.meter.keyid,
			"data": self.data if self.type == PG_DATA else [noneid(key) for key in self.data],
			"comment": self.comment
		}
	
	def loads(data):
		page = Page(data["type"], data["meter"], -1, comment=data["comment"])
		page.data = data["data"]
		return page

	def fixreferences(self, keys):
		self.meter = keys[self.meter]
		if self.type == PG_KEYS:
			self.data = [keys[keyid] if keyid else None for keyid in self.data]

class PageContext:
	def __init__(self, vm, page, option):
		self.vm = vm
		self.page = page
		self.option = option

	def resize(self, size):

		if self.option != A_WRITE:
			raise VMException("No write permissions on page")
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
			raise VMException("No write permissions on page")
			return None

		if self.page.type == PG_DATA and isinstance(value, int):
			self.page.data[key] = value
		elif self.page.type == PG_KEYS and isinstance(value, Key):
			if self.page.data[key] is not None:
				self.page.data[key].refs -= 1
				if self.page.data[key].refs <= 0:
					del self.vm.keys[self.page.data[key].keyid]
			value.refs += 1
			self.page.data[key] = value
		else:
			raise ValueError("Invalid write", self.page.type, value)

	def __repr__(self):
		return str(self.page.data)

	def __len__(self):
		return len(self.page.data)

	def __iter__(self):
		return iter(self.page.data)

def loadkey(data):
	if data["class"] in "Key PageKey MeterKey DataKey".split():
		return globals()[data["class"]].loads(data)
	raise Exception("Invalid key class", data["class"])

class KeyVM:
	def __init__(self):
		self.ids = 0
		self.keys = {}
		self.prime_time_meter = self.create_key(MeterKey, -1, None, comment="Prime Time Meter")
		self.prime_memory_meter = self.create_key(MeterKey, -1, None, comment="Prime Memory Meter")
		self.prime_system_key = self.create_key(SystemKey, 0, comment="Prime System Key")
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

	def create_key(self, keyclass, *args, **kwargs):
		key = keyclass(self.create_id(), *args, **kwargs)
		self.keys[key.keyid] = key
		return key

	def create_page(self, type, memory_meter_key, pagesize, comment=None):
		page = Page(type, memory_meter_key, pagesize, comment=comment)
		keycomment = None if comment is None else comment + " Page Key"
		pagekey = self.create_key(PageKey, self.create_id(), comment=keycomment)
		self.pages[pagekey.secret] = page
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		page = self.pages[pagekey.secret]
		if isinstance(pagekey, PageReadKey):
			option = A_READ
		else:
			option = A_WRITE

		page_context = PageContext(self, page, option)
		return page_context

	def domainkey_from_code(self, code, stacksize=None, datasize=None):
		domainkey = self.create_page(PG_KEYS, self.prime_memory_meter, DOMAINFIELDS, comment="Domain")

		self.prime_time_meter.keeper = domainkey
		self.prime_memory_meter.keeper = domainkey

		domainpage = self.get_page(domainkey)

		domainpage[D_SELF] = domainkey

		# TODO DANGER: if not checked datakeys could be misused for value as reference
		domainpage[D_STATE] = self.create_key(DataKey, S_ACTIVE, comment="D_STATE")
		domainpage[D_TIME] = self.prime_time_meter
		domainpage[D_MEMORY] = self.prime_memory_meter
		domainpage[D_IP] = self.create_key(DataKey, 0, comment="D_IP")

		codepagekey = self.create_page(PG_DATA, self.prime_memory_meter, len(code), comment="Code")
		self.copycode(codepagekey, code)
		domainpage[D_CODE] = codepagekey

		domainpage[D_POINTER] = self.create_key(DataKey, 0, comment="Stack Pointer")

		stackpagekey = self.create_page(PG_DATA, self.prime_memory_meter, stacksize if stacksize else 256, comment="Stack")
		domainpage[D_STACK] = stackpagekey

		datapagekey = self.create_page(PG_DATA, self.prime_memory_meter, datasize if datasize else 256, comment="Data")
		domainpage[D_DATA] = datapagekey

		# First domain receives prime system key
		domainpage[D_RECV] = self.prime_system_key

		return domainkey

	def copycode(self, codepagekey, code):
		codepage = self.get_page(codepagekey)
		assert len(code) <= len(codepage)
		for i in range(len(code)):
			codepage[i] = code[i]

	def run_code(self, code, timelimit=None, memorylimit=None, stacksize=None, datasize=None, debug=False, opendebugger=False, debugsleep=None):

		if timelimit is not None:
			self.prime_time_meter.value = timelimit

		if memorylimit is not None:
			self.prime_memory_meter.value = memorylimit

		domainkey = self.domainkey_from_code(code, stacksize=stacksize, datasize=datasize)
		self.active = domainkey
		self.run_active(debug=debug, opendebugger=opendebugger, debugsleep=debugsleep)
		return self.image()

	def image(self):
		# Spec: Must be guaranteed to be JSON-serializable
		jdata = {
			"active": self.active.keyid,
			"ids": self.ids,
			"keys": {keyid: key.dumps() for keyid, key in self.keys.items()},
			"pages": {pageid: page.dumps() for pageid, page in self.pages.items()},
			"prime_memory_meter": self.prime_memory_meter.keyid,
			"prime_time_meter": self.prime_time_meter.keyid,
			"prime_system_key": self.prime_system_key.keyid,
		}
		return jdata

	def run(self, image, timelimit=None, memorylimit=None, debug=False, opendebugger=False, debugsleep=None):
		jdata = image
		keys = jdata["keys"]
		pages = jdata["pages"]
		self.keys = {int(keyid):loadkey(keydump) for keyid, keydump in keys.items()}
		self.pages = {int(pageid):Page.loads(pagedump) for pageid, pagedump in pages.items()}

		for key in self.keys.values():
			key.fixreferences(self.keys)

		for page in self.pages.values():
			page.fixreferences(self.keys)

		self.active = self.keys[jdata["active"]]
		self.ids = jdata["ids"]

		self.prime_time_meter = self.keys[jdata["prime_time_meter"]]
		self.prime_memory_meter = self.keys[jdata["prime_memory_meter"]]
		self.prime_system_key = self.keys[jdata["prime_system_key"]]

		if timelimit is not None:
			self.prime_time_meter.value = timelimit

		if memorylimit is not None:
			self.prime_memory_meter.value = memorylimit

		self.run_active(debug=debug, opendebugger=opendebugger, debugsleep=debugsleep)
		return self.image()

	def system_call(key):
		# TODO must return key of some sort
		pass

	def setorcreate(self, pagecontext, index, value, comment=None):
		if pagecontext[index] is None or not isinstance(pagecontext[index], DataKey):
			pagecontext[index] = self.create_key(DataKey, value, comment=comment)
		else:
			pagecontext[index].value = value
	def run_active(self, debug=False, opendebugger=False, debugsleep=None):

		sio = None
		if debug:
			if opendebugger:
				start_visualizer()
				sio = SocketIO(message_queue="redis://127.0.0.1:6379/0", use_reloader=False, debug=False)
				sio.emit('broadcast', {'message': "{'status': 'VM connected'}"})

		current = self.active

		while True:#current.associated(self, D_STATE).value == S_ACTIVE:
			# do a step
			# Ascend the meter chain
			print(self)
			# TODO investigate this
			if current is None:
				break

			# TODO what if this fails?
			domainpage = self.get_page(current)

			self.setorcreate(domainpage, D_STATE, S_ACTIVE)

			try:
				timekey = domainpage[D_TIME]
				chain = [timekey]

				if debug:
					self.viz(sio, opendebugger, debugsleep)

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

				#print(str(self) + f"\tIP:{ip}\tINSTR:{INSTRUCTIONNAMES[I]}\tPNT:{pointer}")

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
					a,b = popn(2)
					if b == 0:
						raise VMException("DivisionByZero")
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

				elif I == I_CREATEPAGE:
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
					attenuated_key = key.attenuate(self, type)
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
					if isinstance(targetdomainkey, SystemKey):
						domainpage[D_RECV] = system_call(domainpage[transferkeyindex])
					else:
						targetdomain = self.get_page(targetdomainkey)
						self.setorcreate(domainpage, D_STATE, S_ACTIVE)
						transferkey = domainpage[transferkeyindex]
						targetdomain[D_RECV] = transferkey
						# check if targetdomain is keypage!
						self.active = targetdomainkey
						current = self.active

				elif I == I_PAGEREAD:
					sourcepagekeyindex, sourcepageindex = popn(2)
					sourcepage = self.get_page(domainpage[sourcepagekeyindex])
					if sourcepage.type != PG_DATA:
						raise VMException("Trying to read from non-data page")
						# XXX just skip?

					push(sourcepage[sourcepageindex])

				elif I == I_PAGEWRITE:
					data, targetpagekeyindex, targetpageindex = popn(3)
					targetpage = self.get_page(domainpage[targetpagekeyindex])
					if targetpage.type != PG_DATA:
						raise VMException("Trying to write to non-data page")
						# XXX just skip?
					targetpage[targetpageindex] = data

				#print("Stack:", stackpage[:pointerkey.value])

				if not jump:
					ipkey.value += 1 + reqs[R_CARGS]

			except VMException as e:
				print(e)
				# XXX make sure this domainpage is actually the most recent one
				self.setorcreate(domainpage, D_STATE, S_ERROR)

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

	def viz(self, sio, opendebugger=False, debugsleep=None):

		if opendebugger:
			image = self.image()

			for page in image["pages"].values():
				if page["type"] == PG_KEYS and page["comment"] == "Domain":
					pageid = image["keys"][page["data"][D_CODE]]["secret"]
					codepage = image["pages"][pageid]
					ipvalue = image["keys"][page["data"][D_IP]]["value"]
					codepage["ip"] = ipvalue

			for page in image["pages"].values():
				if page["type"] == PG_DATA and page["comment"] == "Code":
					page["disasm"] = self.disassemble(page)


			sio.emit('broadcast', {'type': 'update', 'message': {'image': json.dumps(image)}})

		if debugsleep:
			sleep(debugsleep)

	def disassemble(self, codepage):
		i = 0
		result = []
		while i < len(codepage["data"]):
			opcode = codepage["data"][i]
			numargs = REQUIREMENTS[opcode][0]
			opinfo = {"op": INSTRUCTIONNAMES[opcode]}
			if numargs > 0:
				opinfo["args"] = codepage["data"][i+1:i+1+numargs]

			if "ip" in codepage and codepage["ip"] == i:
				opinfo["active"] = True

			result.append(opinfo)
			i += 1 + numargs#skip args
		return result