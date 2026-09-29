# Hacking on Blade & Stone

This is the handbook for changing the game yourself: setting up a machine, the edit-build-play loop, and
step-by-step recipes for the common changes. It assumes you're comfortable in a terminal. It doesn't assume
you know FE8 hacking internals.

**The one rule:** you edit `src/`, `data/` and `maps/`. Everything in `gen/`, `engine/`, `build/` and
`.toolchain/` is generated or downloaded and gets **overwritten on the next build**. Every build starts again
from your clean ROMs plus this repo, so the repo is the whole game.

> **Why not FEBuilder?** The game runs on [C-SkillSys](https://github.com/FireEmblemUniverse/fe8u-cskillsys),
> a C engine FEBuilder doesn't understand. FEBuilder can open a *copy* of the built ROM to look around,
> but magic stats, skills and the FE7 battle animations live in tables it can't see, and saving from it
> can overwrite data. Anything you change there is also lost on the next build. FEBuilder is still handy as
> a scratchpad on a *vanilla* ROM, for looking up an item ID or previewing a palette.

---

## 1. Setting up (Windows with WSL2, or Linux)

Tested on a clean Ubuntu 24.04, the default WSL2 distro. It has not been run on a real Windows machine yet.

**Windows only:** open PowerShell as administrator, run `wsl --install`, reboot, and finish the Ubuntu
first-run prompt (it asks for a username and password). From then on, "a terminal" means the **Ubuntu** app.

In the Ubuntu terminal:

```sh
sudo apt update && sudo apt install -y git
cd ~                                   # keep the project in Linux's home folder, NOT under /mnt/c (much faster)
git clone https://github.com/CMApex/fire-emblem-blade-and-stone blade-and-stone
cd blade-and-stone
./install-deps.sh                      # apt packages: ARM compiler, .NET 8, Python, build tools (~1 min)
mkdir -p roms
cp "/mnt/c/Users/<you>/<where your ROMs are>/Sacred Stones.gba" roms/fe8u.gba
cp "/mnt/c/Users/<you>/<where your ROMs are>/Fire Emblem.gba"   roms/fe7u.gba
./setup.sh                             # downloads and builds the engine and tools (~2-5 min, once)
./build.sh                             # -> build/BladeAndStone.gba and build/BladeAndStone.ups
```

- **ROMs:** clean, unpatched **USA** dumps of *The Sacred Stones* (`fe8u.gba`) and *Fire Emblem*
  (`fe7u.gba`, needed for the FE7 cast's portraits, animations and stats). `build.sh` checks their checksums
  and says so if one is wrong.
- **Getting at the files from Windows:** in the Ubuntu terminal, `explorer.exe .` opens the project folder in
  File Explorer. The path looks like `\\wsl.localhost\Ubuntu\home\<you>\blade-and-stone`. VS Code with the
  "WSL" extension (`code .`) edits files in place. Vim inside Ubuntu works too.
- **Playing a build:** open `build/BladeAndStone.gba` in mGBA on Windows (through the `\\wsl.localhost` path),
  or send `build/BladeAndStone.ups` to your phone and patch it there as usual.
- **Maps:** install [Tiled](https://www.mapeditor.org) for Windows (free). See section 4.
- `setup.sh` needs internet: GitHub, plus nuget.org for the .NET part (ColorzCore, the event assembler).
  It installs nothing system-wide; everything goes into `engine/` and `.toolchain/`.

## 2. The loop

```sh
./build.sh                    # ~1-2 min; prints "Built build/BladeAndStone.gba ..." when it worked
```

If something is wrong, the build stops with a message, usually naming the file and line:

| You see | Meaning |
|---|---|
| `gentext: src/Text/ch1.txt:42: ...` | a text problem (unknown `[Code]`, missing `[X]`, 4 faces, see §3) |
| `buildmaps: maps/ch1.tmx: ...` | a map problem (empty tile, flipped tile, missing property) |
| `cast.csv: ...` / `cast_tweaks.csv: ...` | a typo in the character data |
| `BUILD FAILED — see build/make.log` | the engine or the event assembler failed; search the log for `Error` and the file/line |

Event-script errors come from the event assembler (ColorzCore) and look like
`src/Events/Ch1.event:112:1: Error: ...`. Line numbers refer to the copy in
`engine/Contents/BladeAndStone/`, which mirrors `src/` exactly, so the same line in `src/` is the one to fix.

Two machines can produce ROMs whose checksums differ by a few bytes. grit (the graphics converter) compresses a
handful of engine images slightly differently depending on the machine; the decompressed images are identical,
so it's the same game.

If a build ever seems stale (a change that doesn't show up), `./build.sh --clean` rebuilds the engine from scratch
(about 5 minutes).

**Debug builds** start units in handy places (Eirika next to the Prologue seize, Hector next to the Ch1 boss):

```sh
BS_DEFINES="BS_DEBUG_SEIZE BS_DEBUG_CH1" BS_OUT=debug ./build.sh     # -> build/debug.gba
```

Anything wrapped in `#ifdef BS_DEBUG_...` in the event files only exists in debug builds.

---

## 3. Dialogue and text

All script text is in `src/Text/`: `prologue.txt`, `ch1.txt`, and `characters.txt` for names, descriptions
and class names. `blade.txt` just includes them. Each message is a `## NAME` header followed by its text,
ending in `[X]`:

```text
## BS_C1_Talk
[OpenMidLeft][LoadHector][OpenMidRight][LoadEliwood][OpenMidLeft]You're late.[A]
[OpenMidRight]You started without me.[A][X]
```

Events refer to messages by name (`Text(BS_C1_Talk)`), so adding a new message is just adding a new `##`
block. The build assigns the IDs.

| Code | Does |
|---|---|
| `[OpenLeft]` `[OpenMidLeft]` `[OpenFarLeft]` `[OpenFarFarLeft]` (and the `Right` versions) | choose who speaks / where the next face goes |
| `[LoadHector]`, `[LoadEirika]`... | put that character's portrait at the chosen position (generated for the whole cast from `cast.csv` keys) |
| `[LoadActiveUnit]` | portrait of whoever triggered the event (the unit visiting a village, say) |
| `[LoadVillagerMan]` `[LoadVillagerElder]` `[LoadVillagerBoy]` | generic villagers (more: add `[LoadFace][0xNN][0x01]` aliases to `codes.txt`) |
| `[ClearFace]` | remove the face at the current position |
| `[NL]` | new line (a box holds **two** lines) |
| `[A]` | wait for the A button (end of a box) |
| `[.]` `[....]` | short pauses |
| `[ToggleMouthMove]` | stop/start the mouth moving (for `...` beats) |
| `[X]` | end of message (required) |

Shortcuts you can define yourself live in `src/Text/codes.txt` (`[Beat]`, `[Blink]` and so on; comments go
on their own line there). The built-in codes are in `engine/Contents/Texts/textdefs.txt`. The build rejects
unknown codes by name, and boxes with more than two lines.

**⚠ Three faces at most.** FE8's fourth portrait slot shares video memory with the moving-unit sprite. If a
unit is mid-action (a boss kill ending, a talk or visit), a fourth face gets corrupted, like the Oswin bug in
the first demo. The build rejects any message with 4 faces on screen at once. To swap someone in, `[ClearFace]`
somebody first. The only exception: put `// allow-4-faces` on the line right above a `##` header for scenes
that run with **no unit acting**, like chapter openings before or right after units load (`BS_C1_Opening`
is one).

**Names:** FE7 characters use `BS_Name_<Key>` / `BS_Desc_<Key>` in `characters.txt`. For any FE7 character
without one there, the build uses their FE7 text (see `gen/cast_text.txt`); write your own in
`characters.txt` to override it. FE8 characters keep their vanilla names.

---

## 4. Maps (Tiled)

Maps are Tiled files in `maps/` (`prologue.tmx`, `ch1.tmx`). The tile graphics come from your ROM, so the
tilesets are generated into `maps/tilesets/` (not committed) by every build, or by hand:

```sh
python3 tools/maptiles.py            # tilesets for the maps in maps/ (run once after cloning, before opening Tiled)
```

**Editing:** open `maps/ch1.tmx` in Tiled (on Windows through `\\wsl.localhost\Ubuntu\home\<you>\blade-and-stone\maps`).
Pick tiles from the tileset panel and paint them with the stamp brush (B). Select a tile in the tileset to see
its **terrain** (Plains, Forest, Fort...) under Custom Properties. The terrain decides movement, defence and
avoid, so a tile that *looks* like a wall but says `Plains` walks like plains. Save, then `./build.sh`.

- **Coordinates:** Tiled's status bar shows the tile under the mouse. Those are exactly the `[x,y]` used in the
  event files (`UNIT ... [12,2]`, `Village(0x10, ..., 17, 11)`).
- **Rules the build enforces:** every tile painted, no flipped or rotated tiles (FE8 can't), at least 15x10.
- **Which tileset** a map uses is set by the map's custom properties `obj1`, `obj2`, `pal`, `config`
  (Map > Map Properties). The chapter automatically loads whatever the map says. After changing them, run
  `python3 tools/maptiles.py` and reopen the map.
- **Doors, village gates, broken walls** are *map changes*: small tile patches applied during play, written in
  the chapter's event file (`TileMap(...)`, see `BS_P_MapChanges` in `src/Events/Prologue.event`).
- **Starting a new map:** `python3 tools/newmap.py harbor2 --from-vanilla 0x19` copies a vanilla chapter's map
  as a base, or `python3 tools/newmap.py harbor2 --blank 22 18 --tileset-of 0x19` gives you an empty one.
  The chapter numbers are chapter-table indices; `python3 tools/chapterinfo.py 0x19` shows what a vanilla
  chapter uses.
- `tools/solvemap.py` and `maps/sketches/` are an optional generator that turns ASCII terrain into a first
  draft. That's how the Prologue started. It overwrites the `.tmx`, so only use it to begin a map.

---

## 5. Characters and stats

**The cast** is `data/cast.csv`, one row per playable character:

| column | meaning |
|---|---|
| `pid` | character ID. Core characters must be below `0x33`; `0x3B`–`0x3F` are reserved |
| `key` | short name used everywhere (`BS_PID_HECTOR`, `[LoadHector]`, `BS_Name_Hector`) |
| `tier` | `core` or `company` (story role; core gets full supports/skills) |
| `game`, `src` | where their canon data comes from (`fe7`/`fe8` and their ID in that game) |
| `class`, `level` | their class (FE8 class ID, or `0x77`–`0x79` for the new lords) and level |
| `skill` | personal skill, e.g. `QuickRiposte` (list: `engine/docs/SkillInfo.md`, names without `SID_`) |
| `ranks` | weapon ranks, e.g. `Axe:A Sword:C` (empty = canon ranks) |
| `notes` | free text; the word `growing` marks the four still-growing characters |

A veteran's stats are **derived**, not typed in: the build replays their canon career (levels, promotion,
more levels) and puts the result in their current class. `gen/cast_report.md` shows every final stat, growth
and the path taken. Read it after changing anything.

**To adjust someone,** add a row to `data/cast_tweaks.csv` instead of fighting the derivation:

```csv
key,tweaks,why
Hector,def+2 spd-1 g_def+10,should feel tankier than Oswin at the docks
Nino,mag=9,
```

`+N`/`-N` adjusts the derived value, `=N` sets it; `hp str mag skl spd lck def res con` are stats (as shown in
game), `g_<stat>` are growths in %. Class caps still apply.

**Bosses and generic enemies** are `data/npcs.csv`, with the stats typed in directly (level, bases, growths,
ranks). `0x7F Husk` is the generic human enemy and `0xAA Monster` the generic monster; every enemy using that
ID gets those bases plus class bases.

---

## 6. Chapter events

Each chapter is one file in `src/Events/`. It opens with a note on the design intent, then:

1. **chapter data** (`ORG ChapterDataTable + ...`): tileset (from the map), music, name, goal text
2. **pointer list** and the event lists: turn events, talk events, locations (villages, houses, shops), misc (win/lose)
3. **units**: `UNIT` lines grouped into lists
4. **scenes**: the scripts those lists point to

### A unit line

```text
UNIT BS_Husk 0x40 0x00 Level(4, Enemy, True) [13,17] 0b 0x0 0x0 0x0 [SteelAxe, 0, 0, 0] DefaultAI
     who     class leader level  side  auto   x,y     (leave as is)    up to 4 items      AI
```

- **who:** `BS_PID_<KEY>` for cast members, `BS_Husk` / `BS_Monster` / a boss for enemies.
- **class:** hex ID or an FE8 name (`Warrior`, `Paladin`, `Wight`...). Names and item names are in
  `engine/Tools/EventAssembler/EA Standard Library/FE8 Definitions.txt`.
- **`Level(lv, Enemy, True)`:** the last value is auto-level. For generics, `True` means the class growths
  are applied for each level. ⚠ The engine gives *promoted* generic classes about 10 extra hidden levels on
  top of that, so a "Level 4 Warrior" is a lot stronger than it sounds. Check with the numbers tool (§8).
- **AI:** `DefaultAI` (charges), `AttackInRangeAI` (waits until you step into its range), `NeverMoveAI`
  (holds its tile, for bosses), `GuardTileAI`, `HealUnits`, `NoAI` (players). More in
  `EA Standard Library/AI Helpers.txt`.

### Recipes

- **Move an enemy:** change its `[x,y]`. Hover in Tiled to find the coordinates.
- **Add an enemy:** copy a `UNIT` line inside the enemy list (above the lone `UNIT` that ends the list).
- **Hard mode only:** put it in the chapter's `..._EnemiesHard` / `..._ReinfHard` list. Those lists are only
  loaded after the `CHECK_HARD` test in the scenes.
- **Reinforcements:** a `TurnEventEnemy(0, SceneName, turn)` line in the turn list plus a scene that does
  `LOAD1 0x1 UnitList` / `ENUN`. See `BS_C1_Reinforce`.
- **Give a village an item:** `VillageEventItem(TextName, background, Item)`. Villages, houses and the shop
  are in the chapter's `Location` list. The first number in `Village(0x10, ...)` is a flag: use a different
  one (`0x10`, `0x11`...) for each location in the chapter.
- **Shop stock:** the `SHORT ... 0` line under `BS_C1_Shop`.
- **Boss conversations and death quotes:** `src/Events/Quotes.event`.
- **Who the cursor starts on each chapter:** `src/Data/Leaders.event`.

### Adding a chapter

1. Map: `python3 tools/newmap.py ch2 --from-vanilla 0x0B` (or blank), then edit it in Tiled.
2. `python3 tools/chapterinfo.py 2` shows vanilla chapter 2's **map slot, map-changes slot and events slot**.
   Reuse those slots for the new chapter, and the tile animation of a vanilla chapter with the same tileset
   (`newmap.py` prints it).
3. Copy `src/Events/Ch1.event` to `Ch2.event`: set `#define BS_CH2 0x02`, use `BS_MAP_TILESET_CH2`, the new
   slots in `EventPointerTable(...)`, and rename every `BS_C1_` label to `BS_C2_` (labels must be unique
   across the whole game).
4. Include it in `src/BladeAndStone.event` in its own `{ }` block, add `src/Text/ch2.txt` to `blade.txt`,
   add the leader to `src/Data/Leaders.event`.
5. Point the previous chapter's ending at it: `MNC2 0x2` (the Ch1 ending currently returns to the title
   with `MNTS`, because the demo ends there).

---

## 7. Engine settings and code

- `overlay/include/configs/configs.h` switches engine features on and off.
  `overlay/Data/DesignerConfig/designer-config.c` holds game-design knobs (skills per unit, level-up rules...).
  Both are copies of engine files with our changes; the build copies `overlay/` over `engine/`.
- `src/Hacks/Core/Core.c`: our C changes (per-chapter leader, camera fix, no Health & Safety, default
  speeds). A function that replaces a vanilla one needs `LYN_REPLACE_CHECK(Name);` above it **and** a
  `PROTECT`/jump entry in `LynJump.event` next to it; the build checks this.
- C-SkillSys documentation: `engine/docs/` (skills, combat arts, battle system), or the same files
  [on GitHub](https://github.com/FireEmblemUniverse/fe8u-cskillsys/tree/f61f6c20f5dfbd8bf2f436f01c40fbd2551d6ef8/docs).

## 8. Checking the numbers

```sh
python3 tools/numbercheck.py build/BladeAndStone.gba src/Events/Ch1.event
```

This prints every enemy's expected stats, including the hidden levels, with damage, doubling and hit rates
against each player unit. Use it after any enemy or stat change to catch "this Warrior one-rounds Serra"
before a playtest does.

`tools/playtest/` has the headless auto-player used to play builds end to end. It's optional and needs
`libmgba-dev`; see its README.

## 9. Where things come from

| Path | What |
|---|---|
| `src/BladeAndStone.event` | content root; includes everything below |
| `src/Events/` | chapters, world map, quotes |
| `src/Text/` | all script text |
| `src/Data/` | small tables (leaders) |
| `src/Hacks/` | C engine changes |
| `data/cast.csv`, `data/cast_tweaks.csv`, `data/npcs.csv` | characters, adjustments, enemies/bosses |
| `data/fe7_faces.csv` | which FE7 portraits get imported |
| `maps/*.tmx` | maps (Tiled) |
| `overlay/` | our edits to engine files |
| `tools/` | the build's generators, written in Python; each file's first lines say what it does |
| `docs/bible.md` | the story and design bible |
| `gen/` | everything generated from your ROMs and the files above (read it, don't edit it) |

**Build order** (`build.sh`): check ROMs → import FE7 portraits → map tilesets and maps → vanilla tables →
characters and classes (`gencast.py`) → FE7 battle animations (`port_banims.py`) → text (`gentext.py`) → copy
everything into `engine/` → `make` (compiles the C and assembles all events) → patch the moved animation
table → make the `.ups`.

## 10. Getting help

- Fire Emblem Universe forums (feuniverse.us) and their Discord: the C-SkillSys and Event Assembler
  people are there.
- Event Assembler codes: `engine/Tools/EventAssembler/Language Raws/FE8/` (every event code and its
  parameters) and `EA Standard Library/` (the friendly macros used here).
- The FE8 decompilation (github.com/FireEmblemUniverse/fireemblem8u) is the reference for how the vanilla
  game works.
