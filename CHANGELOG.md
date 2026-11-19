# Changelog

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
