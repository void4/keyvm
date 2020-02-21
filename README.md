# keyfuck

Using a key referring to a list of keys is elegant
However, the implementation is not.
Especially not in a brainfuck-like language

indirection etc.

"bundle of rights"

construct new keylist
delete key
traverse key to keylist
attenuate
delete keylist - OS has to track lost keys!
send message/transfer key

-> two keylistkeys
-> two indices

a_ref
a_index
o_ref (keylistkey)
o_index (u256/u16)

actually, try to use one for now

owner-only-readable keys (meters)

total key max? 256

possible to replace without deleting key? for now, yes.

how to transfer data between two pages? memcpy? or just move/copy through code for constant op time?

Just use memory-limit, not memory-time
-> do not delete time=0 domains, if they still have memory
-> manual deletion, no automatic garbage collection except unreferenced keys

keyspace. the final frontier.
