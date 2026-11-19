# Researching an instance

How `/instance` builds or refreshes a note when none exists, or the one it has is stale. The goal isn't a full guide. It's the facts a role briefing needs, each tagged so the script can match it against a character's abilities, and each traceable to a source. Character fit (level, gear, abilities, group) comes from the snapshot at briefing time, so never write it into the note.

Output: `<workspace>/notes/instances/<slug>.md` in the format from `FORMAT.md`, with a `## Sources` section at the end.

## 1. Scope it (no searching yet)
- Resolve the name in `data/instances.json`: slug, type, level range, faction. Not listed? Use the name the user gave, and treat it as version-specific.
- Read the existing note if there is one (workspace first, then shipped). Refresh only the parts that are stale or marked `(verify)`; don't redo good work.
- Decide what the version changed. For a Classic-based version (Forever, Era, SoD), Classic mechanics are the baseline. For Retail, never reuse Classic facts.

## 2. When to look things up
| Fact | Classic-based baseline instance | Version-new instance (e.g. Forever's Ruins of Lordaeron) |
|---|---|---|
| Boss list and order | from knowledge | search |
| Ability names, dispel type, interruptible | from knowledge; look up if unsure | search |
| Add creature types (for CC) | from knowledge; look up if unsure | search |
| Loot and stats | **always look up on Forever** (items and stats change between patches) | search |
| Quests (giver, faction, rewards) | from knowledge; look up rewards on Forever | search |
| Version changes / hotfixes to this instance | **one search, always** | search |

## 3. Where to look (one source per fact type, then a cross-check)
- **Version changes:** search `"<instance> <version> changes"` or the patch notes and hotfix news (icy-veins, wowhead news, official blue posts). One search.
- **Mechanics:** the database boss page and its spell tooltips (wowhead classic/forever). The tooltip gives facts guides often skip:
  - **Dispel type** (`Dispel Type: Curse / Magic / Poison / Disease`) → `dispel:<type>`. No dispel type means it can't be dispelled, so don't tag it.
  - **Cast time** plus whether it's interruptible → `interrupt`. Instant casts can't be interrupted.
  - **NPC type** on the add's page (`Type: Beast / Humanoid / Undead / Demon / Elemental / Dragonkin`) → `cc:<type>`. Check that the add isn't CC-immune (most bosses and many elites are).
- **Strategy and positioning:** one version-specific guide (icy-veins, method.gg, warcrafttavern, mobalytics for Forever). Use it for `position`, `move`, `threat`, role lines and raid `assign:` lines.
- **Loot:** a version loot database (Forever: timesaver.gg dungeon-loot, metaforge). Record armor or weapon type and main stats as the `loot:` tag. Skip item text.
- **Quests:** the database quest page: giver, faction, prerequisite. One line each, under "Before you go".
- **Raids also:** attunement and key quests, the resist school needed (`resist:<school>`), and the standard class assignments per boss.

Budget: about 5 searches or fetches for a dungeon and 8 for a raid. Stop once every boss has its tags. If a site blocks fetching, use the browser fallback the workspace allows. Otherwise use a different site.

## 4. Turn findings into tags (per boss)
Work through this checklist for every ability and add:
1. Debuff on players? → `dispel:<type>` from the tooltip, or untagged context if undispellable.
2. Cast the group should stop? → `interrupt` (or untagged "line-of-sight it" if it can't be interrupted).
3. Adds? → `cc:<type>` only if CC-able; otherwise `position` / role lines.
4. Enrage or frenzy → `enrage`; fear → `fear`; a buff on the boss you can remove → `purge`.
5. Ground effects, frontal cones, knockbacks, run-outs → `position` / `move`.
6. Tank swaps, threat wipes, knockbacks off the tank → `threat`.
7. Role-only jobs → `tank` / `heal` / `dps`; raid jobs → `assign:<Class>`.
8. Notable loot → `loot:<armor or weapon>,<stats>` (spec filtering depends on the stats).

Keep one fact per bullet with one tag. Write the mechanic, not advice for a specific class: the script adds the "→ you: Remove Curse" part itself.

## 5. Cross-check and mark confidence
- Every `dispel:`, `interrupt` and `cc:` tag should match a tooltip, or two sources that agree.
- If sources disagree, keep the more recent one, add `(verify)`, and name both in Sources.
- Mark beta-era or pre-patch info `(verify)`. If you couldn't find a boss's mechanics, write "(mechanics not recorded yet)" under it rather than guessing.

## 6. Record it
- Header: `_Last updated: <today>_ · type: … · levels: … · version: <version> · source: <short list>`.
- End with `## Sources`: one URL per line, with what each was used for (mechanics, loot, quests, changes).
- Then rerun `wowchar brief <instance>` to check the tags produce sensible jobs for the character. Fix tags that land on the wrong class.

## 7. Freshness
`brief` warns when a note is older than 30 days, or 14 for an instance new to its version (`verify: true` in instances.json). On a warning, redo step 1's version-changes search and the loot lookup, update `Last updated`, and keep everything else unless a source contradicts it. Also refresh when the user mentions a patch, or when what they saw contradicts the note ("he didn't do that").

## 8. Character fit (at briefing time, never stored)
The briefing combines the note with the character's snapshot. On top of it, Claude adds:
- **Level vs range:** below the minimum, warn that it's hard. Near the top, say XP is fading. Hardcore realm: be conservative.
- **Kit gaps:** the "watch out" lines, and when the character gains the answer ("Remove Curse at 24").
- **Gear:** repairs, empty slots, and whether the loot list covers their weakest slots.
- **Group:** with watched friends, who covers curse, poison, disease and magic removal and interrupts, and which gaps nobody covers.
