"""Optional: generate a first draft of a map from an ASCII terrain sketch, as a Tiled map.

Reads maps/sketches/<name>.sketch and writes maps/<name>.tmx (+ maps/sketches/<name>.png preview).
This overwrites maps/<name>.tmx, so only use it to start a map; after that, edit the .tmx in Tiled.
Usage: python3 tools/solvemap.py FE8.gba NAME CONFIG OBJ1 OBJ2 PAL SEED [WIDTH]
  e.g. python3 tools/solvemap.py roms/fe8u.gba prologue 3 1 0 2 9   (how the Prologue draft was made)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from mapgen import *
import tmx

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
rom = Rom(sys.argv[1]); name = sys.argv[2]
cfg, obj1, obj2, pal, seed = (int(v, 0) for v in sys.argv[3:8])
width = int(sys.argv[8]) if len(sys.argv) > 8 else 400
model = Model(rom, cfg)
rows, pins, stamps, holes = parse_sketch(open(os.path.join(ROOT, "maps", "sketches", name + ".sketch")).read())
pins = resolve_pins(model, pins, stamps, holes)
g, cost = beam(model, rows, pins, (), seed=seed, width=width)
tmx.write(os.path.join(ROOT, "maps", name + ".tmx"), g, {"obj1": obj1, "obj2": obj2, "pal": pal, "config": cfg},
          "drafted by tools/solvemap.py from maps/sketches/%s.sketch (seed %d)" % (name, seed))
ts = Tileset(rom, obj1, obj2, pal, cfg)
render_map(ts, g, scale=2, gridlines=True).save(os.path.join(ROOT, "maps", "sketches", name + ".png"))
print("%s: cost %.1f" % (name, cost))
print(terrain_ascii(model, g))
