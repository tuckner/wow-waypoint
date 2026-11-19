# 4. /instance: role briefings for dungeons and raids

**Goal:** a single command, `/instance SFK`, `/instance MC` or `/instance ruins of lordaeron`, gives a briefing for *your* character's class, spec and role. For each fight: what you dispel and of which type, which casts you interrupt and with which spell, which adds you CC and with what, where to stand, threat, and what to bring. It goes past DBM by naming your buttons ("Arugal: Remove Curse on Arugal's Curse; you're the only curse remover in this group"), not just the boss timers. Raids get extra sections automatically (below).

## How it gets specific: tags × class ability matrix
Boss mechanics are stored once per instance, role-agnostic, with **tags**. A data file maps each class to the tags it can act on. The script joins them, so the output only names things your class can actually do, at your level, with your talents.

### `data/class-abilities.json` (shared, in the repo)
```json
{
  "Druid": {
    "dispel":  {"curse": {"spell": "Remove Curse", "level": 24}, "poison": {"spell": "Cure Poison", "level": 14}},
    "interrupt": {"bear": {"spell": "Bash (stun)", "level": 14}, "feral": {"spell": "Feral Charge", "talent": "feral_charge"}},
    "cc": {"beast": {"spell": "Hibernate", "level": 18}, "dragonkin": {"spell": "Hibernate", "level": 18}, "outdoor": {"spell": "Entangling Roots", "level": 8}},
    "utility": {"battle-res": {"spell": "Rebirth", "level": 20}, "mana": {"spell": "Innervate", "level": 40}}
  },
  "Mage":    {"dispel": {"curse": "Remove Lesser Curse"}, "interrupt": {"any": "Counterspell"}, "cc": {"beast": "Polymorph", "humanoid": "Polymorph"}},
  "Priest":  {"dispel": {"magic": "Dispel Magic", "disease": "Cure/Abolish Disease"}, "cc": {"undead": "Shackle Undead"}, "utility": {"fear": "Fear Ward (Dwarf)"}},
  "Paladin": {"dispel": {"magic": "Cleanse", "poison": "Purify/Cleanse", "disease": "Purify/Cleanse"}, "cc": {"undead": "Turn Undead"}},
  "Shaman":  {"dispel": {"poison": "Cure Poison / Poison Cleansing Totem", "disease": "Cure Disease / Disease Cleansing Totem"}, "interrupt": {"any": "Earth Shock"}, "utility": {"fear": "Tremor Totem", "purge": "Purge"}},
  "Warlock": {"dispel": {"magic": "Felhunter: Devour Magic"}, "interrupt": {"any": "Felhunter: Spell Lock"}, "cc": {"demon": "Banish", "elemental": "Banish", "any": "Fear (careful indoors)"}},
  "Hunter":  {"utility": {"enrage": "Tranquilizing Shot (60, from MC)"}, "cc": {"any": "Freezing Trap"}},
  "Rogue":   {"interrupt": {"any": "Kick"}, "cc": {"humanoid": "Sap (out of combat)", "any": "Blind"}},
  "Warrior": {"interrupt": {"any": "Pummel / Shield Bash"}, "utility": {"fear": "Berserker Rage"}}
}
```
(Shorthand above for the non-druid classes. In the real file every entry uses the `{spell, level, talent?}` form.) Seed it from Classic. An ability with a `level` above the character's is skipped, and one with a `talent` is shown only if `talentRanks` has it.

### Instance notes: where they live
- **`data/instances/<slug>.md` in the repo:** curated notes that ship with the plugin, so friends get them. Seed the common ones (RFC, WC, DM, SFK, BFD, Gnomer, RFK, SM, RFD, Ulda, ZF, Mara, ST, BRD, LBRS/UBRS, Strat, Scholo, DM, MC, Ony, ZG, BWL, AQ20/40, Naxx), plus Forever's Ruins of Lordaeron once researched.
- **`<workspace>/notes/instances/<slug>.md`:** written by the skill when there's no curated note, or as a personal override. Checked first.
- No sync machinery. If a friend writes a good one, they can send it to you to add to `data/instances/`.

