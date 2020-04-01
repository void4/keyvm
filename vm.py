CELLSIZE = 256
KEYLISTLEN = 16
MK_PARENT, MK_CONTROLLER, MK_RESOURCES = range(3)
PAGESIZE = 256

SYMBOLS = "h><+-[]²½rtlcdfamsp"

def translate(code):
	return [SYMBOLS.index(c) for c in code]

from random import choice

def genrandom(length=256):
	code = ""
	for i in range(length):
		code += choice(SYMBOLS)
	return code

class KeyList:
	def __init__(self):
		self.data = [None for i in range(KEYLISTLEN)]

	def __setitem__(self, key, value):
		# TODO allow ints? DataKey?
		assert isinstance(value, Key), type(value)
		if self.data[key] is not None:
			#del self.data[key]#this actually deletes list entry!
			self.__delitem__(key)
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

class Page:
	def __init__(self, parentmeter):
		self.meter = parentmeter
		self.data = [0 for i in range(PAGESIZE)]

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		#TODO Check if writer has PageKey (not PageReadKey)
		#Create something like PageContext?
		#Cache it?
		self.data[key] = value

	def read(self, key, value):
		self[key] = value

	def __len__(self):
		return len(self.data)

class SegmentKey(Key):
	pass

class Segment(KeyList):

	def length(self, vm):
		"""TODO: also cache this"""
		total_length = 0
		for key in self.data:
			if isinstance(key, PageKey):
				total_length += len(vm.get_page(key))
			elif isinstance(key, SegmentKey):
				total_length += vm.get_segment(key).length(vm)

		return total_length

	def __setitem__(self, key, value):
		# TODO allow ints? DataKey?
		assert isinstance(value, SegmentKey) or isinstance(value, PageKey), type(value)
		if self.data[key] is not None:
			#del self.data[key]#this actually deletes list entry!
			self.__delitem__(key)
		self.data[key] = value

	def traverse(self, vm, offset, start=0):

		# Because subsegment size may change (unless all parents get updated on change, hm)
		# have to check lengths on every memory access
		#TODO perhaps implement len() on Segment and Page keys

		for key in self.data:
			if isinstance(key, PageKey):
				page = vm.get_page(key)
				if offset - start < len(page):
					return page[offset - start], None
				else:
					start += len(page)
			elif isinstance(key, SegmentKey):
				segment = vm.get_segment(key)
				value, start = segment.traverse(vm, offset, start)
				if start is None:
					return value, start

		return None, start

	def read(self, vm, offset):
		value, start = self.traverse(vm, offset)
		if start is None:
			return value

		raise AssertionError("out of bounds memory access")

def split(bits):
	"""splits an 8 bit value into two 4 bit values"""
	a = ((bits >> 4) & 0xf)
	b = (bits & 0xf)
	return a,b

DK_STATE, DK_TIME, DK_MEMORY, DK_IP, DK_CODE, DK_POINTER, DK_STACK, DK_DATA, DK_WORKBENCH, DK_WORKBENCH2 = range(10)
DS_ACTIVE, DS_WAITING = range(2)

class Domain:
	def __init__(self, vm, keylistkey, time_meter_key, memory_meter_key, codesegmentkey, stacksegmentkey, datasegmentkey):
		self.keylistkey = keylistkey

		keys = vm.get_keylist(self.keylistkey)
		keys[DK_STATE] = Key(0)#STATE
		keys[DK_TIME] = time_meter_key
		keys[DK_MEMORY] = memory_meter_key
		keys[DK_IP] = Key(0)#IP
		keys[DK_CODE] = codesegmentkey
		keys[DK_POINTER] = Key(0)#POINTER
		keys[DK_STACK] = stacksegmentkey
		keys[DK_DATA] = datasegmentkey
		keys[DK_WORKBENCH] = self.keylistkey
		keys[DK_WORKBENCH2] = self.keylistkey

	def associated(self, vm, keyindex):
		keys = vm.get_keylist(self.keylistkey)
		return keys[keyindex]

