# Architecture

## General properties

KeyVM is

- a stack-based computational architecture
- single-threaded - control only resides at one place at a time
- deterministic a copy of the program state with the same input will always create the same results, down to the bit
- stateless, image-based - all data necessary to restore a process resides in the process image, which can be saved to and loaded from a file after execution ends

## Access right model

What makes this architecture unique is that its primary object of abstraction are *rights*, represented by objects called keys. In contemporary operating systems and programming languages, the main abstraction is usually the process, with a fixed code and data memory attached to it. Here, a process is just a set of access rights. More than one process can have keys to the same piece of memory. While which process owns which keys can change over time, these access relations are always explicit and absolute. It is impossible to read from or write to something you don't have the keys to. It works just like real, physical keys and locks.

Instead of sending data to another process, you just send a copy of the key that allows it to access the data. Now, data is not the thing that matters, but the rights to it. This is a weird conceptual inversion or abstraction that takes some time to get used to. Since many concepts depend on each other it is difficult to write a description that never depends on later definitions. It is therefore useful to read the following several times.

Everything in this architecture is derived from two things:

- Key: gives access to something, there are many different types of keys. If you don't have the key, you can't access it.
- Page: a contiguous sequence of either bytes *xor* keys of dynamic size, used to store code and data. Pointed to by PageKeys

### Domain
A domain is just a KeyPage that is structured in a way that it can run as a process. It points to a page to contains the code it executes and two others which it uses as data memory and stack respectively.

Domains pass control to each other by invoking a DomainKey. A message contains only a single Key which is copied to the called domains' KeyPage. The called domain can then access the (indirectly) referred to pages with that key. This is the way data and rights are distributed throughout the system.

In this implementation, only one domain has control at a time (single-threaded architecture).

### Meters

MeterKeys account for resources, specifically computation time and memory limits. Domains have to own a time meter key in order to run the code they refer to.
MeterKeys are organized in a tree hierarchy, each meter has a parent meter, up to the so called Prime Meters.

In order to allocate more pages, one needs a Memory MeterKey with sufficient resources.
When a domain runs, the entire meter chain up to the prime meter is decreased at every execution step. When a meter runs out of time, its the controller of its parent (RESEARCH) receives control.

| Key | Right | Example |
| --- | --- | --- |
| MeterKey | Draw resources from the parent meter chain | Separate into time and memory keys? |
| PageKey | Read and write access to a key or data page | Can be attenuated to PageReadKey |
| PageReadKey | Read access to a key or data page | Not yet implemented |
| DomainKey | Allows sending a message and thus transferring control to the referred domain | Also called GateKey in KeyKOS. |
| SystemKey | When called, invokes the VM and returns the result | network io, file system access etc. Protocol TBD |

More info here:

- http://www.cap-lore.com/Agorics/Library/KeyKos/key370.html
- http://www.cap-lore.com/Agorics/Library/KeyKos/

## Main actions

- create a new KeyPage or DataPage
- copy a Key (within the same or to another KeyPage)
- attenuate a Key (weaken its rights, e.g. PageKey -> PageReadKey)
- send a message and transfer control to another domain by calling the PageKey that refers to it
- create a new domain from a prepopulated KeyPage

### Special instructions

The CREATE instruction is used to create a new process from one of the processes' memories. The creating process receives a key to the newly created process.

The RECURSE instruction can be invoked to transfer control to another process image in the list. Each process is assigned resource limits: instruction steps/time ('gas') and a memory allocation limit and/or memory-time cost (cost per word per timestep).

The TRANSFERKEY instruction can be used to give another process the right to call a process the current domain already has access to.
