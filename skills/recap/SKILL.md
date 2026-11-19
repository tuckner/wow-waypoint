---
name: recap
description: Write an adventure recap for a tracked WoW Forever character — what changed since the last recap (levels, gear, professions, talents, rep), how it compares to the current plan, and a short story-style log entry. Use when the user asks for a recap, summary of progress, "what have I done", or a session/weekly wrap-up.
argument-hint: "[character name or slug] [since YYYY-MM-DD]"
---

# Character recap

1. **Pick the character.** Match `$ARGUMENTS` against `notes/characters/characters.json` (name or slug). If none is given and only one character was played since the last recap, use that one. If it's ambiguous, ask.
2. **Refresh data:** `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" update --force`. The armory site only updates on logout; if `lastLogin` in the summary is older than the user implies, say the data may lag.
3. **Find the window.** Read `notes/characters/<slug>/journal.md` if it exists. The newest `<!-- recap: DATE -->` marker is the start of the window, unless the user gave a `since` date. If there's no journal, use the first snapshot.
4. **Get the facts:** `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" diff <slug> --since <date>`, plus `notes/characters/<slug>/summary.md` for current state and pace.
4a. **Read the live log:** `notes/characters/<slug>/activity.md` holds notes recorded during chats since the last `=== recapped ===` marker, plus answered questions. These are the most reliable chat facts. Use them first.
4b. **Infer from chat:** `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" chats --since <date>` prints every question the user asked in this project, with local timestamps. Questions show what they were doing. Pull out:
   - zones and towns ("where is X in Ashenvale")
   - dungeons run ("as a healer what do I need to know about BFD", "I got the staff!")
   - quests worked on, loot won, purchases, crafting, training, talent choices
   - errands left open

   Assign each item to a character by its date (match `lastLogin`/level changes in the history) and topic (class, spec, gear type). Treat "where is/how do I" as *working on* and "I got/I did" as *done*. Leave out pure lookups that say nothing about play, such as addon settings or lore. If the data contradicts something you inferred, go with the data.
5. **Check the plan.** If `notes/characters/<slug>/plan.md` exists, mark each goal as done, partly done or not started, based only on the data. Don't guess at quests: the data has a quest count, not quest names.
5a. **Voice.** Check `recapVoice` in the profile (`python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" profile`).
   - `light` (default): the format below.
   - `in-character diary`: the same structure, but the hook and bullets are written in first person as the character.
   - `lore chronicle`: add a one-line lore aside per entry (zone or faction history).
   - With `spoilers: avoid`, keep new-content plot out.
6. **Write it as a light overview.** The journal is an easy-to-skim journey log, not prose fiction. Keep the reading light and fun, but write it as a summary rather than a story. Read the latest entries first so the tone and numbering stay consistent.
   - **Title:** 2–6 words naming the defining event, numbered with Roman numerals after the last entry. Examples: "V. Down in the Deeps", "III. Kegs, Kodos and Kolkar". Puns and callbacks are welcome.
   - **Subtitle:** date range · level range · a short hero's-journey tag. Examples: Call to Adventure, First Trials, Road of Trials, Allies and Mentors, Descent into the Abyss, Ordeal, Reward, Return with the Elixir, Refusal of the Call. Tags can repeat.
   - **Hook:** one witty line that sums up the stretch.
   - **Bullets:** 3–5 short ones covering dungeons, key loot, zones and quests, training, talents, professions and open errands. **Bold** the highlights, and use the user's own quotes when they're funny. Don't mark where each fact came from; the journal is a light tracker, not a record of sources.
   - Base it on the data, `activity.md` and the chat. It doesn't need to be perfectly accurate, but don't invent big events.
   - Split a long window into several entries when it has clearly different stretches.
7. **Append the entry** before the closing "Where things stand" block of `journal.md`, which reads oldest first. Then update that block with current level, iLvl, quests, professions, talents, rep and "Still open" items, plus a plan check if a plan exists. Entry format:

```markdown
## VII. The Sunken Lantern
_Nov 20–21 · levels 28 → 30 · the Ordeal_

One-line hook.
- **Travel Form** at 30
- **Arena Wristguards** from the Gurubashi trip
- Leatherworking 109 → 125

<!-- recap: 2026-11-21 -->
```
   The hidden `<!-- recap: YYYY-MM-DD -->` line (today's date) is how the script knows when the last recap happened. Always include it. If the file doesn't exist, create it with `# <Name> — journey log`, an italic one-line note, `---`, the entries, then the "Where things stand" block.
8. **Close the window:** `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" log <slug> "=== recapped ==="`. Keep unanswered `?` lines. Answered ones were already rewritten as facts.
9. **Fill gaps.** If key outcomes are still unknown (did X drop, which zone, finished Y), ask 1–3 short questions at the end of the reply and `log` them with `?`.
10. **Reply** with the new entry. Offer `/plan` if the plan is stale or mostly done.

Rules: light tone, no invented events. Keep each entry under ~8 lines. Reply with the new entry itself.
