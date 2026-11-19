---
name: wow-instance
description: Role briefing for a WoW dungeon or raid, specific to the user's character — which debuffs they dispel (and of which type), what they interrupt and with which spell, which adds they CC, positioning and threat, raid assignments, attunements, resist gear, consumables and loot for their spec. Use when the user is about to run, or asks about, a dungeon or raid ("/wow-instance SFK", "heading into BFD", "what do I do in MC").
argument-hint: "<dungeon or raid name/abbreviation> [character] [tank|heal|dps] [with <friends>]"
---

# Instance briefing

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux.

1. **Character and role.** Default: the most recently played owned character (the script picks it if no character is named). Role: from `$ARGUMENTS`, else the character's saved `roles` (first one), else infer from talents. If the class has several roles and none is saved, ask once, then save it: `wowchar set <slug> roles=tank,dps`.
2. **Run the briefing:** `wowchar brief [<char>] <instance> [--role <role>]`.
   - **Exit 2 (no notes yet)**, or the output starts with **STALE / INCOMPLETE**: research the instance by following `${CLAUDE_SKILL_DIR}/../../data/instances/RESEARCH.md`. In short:
     1. Scope it and decide what the version changed.
     2. One search for version changes. Look loot up on Forever.
     3. Take dispel type, interruptibility and add creature types from database tooltips.
     4. Tag it per boss using the checklist.
     5. Cross-check, and mark `(verify)`.
     6. Write `notes/instances/<slug>.md` with a `## Sources` section.

     Stay within the budget (~5 lookups for a dungeon, ~8 for a raid), then rerun `brief`. For STALE, refresh only version changes and loot unless a source contradicts the rest.
   - **UNSOURCED** alone: brief anyway, and add sources the next time the note is refreshed.
   - Tell the user in one line when the briefing rests on fresh research versus an older note, and flag `(verify)` items that touch their jobs.
3. **Reply in one screen**, rewriting the script output (don't paste it raw):
   - **Your job**: 3–6 bullets of what only they or their class covers, naming the button ("Arugal's Curse → Remove Curse, fast").
   - **Per boss**: 1–3 lines each. Skip bosses with nothing for them beyond "tank and spank".
   - **Watch out**: mechanics their kit can't answer yet (with "you get X at level N" when the script says so).
   - **Before you go**: quests to grab, the gear check (repairs, empty slots), consumables their professions can make. For raids: attunement and keys (ask whether they have them and log the answer), resist totals versus what's needed, consumables by role.
   - **Loot for you**: the filtered list.
4. **Profile:** read the profile line from the session-start hook (or `wowchar profile`).
   - *Optimized*: full assignments, consumables and pull tips.
   - *Relaxed*: essentials only.
   - *Lore-driven* or *RP*: add a one-line story hook per boss.
   - *Hardcore* realm: add death-risk warnings (wipe mechanics, pulls to avoid, escape buttons).
   - *Avoid spoilers*: no plot details for new Forever content.
5. **Group coverage:** if the user names who's coming and those friends are watched (`wowchar party`), list who covers curse, poison, disease and magic removal and interrupts, and which gaps nobody covers. Use `data/class-abilities.json` with each friend's class and level.
6. **Log it:** `wowchar log <slug> "Running <instance> as <role>"`, plus an open question for the loot they're after: `wowchar log <slug> "? Did <boss> drop <item>?"`.