### Note format
```markdown
_Last updated: 2026-11-18_ · type: dungeon · levels 22–30 · Classic (Forever changes: none known)

## Before you go
- [quest] Deathstalker Adamant / Vincent (Horde, the Sepulcher) — pick up before entering
- [bring] poison removal for the spiders before Arugal

## Arugal
- [dispel:curse] Arugal's Curse turns a player into a worgen that attacks the group — remove it fast
- [interrupt] Void Bolt (heavy shadow damage) — interrupt or line-of-sight
- [position] he teleports between ledges; ranged spread out, melee follow
- [threat] Thunder Shock knocks everyone back; tank re-picks him up
- [loot:cloth,int] Robes of Arugal
- [loot:cloth,int] Belt of Arugal
```
(Illustrative. Real notes are written and checked during implementation. Tag only real targets: no `cc:` line unless the adds can actually be CC'd.)

Tags: `dispel:<magic|curse|poison|disease>`, `interrupt`, `cc:<creature type>`, `enrage`, `fear`, `position`, `threat`, `tank`, `heal`, `dps`, `quest`, `key`, `bring`, `resist:<school>`, `assign:<class>`, `loot:<armor>,<stats>`. Lines with no tag are context for everyone. The header's `type: dungeon|raid` decides whether the raid sections apply.

## Script: `wowchar.py brief <slug> <instance> [--role tank|heal|dps]`
- Resolves the name through aliases in `data/instances.json` (`sfk`, `shadowfang`, `vc`/`deadmines`, `mc`, `molten core`, …), which also holds type, level range and faction notes. This is the same file the party view uses for its level-window check.
- For every tagged line it keeps the line if (a) it's untagged or a role tag that matches `--role`, or (b) the class has a usable ability for that tag. It then rewrites the line with *your* ability: `[dispel:curse] Arugal's Curse → you: Remove Curse`.
- Mechanics nobody in your kit can handle become a single "watch out" line, not a job.
- Loot is filtered to the spec's stats (`data/spec-stats.json`, e.g. feral = agi/str/stam, no int or spell power).
- **Gear check** from the snapshot: durability under 35%, weak slots this instance's loot can fill, and consumables your own professions can make (`data/consumables.json` by level band).
- **When `type: raid`**, it adds:
  - **Attunement and keys** (MC: Attunement to the Core; Onyxia: Drakefire Amulet; BWL: Blackhand's Command). The snapshot can't show these, so the skill asks once and logs the answer.
  - **Resist gear**: the character's current resist totalled from gear lines, against the school the raid needs (fire for MC/Ony/BWL, nature for AQ40, frost for Naxx).
  - **Class assignments**: `assign:<class>` lines, e.g. "Lucifron: decurse Lucifron's Curse", "Magmadar: hunters Tranq Shot", so it reads like an assignment sheet.
  - **Consumables by role**, marking which ones your professions make.
- Exit code 2 plus the message "no notes yet" when no note exists.

## Skill: `skills/instance/SKILL.md`
Argument: instance name or abbreviation, optionally the character and role.
1. Pick the character (default: the most recently logged-in owned one). Pick the role: `roles` from setup (plan 0), else infer from talents (feral → ask tank or dps once and save it), else ask.
2. If `brief` exits 2: write `notes/instances/<slug>.md` in the tagged format from Classic knowledge. Search the web only for Forever-only or changed instances (Ruins of Lordaeron, Zephras Isle, patch notes for raids). Mark unsure lines `(verify)`, then rerun `brief`.
3. Reply in one screen:
   - **Your job**: 3–6 bullets of what only you or your class covers
   - **Per boss**: 1–3 lines each, with your buttons named
   - **Before you go**: quests to grab, gear check, consumables to craft (plus attunement and resists for raids)
   - **Loot for you**
4. `log` the run plan ("Running SFK as tank") and an open question (`? Did Arugal drop the Robes?`).
5. Use the playstyle from setup (plan 0): *optimized* gets tighter assignments and consumables, *relaxed* gets the essentials only, *lore-driven* or *RP* gets a one-line story hook per boss.
6. With the party view (plan 3), if the user says who's coming, add **group coverage**: who handles curses, poison, disease, magic and interrupts, and the gaps nobody covers.

## Tests
- A level-22 druid in an instance with `[dispel:curse]` gets no curse job (Remove Curse is trained at 24). At level 24 it shows "you: Remove Curse".
- A mage gets the `cc:humanoid` line rewritten as Polymorph; a priest doesn't.
- Talent-gated Feral Charge appears only with the talent.
- Loot filter: feral drops int and spell power items.
- A note with `type: raid` produces the resist and attunement sections; a dungeon note doesn't.
- The workspace note overrides the repo note; a missing note gives exit code 2.

## Done when
`/instance sfk` on your druid gives a tank briefing naming Bash (and Remove Curse once trained), and `/instance mc` on the warlock lists Banish and Spell Lock jobs, fire resist and the attunement question.
