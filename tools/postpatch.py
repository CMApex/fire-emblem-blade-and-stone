"""Post-link patches: write label addresses into ROM offsets that EA may not touch (engine-protected).

gen/postpatch.txt lines: "<rom offset> <label>" — the label's address comes from the EA symbol file.
Usage: python3 tools/postpatch.py ROM SYMFILE
"""
import os, struct, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
rom, sym = sys.argv[1], sys.argv[2]
syms = {}
for line in open(sym, errors="replace"):
    parts = line.split()
    if len(parts) >= 2:
        try:
            syms[parts[1]] = int(parts[0], 16)
        except ValueError:
            pass
d = bytearray(open(rom, "rb").read())
n = 0
for line in open(os.path.join(ROOT, "gen", "postpatch.txt")):
    if not line.strip():
        continue
    off, label = line.split()
    addr = syms[label] | 0x08000000
    struct.pack_into("<I", d, int(off, 16), addr)
    n += 1
open(rom, "wb").write(d)
print("postpatch: %d pointer(s) written" % n)
