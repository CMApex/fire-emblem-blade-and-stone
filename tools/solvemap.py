"""Solve a map sketch and save maps_src/<name>.json (+ a preview PNG).
Usage: python3 tools/solvemap.py FE8.gba NAME CONFIG OBJ1 OBJ2 PAL SEED [WIDTH]
  e.g. python3 tools/solvemap.py roms/fe8u.gba prologue 3 1 0 2 9
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from mapgen import *

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
rom = Rom(sys.argv[1]); name = sys.argv[2]
cfg, obj1, obj2, pal, seed = (int(v, 0) for v in sys.argv[3:8])
width = int(sys.argv[8]) if len(sys.argv) > 8 else 400
model = Model(rom, cfg)
rows, pins, stamps, holes = parse_sketch(open(os.path.join(ROOT, "maps_src", name + ".sketch")).read())
pins = resolve_pins(model, pins, stamps, holes)
g, cost = beam(model, rows, pins, (), seed=seed, width=width)
json.dump({"tileset": {"obj1": obj1, "obj2": obj2, "pal": pal, "config": cfg}, "seed": seed, "grid": g},
          open(os.path.join(ROOT, "maps_src", name + ".json"), "w"))
ts = Tileset(rom, obj1, obj2, pal, cfg)
render_map(ts, g, scale=2, gridlines=True).save(os.path.join(ROOT, "maps_src", name + ".png"))
print("%s: cost %.1f" % (name, cost))
print(terrain_ascii(model, g))
