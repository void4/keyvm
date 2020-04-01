# keyvm

## Architecture

### General

What makes this architecture unique is that its primary object of abstraction are *rights*, represented by objects called keys. In contemporary operating systems and programming languages, the main abstraction is usually the process, with a fixed code and data memory attached to it. Here, a process is just a set of access rights. More than one process can have keys to the same piece of memory. While which process owns which keys can change over time, these access relations are always explicit and absolute. It is impossible to read from or write to something you don't have the keys to. It works just like real, physical keys and locks.

Instead of sending data to another process, you just send a copy of the key that allows it to access the data. Now, data is not the thing that matters, but the rights to it. This is a weird conceptual inversion or abstraction that takes some time to get used to. Since many concepts depend on each other it is difficult to write a description that never depends on later definitions. It is therefore useful to read the following several times.

Everything in the KeyKOS architecture is derived from three things:

- Key: gives access to something, there are many different types of keys. If you don't have the key, you can't access it.
- KeyList (also called Node in KeyKOS): a list of 16 keys. Pointed to by KeyListKeys
- Page: a contiguous sequence of bytes of a fixed size, used to store code and data. Pointed to by PageKeys

#### Domain
A domain is just a KeyList that is structured in a way that it can run as a process. It points to a page to contains the code it executes and to another which it uses as data memory.

Domains pass control by sending a message to another domain by invoking a DomainKey. A message consists only of a KeyListKey which is copied to the called domains' KeyList. In this implementation, only one domain has control at a time (single-threaded architecture).

It is possible to copy keys and send them to another domain. This is the way rights are distributed throughout the system. A domain has only 16 slots in its KeyList, but since (KeyList)Keys can refer to other KeyLists, it is possible to create a tree of keys that is as large as necessary.

#### Meters

MeterKeys account for resources, specifically computation time and memory limits. Domains have to own a time meter key in order to run the code they refer to.
MeterKeys are organized in a tree hierarchy, each meter has a parent meter, up to the so called Prime Meters.

In order to allocate more pages, one needs a Memory MeterKey with sufficient resources.
When a domain runs, the entire meter chain up to the prime meter is decreased at every execution step. When a meter runs out of time, its the controller of its parent (RESEARCH) receives control.

| Key | Right | Example |
| --- | --- | --- |
| MeterKey | Draw resources from the parent meter chain | Separate into time and memory keys? |
| KeyListKey | Read and write access to a KeyList | |
| PageKey | Read and write access to a page | Can be attenuated to PageReadKey |
| PageReadKey | Read access to a page | Not yet implemented |
| DomainKey | Allows sending a message and thus transferring control to the referred domain | Also called GateKey in KeyKOS. |

More info here:

- http://www.cap-lore.com/Agorics/Library/KeyKos/key370.html
- http://www.cap-lore.com/Agorics/Library/KeyKos/

### Main actions

- copy a Key (within the same or to another KeyList)
- create a new KeyList
- create a new domain from a prepopulated KeyList
- attenuate a Key (e.g. PageKey -> PageReadKey)
- send a message and transfer control to another domain

## Usage

`python main.py`

## Notes

This is a combination of:

https://github.com/void4/keyfuck/ - Which had a key-only design, but only ultra-simple brainfuck semantics. This also used the KeyKOS architecture of Node/KeyLists of size 16, tree construction with workbenches to access a larger number of keys.

https://github.com/void4/keyvm-old - Which had a stack based VM, but domains where not exclusively keys, but also contained a fixed code memory.
