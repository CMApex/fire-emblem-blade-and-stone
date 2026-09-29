"""Start a new map in maps/ for Tiled.

  python3 tools/newmap.py NAME --from-vanilla CH
        copy vanilla FE8 chapter CH's map and tileset (CH is a chapter-table index, e.g. 0x0B)
  python3 tools/newmap.py NAME --blank W H --tileset-of CH
        a W x H map filled with the most common plains (or floor) tile of vanilla chapter CH's map, in CH's tileset

Then open maps/NAME.tmx in Tiled. See HACKING.md ("Adding a new map") for hooking it up to a chapter.
Add --rom PATH if your clean FE8 ROM isn't roms/fe8u.gba.
"""
import argparse, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fe8lib import Rom, Chapter, Tileset, TERRAIN, read_map
import tmx

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--from-vanilla", type=lambda s: int(s, 0), metavar="CH")
    ap.add_argument("--blank", nargs=2, type=int, metavar=("W", "H"))
    ap.add_argument("--tileset-of", type=lambda s: int(s, 0), metavar="CH")
    ap.add_argument("--rom", default=os.path.join(ROOT, "roms", "fe8u.gba"))
    ap.add_argument("--force", action="store_true", help="overwrite an existing map")
    a = ap.parse_args()
    if not a.name.replace("_", "").isalnum():
        sys.exit("newmap: use letters, digits and _ in the name (it becomes BS_MAP_TILESET_%s)" % a.name.upper())
    out = os.path.join(ROOT, "maps", a.name + ".tmx")
    if os.path.exists(out) and not a.force:
        sys.exit("newmap: %s already exists (use --force to overwrite)" % os.path.relpath(out, ROOT))
    rom = Rom(a.rom)
    src = a.from_vanilla if a.from_vanilla is not None else a.tileset_of
    if src is None or (a.from_vanilla is None) == (a.blank is None):
        sys.exit("newmap: use either --from-vanilla CH, or --blank W H --tileset-of CH")
    ch = Chapter(rom, src)
    ts = {"obj1": ch.obj1, "obj2": ch.obj2, "pal": ch.pal, "config": ch.config}
    w, h, grid = read_map(rom, ch.mapid)
    if a.blank:
        W, H = a.blank
        if W < 15 or H < 10:
            sys.exit("newmap: maps must be at least 15x10 (one screen)")
        terrain = Tileset(rom, ch.obj1, ch.obj2, ch.pal, ch.config).terrain
        counts = collections.Counter(m for row in grid for m in row).most_common()
        plains = [m for m, _ in counts if TERRAIN[terrain[m]] in ("Plains", "Floor")]
        fill = plains[0] if plains else counts[0][0]
        grid = [[fill] * W for _ in range(H)]
        note = "new %dx%d map in the tileset of vanilla chapter 0x%02X" % (W, H, src)
    else:
        note = "copied from vanilla chapter 0x%02X" % src
    tmx.write(out, grid, ts, note)
    print("newmap: wrote %s (%dx%d, %s)" % (os.path.relpath(out, ROOT), len(grid[0]), len(grid), note))
    os.execvp(sys.executable, [sys.executable, os.path.join(ROOT, "tools", "maptiles.py"), a.rom])


if __name__ == "__main__":
    main()
