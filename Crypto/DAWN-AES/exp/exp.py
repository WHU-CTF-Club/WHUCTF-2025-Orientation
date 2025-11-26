
import socket
import ast
import sys

HOST = "127.0.0.1"
PORT = 9457

def pkcs7_pad(data: bytes, blocksize: int = 16) -> bytes:
    pad_len = blocksize - (len(data) % blocksize)
    if pad_len == 0:
        pad_len = blocksize
    return data + bytes([pad_len]) * pad_len

def pkcs7_unpad(data: bytes, blocksize: int = 16) -> bytes:
    if not data or len(data) % blocksize != 0:
        raise ValueError("Invalid PKCS#7 data length")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > blocksize:
        raise ValueError("Invalid PKCS#7 padding length")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Invalid PKCS#7 padding content")
    return data[:-pad_len]


def recv_until_has(sock: socket.socket, marker: bytes, timeout=5.0) -> bytes:
    sock.settimeout(timeout)
    buf = b""
    while marker not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf

def recv_line_after_marker(sock: socket.socket, marker: bytes, timeout=5.0) -> bytes:

    sock.settimeout(timeout)
    buf = recv_until_has(sock, marker, timeout=timeout)
    if marker not in buf:
        buf += sock.recv(4096)
        if marker not in buf:
            raise RuntimeError("marker not found in server output")
    post = buf.split(marker, 1)[1]
    while b"\n" not in post:
        chunk = sock.recv(4096)
        if not chunk:
            break
        post += chunk
    line = post.split(b"\n", 1)[0]
    return line

def parse_bytes_literal_from_line(line: bytes) -> bytes:
    s = line.strip().decode("latin1", errors="strict")
    b = ast.literal_eval(s)
    if not isinstance(b, (bytes, bytearray)):
        raise ValueError("parsed object is not bytes")
    return bytes(b)

def bxor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

def main():
    known_pt_raw = b"\x00" * 48
    known_pt_padded = pkcs7_pad(known_pt_raw, 16)

    # 连接服务端
    with socket.create_connection((HOST, PORT), timeout=5.0) as s:
        enc_flag_line = recv_line_after_marker(
            s, b"Here is your encrypted flag:"
        )
        enc_flag = parse_bytes_literal_from_line(enc_flag_line)

        if len(enc_flag) < 64:
            print(f"[!] Unexpected enc_flag length: {len(enc_flag)}", file=sys.stderr)

        hex_payload = known_pt_raw.hex().encode()  # 只发 48 字节，服务端会 pad 到 64

        s.sendall(hex_payload + b"\n")

        ct_line = recv_line_after_marker(
            s, b"Here is your ciphertext"
        )
        ct_known = parse_bytes_literal_from_line(ct_line)

        if len(ct_known) != len(pkcs7_pad(known_pt_raw, 16)):
            print(f"[!] Unexpected known ciphertext length: {len(ct_known)}", file=sys.stderr)

        # 还原密钥流
        keystream = bxor(ct_known, known_pt_padded)

        padded_flag = bxor(enc_flag[:len(keystream)], keystream[:len(enc_flag)])
        try:
            flag = pkcs7_unpad(padded_flag, 16)
        except Exception as e:
            print(f"[!] Unpad failed: {e}", file=sys.stderr)
            flag = padded_flag

        print("[+] enc_flag length:", len(enc_flag))
        print("[+] recovered padded_flag length:", len(padded_flag))
        print("[+] FLAG (bytes):", flag)
        try:
            print("[+] FLAG (utf-8):", flag.decode("utf-8"))
        except:
            pass

if __name__ == "__main__":
    main()

# WHUCTF{CRyP70GrapHY_DrEAm_IT5_DAwN_A3S55_SY573M}