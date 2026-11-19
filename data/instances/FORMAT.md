# Instance note format

One file per instance: `data/instances/<ruleset>/<slug>.md` (shipped with the plugin) or `<workspace>/notes/instances/<slug>.md` (personal, checked first). The slug comes from `data/instances.json`.

```markdown
_Last updated: 2026-11-18_ · type: dungeon · levels: 22–30 · version: forever · source: wowhead tooltips + icy-veins + timesaver loot

# Shadowfang Keep

## Before you go
- [quest] Deathstalkers in Shadowfang (Horde, Undercity) — pick up before entering
- [bring] poison removal for Fenrus

## Arugal
- [dispel:curse] Arugal's Curse turns a player into a worgen — remove it fast
- [interrupt] Void Bolt (heavy shadow damage)
- [position] teleports between ledges; ranged spread out
- [loot:cloth,int,heal] Robes of Arugal

## Sources
- https://… (mechanics: spell tooltips)
- https://… (loot, Forever)
```

How to research a note: **RESEARCH.md**. The repo ships only two worked examples (SFK, Molten Core); everything else is researched on demand into your workspace.

Rules:
- **Header line** (first line, italic, `·`-separated `key: value`): `type: dungeon|raid` turns raid sections on.
- **`## ` sections** are bosses (or "Trash", "Before you go"). Lines under "Before you go" always show. `## Sources` (one URL per line, with what it was used for) goes last and isn't shown in briefings.
- **Freshness:** `brief` flags notes older than 30 days (14 for version-new instances), boss sections marked "(mechanics not recorded yet)", and notes with no Sources.
- **Tags** go in brackets at the start of a bullet. Use one tag per bullet where you can; untagged bullets are context for everyone.

| Tag | Who sees it |
|---|---|
| `dispel:magic` `dispel:curse` `dispel:poison` `dispel:disease` | classes with that dispel, rewritten as "→ you: Remove Curse"; others see it under "watch out" |
| `interrupt` | classes with an interrupt (Kick, Counterspell, Earth Shock, Bash…) |
| `cc:beast` `cc:humanoid` `cc:undead` `cc:demon` `cc:elemental` `cc:dragonkin` | classes that can CC that creature type |
| `enrage` `fear` `purge` `battle-res` | classes with Tranquilizing Shot, Tremor/Fear Ward/Berserker Rage, Purge, Rebirth |
| `assign:<Class>` | that class only (raid assignments, e.g. `assign:Warlock` banish the Firesworn) |
| `tank` `heal` `dps` | that role only |
| `threat` | tanks (dps see it as "watch threat") |
| `position` `move` `resist:<school>` | everyone; `resist:fire` also totals the character's fire resist from gear |
| `quest` `key` `attune` `bring` | everyone, in "Before you go" |
| `loot:<armor or weapon>,<stats>` | only if the character can use it and the stats fit the spec. Armor: cloth leather mail plate. Weapons: staff mace dagger sword axe fist polearm 2h-mace 2h-sword 2h-axe bow gun crossbow wand shield. Generic: cloak ring neck trinket offhand. Stats: str agi sta int spi sp heal mp5 ap crit hit def |

Only tag real targets: no `cc:` line unless those adds can actually be CC'd. Mark anything unsure with `(verify)`.
