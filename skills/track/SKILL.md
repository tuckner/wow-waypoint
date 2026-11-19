---
name: track
description: Run WoW character tracking day to day (armory snapshots, gear summaries, milestones, a live activity log, parse health). Use when the user adds a character, says they just logged out, asks about their own gear, level, progress or professions, or when the tracker's session-start message needs acting on. For first-time setup use wow-init.
argument-hint: "[add \"Character Name\" [--region us]] | [update] | [doctor]"
---

# Character tracking

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux. Data lives in the user's workspace under `notes/` (characters, profile, instance notes), never inside the tracker repo; the script refuses to write there. Run `wowchar where` if unsure which folder is in use. **First-time setup, profile changes or adding friends → the `wow-init` skill. "What can this do?" → `wow-help`.**

## Commands
- `update [--force]`: snapshot everyone. Use `--force` when they say they just logged out or changed gear (wowf.io updates on logout).
- `main [<char>]` (show or change the primary character), `focus <char> --session ID` / `focus --clear` (this session's character; see below), `add "<Name>" [--region us] [--version forever] [--watch] [--group G] [--role tank,dps] [--main]`, `set <char> key=value`, `list`, `where`
- `gear <char>`: weakest-first, with stats, enchants, durability and resistances
- `diff <char> --since YYYY-MM-DD`, `milestones <char>` (next 4 levels and profession tier nudges)
- `log <char> "..."` (a leading `?` marks an open question), `pending`, `chats --since DATE`
- `party [--since DATE]`, `brief <instance>`, `dashboard --open`, `statusline`, `install-statusline`
- `doctor [<char>]`: checks the armory page still parses, step by step, and saves the page on failure
- `profile`, `profile set key=value`, `setup-status`

## Main vs focus
- **`main`** is the user's favorite character and the default everywhere: status line, briefings, plans, any question that doesn't name a character. It's long-lived. Change it only when the user says their favorite changed ("my warlock is my main now"), never just because a session is about another character.
- **Context beats main.** "My warlock", a level, a zone or a class spell that only fits another character means that character. Answer and `log` for it; don't change anything for a one-off mention.
- **`focus`** follows stretches of the conversation, and can switch back and forth within one session. When they move onto another character for a while ("ok, warlock questions now", "playing Zalvi today", or a second question in a row about it), run `focus <slug> --session <id>` (the session-start message gives the id; it's also in the scratchpad path) and say so in one line. It pins the status line for this session only and leaves `main` alone. When they come back to main (a druid question, "back on Brightmane"), run `focus --clear` the same way; for a third character, just re-pin. While a pin is on, questions that don't name a character are about the pinned one. Leave out `--session` only when they ask to pin it everywhere.
- The session-start message prints `Session focus: …` when a pin applies to the session; assume that character there.

## Files per character (`notes/characters/<slug>/`)
- `summary.md` (auto): gear, talents, professions, reps, pace, weak slots, **Upcoming** (next 2 levels' unlocks and profession nudges), change log. **Read it first** for any gear, upgrade or progress question.
- `activity.md`: the live log written with `log`
- `journal.md`: from the `recap` skill
- `plan.md`: from the `plan` skill

## Acting on the session-start message
- **Milestones reached**: open the reply with them, one line each ("You hit 30: Travel Form is trainable"). Once they confirm training, `log` it.
- **⚠ armory parsing looks broken**: run `doctor <char>` and show the failing step. If the site changed, the fix goes in `scripts/sources/<site>.py`. Until then, answer from the last good snapshot and say it may be stale.
- **Friend news**: mention it in one short line. Don't log it.
- **Player profile**: respect it (answer length, spoilers, playstyle, recap voice).

## Live activity log (every session)
- **While chatting:** when a message reveals what they're doing, append one line with `wowchar log <slug> "..."`. That covers a zone or quest, a dungeon run, loot won, a purchase, training, a talent pick, or a plan like "heading to Hillsbrad". Write it as a fact or a "working on", not as their question. Example: `log thrall-doomhammer "Tanking SFK at ~24; won Worgpelt Leggings"`. Skip pure lookups like addon settings or lore. Batch it with your answer and don't mention it unless asked. Never log watched friends.
- **Open questions:** when an outcome is unknown and would matter (did it drop, did they finish the quest, which character), log it with a `?` prefix rather than interrupting. Ask 1–3 at a time at a natural pause. When they answer, edit that line in `activity.md` to the answer and drop the `?`.
- **Session start:** the hook prints "Since last recap…" with new activity and open questions. Open the first reply with a 2–3 line "last time" summary and the open questions, then answer what they asked. If it's been more than ~3 days or ~2 levels since the last recap, offer the `recap` skill.
