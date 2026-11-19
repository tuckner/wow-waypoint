# 1. doctor: parse health check

**Goal:** when wowf.io changes its page layout, find out right away and see where parsing broke, instead of silently getting stale or garbage snapshots.

## Behavior
- `wowchar.py doctor [slug]` (default: first tracked character). It fetches live and prints a step-by-step report:
  1. HTTP status, page size
  2. number of `self.__next_f.push` chunks found
  3. whether the slug anchor was found, and how many candidate objects decoded
  4. **shape check** of the chosen object (below), as pass/fail per key
  5. sample parse: level, class, number of items, first item's parsed stats
  - On failure, it saves the raw HTML to `<workspace>/notes/characters/.debug/<slug>-<timestamp>.html` (personal, never in the repo) and prints the path.
- **During `update`:** run the same shape check on every fetch. If any check fails, still save what was parsed but record the failure (below), and add a warning to the hook output:
  `⚠ wowf.io parsing looks broken since 2026-11-20 (missing: trees, professions). Run: wowchar.py doctor`
- Network errors (timeouts, 5xx) are reported separately from parse errors, so a flaky site isn't mistaken for a layout change.

## Shape check
`check_shape(obj) -> list[str]` returns the problems found:
- required: `slug, name, level:int, className, itemLevel, items:list`
- expected (warn if missing): `trees, professions, reputations, stats.values, lastLogin, questsDone`
- each item: `slotName, name, itemLevel, lines:list`; ≥1 item has a `Requires Level` or stat line (proves `item_info` still parses)
- `level` between 1 and 60 (or the Forever cap), and `len(items) <= 19`

## State
`<workspace>/notes/characters/.health.json`: `{"last_ok": ISO, "failing_since": ISO|null, "problems": [...]}`. The hook warns only while `failing_since` is set, and clears it on the next clean fetch.

## Code changes
- `wowchar.py`: split `fetch()` into `fetch_html()` and `extract(html, slug)` so doctor and tests can run each step. Add `check_shape`, `cmd_doctor`, and health read/write. In `cmd_update`, call `check_shape`, then update health, then add the warning.
- `skills/track/SKILL.md`: add `doctor` to the commands list and a line: "if the hook warns about parsing, run doctor and show the user the failing step".

## Tests
- `tests/fixtures/player_ok.html`: a handcrafted minimal page with 2–3 `__next_f.push` chunks containing a fake character "Testy Mctest". Assert that `extract` returns it and `check_shape == []`.
- `player_renamed_key.html` (`items` renamed to `equipment`): assert the problem list names `items`.
- `player_no_anchor.html`: `extract` raises a clear error.
- Health state transitions: ok → fail → fail (keeps the first date) → ok (clears).

## Done when
`doctor` passes on a real character; breaking a key in the fixture produces a precise message; the hook shows the warning once parsing fails.
