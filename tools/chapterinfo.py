"""Show what vanilla FE8 stores for a chapter-table entry: tileset, map slot, events slot, and so on.
New chapters reuse the slots of the vanilla chapter entry they replace (see HACKING.md, "Adding a chapter").
Usage: python3 tools/chapterinfo.py [FE8.gba] CH [CH...]     e.g.  python3 tools/chapterinfo.py 2 3
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fe8lib import Rom, Chapter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
args = sys.argv[1:]
rom_path = args.pop(0) if args and args[0].endswith(".gba") else os.path.join(ROOT, "roms", "fe8u.gba")
if not args:
    sys.exit(__doc__)
rom = Rom(rom_path)
for a in args:
    c = Chapter(rom, int(a, 0))
    print("chapter 0x%02X: tileset obj1 0x%02X obj2 0x%02X pal 0x%02X config 0x%02X | "
          "map slot 0x%02X, tile animations 0x%02X/0x%02X, map-changes slot 0x%02X, events slot 0x%02X"
          % (c.id, c.obj1, c.obj2, c.pal, c.config, c.mapid, c.anim1, c.anim2, c.mapchanges, c.eventsid))
