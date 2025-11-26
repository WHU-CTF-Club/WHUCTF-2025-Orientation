import os
import signal
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.Padding import pad
import socketserver
import socket

flag = os.getenv("GZCTF_FLAG")


def enc(msg, key):
    if isinstance(msg, str):
        msg = msg.encode()
    msg = pad(msg, AES.block_size)
    ctr = Counter.new(128, initial_value=1025)
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    return cipher.encrypt(msg)

class Task(socketserver.BaseRequestHandler):
    def _recvall(self):
        BUFF_SIZE = 2048
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
            self.send(b"Welcome to WHUCTF2025Orientation!")
            key = os.urandom(16)
            assert len(flag) == 48            
            try:
                enc_flag = enc(flag, key)  
                self.send(b"Here is your encrypted flag: "+str(enc_flag).encode())
            except Exception as e:
                self.send(b"Error in encryption: " + str(e).encode())
                return
            for i in range(30):
                try:
                    plaintext = self.recv("Please input your plaintext: ").decode()
                    plaintext = bytes.fromhex(plaintext)
                    ciphertext = enc(plaintext, key)
                    self.send(b"Here is your ciphertext"+str(ciphertext).encode())
                except Exception:
                    self.send(b'Error!')
                    break
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