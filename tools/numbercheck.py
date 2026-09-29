"""Numbers check for a chapter: expected enemy stats and a combat matrix against the player units.

Reads the *built* ROM (character, class and item tables as they will be in game), parses the
chapter's UNIT lines, and prints, per enemy: expected stats (autolevel = class growths, like FE8
generics) and, against each player unit, damage dealt/taken, doubling and hit rates.
Usage: python3 tools/numbercheck.py build/BladeAndStone.gba src/Events/Prologue.event
"""
import os, re, struct, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
CHARS, CLASSES, ITEMS = 0x803D30, 0x807110, 0x809B10
STATS = ["hp", "pow", "skl", "spd", "def", "res", "lck"]
HIDDEN_PROMOTED = 10


def defines():
    d = {}
    src = os.path.join(ROOT, "engine/Tools/EventAssembler/EA Standard Library/FE8 Definitions.txt")
    for path in (src, os.path.join(ROOT, "gen/CastDefs.event")):
        for m in re.finditer(r"#define\s+(\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", open(path, errors="replace").read()):
            d[m.group(1)] = int(m.group(2), 0)
    return d


def ev(expr, d, local):
    expr = expr.strip()
    for k in (local, d):
        if expr in k:
            return k[expr]
    return int(expr, 0)


class Rom:
    def __init__(self, path):
        self.d = open(path, "rb").read()

    def char(self, pid):
        o = CHARS + pid * 52
        b = struct.unpack_from("<8b", self.d, o + 0x0C)
        return dict(zip(STATS[:6] + ["lck", "con"], b)), self.d[o + 5]

    def cls(self, c):
        o = CLASSES + c * 84
        b = struct.unpack_from("<8b", self.d, o + 0x0B)       # hp pow skl spd def res con mov
        g = struct.unpack_from("<7b", self.d, o + 0x1B)
        base = dict(zip(["hp", "pow", "skl", "spd", "def", "res", "con", "mov"], b)); base["lck"] = 0
        return base, dict(zip(STATS, g))

    def item(self, i):
        o = ITEMS + i * 36
        mt, hit, wt, crit = self.d[o + 0x15], self.d[o + 0x16], self.d[o + 0x17], self.d[o + 0x18]
        rng = self.d[o + 0x19]
        attr = struct.unpack_from("<I", self.d, o + 8)[0]
        return dict(mt=mt, hit=hit, wt=wt, crit=crit, rmin=rng >> 4, rmax=rng & 15, magic=bool(attr & 0x42), type=self.d[o + 7])


def stats(rom, pid, cls, lvl, auto):
    cb, cg = rom.cls(cls)
    pb, _ = rom.char(pid)
    s = {k: cb.get(k, 0) + pb.get(k, 0) for k in STATS}
    s["con"] = cb["con"] + pb["con"]
    if auto:
        promoted = struct.unpack_from("<I", rom.d, CLASSES + cls * 84 + 0x28)[0] & 0x100
        levels = lvl - 1 + (HIDDEN_PROMOTED if promoted else 0)   # C-SkillSys hidden levels (measured in RAM)
        for k in STATS:
            s[k] += cg[k] * levels / 100.0
    return {k: round(v) for k, v in s.items()}


