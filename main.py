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

DK_STATE, DK_TIME, DK_IP, DK_CODE, DK_DATA = range(5)
DS_ACTIVE, DS_WAITING = range(2)

class Domain:
	def __init__(self, time_meter_key, codepagekey, datapagekey):
		self.keys = KeyList()
		self.keys[DK_STATE] = Key(0)#STATE
		self.keys[DK_TIME] = time_meter_key
		self.keys[DK_IP] = Key(0)#IP
		self.keys[DK_CODE] = codepagekey
		self.keys[DK_DATA] = datapagekey

class KeyFuck:
	def __init__(self):
		self.domains = []
		self.pages = []
		self.prime_time_meter = MeterKey([None, None, -1])
		self.prime_memory_meter = MeterKey([None, None, -1])

	def create_page(self, memory_meter_key):
		page = Page(memory_meter_key)
		#should use dict with globally unique id, in case pages get deleted
		pagekey = PageKey(len(self.pages))
		self.pages.append(page)
		return pagekey

	def get_page(self, pagekey):
		assert isinstance(pagekey, PageKey)
		return self.pages[pagekey.value]

	def create_domain(self, time_meter_key, memory_meter_key):
		codepagekey = self.create_page(memory_meter_key)
		datapagekey = self.create_page(memory_meter_key)

		domain = Domain(time_meter_key, codepagekey, datapagekey)
		domainkey = len(self.domains)
		self.domains.append(domain)

		return DomainKey(domainkey)

	def run(self):
		current = self.domains[0]

		while current.keys[DK_STATE].value == DS_ACTIVE:
			# do a step
			timekey = current.keys[DK_TIME]
			if timekey.value[MK_RESOURCES] <= 0 and timekey.value[MK_PARENT] is not None:
				current = timekey.value[MK_PARENT]
				continue

			timekey.value[MK_RESOURCES] -= 1

			code = self.get_page(current.keys[DK_CODE])
			ip = current.keys[DK_IP].value

			instruction = code[ip]
			print(instruction)

kf = KeyFuck()
kf.create_domain(kf.prime_time_meter, kf.prime_memory_meter)
kf.run()
