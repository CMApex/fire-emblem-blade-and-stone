"""Clone/override classes from data/classes.csv onto the Skill System ClassTable.csv (and level caps / mag tables if present)."""
import csv, os
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
T = os.path.join(ROOT, "Tables/NightmareModules/CharactersClasses/ClassTable.csv")
rows = list(csv.reader(open(T)))
hdr = rows[0]
byid = {int(r[3], 16): i for i, r in enumerate(rows) if i > 0}
col = {}
for i, h in enumerate(hdr):
    col.setdefault(h, i)
for e in csv.DictReader(open(os.path.join(ROOT, "data", "classes.csv"))):
    cid = int(e["id"], 16)
    if e.get("clone_from"):
        src = rows[byid[int(e["clone_from"], 16)]]
        new = list(src)
        new[3] = "0x%x" % cid
        rows[byid[cid]] = new
    r = rows[byid[cid]]
    if e.get("label"):
        r[0] = e["label"]
    for k, v in e.items():
        if k in ("id", "clone_from", "label") or not v:
            continue
        r[col[k]] = v
csv.writer(open(T, "w", newline="")).writerows(rows)
print("patched classes")

# mirror level caps / magic tables for cloned classes if those csvs exist
for fn in ("ClassLevelCapTable.csv", "MagClassEditor.csv"):
    p = os.path.join(ROOT, "Tables/NightmareModules/CharactersClasses", fn)
    if not os.path.exists(p):
        continue
    rr = list(csv.reader(open(p)))
    idx = {}
    for i, r in enumerate(rr[1:], 1):
        try:
            idx[int(r[0].split()[0], 16)] = i
        except ValueError:
            pass
    for e in csv.DictReader(open(os.path.join(ROOT, "data", "classes.csv"))):
        if e.get("clone_from"):
            a, b = int(e["id"], 16), int(e["clone_from"], 16)
            if a in idx and b in idx:
                rr[idx[a]] = [rr[idx[a]][0]] + rr[idx[b]][1:]
    csv.writer(open(p, "w", newline="")).writerows(rr)
