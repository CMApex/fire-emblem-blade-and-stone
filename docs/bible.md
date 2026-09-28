# Fire Emblem: Blade & Stone — Design Bible (v3)

*FE8 hack on the C-SkillSys engine. FE7 and FE8 veterans, one original story, about a year after both games.*

Internal working doc. v3 turns most of v2's open questions into **decisions**. Nat can veto any of them. Anything still undecided is tagged **[OPEN]**. Other tags: **[NEEDS SCRIPT]** (has to prove itself in scenes), **[UNTESTED]** (mechanics with no playtest yet), **[CUT IF SLOW]**.

Companion docs: `docs/research-memo.md` (engine and feature research), and the change log in §15.

---

## 1. Premise

In the same year, on two continents across the Gray Sea, two wars ended.

In **Elibe**, Eliwood, Hector and Lyn killed Nergal on Valor. Nils went back through the Dragons' Gate and sealed it from the far side. Ninian stayed with Eliwood, knowing that Elibe's changed air means her strength will never return.

In **Magvel**, Eirika and Ephraim defeated Fomortiis. Four of the five Sacred Stones were destroyed during the war. The fifth, Rausten's, survived and became the prison of the Demon King's soul. His body was destroyed.

Neither continent knows the two victories touched the same old wound, the **seam** between worlds. The Scouring and the Ending Winter tore it a thousand years ago. The Gate is a road *through* it to the world the dragons went to. Two centuries later, Magvel's five Stones bound Fomortiis, and without anyone knowing, they also braced Magvel's side of the seam.

Now four braces are gone, the fifth is already full, and the Gate is sealed from the far side. The load redistributes. Scars open at the ruined Stone shrines and under Valor. Then the Gray Sea starts to glow, and to sing.

