# Blade & Stone — Research & Decision Memo (Sept 2026)

What the best FE8 hacks do, what the current engine options are, and what we're adopting.
Decisions are marked **DECIDED** (Nat can veto any of them) or **TEST FIRST** (depends on a technical check).

---

## 1. What was surveyed

| Hack | Why it matters to us |
|---|---|
| **The Morrow's Golden Country (TMGC)** | The explicit design reference. Its buildfile is open source, and I read it directly. |
| **Vision Quest** | Widely called the best-polished long FE8 hack. It uses a deliberately restrained skill design. |
| **The Last Promise, The Four Kings, Justice and Pride, Staff of Ages, Souls of the Forest** | The most-cited "superb level design" and full-campaign FE8 hacks. |
| **"OK Redux" / FE8 Plus vanilla-improvement patches** | A concrete list of QoL items players now treat as standard. |
| **FE8U C-SkillSys** ("Modern c-skillsystem", FEU org, LTS 3.3, updated Sept 2026) | The current-generation engine base. I built it here and booted it. |
| **FE8 Skill System (EA/asm)** | Our current base. It's what TMGC was built on. |
| **FE8 decompilation** | Reference for how everything actually works. |

## 2. What the good hacks have in common

**TMGC** (from its source tree):
- STR/MAG split, raised HP caps (80 player / 120 enemy), and higher stat and promotion gains
- Tellius-style base conversations and a support rework with personalized bonuses
- Free-roam interlude chapters (Mokha's FreeMovement)
- Combat arts, custom autoleveling, reworked crit and hit
- Staff rework, heal-amount display, droppable-item icons, and "less annoying fog" (bumping into a fog enemy doesn't waste your turn)
- A conversation viewer, and Normal/Hard/Lunatic plus growth options

**Vision Quest:**
- *"Pared down skills to give units a niche without making anything wonky."* No proc skills; one class skill at level 15.
- Armor knights get 5 move. Bows are stronger. Throwing weapons are weaker. Effective weapons are actually useful.
- A player-phase focus and threatening enemies. Early Warp and Rescue. FE5-style trading. Tellius supports.

**Shared lessons:**
- Level design is praised far more than mechanics count.
- Every unit needs a niche.
- Keep skills readable: few, meaningful, and visible.

**Standard QoL checklist** (from vanilla-improvement patches):
- Growths on the stat screen (Select)
- Global enemy range
- HP bars with damage warnings
- Droppable and stealable item icons
- L to toggle animations and to cycle enemies
- Battle stats with animations off
- Heal-amount display
- Hold A for faster movement
- Skip the health-and-safety screen
- Fast text by default
- Act after Talk or Support
- A to fast-forward battle animations
- Option to disable staff and dance animations
- Monster weapon stats visible
- Steal with a full inventory
- A 200-item convoy
- Item combining in prep

## 3. The big technical finding: roster limits

These are FE8 engine facts, checked in the decompilation:
- **The save holds at most 51 player units** (`UNIT_SAVE_AMOUNT_BLUE = 51`). RAM has 62 blue slots, but anything past 51 is lost on save.
- **Per-character records (BWL)** exist for only a limited range of character IDs:
  - Vanilla and the old Skill System: IDs 0x01–0x45 (69). The old system stores *learned* skills there.
  - C-SkillSys: IDs 0x01–0x32 (51). It stores learned and equipped skills **and support progress** there. It flags this value as hard to change.

The v1 bible's "77 veterans in one army" is **not possible on this engine.** With 77 characters, at least 26 can never be in the permanent army at the same time.

**DECIDED: a tiered, rotating cast.** This also serves the canon review's "large-cast realism" point: kings have kingdoms and people have jobs.

- **Core (≤ 51, IDs 0x01–0x32):** the permanent army over the course of the game. Full features: learn and equip skills, growing supports.
- **Company (IDs 0x33+):** side-party and guest veterans who join for arcs, leave, and some return. They keep fixed personal and class skills and preset supports, but can't learn or equip new skills. Every veteran is playable at some point. The army never holds more than 51 at once.
- **Who's in which tier** is a writing decision made per act. The tier is invisible to players except that Company units don't show a skill-learning prompt.
- **TEST FIRST:** whether save space allows raising C-SkillSys's 51 to 69. If yes, most Company units get promoted to Core.

## 4. Engine base

**DECIDED: migrate to FE8U C-SkillSys (LTS)** while we only have two chapters. The cost now is small and would grow with every chapter.

| | Old Skill System (current) | C-SkillSys |
|---|---|---|
| Language | EA + asm | C against the decompilation headers, which is much easier for me to write custom mechanics in (seam tiles, the Rausten Stone, Echo limits) |
| Skills | ~250 | 500+, with up to 0x400 IDs |
| STR/MAG | optional add-on | built in |
| Skill equip | fixed plus 4 learned | 2 personal + 2 class fixed, plus up to 7 equippable, chosen in prep (3H-style) |
| Combat arts | no (TMGC added its own) | built in |
| Maintenance | active | active, with an LTS channel |
| Full-feature character IDs | 69 for learned skills; supports unlimited | **51** (the downside) |
| Builds here? | yes | **yes, verified.** It needed gcc-arm, a source build of grit/gbalzss, and gawk. |

It also includes a `LeaderFix`, the exact cursor bug I patched by hand. Its authors hit the same problem.

**The configuration we'll use:**
- STR/MAG split **on**.
- Equippable skills **max 3**, so a GBA screen stays readable (Vision Quest lesson).
- Combat arts **on**: weapon-based, costing durability. They give veterans tactical depth at high numbers.
- Engage-style combo attack **off**, since it's slow and alien to the GBA feel.
- Surround penalty **off** and ranged hit decay **off**. Both are hidden modifiers that muddy the forecast.
- Guaranteed level-up retry **on** (no empty level-ups).
- Level-ups: GBA-style random on Normal and Hard. Fixed growths as a player option **[TEST FIRST]**.

## 5. FE7 visuals

Checked directly in both ROMs:
- **FE7's battle-animation table (0xE00008) uses exactly FE8's format** (0xC00008): name, mode table, a compressed script holding absolute pointers to compressed sprite sheets, compressed OAM for each facing, and a compressed palette.
- A port means decompressing the script, copying and relocating the sheets, then recompressing. **DECIDED: port these from the user's FE7 ROM at build time.**
  - Eliwood (Lord `erlm`, Knight Lord `lokm`)
  - Hector (Lord `helm`, Great Lord `grlm`)
  - Lyn (Lord `allf`, Blade Lord `bllf`)
  - Nomad and Nomad Trooper (`nomm`, `notm`), Bard (`brdm`, Nils), Dancer (`danf`, Ninian), Archsage (`ssam`, Athos)
- **Also port:** FE7 standing and moving map sprites for those classes, and FE7's character-specific battle palettes (Eliwood's blue, Hector's, Lyn's green, and so on).
- **FE7 lord classes become real classes** instead of Paladin/General clones.

## 6. QoL: adopt, and how

| Feature | Plan |
|---|---|
| Danger zone, HP bars, battle stats with animations off, L-toggle animations, Talk/Support don't end turn | C-SkillSys has equivalents or we carry the patches over. **Adopt.** |
| **Growths on the stat screen** | **Adopt.** A stat-screen page toggle. |
| **Fast text default, skip health-and-safety** | **Adopt.** A small patch. |
| **Heal amount display, drop/steal icons** | **Adopt.** |
| Hold A to move faster; A to fast-forward battle animations | **Adopt if a clean patch exists**, otherwise write it in C. |
| L cycles enemies | **Adopt.** |
| 200-item convoy | C-SkillSys has it built in. **Adopt.** |
| Convoy access on prep | **Adopt.** |
| Casual mode at new game | **Adopt.** |
| Less-annoying fog (TMGC) | **Adopt**, since several Act II and III maps will use fog. |
| Undo (phase-start suspend) | C-SkillSys can autosave at player-phase start. **Adopt** as an option. |
| Tellius-style base conversations / free-roam interludes | **TEST FIRST.** Port FreeMovement or use prep-screen base convos. |
| Staff and dance animation toggle | Nice to have, low priority. |

## 7. Design pillars from the research, applied to us

- **Level design first.** Every map gets a sketch with an intent sentence (what it tests, where the pressure comes from) before any tiles are placed. It then goes through a bot playtest plus a numbers check (enemy damage vs. our defenses) before it's sent to Nat.
- **Skills stay restrained.** One personal skill per character that reads like them, one class skill, and a few learnable skills. Almost no proc-RNG skills.
- **Enemies are threatening.** Our first bot playthrough went deathless. That's a signal that the Prologue and Chapter 1 are too soft for veterans.
- **Every unit gets a niche**, especially the nine cavaliers.

## Sources
- [TMGC FEU thread](https://feuniverse.us/t/fe8-fire-emblem-the-morrows-golden-country-complete/16284) · [TMGC buildfiles](https://github.com/Retina1/TMGC_Buildfiles)
- [Vision Quest FEU thread](https://feuniverse.us/t/fe8-complete-fire-emblem-vision-quest-v3-by-pushwall-1-oct-22/3815)
- [FandomSpot: best FE ROM hacks](https://www.fandomspot.com/best-fire-emblem-rom-hacks/)
- [OK Redux vanilla-improvement patches](https://feuniverse.us/t/fe6-fe7-fe8-gba-fire-emblem-the-ok-redux-vanilla-improvement-patches/28082)
- [Modern c-skillsystem FEU thread](https://feuniverse.us/t/fe8-modern-c-skillsystem-3-3-0-lts/24614) · [fe8u-cskillsys repo](https://github.com/FireEmblemUniverse/fe8u-cskillsys)
- [FE8 Skill System](https://github.com/FireEmblemUniverse/SkillSystem_FE8)
- [FE8 decompilation](https://github.com/FireEmblemUniverse/fireemblem8u)
