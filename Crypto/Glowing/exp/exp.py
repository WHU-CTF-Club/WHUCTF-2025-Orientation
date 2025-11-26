import argparse
import socket
import re
from collections import Counter

def recv_blocks(host, port, timeout=10.0):
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    data = b""
    try:
        while True:
            chunk = s.recv(40960)
            if not chunk:
                break
            data += chunk
    finally:
        s.close()
    lines = data.decode(errors="ignore").splitlines()
    blocks = []
    pat = re.compile(r"Block\s+\d+\s*:\s*(0x[0-9a-fA-F]+)")
    for ln in lines:
        m = pat.search(ln)
        if m:
            x = int(m.group(1), 16)
            blen = (x.bit_length() + 7) // 8
            blocks.append(x.to_bytes(blen, "big"))
    return blocks

def printable(b): 
    return 32 <= b <= 126

def is_alpha(b):  
    return (65 <= b <= 90) or (97 <= b <= 122)

def freq_bonus(ch):
    # 给常见字符额外奖励，提升评分稳定性
    # 空格、字母最高；再是数字、逗号、点、冒号、分号、引号、下划线、感叹号、问号、括号、大括号等
    if ch == 0x20: return 4.0
    if 97 <= ch <= 122 or 65 <= ch <= 90: return 3.0
    if 48 <= ch <= 57: return 1.5
    if ch in b",.;:'\"-_!?#()/{}[]": return 1.2
    return 0.5  # 其他可打印

def decrypt_with_key(ct, key):
    L = min(len(ct), len(key))
    out = bytearray(L)
    for i in range(L):
        out[i] = ct[i] ^ key[i]
    return bytes(out)

# -------- 1) 空格启发初值 --------
def init_key_by_space(cts, alpha_threshold=0.6):
    max_len = max(len(c) for c in cts)
    key = bytearray([0] * max_len)
    known = [False] * max_len
    n = len(cts)
    for i, ci in enumerate(cts):
        for k in range(len(ci)):
            hits = 0
            total = 0
            for j, cj in enumerate(cts):
                if j == i: continue
                if k < len(cj):
                    total += 1
                    x = ci[k] ^ cj[k]
                    if is_alpha(x):
                        hits += 1
            if total and hits / total >= alpha_threshold:
                key[k] = ci[k] ^ 0x20
                known[k] = True
    return key, known

# -------- 2) 全局一致性评分（候选搜索） --------
def build_candidates_for_pos(cts, pos):
    # 候选集合：来自“空格候选 + 常见字符候选集”的并集
    cand = set()
    COMMON = b" etaoinshrdlcumwfgypbvkxjqzETAOINSHRDLCUMWFGYPBVKXJQZ"
    COMMON += b"0123456789,.;:'\"-_!?#()/{}[]"
    for ci in cts:
        if pos < len(ci):
            # 空格候选
            cand.add(ci[pos] ^ 0x20)
            # 常见字符候选
            for ch in COMMON:
                cand.add(ci[pos] ^ ch)
    return list(cand)

def score_key_byte(cts, pos, kb):
    # 该 kb 作为 key[pos] 时的全局得分：所有密文的该位解出后可打印 + 频率奖励
    score = 0.0
    for ci in cts:
        if pos < len(ci):
            ch = ci[pos] ^ kb
            if printable(ch):
                score += 1.0 + freq_bonus(ch)
            else:
                score -= 2.0  # 强惩罚不可打印
    return score

def global_refine_key(cts, key, known, iters=2):
    max_len = len(key)
    for _ in range(iters):
        changed = 0
        for pos in range(max_len):
            cands = build_candidates_for_pos(cts, pos)
            if not cands:
                continue
            best_k = key[pos]
            best_s = score_key_byte(cts, pos, best_k)
            for kb in cands:
                s = score_key_byte(cts, pos, kb)
                if s > best_s + 0.5:  # 需要超出一定 margin 才替换
                    best_s = s
                    best_k = kb
            if best_k != key[pos]:
                key[pos] = best_k
                known[pos] = True
                changed += 1
        if changed == 0:
            break
    return key, known

# -------- 3) 可选 crib 应用 --------
def apply_crib(cts, key, known, idx, offset, text):
    if idx < 0 or idx >= len(cts): return
    ct = cts[idx]
    bs = text.encode()
    for u, ch in enumerate(bs):
        p = offset + u
        if p < len(ct) and p < len(key):
            key[p] = ct[p] ^ ch
            known[p] = True

def main():
    ap = argparse.ArgumentParser(description="Robust many-time pad solver (空格启发 + 全局一致性评分 + 迭代收敛)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=6614)
    ap.add_argument("--alpha-threshold", type=float, default=0.60)
    ap.add_argument("--iters", type=int, default=2, help="全局细化迭代次数（默认2）")
    ap.add_argument("--crib", action="append", default=[], help='形如 idx:offset:"text" ，可多次使用')
    args = ap.parse_args()

    cts = recv_blocks(args.host, args.port)
    if not cts:
        print("[!] 没收到任何 Block")
        return

    lens = [len(c) for c in cts]
    print(f"[*] 收到 {len(cts)} 条密文，长度范围：{lens}")

    key, known = init_key_by_space(cts, args.alpha_threshold)
    # 全局细化
    key, known = global_refine_key(cts, key, known, iters=args.iters)

    # 可选 crib
    for item in args.crib:
        m = re.match(r'(\d+)\s*:\s*(\d+)\s*:\s*"(.*)"\s*$', item)
        if not m:
            print(f"[warn] 忽略非法 crib：{item}")
            continue
        idx = int(m.group(1)); off = int(m.group(2)); txt = m.group(3)
        apply_crib(cts, key, known, idx, off, txt)
        # crib 后再细化一轮，通常能级联提升
        key, known = global_refine_key(cts, key, known, iters=1)

    def show_char(k):
        return chr(k) if printable(k) else '*'
    flag_str = "".join(show_char(k) for k in key)
    known_cnt = sum(1 for v in known if v)
    print(f"[*] 已恢复 key 字节 {known_cnt}/{len(key)} ({known_cnt*100/len(key):.1f}%)")
    print(f"[*] 当前 flag 估计：{flag_str}")

    print("\n[+] 部分明文预览：")
    for i, ct in enumerate(cts):
        pt = decrypt_with_key(ct, key)
        shown = "".join(chr(b) if printable(b) else '.' for b in pt)
        print(f"  P[{i:02d}] {shown}")

    print('\n[hint] 若仍有个别符号错位，可试： --iters 3 或加一条小 crib，比如：')
    print('       --crib 0:0:"Afterglow "  或  --crib 0:6:" glow" 之类明显英文片段。')

if __name__ == "__main__":
    main()

# WHUCTF{We1com3_to_Crypto_Lets_Glowinggg_15b81fc963e1}