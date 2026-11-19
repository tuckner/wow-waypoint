---
name: wow-dashboard
description: Build and open a local HTML dashboard of the user's WoW characters (and watched friends) — level and item level over time, quests per day, pace and rough time to max level, gear by item level, professions, and recent changes. Use when the user asks to see their progress, a chart, a dashboard, or how fast they're leveling.
argument-hint: "[group name]"
---

# Dashboard

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux.

1. `wowchar update`, then `wowchar dashboard --open [--group <name>]`. It writes `notes/characters/dashboard.html` and opens it in the browser. It's one self-contained file with a tab per character (paper-doll gear around the character's render, stats, talents, professions, reputation), a Friends tab and a Progress tab with charts. Images (renders, item and profession icons) are fetched once into `notes/cache/` and inlined, so the page works offline and as a published artifact. Only image URLs go out, never character data. Card backdrops can include the user's own images: drop them in `notes/backdrops/` (see design/README.md). Open a specific tab with `#<slug>`, `#friends` or `#progress`.
2. Reply with 2–3 headline facts from `wowchar party` (who leveled most this week, rough ETAs, the next milestone). Don't describe the page section by section.
3. With fewer than ~3 days of snapshots the charts show "not enough history yet". Say so, and note that snapshots are taken at most once a day (more often with `update --force`).
4. Offer once, without pushing, to publish it as a private claude.ai page *only if* they want a link to send friends, and remind them it shows everyone's gear and progress. Don't publish unless they say yes.
