# 6. Status line

**Goal:** a short always-visible line in Claude Code while you're in your WoW workspace, e.g.
`Brightmane 28 Druid · iLvl 24 · +2 lvl/7d · next: Travel Form @30 · 3 open ?`

It's a **workspace setting**: `/wow-waypoint:init` (plan 0) installs it into the workspace's project `.claude/settings.json`, so it shows only in the WoW folder and not in your other projects.

## Command: `wowchar.py statusline`
- Reads the status-line JSON from stdin. Use `workspace.project_dir` (fall back to `cwd`) to find the workspace, ignoring env vars, since status-line commands may not get `CLAUDE_PROJECT_DIR`.
- **No network, no writes.** It reads `characters.json`, the last line of each owned character's `history.jsonl`, and `activity.md` for open `?` lines. Target under 50ms. Read from the end of the file rather than loading the whole history.
- Which character: the owned one with the newest `lastLogin`. With `--all`, show compact entries for every owned character: `Brightmane 28 · Ashvale 28`.
- Segments, each dropped when empty: name level class · iLvl · pace · next milestone (plan 2) · open questions · friend news count (plan 3) · `⚠ repair gear` (any slot under 35%) · `⚠ parse` (plan 1 health failing).
- Plain-ASCII fallback with `--ascii`. Keep it under ~80 characters; truncate the milestone text first.
- Any exception prints nothing and exits 0, so a broken tracker never breaks the status line.

## Install: `wowchar.py install-statusline`
- Writes into `<workspace>/.claude/settings.json` (creating it if needed, keeping all other keys):
  ```json
  "statusLine": {"type": "command", "command": "python3 \"<resolved script path>\" statusline"}
  ```
  It uses the script's resolved absolute path, because each friend's plugin install path differs. `/wow-waypoint:init` re-runs this when the path has changed (e.g. after a plugin update), and `doctor` (plan 1) warns when the configured path no longer exists.
- If a `statusLine` already exists and isn't ours, don't overwrite it. Show it and offer to chain: the command runs the existing one and appends our segment.
- First check whether a plugin can provide `statusLine` directly. If it can, use that instead, so nothing has to be written into settings.
- For the original author's workspace: installed into its project `.claude/settings.json`.

## Tests
- Synthetic workspace plus stdin JSON gives the expected string.
- An empty workspace gives empty output, exit 0.
- Corrupt history gives empty output, exit 0.
- `install-statusline` keeps existing hooks and keys and refuses to clobber a foreign `statusLine`.
- Timing: under 100ms on a 1,000-line history.

## Done when
The line shows in this workspace, updates after `update --force`, and doesn't appear in other folders.
