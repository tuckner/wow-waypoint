"""python3 -m unittest discover -s tests  (from the repo root). Synthetic data only."""
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
FX = REPO / "tests" / "fixtures"

import core  # noqa: E402
import milestones  # noqa: E402
from sources import wowfio  # noqa: E402
from sources.errors import ParseError  # noqa: E402


def snap(level, days_ago, cls="Druid", quests=100, ilvl=20, slug="testy-mctest", name="Testy Mctest", prof=None, gear=None):
    t = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return {"at": t, "slug": slug, "name": name, "race": "Tauren", "class": cls, "faction": "horde", "level": level,
            "itemLevel": ilvl, "lastLogin": t, "quests": quests, "talents": {"Feral Combat": max(0, level - 9)},
            "talentRanks": {"Feral Combat": {"feral_charge": 1}}, "professions": prof or {"Leatherworking": "100/150"},
            "gear": gear or {"Chest": "Test Tunic"}, "gearIlvl": {"Chest": ilvl}, "reps": {}, "stats": {}, "kills": 0,
            "achievements": [], "mounts": []}


class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)
        self._xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.ws / ".config")  # never read the real remembered home
        core.set_root(self.ws)
        core.BASE.mkdir(parents=True)

    def tearDown(self):
        if self._xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._xdg
        self.tmp.cleanup()

    def add(self, slug, snaps, **extra):
        chars = core.load_config()
        chars.append({"region": "us", "slug": slug, "name": snaps[-1]["name"], **extra})
        core.save_config(chars)
        d = core.BASE / slug
        d.mkdir()
        (d / "history.jsonl").write_text("".join(json.dumps(s) + "\n" for s in snaps))
        latest = {"slug": slug, "name": snaps[-1]["name"], "level": snaps[-1]["level"], "class": snaps[-1]["class"],
                  "items": [{"slot": "Chest", "name": "Test Tunic", "ilvl": 24, "quality": 2,
                             "lines": ["+5 Agility", "+4 Fire Resistance", "Durability 10 / 100"]}]}
        (d / "latest.json").write_text(json.dumps(latest))


# ---------- 0. where notes live ----------

class TestHome(Workspace):
    def test_remembered_home_is_used_from_any_folder(self):
        home = self.ws / "wow-notes"
        (home / "notes" / "characters").mkdir(parents=True)
        (home / "notes" / "characters" / "characters.json").write_text("[]")
        core.write_pointer(home=str(home), announce="home")
        elsewhere = self.ws / "some-code-project"
        elsewhere.mkdir()
        root, how = core.find_workspace(elsewhere, use_env=False, explain=True)
        self.assertEqual((root, how), (home.resolve(), "home"))

    def test_local_notes_beat_the_remembered_home(self):
        core.write_pointer(home=str(self.ws / "elsewhere"))
        (self.ws / "elsewhere").mkdir()
        local = self.ws / "local"
        (local / "notes" / "characters").mkdir(parents=True)
        (local / "notes" / "characters" / "characters.json").write_text("[]")
        self.assertEqual(core.find_workspace(local / "notes", use_env=False, explain=True), (local.resolve(), "local"))

    def test_home_set_creates_the_folder(self):
        target = self.ws / "picked"
        env = {**os.environ, "XDG_CONFIG_HOME": str(self.ws / ".config")}
        env.pop("WOWCHAR_HOME", None)
        env.pop("CLAUDE_PROJECT_DIR", None)
        out = subprocess.run([sys.executable, str(REPO / "scripts" / "wowchar.py"), "home", "set", str(target), "--announce", "home"],
                             capture_output=True, text=True, env=env, cwd=self.ws)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue((target / "notes" / "characters" / "characters.json").exists())
        self.assertEqual(core.read_pointer()["home"], str(target.resolve()))
        self.assertEqual(core.read_pointer()["announce"], "home")


# ---------- 1. doctor / parsing ----------

