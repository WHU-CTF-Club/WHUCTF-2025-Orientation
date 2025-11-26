import os
import socketserver
from Crypto.Util.number import bytes_to_long, long_to_bytes, getPrime, inverse
from typing import Optional

# 从环境变量中导入flag，flag采用动态生成。
FLAG = os.getenv("GZCTF_FLAG")
# p1 = 9957067130325844661771676951799683243691455051257464585572795963404166418150160638368310360729364534185520209372731921422614390173737189271028807838074213
# q1 = 9761232651606259763457493867116443989171553327248270595346296533243151489194165522404231291263405459396823152220166621687410397118660487146724303142059457  
N1 = 97193248786772076344801478412942537580148582980635142502849444521067616803943312374593542468303690121283818440808583060605827280057328470704715539086624579353506968439306265441889950440990330700696735418764195482460721682726018404004671178467544602051380812232685706637938592325884948232685037532705624482341
# p2 = 8498606058512404215918853322794872546817585081829806868951124646248794818055642927161584186602060079600971640208568668398920829744906270789846026260908767
# q2 = 11611488687567169573903678949001767841730624375831644041403824272481683559664326576797286487164007633050655299763466807170465884984442105335327413065590033   
N2 = 98681468108506592379294575372927663776465559873444280174050907557247380322446296625524260310867571975542468727271645232447231072934655178774599560720646560318048392364066156261429607524258424971253985065807258673046250613385296577538038535633901733703822325326241267530175426971652335848071794501643637519311   
# p3 = 8423061434073349843491653162619230434885376528397788917861278346434256837095344818046305963166280983773478552699709615589652414284173169115553873849711671
# q3 = 12947941719703030447555253560603753244235408987620443880019793241087075729613068176101571310677174681779547183763797904768562683918219591586245176842390607
N3 = 109061308549859963194409679636266525492152165714143166006893920995498757015928402063669817304816119887402269132902649463362765731201815789814937012920324352108536834840133504502932634861668452657488201508113606850242047363631302345359669598035857257513438354439840940727208155406890550417658048109137308674297   

e1 = 59407   
e2 = 52387   

key = "just_do_it_without_d"  

# convert key plaintext to bytes
if isinstance(key, (bytes, bytearray)):
    key_bytes = bytes(key)
else:
    key_bytes = key.encode('utf-8')

Ns = [N1, N2, N3]

# ensure KEY_INT < Ni
KEY_INT = bytes_to_long(key_bytes)
if not all(KEY_INT < n for n in Ns):
    raise SystemExit("ERROR: KEY integer value must be smaller than all moduli Ni. Choose smaller KEY or larger moduli.")

# ensure gcd(e1,e2) == 1

# server slots: number 1 uses N1, number uses N2, number uses N3
SLOTS = {
    1: {"n": N1, "label": "number1"},
    2: {"n": N2, "label": "number2"},
    3: {"n": N3, "label": "number3"},
}

# 两轮加密使用的加密指数
ROUND_EXP = {1: e1, 2: e2} 

class ChallengeHandler(socketserver.BaseRequestHandler):
    def send(self, text: str, newline: bool = True):
        if isinstance(text, str):
            b = text.encode()
        else:
            b = text
        if newline:
            b += b"\n"
        try:
            self.request.sendall(b)
        except:
            pass

    def recvline(self, prompt: bytes = b"> "):
        try:
            self.request.sendall(prompt)
        except:
            pass
        data = b""
        try:
            while True:
                ch = self.request.recv(1)
                if not ch or ch == b"\n":
                    break
                data += ch
            return data.decode(errors="ignore").strip()
        except:
            return ""

    def handle(self):
        self.request.settimeout(120)
        try:
            self.send("Welcome to the challenge. You have 2 encryption rounds, then one submission round.")
            self.send("")
            self.send("Public moduli (N):")
            for idx in (1,2,3):
                self.send(f"  [{idx}] N = {SLOTS[idx]['n']}    ({SLOTS[idx]['label']})")
            self.send("")
            self.send("Note: The server will use exponent e1 for round 1 and e2 for round 2.")
            self.send("Exponents (e1,e2) will be revealed AFTER the two rounds finish.")
            self.send("")

            collected = []  

            # Two encryption rounds
            for round_no in (1, 2):
                self.send(f"--- Round {round_no} ---")
                choice = self.recvline(b"Choose number index (1-3): ")
                try:
                    idx = int(choice)
                except:
                    self.send("[-] invalid choice (not a number).")
                    continue
                if idx not in (1,2,3):
                    self.send("[-] invalid number index.")
                    continue

                # encrypt server-side KEY with that slot's modulus using this round's exponent
                n = SLOTS[idx]["n"]
                e = ROUND_EXP[round_no]
                # KEY_INT guaranteed < n earlier
                c = pow(KEY_INT, e, n)
                collected.append((round_no, idx, c))
                self.send(f"[+] Ciphertext (int) = {c}")
                self.send(f"[+] Used modulus N (number {idx}) = {n}")
                self.send(f"[+] Note: exponent e for this round will be revealed later.")
                self.send("")

            # After two rounds, reveal e1 and e2
            self.send("=== Rounds complete. Now revealing exponents ===")
            self.send(f"e1 = {e1}")
            self.send(f"e2 = {e2}")
            self.send("")

            # print what ciphertexts were given in the session
            self.send("Collected ciphertexts in your session:")
            for i, (r, sidx, cvalue) in enumerate(collected, 1):
                self.send(f" [{i}] round = {r} number = {sidx} c = {cvalue}")

            self.send("")
            # Submission round: now accept plaintext key (ASCII) from the player
            self.send("Now submit the recovered key as an ASCII string (exact plaintext).")
            submission = self.recvline(b"key_plain> ")
            if not submission:
                self.send("[-] No submission, bye.")
                return
            sub = submission.rstrip('\n')
            try:
                sub_bytes = sub.encode('utf-8')
            except Exception:
                self.send("[-] Submission encoding error.")
                return

            # compare exact bytes
            if sub_bytes == key_bytes:
                self.send("[+] Correct! Here is your flag:")
                try:
                    self.send(FLAG.decode())
                except:
                    self.send(str(FLAG))
            else:
                self.send("[-] Incorrect key.")
            self.send("bye!")
        except Exception as e:
            try:
                self.send(f"[-] Server error: {e}")
            except:
                pass
        finally:
            try:
                self.request.close()
            except:
                pass

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9999
    print(f"Listening on {HOST}:{PORT}")
    with ThreadedServer((HOST, PORT), ChallengeHandler) as server:
        server.serve_forever()
