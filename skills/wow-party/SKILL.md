---
name: wow-party
description: Group view of the user's characters and their watched friends — who's ahead, what friends have been doing lately, which dungeons fit everyone's levels, and who needs what gear. Use for "how's the group doing", "what has <friend> been up to", "what dungeon should we run", "who needs X", "level race", or adding a friend's character.
argument-hint: "[--since YYYY-MM-DD] [group name] | add <friend name>"
---

# Party view

`wowchar` below means `python3 "${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py"`. Type the full command each time; don't store it in a shell variable (`W="python3 …"; $W args` fails in zsh, which doesn't split words). The script is also executable, so `"${CLAUDE_SKILL_DIR}/../../scripts/wowchar.py" args` works on macOS and Linux. Friends are read-only "watched" characters: their public armory data only. Never log their activity, and never make plans or recaps for them.

- **Add a friend:** `wowchar add "<First Last>" --region us --watch [--group <name>]`. Mention it's polite to ask them first.
- **Overview:** `wowchar update`, then `wowchar party [--group <name>]`. A table (★ = the user's own) plus the shared level window and anyone lagging or leading.
- **What friends did:** `wowchar party --since <date>` (default: the last 7 days). Summarize each person in one line: levels, notable gear (rare or better), profession jumps, mounts.
- **"What should we run?"** Take the dungeons that fit everyone from the footer. For each candidate, count members whose weak or empty slots that dungeon's loot fills for their spec. Use the `loot:` lines in the instance notes (`brief` output or `data/instances/`) or Classic knowledge. Recommend 1–2 with a reason each. If someone's out of range, say who and suggest the closest fit.
- **"Who needs X":** read the friends' `notes/characters/<slug>/summary.md` gear tables.

Keep it to one screen. Friend data lags until they log out (the armory updates on logout).

Realm filter: when the user asks about friends on one kind of realm ("my PvP friends", "who's on RP"), add `--realm pvp|pve|rp|rppvp` (comma-separated for several). It filters friends only; your own characters always show. The dashboard's Friends tab has the same filter as buttons.
