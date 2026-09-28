"""Generate the Blade & Stone cast from data/cast.csv and the user's FE7/FE8 ROMs.

Veteran numbers (bible §13) are *derived*, not hand-typed: each character starts from their
canon bases/growths and walks the path they'd have walked by the end of their game —
levels in their old class, a promotion (with that class's promotion gains), then a few
levels in the promoted class — using expected values. The result is re-based onto the
FE8 class they now use. STR/MAG is split for C-SkillSys. Growths are scaled down for
veterans (they don't grow fast any more); the growing four keep canon growths.

Outputs (all under gen/, never committed — derived from the user's ROMs):
  gen/Characters.event        character table entries (ORG into the vanilla table)
  gen/CastDefs.event          #define BS_PID_<KEY>
  gen/cast_text.txt           names/descriptions for characters without hand-written ones
  gen/engine/...              C tables for the engine: personal skills, personal magic, learnsets
  gen/cast_report.md          human-readable stat sheet (for balancing)

Usage: python3 tools/gencast.py FE8.gba FE7.gba
"""
import csv, os, re, struct, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from fe7text import TextDecoder

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
GEN = os.path.join(ROOT, "gen")
ENGINE = os.path.join(ROOT, "engine")

FE8_CHARS, FE8_CLASSES = 0x803D30, 0x807110
FE7_CHARS, FE7_CLASSES = 0xBDCE18, 0xBE015C
CHAR_SZ, CLASS_SZ = 52, 84

CA_PROMOTED, CA_LORD, CA_FEMALE, CA_MAXLEVEL10 = 1 << 8, 1 << 13, 1 << 14, 1 << 19

WTYPES = ["Sword", "Lance", "Axe", "Bow", "Staff", "Anima", "Light", "Dark"]
RANK = {"E": 1, "D": 31, "C": 71, "B": 121, "A": 181, "S": 251}
RANK_NAME = [(251, "S"), (181, "A"), (121, "B"), (71, "C"), (31, "D"), (1, "E")]

# FE8 classes whose "power" is magic (tomes/staves)
MAGIC_CLASSES = {0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32,
                 0x39, 0x3E, 0x7F, 0x44, 0x45, 0x4A, 0x4B, 0x4C, 0x4F}
FE7_FEMALE = {"Lyn", "Serra", "Rebecca", "Ninian", "Florina", "Nino", "Priscilla", "Louise", "Isadora",
              "Karla", "Fiora", "Farina", "Vaida"}
VETERAN_GROWTH = 0.6          # veterans keep 60% of canon growths

# New Blade & Stone classes: FE7 stat block, FE8 clone for everything else (see gen/Classes.event)
NEW_CLASSES = {
    # id: (label, FE7 promoted class, FE8 class to clone, name msg, desc msg, extra attributes)
    0x77: ("Knight Lord", 0x07, 0x07, "BS_ClassKnightLord", "BS_ClassKnightLordDesc", CA_LORD | CA_PROMOTED),
    0x78: ("Great Lord (Hector)", 0x09, 0x11, "BS_ClassGreatLordH", "BS_ClassGreatLordHDesc", CA_LORD | CA_PROMOTED),
    0x79: ("Blade Lord", 0x08, 0x16, "BS_ClassBladeLord", "BS_ClassBladeLordDesc", CA_LORD | CA_PROMOTED | CA_FEMALE),
}


def rd(path):
    return open(path, "rb").read()


