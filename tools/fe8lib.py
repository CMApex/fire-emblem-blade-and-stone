"""fe8lib: helpers for reading FE8U (and FE7U) ROM data — LZ77, chapters, tilesets, maps, rendering."""
import struct
from PIL import Image

ROM_BASE = 0x08000000

TERRAIN = ["None", "Plains", "Road", "Village", "VillageC", "House", "Armory", "Vendor", "Arena", "CRoom",
           "Fort", "CastleGate", "Forest", "Thicket", "Sand", "Desert", "River", "Mountain", "Peak", "Bridge",
           "Bridge2", "Sea", "Lake", "Floor", "FloorM", "Fence", "Wall", "WallDmg", "Rubble", "Pillar", "Door",
           "Throne", "ChestE", "ChestF", "Roof", "Gate", "Church", "Ruins", "Cliff", "Ballista", "LBallista",
           "KBallista", "ShipFlat", "ShipWreck", "T2C", "Stairs", "T2E", "Glacier", "Arena2", "Valley", "Fence2",
           "Snag", "BridgeSnag", "Sky", "Deeps", "RuinsV", "Inn", "Barrel", "Bone", "Dark", "Water", "Gunnels",
           "Deck", "Brace", "Mast"]


class Rom:
    def __init__(self, path):
        self.data = bytearray(open(path, "rb").read())

    def u8(self, off):
        return self.data[off & 0x1FFFFFF]

    def u16(self, off):
        return struct.unpack_from("<H", self.data, off & 0x1FFFFFF)[0]

    def u32(self, off):
        return struct.unpack_from("<I", self.data, off & 0x1FFFFFF)[0]

    def ptr(self, off):
        p = self.u32(off)
        return p - ROM_BASE if ROM_BASE <= p < ROM_BASE + 0x2000000 else None

    def lz77(self, off):
        return lz77_decompress(self.data, off & 0x1FFFFFF)


def lz77_decompress(data, off):
    assert data[off] == 0x10, "not LZ77 at %X (%02X)" % (off, data[off])
    size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
    out = bytearray()
    p = off + 4
    while len(out) < size:
        flags = data[p]; p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[p], data[p + 1]; p += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[p]); p += 1
    return bytes(out[:size]), p - off


def lz77_compress(src):
    """Simple greedy LZ77 (GBA BIOS compatible, VRAM-safe: disp >= 2)."""
    src = bytes(src)
    out = bytearray([0x10, len(src) & 0xFF, (len(src) >> 8) & 0xFF, (len(src) >> 16) & 0xFF])
    i, n = 0, len(src)
    while i < n:
        flag_pos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_disp = 0, 0
            start = max(0, i - 0x1000)
            maxlen = min(18, n - i)
            j = i - 2
            while j >= start:
                l = 0
                while l < maxlen and src[j + l] == src[i + l]:
                    l += 1
                if l > best_len:
                    best_len, best_disp = l, i - j
                    if l == maxlen:
                        break
                j -= 1
            if best_len >= 3:
                d = best_disp - 1
                out.append(((best_len - 3) << 4) | (d >> 8)); out.append(d & 0xFF)
                flags |= 0x80 >> bit; i += best_len
            else:
                out.append(src[i]); i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def gba_color(c):
    r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
    return (r << 3 | r >> 2, g << 3 | g >> 2, b << 3 | b >> 2)


def read_palette(rom, off, count=16):
    return [gba_color(rom.u16(off + 2 * i)) for i in range(count)]