*(Writers' note, never dialogue: both victories were right, and both had consequences.)*

## 2. Tone & Writing Rules

Serious, with real stakes. Not grimdark. FE7/FE8's earnest register. TMGC's sincerity.

1. The bible knows the theme. Characters rarely say it. No closing aphorisms.
2. Humor comes from personality clashes, and lives in supports, base conversations and quiet stretches. It is **not** a pressure valve after every dark beat. Let sadness sit.
3. No modern therapy vocabulary. No thesis phrasing. No "you're right, but..." ping-pong.
4. "Genocide" belongs in this document. Dialogue uses *slaughter, purge, hunted, driven out, the Scouring*.
5. Scenes may end unresolved. Echoes especially.
6. Veterans are people, not their crossover joke.
7. Kings are kings. Rank, duty and absence have weight.
8. Titles and forms of address follow the source games (Lord Hector, Princess Eirika, Your Majesty, Sir Kent).

## 3. Canon Baseline (checked against the scripts)

- **Rausten's Stone survived** and holds Fomortiis's soul. His body was destroyed. (FE8 Final: *"The Demon King's soul has been bound once more."* / *"We've destroyed the Demon King's body."*) Destroyed Stones: Renais, Frelia, Jehanna, Grado.
- **Fomortiis is an individual demon.**
- **The Scouring** (~1,000 years before FE7) and **Fomortiis's fall** (~800 years before FE8) are separate events.
- **The Gate leads to another inhabited world** where dragons live stably, with humans too (Nils).
- **Ninian fades because of Elibe's air** (FE7 Final: *"our strength will never return"*). The closed Gate removed her road back. It didn't cause her condition.
- **Arcadia** has centuries of peaceful coexistence.
- **Vigarde** died before the invasion. Lyon reanimated the body.
- Orson's wife is **Monica**.
- **Valor** is off Lycia's southern coast.
- **Desmond** is alive.
- **Nergal is Ninian and Nils's father.** Treated as true, known to almost no one.

## 4. FE6 Compatibility: **STRICT** (DECIDED by Nat)

Everything in Blade & Stone must leave the world able to become FE6's Elibe.

| Constraint | Consequence for us |
|---|---|
| Roy and Lilina (born ~985) don't exist yet | No children onscreen. Hector is **unmarried**. Lilina's mother is never named or shown. |
| Ninian dies young, before FE6 | **The ending cannot cure her.** At the end she chooses Elibe and Eliwood again, with full knowledge. That's the story's emotional cost. |
| Arcadia is secret in FE6 | Arcadia's location stays secret. Only a handful of the army ever goes there. Its people swear them to silence. |
| No return of dragons by FE6 | **The door is narrow, hidden and guarded.** It allows deliberate passage, not migration. |
| Hector, Eliwood, Zephiel, Desmond all reach FE6 | Nobody on that list dies. Desmond's scheming stays local. Zephiel appears at most in background politics. |
| Nils isn't in Elibe in FE6 | Nils returns to the far side at the end. |
| Athos is dead | He appears only as an Echo, playable briefly (§8). |
| Fae is in Arcadia | She can exist offscreen, but no cameo (nothing to gain, much to break). |
| Karla, Pent, Louise, Bartre and others have FE6-era futures | Nobody with an FE6 descendant or later appearance dies. |

## 5. Cosmology

```
Elibe  ──►  the seam (a damaged layer between worlds)  ──►  the dragons' world
                        ▲
      Magvel's Sacred Stones braced it from this side (4 of 5 now gone)
```
- **The seam** is a wound between worlds that behaves like a **pressure system**. When one outlet closes (the Gate), stress moves to the weakest points (the old Stone shrines). It holds fragments, failed crossings, residue, and memories without whole people. **DECIDED:** that's how it physically works.
- **Why the Gray Sea was always hard to cross:** the seam runs under it. Storms come out of nowhere, compasses wander, and sailors hear singing. **DECIDED.**
- **The Stones and the seam: a side effect.** The Stones' makers built prisons for Fomortiis's power. The bracing was an accident nobody recorded, which is why nobody knows how to fix it. **DECIDED.**
- **Fomortiis and the seam:** Fomortiis found and fed on power leaking through Magvel's side of the seam. That's why the Stones that bound him also braced it. He is himself, not the seam. **DECIDED.**
- **The Hollow Throng** is the aggregate danger inside the seam: corrupted residue and fragments warped by centuries of pressure, with traces of dragons, humans and Fomortiis's influence. **Not** mad dragons, and **not** Fomortiis. Dragons are not the corruption.
- **The Rausten Stone** now bears a load it was never meant to carry alone. It's the Act I pressure point (§11). Fomortiis is **not** free.

## 6. Rules of the Crossover

1. **Time:** about a year after both games. Everyone is a veteran.
2. **Geography:** one world. **Magvel lies south to southeast of Elibe** across the Gray Sea, and Valor sits off southern Lycia at the sea's northwest edge.
3. **FE7 continuity:** Eliwood/Ninian married (it happened soon after FE7). **Lyn unpaired:** she went back to Sacae, and Caelin is entrusted to Ostia. **Roy is not born.**
4. **FE8 continuity is composite:** compatible material from both routes is usable, and where they conflict, one version is chosen. All recruitable FE8 units survived. Orson and Glen are dead.
5. **Lyon (DECIDED, hard rule for his Echo):**
   > Lyon was genuinely corrupted, and the Demon King's hold on him grew until it was nearly total. But he was never only a puppet. The jealousy was his own. So were some of the lies, and some of the choices, the ones he made while telling himself he was still trying to save everyone. He loved Eirika and Ephraim and resented them in the same breath. Near the end, what remained of him wanted to be stopped, and also wanted to win. His Echo may show any of these fragments, but never all of them at once, and it never resolves which one was "really" him.
6. **No time travel, no alternate selves.** Crossings and Echoes come from the seam.
7. **Echoes** are fragments of the dead and incomplete by nature (§9).
8. **Ninian and Myrrh** are the emotional axis of the dragon plot, from different histories. Don't merge them into one dragon mythology.

## 7. Who Governs While the Heroes Are Away (DECIDED)

| Realm | Arrangement | Consequence |
|---|---|---|
| **Ostia** | **Oswin is regent** from Chapter 1's end until Act II, when the Lycian League sends a council under Marquess **Santaruz**'s old steward. Then Oswin rejoins. | Oswin plays in Ch. 1 and then leaves. Hector's "Oswin, Ostia is yours" stays as written. |
| **Pherae** | **Marcus** is regent, as he was during Eliwood's absence in FE7. Isadora and Harken stay with him. | Marcus, Isadora and Harken are Company-tier and join late, briefly, when the war reaches Lycia again. |
| **Renais** | Ephraim won't leave the crown with no one to wear it. **Seth is offered the regency and refuses** because he won't leave Eirika. The Renais **Council of Regency** (new NPC: Chancellor **Orlan**, an old minister of Fado's) governs, and **Gilliam stays** to hold the capital's garrison for Act I. | Gilliam plays in Ch. 2, stays, and rejoins in Act II. Ephraim's struggle with leaving is a Ch. 2 thread. [NEEDS SCRIPT] |
| **Frelia** | King Hayden rules. Innes goes, grudgingly. Tana goes. | |
| **Rausten** | Mansel rules. L'Arachel goes "on a holy crusade," as usual. | |
| **Grado** | Knoll and Duessel are part of the reconstruction council. Duessel leaves only when the Hollow Light (Ch. 8) forces it. | |
| **Sacae** | Lyn rides out with the Kutolah's blessing. Kent and Sain are *not* her retainers anymore. They serve Ostia-administered Caelin, and they come to her. | |

## 8. Cast: Tiers, Classes, Personal Skills (DECIDED)

**Engine facts (see the research memo):** the save holds **51 player units**, and C-SkillSys gives full features (learned and equipped skills, growing supports) only to **character IDs below 51**.

- **Core tier (50 IDs, 0x01–0x32):** the permanent army. Full features.
- **Company tier:** side-party and guest veterans who join for arcs, leave, and some return. They have fixed personal and class skills and preset supports.
- **The army never holds more than 51.**

**Everyone starts in a promoted class** except four who are still growing: **Ross, Amelia, Ewan, Nino**. They promote mid-game, so the game keeps a small promotion arc.

Personal skills come from C-SkillSys's catalog. Each is picked to *read like the character*. Proc (random-activation) skills are avoided except Jaffar's, which is canon.

### 8.1 Core (50)
| Char | Class | Personal skill | Why | Joins |
|---|---|---|---|---|
| Eirika | Great Lord (F) | Charisma (+10 hit/avo to allies within 3) | holds people together | P |
| Ephraim | Great Lord (M) | Charge (+1 dmg per 2 tiles moved) | never stops moving | 2 |
| Seth | Paladin | Loyalty (near a lord: −3 dmg taken, +15 hit) | His power is tied to Eirika. This also keeps him from Jagen-soloing. | P |
| Forde | Paladin | AlertStance (Wait only: +15 avo) | lazy, and it works | P |
| Kyle | Great Knight | Pragmatic (foe not full HP: +3 atk, +1 def/res) | practical | P |
| Franz | Paladin | KnightAspirant (HP>75%: +2 dmg, +15 avo) | young knight | 2 |
| Moulder | Bishop | StaffSavant (+1 staff range) | the old hand | 2 |
| Vanessa | Falcon Knight | Perfectionist (full HP: +15 hit/avo) | exacting | 4 |
| Ross | *Fighter* (growing) | QuickLearner (doubles vs higher-level foes) | the kid among legends | 2 |
| Colm | Rogue | Pickup (take foe's last item on kill) | thief | 4 |
| Neimi | Sniper | Patience (attacked: +10 avo) | quiet courage | 4 |
| Innes | Sniper | Vanity (+2 dmg, +10 hit at range 2) | pride | 4 |
| Tana | Falcon Knight | SocialButterfly (2× support gain) | everyone's friend | 4 |
| Lute | Sage | Focus (+10 crit with no ally within 3) | aloof prodigy | II |
| Ewan | *Pupil* (growing) | Aptitude (+20% growths) | he'll be great | II |
| Cormag | Wyvern Lord | Frenzy (+1 dmg per 4 taken) | grief | 8 |
| Duessel | Great Knight | Obstruct (foes can't pass adjacent) | the Obsidian wall | 8 |
| Knoll | Druid | MaleficAura (enemies within 2 take +2 magic dmg) | dark scholar | 8 |
| L'Arachel | Valkyrie | HolyAura (+1 dmg/+5 hit/avo/crit with light) | righteousness | 6 |
| Joshua | Swordmaster | FranticSwing (hit ≤50%: +50 crit) | gambler | II |
| Tethys | Dancer | Charm (allies within 2 +3 atk) | the stage | II |
| Myrrh | Manakete | DragonWall (dmg reduced by 4%×RES diff) | ancient calm | II |
| Marisa | Swordmaster | FlashingBlade (faster: +15 crit) | Crimson Flash | II |
| Gerik | Hero | Inspiration (allies within 2 +2 dmg, −2 taken) | mercenary captain | II |
| Saleh | Sage | SlowBurn (+1 hit/avo per turn, max 15) | patient teacher | II |
| Eliwood | **Knight Lord** (FE7 anims) | Chivalry (foe full HP: +2 atk/def/res) | chivalry | 1 |
| Hector | **Great Lord (Hector)** (FE7 anims) | QuickRiposte (attacked at HP>50%: doubles) | "hit me, I dare you" | 1 |
| Lyn | **Blade Lord** (FE7 anims) | LawsOfSacae (with 2+ allies in 2×2: +4 atk/spd/def/res) | named for her | 5 |
| Oswin | General | GuardBearing (first EP combat: −50% dmg) | stoic | 1, then regent, back in II |
| Matthew | Assassin | Pass (move through foes) | spy | 1 |
| Serra | Bishop | StunningSmile (vs male foe: −20 avo) | Serra | 1 |
| Rebecca | Sniper | Forager (heal 20% on plain/forest/mountain) | hunter's daughter | 3 |
| Lowen | Paladin | Barricade (halve dmg after first hit) | timid, sturdy | 3 |
| Ninian | Dancer | NightTide (adjacent allies +5 def/res) | protective | 3 |
| Kent | Paladin | Solidarity (adjacent allies +10 crit/crit-avo) | dutiful | 5 |
| Sain | Paladin | QuickBurn (+15 hit/avo, decays per turn) | starts hot, fades | 5 |
| Wil | Sniper | Camaraderie (heal 10% with allies near) | cheerful | 5 |
| Florina | Falcon Knight | Shade (less likely to be targeted) | shy | 5 |
| Rath | Nomad Trooper (FE7 anims) | OutdoorFighter (+10 hit/avo outdoors) | the plains | 5 |
| Guy | Swordmaster | Prescience (initiating melee: +15 hit/avo) | eager | 7 |
| Nino | *Mage* (growing) | Paragon (2× EXP) | still growing | 9 |
| Jaffar | Assassin | Lethality (instant kill, SKL%) | canon | 9 |
| Legault | Assassin | Infiltrator (near 2+ foes: +3 dmg, +15 hit) | thief | 2 (found in P) |
| Heath | Wyvern Lord | Opportunist (+4 dmg when foe can't counter) | deserter's instincts | II |
| Raven | Hero | Wrath (HP<50%: +20 crit) | old anger | II |
| Lucius | Bishop | Peacebringer (all within 2 deal −2) | gentle | II |
| Priscilla | Valkyrie | Amaterasu (allies within 2 heal 20%/turn) | healer | II |
| Canas | Druid | SealResistance (−6 RES to foe after combat) | scholar of dark | II |
| Erk | Sage | MageSlayer (+2 dmg, +10 crit vs mages) | tutor's rigor | II |
| Gilliam | General | StanceSteady (attacked: +6 def) | steadfast | 2, garrison, back in II |

### 8.2 Company (26 + Merlinus)
| Char | Class | Personal skill | Arc |
|---|---|---|---|
| Garcia | Warrior | StrongRiposte (attacked: +3 dmg) | Caer Pelyn |
| Natasha | Bishop | VoiceOfPeace (enemies within 2 −2 dmg) | Rausten |
| Amelia | *Recruit* (growing) | Discipline (2× WEXP) | Grado |
| Artur | Bishop | Slayer (effective vs monsters) | Caer Pelyn |
| Dozla | Berserker | RecklessFighter (both double at HP>50%) | Rausten |
| Rennac | Rogue | Shakedown (steal gold = dmg) | Rausten |
| Syrene | Falcon Knight | HoneFlier (fliers in 2×2 +6 atk/spd) | Frelia |
| Pent | Sage | Gentilhomme (female allies within 2 −2 dmg) | Etruria |
| Louise | Sniper | Demoiselle (male allies within 2 −2 dmg) | Etruria (with Pent, on purpose) |
| Marcus | Paladin | BattleVeteran | Pherae regent, late |
| Isadora | Paladin | Horseguard | Pherae, late |
| Harken | Hero | StanceFierce | Pherae, late |
| Karel | Swordmaster | InnerFlame1 (+10 atk with no ally within 3) | Sacae / wandering |
| Karla | Swordmaster | Bushido | Sacae / wandering |
| Bartre | Warrior | BrashAssault | Caelin |
| Dorcas | Warrior | StanceSturdy | Caelin |
| Wallace | General | Sturdy (full HP: can't die) | Caelin |
| Geitz | Warrior | SteadyBrawler | Western Isles |
| Dart | Berserker | SeaWays (walks on water) | Western Isles, sea maps |
| Hawkeye | Berserker | Hawkeye (always hits) | Nabata |
| Renault | Bishop | Imbue (heal MAG/turn) | Western Isles |
| Fiora | Falcon Knight | Skyguard | Ilia |
| Farina | Falcon Knight | Deal (20% cheaper shopping) | Ilia |
| Vaida | Wyvern Lord | Intimidate (−10 avo to foes within 2) | Bern (a delicate position) |
| Nils | Bard (FE7 anims) | WhitePool (adjacent +5 atk/spd) | Act III guest |
| Athos (Echo) | Archsage (FE7 anims) | DriveMag (allies within 2 +4 MAG) | Act III, fading stats, fixed chapter count |
| Merlinus | *not a unit* | runs the convoy and the shop in interludes | from Ch. 3 |

**[OPEN, technical]:** if the save can be reorganized to fit about 60 full-feature IDs (see the research memo), Company members most tied to the main plot get promoted to Core first: Pent, Louise, Karel, Marcus.

## 9. Echoes

**Rule:** an Echo is a surviving shape (a desire, fear, promise, obsession or memory), not the person. It often lacks the exact part the living most want to hear. Echoes usually leave a scene with **less certainty and more truth.**

| Echo | Faces | Fragment | Guardrail |
|---|---|---|---|
| Leila | Matthew, Jaffar | still planning a future | no absolution for Jaffar |
| Elbert | Eliwood | the promise to protect Pherae | can't know it was kept |
| Uther | Hector | the marquess and brother, still instructing | never says "proud" |
| Lyon | Ephraim, Eirika, Knoll | contradictory fragments (§6 rule 5) | never resolved |
| Glen | Cormag | the sun-general's honor | [NEEDS SCRIPT] |
| Vigarde (the man) | Ephraim, Eirika, Duessel, Knoll | a father's fear, an unprepared heir | no guilt for his corpse's orders |
| Orson | Seth | love that refused death | |
| Monica (separate Echo) | Seth, Orson's Echo | the real woman | her difference from the false body is the scene |
| Nergal (pre-hunger fragment) | Ninian, Nils, Athos | the scholar, with the seed of the hunger in him | fatherhood stays implied |
| Athos | everyone | the last lesson | playable, fading, time-limited |

## 10. The Antagonists

### 10.1 Ysolde of Arcadia
A human raised in Arcadia. Patient, kind, moved by the heroes. Wrong in a way that follows from love.

- **Grievance:** Arcadia's archive keeps what human histories erased. After the Ending Winter weakened the dragons, humans hunted the ones who couldn't hold their true forms. She calls it genocide, and the archive supports her. How the war *began* stays contested. The heroes accept the atrocity without accepting her solution.
- **Seren (DECIDED):** her dragon mother has been declining **for years**. Ysolde *knows* the decline is real. She *believes* the other world is the cure, and Ninian's much faster fading convinced her.
- **How she knows about Magvel (DECIDED):** Arcadia's oldest records hold dragon accounts of a southern shore across the sea, from before the Scouring. **Months ago**, a ship from Magvel reached Valor: the Unwritten's first crossing (§10.2). Its survivors told her about the Stones. The ghost ship in Ch. 1, the *Merchant Grace* out of Port Kiris, is one of the Unwritten's later ships.
- **Goal:** tear the seam open permanently so any dragon can cross and no one can wall them in again.
- **Midpoint offer to Ninian:** *"There is a road back to your strength. You gave it up once for love. I can give you that choice again."*
- **Her turn, in five stages:**
  1. contrary evidence
  2. rationalization
  3. the rupture hurts **Seren**
  4. she tries to control it and learns it can't tell rescue from destruction
  5. she chooses repair

  It costs her Seren, who goes through the rupture and doesn't come back as herself. [NEEDS SCRIPT]

### 10.2 Brother Maelis & the Unwritten (DECIDED)
An excommunicated Rausten priest. In the war he lost his whole parish to Grado's monsters. Since the seam began opening, he's seen **Echoes of his dead** walking on the shore. He believes that if the seam opens fully, the dead come back whole. **He wants to break the Rausten Stone,** the last brace, to force it open.

He mirrors Ysolde: grief, the same seam, a different lost thing (the dead, not the dragons). Where Ysolde is careful, he is careless. The Unwritten are people the war emptied out. **He's wrong about the dead** (Echoes are fragments, §9), and the Echoes' incompleteness is what eventually breaks him. Act II antagonist, Act III tragedy.

### 10.3 Supporting antagonists
- **Desmond of Bern:** funds "archaeology" on Valor for leverage against Lycia. Local and selfish. **Legault** was crewing a Bern salvage ship at Valor when the seam swallowed it. He's the only survivor, and that's how he ended up in Renais. **DECIDED.** It also answers why Legault was the first to cross, and at what cost: his crew.
- **Kaelen Reed:** a Black Fang splinter leader hunting Nino and Jaffar. [CUT IF SLOW]

## 11. The Ending & the Door

- The heroes repair the seam with a **regulated passage**: a door, not a wall.
- **Keepers (DECIDED):** **Nils** on the far side, which is what he was already doing (see *Nils* below). On the Elibe side, **Arcadia's dragons in turns**, as a community and never one person forever. Myrrh helps attune the door and then goes home to Darkling Woods, free.
- **Cost (DECIDED):**
  1. The door is **narrow and hidden**. It permits deliberate crossings, not a return of dragons (FE6 strict).
  2. **It can't save Ninian.** She could go through and live, but she'd have to stay on the far side. She chooses Eliwood and Elibe again.
  3. Arcadia's secrecy becomes permanent, sworn by everyone who saw it.
- **Nils:** he got home and sealed the Gate as FE7 ends. When the seam began failing, he went in from the far side to hold a rupture shut, and that's where Act III finds him. He goes home at the end.

### The Rausten Stone arc (DECIDED)
- Act I: dreams around it, warmth, hairline cracks. Ch. 6 is the first real crack.
- Act II: Maelis moves on it.
- Act III: its condition shapes the final repair.

On the map, it suppresses seam tiles near it [UNTESTED]. Carrying it is a risk, because the Demon King's soul is still inside.

## 12. Structure

About 30 main chapters, a final, and around 8 side-party chapters, with free-roam interludes [TEST FIRST]. The army-size rule is §8.

### Act I — Two Shores (Prologue–Ch. 10)
| # | Title | Where | Joins | Leaves |
|---|---|---|---|---|
| P | The Year After | Renais (Merrow Point) | Eirika, Seth, Forde, Kyle | |
| 1 | The Marquess's Docks | Ostia | Hector, Oswin, Matthew, Serra, Eliwood (turn 2) | Oswin (regent) |
| 2 | Crown and Border | Renais | Ephraim, Franz, Gilliam, Moulder, Ross, Legault | Gilliam (garrison) |
| 3 | Pherae's Autumn | Pherae | Ninian, Rebecca, Lowen, Merlinus (convoy) | |
| 4 | Frelian Skies | Frelia | Innes, Tana, Vanessa, Neimi, Colm, Syrene (C) | Syrene |
| 5 | Wind over Sacae *(side party)* | Sacae | Lyn, Kent, Sain, Wil, Florina, Rath | |
| 6 | Rausten's Heretic | Rausten | L'Arachel, Natasha (C), Dozla (C), Rennac (C) | Company leaves after |
| 7 | The Old Marches of Caelin | Ostian-held Caelin | Guy, Wallace (C), Dorcas (C), Bartre (C) | Company |
| 8 | Hollow Light | Grado | Duessel, Knoll, Cormag, Amelia (C) | Amelia |
| 9 | The Fang Reforged *(side party)* | Lycia | Nino, Jaffar | |
| 10 | Two Shores | the Gray Sea off Valor | **the casts meet** | |

### Act II — The Crossing (Ch. 11–21)
The allied armies at sea. Arcadia. Maelis moves on the Rausten Stone. Ysolde's midpoint offer.

Joining: Jehanna (Joshua, Marisa, Gerik, Tethys), Caer Pelyn (Saleh, Ewan, Lute, Artur, Garcia), Etruria (Raven, Lucius, Priscilla, Canas, Erk, Pent, Louise), the Western Isles (Dart, Geitz, Renault), Ilia (Fiora, Farina), Bern (Heath, Vaida), Nabata (Karel, Karla, Hawkeye), Darkling Woods (Myrrh), plus Oswin and Gilliam returning.

### Act III — Through the Seam (Ch. 22–30 + Final)
Echo-heavy. Nils. Athos (playable, time-limited). Ysolde's turn. Maelis's end. "The Door." We never enter the dragons' world.

## 13. Systems (DECIDED unless tagged)

- **Engine:** FE8U C-SkillSys LTS. STR/MAG split **on**.
- **Stat scale:** **veterans' numbers.** Everyone starts promoted at **promoted level 1–5**, with bases around where a well-used unit ended FE7/FE8. Promoted caps are about **+5 over vanilla**, with per-character max status for signature stats (C-SkillSys "character max status"). HP cap **80**. Enemies scale to match. Level cap 20.
- **Growth:** lower personal growths than vanilla, because veterans don't grow fast. The growing four (Ross, Amelia, Ewan, Nino) get vanilla-like growths. **Guaranteed level-up retry on.**
- **Skills:**
  - 1 personal skill (§8) + 1 class skill (class identity: Canto for mounts, Locktouch/Steal for thieves, and so on).
  - Up to **3 equippable learned skills**, learned at levels 5/10/15/20 from short per-class lists.
  - Skill scrolls are rare: chests and village rewards.
  - Proc skills are almost absent.
- **Combat arts: on**, weapon-based, costing durability. [UNTESTED balance]
- **Off:** combo attacks, surround penalty, ranged hit decay (hidden modifiers).
- **Weapons:**
  - Iron, Steel and Silver as vanilla, plus custom weapons from the story (Durandal is in Pherae and stays there. Armads and Sol Katti are at home. **No legendary weapons in play** except Sieglinde and Siegmund, which exist in FE8's present).
  - Bows get a little stronger. Throwing weapons get weaker (Vision Quest lesson).
- **Supports:** vanilla GBA map supports, with cross-roster pairs as a feature (§14). Base conversations in interludes [TEST FIRST].
- **Difficulty:** Normal, Hard, plus **Casual** at new game. Hard = enemy bonus levels, extra reinforcements through CHECK_HARD, and some tighter objectives.
- **Map principles:** every map starts as a sketch plus an intent sentence (what it tests, where the pressure comes from), then gets a bot playtest and a numbers check before release. Telegraphed reinforcements. Bosses with kits.
- **Seam tiles [UNTESTED]:** dormant / unstable (opens next turn) / open / sealed / corrupted, built on the Dragon Vein framework.

## 14. Cross-Roster Supports

**Rule:** every crossover support needs at least one discovery you couldn't predict from class, archetype or surface personality.

| Pair | Under the surface |
|---|---|
| Hector × Ephraim | two new kings learning that battlefield freedom and ruling differ. The table gag happens **once**. |
| Lyn × Eirika | opposite relationships to their own nobility |
| Eliwood × Knoll | the lord who would have understood Lyon |
| Canas × Knoll | two scholars of dark magic, and what each refused to learn |
| Matthew × Colm; Legault × Rennac | what each would never steal |
| Sain × Forde | **not mirrors.** Sain performs; Forde hides a reflective streak behind the laziness. |
| Kent × Kyle | the support finds the difference |
| Serra × L'Arachel | royal mission vs. vanity built on insecurity |
| Farina × Tana | |
| Renault × Moulder | two priests with very different pasts |
| Raven × Innes | not just "two grumps": two men who resent what they were born into |
| Ninian × Myrrh | different dragon histories |
| Nino × Ewan | the growing four, two of them |
| Oswin × Gilliam | six lines, each one revealing something |
| Seth × Oswin | two men who'd die for their lords, and what each thinks that means |
| Pent × Louise (Company) | preset A-rank, already married, with a scene rather than a support chain |

## 15. Change Log

### v2 → v3 (decisions)
- FE6 strict, with the consequences table (§4).
- The Lyon rule is finalized (§6.5).
- Governance during absences decided (§7). Oswin, Gilliam and the Pherae knights stay home for a while.
- A tiered cast forced by engine limits: 50 Core plus 26 Company, 76 playable veterans in all (§8). Everyone promoted except the growing four. Personal skills assigned from the engine catalog.
- Cosmology open questions resolved: the seam's nature, the Gray Sea, the Stones' side effect, Fomortiis and the seam (§5).
- Ysolde's knowledge of Magvel, and Seren's illness, decided (§10.1).
- Maelis defined: grief for the dead, mirroring Ysolde's grief for dragons (§10.2).
- Legault's crossing and its cost: a Bern salvage crew lost to the seam (§10.3).
- The door's keepers and cost decided. The ending doesn't save Ninian (§11).
- Systems decided: engine, stat scale, skills, arts, difficulty (§13).

### v1 → v2 (canon corrections)
The Rausten Stone survives. Scouring and Fomortiis are separate eras. The Gate leads to a real world, and the seam is between. Ninian's fading has a canon cause. Arcadia's dragons aren't suddenly dying. Fomortiis is an individual. FE8 continuity is composite. Nils got home. Valor is south of Lycia. Caelin is under Ostia. Vigarde's Echo was fixed. Monica is spelled correctly. Desmond's role was narrowed.

### Existing script lines to update in the rewrite
- The world-map intro's "all Stones gone" becomes "four of five".
- Legault's "east of Lycia" becomes "south," and his salvage-crew backstory is set up.
- Ch. 1: the ghost ship's log should hint at the Unwritten (a Rausten prayer scratched in the hold, say).
