---
name: macro
description: Write in-game WoW macros that find and target the mobs, rares and NPCs for the quests the user is on — one keypress targets the nearest live match with no scripts. Use when the user asks for a targeting or "find" macro, can't find a quest mob, rare or NPC ("where is Shadumbra", "I can't find Alonso"), wants a scan or sweep macro for their current quests, or says "/macro".
argument-hint: "[quest, mob or NPC names… | current] [character]"
---

# Targeting macros

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words).

## 1. Work out what to target

- **Named in `$ARGUMENTS`** (quests, mobs or NPCs): use those.
- **`current` or nothing named:** read the character's recent `activity.md` (find the folder with `wowchar where`) and take the "Working on…" and quest lines that aren't marked done. List what you found in one line and build from it. If nothing is open, ask which quests.
- **Quest → unit names.** Turn each quest into the exact in-game names of the units to kill, loot or talk to. Use your own knowledge for quests that exist in the base game. Look up only quests that are new or changed in this version (check the version in `wowchar profile`; for Forever, `wowhead.com/forever/quest=<id>` lists the mobs). Skip objectives that are ground objects (jugs, crates, herbs). `/target` can't find objects, so say so in one line and point to the map or Questie.
- Use **exact names** with the right capitalization and punctuation (`Shadumbra`, `Twilight Lord Kelris`, `Bleakheart Satyr`). A wrong name fails silently.

## 2. Build the macros

Rules for the Classic-based clients (Classic Era, Hardcore, SoD, Forever):

- **255 characters max per macro**, newlines included. Count each macro and print the count. If one runs over, split it.
- **Macro names: 16 characters max.** Suggest the question-mark icon (the client then shows the first spell's icon, and these have none).
- **Exact vs partial:** `/targetexact Name` matches only that name. `/tar Name` is a partial match ("Satyr" also hits "Satyr Trickster"). Use `/targetexact` for single rares and NPCs, and `/tar` with a shared word to sweep a mob family.
- **Range:** these only find units the client has loaded near you (roughly your view range), not across the zone. Tell the user to tap it as they move.
- **Skip corpses and friendlies:** add `/cleartarget [dead]` after targeting. On kill macros, also add `/cleartarget [noharm]`. Leave that line off for friendly NPCs.
- **No `/run` or `/script`, ever.** Script lines make the client ask the player to allow custom scripts, which weakens their security setting. Use only plain slash commands and conditionals.
- **Targeting only, by default.** The target frame popping up is the alert. Add a mark only if the user asks: `/stopmacro [noexists]` then `/tm 8` (skull; `/tm 1` star for NPCs). A second press on the same unit toggles the mark off.
- **Several mobs in one macro:** chain one `/tar` per name. A miss leaves the current target alone, so the **last line that finds something wins**. Put the most important target last and start with `/cleartarget`.
- **One press per scan.** Blizzard blocks macros that loop or act on their own. Never write anything that moves, attacks or repeats automatically. Suggest binding the macro to a key and tapping it.

### Templates

Single rare or quest mob:
```
/cleartarget
/targetexact Shadumbra
/cleartarget [dead]
```

Quest sweep (several kill targets, most important last):
```
/cleartarget
/tar Bleakheart
/tar Felmusk
/targetexact Xavian Hellcaller
/cleartarget [dead]
/cleartarget [noharm]
```

Friendly NPC in a crowd (quest giver, trainer, vendor):
```
/targetexact Senani Thunderheart
```

## 3. Reply

Keep it to one screen.

- **Per macro:** a name (16 characters or fewer), one line on what it does and for which quest, the macro in a code block, and its character count.
- **How to add it, once:** type `/macro`, click **New**, pick the **character-specific** tab (18 slots; general has 120), choose the question-mark icon, paste the macro, then drag it to your action bar.
- **Caveats in one line each:** only nearby units, and objects aren't targetable.
- Offer to save them: append to `notes/macros.md` in the workspace (create it with a `_Last updated: YYYY-MM-DD_` line; one `## <macro name>` section per macro with its quest). Rewrite a macro already in that file instead of adding a duplicate.

Don't log macro requests to `activity.md` by themselves. But if the request shows what they're doing ("can't find Shadumbra"), log that the usual way: `wowchar log <slug> "Hunting Shadumbra (Ashenvale Hunt)"`.
