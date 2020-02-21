CELLSIZE = 256
KEYLISTLEN = 16

class KeyList:
	def __init__(self):
		self.data = [None for i in range(KEYLISTLEN)]

	def __setitem__(self, key, value):
		assert isinstance(value, Key)
		if self.data[key] is not None:
			del self.data[key]
		self.data[key] = value

	def __getitem__(self, key):
		return self.data[key]

	def __delitem__(self, key):
		self.data[key].refs -= 1
		self.data[key] = None

	def __iter__(self):
		return iter(self.data)

class Key:
	def __init__(self, value):
		self.value = value
		self.refs = 1#increase on copy, decrease on KeyList delete

	def __str__(self):
		#[%i]" % self.refs
		return "🔑 " + str(self.__class__).split(".")[-1][:-2] + ": " + str(self.value)

	def attenuate(self, option=None):
		return self

class PageKey(Key):
	pass

class DomainKey(Key):
	pass

class KeyListKey(Key):
	# def __setattr__(self, name, value):
	#	if name == "refs":
	# delete corresponding keylist? or really only if meter is deleted?
	# -> keylist could reference itself, so prob yeah, since only meters are guaranteed to be hierarchical
	# should meter key grant access to everything?
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

MK_PARENT, MK_CONTROLLER, MK_RESOURCES = range(3)

PAGESIZE = 16

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

DK_STATE, DK_TIME, DK_IP, DK_CODE, DK_POINTER, DK_DATA, DK_WORKBENCH, DK_WORKBENCH2 = range(8)
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
		keys[DK_WORKBENCH] = self.keylistkey
		keys[DK_WORKBENCH2] = self.keylistkey

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
		if not memory_meter_key.use(PAGESIZE):
			return None
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

		#TODO if codepagekey is None or datapagekey is None, revert

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

	def viz(self, keylistkey, depth=0, visited=None):
		if visited is None:
			visited = [keylistkey]
		keylist = self.get_keylist(keylistkey)
		prefix = "\t"*depth
		print(prefix + "KeyList", keylistkey.value)
		for key in keylist:
			print(prefix + "|" + str(key))#str(key.__class__))#
			if isinstance(key, KeyListKey) and key not in visited:
				visited.append(key)
				self.viz(key, depth+1, visited)

	def gviz(self):
		import pandas as pd
		import numpy as np
		import networkx as nx
		import matplotlib.pyplot as plt
		fm = []
		to = []
		color = []
		for klid, keylist in self.keylists.items():
			for key in keylist:
				if key is None:
					continue
				fm.append(key)
				to.append(klid)
				color.append("black")
				if isinstance(key, KeyListKey):
					# this should be a different color at least
					fm.append(key)
					to.append(key.value)
					color.append("red")
		df = pd.DataFrame({ 'source':fm, 'target':to, 'color':color})
		G=nx.from_pandas_edgelist(df, create_using=nx.DiGraph(), edge_attr=True)
		nx.draw(G, with_labels=True, node_size=1500, alpha=0.3, arrows=True)#.values)
		plt.show()

	def run(self, domainkey):

		current = self.get_domain(domainkey)

		keys = self.get_keylist(current.keylistkey)

		while True:#current.associated(self, DK_STATE).value == DS_ACTIVE:
			# do a step
			# Ascend the meter chain
			timekey = keys[DK_TIME]
			chain = [timekey]

			while True:
				parentkey = chain[-1].value[MK_PARENT]
				if parentkey is None:
					break
				chain.append(parentkey)

			print([str(k) for k in chain])

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

			code = self.get_page(keys[DK_CODE])
			ipkey = keys[DK_IP]
			ip = ipkey.value

			if ip >= len(code):
				# TODO move up
				if timekey.value[MK_PARENT] is None:
					break
				continue
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
			elif symbol == "²":
				data[pointer] = (data[pointer]<<1)%CELLSIZE
			elif symbol == "½":
				data[pointer] = (data[pointer]>>1)%CELLSIZE
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

			elif symbol == "r":
				# root, reset workbench to domain keylistkey
				keys[DK_WORKBENCH] = current.keylistkey

			elif symbol == "t":
				# Traverse workbench down
				assert data[pointer] < 16
				key = keys[data[pointer]]
				assert isinstance(key, KeyListKey)
				keys[DK_WORKBENCH] = key

			elif symbol == "l":
				# Create new KeyList in workbench
				assert data[pointer] < 16
				newkeylistkey = self.create_keylist()
				wb1 = self.get_keylist(keys[DK_WORKBENCH])
				wb1[data[pointer]] = newkeylistkey

			elif symbol == "c":
				# Copy key
				wb1 = self.get_keylist(keys[DK_WORKBENCH])
				wb2 = self.get_keylist(keys[DK_WORKBENCH2])

				indices = data[pointer]
				wb1i = (indices & 0xf)
				wb2i = ((indices >> 4) & 0xf)

				wb2[wb2i] = wb1[wb1i]

				#include attenuate here?
			elif symbol == "d":
				# Make this also a 'm' message?
				# Create new domain
				wb2 = keys[DK_WORKBENCH2]
				self.create_domain(wb2[0], wb2[1], wb2[2])

			elif symbol == "s":
				keys[DK_WORKBENCH], keys[DK_WORKBENCH2] = keys[DK_WORKBENCH2], keys[DK_WORKBENCH]

			elif symbol == "a":
				# Attenuate key
				# how to weaken meter key by certain amount? if CELLSIZE=256, this might suck
				# attenuate in place or by copy/transfer?
				# for now, in place
				wb1 = self.get_keylist(keys[DK_WORKBENCH])
				indices = data[pointer]
				wbi1 = (indices & 0xf)
				option = ((indices >> 4) & 0xf)

				key = wb1[wbi1]

				if key is not None:
					wb1[wbi1] = key.attenuate(option)

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
					sender = current
					receiver = self.get_domain(domainkey)

					# use DK_WORKBENCH2 as DK_INBOX!, also as outbox?
					#		keys[DK_INBOX] = kf.create_keylist()
					receiver.keys[DK_WORKBENCH2] = sender.keys[DK_WORKBENCH2]

					current = receiver

			if not jump:
				ipkey.value += 1

from random import choice

SYMBOLS = "><+-[]rtlcdsam"

def translate(code):
	return [SYMBOLS.index(c) for c in code]

def genrandom(length=256):
	code = ""
	for i in range(length):
		code += choice(SYMBOLS)
	return code

PROGRAM = "+++++++l>+"


kf = KeyFuck()
domainkey = kf.create_domain(kf.prime_time_meter, kf.prime_memory_meter, translate(PROGRAM))#genrandom()))
kf.run(domainkey)
domain = kf.get_domain(domainkey)
datapagekey = domain.associated(kf, DK_DATA)
data = kf.get_page(datapagekey).data
print(data)
kf.viz(domain.keylistkey)
#kf.gviz()
