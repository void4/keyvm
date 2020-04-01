from ..main import KeyVM

vm = KeyVM()

codepagekey = vm.create_page(vm.prime_memory_meter)

codesegmentkey = vm.create_segment()
codesegment = vm.get_segment(codesegmentkey)
codesegment[0] = codepagekey

datapagekey = vm.create_page(vm.prime_memory_meter)

datasegmentkey = vm.create_segment()
datasegment = vm.get_segment(datasegmentkey)
datasegment[0] = datapagekey

stackpagekey = vm.create_page(vm.prime_memory_meter)

stacksegmentkey = vm.create_segment()
stacksegment = vm.get_segment(stacksegmentkey)
stacksegment[0] = stackpagekey

domainkey = vm.create_domain(vm.prime_time_meter, vm.prime_memory_meter, codesegmentkey)
