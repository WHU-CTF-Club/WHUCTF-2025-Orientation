import os
import signal
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.Padding import pad
import socketserver
import socket
from random import randrange
from Crypto.Hash import SHA256

# flag = os.getenv("GZCTF_FLAG")
flag = "whuctf{Ch3ck_7he_Curv3_1s_Very_Imp0rtant!}"
p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
a = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
G = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296, 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)

def point_add(P, Q):
    if P == (0, 0):
        return Q
    if Q == (0, 0):
        return P
    (x1, y1) = P
    (x2, y2) = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return 0, 0
    if P != Q:
        k = ((y2 - y1) * pow(x2 - x1, p - 2, p)) % p
    else:
        k = ((3 * x1 * x1 + a) * pow(2 * y1, p - 2, p)) % p

    x3 = (k * k - x1 - x2) % p
    y3 = (k * (x1 - x3) - y1) % p
    return x3, y3


def scalar_multiply(k, P):
    result = (0, 0)
    addend = P

    while k:
        if k % 2 == 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k //= 2

    return result


class Task(socketserver.BaseRequestHandler):
    def _recvall(self):
        BUFF_SIZE = 8172
        data = b''
        while True:
            part = self.request.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                break
        return data.strip()

    def send(self, msg, newline=True):
        try:
            if newline:
                msg += b'\n'
            self.request.sendall(msg)
        except:
            pass

    def recv(self, prompt=b'[-] '):
        self.send(prompt, newline=False)
        return self._recvall()

    def handle(self):
        self.request.settimeout(180)
        try:
            self.send(b"Invalid-Curve-Attack")
            sk = (randrange(1, p) % 2**128)
            pub = scalar_multiply(sk, G)          
            self.send(b"public key: \n")
            self.send(str(pub).encode())

            for i in range(7):
                try:
                    self.send(b"Input your x: \n")
                    user_x = self.recv().decode()
                    self.send(b"Input your y: \n")
                    user_y = self.recv().decode()
                    user_pub_key = (int(user_x), int(user_y))
                    shared_key = scalar_multiply(sk, user_pub_key)
                    self.send(b"Your shared key: \n")
                    self.send(str(shared_key).encode())
                except Exception:
                    self.send(b'Error!')
                    break

            self.send(b"Here is the encrypted flag\n")
            SHA = SHA256.new()
            SHA.update(str(sk).encode())
            KEY = SHA.digest()
            cipher = AES.new(KEY, AES.MODE_ECB)
            if isinstance(flag, str):
                flag_bytes = flag.encode()
            else:
                flag_bytes = flag
            ct = cipher.encrypt(pad(flag_bytes, AES.block_size))
            self.send(ct.hex().encode())
        except socket.timeout:
            self.send(b"Time's up!")
        finally:
            self.request.close()  # 确保连接被关闭




class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":

    HOST, PORT = '0.0.0.0', 9999

    print("HOST:POST " + HOST + ":" + str(PORT))
    server = ThreadedServer((HOST, PORT), Task)
    server.allow_reuse_address = True
    server.serve_forever()