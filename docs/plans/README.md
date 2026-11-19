# Implementation plans

_Written 2026-11-18. **Status: all built in 0.2.0** (see CHANGELOG.md). Kept as design notes._

| # | Plan | Size | Depends on |
|---|---|---|---|
| 0 | [/wow-waypoint:init: first-run setup](00-init.md) | M | none (friends and status line steps light up after 3 and 6) |
| 1 | [doctor: parse health check](01-doctor.md) | S | none |
| 2 | [Milestones on level-up](02-milestones.md) | M | none |
| 3 | [Watched friends, party view and friend progress](03-party.md) | M | 0 |
| 4 | [/instance: role briefings for dungeons and raids](04-instance.md) | L | 0 (roles), 3 for group coverage |
| 5 | [Dashboard](05-dashboard.md) | L | 2, 3 |
| 6 | [Status line (workspace setting)](06-statusline.md) | S | 0, 2 |

Dropped: shared guides synced between friends. Friends share progress only through wowf.io (plan 3). General Q&A notes stay in each person's own `notes/`.

## Cross-cutting rules (apply to every plan)
- **Stdlib Python only.** No pip installs; friends just need python3.
- **Personal data never in the repo.** Anything per-person (characters, friends, profile, dashboard, instance overrides) goes under `<workspace>/notes/`. `guard()` already enforces this; new write paths must call it. Test fixtures are synthetic, never a real character's wowf.io page.
- **Shared reference data goes in `data/`** (milestones, class abilities, instances, spec stats, consumables, curated instance notes), so fixing a fact is a one-line edit rather than a Python change.
- **Forever vs Classic:** data entries default to Classic. Anything that might differ on Forever gets `"verify": true` and the skills mention it in one line.
- **Config schema changes** to `characters.json` must stay backward compatible: missing keys mean the old behavior.
- **Each feature ends with:** README section, `track` skill update if it adds commands, `setup-status` update if init should know about it, version bump in `plugin.json`, and a line in `CHANGELOG.md` (created with the first feature built).
- **Tests:** `tests/` with `python3 -m unittest`, using synthetic fixtures in `tests/fixtures/`. Each plan lists its own tests.

- **Game version aware:** shared data is keyed by ruleset (`classic` now; `retail` and others later), and snapshots come through a source interface chosen by each character's version (plan 0). Only wowf.io (Forever) is supported at first.

## Open questions to settle during implementation
- Which data sources cover Classic Era, Hardcore, SoD and Retail (the Blizzard profile API needs a key; raider.io is keyless for Retail), and how much gear and talent detail each one exposes. Each one becomes its own plan once chosen.
- Does wowf.io tell apart same-named characters on different realms? If so, the realm joins the fetch key (plan 0).
- Can a plugin provide `statusLine` directly? If not, `install-statusline` writes it to workspace settings (plan 6).