class KeyVM:
	def __init__(self, timelimit=-1, memorylimit=-1):
		self.ids = 0
		self.keylists = {}
		self.domains = {}
		self.pages = {}
		self.segments = {}
		self.prime_time_meter = MeterKey([None, None, timelimit])
		self.prime_memory_meter = MeterKey([None, None, memorylimit])

	def __repr__(self):
		return f"Time: {self.prime_time_meter.value[2]}\tMemory:{self.prime_memory_meter.value[2]}\tKeylists:{len(self.keylists)}\tDomains:{len(self.domains)}\tPages:{len(self.pages)}"

	def create_id(self):
		#should use dict with globally unique id, in case pages get deleted
		self.ids += 1
		return self.ids

	def create_keylist(self):#TODO memory_meter_key
		keylist = KeyList()
		keylistkey = KeyListKey(self.create_id())
		self.keylists[keylistkey.value] = keylist
		return keylistkey

	def get_keylist(self, keylistkey):
		assert isinstance(keylistkey, KeyListKey), type(keylistkey)
		return self.keylists[keylistkey.value]

	def create_page(self, memory_meter_key):
		if not memory_meter_key.use(PAGESIZE):
			raise AssertionError("NOT IMPLEMENTED")
			return None
		page = Page(memory_meter_key)
		pagekey = PageKey(self.create_id())
		self.pages[pagekey.value] = page
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		return self.pages[pagekey.value]

	def create_domain(self, time_meter_key, memory_meter_key, codesegmentkey, datasegmentkey=None, stacksegmentkey=None, keylistkey=None):
		if keylistkey is None:
			keylistkey = self.create_keylist()#masterkey


		datapagekey = self.create_page(memory_meter_key)

		#TODO if codepagekey is None or datapagekey is None, revert

		domain = Domain(self, keylistkey, time_meter_key, memory_meter_key, codepagekey, datapagekey)
		domainkey = DomainKey(self.create_id())
		self.domains[domainkey.value] = domain
		# set domain bit on keylist datastructure
		return domainkey

	def get_domain(self, domainkey):
		assert isinstance(domainkey, DomainKey)
		return self.domains[domainkey.value]

	def create_segment(self):
		segmentkey = SegmentKey(self.create_id())
		self.segments[segmentkey.value] = Segment()
		return segmentkey

	def get_segment(self, segmentkey):
		assert isinstance(segmentkey, SegmentKey)
		return self.segments[segmentkey.value]

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
			elif isinstance(key, DomainKey):
				domain = self.get_domain(key)
				# Prevent visualizing domain keylist twice
				if domain.keylistkey not in visited:
					visited.append(domain.keylistkey)
					self.viz(domain.keylistkey, depth+1, visited)

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
		nx.spring_layout(G)
		nx.draw(G, with_labels=True, node_size=1500, alpha=0.3, arrows=True)#.values)
		plt.show()


	def copycode(self, codepagekey, code):
		codepage = self.get_page(codepagekey)
		assert len(code) <= len(codepage)
		for i in range(len(code)):
			codepage[i] = code[i]

	def run(self, domainkey, debug=False):

		current = self.get_domain(domainkey)

		while True:#current.associated(self, DK_STATE).value == DS_ACTIVE:
			# do a step
			# Ascend the meter chain
			print(self)
			# TODO investigate this
			if current is None:
				break

			keys = self.get_keylist(current.keylistkey)

			timekey = keys[DK_TIME]
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


			codesegment = self.get_segment(keys[DK_CODE])
			ipkey = keys[DK_IP]
			ip = ipkey.value

			if ip >= len(codesegment):
				# TODO move up
				if timekey.value[MK_PARENT] is None:
					break
				continue

			instruction = codesegment[ip]

			stacksegment = self.get_segment(keys[DK_STACK])

			pointerkey = keys[DK_POINTER]
			pointer = pointerkey.value

			# TODO segment_or_page
			data = self.get_segment(keys[DK_DATA])

			#print(data.data)

			symbol = SYMBOLS[instruction]
			print(symbol, end="")

			jump = False

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
				wb = self.get_keylist(keys[DK_WORKBENCH])
				wb[data[pointer]] = newkeylistkey

			elif symbol == "c":
				# Copy key
				wb1 = self.get_keylist(keys[DK_WORKBENCH])
				wb2 = self.get_keylist(keys[DK_WORKBENCH2])

				indices = data[pointer]
				wb1i, wb2i = split(indices)
				#print(wb1[wb1i])
				wb2[wb2i] = wb1[wb1i]

				#include attenuate here?
			elif symbol == "d":
				# Make this also a 'm' message?
				# Create new domain
				keylistkey = keys[DK_WORKBENCH2]
				wb2 = self.get_keylist(keylistkey)
				domainkey = self.create_domain(wb2[0], wb2[1], wb2[2], keylistkey)
				wb1 = self.get_keylist(keys[DK_WORKBENCH])
				wb1[data[pointer]] = domainkey

			elif symbol == "f":
				keys[DK_WORKBENCH], keys[DK_WORKBENCH2] = keys[DK_WORKBENCH2], keys[DK_WORKBENCH]

			elif symbol == "a":
				# Attenuate key
				# how to weaken meter key by certain amount? if CELLSIZE=256, this might suck
				# attenuate in place or by copy/transfer?
				# for now, in place
				wb = self.get_keylist(keys[DK_WORKBENCH2])
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

					# use DK_WORKBENCH2 as DK_INBOX!, also as outbox?
					#		keys[DK_INBOX] = vm.create_keylist()
					# Allow sending only one key? or entire workbench? copy or allow access to keylistkey?
					# Allow empty message? -> Empty workbench
					receiverkeys = self.get_keylist(receiver.keylistkey)
					receiverkeys[DK_WORKBENCH2] = keys[DK_WORKBENCH2]
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

			elif symbol == "s":
				"""create segment/upgrade keylist"""
				# only on empty keyslot? upgrading/preparing existing keylist?
				# meterkeyindex missing
				slotindex, _ = split(data[pointer])
				if keys[slotindex] is None:
					keys[slotindex] = self.create_segment()
				else:
					#???
					pass

			if not jump:
				ipkey.value += 1
