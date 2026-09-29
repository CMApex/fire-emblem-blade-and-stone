# Fire Emblem: Blade & Stone

An FE8 (Sacred Stones) hack that brings the full casts of FE7 and FE8 together in one original story,
built on the [FE8U C-SkillSys](https://github.com/FireEmblemUniverse/fe8u-cskillsys) engine.
Story and design live in [`docs/bible.md`](docs/bible.md); engine research and decisions in [`docs/research-memo.md`](docs/research-memo.md).

**Status (demo):** the Prologue ("The Year After", Renais) and Chapter 1 ("The Marquess's Docks", Ostia) are playable back to back.

- All 76 FE7/FE8 veterans exist as characters, with stats derived from canon, STR/MAG split and personal skills.
- Every FE7 veteran fights with their own FE7 battle animation and personal palette. Eliwood, Hector and Lyn have real FE7 lord classes with FE7 stats and map sprites.
- QoL: no Health & Safety screen; fast text and fast map speed by default; growth display (Select on the stat screen), HP bars, danger zone, 200-item convoy (engine).

## Playing

Apply `BladeAndStone.ups` to a clean **Fire Emblem: The Sacred Stones (USA)** ROM
(CRC32 `A47246AE`) with any UPS patcher (e.g. Floating IPS, Rom Patcher JS, or `python3 tools/ups.py apply`).
The patched ROM is about 21 MB (GBA ROMs may be up to 32 MB).

## Building

Linux or WSL. `./setup.sh` fetches and builds the pinned engine into `engine/` (git, python3 with Pillow and
pyelftools, arm-none-eabi gcc or devkitARM, cmake, ghc and cabal, .NET SDK 8, gawk, moreutils, devkitPro grit and gbalzss).

```sh
mkdir -p roms
cp /path/to/FE8U.gba roms/fe8u.gba     # clean Sacred Stones (USA)
cp /path/to/FE7U.gba roms/fe7u.gba     # clean Fire Emblem (USA): FE7 portraits, animations and stats are read from it
./setup.sh                              # once
./build.sh                              # -> build/BladeAndStone.gba and build/BladeAndStone.ups
```

Debug builds: `BS_DEFINES="BS_DEBUG_SEIZE BS_DEBUG_CH1" BS_OUT=debug ./build.sh`.
No ROM data is committed. Everything under `gen/` and `build/` is derived from the ROMs you supply.

## Layout

| Path | What |
|---|---|
| `src/BladeAndStone.event` | content root (included by the engine at its free-space section) |
| `src/Events/` | chapters (each opens with a design-intent note), quotes, world map |
| `src/Hacks/Core/` | C engine changes: per-chapter leader, camera clamp fix, QoL |
| `src/Text/` | all script text (`blade.txt` is the root; `codes.txt` has text shortcuts) |
| `src/Data/` | small data tables (leaders) |
| `overlay/` | our edits to engine files (configs, designer config, text makefile stub, main.event) |
| `data/cast.csv` | the cast: IDs, tiers, classes, levels, personal skills, weapon ranks |
| `data/npcs.csv` | bosses and generic enemies (explicit numbers) |
| `data/fe7_faces.csv` | FE7 portraits to port |
| `maps_src/*.sketch` | map sketches (terrain ASCII + stamps from vanilla maps + pins); `*.json` are solved maps |
| `tools/gencast.py` | derives veteran stats from canon; writes character/class data and engine skill/magic tables |
| `tools/port_banims.py` | ports FE7 battle animations, personal palettes and map sprites |
| `tools/gentext.py` | compiles our text into the engine's text table |
| `tools/numbercheck.py` | numbers check: expected enemy stats vs. the party (damage, doubling, hit) |
| `tools/solvemap.py`, `tools/mapgen.py` | map solver (vanilla adjacency, beam search) |
| `tools/playtest/` | headless emulator harness and auto-player used to play the build end to end |

## Credits

Built on [FE8U C-SkillSys](https://github.com/FireEmblemUniverse/fe8u-cskillsys) (Mokha and contributors),
FE-CLib-Mokha, ColorzCore / Event Assembler, the Individual Animation patch (7743), and the FE8 decompilation project for reference.
Fire Emblem is © Nintendo / Intelligent Systems. This is a non-commercial fan project.
