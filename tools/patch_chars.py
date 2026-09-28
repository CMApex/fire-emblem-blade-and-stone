"""Apply Blade & Stone character edits (data/characters.csv) onto the Skill System CharacterTable.csv."""
import csv, os, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TABLE = os.path.join(ROOT, "Tables/NightmareModules/CharactersClasses/CharacterTable.csv")
rows = list(csv.reader(open(TABLE)))
hdr = rows[0]
col = {h: i for i, h in enumerate(hdr)}
# duplicate header names (N/A) — build by position for the ones we need
FIELDS = ["Name", "Description", "Support Class", "Portrait", "Affinity", "Lv", "HP", "Atk", "Skl", "Spd", "Def", "Res",
          "Luck", "Con", "Sword", "Lance", "Axe", "Bow", "Staff", "Anima", "Light", "Dark",
          "HP Growth", "Atk Growth", "Skl Growth", "Spd Growth", "Def Growth", "Res Growth", "Luck Growth", "CharClassAbility"]
edits = list(csv.DictReader(open(os.path.join(ROOT, "data", "characters.csv"))))
byid = {}
for i, r in enumerate(rows[1:], 1):
    byid[int(r[0].split()[0], 16)] = i
for e in edits:
    cid = int(e["id"], 16)
    r = rows[byid[cid]]
    if e.get("label"):
        r[0] = "0x%02X %s" % (cid, e["label"])
    for f in FIELDS:
        v = (e.get(f) or "").strip()
        if v:
            r[col[f]] = v
csv.writer(open(TABLE, "w", newline="")).writerows(rows)
print("patched %d characters" % len(edits))
