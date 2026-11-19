# 3. Watched friends and party view

**Goal:** add friends' characters as read-only "watch" entries (wowf.io profiles are public) to see the group at a glance and follow their progress over time. Who's ahead, what they've done lately, what level range fits everyone, and who needs what. This is the only sharing between friends: each person keeps their own workspace, and friends' state comes straight from wowf.io. No synced files and no shared notes.

## Config
`characters.json` entries gain optional fields (missing means the old behavior, i.e. an owned character):
```json
{"region": "us", "slug": "thrall-doomhammer", "name": "Thrall Doomhammer", "watch": true, "group": "tuesday crew"}
```
Owned characters can also have `"roles": ["tank","dps"]` (set by plan 0 setup, used by plan 4).

## Commands
- `add "<Name>" --watch [--group NAME]`: same fetch as now, stored the same way.
- `party [--group NAME]`: a table of everyone (own characters marked ★): name, class, level, iLvl, pace (lvl/day), rough ETA to next 5 levels, last login, professions with skill, 3 weakest slots. Then a footer:
  - **Shared level window:** min/max level and dungeons whose Classic range fits everyone (from `data/instances.json`, shared with plan 4)
  - **Lagging / leading:** anyone more than 3 levels from the median
- `party --since YYYY-MM-DD` (default: 7 days): **friend progress**, i.e. the existing `diff` run for each character over the window. Levels gained, new gear (rare or better called out), profession jumps, new mounts and achievements, quests per day.
- `list` shows a `watch` column.
- **Friend news in the hook:** at session start, one line per friend who changed since your last session, e.g. `Friend news: Thrall 27→30 (new: Arugal's robes), Jaina hit Expert tailoring`. Claude mentions it in a short line, without logging it.

## Rules for watched characters
- Snapshots and summary.md as usual (handy for gear questions about friends).
- **No** activity log, no open questions, no recap or plan, no milestones announcements. `log` refuses with "watched character".
- `hook_instructions` names only owned characters for logging; adds "Watched: N friends (party command)".
- Throttle the same as owned characters. Add `--watch-every 48h` if it gets noisy.

## Skill: `skills/party/SKILL.md`
Trigger: "how's the group doing", "what has Thrall been up to", "what dungeon should we run", "who needs X", "level race".
1. `update`, then `party`.
2. To answer "what dungeon": take the shared window, then for each candidate dungeon count how many members have a weak or empty slot that dungeon's notable loot fills for their spec. Use the instance notes loot lines (plan 4) or Classic knowledge. Recommend 1–2 with reasons.
3. Keep it to one screen. Don't log friends' activity.

## Privacy
Friends' snapshots live in your workspace like yours, never in the repo. The README says to ask friends before watching them. That's polite even though the data is public.

## Tests
- `add --watch` is stored with `watch: true`.
- `log` on a watched character exits with an error.
- `party` computes the shared window correctly for levels [22, 25, 28] → dungeons covering 22–28.
- Hook text excludes watched characters from the logging list.

## Done when
Adding one friend shows up in `party`, the hook mentions them correctly, and the party skill recommends a dungeon for a sample group.
