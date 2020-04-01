from vm import KeyVM, translate, DK_DATA
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
	vm = KeyVM(15000)#TODO this doesn't really work, investigate
	codepagekey = vm.create_page(vm.prime_memory_meter)
	vm.copycode(codepagekey, translate(program))
	domainkey = vm.create_domain(vm.prime_time_meter, vm.prime_memory_meter, codepagekey)#genrandom()))
	try:
		vm.run(domainkey, False)
	except AssertionError as e:
		print(e)
		traceback.print_exc()
	except KeyboardInterrupt:
		pass
	domain = vm.get_domain(domainkey)
	datapagekey = domain.associated(vm, DK_DATA)
	data = vm.get_page(datapagekey).data
	#print([bin(d)[2:].zfill(8) for d in data])
	#vm.viz(domain.keylistkey)
	#vm.gviz()
	print(vm)
