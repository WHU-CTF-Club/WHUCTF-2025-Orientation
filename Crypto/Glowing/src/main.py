import os
import socketserver
import socket
from secret import plain
from Crypto.Util.number import *

flag = os.getenv("GZCTF_FLAG")
flag = flag.encode()

def encrypt():
    length = len(flag)
    block = [plain[i:i + length] for i in range(0, len(plain), length)]
    c = []
    for i in block:
        result = bytes(a ^ b for a, b in zip(flag, i))
        c.append(result)
    b = []
    for i in c:
        b.append(hex(bytes_to_long(i)))
    return b

class Task(socketserver.BaseRequestHandler):
    def _recvall(self):
        BUFF_SIZE = 4096
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
        self.request.settimeout(90)
        try:
            encrypted_data = encrypt()
            for i, block in enumerate(encrypted_data):
                self.send(f"Block {i+1}: {block}".encode())
            
        except socket.timeout:
            self.send(b"Time's up!")
        finally:
            self.request.close()

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    HOST, PORT = '0.0.0.0', 9999
    print("HOST:POST " + HOST + ":" + str(PORT))
    server = ThreadedServer((HOST, PORT), Task)
    server.allow_reuse_address = True
    server.serve_forever()