class TestParse(unittest.TestCase):
    def test_ok_fixture(self):
        raw = wowfio.extract(FX.joinpath("player_ok.html").read_text(), "testy-mctest")
        self.assertEqual(raw["level"], 24)
        self.assertEqual(wowfio.check(raw), [])
        n = wowfio.normalize(raw)
        self.assertEqual(n["name"], "Testy Mctest")
        self.assertEqual(n["realmType"], "PvE")
        self.assertEqual(n["items"][0]["slot"], "Chest")

    def test_wowhead_tooltip_lines(self):
        import wowhead
        h = ("<table><tr><td><!--nstart--><b class=\"q3\">Hood</b><!--nend--><br>Item Level 25<br>Binds when picked up"
             "<table width=\"100%\"><tr><td>Head</td><th>Leather</th></tr></table>+8 Agility</td></tr></table>")
        self.assertEqual(wowhead.tooltip_lines(h), ["Hood", "Item Level 25", "Binds when picked up", "Head  Leather", "+8 Agility"])
        self.assertIsNone(wowhead.icon_bytes("../etc/passwd"))

    def test_renamed_key_reported(self):
        raw = wowfio.extract(FX.joinpath("player_renamed_key.html").read_text(), "testy-mctest")
        problems = wowfio.check(raw)
        self.assertIn("missing trees", problems)
        self.assertIn("missing professions", problems)

    def test_no_anchor(self):
        with self.assertRaises(ParseError):
            wowfio.extract(FX.joinpath("player_no_anchor.html").read_text(), "testy-mctest")

    def test_no_chunks(self):
        with self.assertRaises(ParseError):
            wowfio.extract("<html>new layout</html>", "testy-mctest")


class TestHealth(Workspace):
    def test_transitions(self):
        core.record_health("a", [])
        self.assertEqual(core.failing(), {})
        core.record_health("a", ["missing items"])
        first = core.failing()["a"]["failing_since"]
        time.sleep(1.1)
        core.record_health("a", ["missing items"])
        self.assertEqual(core.failing()["a"]["failing_since"], first)
        core.record_health("a", [])
        self.assertEqual(core.failing(), {})


class TestGuard(unittest.TestCase):
    def test_refuses_repo(self):
        with self.assertRaises(SystemExit):
            core.guard(REPO / "notes" / "characters")


# ---------- 2. milestones ----------

class TestMilestones(Workspace):
    def test_travel_form(self):
        whats = [e["what"] for e in milestones.entries("Druid", 29, 31)]
        self.assertIn("Travel Form", whats)
        self.assertTrue(any("class trainer" in w and "30" in w for w in whats))

    def test_unknown_class(self):
        e = milestones.entries("Necromancer", 39, 40, with_generated=False)
        self.assertEqual([x["kind"] for x in e], ["mount"])

    def test_profession_wait(self):
        n = milestones.profession_nudges({"Leatherworking": "148/150"}, 19)
        self.assertFalse(n[0]["ready"])
        self.assertIn("needs level 20", n[0]["what"])
        n = milestones.profession_nudges({"Cooking": "130/150"}, 25)
        self.assertTrue(n[0]["ready"])

    def test_announce_once(self):
        core.char_dir("x")
        self.assertEqual(milestones.announce("x", snap(28, 2)), [])  # first run records only
        got = milestones.announce("x", snap(30, 0))
        self.assertTrue(any("Travel Form" in g for g in got))
        self.assertEqual(milestones.announce("x", snap(30, 0)), [])

    def test_diff_has_milestone(self):
        d = core.diff(snap(29, 1), snap(30, 0))
        self.assertTrue(any(x.startswith("milestone: Travel Form") for x in d))


# ---------- 3. party ----------

def run_cli(ws, *args):
    env = {**os.environ, "WOWCHAR_HOME": str(ws)}
    env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run([sys.executable, str(REPO / "scripts" / "wowchar.py"), *args], capture_output=True, text=True, env=env)


