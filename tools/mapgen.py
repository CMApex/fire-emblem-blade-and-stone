"""mapgen: generate FE8 maps from an ASCII terrain sketch using adjacency learned from vanilla maps.

Sketch legend (one char per tile):
  .  plains      f  forest     t  thicket    m  mountain   ^  peak
  ~  sea         s  sand       r  road       w  river      c  cliff
  l  lake        =  bridge     ?  anything   #  ruins/rubble/wall (Ruins, Rubble, WallDmg, Wall)
  F  fort        H  house      V  village    G  gate       A  armory   E  vendor
Pins: after the sketch, lines like  "pin X Y META"  force an exact metatile.
Stamps: "stamp X Y CHAPTER SX SY W H" copies a rectangle from a vanilla chapter map (same tileset).
"""
import random, sys, collections
from fe8lib import *

CLASSES = {
    '.': {"Plains"}, 'f': {"Forest"}, 't': {"Thicket"}, 'm': {"Mountain"}, '^': {"Peak"},
    '~': {"Sea"}, 's': {"Sand"}, 'r': {"Road"}, 'w': {"River"}, 'c': {"Cliff"}, 'l': {"Lake"},
    '=': {"Bridge", "Bridge2"}, '#': {"Ruins", "Rubble", "WallDmg", "Wall"},
    'F': {"Fort"}, 'H': {"House"}, 'V': {"Village"}, 'G': {"Gate"}, 'A': {"Armory"}, 'E': {"Vendor"},
    'x': {"Fence"}, 'W': {"Wall"}, '_': {"Floor"}, 'T': {"T2E", "T2C"}, 'b': {"Barrel"}, 'd': {"Deck"},
    'g': {"Gunnels"}, 'S': {"Stairs"}, 'C': {"ChestF"}, 'D': {"Door"},
}
TID = {n: i for i, n in enumerate(TERRAIN)}


class Model:
    def __init__(self, rom, config_id, extra_chapters=()):
        self.rom = rom
        self.freq = collections.Counter()
        self.H = collections.defaultdict(set)   # a -> set of b that appeared to the right of a
        self.V = collections.defaultdict(set)   # a -> set of b that appeared below a
        self.maps = {}
        seen = set()
        for c in range(0x4F):
            ch = Chapter(rom, c)
            if ch.config != config_id or ch.mapid in seen:
                continue
            seen.add(ch.mapid)
            try:
                w, h, g = read_map(rom, ch.mapid)
            except Exception:
                continue
            if w < 5 or h < 5:
                continue
            self.maps[c] = g
            for y in range(h):
                for x in range(w):
                    a = g[y][x]
                    self.freq[a] += 1
                    if x + 1 < w: self.H[a].add(g[y][x + 1])
                    if y + 1 < h: self.V[a].add(g[y + 1][x])
        self.Hr = collections.defaultdict(set)
        self.Vr = collections.defaultdict(set)
        for a, bs in self.H.items():
            for b in bs: self.Hr[b].add(a)
        for a, bs in self.V.items():
            for b in bs: self.Vr[b].add(a)
        ch0 = next(Chapter(rom, c) for c in range(0x4F) if Chapter(rom, c).config == config_id)
        self.tileset = tileset_for_chapter(rom, ch0)
        self.tiles = sorted(self.freq)

    def pathfrac(self, m):
        if not hasattr(self, "_pf"):
            self._pf = {}
        if m not in self._pf:
            px = list(self.tileset.meta_image(m).getdata())
            self._pf[m] = sum(1 for (r, g, b) in px if r > 200 and g > 200 and b < 225 and r >= b + 25) / 256.0
        return self._pf[m]

    def terrain_of(self, m):
        return TERRAIN[self.tileset.terrain[m]]


def parse_sketch(text):
    rows, pins, stamps = [], {}, []
    holes = []
    for line in text.splitlines():
        s = line.split("//")[0].rstrip()
        if not s:
            continue
        if s.startswith("hole "):
            holes.append(tuple(int(v, 0) for v in s.split()[1:]))
        elif s.startswith("pin "):
            _, x, y, m = s.split(); pins[(int(x), int(y))] = int(m, 0)
        elif s.startswith("stamp "):
            p = s.split(); stamps.append(tuple(int(v, 0) for v in p[1:]))
        else:
            rows.append(s)
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, '?') for r in rows]
    return rows, pins, stamps, holes


