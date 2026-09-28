"""Compile maps_src/*.json into Maps/<name>_data.dmp (LZ77) and verify round-trip."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
from fe8lib import encode_map, lz77_compress, lz77_decompress

ROOT = os.path.join(os.path.dirname(__file__), "..")


def build(name):
    src = json.load(open(os.path.join(ROOT, "maps_src", name + ".json")))
    raw = encode_map(src["grid"])
    comp = lz77_compress(raw)
    back, _ = lz77_decompress(comp, 0)
    assert back == raw, "LZ77 round-trip failed for " + name
    out = os.path.join(ROOT, "Maps", "bs_" + name + "_data.dmp")
    open(out, "wb").write(comp)
    print("map %-10s %dx%d  raw %d -> lz %d bytes" % (name, len(src["grid"][0]), len(src["grid"]), len(raw), len(comp)))


if __name__ == "__main__":
    for f in sorted(glob.glob(os.path.join(ROOT, "maps_src", "*.json"))):
        build(os.path.splitext(os.path.basename(f))[0])
