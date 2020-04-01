from ..main import KeyVM

vm = KeyVM()
page1key = vm.create_page(vm.prime_memory_meter)
page2key = vm.create_page(vm.prime_memory_meter)
page3key = vm.create_page(vm.prime_memory_meter)

segment1key = vm.create_segment()
segment2key = vm.create_segment()

segment2 = vm.get_segment(segment2key)
segment2[0] = page1key
segment2[1] = page2key

segment1 = vm.get_segment(segment1key)
segment1[0] = segment2key
segment1[1] = page3key

print(segment1.length(vm))
print(segment1.read(vm, 512))
