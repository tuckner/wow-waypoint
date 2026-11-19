# 🧭 WoW Waypoint - Claude Skill

**A leveling buddy for World of Warcraft that lives in Claude Code.**

Tell it who you play, and it keeps an eye on your characters: what you're wearing, what you've done, what's next. Ask it anything you'd ask a guildmate ("what should I do tonight?", "what do I interrupt in SFK?", "is this belt an upgrade?") and get an answer that fits *your* character.

> 🎮 Made for **WoW Forever**. Other versions work for questions, plans and recaps, but can't track your character's gear or level yet.

---

## 🚀 Get started

You'll need [Claude Code](https://claude.com/claude-code) and Python 3. Python is already on Macs and most Linux machines; on Windows, grab it from [python.org](https://www.python.org/downloads/).

**1. Make a folder for your WoW notes** and open Claude Code there:

```sh
mkdir -p ~/wow && cd ~/wow && claude
```

**2. Install wow-waypoint:**

```
/plugin marketplace add tuckner/wow-waypoint
/plugin install wow-waypoint@wow-waypoint
```

If it asks where to install, pick **project** so it stays in this folder.

**3. Restart Claude Code** in the same folder and run:

```
/wow-init
```

It asks about your characters, how you like to play and who you play with, and then you're set. 🎉 A good first thing to try is `/plan`.

---

## ✨ What it does

🧭 **`/dashboard`: your adventure at a glance.** A page with a trading card for each character, what to do next, your route to 60, your gear, your friends, and a journal of everything so far.

🗺️ **`/plan`: what to do next.** Where to level, which dungeons to run, which gear to chase, and what to train, sized to how much time you have.

📖 **`/recap`: your story so far.** Turns your recent sessions into a short journal chapter.

⚔️ **`/instance <name>`: a briefing before you go in.** What *you* should dispel, interrupt and crowd-control, where to stand, and which loot is for you.

👥 **`/party`: you and your friends.** Who's ahead, what they've been up to, and which dungeons fit everyone.

❓ **`/wow-help`: lost?** Shows everything it can do.

**It also works quietly in the background:**
- 🔄 Checks your characters when you start a session and calls out milestones ("you hit 30: Travel Form!").
- 📝 Remembers what you mention (a drop, a quest, a dungeon) for your next recap.
- 📟 Can show your character in Claude Code's status line: `Brightmane 28 Druid · iLvl 24 · next: Travel Form @30`

---

## 🔄 Keeping it up to date

```
/plugin marketplace update wow-waypoint
```

Then restart Claude Code. You can also turn on auto-updates under `/plugin` → **Marketplaces**. See what's new on the [Releases page](https://github.com/tuckner/wow-waypoint/releases).

> 📟 Using the status line? Run `/wow-init` again after an update so it keeps working.

## 🤝 Playing with friends

Your friends can install it the same way and follow each other with `/party`. Only add someone's character if they're okay with it.

## 🗑️ Removing it

```
/plugin uninstall wow-waypoint@wow-waypoint
```

Your notes stay in your folder.

---

## 🔒 Your data stays with you

Everything about you (characters, journal, plans, dashboard) is saved in your own folder, under `notes/`. It only reads public information: your characters' pages on wowf.io, item details from Wowhead, and game images. It never sends your notes anywhere.

---

## 🧑‍💻 Want to help?

Bug reports and pull requests are welcome. If something about the game is wrong (a spell level, a milestone, a dungeon tip), the facts live in plain files under `data/` and are easy to fix. Tests run with `python3 -m unittest discover -s tests`.
