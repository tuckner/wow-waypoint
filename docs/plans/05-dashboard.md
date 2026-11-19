# 6. Dashboard

**Goal:** `/dashboard` builds one self-contained HTML page from `history.jsonl` for your characters (and watched friends). It shows level and item level over time, pace, ETA, gear quality and professions. You open it locally; nothing gets uploaded unless you choose to.

## Output
`wowchar.py dashboard [--out PATH] [--group NAME]` writes `<workspace>/notes/characters/dashboard.html`. Everything is inline (CSS, JS, SVG, data as a JSON `<script>` block): no CDN, works offline, and stays private. It's personal data, so it's written under `notes/` and `guard()` applies.

## Sections (top to bottom)
1. **Hero tiles**, one per owned character: level, iLvl, levels in the last 7d, rough "60 in ~N days" (pace-based, labeled rough), next milestone (plan 2).
2. **Level over time**: a line chart, one series per character (owned plus watched), step-after interpolation (levels are integers), x = date.
3. **Item level over time**: a separate chart (never a dual axis with level).
4. **Quests per day**: bars per character per day, from the `quests` deltas.
5. **Gear table**: rows = slots, columns = owned characters, cells = item name + iLvl, shaded by item level (sequential, one hue), with empty slots marked.
6. **Professions**: horizontal bars, skill out of cap, per character.
7. **Milestone timeline**: change-log events (level-ups, new gear, mounts) as a list.

## Chart rules (from the dataviz skill; follow them while building)
- **Colors:** use the validated default palette (dataviz `references/palette.md`), copied as constants into the script. Characters take hues in `characters.json` order, fixed per character. Never re-color when one is filtered out. Run `validate_palette.js` for light and dark. Dark mode uses its own validated steps via `prefers-color-scheme`.
- 2px lines, markers ≥8px, recessive grid, one y-axis per chart.
- Legend whenever there are ≥2 series, plus direct end-labels when there are ≤4. With more than 8 characters, fold the extras into small multiples rather than generating new hues.
- Hover: a crosshair and tooltip on line charts, a per-bar tooltip on bars, with hit targets bigger than the marks.
- A "Show table" toggle under each chart, for accessibility.
- Text uses ink tokens, not series colors.
- Works at phone width (16px gutter, no horizontal scroll).
- Before calling it done, render it and look at it (headless screenshot or open it in the browser): label collisions, sparse data.

## Data handling
- Snapshots are throttled to about one a day, so the chart resolution is daily. Collapse identical consecutive snapshots.
- Few points (under 3): show tiles and tables, and replace the charts with "Not enough history yet, check back after a few sessions."
- ETA: average levels/day over the last 7–14 days, times levels remaining. Clamp it, and hide it under 3 days of data. XP per level grows, so call it rough.

## Skill: `skills/dashboard/SKILL.md`
1. `update`, then `dashboard`.
2. Open it: `open` on macOS, `xdg-open` on Linux, `start` on Windows.
3. Reply with 2–3 headline facts (who leveled most this week, ETAs).
4. Offer, once and don't push, to publish it as a private claude.ai artifact *only if* the user wants a link to share with friends. Remind them it contains the gear and progress of everyone shown.

## Tests
- Generating from synthetic history (2 characters, 5 snapshots) produces valid HTML containing the JSON data block and both series.
- With fewer than 3 points, no `<svg class="chart">` is emitted.
- Writing into the repo path is refused (`guard`).

## Done when
The page renders cleanly in light and dark mode, at desktop and phone width, with your two characters plus one watched friend, and the palette validator passes.
