from vm import KeyVM
from instructions import *

code = [I_PUSH, 1, I_PUSH, 2, I_ADD]

vm = KeyVM()
vm.run_code(code)
