"""Read and write the Tiled maps in maps/*.tmx.

A Blade & Stone map is a Tiled map (orthogonal, 16x16 tiles, fixed size) with:
  * map properties obj1, obj2, pal, config: the FE8 tileset (graphics, palette, metatile config),
    written as hex strings like "0x0E";
  * one tile layer (named "Map" by convention) whose tiles come from the generated tileset
    maps/tilesets/fe8_<obj1>_<obj2>_<pal>_<config>.tsx (1024 metatiles, 32 per row).
Any other layers (notes, object layers for planning unit positions...) are ignored by the build.
"""
import base64, gzip, os, re, struct, zlib
import xml.etree.ElementTree as ET

TILESET_KEYS = ("obj1", "obj2", "pal", "config")
FLIP_BITS = 0xE0000000


class MapError(Exception):
    pass


def tileset_name(ts):
    return "fe8_%02x_%02x_%02x_%02x" % tuple(ts[k] for k in TILESET_KEYS)


def _layer_values(layer, w, h, where):
    data = layer.find("data")
    if data is None:
        raise MapError("%s: layer %r has no data" % (where, layer.get("name")))
    if data.find("chunk") is not None:
        raise MapError("%s: this is an infinite map; untick Map > Map Properties > Infinite in Tiled" % where)
    enc, comp = data.get("encoding"), data.get("compression")
    if enc == "csv":
        vals = [int(v) for v in data.text.replace("\n", "").split(",") if v.strip()]
    elif enc == "base64":
        raw = base64.b64decode(data.text.strip())
        if comp == "zlib":
            raw = zlib.decompress(raw)
        elif comp == "gzip":
            raw = gzip.decompress(raw)
        elif comp:
            raise MapError("%s: tile layer compression %r isn't supported; use CSV (Map > Map Properties > "
                           "Tile Layer Format)" % (where, comp))
        vals = list(struct.unpack("<%dI" % (len(raw) // 4), raw))
    elif enc is None:
        vals = [int(t.get("gid", 0)) for t in data.findall("tile")]
    else:
        raise MapError("%s: unknown tile layer encoding %r" % (where, enc))
    if len(vals) != w * h:
        raise MapError("%s: layer %r has %d tiles, expected %dx%d" % (where, layer.get("name"), len(vals), w, h))
    return vals


def read(path):
    """-> dict(name, width, height, tileset={obj1..config}, grid=[[metatile]])"""
    where = os.path.relpath(path)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise MapError("%s: not valid XML (%s)" % (where, e))
    w, h = int(root.get("width")), int(root.get("height"))
    if int(root.get("tilewidth")) != 16 or int(root.get("tileheight")) != 16:
        raise MapError("%s: tiles must be 16x16" % where)
    props = {p.get("name"): p.get("value") for p in root.findall("./properties/property")}
    ts = {}
    for k in TILESET_KEYS:
        if k not in props:
            raise MapError("%s: missing map property %r (Map > Map Properties > Custom Properties)" % (where, k))
        ts[k] = int(props[k], 0)
    sets = root.findall("tileset")
    if len(sets) != 1:
        raise MapError("%s: a map must use exactly one tileset (the generated fe8_*.tsx), found %d" % (where, len(sets)))
    firstgid = int(sets[0].get("firstgid"))
    layers = root.findall("layer")
    layer = next((l for l in layers if l.get("name") == "Map"), layers[0] if len(layers) == 1 else None)
    if layer is None:
        raise MapError("%s: several tile layers and none is named 'Map'" % where)
    vals = _layer_values(layer, w, h, where)
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            g = vals[y * w + x]
            if g & FLIP_BITS:
                raise MapError("%s: tile at (%d,%d) is flipped or rotated; FE8 maps can't do that" % (where, x, y))
            if g == 0:
                raise MapError("%s: tile at (%d,%d) is empty; every tile must be painted" % (where, x, y))
            m = g - firstgid
            if not 0 <= m < 0x400:
                raise MapError("%s: tile at (%d,%d) isn't from the FE8 tileset" % (where, x, y))
            row.append(m)
        grid.append(row)
    return {"name": os.path.splitext(os.path.basename(path))[0], "width": w, "height": h,
            "tileset": ts, "grid": grid, "tileset_source": sets[0].get("source")}


def write(path, grid, ts, note=None):
    """Write a new .tmx (CSV layer) for grid using the generated tileset for ts."""
    h, w = len(grid), len(grid[0])
    rows = [",".join(str(m + 1) for m in r) for r in grid]
    csv = ",\n".join(rows)
    props = "".join('   <property name="%s" value="0x%02X"/>\n' % (k, ts[k]) for k in TILESET_KEYS)
    if note:
        props += '   <property name="note" value="%s"/>\n' % note.replace('"', "'")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<map version="1.8" tiledversion="1.8.2" orientation="orthogonal" renderorder="right-down" '
           'width="%d" height="%d" tilewidth="16" tileheight="16" infinite="0" nextlayerid="2" nextobjectid="1">\n'
           ' <properties>\n%s </properties>\n'
           ' <tileset firstgid="1" source="tilesets/%s.tsx"/>\n'
           ' <layer id="1" name="Map" width="%d" height="%d">\n'
           '  <data encoding="csv">\n%s\n</data>\n'
           ' </layer>\n'
           '</map>\n') % (w, h, props, tileset_name(ts), w, h, csv)
    open(path, "w", encoding="utf-8", newline="\n").write(xml)


def fix_tileset_source(path, ts):
    """Point the map's <tileset source> at the generated tileset matching its properties. Returns True if changed."""
    text = open(path, encoding="utf-8").read()
    want = "tilesets/%s.tsx" % tileset_name(ts)
    new = re.sub(r'(<tileset\s+firstgid="\d+"\s+source=")[^"]*(")', lambda m: m.group(1) + want + m.group(2), text, count=1)
    if new != text:
        open(path, "w", encoding="utf-8", newline="").write(new)
        return True
    return False
