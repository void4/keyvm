# KeyVM

## Documentation

https://keyvm.readthedocs.io

https://esolangs.org/wiki/KeyVM

## Quickstart

Needs Python >3.6. Tested with Python 3.8.2

### Download

`git clone https://github.com/void4/keyvm.git`

### Installation

`pip install -r requirements.txt`

### Usage

`python main.py`

## Notes

This is a combination of:

https://github.com/void4/keyfuck/ - Which had a key-only design, but only ultra-simple brainfuck semantics. This also used the KeyKOS architecture of Node/KeyLists of size 16, tree construction with workbenches to access a larger number of keys.

https://github.com/void4/keyvm-old - Which had a stack based VM, but domains where not exclusively keys, they also contained a fixed code memory and stack.
