# Assembler

The assembler accepts instructions in a tree format

`memwrite(memread(0,0),1,codelen())`

is expanded to

```
PUSH 0
PUSH 0
MEMREAD
PUSH 1
CODELEN
MEMWRITE
```

It doesn't yet check if the inputs/outputs match up.
