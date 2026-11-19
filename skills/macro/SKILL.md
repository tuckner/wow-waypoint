---
name: macro
description: Write in-game WoW macros for the user's character — finding and targeting quest mobs, rares and NPCs, casting spells and shifting forms, mouseover and self-cast heals, trinkets and items, stopcasting or interrupts, and group or chat shortcuts. Uses plain slash commands only, no scripts. Use when the user asks for a macro, wants one button to do several things, can't find a quest mob, rare or NPC ("where is Shadumbra"), wants a sweep macro for their current quests, or says "/wow-waypoint:macro".
argument-hint: "[what it should do | mob or NPC names | current] [character]"
---

# Macros

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words).

## 1. Work out what they need

- **What the macro should do**, from `$ARGUMENTS` or the conversation. If it's vague ("macros for my druid"), offer 3–5 that fit their class, role and level, and let them pick.
- **Character:** read `notes/characters/<slug>/summary.md` (find the folder with `wowchar where`) for class, level, talents and roles. Use only spells they have at their level, and say so when a macro needs a spell they'll learn later.
- **Version:** check `wowchar profile`. The rules below are for the Classic-based clients (Classic Era, Hardcore, SoD, Forever). For Retail, use its own syntax and limits.
- **Targeting a quest:** `current` or no names means read the character's recent `activity.md` and take the "Working on…" and quest lines that aren't marked done, listed in one line. Turn each quest into the exact in-game unit names. Use your own knowledge for base-game quests, and look up only quests that are new or changed in this version (for Forever, `wowhead.com/forever/quest=<id>`). Ground objects like jugs, crates and herbs can't be targeted, so say so in one line and point to the map or Questie.
- Use **exact names** for spells, items and units, with the right capitalization and punctuation. A wrong name fails silently.

## 2. Rules (every macro)

- **255 characters max**, newlines included. Count each macro and print the count. If one runs over, split it.
- **Macro names: 16 characters max.** Suggest the question-mark icon, so the button shows the icon of whatever the macro will cast.
- **No `/run` or `/script`, ever.** Script lines make the client ask the player to allow custom scripts, which weakens their security setting. Use only slash commands and conditionals. If something can only be done with a script, say so and offer the nearest plain version.
- **One press, one action.** Blizzard allows one spell or ability per hardware press, so each press casts at most one thing. Never write anything that loops, moves the character, or acts without a press.
- **Conditionals** go in square brackets, and the first matching clause wins: `[@mouseover,help,nodead]`, `[@player]`, `[harm]`, `[nodead]`, `[combat]`, `[mod:shift]`, `[form:N]`, `[stealth]`, `[exists]`. `@unit` is shorthand for `target=unit`.
- **Spell ranks:** `/cast Healing Touch(Rank 4)` picks a rank. Without one, the highest rank is cast.
- **Forms:** `/cast !Cat Form` shifts into the form and doesn't shift you out if you're already in it. `[form:N]` numbers depend on which forms the character knows, so prefer the `!` form over `[form:N]`.
- `#showtooltip` on the first line shows the right icon and tooltip. It costs characters, so drop it if the macro is tight.

## 3. Templates

**Targeting** (only finds units near you, not across the zone, so tap it as you move):
```
/cleartarget
/targetexact Shadumbra
/cleartarget [dead]
```
- `/targetexact` matches the exact name. `/tar` does a partial match, so `/tar Satyr` also hits Satyr Trickster, which is useful for sweeping a mob family.
- **Sweep:** chain one `/tar` per name. A miss leaves the current target alone, so the last line that finds something wins. Put the most important one last, start with `/cleartarget`, and end kill macros with `/cleartarget [noharm]`.
- Add a skull only when asked: `/stopmacro [noexists]`, then `/tm 8`. A second press on the same unit removes it.

**Mouseover heal**, which falls back to your target and then to yourself:
```
#showtooltip
/cast [@mouseover,help,nodead][help,nodead][@player] Rejuvenation
```

**Self-cast with a modifier** (hold Alt to cast on yourself):
```
#showtooltip
/cast [mod:alt,@player][] Healing Touch
```

**Stop casting, then cast** (interrupts and emergency spells):
```
#showtooltip
/stopcasting
/cast Earth Shock
```

**Form plus opener** (the first press shifts, the next one opens):
```
#showtooltip
/cast [noform] !Cat Form; Ravage
```
For any other action from caster form, use `[noform]` and `;` the same way. Prefer this over `[form:N]`.

**Trinket and on-use item, then an ability:**
```
#showtooltip
/use 13
/cast Heroic Strike
```
Slot 13 is the top trinket and 14 the bottom. An item on cooldown is skipped, and the cast still goes off.

**Chat or group shortcut:**
```
/p Pulling in 3, mark skull first
/tm 8
```

## 4. Reply

Keep it to one screen.

- **Per macro:** a name (16 characters or fewer), one line on what it does, the macro in a code block, and its character count. Flag anything you couldn't confirm for this client as (verify).
- **How to add it, once:** type `/macro`, click **New**, pick the **character-specific** tab (18 slots; general has 120, shared by all your characters), choose the question-mark icon, paste the macro, then drag it to your action bar.
- **Caveats in one line each**, only the ones that apply: a spell they don't have yet, targeting only reaching nearby units, objects not being targetable.
- Offer to save them: append to `notes/macros.md` in the workspace (create it with a `_Last updated: YYYY-MM-DD_` line; one `## <macro name>` section per macro with its character and purpose). Rewrite a macro already in that file instead of adding a duplicate.

Don't log macro requests to `activity.md` by themselves. But if the request shows what they're doing ("can't find Shadumbra"), log that the usual way: `wowchar log <slug> "Hunting Shadumbra (Ashenvale Hunt)"`.