def resolve_pins(model, pins, stamps, holes=()):
    out = {}
    for (x0, y0, chap, sx, sy, sw, sh) in stamps:
        src = model.maps[chap]
        for dy in range(sh):
            for dx in range(sw):
                out[(x0 + dx, y0 + dy)] = src[sy + dy][sx + dx]
    for (hx, hy, hw, hh) in holes:
        for dy in range(hh):
            for dx in range(hw):
                out.pop((hx + dx, hy + dy), None)
    out.update(pins)
    return out


def solve(model, rows, pins=None, stamps=(), seed=0, tries=200, soft=None):
    pins = dict(pins or {})
    h, w = len(rows), len(rows[0])
    for (x0, y0, chap, sx, sy, sw, sh) in stamps:
        src = model.maps[chap]
        for dy in range(sh):
            for dx in range(sw):
                pins[(x0 + dx, y0 + dy)] = src[sy + dy][sx + dx]
    base = {}
    for y in range(h):
        for x in range(w):
            if (x, y) in pins:
                base[(x, y)] = {pins[(x, y)]}
                continue
            c = rows[y][x]
            if c == '?':
                base[(x, y)] = set(model.tiles)
            else:
                allowed = CLASSES[c]
                base[(x, y)] = {m for m in model.tiles if model.terrain_of(m) in allowed}
            if not base[(x, y)]:
                raise ValueError("no tiles for class %r at %d,%d" % (c, x, y))
    rng = random.Random(seed)
    best = None
    for attempt in range(tries):
        dom = {k: set(v) for k, v in base.items()}
        if not propagate(model, dom, w, h, list(dom)):
            raise ValueError("sketch unsatisfiable before search (check pins/stamps & sketch)")
        ok = True
        while True:
            open_cells = [(len(d), k) for k, d in dom.items() if len(d) > 1]
            if not open_cells:
                break
            n = min(o[0] for o in open_cells)
            cands = [k for (l, k) in open_cells if l == n]
            k = rng.choice(cands)
            choices = sorted(dom[k])
            weights = [model.freq[m] ** 0.75 for m in choices]
            pick = rng.choices(choices, weights)[0]
            saved = {kk: set(vv) for kk, vv in dom.items()}
            dom[k] = {pick}
            if not propagate(model, dom, w, h, [k]):
                dom = saved
                dom[k].discard(pick)
                if not dom[k] or not propagate(model, dom, w, h, [k]):
                    ok = False
                    break
        if ok:
            return [[next(iter(dom[(x, y)])) for x in range(w)] for y in range(h)]
    raise RuntimeError("failed to solve after %d tries" % tries)


def propagate(model, dom, w, h, queue):
    queue = collections.deque(queue)
    while queue:
        x, y = queue.popleft()
        d = dom[(x, y)]
        for dx, dy, rel in ((1, 0, model.H), (-1, 0, model.Hr), (0, 1, model.V), (0, -1, model.Vr)):
            nk = (x + dx, y + dy)
            if nk not in dom:
                continue
            nd = dom[nk]
            ok = set()
            for a in d:
                ok |= rel[a]
            new = nd & ok
            if new != nd:
                if not new:
                    return False
                dom[nk] = new
                queue.append(nk)
    return True



NEAR = {  # soft alternatives: class -> {terrain: cost}
    '~': {"Cliff": 1.0, "Sand": 1.5, "Lake": 1.0}, 's': {"Plains": 1.0, "Sea": 1.5},
    '.': {"Road": 2.0, "Sand": 2.0, "Forest": 2.5}, 'f': {"Thicket": 0.5, "Plains": 2.0},
    'm': {"Peak": 1.0, "Plains": 2.5}, '^': {"Mountain": 0.7, "Cliff": 2.0},
    'r': {"Plains": 2.0, "Bridge": 1.0}, 'c': {"Sea": 1.5, "Peak": 1.5, "Plains": 2.5},
    'w': {"Bridge": 1.5, "Lake": 1.0}, '#': {"Plains": 2.0, "Fort": 2.0, "Pillar": 1.0},
}


