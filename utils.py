def num(a, bitlen=8):
	c = ""
	bitstring = bin(a)[2:].zfill(bitlen)

	for index, bit in enumerate(bitstring):
		c += "²"
		if bit == "1":
			c += "+"
	return c

def clear():
	return "½"*8

def pair(a,b):
	#can omit zfill here, but only if memory cell zero beforehand
	return num(a,4)+num(b,4)

"""
print(num(255))
print(pair(1,0))
print(clear())
"""

def asm(p):
	result = ""

	i = 0

	def read(n):
		nonlocal i
		end = i+n
		data = p[i:end]
		i = end
		return data

	def readi():
		nonlocal i
		num = ""
		while p[i] in "0123456789":
			num += p[i]
			i += 1
		return int(num)

	def ass(c):
		assert read(len(c)) == c

	def readargs(n):
		args = []
		ass("(")
		for j in range(n):
			args.append(readi())
			if j != n-1:
				ass(",")
		ass(")")
		return args

	while True:
		if i >= len(p):
			break

		op = p[i]

		if op in "ca":
			read(1)
			result += pair(*readargs(2)) + op + "\n"
		elif op in "dm":
			read(1)
			result += num(readargs(1)[0]) + op + "\n"
		elif op in "0123456789":
			result += num(readi()) + "\n"
		elif op in "\n \t":
			read(1)
		else:
			result += read(1) + "\n"

	return result
