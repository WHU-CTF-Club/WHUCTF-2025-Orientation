from Crypto.Util.number import long_to_bytes
import random
from math import gcd

n = 296479844664272841387463850582243657126828119747349973346435535648935441635465312810350497483607049970085821956459661662692973319981396328779513620912107583819415692221101105411336391873306912120452454317542084369771744217331963232299212065242041156272129073540110780668196425201679950044385685445679846778347
c = 84692924424159029375705037275007001388172414239834582135000648750992548456871496822136727956597690220702213262902037504593911233438610748485090479193684709027884736254799368870937838753469541811262496061040057267610870764568322699040382946018900707992153960423862612887710459195256776757044417009782938361082
gift = 21421603276242590809123617511450570837337402206836779981567079352993366015619163071408369108635441638538232684908091184725983048794325905048688959817124356500295224735311794477563728619181884259535337568018718855239555955087561894469863548151643792685740640226748588714507816988356674222578609651565533919716
p = 19687580167348054419037621751763141888090639359076710032957467670232934720884909706272293092928808749415015253610630577924280596873216734673292634004736001
q = 15059232376154895735979796718643246692443454923212544002237091308226990672034157655825730825874336047961590285972788514713569522439537524000069100107386347
e = 809  # = 2 * 3 * 11 * 17

def factor_small(n: int):
    res = {}
    d = 2
    m = n
    while d * d <= m:
        while m % d == 0:
            res[d] = res.get(d, 0) + 1
            m //= d
        d += 1 if d == 2 else 2  # 小优化：除2之后只试奇数
    if m > 1:
        res[m] = res.get(m, 0) + 1
    return res  # dict: prime -> exponent

# valuation w.r.t. prime r
def v_p(n: int, r: int) -> int:
    cnt = 0
    while n % r == 0:
        n //= r
        cnt += 1
    return cnt

# 找到阶**恰为 e**的 e 次单位根生成元 z （在 F_p* 中）
def find_z_exact_order_e(p: int, e: int, e_primes):
    exp = (p - 1) // e
    while True:
        a = random.randrange(2, p - 1)
        z = pow(a, exp, p)
        if z == 1:
            continue
        if pow(z, e, p) != 1:
            continue
        ok = True
        for r in e_primes:
            if pow(z, e // r, p) == 1:
                ok = False
                break
        if ok:
            return z

# 在模素数 p 下求 c 的所有 e 次根（兼容复合 e）
def e_th_roots_mod_prime(c_mod_p: int, e: int, p: int):
    # 1) 剥离 e 的所有素因子在 (p-1) 中的幂次 -> s 与 e 互素
    e_fac = factor_small(e)
    g = 1
    for r in e_fac.keys():
        g *= r ** v_p(p - 1, r)
    s = (p - 1) // g
    # 保证 gcd(e, s) == 1
    assert gcd(e, s) == 1

    # 2) 基根 m0 = c^{e^{-1} mod s} (mod p)
    d = pow(e, -1, s)
    m0 = pow(c_mod_p, d, p)

    # 3) 找生成元 z（阶恰为 e）
    z = find_z_exact_order_e(p, e, list(e_fac.keys()))

    # 4) 列出 e 条分支：m0 * z^i
    roots = []
    zpow = 1
    for _ in range(e):
        roots.append((m0 * zpow) % p)
        zpow = (zpow * z) % p
    return roots

# CRT 合并 ap (mod p) 与 aq (mod q)
inv_p_mod_q = pow(p, -1, q)
def crt_pq(ap: int, aq: int, p: int, q: int, n: int):
    return (ap + p * (((aq - ap) % q) * inv_p_mod_q % q)) % n

def solve():
    cp = c % p
    cq = c % q

    roots_p = e_th_roots_mod_prime(cp, e, p)
    roots_q = e_th_roots_mod_prime(cq, e, q)

    # 理论组合数 e^2 ≈ 1.26e6，双层循环即可
    for rp in roots_p:
        for rq in roots_q:
            m = crt_pq(rp, rq, p, q, n)
            b = long_to_bytes(m)
            if b.startswith(b'WHUCTF{') and b.endswith(b'}'):
                print(b.decode(errors="ignore"))
                return
    print("Flag not found")

if __name__ == "__main__":
    solve()