def anneal(model, rows, pins=None, stamps=(), seed=0, sweeps=400, W=12.0, mismatch=6.0, verbose=False):
    import numpy as np
    pins = dict(pins or {})
    for (x0, y0, chap, sx, sy, sw, sh) in stamps:
        src = model.maps[chap]
        for dy in range(sh):
            for dx in range(sw):
                pins[(x0 + dx, y0 + dy)] = src[sy + dy][sx + dx]
    rng = np.random.default_rng(seed)
    tiles = model.tiles
    n = len(tiles)
    idx = {t: i for i, t in enumerate(tiles)}
    Hm = np.zeros((n, n), bool); Vm = np.zeros((n, n), bool)
    for a, bs in model.H.items():
        for b in bs: Hm[idx[a], idx[b]] = True
    for a, bs in model.V.items():
        for b in bs: Vm[idx[a], idx[b]] = True
    terr = [model.terrain_of(t) for t in tiles]
    freq = np.array([model.freq[t] for t in tiles], float)
    prior = -0.35 * np.log(freq)
    h, w = len(rows), len(rows[0])
    unary = np.zeros((h, w, n))
    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            if c == '?':
                unary[y, x] = prior
                continue
            allowed = CLASSES[c]; near = NEAR.get(c, {})
            u = np.array([0.0 if t in allowed else near.get(t, mismatch) for t in terr])
            unary[y, x] = u + prior
    for (x, y), m in pins.items():
        u = np.full(n, 1e6); u[idx[m]] = 0; unary[y, x] = u
    g = np.array([[int(np.argmin(unary[y, x])) for x in range(w)] for y in range(h)])
    cells = [(x, y) for y in range(h) for x in range(w) if (x, y) not in pins]
    for s in range(sweeps):
        T = max(0.05, 3.0 * (1 - s / (sweeps * 0.85)))
        rng.shuffle(cells)
        for (x, y) in cells:
            e = unary[y, x].copy()
            if x > 0: e += W * ~Hm[g[y, x - 1], :]
            if x < w - 1: e += W * ~Hm[:, g[y, x + 1]]
            if y > 0: e += W * ~Vm[g[y - 1, x], :]
            if y < h - 1: e += W * ~Vm[:, g[y + 1, x]]
            if T <= 0.06:
                g[y, x] = int(np.argmin(e))
            else:
                p = np.exp(-(e - e.min()) / T); p /= p.sum()
                g[y, x] = int(rng.choice(n, p=p))
    bad = 0
    for y in range(h):
        for x in range(w):
            if x < w - 1 and not Hm[g[y, x], g[y, x + 1]]: bad += 1
            if y < h - 1 and not Vm[g[y, x], g[y + 1, x]]: bad += 1
    mis = sum(1 for y in range(h) for x in range(w) if rows[y][x] != '?' and terr[g[y, x]] not in CLASSES[rows[y][x]])
    if verbose:
        print("seams:", bad, "terrain mismatches:", mis)
    return [[tiles[g[y, x]] for x in range(w)] for y in range(h)], bad, mis


