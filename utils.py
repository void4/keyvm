def num(a):
    c = ""
    for i in bin(a)[2:]:
        if i == "1":
            c += "+"
        c += "²"
    return c

def clear():
    return "½"*8

def pair(a,b):
    c = ""
    for i in bin(a)[2:].zfill(4):#can omit zfill here, but only if memory cell zero beforehand
        if i == "1":
            c += "+"
        c += "²"

    for i in bin(b)[2:].zfill(4):
        if i == "1":
            c += "+"
        c += "²"

    return c

print(num(255))
print(pair(1,0))
print(clear())
