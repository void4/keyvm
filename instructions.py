NUMINSTR = 21
I_PUSH, I_ADD, I_SUB, I_MUL, I_DIV, I_MOD, I_AND, I_OR, I_XOR, I_NOT, I_CREATEPAGE, I_PAGETYPE, I_PAGESIZESET, I_PAGESIZEGET, I_CALL, I_COPYKEY, I_ATTENUATE, I_JUMP, I_JUMPIF, I_PAGEREAD, I_PAGEWRITE = range(NUMINSTR)

#TODO I_KEYVALUE

INSTRUCTIONNAMES = "I_PUSH, I_ADD, I_SUB, I_MUL, I_DIV, I_MOD, I_AND, I_OR, I_XOR, I_NOT, I_CREATEPAGE, I_PAGETYPE, I_PAGESIZESET, I_PAGESIZEGET, I_CALL, I_COPYKEY, I_ATTENUATE, I_JUMP, I_JUMPIF, I_PAGEREAD, I_PAGEWRITE".split(", ")

R_CARGS, R_NONE = range(2)
# Codeargs
REQUIREMENTS = {
    I_PUSH: [1],
    I_ADD: [0],
    I_SUB: [0],
    I_MUL: [0],
    I_DIV: [0],
    I_MOD: [0],
    I_AND: [0],
    I_OR: [0],
    I_XOR: [0],
    I_NOT: [0],
    I_CREATEPAGE: [0],
    I_PAGETYPE: [0],
    I_PAGESIZESET: [0],
    I_PAGESIZEGET: [0],
    I_CALL: [0],
    I_COPYKEY: [0],
    I_ATTENUATE: [0],
    I_JUMP: [0],
    I_JUMPIF: [0],
    I_PAGEREAD: [0],
    I_PAGEWRITE: [0],
}

# Key attenuation options
A_WRITE, A_READ = range(2)

# Page types
PG_DATA, PG_KEYS = range(2)

# Put this into a separate file, since this is a higher level definition?
DOMAINFIELDS = 10
D_TIME, D_MEMORY, D_SELF, D_STATE, D_IP, D_CODE, D_POINTER, D_STACK, D_DATA, D_RECV = range(DOMAINFIELDS)
S_ACTIVE, S_WAITING, S_ERROR = range(3)#omit these? global active index in image?