def softwfc(model, rows, pins=None, stamps=(), seed=0, beta=1.6, restarts=30, verbose=False, max_backtracks=4000):
    import math
    pins = dict(pins or {})
    for (x0, y0, chap, sx, sy, sw, sh) in stamps:
        src = model.maps[chap]
        for dy in range(sh):
            for dx in range(sw):
                pins[(x0 + dx, y0 + dy)] = src[sy + dy][sx + dx]
    h, w = len(rows), len(rows[0])
    terr = {t: model.terrain_of(t) for t in model.tiles}

    def cost(c, t):
        if c == '?':
            return 0.0
        if c == 'r':
            if terr[t] in ("Plains", "Road", "Bridge"):
                return max(0.0, 0.55 - model.pathfrac(t)) * 8.0
            return 6.0
        if c == '.' and terr[t] == "Plains":
            return max(0.0, model.pathfrac(t) - 0.25) * 6.0
        if terr[t] in CLASSES[c]:
            return 0.0
        return NEAR.get(c, {}).get(terr[t], 6.0)
    W = {}
    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            W[(x, y)] = {t: (model.freq[t] ** 0.5) * math.exp(-beta * cost(c, t)) for t in model.tiles}
    best = None
    rng = random.Random(seed)
    for r in range(restarts):
        dom = {(x, y): ({pins[(x, y)]} if (x, y) in pins else set(model.tiles)) for y in range(h) for x in range(w)}
        if not propagate(model, dom, w, h, list(dom)):
            raise ValueError("pins inconsistent")
        stack = []
        backtracks = 0
        ok = True
        while True:
            # choose cell with min entropy (weighted)
            bestk, beste = None, 1e18
            for k, d in dom.items():
                if len(d) <= 1:
                    continue
                ws = [W[k][t] for t in d]
                tot = sum(ws)
                if tot <= 0:
                    e = -1
                else:
                    e = -sum((v / tot) * math.log(v / tot) for v in ws if v > 0) + rng.random() * 1e-3
                if e < beste:
                    beste, bestk = e, k
            if bestk is None:
                break
            k = bestk
            choices = sorted(dom[k])
            ws = [W[k][t] + 1e-9 for t in choices]
            pick = rng.choices(choices, ws)[0]
            snapshot = {kk: set(vv) for kk, vv in dom.items()}
            dom[k] = {pick}
            while not propagate(model, dom, w, h, [k]):
                backtracks += 1
                dom = snapshot
                dom[k].discard(pick)
                if not dom[k] or backtracks > max_backtracks:
                    ok = False
                    break
                snapshot = {kk: set(vv) for kk, vv in dom.items()}
                choices = sorted(dom[k]); ws = [W[k][t] + 1e-9 for t in choices]
                pick = rng.choices(choices, ws)[0]
                dom[k] = {pick}
            if not ok:
                break
        if not ok:
            continue
        g = [[next(iter(dom[(x, y)])) for x in range(w)] for y in range(h)]
        mis = sum(cost(rows[y][x], g[y][x]) for y in range(h) for x in range(w))
        if verbose:
            print("restart", r, "cost", round(mis, 1))
        if best is None or mis < best[0]:
            best = (mis, g)
        if mis == 0:
            break
    if best is None:
        raise RuntimeError("softwfc failed")
    return best[1], best[0]


