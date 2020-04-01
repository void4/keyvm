from vm import KeyVM
from instructions import *

three = [I_PUSH, 1, I_PUSH, 2, I_ADD]
code = [I_PUSH, D_SELF, I_PUSH, 10, I_PAGESIZESET, I_PUSH, 9, I_PUSH, 0, I_PUSH, D_MEMORY, I_PUSH, 42, I_PAGECREATE]

vm = KeyVM()
image = vm.run_code(code)

#print(image)
import zlib
compressed = zlib.compress(image)
#print(compressed)
print(len(image), len(compressed))