class TestParty(Workspace):
    def test_window(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import wowchar
        names = {i["slug"] for i in wowchar.instance_window([22, 25, 28], ["horde"])}
        self.assertIn("shadowfang-keep", names)
        self.assertIn("blackfathom-deeps", names)
        self.assertNotIn("wailing-caverns", names)
        self.assertNotIn("stormwind-stockade", names)  # Alliance city

    def test_watch_rules(self):
        self.add("me-one", [snap(24, 3, slug="me-one", name="Me One"), snap(26, 0, slug="me-one", name="Me One")])
        self.add("pal-two", [snap(20, 3, slug="pal-two", name="Pal Two"), snap(23, 0, slug="pal-two", name="Pal Two")], watch=True)
        r = run_cli(self.ws, "log", "pal-two", "did a thing")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("watched", r.stderr)
        r = run_cli(self.ws, "party")
        self.assertIn("★ | Me One", r.stdout)
        self.assertIn("Shared level window: 23–26", r.stdout)
        r = run_cli(self.ws, "party", "--since", (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"))
        self.assertIn("Pal Two (lvl 20 → 23)", r.stdout)

    def test_hook_lists_only_owned_for_logging(self):
        self.add("me-one", [snap(26, 0, slug="me-one", name="Me One")])
        self.add("pal-two", [snap(23, 0, slug="pal-two", name="Pal Two")], watch=True)
        import wowchar
        text = wowchar.hook_instructions(core.load_config())
        self.assertIn("is on for Me One (me-one)", text)
        self.assertIn("Watched friends (1): Pal Two", text)


# ---------- 4. instance briefings ----------

NOTE = """_Last updated: 2026-01-01_ · type: dungeon · levels: 20–30

## Before you go
- [quest] grab the quest

## Boss
- [dispel:curse] Nasty Curse
- [cc:humanoid] Humanoid adds
- [interrupt] Big Heal
- [loot:cloth,int] Caster Robe
- [loot:leather,agi] Agile Vest
"""

RAID = NOTE.replace("type: dungeon", "type: raid") + "- [resist:fire] fire everywhere\n"


class TestBrief(Workspace):
    def setUp(self):
        super().setUp()
        (self.ws / "notes" / "instances").mkdir(parents=True)
        (self.ws / "notes" / "instances" / "test-dungeon.md").write_text(NOTE)
        (self.ws / "notes" / "instances" / "test-raid.md").write_text(RAID)

    def brief(self, cls, level, inst="test-dungeon", ranks=None):
        import brief
        s = snap(level, 0, cls=cls)
        s["talents"] = {"Feral Combat": 15} if cls == "Druid" else {}
        s["talentRanks"] = {"Feral Combat": ranks or {}} if cls == "Druid" else {}
        if not core.find_char("testy-mctest"):
            self.add("testy-mctest", [s])
        else:
            (core.BASE / "testy-mctest" / "history.jsonl").write_text(json.dumps(s) + "\n")
        lines, code = brief.build(core.find_char("testy-mctest"), inst)
        return "\n".join(lines), code

    def test_curse_level_gate(self):
        out, _ = self.brief("Druid", 22)
        self.assertNotIn("→ you: Remove Curse", out)
        self.assertIn("you get Remove Curse at 24", out)
        out, _ = self.brief("Druid", 24)
        self.assertIn("Nasty Curse → you: Remove Curse", out)

    def test_cc_by_class(self):
        out, _ = self.brief("Mage", 30)
        self.assertIn("Humanoid adds → you: Polymorph", out)
        out, _ = self.brief("Priest", 30)
        self.assertNotIn("→ you: Polymorph", out)

    def test_talent_gate(self):
        out, _ = self.brief("Druid", 24, ranks={"feral_charge": 1})
        self.assertIn("Big Heal → you: Feral Charge", out)
        out, _ = self.brief("Druid", 24, ranks={})
        self.assertIn("Big Heal → you: Bash", out)

    def test_loot_filter(self):
        out, _ = self.brief("Druid", 24)
        self.assertIn("Agile Vest", out)
        self.assertNotIn("Caster Robe", out)

    def test_raid_sections(self):
        out, _ = self.brief("Druid", 24, inst="test-raid")
        self.assertIn("RAID", out)
        self.assertIn("fire (you have 4 from gear)", out)
        out, _ = self.brief("Druid", 24)
        self.assertNotIn("\nRAID", out)

    def test_missing_note(self):
        out, code = self.brief("Druid", 24, inst="gnomeregan")
        self.assertEqual(code, 2)
        self.assertIn("no notes yet", out)

    def test_freshness(self):
        import brief
        from datetime import date
        h, secs = brief.parse_note(NOTE + "\n## Sources\n- https://example.test (mechanics)\n")
        self.assertEqual(h["sources"], ["https://example.test (mechanics)"])
        self.assertNotIn("Sources", [t for t, _ in secs])
        self.assertEqual(brief.freshness(h, {}, secs, today=date(2026, 1, 10)), [])
        self.assertTrue(brief.freshness(h, {}, secs, today=date(2026, 3, 1))[0].startswith("STALE"))
        self.assertTrue(brief.freshness(h, {"verify": True}, secs, today=date(2026, 1, 20))[0].startswith("STALE"))
        h2, secs2 = brief.parse_note(NOTE + "\n## Empty Boss\n- (mechanics not recorded yet)\n")
        msgs = brief.freshness(h2, {}, secs2, today=date(2026, 1, 2))
        self.assertTrue(any(m.startswith("INCOMPLETE") and "Empty Boss" in m for m in msgs))
        self.assertTrue(any(m.startswith("UNSOURCED") for m in msgs))

    def test_shipped_notes_parse(self):
        import brief
        for p in (REPO / "data" / "instances" / "classic").glob("*.md"):
            header, sections = brief.parse_note(p.read_text())
            self.assertIn(header.get("type"), ("dungeon", "raid"), p.name)
            self.assertTrue(sections, p.name)


# ---------- 5. dashboard ----------

class TestDashboard(Workspace):
    def test_renders(self):
        import dashboard
        self.add("me-one", [snap(l, 6 - i, slug="me-one", name="Me One", quests=100 + i * 7) for i, l in enumerate([20, 21, 22, 24, 25])])
        self.add("pal-two", [snap(l, 6 - i, slug="pal-two", name="Pal Two") for i, l in enumerate([18, 19, 21, 22, 23])], watch=True)
        html = dashboard.render()
        self.assertIn('id="data"', html)
        self.assertIn("Me One", html)
        self.assertIn("Pal Two", html)
        self.assertIn("id='sec-level'", html)
        self.assertIn("class='elev'", html)
        friends = html[html.index("data-view='friends'"):html.index("data-view='standings'")]
        self.assertIn("Pal Two", friends)
        self.assertNotIn("Me One", friends)  # the friends page shows friends only

    def test_sparse(self):
        import dashboard
        self.add("me-one", [snap(20, 0, slug="me-one", name="Me One")])
        html = dashboard.render()
        self.assertIn("id='sec-board'", html)
        self.assertIn("No friends watched yet", html)
        self.assertIn("No journal yet", html)

    def test_refuses_repo_path(self):
        import dashboard
        with self.assertRaises(SystemExit):
            dashboard.write(REPO / "dash.html")


# ---------- 6. status line ----------

class TestStatusline(Workspace):
    def test_line(self):
        import statusline
        self.add("me-one", [snap(28, 2, slug="me-one", name="Me One"), snap(29, 0, slug="me-one", name="Me One")])
        line = statusline.render({"workspace": {"project_dir": str(self.ws)}})
        self.assertTrue(line.startswith("Me 29 Druid"), line)
        self.assertIn("next: Travel Form @30", line)
        self.assertIn("repair gear", line)  # synthetic chest is at 10/100

    def test_focus_session(self):
        import statusline
        self.add("me-one", [snap(28, 0, slug="me-one", name="Me One")])
        self.add("alt-two", [snap(20, 1, slug="alt-two", name="Alt Two", cls="Mage")])
        (core.BASE / ".focus.json").write_text(json.dumps({"slug": "alt-two", "session_id": "S1"}))
        ws = {"workspace": {"project_dir": str(self.ws)}}
        self.assertTrue(statusline.render({**ws, "session_id": "S1"}).startswith("Alt 20"))
        self.assertTrue(statusline.render({**ws, "session_id": "S2"}).startswith("Me 28"))

    def test_hook_focus_line(self):
        import wowchar
        self.add("me-one", [snap(28, 0, slug="me-one", name="Me One")])
        self.add("alt-two", [snap(20, 1, slug="alt-two", name="Alt Two", cls="Mage")])
        (core.BASE / ".focus.json").write_text(json.dumps({"slug": "alt-two", "session_id": "S1"}))
        chars = core.load_config()
        self.assertIn("Session focus: Alt Two", wowchar.hook_instructions(chars, "S1"))
        self.assertNotIn("Session focus", wowchar.hook_instructions(chars, "S2"))
        self.assertIn("--session S2", wowchar.hook_instructions(chars, "S2"))

    def test_empty_and_corrupt(self):
        import statusline
        empty = tempfile.TemporaryDirectory()
        self.assertEqual(statusline.render({"workspace": {"project_dir": empty.name}}), "")
        empty.cleanup()
        self.add("me-one", [snap(28, 0, slug="me-one", name="Me One")])
        (core.BASE / "me-one" / "history.jsonl").write_text("{not json\n")
        self.assertEqual(statusline.render({"workspace": {"project_dir": str(self.ws)}}), "")

    def test_cli_never_fails(self):
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "wowchar.py"), "statusline"], input="garbage",
                           capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(r.returncode, 0)

    def test_speed(self):
        import statusline
        hist = [snap(10 + i // 40, 1000 - i, slug="me-one", name="Me One") for i in range(1000)]
        self.add("me-one", hist)
        t = time.perf_counter()
        statusline.render({"workspace": {"project_dir": str(self.ws)}})
        self.assertLess(time.perf_counter() - t, 0.1)

    def test_install_keeps_keys(self):
        settings = self.ws / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"hooks": {"SessionStart": []}, "statusLine": {"type": "command", "command": "echo hi"}}))
        r = run_cli(self.ws, "install-statusline")
        self.assertEqual(r.returncode, 1)  # refuses to clobber a foreign status line
        r = run_cli(self.ws, "install-statusline", "--chain")
        s = json.loads(settings.read_text())
        self.assertIn("hooks", s)
        self.assertIn("--prefix-cmd 'echo hi'", s["statusLine"]["command"])


