from vm import KeyFuck, translate, DK_DATA
from utils import asm

#XXX REPLICATOR XXX
source = """
+++
[
7l
c(1,0)
a(0,2)
c(8,1)
c(3,2)
d(9)
7l
c(9,0)
m(7)
]
"""

if __name__ == "__main__":
	program = asm(source)
	print(program)

	program = program.replace("\n", "").replace(" ", "")
	import traceback
	kf = KeyFuck(15000)#TODO this doesn't really work, investigate
	codepagekey = kf.create_page(kf.prime_memory_meter)
	kf.copycode(codepagekey, translate(program))
	domainkey = kf.create_domain(kf.prime_time_meter, kf.prime_memory_meter, codepagekey)#genrandom()))
	try:
		kf.run(domainkey, False)
	except AssertionError as e:
		print(e)
		traceback.print_exc()
	except KeyboardInterrupt:
		pass
	domain = kf.get_domain(domainkey)
	datapagekey = domain.associated(kf, DK_DATA)
	data = kf.get_page(datapagekey).data
	#print([bin(d)[2:].zfill(8) for d in data])
	#kf.viz(domain.keylistkey)
	#kf.gviz()
	print(kf)
