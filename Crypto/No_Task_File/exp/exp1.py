from pwn import *
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes, inverse
import hashlib

def egcd(a, b):
    if a == 0:
        return b, 0, 1
    g, y, x = egcd(b % a, a)
    return g, x - (b // a) * y, y

def common_modulus_attack(c1, c2, e1, e2, n):
    g, a, b = egcd(e1, e2)
    assert g == 1, "gcd(e1, e2) != 1"

    if a < 0:
        c1 = inverse(c1, n)
        a = -a
    if b < 0:
        c2 = inverse(c2, n)
        b = -b

    m = (pow(c1, a, n) * pow(c2, b, n)) % n
    return m

def main():
    conn = remote('localhost', 64751)

    # Step 1: Read banner until prompt
    conn.recvuntil(b"Welcome to RSA Challenge")
    conn.recvuntil(b"[-] ")  # Wait for first prompt

    # Step 2: Send choice '2'
    conn.sendline(b"2")

    # Step 3: Parse response
    # Format:
    # N = ...
    # e1 = ...
    # e2 = ...
    # C_secret_e2 = ...
    # C_secret_e1 = ...
    # IV = ...
    # C_flag = ...

    n_line = conn.recvline().decode().strip()
    e1_line = conn.recvline().decode().strip()
    e2_line = conn.recvline().decode().strip()
    c2_line = conn.recvline().decode().strip()
    c1_line = conn.recvline().decode().strip()
    iv_line = conn.recvline().decode().strip()
    cflag_line = conn.recvline().decode().strip()

    # Parse values
    n = int(n_line.split("= ")[1])
    e1 = int(e1_line.split("= ")[1])
    e2 = int(e2_line.split("= ")[1])
    C_secret_e2 = int(c2_line.split("= ")[1])
    C_secret_e1 = int(c1_line.split("= ")[1])
    iv = bytes.fromhex(iv_line.split("= ")[1])
    cflag = bytes.fromhex(cflag_line.split("= ")[1])

    log.info(f"n = {n}")
    log.info(f"e1 = {e1}, e2 = {e2}")
    log.info(f"IV = {iv.hex()}")
    log.info(f"C_flag len = {len(cflag)}")

    # Step 4: Recover secret_int
    secret_int = common_modulus_attack(C_secret_e1, C_secret_e2, e1, e2, n)
    log.success(f"Recovered secret_int!")

    # Step 5: Derive key and decrypt
    aes_key = hashlib.sha256(long_to_bytes(secret_int)).digest()
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    padded_flag = cipher.decrypt(cflag)

    # Remove PKCS#7 padding
    pad_len = padded_flag[-1]
    if 1 <= pad_len <= 16:
        flag = padded_flag[:-pad_len]
    else:
        flag = padded_flag  # fallback

    log.success(f"Flag: {flag.decode()}")

    conn.close()

if __name__ == "__main__":
    main()