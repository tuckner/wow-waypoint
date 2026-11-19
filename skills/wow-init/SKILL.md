---
name: wow-init
description: First-run setup for WoW character tracking — asks which game version they play, their characters, region, roles, playstyle and goals, friends' characters, and installs the status line. Use when someone first uses the WoW tracker, says "set up", "get started", "init", or wants to change their profile, add friends, or redo setup. Re-running edits answers instead of starting over.
argument-hint: "[what to change, e.g. 'add friends' or 'playstyle']"
---

# WoW tracker setup

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux. Keep the whole flow quick: about 4 question rounds and under 3 minutes. Every optional question can be skipped.

## 1. Check state
Run `wowchar setup-status` (JSON).
- `inside_repo: true` → stop: this is the plugin's own folder. Ask them to open Claude Code in the folder they want for WoW notes.
- If characters, profile and statusline are all set up, summarize them in 3 lines and ask what to change (`$ARGUMENTS` may already say). Jump to that step only.
- If it's partly done, resume at the first missing step. Don't re-ask answered questions.

## 2. Workspace rules
If `claude_md` is `missing`, copy the `template` path from setup-status to `./CLAUDE.md`, filling in the version line once the version is known (step 3). If a non-WoW CLAUDE.md exists, offer to append the template's sections instead of overwriting.

## 3. Game version (ask first, on its own)
One `AskUserQuestion`: "Which version of WoW do you play?" Options: WoW Forever, Classic Era / Hardcore, Season of Discovery, Retail (the user can type "a mix" or Cata/MoP Classic under Other).
- Map the answer to a version key: `forever`, `era`, `hardcore`, `sod`, `progression`, `retail`. Save it with `wowchar profile set version=<key>`.
- setup-status lists `versions_supported`. If theirs isn't supported, say plainly: "Character snapshots aren't available for <version> yet (no armory site hooked up), but Q&A, plans and recaps still work." Then continue.
- "A mix": ask the version per character in step 5.

## 4. Characters (free text)
"What are your characters' names (first and last, as on the armory)? Main first."

## 5. Round 1 (one AskUserQuestion, at most 4 questions)
- **Region**: US / EU (wowf.io needs it: `/players/<region>/<first-last>`)
- **Realm type**: the options from data/sources.json `realmTypes` for their version (e.g. Forever: PvE / PvP / RP). Skip this if the first fetch in step 6 returns it, since wowf.io reports it.
- **Playstyle** (multiSelect): Relaxed, Optimized / speed, Lore-driven, Role-play (they can type completionist, gold-making or PvP under Other)
- **Time per week**: under 5h / 5–15h / 15h+

Save the answers: `wowchar profile set region=us realmType=PvP playstyle=relaxed,lore hoursPerWeek=5-15`.

## 6. Add and confirm each character
`wowchar add "<First Last>" --region <r> [--version <v>] [--main]` (main = the first one named). Read back what it prints ("Brightmane Hoof: level 28 Tauren Druid, PvP realm. That's you?").
- 404: try the other region, and remind them wowf.io only knows a character after its first logout.
- Unsupported version: the add saves the entry without a snapshot. That's fine.
- If the fetch reports a realm type, save it: `profile set realmType=<value>`.

## 7. Round 2: roles
One question per character whose class can do more than one role (multiSelect; options by class: druid tank/heal/dps, paladin tank/heal/dps, warrior tank/dps, priest and shaman heal/dps). Single-role classes are dps automatically. Save with `wowchar set <slug> roles=tank,dps`.

## 8. Round 3 (one AskUserQuestion)
- **Goals** (multiSelect): Hit max level, Raid-ready, Profession / gold target, A specific mount (Other: a date, a PvP rank)
- **Answer style**: Brief / Detailed
- **Spoilers for new content**: Avoid / Fine
- **Recap voice**: Light summary (default) / In-character diary / Lore chronicle

Save: `profile set goals=... answerStyle=brief spoilers=avoid recapVoice=light`. For free-text goals ("60 by January"), store the user's words.

## 9. Friends (free text, optional but encouraged)
"Want to add friends' characters? They show up in the party view, friend news at session start, and group coverage in /instance briefings (who handles curses, interrupts…). Names, region, and a group name if you like. It's polite to ask them first, even though wowf.io is public."
For each: `wowchar add "<Name>" --region <r> --watch [--group <name>]`, confirming like step 6. Also ask: solo / duo-trio / guild, the guild name, and the usual play night → `profile set group.type=duo-trio group.guild=... group.night=Tue`.

## 10. Status line
Show an example (`Brightmane 28 Druid · iLvl 24 · next: Travel Form @30 · 3 open ?`) and ask whether they want it in this folder. On yes: `wowchar install-statusline`. If it reports an existing status line, show it and offer `install-statusline --chain` (keeps theirs, appends ours).

## 11. Optional extras (one quick free-text question, skippable)
"Any addons you use (Questie, DBM, Details…) or anything else I should know?" → `profile set addons=Questie,DBM`.

## 12. Finish
1. `wowchar update`, then show what's tracked.
2. Log a start line for each owned character: `wowchar log <slug> "Started tracking (wow-init)"`.
3. Reply with a 5-line summary: version, characters and roles, profile in one line, friends, status line. Then suggest: `/plan` for what to do next, `/instance <name>` before a dungeon or raid, `/dashboard` to see progress.