# ---------- 0. setup / profile / versions ----------

class TestSetup(Workspace):
    def test_status_and_profile(self):
        import wowchar
        st = wowchar.setup_status()
        self.assertEqual(st["characters"], [])
        self.assertEqual(st["profile"], "missing")
        p = {}
        k, v = core.parse_assignment("playstyle=relaxed,lore")
        core.set_path(p, k, v)
        k, v = core.parse_assignment("group.type=duo-trio")
        core.set_path(p, k, v)
        core.save_profile(p)
        prof = core.load_profile()
        self.assertEqual(prof["playstyle"], ["relaxed", "lore"])
        self.assertEqual(prof["group"]["type"], "duo-trio")
        self.assertIn("relaxed + lore", core.profile_line(prof))

    def test_unsupported_version(self):
        import sources
        with self.assertRaises(sources.Unsupported):
            sources.fetch({"slug": "x", "region": "us", "version": "retail"}, core.data("sources"))
        self.assertEqual(core.version_of({"slug": "x"}), "forever")

    def test_retail_add_saves_without_snapshot(self):
        r = run_cli(self.ws, "add", "Some Hero", "--version", "retail")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("isn't available for Retail yet", r.stdout)
        self.assertEqual(core.load_config()[0]["version"], "retail")
        r = run_cli(self.ws, "add", "Some Hero", "--version", "retail")
        self.assertIn("already tracked", r.stdout)


