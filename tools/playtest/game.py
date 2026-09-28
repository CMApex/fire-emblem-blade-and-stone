"""Interactive FE8 driver on top of gbarun (persistent emulator process).

g = Game(rom); g.press('A'); g.cursor(); g.units('blue'); g.move_cursor(x, y); g.shot('file.png')
"""
import os, struct, subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GBARUN = os.path.join(HERE, "gbarun", "gbarun")

BMST = 0x0202BCB0
PLAYST = 0x0202BCF0
ARRAYS = {"blue": (0x0202BE4C, 62), "red": (0x0202CFBC, 50), "green": (0x0202DDCC, 20)}
CHAR_BASE = 0x08803D30
MOVMAP = 0x0202E4E0


class Game:
    def __init__(self, rom, state=None, shotdir="/tmp/claude-0/game"):
        self.p = subprocess.Popen([GBARUN, rom, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.shotdir = shotdir
        os.makedirs(shotdir, exist_ok=True)
        self.n = 0
        self.log = []
        if state:
            self.cmd("load " + state)

    def cmd(self, line):
        self.p.stdin.write(line + "\nack\n")
        self.p.stdin.flush()
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise RuntimeError("emulator died")
            if l.strip() == "ACK":
                return out
            out.append(l.rstrip("\n"))

    def wait(self, n):
        self.cmd("wait %d" % n)

    def press(self, keys, after=10):
        self.cmd("press %s %d" % (keys, after))

    def hold(self, keys, n):
        self.cmd("hold %s %d" % (keys, n))

    def dump(self, addr, n):
        out = self.cmd("dump 0x%X %d" % (addr, n))
        return bytes.fromhex(out[-1].split()[1])

    def u8(self, a): return self.dump(a, 1)[0]
    def u16(self, a): return struct.unpack("<H", self.dump(a, 2))[0]
    def u32(self, a): return struct.unpack("<I", self.dump(a, 4))[0]

    def cursor(self):
        x, y = struct.unpack("<hh", self.dump(BMST + 0x14, 4))
        return x, y

    def turn(self):
        d = self.dump(PLAYST, 0x14)
        return struct.unpack_from("<H", d, 0x10)[0], d[0x0F]

    def units(self, side="blue"):
        base, n = ARRAYS[side]
        raw = self.dump(base, 0x48 * n)
        res = []
        for i in range(n):
            u = raw[i * 0x48:(i + 1) * 0x48]
            pchar = struct.unpack_from("<I", u, 0)[0]
            if not pchar:
                continue
            state = struct.unpack_from("<I", u, 0xC)[0]
            cid = (pchar - CHAR_BASE) // 52
            pclass = struct.unpack_from("<I", u, 4)[0]
            items = [struct.unpack_from("<H", u, 0x1E + 2 * k)[0] for k in range(5)]
            res.append(dict(slot=i, cid=cid, x=u[0x10], y=u[0x11], hp=u[0x13], maxhp=u[0x12], level=u[8],
                            state=state, dead=bool(state & 0x4), hidden=bool(state & 0x1),
                            acted=bool(state & 0x2), items=items, pclass=pclass))
        return res

    def move_cursor(self, x, y, maxsteps=60):
        for _ in range(maxsteps):
            cx, cy = self.cursor()
            if (cx, cy) == (x, y):
                return True
            keys = []
            if cx < x: keys.append("RIGHT")
            elif cx > x: keys.append("LEFT")
            if cy < y: keys.append("DOWN")
            elif cy > y: keys.append("UP")
            self.press("+".join(keys), 6)
        return self.cursor() == (x, y)

    def shot(self, label=""):
        f = os.path.join(self.shotdir, "%04d.png" % self.n)
        self.n += 1
        self.cmd("shot " + f)
        self.log.append((f, label))
        return f

    def save(self, path): self.cmd("save " + path)
    def load(self, path): self.cmd("load " + path)

    def sheet(self, out, files=None, cols=4):
        from PIL import ImageDraw
        items = files if files is not None else self.log
        if not items:
            return
        cols = min(cols, len(items))
        rows = (len(items) + cols - 1) // cols
        s = Image.new("RGB", (cols * 244, rows * 176), (60, 0, 60))
        d = ImageDraw.Draw(s)
        for i, (f, lab) in enumerate(items):
            x, y = (i % cols) * 244 + 2, (i // cols) * 176 + 2
            s.paste(Image.open(f), (x, y))
            d.text((x + 2, y + 161), lab, fill=(255, 255, 0))
        s.save(out)
        self.log = []

    def close(self):
        try:
            self.p.stdin.close(); self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def act(g, frm, to, choice="wait", label=""):
    """Select unit at frm, move to `to`, then pick a menu action.
    choice: 'wait' | 'first' (top option: Attack/Visit/Seize/Talk...) | int (DOWN presses from top)."""
    g.move_cursor(*frm); g.press("A", 20)
    g.move_cursor(*to); g.press("A", 30)
    g.shot(label + " menu")
    if choice == "wait":
        g.press("UP", 8); g.press("A", 40)
    elif choice == "first":
        g.press("A", 40)
    else:
        for _ in range(choice): g.press("DOWN", 8)
        g.press("A", 40)


def attack(g, frm, to, target_steps=0, label=""):
    """Move and attack: Attack -> first weapon -> target (RIGHT x steps) -> confirm."""
    act(g, frm, to, "first", label)
    g.press("A", 30)                 # weapon
    for _ in range(target_steps): g.press("RIGHT", 10)
    g.shot(label + " forecast")
    g.press("A", 60)                 # confirm
    for _ in range(40):              # battle anims + possible quotes/level ups
        g.wait(30)
        if g.turn()[1] == 0 and g.u8(0x03004E50) is not None:
            pass
    g.shot(label + " after")


def run_until_player(g, snap_every=240, maxframes=20000, label="ep"):
    """End of turn: spam B through enemy phase until player phase of a new turn."""
    t0 = g.turn()[0]
    f = 0
    while f < maxframes:
        g.press("B", 20); f += 30
        t, ph = g.turn()
        if f % snap_every < 30:
            g.shot("%s t%d ph%02X" % (label, t, ph))
        if t > t0 and ph == 0:
            for _ in range(6): g.press("B", 30)
            g.shot("%s player t%d" % (label, t))
            return True
    return False


def end_turn(g, empty):
    g.move_cursor(*empty); g.press("A", 30)
    g.press("UP", 8); g.press("A", 60)
