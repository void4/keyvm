# Bytecode

| Instruction | Description |
|-------------|-------------|
| CREATE | Create a new process from the given `<memory>` |
| ALLOC | Allocate `<size>` words at the end of `<memory>` |
| TRANSFERKEY | Transfer the key `<transferkeyindex>` to the process pointed to by `<targetkeyindex>`			Should probably be renamed, because it rather "copies" the key |
| RECURSE | Recurse into process pointed to by `<keyindex>`, with `<gas>` and `<mem>` limits |
| MEMSIZE | Push the number of memories onto the stack |
| MEMWRITE | Write `<data>` to the `<memory>` at `<address>` |
| MEMCREATE | Create a new empty memory |
| ADD | Compute `<arg1>` + `<arg2>` and push the result on the stack |
| SUB | Compute `<arg1>` - `<arg2>` and push the result on the stack |
| MUL | Compute `<arg1>` * `<arg2>` and push the result on the stack |
| DIV | Compute `<arg1>` / `<arg2>` and push the result on the stack |
| JUMP | Set the instruction pointer to `<target>` (unconditional jump/goto) |
| JUMPIF | Set the instruction pointer to `<target>` if `<condition>` >` 0 (conditional jump) |
| CODEREAD | Push the `<code_index>` word of the own flattened representation onto the stack |
| CODELEN | Push the length of the own flattened representation onto the stack |
| PUSH | Pushes the immediate argument onto the stack |
| DUP | Duplicate the topmost element of the stack |
| MEMPUSH | Depending on `<memory>`, read either from (0:HEADER, 1:CODE, 2: n-2 memory) at `<address>` |
| FORK | Duplicate this process and receive its key |
| HALT | Set the halt status on this process and jump back to parent. |
| RETURN | Set the return status on this process and jump back to parentself.	Used to indicate that return values are available (TODO) |
| RANDOM | (Temporary) random number generator: integer between `<mi>` and `<ma>` (exclusive) |


For more, see instructions.py
