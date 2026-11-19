---
name: wow-plan
description: Build a next-steps leveling plan for a tracked WoW Forever character — where to quest and which dungeons to run for the next few levels, gear targets per weak slot with sources, profession and training goals, and errands. Use when the user asks what to do next, what to target, a leveling plan, or upgrade goals.
argument-hint: "[character name or slug] [focus: gear|leveling|professions]"
---

# Character plan

1. **Pick the character** from `notes/characters/characters.json` (match `$ARGUMENTS`). Ask if it's ambiguous.
2. **Refresh and read:** `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" update`, then read `notes/characters/<slug>/summary.md` and run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" gear <slug>`; for a character with several roles also run `sets <slug>` (the gear set last worn for each role). Also read `plan.md` and the newest `journal.md` entry if they exist, so goals that are already done get dropped and unfinished ones carry over.
2a. **Read the profile and Upcoming.** Run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" profile`, and read the `## Upcoming` section of summary.md (milestones and profession nudges).
   - *Relaxed*: story quest chains and fewer dungeon spams.
   - *Optimized*: efficient routes, dungeon farming for key gear, professions picked for power or gold.
   - *Lore-driven*: favor the big story chains.
   - *Completionist*: add quest-chain and exploration targets.
   - Size "Next session" to `hoursPerWeek` (under 5h → 2–3 actions).
   - Fold goals (e.g. "epic mount") into errands, with gold-saving reminders.
   - Use the saved `roles` for gear targets.
   - If the version isn't Forever, answer from that version's rules and say when shipped data (milestones, instance notes) doesn't cover it.
3. **Check existing notes** in `notes/` (class file, dungeons, professions) and reuse their answers. Use Classic knowledge for zones, quests, dungeons and items. Search MetaForge or wowhead/forever only for Forever-specific items or systems, or when unsure, and mark anything unverified.
4. **Gear targets.** For each empty slot and the 3–5 weakest slots (lowest iLvl, wrong stats for the spec, or a req level ≥8 below the character's level), give 1–3 targets that are realistic within the next ~5 levels. Use only stats the spec wants; for example, a feral druid wants no Int or spell power. For each target give the source: quest reward, dungeon boss, AH ("of the X" greens), or craftable by the character's own professions. Flag items under 35% durability for repair. With several role sets, judge each set against its own roles (the healer set wants Int/Spi/healing, the tank + DPS set Agi/Str/AP) and follow the profile's priority between them. If a set is old, say upgrades since then may be missing.
5. **Write `notes/characters/<slug>/plan.md`**, overwriting the old one but keeping unfinished goals:

```markdown
_Plan written 2026-11-18 at level 28. Refresh with /wow-plan when most of it is done._

# <Name> — plan (levels 28 → 32)

## Next session
- 3–5 concrete, ordered actions (train at 30, turn in X, run SFK for Y)

## Leveling route
| Levels | Zone / dungeon | Why (key quests or drops) |

## Gear targets
| Slot | Current (iLvl) | Target | Source | Priority |

## Professions
- skill now → next milestone (trainer or recipe needed, mats to farm along the route)

## Talents & spells
- next points to spend; spells or ranks to train at upcoming levels (from summary.md Upcoming / `milestones <slug>`)

## Errands
- repairs, bank or AH, reputation turn-ins, class quests
```

6. **Reply** with the "Next session" list and the top 3 gear targets. Point to plan.md for the rest.

Keep it practical: about one screen, no padding. Before a dungeon on the route, point to `/wow-instance <name>` for the role briefing. Cite links for drop sources and Forever-specific claims.
