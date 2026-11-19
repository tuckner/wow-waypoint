---
name: wow-help
description: Explain what the wow-waypoint plugin can do — every command and feature, how they fit together, and what to try next given what's already set up. Use when the user asks for help with the WoW tracker, "what can you do", "how does this work", "what commands are there", or "/wow-help <topic>".
argument-hint: "[topic: setup | tracking | log | milestones | instance | macro | plan | recap | party | dashboard | statusline | doctor | versions | data | commands]"
---

# wow-waypoint help

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux.

1. Run `wowchar setup-status` (JSON) so the help fits this person: are characters tracked, is there a profile, any friends, is the status line installed, which versions are supported.
2. **No topic in `$ARGUMENTS`:** reply with the overview below, trimmed to one screen. Then add a short **"Next for you"** line based on setup-status:
   - nothing set up → "Run `/wow-init`"
   - no friends → "Add friends with `/wow-party add <name>`"
   - no status line → "Turn on the status line with `/wow-init statusline`"
   - otherwise → suggest `/wow-instance` before their next dungeon, or `/wow-dashboard`.
3. **With a topic:** give only that section, in more depth: what it does, an example of how to ask for it, and the matching `wowchar` command. Use the README and the skill's own SKILL.md for details.
4. Write it the way a guildmate would explain it: plain words, no file paths unless they ask how it works under the hood.

## Overview to present

**Get started**
- `/wow-init`: one-time setup. It asks which version you play (Forever, Classic Era, Hardcore, SoD, Retail…), your characters (it looks each one up so you can confirm), region, roles, playstyle (relaxed, optimized, lore, RP…), goals, how much you play, friends' characters, and whether you want the status line. Run it again any time to change an answer.

**Just play and ask questions**
- **Automatic snapshots:** at session start your characters are refreshed from the armory site, at most once a day. It only updates after you log out, so say "I just logged out" to refresh right away.
- **Live activity log:** as you ask questions ("where's the Felhunter quest?", "I got the staff!"), Claude quietly notes what you're doing. When an outcome matters, it asks you about it later.
- **Milestones:** when you level past an unlock (Travel Form at 30, your mount at 40, a new profession tier), you get a heads-up once.
- **Gear and progress questions** ("what should I upgrade?", "how's my pace?") are answered from your character's current gear, talents, professions and rep.

**Before a dungeon or raid**
- `/wow-instance <name>` (e.g. `/wow-instance sfk`, `/wow-instance mc`): a briefing for *your* class, level and role. It covers what you dispel and of which type, what you interrupt and with which spell, what you can CC, where to stand, raid assignments, attunements, resist gear, consumables your professions make, and loot for your spec. If it has no notes for that instance, or they're old, it researches them first and saves them for next time.

**While questing**
- `/wow-macro`: in-game macros for your character, such as targeting a quest mob, rare or NPC (`/wow-macro current` uses the quests you've mentioned), mouseover heals, form plus opener, trinkets and party shortcuts. They use only spells you have at your level and plain slash commands, so the game never asks you to allow scripts.

**Planning and looking back**
- `/wow-plan`: next session's to-do list, a leveling route, gear targets for your weakest slots, and profession and training goals, shaped by your playstyle and time budget.
- `/wow-recap`: a short, titled journal entry for what you did since the last one, in the voice you picked (light summary, in-character diary, or lore chronicle).
- `/wow-dashboard`: a page with charts of level and item level over time, quests per day, rough time to max level, gear and professions. It opens in your browser and stays on your computer.

**Friends**
- `/wow-party`: follow friends' characters (read-only, from their public armory page). See who's ahead, what they did this week, which dungeons fit everyone, and who needs what. Friend news shows up at session start, and `/wow-instance` can tell who in the group covers curses, poison or interrupts.

**Always on**
- **Status line:** a short line under the prompt, e.g. `Brightmane 28 Druid · iLvl 24 · next: Travel Form @30 · ⚠ repair gear`. It shows your main (favorite) character; say "playing <name> today" to pin another one for just that session (`focus`), without changing your main.
- **Health check:** if the armory site changes and stops reading correctly, you get a warning, and "run doctor" shows exactly where it broke.

**Good to know**
- **Your data stays local:** everything about your characters lives in your own WoW folder, never in the shared plugin.
- **Versions:** snapshots work for WoW Forever today. Other versions get setup, Q&A, plans and recaps, and snapshots once their armory site is added.
- **Fixing facts:** spell levels, milestones and the instance research method are plain files in the plugin's `data/` folder. If Forever changed something, it's a one-line fix.

## Topic details (for `/wow-help <topic>`)
- **commands**: list the `wowchar` commands grouped as in `wowchar` with no arguments (it prints the help). Say most people never need them because the skills run them.
- **log**: how the activity log works (facts versus `?` questions), where it lives (`notes/characters/<slug>/activity.md`), and that `/wow-recap` folds it into the journal.
- **versions**: the supported and not-yet versions from setup-status, and that each version uses its own armory site (`data/sources.json`).
- **data**: what's stored where. `notes/characters/` holds snapshots, summary, activity, journal and plan; `notes/profile.md` holds the profile; `notes/instances/` holds instance notes. Mention `wowchar where`.
- **statusline**: install with `wowchar install-statusline` (or `--chain` to keep an existing one), pin with `wowchar focus <char> [--session ID]` (this session's character; `main` stays your favorite), unpin with `focus --clear`. It never goes online.
- **doctor**: `wowchar doctor [<char>]` checks the site step by step and saves the page if something fails.