def beam(model, rows, pins=None, stamps=(), seed=0, width=300, noise=0.6, freqw=0.25, verbose=False):
    """Row-major beam search: each partial map keeps full grid; tile must be seen-adjacent to left & up."""
    import math, heapq
    pins = dict(pins or {})
    for (x0, y0, chap, sx, sy, sw, sh) in stamps:
        src = model.maps[chap]
        for dy in range(sh):
            for dx in range(sw):
                pins[(x0 + dx, y0 + dy)] = src[sy + dy][sx + dx]
    h, w = len(rows), len(rows[0])
    terr = {t: model.terrain_of(t) for t in model.tiles}
    rng = random.Random(seed)

    def cost(c, t):
        if c == '?':
            return 0.0
        if c == 'r':
            if terr[t] in ("Plains", "Road", "Bridge"):
                return max(0.0, 0.55 - model.pathfrac(t)) * 8.0
            return 6.0
        if c == '.' and terr[t] == "Plains":
            return max(0.0, model.pathfrac(t) - 0.25) * 6.0
        if terr[t] in CLASSES[c]:
            return 0.0
        return NEAR.get(c, {}).get(terr[t], 6.0)
    fpen = {t: -freqw * math.log(model.freq[t]) for t in model.tiles}
    # per-cell cost cache
    cc = {}
    for y in range(h):
        for x in range(w):
            if (x, y) in pins:
                cc[(x, y)] = {pins[(x, y)]: 0.0}
            else:
                c = rows[y][x]
                border = any(0 <= x + dx < w and 0 <= y + dy < h and rows[y + dy][x + dx] != c
                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                k = 0.35 if border else 1.0
                cc[(x, y)] = {t: k * cost(c, t) + fpen[t] for t in model.tiles}
    # lookahead: a tile must be able to have *some* right/down neighbor matching the next cell's best options
    beams = [(0.0, ())]
    for y in range(h):
        for x in range(w):
            nxt = []
            for score, tiles in beams:
                left = tiles[-1] if x > 0 else None
                up = tiles[-w] if y > 0 else None
                if left is not None and up is not None:
                    cand = model.H[left] & model.V[up]
                elif left is not None:
                    cand = model.H[left]
                elif up is not None:
                    cand = model.V[up]
                else:
                    cand = cc[(x, y)].keys()
                cell = cc[(x, y)]
                if (x, y) in pins:
                    t = pins[(x, y)]
                    pen = 0.0
                    if left is not None and t not in model.H[left]: pen += 15.0
                    if up is not None and t not in model.V[up]: pen += 15.0
                    nxt.append((score + pen + rng.random() * noise, tiles + (t,)))
                    continue
                added = 0
                for t in cand:
                    if t not in cell:
                        continue
                    if x < w - 1 and not model.H[t]:
                        continue
                    if y < h - 1 and not model.V[t]:
                        continue
                    pr = pins.get((x + 1, y))
                    if pr is not None and pr not in model.H[t]:
                        continue
                    pd = pins.get((x, y + 1))
                    if pd is not None and pd not in model.V[t]:
                        continue
                    ns = score + cell[t] + rng.random() * noise
                    nxt.append((ns, tiles + (t,)))
                    added += 1
                if not added:
                    # seam fallback: every constraint becomes soft; keep the least-violating tiles
                    pr = pins.get((x + 1, y)); pd = pins.get((x, y + 1))
                    opts = []
                    for t, c in cell.items():
                        v = 0
                        if left is not None and t not in model.H[left]: v += 1
                        if up is not None and t not in model.V[up]: v += 1
                        if pr is not None and pr not in model.H[t]: v += 1
                        if pd is not None and pd not in model.V[t]: v += 1
                        opts.append((v, c, t))
                    mv = min(o[0] for o in opts)
                    for v, c, t in opts:
                        if v == mv:
                            nxt.append((score + c + 15.0 * v + rng.random() * noise, tiles + (t,)))
            if not nxt:
                raise RuntimeError("beam died at %d,%d" % (x, y))
            if len(nxt) > width:
                nxt = heapq.nsmallest(width, nxt, key=lambda e: e[0])
            beams = nxt
        # prune duplicate row-states (keep best per last-row signature) for diversity
        seen = {}
        for sc, tl in beams:
            sig = tl[-w:]
            if sig not in seen or seen[sig][0] > sc:
                seen[sig] = (sc, tl)
        beams = sorted(seen.values(), key=lambda e: e[0])
        if verbose:
            print("row", y, "best", round(beams[0][0], 1), "beams", len(beams))
    sc, tl = beams[0]
    g = [list(tl[y * w:(y + 1) * w]) for y in range(h)]
    mis = sum(cost(rows[y][x], g[y][x]) for y in range(h) for x in range(w) if (x, y) not in pins)
    return g, mis


def terrain_ascii(model, grid):
    inv = {}
    for k, v in CLASSES.items():
        for t in v: inv.setdefault(t, k)
    return "\n".join("".join(inv.get(model.terrain_of(t), '?') for t in r) for r in grid)


if __name__ == "__main__":
    rom = Rom(sys.argv[1])
    model = Model(rom, int(sys.argv[2], 0))
    rows, pins, stamps, holes = parse_sketch(open(sys.argv[3]).read())
    pins = resolve_pins(model, pins, stamps, holes); stamps = ()
    g, mis = beam(model, rows, pins, stamps, seed=int(sys.argv[5]) if len(sys.argv) > 5 else 0, width=int(sys.argv[6]) if len(sys.argv) > 6 else 300)
    print("sketch cost", round(mis, 1))
    print(terrain_ascii(model, g))
    render_map(model.tileset, g).save(sys.argv[4])

