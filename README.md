# Fire Emblem: Blade & Stone

An FE8 (Sacred Stones) hack that brings the full casts of FE7 and FE8 together in one original story,
built on the [FE8U C-SkillSys](https://github.com/FireEmblemUniverse/fe8u-cskillsys) engine.
Story and design live in [`docs/bible.md`](docs/bible.md); engine research and decisions in [`docs/research-memo.md`](docs/research-memo.md).
To change the game yourself, start with [`HACKING.md`](HACKING.md).

**Status (demo):** the Prologue ("The Year After", Renais) and Chapter 1 ("The Marquess's Docks", Ostia) are playable back to back.

- All 76 FE7/FE8 veterans exist as characters, with stats derived from canon, STR/MAG split and personal skills.
- Every FE7 veteran fights with their own FE7 battle animation and personal palette. Eliwood, Hector and Lyn have real FE7 lord classes with FE7 stats and map sprites.
- QoL: no Health & Safety screen; fast text and fast map speed by default; growth display (Select on the stat screen), HP bars, danger zone, 200-item convoy (engine).

## Playing

Apply `BladeAndStone.ups` to a clean **Fire Emblem: The Sacred Stones (USA)** ROM
(CRC32 `A47246AE`) with any UPS patcher (e.g. Floating IPS, Rom Patcher JS, or `python3 tools/ups.py apply`).
The patched ROM is about 21 MB (GBA ROMs may be up to 32 MB).

## Building and changing the game

See **[HACKING.md](HACKING.md)**: setup on Windows (WSL2) or Linux, the build loop, and recipes for editing
dialogue, stats, enemies, maps (in [Tiled](https://www.mapeditor.org)) and chapters. The short version, in an
Ubuntu 24.04 / WSL2 terminal:

```sh
./install-deps.sh                       # once: apt packages
mkdir -p roms
cp /path/to/FE8U.gba roms/fe8u.gba      # clean Sacred Stones (USA)
cp /path/to/FE7U.gba roms/fe7u.gba      # clean Fire Emblem (USA): FE7 portraits, animations and stats are read from it
./setup.sh                              # once: fetches and builds the pinned engine and tools
./build.sh                              # -> build/BladeAndStone.gba and build/BladeAndStone.ups
```

No ROM data is committed. Everything under `gen/`, `build/`, `engine/`, `.toolchain/` and `maps/tilesets/` is
downloaded or derived from the ROMs you supply.

## Layout

| Path | What |
|---|---|
| `src/` | the game: chapter events, script text, small data tables, C engine changes |
| `data/` | the cast (`cast.csv`), hand stat adjustments (`cast_tweaks.csv`), bosses and enemies (`npcs.csv`) |
| `maps/*.tmx` | maps, edited in Tiled |
| `overlay/` | our edits to engine files (configs, designer config, main.event) |
| `tools/` | the generators the build runs, plus helpers (`newmap.py`, `chapterinfo.py`, `numbercheck.py`) |
| `tools/playtest/` | headless emulator harness and auto-player used to play builds end to end |
| `docs/` | story bible and research notes |

## Credits

Built on [FE8U C-SkillSys](https://github.com/FireEmblemUniverse/fe8u-cskillsys) (Mokha and contributors),
FE-CLib-Mokha, ColorzCore / Event Assembler, the Individual Animation patch (7743), and the FE8 decompilation project for reference.
Fire Emblem is © Nintendo / Intelligent Systems. This is a non-commercial fan project.