class Cls:
    """One class entry (FE7 and FE8 share the 84-byte layout)."""
    def __init__(self, data, table, cid):
        o = table + cid * CLASS_SZ
        self.raw = bytes(data[o:o + CLASS_SZ])
        self.id = cid
        self.promotes_to = data[o + 5]
        b = data[o + 0x0B:o + 0x13]           # hp pow skl spd def res con mov
        self.base = {"hp": b[0], "pow": b[1], "skl": b[2], "spd": b[3], "def": b[4], "res": b[5], "lck": 0, "con": b[6]}
        self.mov = b[7]
        c = data[o + 0x13:o + 0x1A]
        self.cap = {"hp": c[0], "pow": c[1], "skl": c[2], "spd": c[3], "def": c[4], "res": c[5], "lck": 30, "con": c[6]}
        p = data[o + 0x22:o + 0x28]
        self.promo = {"hp": p[0], "pow": p[1], "skl": p[2], "spd": p[3], "def": p[4], "res": p[5], "lck": 0, "con": 0}
        self.attr = struct.unpack_from("<I", data, o + 0x28)[0]
        self.ranks = list(data[o + 0x2C:o + 0x34])

    @property
    def promoted(self):
        return bool(self.attr & CA_PROMOTED)

    @property
    def trainee(self):
        return bool(self.attr & CA_MAXLEVEL10)


STATS = ["hp", "pow", "skl", "spd", "def", "res", "lck"]


class Char:
    def __init__(self, data, table, pid):
        o = table + pid * CHAR_SZ
        self.raw = bytes(data[o:o + CHAR_SZ])
        self.name_id, self.desc_id = struct.unpack_from("<HH", data, o)
        self.cls = data[o + 5]
        self.face = struct.unpack_from("<H", data, o + 6)[0]
        self.mini, self.affinity = data[o + 8], data[o + 9]
        self.level = data[o + 0x0B]
        b = struct.unpack_from("<8b", data, o + 0x0C)  # hp pow skl spd def res lck con
        self.base = dict(zip(["hp", "pow", "skl", "spd", "def", "res", "lck", "con"], b))
        self.ranks = list(data[o + 0x14:o + 0x1C])
        g = data[o + 0x1C:o + 0x23]
        self.growth = dict(zip(STATS, g))
        self.attr = struct.unpack_from("<I", data, o + 0x28)[0]


def engine_head(path):
    """Engine file as committed at the pinned commit (so regeneration never compounds)."""
    return subprocess.run(["git", "-C", ENGINE, "show", "HEAD:" + path], capture_output=True, text=True, check=True).stdout


def job_magic():
    """Parse the engine's gMagicJInfos (class magic base/growth/cap/bonus) by class constant name."""
    src = engine_head("Data/StrMag/Source/JobMagicInfo.c")
    consts = {}
    for m in re.finditer(r"(CLASS_\w+)\s*=\s*(0x[0-9A-Fa-f]+)",
                         open(os.path.join(ENGINE, "Tools/FE-CLib-Mokha/include/constants/classes.h")).read()):
        consts[m.group(1)] = int(m.group(2), 16)
    out = {}
    for m in re.finditer(r"\[(CLASS_\w+)\]\s*=\s*\{([^}]*)\}", src):
        f = dict(re.findall(r"\.(\w+)\s*=\s*(-?\d+)", m.group(2)))
        out[consts[m.group(1)]] = {k: int(v) for k, v in f.items()}
    return out, src


def walk(ch, src_classes, dst_classes, src_is_fe7, target, lt):
    """Expected totals after the character's path. Returns (totals, description)."""
    c0 = src_classes[ch.cls]
    tot = {k: c0.base.get(k, 0) + ch.base[k] for k in ch.base}
    lv, path = ch.level, []

    def gain(n, label):
        nonlocal lv
        if n <= 0:
            return
        for k in STATS:
            tot[k] += ch.growth[k] * n / 100.0
        path.append("+%d lv %s" % (n, label))
        lv += n

    def promote(cls, label):
        for k in STATS:
            tot[k] += cls.promo[k]
        path.append("promote -> %s" % label)

    dst = dst_classes[target]
    if c0.trainee:
        gain(10 - ch.level, "trainee")
        promote(dst, "0x%02X" % target)
        gain(lt - 1, "new class")
    elif not c0.promoted and dst.promoted:
        gain(20 - ch.level, "base class")
        if src_is_fe7:
            promote(src_classes[c0.promotes_to], "FE7 0x%02X" % c0.promotes_to)
        else:
            promote(dst, "0x%02X" % target)
        gain(lt - 1, "promoted")
    else:
        gain(lt - ch.level, "same tier")
    return tot, ", ".join(path) or "as canon"


