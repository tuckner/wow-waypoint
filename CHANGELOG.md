# Changelog

## [0.7.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.6.0...wow-waypoint-v0.7.0) (2026-11-19)


### Features

* **init:** never overwrite an existing CLAUDE.md ([c93ec29](https://github.com/tuckner/wow-waypoint/commit/c93ec29b0bfe793d905500f58719ace2428e490b))

## [0.6.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.5.0...wow-waypoint-v0.6.0) (2026-11-19)


### ⚠ BREAKING CHANGES

* the /wow-* skill names are gone; use /wow-waypoint:<name>. Workspaces that symlinked skills into .claude/skills should load the plugin instead (claude --plugin-dir /path/to/wow-waypoint) and drop any hand-added SessionStart hook.

### Features

* drop the wow- prefix from skill names; plugin skills are /wow-waypoint:init, /wow-waypoint:plan, ... ([4af54bf](https://github.com/tuckner/wow-waypoint/commit/4af54bf8618b084941c18593aa57aae4829c521e))

## [0.5.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.4.0...wow-waypoint-v0.5.0) (2026-11-19)


### Features

* `add` accepts a wowf.io profile link; init asks for the link when a name can't be fetched ([cc5ee0c](https://github.com/tuckner/wow-waypoint/commit/cc5ee0c4288fb01854966a1278668a63903bc4c7))
* **dashboard:** average item level over time atop the Gear page; fix leveling chart starts, overlapping flags and cut-off projection ([f64ef7a](https://github.com/tuckner/wow-waypoint/commit/f64ef7a918ce0832ba13c074f59d87ba617adc38))
* **init:** character names are a required question in the first setup form, never asked in chat ([cc5ee0c](https://github.com/tuckner/wow-waypoint/commit/cc5ee0c4288fb01854966a1278668a63903bc4c7))
* **init:** WoW context only in the notes folder by default; names asked in the setup form ([cc5ee0c](https://github.com/tuckner/wow-waypoint/commit/cc5ee0c4288fb01854966a1278668a63903bc4c7))
* item level tracks your best gear set, not just what you logged out in ([ce25d94](https://github.com/tuckner/wow-waypoint/commit/ce25d9466a3c11a0b8cb8dabef7ae4664a44af61))


### Bug Fixes

* session start no longer injects a 'last time' recap; open questions stay as background ([2e52bf7](https://github.com/tuckner/wow-waypoint/commit/2e52bf7ca1b01f4d363617fec0b43f2da6a12d79))

## [0.4.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.3.0...wow-waypoint-v0.4.0) (2026-11-19)


### ⚠ BREAKING CHANGES

* prefix every skill with wow- (/wow-plan, /wow-recap, /wow-instance, ...)

### Features

* filter friends by realm type (PvP, PvE, RP, RP-PvP) on the dashboard and with `party --realm` ([df0bbc9](https://github.com/tuckner/wow-waypoint/commit/df0bbc999e5c440cf192e207388d57ff99c0cbc4))
* gear sets by role (healer vs tank + DPS) in summary.md, `sets`, and the dashboard gear readout ([df0bbc9](https://github.com/tuckner/wow-waypoint/commit/df0bbc999e5c440cf192e207388d57ff99c0cbc4))
* prefix every skill with wow- (/wow-plan, /wow-recap, /wow-instance, ...) ([df0bbc9](https://github.com/tuckner/wow-waypoint/commit/df0bbc999e5c440cf192e207388d57ff99c0cbc4))
* session hook flags due recaps and plans and runs them (profile autoSkills=auto|offer|off) ([df0bbc9](https://github.com/tuckner/wow-waypoint/commit/df0bbc999e5c440cf192e207388d57ff99c0cbc4))

## [0.3.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.2.0...wow-waypoint-v0.3.0) (2026-11-19)


### Features

* /macro covers all macro types, not just targeting ([3198ac6](https://github.com/tuckner/wow-waypoint/commit/3198ac6b743dc8071b1608e8bd7472176a55c92e))
* /macro skill for quest-mob targeting macros ([a185f3f](https://github.com/tuckner/wow-waypoint/commit/a185f3f1717ffc539e5760f266b40ae692ea5235))


### Bug Fixes

* /macro writes targeting-only macros with no /run lines ([a72a820](https://github.com/tuckner/wow-waypoint/commit/a72a820a87e0ea24b37adeaf2312e7e63049249d))

## [0.2.0](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.1.1...wow-waypoint-v0.2.0) (2026-11-19)


### Features

* drop the drawn card scenes; class glow plus photo backdrops ([331744e](https://github.com/tuckner/wow-waypoint/commit/331744e3304732033bc8c5cacd86f2f117773c00))
* photo backdrops for trading cards and a download icon on the card ([a5a45da](https://github.com/tuckner/wow-waypoint/commit/a5a45dabb2fb5ec9ebcd27eebd6b63487c52b536))


### Bug Fixes

* card backdrops show again; last names on cards and in the sidebar ([ad1dbbc](https://github.com/tuckner/wow-waypoint/commit/ad1dbbc1e2207b5e3c875d35afa7e7fdcdfa3798))
* sit the card model lower so it stands on the backdrop ([cb3522f](https://github.com/tuckner/wow-waypoint/commit/cb3522f3e983482dd11aa9e1c412707bfb3f220c))

## [0.1.1](https://github.com/tuckner/wow-waypoint/compare/wow-waypoint-v0.0.1...wow-waypoint-v0.1.1) (2026-11-19)


### Features

* offer the current folder first when picking where notes go ([ae30475](https://github.com/tuckner/wow-waypoint/commit/ae30475cb47d0152c2eaeffd6b3b375397c75ac2))
* pick where notes are saved and use wow-waypoint from any folder ([34b1747](https://github.com/tuckner/wow-waypoint/commit/34b1747013a94652f2adcbf216d6c3180c50ee9f))
* wow-waypoint 0.0.1 ([afc59de](https://github.com/tuckner/wow-waypoint/commit/afc59de081e92294b489a0c301e18ee38618cf57))


### Miscellaneous Chores

* release 0.1.1 ([ed5a9ed](https://github.com/tuckner/wow-waypoint/commit/ed5a9ede8b073d7d80665fb5e681b86360d56320))

## 0.0.1 (2026-11-18)

First public release.

- **Tracking:** armory snapshots (WoW Forever), gear summaries, milestones, a live activity log, `doctor` parse checks and a status line.
- **Skills:** `/wow-init` setup, `/plan`, `/recap`, `/instance` role briefings, `/party`, `/dashboard`, `/wow-help`.
- **Waypoint dashboard:** a page per character (trading card with switchable backdrops and save-as-image, Hero panel with Up next, route-to-60 survey map, gear readout), friend pages, and Progress pages for standings, leveling, gear, activity and the journal.
- **Waypoint design system** in `design/`: tokens and rules shared by every generated page.
- **Wowhead lookups:** item icons and tooltips, cached locally; only item IDs and icon names are sent.
