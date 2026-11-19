# wow-waypoint

A Claude Code plugin that keeps track of your WoW characters and helps you play them.

| Skill | What it does |
|---|---|
| `/wow-help [topic]` | What the plugin can do, tailored to what you've set up; a topic (e.g. `instance`, `statusline`) goes deeper. |
| `/wow-init` | First-run setup: game version, characters, region, roles, playstyle, goals, friends, status line. Re-run it to change answers. |
| `/instance <name>` | Role briefing for a dungeon or raid, written for *your* class, level and talents: what you dispel and of which type, what you interrupt and with which spell, what you CC, positioning, raid assignments, attunements, resist gear, consumables your professions make, and loot for your spec. |
| `/plan` | Next session, leveling route, gear targets per weak slot, profession and training goals. Shaped by your playstyle and time budget. |
| `/recap` | A light, titled journey-log entry for what changed since the last recap, in your chosen voice. |
| `/party` | You plus watched friends: level race, what friends did this week, which dungeons fit everyone, who needs what. |
| `/dashboard` | Local HTML page: level and item level over time, quests per day, rough time to 60, gear and professions. |
| `track` | The day-to-day rules: snapshots, the live activity log Claude keeps from your questions, milestones, parse health. |

Also:
- **Session start:** refreshes snapshots (at most once per 20h), announces milestones once ("you hit 30: Travel Form"), shows friend news, and warns if the armory site stopped parsing.
- **Status line** (per workspace): `Brightmane 28 Druid · iLvl 24 · next: Travel Form @30 · 3 open ?`

Python 3 standard library only. Nothing to install beyond Claude Code.

## Game versions

| Version | Armory site | Status |
|---|---|---|
| WoW Forever | wowf.io | supported |
| Classic Era / Hardcore / SoD / Cata-MoP Classic / Retail | not chosen yet | setup, Q&A, plans and recaps work; snapshots don't yet |

Each version maps to its own site in `data/sources.json`, and each site has an adapter in `scripts/sources/`. A character can override its site with `"source"` in `characters.json`. Adding a site means writing one adapter that returns the normalized snapshot shape (see `sources/wowfio.py`).

## Install

```sh
git clone <this repo> ~/src/wow-waypoint
```

In Claude Code, from the folder you want for WoW notes:

```
/plugin marketplace add ~/src/wow-waypoint
/plugin install wow-waypoint@wow-waypoint
```

Pick **project scope** so the hook only runs in your WoW folder. Restart Claude Code, then run `/wow-init`. After pulling updates, run `/plugin marketplace update wow-waypoint`.

## Your data stays yours

Everything personal (characters, friends you watch, your profile, the dashboard, your own instance notes) is written to `<your workspace>/notes/`. The workspace is `$WOWCHAR_HOME` if set, else the Claude Code project folder, else the nearest folder above the current one that has `notes/characters/`.

Friends' characters come from their public wowf.io pages. Ask before watching someone.

## Layout

```
.claude-plugin/        plugin.json, marketplace.json
hooks/hooks.json       SessionStart: snapshots, milestones, friend news, parse health, logging rules
scripts/wowchar.py     CLI (python3 scripts/wowchar.py prints help)
scripts/core.py        paths, config, profile, snapshots, diffs
scripts/sources/       one adapter per armory site (wowfio.py)
scripts/milestones.py  level unlocks + profession tier nudges
scripts/brief.py       /instance engine: tagged notes × class abilities
scripts/dashboard.py   self-contained HTML dashboard
scripts/statusline.py  status line (no network, no writes, never errors)
data/                  shared facts by ruleset: sources, milestones, class abilities, spec stats, consumables, instances
data/instances/        RESEARCH.md (how to look up an instance), FORMAT.md, two worked examples
skills/                wow-help, wow-init, track, plan, recap, instance, party, dashboard
templates/CLAUDE.md    starter Q&A rules for a WoW workspace
tests/                 python3 -m unittest discover -s tests (synthetic fixtures only)
docs/plans/            the design plans these features were built from
```

## Fixing facts

Game data lives in plain JSON and Markdown under `data/`, grouped by ruleset (`classic` today). If a spell level or milestone is wrong, or Forever changed it, edit the line and mark it `"verify": true` if you're not sure. Instance notes aren't shipped in bulk: `/instance` researches each one on demand using `data/instances/RESEARCH.md` and saves it to your workspace (`notes/instances/`), with sources and a date so it can tell when a note is stale. Instance notes use bracket tags (`[dispel:curse]`, `[interrupt]`, `[cc:beast]`, `[loot:leather,agi]`…) that `/instance` matches against each class's abilities. See `data/instances/FORMAT.md`.

## Developing without installing

Symlink the skills into a workspace's `.claude/skills/` and point a SessionStart hook in `.claude/settings.json` at `scripts/wowchar.py update --quiet --hook`. The skills locate the script relative to their own folder, so symlinks work.

## Releases

Versions follow [Semantic Versioning](https://semver.org) and are cut by [Release Please](https://github.com/googleapis/release-please). Title pull requests with [Conventional Commits](https://www.conventionalcommits.org):

- `fix: …` makes a patch release (0.0.1 → 0.0.2)
- `feat: …` makes a minor release (0.0.1 → 0.1.0)
- `feat!: …` or a `BREAKING CHANGE:` footer is a breaking change; before 1.0 it also bumps the minor version

Release Please keeps an open release PR that collects these into `CHANGELOG.md` and bumps `.claude-plugin/plugin.json`. Merging it tags the release and publishes it on GitHub; plugin users get it on their next plugin update. Tests run on every pull request.

