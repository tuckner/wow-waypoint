# 🧭 wow-waypoint

**Your WoW characters, tracked and coached, right inside Claude Code.**

wow-waypoint follows your characters' armory pages, keeps a journal of your adventure, and gives you advice that fits *your* class, level, gear and playstyle. Ask questions like you'd ask a guildmate. Claude answers and quietly keeps your log up to date.

> 🎮 Built for **WoW Forever** today. Other versions get setup, Q&A, plans and recaps, but no armory snapshots yet ([details](#-game-versions)).

---

## 🚀 Quick start

You need [Claude Code](https://claude.com/claude-code) and Python 3. Python is already on macOS and most Linux; on Windows, get it from [python.org](https://www.python.org/downloads/).

**1. Make a folder for your WoW notes** and start Claude Code in it:

```sh
mkdir -p ~/wow && cd ~/wow && claude
```

**2. Add the plugin straight from GitHub** (no clone needed):

```
/plugin marketplace add tuckner/wow-waypoint
/plugin install wow-waypoint@wow-waypoint
```

When it asks for a scope, pick **project**, so it only runs in this folder.

**3. Restart Claude Code** in the same folder, then run:

```
/wow-init
```

It asks a few questions (game version, characters, region, roles, playstyle, friends) and sets everything up. That's it. Try `/plan` next. 🎉

---

## ✨ What you get

| | Command | What it does |
|---|---|---|
| 🧭 | `/dashboard` | The **Waypoint dashboard**: a trading card for each character, a Hero panel with *Up next* suggestions, a route-to-60 map, your gear, friend pages, and Progress pages (standings, leveling, gear, activity, journal). |
| 🗺️ | `/plan` | What to do next session, where to level, gear targets for your weakest slots, and profession goals. |
| 📖 | `/recap` | Turns what you've done into a short, titled chapter in your character's journal. |
| ⚔️ | `/instance <name>` | A briefing before a dungeon or raid, for *your* class and talents: what to dispel, interrupt and CC, positioning, and loot for your spec. |
| 👥 | `/party` | You and your friends: the level race, what they've been up to, and which dungeons fit everyone. |
| 🛠️ | `/wow-init` | First-time setup. Run it again any time to change your answers. |
| ❓ | `/wow-help` | Everything the plugin can do, tailored to what you've set up. |

**Running in the background:**
- 🔄 **Session start:** refreshes your characters (at most once every 20 hours), announces milestones once ("you hit 30: Travel Form!"), and shares friend news.
- 📝 **Live activity log:** when you mention a dungeon, a drop or a quest, Claude notes it for your next recap.
- 📟 **Status line:** `Brightmane 28 Druid · iLvl 24 · next: Travel Form @30 · 3 open ?`

---

## 🔄 Updating

```
/plugin marketplace update wow-waypoint
```

Then restart Claude Code. To update automatically, turn on auto-update under `/plugin` → **Marketplaces**. See what changed on the [Releases page](https://github.com/tuckner/wow-waypoint/releases).

> 📟 **Status line users:** each update installs to a new folder. After updating, run `/wow-init` again (or ask Claude to "reinstall the status line") so it points at the new copy.

## 🤝 Sharing with friends

Friends install it the same way. To have Claude Code offer it automatically in a shared folder, add this to that folder's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "wow-waypoint": { "source": { "source": "github", "repo": "tuckner/wow-waypoint" } }
  },
  "enabledPlugins": { "wow-waypoint@wow-waypoint": true }
}
```

## 🗑️ Uninstalling

```
/plugin uninstall wow-waypoint@wow-waypoint
```

Your `notes/` folder stays where it is.

---

## 🔒 Your data stays yours

Everything personal (characters, watched friends, your profile, journal, plans and dashboard) lives in **your** folder under `notes/`, never inside the plugin. The folder is `$WOWCHAR_HOME` if set, otherwise your Claude Code project folder.

**What goes over the network:**
- 🌐 **wowf.io**: your characters' public armory pages, at most once every 20 hours unless you ask for a refresh.
- 🖼️ **Images**: character renders (render.worldofwarcraft.com), item icons (wow.zamimg.com) and profession icons (assets.wowf.io). Only image addresses are requested.
- 🔎 **Wowhead tooltips**: looked up by item ID only.

Images and tooltips are cached in `notes/cache/` and built into the dashboard, so it works offline. No character data is sent anywhere.

👋 Friends' characters come from their public wowf.io pages. Ask before you watch someone.

---

## 🎮 Game versions

| Version | Armory site | Status |
|---|---|---|
| WoW Forever | wowf.io | ✅ Supported |
| Classic Era / Hardcore / SoD / Cata-MoP Classic / Retail | not chosen yet | 🟡 Setup, Q&A, plans and recaps work; snapshots don't yet |

Want to add a site? Each version maps to one in `data/sources.json`, and each site gets an adapter in `scripts/sources/` that returns the normalized snapshot shape (see `sources/wowfio.py`). A single character can use a different site with `"source"` in `characters.json`.

## 🩹 Fixing facts

Game data is plain JSON and Markdown under `data/`, grouped by ruleset (`classic` today). If a spell level or milestone is wrong, or Forever changed it, edit the line, and mark it `"verify": true` if you're not sure.

Instance notes aren't shipped in bulk. `/instance` researches each one when you need it (see `data/instances/RESEARCH.md`) and saves it to `notes/instances/`, with sources and a date so it knows when a note is stale. Notes use bracket tags like `[dispel:curse]`, `[interrupt]`, `[cc:beast]` and `[loot:leather,agi]` that `/instance` matches to your class's abilities. See `data/instances/FORMAT.md`.

---

## 🧑‍💻 For developers

### Project layout

```
.claude-plugin/        plugin.json, marketplace.json
.github/workflows/     tests on every PR; Release Please
hooks/hooks.json       SessionStart: snapshots, milestones, friend news, parse health, logging rules
scripts/wowchar.py     CLI (python3 scripts/wowchar.py prints help)
scripts/core.py        paths, config, profile, snapshots, diffs
scripts/sources/       one adapter per armory site (wowfio.py)
scripts/milestones.py  level unlocks + profession tier nudges
scripts/brief.py       /instance engine: tagged notes × class abilities
scripts/dashboard.py   the Waypoint dashboard (one self-contained HTML file)
scripts/progress.py    the dashboard's Progress pages (journal, leveling, activity...)
scripts/wowhead.py     cached Wowhead tooltips, item icons and images
scripts/statusline.py  status line (no network, no writes, never errors)
design/                the Waypoint design system: tokens.css and its rules (README.md)
data/                  shared facts by ruleset: sources, milestones, class abilities, spec stats, consumables, instances
data/instances/        RESEARCH.md (how to look up an instance), FORMAT.md, two worked examples
skills/                wow-help, wow-init, track, plan, recap, instance, party, dashboard
templates/CLAUDE.md    starter Q&A rules for a WoW workspace
tests/                 python3 -m unittest discover -s tests (synthetic fixtures only)
docs/plans/            the design plans these features were built from
```

Python 3 standard library only.

### Working from a clone

```sh
git clone https://github.com/tuckner/wow-waypoint.git ~/src/wow-waypoint
```

Then either add the clone as a local marketplace (`/plugin marketplace add ~/src/wow-waypoint`), or symlink its `skills/*` into a workspace's `.claude/skills/` and point a SessionStart hook in that workspace's `.claude/settings.json` at `python3 ~/src/wow-waypoint/scripts/wowchar.py update --quiet --hook`. The skills find the script relative to their own folder, so symlinks work.

🧪 Run the tests with `python3 -m unittest discover -s tests`.

### 🏷️ Releases

Versions follow [Semantic Versioning](https://semver.org) and are cut by [Release Please](https://github.com/googleapis/release-please). Title pull requests with [Conventional Commits](https://www.conventionalcommits.org):

- `fix: …` → patch release (0.0.1 → 0.0.2)
- `feat: …` → minor release (0.0.1 → 0.1.0)
- `feat!: …` or a `BREAKING CHANGE:` footer → breaking change (before 1.0 this also bumps the minor version)

Release Please keeps an open release PR that collects these into `CHANGELOG.md` and bumps `.claude-plugin/plugin.json`. Merging it tags the release and publishes it on GitHub, and plugin users get it on their next update. Tests run on every pull request.
