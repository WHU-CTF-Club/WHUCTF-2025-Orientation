from Crypto.Util.number import *
from secret import flag
import hashlib
assert flag[:7] == "WHUCTF{" and flag[-1] == "}" 
assert len(flag) >= 30 and len(flag) <= 40
p = getPrime(100)
q = getPrime(100)
n = p * q
e = 65537
m = bytes_to_long(flag.encode())
assert m > n

c = pow(m, e, n)
print(f'c = {c}')
print(f'p = {p}')
print(f'q = {q}')


print(hashlib.sha256(flag.encode('utf-8')).hexdigest())

# c = 698197338115320902659299443514800163171265012433857406902584
# p = 1046072450373105149601541223881
# q = 1152643457422372971125753823383
# 2005d55e7dc2c2776cbca592d34a8481129bc8d66511055036dbf408154847bd