from lark import Lark, Tree, Transformer
from instructions import *
import time

asmgrammar = r"""
%ignore /[\t \f\n]+/  // Whitespace
%import common.WORD
NAME: /[a-zA-Z_]\w*/
LABEL: /[a-zA-Z_]\w*:/
NUMBER: DEC_NUMBER
DEC_NUMBER: /0|[1-9]\d*/i

start: (expr | LABEL )*
INNERLABEL: /:[a-zA-Z_]\w*/
expr: NAME "\n" | NAME "(" [ expr [("," expr)*] ] ")" | NUMBER | INNERLABEL | COMMENT
COMMENT: ";" /[^\n]/* "\n"
"""#TODO instead of \n semicolon or general whitespace \w
asml = Lark(asmgrammar, debug=False)

class AsmTransformer(Transformer):
    def start(self, node):
        #print(node)
        return sum([n if isinstance(n, list) else [n.value] for n in node], [])
    def comment(self, node):
        return []
    def expr(self, node):
        if node[0].type == "NAME":
            code = []
            for arg in node[1:]:
                if isinstance(arg, list):
                    code += arg
                else:
                    raise Exception("ASM Parse Error")
            if node[0].value != "push":
                code += [node[0].value.upper()]
            return code
        elif node[0].type == "NUMBER":
            return ["PUSH %i" % int(node[0].value)]
        elif node[0].type == "INNERLABEL":
            return ["PUSH %s" % str(node[0].value)]
        elif node[0].type == "COMMENT":
            return []
        else:
            raise Exception("ASM Parse Error")

def assemble(code):
    instrcounter = 0
    wordcounter = 0
    labels = {}
    for i, instr in enumerate(code):
        if instr.endswith(":"):
            labels[instr[:-1]] = instrcounter#wordcounter if flattened
        elif instr.startswith("PUSH "):
            instrcounter += 1
            wordcounter += 2
        else:
            instrcounter += 1
            wordcounter += 1
        #print(instrcounter, instr)

    #print(labels)
    binary = []
    #print("CODE", code, type(code))
    for i, instr in enumerate(code):
        if instr.endswith(":"):
            pass
        elif instr.startswith("PUSH :"):
            binary.append([I_PUSH, labels[instr.split(":")[-1]]])
        else:
            instr = instr.split()
            #print(instr)
            try:
                opcode = eval("I_"+instr[0])
                binary.append([opcode]+list([eval(n) for n in instr[1:]]))
            except IndexError as e:
                print(e, instr)

    return binary

asmt = AsmTransformer()
def asm(text):
    """Assemble ast-assembly code into vm binary"""
    parsed = asml.parse(text)
    #print(parsed)
    transformed = asmt.transform(parsed)
    #print(transformed)

    binary = assemble(transformed)

    flat = []
    for sublist in binary:
        flat.extend(sublist)

    return flat

code = """
add(1,0)
start:
add(1,1)
jump(:start)
"""

if __name__ == "__main__":
    print(asm(code))
