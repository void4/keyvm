#the ast module is fucking useless, because it doesnt include comments
#same with inspect, because it only gives the source, not a tree

with open("../vm.py") as f:
    text = f.read()

from horast import parse, unparse
#print("Parsing...")
tree = parse(text)
#print(unparse(tree))
#print(tree)
"""
class Visitor(RecursiveAstVisitor[typed_ast.ast3]):
    def visit_node(self, node):
        if not only_localizable or hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            print(node)
visitor = Visitor()
visitor.visit(tree)
"""

from typed_ast import _ast3 as ast
from horast.nodes import Comment

node = tree.body[2].body[-1].body[-2]

print("| Instruction | Description |")
print("|-------------|-------------|")

while len(node.orelse) > 0:
    #print(type(node.orelse[0]))
    if type(node.orelse[0]) in [ast.Break]:
        break
    if node.test.left.id == "I":
        iname = node.test.comparators[0].id[2:]
        desc = ""
        #print(node.body)
        if len(node.body) > 0:
            first = node.body[0]
            if type(first) in [Comment, ast.Expr]:
                if type(first.value) == ast.Str:
                    desc = first.value.s.replace("\n", "").strip().replace("<", "`<").replace(">", ">`")
        print("| %s | %s |" % (iname, desc))#, dir(first))

    #print(node.orelse)
    node = [x for x in node.orelse if type(x) == ast.If][0]
