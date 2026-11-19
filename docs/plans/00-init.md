# 0. /wow-init: first-run setup

**Goal:** one guided conversation the first time someone uses the plugin. It seeds everything the other features need: characters, region and realm, roles, friends, playstyle, and the workspace files and settings. Running it again edits answers instead of starting over.

Named `/wow-init` because Claude Code already has a built-in `/init`. The setup section of the `track` skill moves here; `track` just points to it.

## What it collects

| Topic | How it's asked | Required? | Used by |
|---|---|---|---|
| **Game version**: WoW Forever, Classic Era / Hardcore, Season of Discovery, Classic progression (Cata/MoP Classic), or Retail. Can differ per character | choice, asked **first** | **yes**: it decides the data source and which game rules apply (see "Game versions" below) | fetch, every skill and data file |
| Character names (main + alts) | free text | **yes** | everything |
| Region (US / EU / …) | choice | **yes**: wowf.io URLs are `/players/<region>/<first-last>` | fetch |
| Realm name and realm type (PvE / PvP / RP / Hardcore, whatever Forever offers) | choice + free text | recommended. Verify whether wowf.io needs the realm to tell same-named characters apart; if so, it becomes required and goes into the fetch URL | advice, safety, recap voice |
| Role(s) per character (options depend on class: druid → tank/heal/dps, mage → dps) | choice, multi-select | recommended | `/instance`, `/plan` |
| Main vs alt | choice | optional | status line, default character |
| Playstyle: relaxed, optimized/speed, lore-driven, role-play, completionist, gold-making, PvP | choice, multi-select | recommended | `/plan`, `/recap`, `/instance` tone and depth |
| Time per week (<5h / 5–15h / 15h+) and typical session length | choice | optional | `/plan` sizing (how much "next session" holds) |
| Goals: hit 60 by a date, raid-ready, a profession or gold target, a specific mount, PvP rank | choice + free text | optional | `/plan`, milestones |
| Answer style (brief / detailed) | choice | optional | all answers |
| Spoilers for new Forever content (avoid / fine) | choice | optional | searches, instance notes, recaps |
| Recap voice: light summary (default), in-character diary, lore chronicle | choice | optional | `/recap` |
| Group play: solo / duo-trio / guild, plus guild name and usual play night | choice + free text | optional | party view |
| Friends' characters (name, region, which group) | free text | optional, encouraged ("makes recaps and party view more fun") | party view, friend news, group coverage in `/instance` |
| Addons in use (Questie, DBM, Details, …) | free text | optional | answers can refer to what they already see |

## Flow (`skills/wow-init/SKILL.md`)
1. **Check state:** `wowchar.py setup-status` prints what exists: workspace CLAUDE.md, characters, profile, friends, status line. If everything exists, say so and ask what to change (re-run mode). If setup was partial, resume at the first missing step.
2. **Folder:** confirm this is the folder to use for WoW notes. It must not be the plugin repo (`guard()` enforces this).
3. **Workspace rules:** copy `templates/CLAUDE.md` in. If a CLAUDE.md already exists, offer to merge instead of overwriting.
4. **Game version (first question, on its own):** WoW Forever / Classic Era or Hardcore / Season of Discovery / Classic progression / Retail, plus "a mix" (then ask per character in step 6). If the version has no data source yet, say so plainly: setup continues with the profile and Q&A rules, and character tracking stays off for those characters until a source exists.
4b. **Characters (free text):** "What are your characters' names, starting with your main?"
5. **Round 1 (one `AskUserQuestion` call, at most 4 questions):** region, realm type (options depend on the version: Forever's realm types, Era/Hardcore/SoD, Retail's Normal/RP), playstyle (multi-select), time per week.
6. **Add and confirm** each character: `add "<Name>" --region <r>`, then show what came back ("Brightmane Hoof: level 28 Tauren Druid, Leatherworking 109. That's you?"). On a 404, try the other region and remind them that wowf.io only knows a character after its first logout.
7. **Round 2:** roles per character (one question per character, options by class) and main vs alt.
8. **Round 3:** goals (multi-select), answer style, spoilers, recap voice.
9. **Friends (free text):** "Want to add friends' characters? The party view, friend news and group coverage in `/instance` use them. Names, region, and a group name if you like." Then `add --watch --group`, confirming each like step 6. Mention asking friends first is polite.
10. **Status line:** offer it (show an example line). On yes, run `install-statusline` (plan 6).
11. **Finish:** run `update`, write `notes/profile.md`, and reply with a 5-line summary of what's set up, plus suggestions: `/plan` for what to do next, `/instance <name>` before a run, the dashboard. Log `"Started tracking (wow-init)"` for each owned character.

Keep it quick: about 4 question rounds and under 3 minutes. Every optional question can be skipped ("Skip" is always an option, or they can pick Other and type).

