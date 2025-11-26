# exp_wiener.py
import socket, re
from math import isqrt
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util.number import long_to_bytes

HOST = "127.0.0.1"
PORT = 10003

pat_int = lambda k: re.compile(rf"^{k}\s*=\s*([0-9]+)\s*$")
pat_hex = lambda k: re.compile(rf"^{k}\s*=\s*([0-9a-fA-F]+)\s*$")

def recv_line(sock):
    buf = b''
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        if ch == b'\n':
            break
        buf += ch
    return buf.decode(errors='ignore')

def drain_to_menu(sock):
    while True:
        line = recv_line(sock)
        if not line:
            break
        if line.startswith("Menu:"):
            _ = recv_line(sock); _ = recv_line(sock)
            return

def aes_cbc_dec(key_bytes, iv, ct):
    aes = AES.new(key_bytes, AES.MODE_CBC, iv)
    return unpad(aes.decrypt(ct), 16)

# ---- Wiener helpers ----
def cont_frac(num, den):
    while den:
        a = num // den
        yield a
        num, den = den, num - a * den

def convs(cf):
    n1, n2 = 1, 0
    d1, d2 = 0, 1
    for a in cf:
        n = a * n1 + n2
        d = a * d1 + d2
        yield (n, d)
        n2, n1 = n1, n
        d2, d1 = d1, d

def wiener_attack(e, N):
    for (k, d) in convs(cont_frac(e, N)):
        if k == 0: continue
        if (e*d - 1) % k != 0: continue
        phi = (e*d - 1)//k
        s = N - phi + 1
        D = s*s - 4*N
        if D < 0: continue
        r = isqrt(D)
        if r*r != D: continue
        p = (s + r)//2
        q = (s - r)//2
        if p*q == N and p>1 and q>1:
            return d
    return None

def main():
    with socket.create_connection((HOST, PORT)) as s:
        recv_line(s)
        drain_to_menu(s)
        s.sendall(b"2\n")

        int_fields = ["N","e1","e2","C_secret","C_secret_e2"]
        hex_fields = ["IV","C_flag"]
        int_re = { k: pat_int(k) for k in int_fields }
        hex_re = { k: pat_hex(k) for k in hex_fields }
        vals = {}

        for _ in range(50):
            line = recv_line(s)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            for k, rgx in int_re.items():
                m = rgx.match(line)
                if m:
                    vals[k] = int(m.group(1))
            for k, rgx in hex_re.items():
                m = rgx.match(line)
                if m:
                    vals[k] = bytes.fromhex(m.group(1))
            if ("N" in vals) and ("e2" in vals) and (("C_secret" in vals) or ("C_secret_e2" in vals)) and ("IV" in vals) and ("C_flag" in vals):
                break

        if "C_secret" in vals:
            Csec = vals["C_secret"]
        elif "C_secret_e2" in vals:
            Csec = vals["C_secret_e2"]
        else:
            raise RuntimeError("parse failed: no C_secret(_e2)")

        N, e2 = vals.get("N"), vals.get("e2")
        iv, Cfg = vals.get("IV"), vals.get("C_flag")
        if not (N and e2 and Csec and iv and Cfg):
            raise RuntimeError("parse failed: missing fields")

        d2 = wiener_attack(e2, N)
        if d2 is None:
            raise RuntimeError("Wiener 失败：当前 (N,e2) 可能不满足小私钥条件。")

        m_secret = pow(Csec, d2, N)
        key = sha256(long_to_bytes(m_secret)).d_
