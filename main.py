from vm import KeyVM
from instructions import *
from assembler import asm

three = [I_PUSH, 1, I_PUSH, 2, I_ADD]
pagecreate = [I_PUSH, D_SELF, I_PUSH, 10, I_PAGESIZESET, I_PUSH, 9, I_PUSH, 0, I_PUSH, D_MEMORY, I_PUSH, 42, I_CREATEPAGE]

code = """
add(1,0)
start:
add(1,1)
jump(:start)
"""

code = asm(code)

print(code)

vm = KeyVM()
image = vm.run_code(code, 750)

print("RESUME")

#vm = KeyVM()
image = vm.run(image, 100)

"""
#print(image)
import zlib
compressed = zlib.compress(image)
#print(compressed)
print(len(image), len(compressed))
"""