## Storage
- `<workspace>/notes/profile.json` (personal, never in the repo):
  ```json
  {"version": "forever", "region": "us", "realm": "…", "realmType": "pve",
   "playstyle": ["relaxed", "lore"], "hoursPerWeek": "5-15", "goals": ["60 by Jan", "Epic mount"],
   "answerStyle": "brief", "spoilers": "avoid", "recapVoice": "light", "group": {"type": "duo-trio", "guild": null, "night": "Tue"},
   "addons": ["Questie", "DBM"], "updated": "2026-11-18"}
  ```
- Per-character `roles`, `main` and `version` go in `characters.json` (the fields from plan 3). A missing `version` means `forever`, so existing entries keep working.

## Game versions
The version picks two things: the **data source** (where snapshots come from) and the **ruleset** (which game facts apply).

| Version | Ruleset | Data source | Status |
|---|---|---|---|
| WoW Forever | `classic` + Forever overrides | wowf.io (today's scraper) | supported |
| Classic Era / Hardcore / SoD | `classic` (SoD adds runes, so treat SoD-specific facts as `verify`) | Blizzard Classic profile API (needs a free API client id and secret) or a public armory site | **research**: pick the source and check what gear and talent data it exposes |
| Classic progression (Cata/MoP Classic) | its own expansion's rules | Blizzard Classic profile API | research; low priority |
| Retail | `retail` | raider.io public API (no key: gear, item level, M+ score) or the Blizzard profile API | research; most `data/` files don't apply |

- **One armory site per version, swappable.** `data/sources.json` maps each version to its source: `{"forever": {"source": "wowfio", "url": "https://wowf.io/en/players/{region}/{slug}"}, "era": {"source": "…"}, …}`. A character entry can override it with `"source": "<id>"` (e.g. when a version has two armory sites and one is down or better). Because characters can be on different versions, one workspace can mix sources, and `update` fetches each character from its own.
- **Script:** move today's wowf.io code behind a small source interface: `fetch(char) -> normalized dict` (the same shape `compact()` produces now). One adapter per site (`sources/wowfio.py`, later `sources/raiderio.py`, …), registered by id. `doctor` (plan 1) tests whichever adapter each character uses. New sources are added later as their own plan once researched. Unsupported versions fail with a clear "tracking not available for <version> yet" message, never a crash.
- **Data files are keyed by ruleset:** `milestones.json`, `class-abilities.json`, `instances.json` and the instance notes get a top-level `classic` key now, so `retail` (or `cata`) can be added later without reshaping. Skills whose data has no entry for the ruleset say so and fall back to plain knowledge answers.
- **Workspace rules:** `templates/CLAUDE.md` gets a version line filled in by setup ("This workspace is for <version>: answer from <ruleset> knowledge; search for changes specific to <version>"). The current text becomes the Forever variant.
- **Hook output** includes the version in the profile line, so Claude never answers Retail questions with Classic facts or the other way round.
- The plugin is named `wow-waypoint` (version-neutral).
- `notes/profile.md` is a readable copy that Claude reads; the JSON is what the script reads.
- Script: `wowchar.py profile` (print), `profile set key=value` (edit one answer without re-running setup), `setup-status`.

## How the profile changes behavior
- **Hook output** adds one line: `Player profile: relaxed + lore-driven, ~5–15h/week, brief answers, avoid Forever spoilers. Respect it.`
- **`/plan`:** *relaxed* means story quest chains and fewer dungeon spams, sized to the time budget. *Optimized* means efficient routes, dungeon farming for key gear, and professions picked for gold or power. *Completionist* adds quest-chain and achievement targets.
- **`/recap`:** writes in the chosen voice. An in-character diary uses first person as the character, and *lore-driven* adds a one-line lore aside.
- **`/instance`:** *optimized* gets full assignments and consumables, *relaxed* the essentials. *Lore-driven* or *RP* adds a story hook per boss. On a **hardcore** realm, add death-risk warnings (wipe mechanics, pulls to avoid, escape buttons).
- **Search and answers:** avoid spoilers means no plot details for new Forever content unless asked. Brief vs detailed sets answer length.
- **Milestones (plan 2):** goals such as "Epic mount" add a gold-saving reminder at the right level.

## Build notes
- Build the base version first (steps 1–8 and 11). Steps 9 and 10 light up once plans 3 and 6 land. The skill checks `setup-status`, which reports which features are available.
- First check how `wowf.io` handles realms (same name on two realms). It decides whether the realm is part of the fetch key.

## Tests
- `setup-status` on an empty folder → everything missing; after `add` and `profile set` → only friends and status line missing.
- `profile set playstyle=relaxed,lore` round-trips into the JSON as a list.
- A character with `version: retail` (no source yet) gives the clear "not available yet" message from `update`, while other characters still update. An entry with no version is treated as Forever.
- Re-run mode doesn't duplicate characters.
- Hook output contains the profile line only when a profile exists.

## Done when
A fresh folder plus `/wow-init` ends with a tracked character, a profile, friends watched, the status line showing, and `/plan` visibly reflecting the playstyle (e.g. relaxed vs optimized produce different routes).
