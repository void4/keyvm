from vm import KeyVM
from instructions import *

code = [I_PUSH, 1, I_PUSH, 2, I_ADD]

vm = KeyVM()
image = vm.run_code(code)

#print(image)
import zlib
compressed = zlib.compress(image)
#print(compressed)
print(len(image), len(compressed))
