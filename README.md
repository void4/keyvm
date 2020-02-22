# keyfuck

## Architecture

### General

Everything in the KeyKOS architecture is derived from three things:

- Key: gives access to something, there are many different types of keys. If you don't have the key, you can't access it.
- KeyList (also called Node in KeyKOS): a list of 16 keys. Pointed to by KeyListKeys
- Page: a contiguous sequence of bytes of a fixed size, used to store code and data. Pointed to by PageKeys

#### Domain
A domain is just a KeyList that is structured in a way that it can run as a process. It is possible to copy keys and send them to another domain. This is the way rights are distributed throughout the system.

#### Meters

MeterKeys account for resources, specifically computation time and memory limits. Domains have to own a time meter key in order to run the code they refer to.
MeterKeys are organized in a tree hierarchy, each meter has a parent meter, up to the so called Prime Meters.

In order to allocate more pages, one needs a Memory MeterKey with sufficient resources.
When a domain runs, the entire meter chain up to the prime meter is decreased at every execution step. When a meter runs out of time, its the controller of its parent (RESEARCH) receives control.

More info here: http://www.cap-lore.com/Agorics/Library/KeyKos/

| Key | Right | Example |
| --- | --- | --- |
| MeterKey | | |
| KeyListKey | Read and write access to a page | |
| PageKey | Read and write access to a page | Can be attenuated to PageReadKey |
| PageReadKey | Read access to a page | |
| DomainKey | Allows sending a message and thus transferring control to the referred domain | Also called GateKey in KeyKOS. Make this the same as KeyListKey? |
| | | |

### Main actions

- copy a Key (within the same or to another KeyList)
- create a new KeyList
- create a new domain from a prepopulated KeyList
- attenuate a Key (e.g. PageKey -> PageReadKey)
- send a message and transfer control to another domain

### Keyfuck-Specific
A domain has two "workbenches". This weird setup is required to make the brainfuck-semantics as elegant as possible.

## Usage

`python main.py`

## Notes

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