if __name__ == "__main__":
    unittest.main()


# ---------- gear sets by role ----------

class TestGearSets(Workspace):
    def test_item_tags(self):
        import gearsets
        self.assertEqual(gearsets.item_tag(["+8 Agility", "+10 Stamina"]), "phys")
        self.assertEqual(gearsets.item_tag(["+18 Spell Healing", "+6 Spirit"]), "heal")
        self.assertEqual(gearsets.item_tag(["+5 Intellect", "-3 Agility"]), "caster")
        self.assertIsNone(gearsets.item_tag(["+4 Stamina", "-3 Spirit"]))

    def test_two_sets_mapped_to_roles(self):
        import gearsets
        feral = snap(28, 2, gear={"Chest": "Cat Vest", "Back": "Old Cloak"})
        feral["stats"] = {"agility": 84, "strength": 64, "intellect": 50, "spirit": 70, "spell_power": 0}
        heal = snap(30, 0, gear={"Chest": "Heal Robe", "Back": "Cat Cloak"})
        heal["stats"] = {"agility": 53, "strength": 52, "intellect": 63, "spirit": 85, "spell_power": 37}
        self.add("testy-mctest", [feral, heal], roles=["heal", "tank", "dps"])
        gearsets.remember_items("testy-mctest", {"items": [
            {"slot": "Chest", "name": "Heal Robe", "ilvl": 28, "lines": ["+18 Spell Healing"]},
            {"slot": "Back", "name": "Cat Cloak", "ilvl": 32, "lines": ["+10 Attack Power"]}]})
        ss = gearsets.sets("testy-mctest")
        self.assertEqual([s["roles"] for s in ss], [["heal"], ["tank", "dps"]])
        self.assertTrue(ss[0]["current"])
        self.assertEqual(ss[1]["gear"]["Back"], "Cat Cloak")  # worn with the healer set, suits feral
        self.assertTrue(ss[1]["filled"]["Back"])
        self.assertEqual(ss[1]["gear"]["Chest"], "Cat Vest")

    def test_single_role_has_no_sets_section(self):
        import gearsets
        self.add("testy-mctest", [snap(20, 0, cls="Warlock")], roles=["dps"])
        self.assertEqual(gearsets.summary_lines("testy-mctest", core.find_char("testy-mctest")), [])


