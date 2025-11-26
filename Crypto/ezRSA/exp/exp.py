# sagemath 10.6


from Crypto.Util.number import *
from tqdm import tqdm
import string


c = 698197338115320902659299443514800163171265012433857406902584
p = 1046072450373105149601541223881
q = 1152643457422372971125753823383
n = p * q
phi = (p-1)*(q-1)
e = 65537
d = inverse_mod(e,phi)
newm = long_to_bytes(pow(c,d,n))
c = bytes_to_long(newm)

prefix = b"WHUCTF{"
suffix = b"}"
t = n
centerMark =85

# 遍历flag的长度
for i in tqdm(range(30, 40)):
    length = i
    k = length - len(prefix) - len(suffix)
    pc = c
    # 剥离前后缀的影响
    pc = (pc - bytes_to_long(prefix) * pow(256, k + len(suffix), n) - bytes_to_long(suffix)) % n

    # 获得明文的对应长整数
    cc = pc * inverse_mod(256, n) % n
    sumConstant = sum(256^j for j in range(k))
    C = (cc - centerMark * sumConstant) % n

    # 造格子 规约
    M = matrix(ZZ, k + 2, k + 2)
    for index in range(k):
        M[index, index] = 1
        M[index, k+1] = t * 256^index
    M[k, k] = 1
    M[k, k + 1] = -t * C
    M[k + 1, k + 1] = t * n
    L = M.LLL()
    # print(L)

    # 筛选可能的答案
    for row in L:
        if row[-1] == 0:
            tag = 1
            for num in row[:-2]:
                if num < 33 - centerMark or num > 126 - centerMark:
                    tag = 0
                    break        
            if tag:
                flag = ""
                for num in row[:-2][::-1]:
                    flag += chr(num + centerMark)
                if chr(centerMark) * 4  not in flag:
                    pflag = b"WHUCTF{" + flag.encode() + b"}"    
                    print(f"length {i} , flag {pflag}")
        
'''
length 39 , flag b'WHUCTF{Oops_maybe_the_flag_is_too_long}'
length 39 , flag b'WHUCTF{a7k1am`IQF=Nd(SZ<iOjRnh2-1^u(4<}'
length 39 , flag b'WHUCTF{U^\\{"9]sl[_^FH*RZT3kUg}Y0cQ=z^?}'
length 39 , flag b'WHUCTF{UR|N[.<:U9RNJifAB"/ylZ0ZR6\\,j[6}'
length 39 , flag b'WHUCTF{k=E5FdB;B+TqM{QtRUYq1>zKvZAJ@`[}'
'''