def main(rom_path, event_path):
    rom = Rom(rom_path)
    d = defines()
    text = open(event_path).read()
    local = {m.group(1): m.group(2) for m in re.finditer(r"#define\s+(\w+)\s+(\S+)", text)}
    local = {k: (ev(v, d, {}) if re.match(r"^(0x[0-9A-Fa-f]+|\d+)$", v) or v in d else v) for k, v in local.items()}
    local = {k: v for k, v in local.items() if isinstance(v, int)}
    units = {"Ally": [], "Enemy": []}
    rx = re.compile(r"^UNIT\s+(\S+)\s+(\S+)\s+\S+\s+Level\(([^,]+),\s*(Ally|Enemy|NPC),\s*(True|False)\)\s+\[(\d+),(\d+)\]\s+\S+\s+\S+\s+\S+\s+\S+\s+\[([^\]]*)\]\s*(\S*)", re.M)
    section = None
    for line in text.splitlines():
        if re.match(r"^\w+:\s*$", line):
            section = line.strip()[:-1]
        m = rx.match(line.strip())
        if not m or "DEBUG" in (section or ""):
            continue
        pid, cls, lvl = (ev(m.group(i), d, local) for i in (1, 2, 3))
        items = [ev(x, d, local) for x in m.group(8).split(",") if x.strip() not in ("0", "")]
        s = stats(rom, pid, cls, lvl, m.group(5) == "True")
        w = next((rom.item(i) for i in items if rom.item(i)["mt"] > 0 and rom.item(i)["type"] not in (4, 9)), None)
        units.setdefault(m.group(4), []).append(dict(sec=section, pid=pid, cls=cls, lvl=lvl, x=int(m.group(6)), y=int(m.group(7)), s=s, w=w, ai=m.group(9)))
    names = {v: k for k, v in d.items() if k.startswith("BS_PID_")}
    players = [u for u in units["Ally"] if u["sec"] and "Reinf" not in u["sec"]]
    seen, uniq = set(), []
    for p in players:
        if p["pid"] not in seen:
            seen.add(p["pid"]); uniq.append(p)
    players = uniq

    def atk(a, b):
        w = a["w"]
        if not w:
            return 0, 0, False
        power = a["s"]["pow"] + w["mt"]
        dmg = max(0, power - (b["s"]["res"] if w["magic"] else b["s"]["def"]))
        as_a = a["s"]["spd"] - max(0, w["wt"] - a["s"]["con"])
        wb = b["w"] or dict(wt=0)
        as_b = b["s"]["spd"] - max(0, wb["wt"] - b["s"]["con"])
        hit = a["s"]["skl"] * 2 + a["s"]["lck"] // 2 + w["hit"] - (as_b * 2 + b["s"]["lck"])
        return dmg, max(0, min(100, hit)), as_a - as_b >= 4

    print("%-24s %4s %4s %4s %4s %4s %4s  weapon" % ("enemy", "HP", "Atk", "Skl", "Spd", "Def", "Res"))
    for e in units["Enemy"]:
        w = e["w"]
        print("%-24s %4d %4d %4d %4d %4d %4d  mt%s  L%d class 0x%02X @(%d,%d) %s [%s]" % (
            (names.get(e["pid"], "pid 0x%02X" % e["pid"]).replace("BS_PID_", "")[:12] + " " + (e["sec"] or ""))[:24],
            e["s"]["hp"], e["s"]["pow"] + (w["mt"] if w else 0), e["s"]["skl"], e["s"]["spd"], e["s"]["def"], e["s"]["res"],
            w["mt"] if w else "-", e["lvl"], e["cls"], e["x"], e["y"], e["ai"], e["sec"]))
        cells = []
        for p in players:
            t_dmg, t_hit, t_dbl = atk(e, p)
            g_dmg, g_hit, g_dbl = atk(p, e)
            rounds = "-" if g_dmg == 0 else "%d" % -(-e["s"]["hp"] // (g_dmg * (2 if g_dbl else 1)))
            cells.append("%s: takes %d%s@%d%%, deals %d%s@%d%% (%s rds)" % (
                names.get(p["pid"], "?").replace("BS_PID_", "")[:6], t_dmg, "x2" if t_dbl else "", t_hit,
                g_dmg, "x2" if g_dbl else "", g_hit, rounds))
        print("    " + " | ".join(cells))
    print("\nplayers:", ", ".join("%s HP%d Atk%d Def%d Spd%d" % (names.get(p["pid"], "?").replace("BS_PID_", ""), p["s"]["hp"],
          p["s"]["pow"] + (p["w"]["mt"] if p["w"] else 0), p["s"]["def"], p["s"]["spd"]) for p in players))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