def decode_tile(gfx, idx):
    """Return 8x8 list of palette indices for 4bpp tile idx."""
    base = idx * 32
    t = gfx[base:base + 32]
    if len(t) < 32:
        return [[0] * 8 for _ in range(8)]
    return [[(t[y * 4 + x // 2] >> (4 * (x & 1))) & 0xF for x in range(8)] for y in range(8)]


FE8_CHAPTER_TABLE = 0x8B0890
FE8_CHAPTER_SIZE = 148
FE8_ASSET_TABLE = 0x8B363C


class Chapter:
    def __init__(self, rom, cid):
        base = FE8_CHAPTER_TABLE + cid * FE8_CHAPTER_SIZE
        self.id = cid
        self.obj1 = rom.u8(base + 4)
        self.obj2 = rom.u8(base + 5)
        self.pal = rom.u8(base + 6)
        self.config = rom.u8(base + 7)
        self.mapid = rom.u8(base + 8)
        self.anim1 = rom.u8(base + 9)
        self.anim2 = rom.u8(base + 10)
        self.mapchanges = rom.u8(base + 11)
        self.eventsid = rom.u8(base + 0x74)


def asset(rom, idx):
    return rom.ptr(FE8_ASSET_TABLE + 4 * idx)


class Tileset:
    """Decoded tileset: graphics, palettes, metatile config and terrain lookup."""
    def __init__(self, rom, obj1, obj2, pal, config):
        gfx = bytearray(0x800 * 32)
        g1, _ = rom.lz77(asset(rom, obj1))
        gfx[:len(g1)] = g1
        if obj2 and asset(rom, obj2):
            g2, _ = rom.lz77(asset(rom, obj2))
            gfx[0x200 * 32:0x200 * 32 + len(g2)] = g2
        self.gfx = bytes(gfx)
        poff = asset(rom, pal)
        self.palettes = [read_palette(rom, poff + 32 * i) for i in range(10)]
        cfg, _ = rom.lz77(asset(rom, config))
        self.meta = [struct.unpack_from("<4H", cfg, 8 * i) for i in range(0x400)]
        self.terrain = cfg[0x2000:0x2400]
        self._cache = {}

    def meta_image(self, m, fog=False):
        key = (m, fog)
        if key in self._cache:
            return self._cache[key]
        img = Image.new("RGB", (16, 16))
        px = img.load()
        for q, ent in enumerate(self.meta[m]):
            tile = ent & 0x3FF
            hf, vf = (ent >> 10) & 1, (ent >> 11) & 1
            p = (ent >> 12) & 0xF
            pal = self.palettes[min(9, p + (5 if fog else 0))]
            t = decode_tile(self.gfx, tile)
            ox, oy = (q & 1) * 8, (q >> 1) * 8
            for y in range(8):
                for x in range(8):
                    sx = 7 - x if hf else x
                    sy = 7 - y if vf else y
                    px[ox + x, oy + y] = pal[t[sy][sx]]
        self._cache[key] = img
        return img

    def sheet(self, cols=32, grid=False):
        """Render all 1024 metatiles into a 512x512 sheet (tmx-style)."""
        img = Image.new("RGB", (cols * 16, (0x400 // cols) * 16))
        for m in range(0x400):
            img.paste(self.meta_image(m), ((m % cols) * 16, (m // cols) * 16))
        return img


def tileset_for_chapter(rom, ch):
    return Tileset(rom, ch.obj1, ch.obj2, ch.pal, ch.config)


def read_map(rom, mapid):
    raw, _ = rom.lz77(asset(rom, mapid))
    w, h = raw[0], raw[1]
    vals = struct.unpack_from("<%dH" % (w * h), raw, 2)
    grid = [[vals[y * w + x] >> 2 for x in range(w)] for y in range(h)]
    return w, h, grid


def encode_map(grid):
    h, w = len(grid), len(grid[0])
    out = bytearray([w, h])
    for row in grid:
        for m in row:
            out += struct.pack("<H", m << 2)
    return bytes(out)


def render_map(ts, grid, scale=1, gridlines=False, labels=None):
    h, w = len(grid), len(grid[0])
    img = Image.new("RGB", (w * 16, h * 16))
    for y in range(h):
        for x in range(w):
            img.paste(ts.meta_image(grid[y][x]), (x * 16, y * 16))
    if gridlines or labels:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        if gridlines:
            for x in range(w):
                d.line([(x * 16, 0), (x * 16, h * 16)], fill=(0, 0, 0))
            for y in range(h):
                d.line([(0, y * 16), (w * 16, y * 16)], fill=(0, 0, 0))
        if labels:
            for (x, y), (txt, col) in labels.items():
                d.rectangle([x * 16 + 2, y * 16 + 2, x * 16 + 13, y * 16 + 13], outline=col)
                d.text((x * 16 + 4, y * 16 + 3), txt, fill=col)
    if scale != 1:
        img = img.resize((w * 16 * scale, h * 16 * scale), Image.NEAREST)
    return img
