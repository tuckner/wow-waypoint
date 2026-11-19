# 2. Milestones on level-up

**Goal:** when a snapshot shows a character crossed a level that unlocks something, Claude reminds you at session start ("You hit 30: train Travel Form, Felhunter quest is open"). It also lists what's coming in the next ~2 levels.

## Data: `data/milestones.json` (shared, PR-friendly)
```json
{
  "all": [
    {"level": 10, "what": "First talent point; Journeyman professions (150) trainable", "kind": "talent"},
    {"level": 40, "what": "Riding + first mount", "kind": "mount", "verify": true},
    {"level": 60, "what": "Epic mount", "kind": "mount", "verify": true}
  ],
  "Druid": [
    {"level": 10, "what": "Bear Form (class quest)", "kind": "quest"},
    {"level": 16, "what": "Aquatic Form (class quest)", "kind": "quest"},
    {"level": 20, "what": "Cat Form, Rebirth", "kind": "spell"},
    {"level": 30, "what": "Travel Form", "kind": "spell"},
    {"level": 40, "what": "Dire Bear Form", "kind": "spell"}
  ],
  "Warlock": [ {"level": 10, "what": "Voidwalker (class quest)", "kind": "quest"}, "...Succubus 20, Felhunter 30, Felsteed 40, Infernal 50, Dreadsteed 60" ],
  "professions": {"Journeyman": 10, "Expert": 20, "Artisan": 35}
}
```
- Seed it for all 9 classes from Classic knowledge: class-quest forms, pets, totems and stances, key spells (Remove Curse, Abolish Poison, Resurrection), mount quests. Tag anything Forever might change with `verify`.
- Add generic rules, computed rather than listed: "new spell ranks at every even level" and "talent point every level from 10".

## Script
- `milestones(cls, from_lvl, to_lvl)` → entries with `from < level <= to`, plus generated ones.
- **Profession nudges** from the snapshot: when `skill >= max - 5` and the next tier's level requirement is met, return "Leatherworking 148/150: train Expert (needs lvl 20 ✓)". When the level isn't met yet: "...needs lvl 20 (you're 18)".
- In `diff()`: on a level change, add `milestone: ...` lines, which then show up in the change log and the update report.
- In `summary.md`, add an `## Upcoming` section with the next 2 levels' entries and profession nudges.
- Hook output: if a milestone was crossed since the last session, add `Milestones reached: ... (remind the user once, then log it)`. Track which milestones were already announced in `notes/characters/<slug>/.announced.json` so the reminder fires only once.

## Skill changes
- `track`: when the hook lists milestones, open the reply with them (one line each). Once the user confirms training, `log` it ("Trained Travel Form").
- `plan`: read `## Upcoming` and fold it into "Talents & spells" and "Next session".

## Tests
- Druid going 29→31 returns Travel Form plus even-level training at 30.
- Profession at 148/150 at level 19 gives the "needs lvl 20" message.
- The announcement fires once, not twice.
- An unknown class returns only the `all` entries.

## Done when
Forcing a fake history line (level −2) makes the hook print the right reminders once, and summary.md shows Upcoming.