def main(fe8_path, fe7_path):
    d8, d7 = rd(fe8_path), rd(fe7_path)
    t7 = TextDecoder(d7, 0x6B8, 0x6BC, 0xB808AC)
    c8 = {i: Cls(d8, FE8_CLASSES, i) for i in range(0x80)}
    c7 = {i: Cls(d7, FE7_CLASSES, i) for i in range(0x48)}
    # new classes take their stat block from FE7
    for cid, (label, fe7c, clone, *_rest) in NEW_CLASSES.items():
        k = Cls(d8, FE8_CLASSES, clone)
        f = c7[fe7c]
        k.id, k.base, k.cap, k.promo, k.mov = cid, dict(f.base), dict(f.cap), dict(f.promo), f.mov
        k.attr = k.attr | NEW_CLASSES[cid][5]
        c8[cid] = k
    jmag, jmag_src = job_magic()
    for cid, (label, fe7c, clone, *_r) in NEW_CLASSES.items():
        jmag[cid] = dict(jmag.get(clone, {"base": 0, "growth": 5, "cap": 20, "bonus": 0}))

    faces = {}
    fd = os.path.join(GEN, "FE7FaceDefs.event")
    for m in re.finditer(r"#define BS_FACE_(\w+) (0x[0-9A-F]+)", open(fd).read()):
        faces[m.group(1)] = m.group(0).split()[1]

    manual_text = ""
    for fn in os.listdir(os.path.join(ROOT, "src", "Text")):
        manual_text += open(os.path.join(ROOT, "src", "Text", fn), encoding="utf-8").read()

    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cast.csv")))]
    ev = ["// generated by tools/gencast.py from data/cast.csv — do not edit", "PUSH"]
    defs = ["// generated by tools/gencast.py — character IDs"]
    text = ["// generated by tools/gencast.py — placeholder names/descriptions from canon (rewrite in src/Text)"]
    person_skills, pmag, report = [], [], []
    report.append("| pid | who | class | Lv | HP | Str | Mag | Skl | Spd | Lck | Def | Res | Con | growths (HP/Str/Mag/Skl/Spd/Lck/Def/Res) | path |")
    report.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    seen = set()
    for r in rows:
        pid, key, game = int(r["pid"], 16), r["key"], r["game"]
        assert pid not in seen, "duplicate pid %s" % r["pid"]
        seen.add(pid)
        assert 0 < pid < 0x60 and not (0x3B <= pid <= 0x3F), "%s: pid 0x%02X is reserved" % (key, pid)
        if r["tier"] == "core":
            assert pid < 0x33, "%s: Core characters must have pid < 0x33 (C-SkillSys BWL limit)" % key
        is7 = game == "fe7"
        src = int(r["src"], 16)
        ch = Char(d7 if is7 else d8, FE7_CHARS if is7 else FE8_CHARS, src)
        target, lt = int(r["class"], 16), int(r["level"])
        dst = c8[target]
        growing = "growing" in r["notes"]
        tot, path = walk(ch, c7 if is7 else c8, c8, is7, target, lt)
        tot = {k: round(v) for k, v in tot.items()}
        magical = target in MAGIC_CLASSES
        jm = jmag.get(target, {"base": 0, "growth": 5, "cap": 20})
        # STR/MAG split: canon "power" becomes magic for casters
        if magical:
            mag_tot = tot["pow"]
            str_tot = dst.base["pow"] + max(1, round(mag_tot * 0.2))
            mag_g, str_g = ch.growth["pow"], 15
        else:
            str_tot = tot["pow"]
            mag_tot = jm["base"] + (2 if not growing else 1)
            mag_g, str_g = 10, ch.growth["pow"]
        tot["pow"] = str_tot
        # clamp to caps
        for k in ["hp", "pow", "skl", "spd", "def", "res", "lck"]:
            tot[k] = min(tot[k], dst.cap[k] if k != "lck" else 30)
        mag_tot = min(mag_tot, jm.get("cap", 20) or 20)
        # personal = total - new class base
        pers = {k: tot[k] - dst.base.get(k, 0) for k in STATS}
        pers["con"] = (ch.base["con"] + (c7 if is7 else c8)[ch.cls].base["con"]) - dst.base["con"]
        pmag_base = mag_tot - jm["base"]
        scale = 1.0 if growing else VETERAN_GROWTH
        g = dict(ch.growth)
        g["pow"] = str_g
        gs = {k: int(round(g[k] * scale / 5.0) * 5) for k in STATS}
        mg = int(round(mag_g * scale / 5.0) * 5)
        # weapon ranks
        ranks = [0] * 8
        if r["ranks"].strip():
            for tok in r["ranks"].split():
                w, lvl = tok.split(":")
                ranks[WTYPES.index(w)] = RANK[lvl]
        else:
            ranks = list(ch.ranks)
        # identity
        if is7:
            name = "BS_Name_" + key
            desc = "BS_Desc_" + key
            if "## " + name not in manual_text:
                text += ["## " + name, t7.decode(ch.name_id).rstrip("\x00") + "[X]", ""]
            if "## " + desc not in manual_text:
                raw = t7.decode(ch.desc_id).rstrip("\x00")
                raw = re.sub(r"[^\x01\x20-\x7E]", "", raw).replace("\x01", "[NL]")
                text += ["## " + desc, raw + "[X]", ""]
            face = "BS_FACE_" + key.upper()
            assert key.upper() in faces, "no FE7 face for " + key
            mini, pal = 0, (0, 0)
            attrs = CA_FEMALE if key in FE7_FEMALE else 0
            visit = 0
        else:
            name, desc = "0x%X" % ch.name_id, "0x%X" % ch.desc_id
            face = "0x%X" % ch.face
            mini = ch.mini
            pal = (ch.raw[0x23], ch.raw[0x24])
            attrs = ch.attr
            visit = ch.raw[0x30]
        affinity = ch.affinity
        clamp = lambda v: max(-128, min(127, v))
        ev += ["",
               "// 0x%02X %s (%s 0x%02X) -> class 0x%02X Lv%d — %s" % (pid, key, game.upper(), src, target, lt, path),
               "ORG 0x%X" % (FE8_CHARS + pid * CHAR_SZ),
               "SHORT %s %s" % (name, desc),
               "BYTE 0x%02X 0x%02X" % (pid, target),
               "SHORT %s" % face,
               "BYTE 0x%02X 0x%02X 0x%02X %d" % (mini, affinity, pid, lt),
               "BYTE %s" % " ".join("0x%02X" % (clamp(pers[k]) & 0xFF) for k in ["hp", "pow", "skl", "spd", "def", "res", "lck", "con"]),
               "BYTE %s" % " ".join(str(v) for v in ranks),
               "BYTE %s" % " ".join(str(gs[k]) for k in STATS),
               "BYTE 0x%02X 0x%02X 0 0 0" % pal,
               "WORD 0x%X" % attrs,
               "WORD 0",                       # supports: authored later (vanilla lists use vanilla IDs)
               "BYTE 0x%02X 0 0 0" % visit]
        defs.append("#define BS_PID_%s 0x%02X" % (key.upper(), pid))
        defs.append("#define BS_LV_%s %d" % (key.upper(), lt))
        defs.append("#define BS_CLASS_%s 0x%02X" % (key.upper(), target))
        if r["skill"]:
            person_skills.append((pid, key, r["skill"]))
        pmag.append((pid, key, pmag_base, mg))
        rk = " ".join("%s %s" % (WTYPES[i], next(n for v, n in RANK_NAME if ranks[i] >= v)) for i in range(8) if ranks[i])
        report.append("| 0x%02X | %s | 0x%02X | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %s | %s; %s |" % (
            pid, key, target, lt, tot["hp"], tot["pow"], mag_tot, tot["skl"], tot["spd"], tot["lck"], tot["def"], tot["res"],
            dst.base["con"] + pers["con"], "/".join(str(x) for x in [gs["hp"], gs["pow"], mg, gs["skl"], gs["spd"], gs["lck"], gs["def"], gs["res"]]),
            path, rk))
    # --- NPCs, bosses and generics: explicit numbers from data/npcs.csv (no canon walk) ---
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "npcs.csv"))):
        pid, key = int(r["pid"], 16), r["key"]
        assert pid not in seen and pid >= 0x52 and not (0x3B <= pid <= 0x3F), "npc %s: bad pid" % key
        seen.add(pid)
        target = int(r["class"], 16)
        ranks = [0] * 8
        for tok in r["ranks"].split():
            w_, lvl = tok.split(":")
            ranks[WTYPES.index(w_)] = RANK[lvl]
        gr = [int(x) for x in r["growths"].split("/")]   # hp str mag skl spd lck def res
        attrs = (0x8000 if "boss" in r["attrs"] else 0) | (CA_FEMALE if "female" in r["attrs"] else 0)
        ev += ["", "// 0x%02X %s (NPC) — %s" % (pid, key, r["notes"]),
               "ORG 0x%X" % (FE8_CHARS + pid * CHAR_SZ),
               "SHORT %s %s" % (r["name"], r["desc"]),
               "BYTE 0x%02X 0x%02X" % (pid, target),
               "SHORT %s" % r["face"],
               "BYTE 0 0 0x%02X %s" % (pid, r["level"]),
               "BYTE %s" % " ".join(r[k] for k in ["hp", "str", "skl", "spd", "def", "res", "lck", "con"]),
               "BYTE %s" % " ".join(str(v) for v in ranks),
               "BYTE %d %d %d %d %d %d %d" % (gr[0], gr[1], gr[3], gr[4], gr[6], gr[7], gr[5]),
               "BYTE 0 0 0 0 0", "WORD 0x%X" % attrs, "WORD 0", "BYTE 0 0 0 0"]
        defs.append("#define BS_PID_%s 0x%02X" % (key.upper(), pid))
        pmag.append((pid, key, int(r["mag"]), gr[2]))
    ev.append("POP")

    os.makedirs(os.path.join(GEN, "engine/Data/SkillSys/Source"), exist_ok=True)
    os.makedirs(os.path.join(GEN, "engine/Data/StrMag/Source"), exist_ok=True)
    w = lambda p, s: open(os.path.join(GEN, p), "w", encoding="utf-8").write(s)
    w("Characters.event", "\n".join(ev) + "\n")
    w("CastDefs.event", "\n".join(defs) + "\n")
    w("cast_text.txt", "\n".join(text) + "\n")
    w("cast_report.md", "# Blade & Stone cast — generated stats\n\nTotals include class bases. "
      "Growths are after the veteran scale.\n\n" + "\n".join(report) + "\n")

    # --- engine C tables ---
    hdr = '#include "common-chax.h"\n#include "skill-system.h"\n#include "constants/skills.h"\n\n/* generated by tools/gencast.py — do not edit */\n'
    ps = [hdr, "const u16 gConstSkillTable_Person[0x100][2] = {"]
    for pid, key, sk in person_skills:
        ps.append("\t[0x%02X] = { SID_%s }, /* %s */" % (pid, sk, key))
    ps.append("};\n")
    w("engine/Data/SkillSys/Source/SkillTable-person.c", "\n".join(ps))
    gen_c = [hdr,
             "/* Learnsets: authored with the class-skill pass (bible §13). Empty until then. */",
             "const struct SkillPreloadPConf gSkillPreloadPData[0x100] = { };",
             "const struct SkillPreloadJConf gSkillPreloadJData[0x100] = { };", ""]
    w("engine/Data/SkillSys/Source/SkillTable-generic.c", "\n".join(gen_c))
    pm = ['#include "common-chax.h"\n#include "strmag.h"\n\n/* generated by tools/gencast.py — do not edit */\n',
          "const struct UnitMagicInfo gMagicPInfos[0x100] = {"]
    for pid, key, base, growth in pmag:
        pm.append("\t[0x%02X] = { .base = %d, .growth = %d }, /* %s */" % (pid, base, growth, key))
    pm.append("};\n")
    w("engine/Data/StrMag/Source/PersonMagicInfo.c", "\n".join(pm))
    # class magic for the new classes: engine table + our entries
    extra = "".join("\n\t[0x%02X] = { .base = %d, .growth = %d, .cap = %d, .bonus = %d }, /* %s (Blade & Stone) */" % (
        cid, jmag[cid]["base"], jmag[cid]["growth"], jmag[cid]["cap"], jmag[cid].get("bonus", 0), NEW_CLASSES[cid][0])
        for cid in NEW_CLASSES)
    i = jmag_src.rindex("};")
    w("engine/Data/StrMag/Source/JobMagicInfo.c", jmag_src[:i] + extra.lstrip("\n") + "\n" + jmag_src[i:])

    # --- new classes (stat block from FE7, rest cloned) ---
    cl = ["// generated by tools/gencast.py — Blade & Stone classes", "PUSH"]
    for cid, (label, fe7c, clone, nm, ds, extra_attr) in NEW_CLASSES.items():
        k = c8[cid]
        o = FE8_CLASSES + cid * CLASS_SZ
        b, c, p = k.base, k.cap, k.promo
        cl += ["", "// 0x%02X %s: FE7 class 0x%02X stats, cloned from FE8 class 0x%02X" % (cid, label, fe7c, clone),
               "ORG 0x%X" % o]
        raw = bytearray(c8[clone].raw) if False else bytearray(Cls(d8, FE8_CLASSES, clone).raw)
        struct.pack_into("<B", raw, 4, cid)
        raw[5] = 0
        raw[0x0B:0x13] = bytes([b["hp"], b["pow"], b["skl"], b["spd"], b["def"], b["res"], b["con"], k.mov])
        raw[0x13:0x1A] = bytes([c["hp"], c["pow"], c["skl"], c["spd"], c["def"], c["res"], c["con"]])
        raw[0x22:0x28] = bytes([p["hp"], p["pow"], p["skl"], p["spd"], p["def"], p["res"]])
        struct.pack_into("<I", raw, 0x28, k.attr)
        cl.append("SHORT %s %s" % (nm, ds))
        cl.append("BYTE " + " ".join("0x%02X" % x for x in raw[4:0x34]))
        cl.append("WORD " + " ".join("0x%08X" % struct.unpack_from("<I", raw, j)[0] for j in range(0x34, CLASS_SZ, 4)))
    for cid, (label, fe7c, clone, *_r) in NEW_CLASSES.items():   # moving map sprites (gMuInfoTable, by class-1)
        mu = d8[0x9A2E00 + (clone - 1) * 8: 0x9A2E00 + clone * 8]
        cl += ["ORG 0x%X  // MU for 0x%02X <- 0x%02X" % (0x9A2E00 + (cid - 1) * 8, cid, clone),
               "WORD 0x%08X 0x%08X" % struct.unpack("<II", mu)]
    cl.append("POP")
    w("Classes.event", "\n".join(cl) + "\n")
    print("cast: %d characters, %d personal skills, %d new classes" % (len(rows), len(person_skills), len(NEW_CLASSES)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
