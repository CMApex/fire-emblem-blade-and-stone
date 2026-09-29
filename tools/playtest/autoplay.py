"""A simple FE8 auto-player for playtesting: reads RAM, plays sensible turns, screenshots everything notable."""
import os, sys, struct
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game import Game, MOVMAP

BUBBLE = (243, 244, 237)


class Player:
    def __init__(self, g, log_every_dialog=True):
        self.g = g
        self.dialog_shots = log_every_dialog
        self.events = []

    # ---------- perception ----------
    def is_dialog(self):
        """A conversation is open <=> a gProcScr_Talk proc (0x08591358) is alive in the proc pool."""
        raw = self.g.dump(0x02024E68, 0x6C * 64)
        for i in range(64):
            if struct.unpack_from("<I", raw, i * 0x6C)[0] == 0x08591358:
                return True
        return False

    def map_size(self):
        return self.g.u8(0x0202E4D4), self.g.u8(0x0202E4D6)

    def is_idle(self):
        """Idle on the map in player phase <=> a d-pad press moves the map cursor."""
        t, ph = self.g.turn()
        if ph != 0:
            return False
        if any((u["state"] & 1) and not (u["state"] & 0x4C) and u["x"] < 0x40 for u in self.g.units("blue")):
            return False                    # a unit is picked up / mid-action
        x, y = self.g.cursor()
        w, h = self.map_size()
        k, back = ("RIGHT", "LEFT") if x < w - 1 else ("LEFT", "RIGHT")
        self.g.press(k, 8)
        moved = self.g.cursor() != (x, y)
        if moved:
            self.g.press(back, 8)
        return moved

    def canto(self):
        """If a mounted unit is in Canto (has-moved bit, not yet unselectable), end it in place."""
        for u in self.g.units("blue"):
            if (u["state"] & 0x40) and not (u["state"] & 0x2) and not (u["state"] & 0xC) and u["x"] < 0x40:
                self.g.move_cursor(u["x"], u["y"]); self.g.press("A", 30)
                self.g.shot("canto menu")
                self.g.press("UP", 8); self.g.press("A", 30)
                return True
        return False

    def settle(self, label="", maxloops=400):
        """Advance dialogue / popups / animations until the player can act again."""
        last_dialog = False
        for i in range(maxloops):
            if self.is_dialog():
                if not last_dialog or i % 6 == 0:
                    self.g.shot("%s dlg" % label)
                self.g.press("A", 45)
                last_dialog = True
                continue
            last_dialog = False
            if self.g.turn()[1] == 0 and self.canto():
                continue
            if self.is_idle():
                if self.canto():
                    continue
                return True
            t, ph = self.g.turn()
            if ph == 0 and i % 4 == 3:
                self.g.press("B", 30)      # popups ("Got an item", level-up) close on B; B never selects a unit
            else:
                self.g.wait(30)
        self.g.shot("%s STUCK" % label)
        return False

    def movemap(self):
        w, h = self.map_size()
        rows = self.g.u32(MOVMAP)
        out = []
        for y in range(h):
            out.append(self.g.dump(self.g.u32(rows + 4 * y), w))
        return out

    # ---------- actions ----------
    def arrive(self, cid, tile, maxwait=20):
        """After confirming a destination: wait until the unit stands there and its menu is up."""
        for _ in range(maxwait):
            us = [x for x in self.g.units("blue") if x["cid"] == cid]
            if us and (us[0]["x"], us[0]["y"]) == tuple(tile):
                self.g.wait(25)
                return True
            self.g.wait(10)
        return False

    def path_dist(self, u, target):
        """Dijkstra distance (in move cost) from every tile to target for this unit's class; enemies block."""
        import heapq, struct as st
        g = self.g
        w, h = self.map_size()
        rows = g.u32(0x0202E4DC)
        terr = [g.dump(g.u32(rows + 4 * y), w) for y in range(h)]
        costp = st.unpack("<I", g.dump(u["pclass"] + 0x38, 4))[0]
        cost = g.dump(costp, 0x41)
        red = {(r["x"], r["y"]) for r in g.units("red") if not r["hidden"] and not r["dead"] and r["hp"] > 0}
        INF = 10 ** 9
        dist = [[INF] * w for _ in range(h)]
        tx, ty = target
        dist[ty][tx] = 0
        pq = [(0, tx, ty)]
        while pq:
            d, x, y = heapq.heappop(pq)
            if d > dist[y][x]:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    c = cost[terr[y][x]]            # cost of stepping onto (x,y) from (nx,ny)
                    if c == 0xFF or c >= 0x80:
                        continue
                    if (x, y) in red and (x, y) != (tx, ty):
                        continue
                    nd = d + max(1, c)
                    if nd < dist[ny][nx]:
                        dist[ny][nx] = nd
                        heapq.heappush(pq, (nd, nx, ny))
        return dist

    def menu(self):
        """The open menu (sProc_Menu) as (current index, [(def ptr, msg id, onSelected)]), or None."""
        raw = self.g.dump(0x02024E68, 0x6C * 64)
        for i in range(64):
            if struct.unpack_from("<I", raw, i * 0x6C)[0] == 0x085B64D0:
                o = i * 0x6C
                cnt, cur = raw[o + 0x60], raw[o + 0x61]
                items = []
                for k in range(cnt):
                    ip = struct.unpack_from("<I", raw, o + 0x34 + 4 * k)[0]
                    d = self.g.u32(ip + 0x30)
                    items.append((d, self.g.u16(d + 4), self.g.u32(d + 0x14)))
                return cur, items
        return None

    HEAL_ITEMS = (0x6C, 0x6D, 0xA2)            # Vulnerary, Elixir, Vulnerary (2)
    ITEM_CMD, USE_CMD = 0x080232E9, 0x08023771

    def pick(self, target_onsel=None, index=None):
        """Move the open menu's cursor to the entry with this handler (or index) and press A."""
        for _ in range(8):                      # menus open a few frames late; poll
            m = self.menu()
            if m and (index is not None or any(it[2] == target_onsel for it in m[1])):
                break
            self.g.wait(10)
        else:
            return False
        cur, items = m
        if index is None:
            index = [k for k, it in enumerate(items) if it[2] == target_onsel][0]
        for _ in range((index - cur) % len(items)):
            self.g.press("DOWN", 16)
        self.g.wait(12)
        before = self.menu()
        self.g.press("A", 40)
        if self.menu() == before:               # input landed during the menu's open animation: once more
            self.g.press("A", 40)
        return True

    def use_heal_item(self, u, label=""):
        """With the unit menu open: Item -> the first healing item -> Use. Returns True if used."""
        slot = next((k for k, it in enumerate(u["items"]) if (it & 0xFF) in self.HEAL_ITEMS), None)
        if slot is None or not self.pick(self.ITEM_CMD):
            print("   heal fail@item", slot, self.menu()); return False
        self.g.wait(20)
        if not self.pick(index=slot):
            print("   heal fail@slot", self.menu()); self.cancel(); return False
        if not self.pick(self.USE_CMD):
            if self.menu() is None:            # the item was used already (menu closed)
                self.settle(label + " heal"); return True
            print("   heal fail@use", self.menu()); self.cancel(); return False
        self.g.shot(label + " heal")
        self.settle(label + " heal")
        return True

    def select(self, u):
        self.g.move_cursor(u["x"], u["y"]); self.g.press("A", 45)

    def cancel(self):
        for _ in range(3): self.g.press("B", 15)

    def do_unit(self, u, goal=None, seize=None, allow_attack=True, label="", visit=None, talk_to=None):
        g = self.g
        blue = [b for b in g.units("blue") if not b["hidden"] and not b["dead"]]
        red = [r for r in g.units("red") if not r["hidden"] and not r["dead"] and r["hp"] > 0]
        occupied = {(b["x"], b["y"]) for b in blue + red + [x for x in g.units("green") if not x["hidden"]]}
        self.select(u)
        mm = self.movemap()
        reach = [(x, y) for y, row in enumerate(mm) for x, v in enumerate(row)
                 if v != 0xFF and ((x, y) not in occupied or (x, y) == (u["x"], u["y"]))]
        if not reach:
            self.cancel(); return "none"
        def enemy_adjacent(t):
            return any(abs(t[0] - r["x"]) + abs(t[1] - r["y"]) == 1 for r in red)
        # visit a house/village?
        if visit and visit in reach and not enemy_adjacent(visit):
            g.move_cursor(*visit); g.press("A", 10); self.arrive(u["cid"], visit); g.shot(label + " visit menu"); g.press("A", 45)
            self.settle(label + " visit")
            return "visit"
        # talk to someone?
        if talk_to:
            tu = [b for b in blue if b["cid"] == talk_to]
            if tu:
                tx, ty = tu[0]["x"], tu[0]["y"]
                spots = [p for p in reach if abs(p[0] - tx) + abs(p[1] - ty) == 1 and not enemy_adjacent(p)]
                if spots:
                    g.move_cursor(*spots[0]); g.press("A", 10); self.arrive(u["cid"], spots[0]); g.shot(label + " talk menu")
                    g.press("A", 45); g.press("A", 45)
                    self.settle(label + " talk")
                    return "talk"
        # seize?
        if seize and seize in reach:
            g.move_cursor(*seize); g.press("A", 10); self.arrive(u["cid"], seize); g.shot(label + " seize menu"); g.press("A", 45)
            return "seize"
        best = None
        # a wounded unit pulls back out of reach instead of trading blows (what any player would do)
        if u["hp"] < 0.45 * u["maxhp"] and red and not (seize and seize in reach):
            tile = max(reach, key=lambda p: (min(abs(p[0] - r["x"]) + abs(p[1] - r["y"]) for r in red), -abs(p[0] - u["x"]) - abs(p[1] - u["y"])))
            g.move_cursor(*tile); g.press("A", 10); self.arrive(u["cid"], tile)
            g.shot(label + " retreat")
            healed = self.use_heal_item(u, label)
            print("  retreat c%X hp %d/%d -> %s healed=%s items=%s" % (u["cid"], u["hp"], u["maxhp"], tile, healed, [hex(i) for i in u["items"]]), flush=True)
            if not healed:
                g.press("UP", 12); g.press("A", 45)
            self.settle(label + " retreat")
            return "retreat"
        if allow_attack:
            for e in red:
                for (x, y) in reach:
                    if abs(x - e["x"]) + abs(y - e["y"]) == 1:
                        score = e["hp"] * 10 + abs(x - u["x"]) + abs(y - u["y"])
                        if best is None or score < best[0]:
                            best = (score, (x, y), e)
        if best:
            _, tile, e = best
            g.move_cursor(*tile); g.press("A", 10); self.arrive(u["cid"], tile)
            g.shot(label + " menu")
            g.press("A", 45)                     # Attack (top option when a target is in range)
            g.press("A", 60)                     # first weapon
            reds = {(r["x"], r["y"]) for r in red}
            for _ in range(3):                   # C-SkillSys can show an extra page (combat arts) before targeting
                if g.cursor() in reds:
                    break
                g.shot(label + " pre-target")
                g.press("A", 60)
            for _ in range(6):
                if g.cursor() == (e["x"], e["y"]):
                    break
                g.press("RIGHT", 12)
            g.shot(label + " forecast")
            g.press("A", 40)
            self.settle(label + " battle")
            g.shot(label + " done")
            return "attack"
        # move toward goal
        target = goal
        if target is None and red:
            target = min(((r["x"], r["y"]) for r in red), key=lambda p: abs(p[0] - u["x"]) + abs(p[1] - u["y"]))
        if target is None:
            tile = (u["x"], u["y"])
        else:
            dist = self.path_dist(u, target)
            tile = min(reach, key=lambda p: (dist[p[1]][p[0]], abs(p[0] - target[0]) + abs(p[1] - target[1]), -mm[p[1]][p[0]]))
        g.move_cursor(*tile); g.press("A", 10); self.arrive(u["cid"], tile)
        g.press("UP", 12); g.press("A", 45)    # Wait (last option); C-SkillSys menus open a little slower
        self.settle(label + " wait")
        return "move"

    def end_turn(self, label=""):
        g = self.g
        w, h = self.map_size()
        occupied = {(u["x"], u["y"]) for s in ("blue", "red", "green") for u in g.units(s) if not u["hidden"]}
        spot = next((x, y) for y in range(h) for x in range(w) if (x, y) not in occupied)
        g.move_cursor(*spot); g.press("A", 45)
        g.shot(label + " map menu")
        g.press("UP", 12); g.press("A", 60)
        t0 = g.turn()[0]
        n = 0
        while True:
            n += 1
            if self.is_dialog():
                g.shot(label + " ep dlg"); g.press("A", 45); continue
            t, ph = g.turn()
            if t > t0 and ph == 0 and self.is_idle():
                g.shot(label + " new turn %d" % t)
                return t
            if n % 8 == 0:
                g.shot(label + " ep t%d ph%02X" % (t, ph))
            g.wait(40)
            if n > 600:
                g.shot(label + " EP STUCK"); return None
