# Fire Emblem: Blade & Stone

An FE8 (Sacred Stones) buildfile hack that brings the full casts of FE7 and FE8 together in one original story.
Story and design live in [`docs/bible.md`](docs/bible.md).

**Status:** Prologue ("The Year After") is playable end to end: world map narration, a new map, events, a village and a house, reinforcements, a seize, and an ending that introduces the first FE7 character.

## Playing

Apply `BladeAndStone.ups` to a clean **Fire Emblem: The Sacred Stones (USA)** ROM
(CRC32 `A47246AE`) with any UPS patcher (e.g. Floating IPS, or `python3 tools/ups.py apply`).

## Building

Requirements: Linux (or WSL), Python 3 with Pillow, the .NET SDK (6+), and `libffi7` for the bundled Haskell tools.

```sh
mkdir -p roms
cp /path/to/FE8U.gba roms/fe8u.gba     # clean Sacred Stones (USA)
cp /path/to/FE7U.gba roms/fe7u.gba     # clean Fire Emblem (USA) — FE7 portraits are ported at build time
./build.sh                              # -> build/BladeAndStone.gba
python3 tools/ups.py make roms/fe8u.gba build/BladeAndStone.gba build/BladeAndStone.ups
```

Debug builds: `BS_DEFINES="BS_DEBUG_SEIZE" BS_OUT=debug_seize ./build.sh` (starts Eirika next to the chapel).

No ROM data is committed. Everything under `build/` is derived from the ROMs you supply.

## Layout

| Path | What |
|---|---|
| `docs/bible.md` | story bible: premise, tone, cast, act and chapter plan |
| `Events/BladeAndStone.event` | chapter installer (world map + chapters) |
| `Events/Prologue.event`, `Events/WM_Prologue.event` | Prologue events and world map narration |
| `Text/blade/*.txt` | all Blade & Stone script text |
| `maps_src/*.sketch` | map sketches (terrain ASCII + stamps from vanilla maps) |
| `maps_src/*.json` | solved maps (metatile grids) |
| `data/characters.csv` | character stat overrides (applied by `tools/patch_chars.py`) |
| `data/fe7_faces.csv` | FE7 portraits to port, and the FE8 face IDs they get (0xAC+) |
| `tools/` | map solver, FE7 portrait importer, text linters, UPS tool, ROM helpers |

## Tools

- **`tools/mapgen.py`**: generates maps from an ASCII terrain sketch. It learns which metatiles can sit next to which from every vanilla map on the same tileset, then solves your sketch with a beam search. You can stamp rectangles from vanilla maps (coastlines, mountains, villages) and cut holes to redesign spots.
- **`tools/import_fe7_faces.py`**: copies FE7 portraits into an expanded FE8 portrait table (repointed at `0x5524`) and generates `[LoadName]` text codes.
- **`tools/lint_text.py`, `tools/lint_boxes.py`**: catch lines that are too wide and boxes with more than two lines.
- **`tools/fe8lib.py`**: LZ77, tileset and map decoding, and a map renderer.

## Credits

Built on the [FE8 Skill System](https://github.com/FireEmblemUniverse/SkillSystem_FE8) and its many contributors (see `CREDITS.md`), ColorzCore/Event Assembler, and the FE8 decompilation project for reference.
Fire Emblem is © Nintendo / Intelligent Systems. This is a non-commercial fan project.
