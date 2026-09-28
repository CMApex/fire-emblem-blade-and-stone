"""Extract the vanilla FE8 quote tables we extend (global entries only) into gen/."""
import os, struct, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
d = open(sys.argv[1], "rb").read()
out = os.path.join(ROOT, "gen")
# death quotes: 12-byte entries at 0x9ECD4C; keep chapter==0xFF (global) entries
o, keep = 0x9ECD4C, bytearray()
while True:
    pid, route, ch = struct.unpack_from("<HBB", d, o)
    if pid == 0xFFFF:
        break
    if ch == 0xFF:
        keep += d[o:o + 12]
    o += 12
keep += struct.pack("<HBBHHI", 0xFFFF, 0, 0, 0, 0, 0)
open(os.path.join(out, "vanilla_defeat.bin"), "wb").write(keep)
# battle quotes: 16-byte entries at 0x9EC6BC; keep chapter 0xFF / 0xFE entries
o, keep = 0x9EC6BC, bytearray()
while True:
    a, b, ch = struct.unpack_from("<HHH", d, o)
    if a == 0xFFFF:
        break
    if ch in (0xFF, 0xFE):
        keep += d[o:o + 16]
    o += 16
keep += struct.pack("<HHHHHHI", 0xFFFF, 0, 0, 0, 0, 0, 0)
open(os.path.join(out, "vanilla_battle.bin"), "wb").write(keep)
print("extracted quote tables")
