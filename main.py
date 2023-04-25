import argparse
import json

from vm import KeyVM

from assembler import asm

parser = argparse.ArgumentParser(
    prog="KeyVM",
    description="secure virtual machine",
    epilog="🔑",
)

parser.add_argument("filename")

parser.add_argument("-d", "--debug", action="store_true", default=False, dest="debug")
parser.add_argument("-w", "--webdebug", action="store_true", default=False, dest="webdebug")
parser.add_argument("-c", "--debugcomm", action="store_true", default=False, dest="debugcomm")

parser.add_argument("-s", "--sleep", default=None, type=float, dest="sleep")

parser.add_argument("-z", "--zstats", action="store_true", default=False, dest="zstats")

args = parser.parse_args()

if args.webdebug:
    args.debug = True
    args.debugcomm = True

if args.filename.endswith(".ism"):
    with open(args.filename) as f:
        text = f.read()
        code = asm(text)
elif args.filename.endswith(".l"):
    with open(args.filename) as f:
        text = f.read()
        prefix = "from instructions import *;"
        exec(prefix+text)
        if not "code" in globals():
            print("Loaded file {args.filename} did not define 'code' variable")
            exit(1)

vm = KeyVM()
image = vm.run_code(code, 750, stacksize=256, datasize=256, debug=args.debug, opendebugger=args.webdebug, debugcomm=args.debugcomm, debugsleep=args.sleep)

print("RESUME")

#vm = KeyVM()
image = vm.run(image, 100, debug=args.debug, debugcomm=args.debugcomm, debugsleep=args.sleep)

#print(image)
# Show compression stats
if args.zstats:
    import zlib
    imagestring = json.dumps(image)
    imagebytes = imagestring.encode("utf8")
    compressed = zlib.compress(imagebytes)
    #print(compressed)
    print(len(imagebytes), len(compressed))