class TestDue(Workspace):
    def test_recap_and_plan_due_for_main(self):
        import wowchar
        self.add("testy-mctest", [snap(26, 4), snap(30, 0)], main=True)
        d = core.BASE / "testy-mctest"
        (d / "journal.md").write_text(f"<!-- recap: {(datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')} -->\n")
        (d / "plan.md").write_text(f"_Plan written {(datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')} at level 26._\n# x — plan (levels 26 → 30)\n")
        got = dict(wowchar.due(core.find_char("testy-mctest")))
        self.assertIn("wow-recap", got)
        self.assertIn("wow-plan", got)
        self.assertIn("run these yourself", wowchar.due_report({}))
        self.assertEqual(wowchar.due_report({"autoSkills": "off"}), "")

    def test_idle_alt_is_skipped(self):
        import wowchar
        self.add("testy-mctest", [snap(28, 5), snap(28, 0)])
        self.assertEqual(wowchar.due_report({}), "")


class TestRealmFilter(Workspace):
    def test_realm_keys(self):
        self.assertEqual([core.realm_key(x) for x in ("PvP", "PvE", "RP", "RP-PvP", "Normal", None)],
                         ["pvp", "pve", "rp", "rppvp", "pve", None])
        self.assertEqual([core.realm_label(x) for x in ("Normal", "pvp", "Hardcore", None)], ["PvE", "PvP", "Hardcore", None])
        self.assertEqual(core.realm_filter("pvp, RP-PvP"), {"pvp", "rppvp"})
        with self.assertRaises(SystemExit):
            core.realm_filter("pvx")
