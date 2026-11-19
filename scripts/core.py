"""Shared paths, config, profile, snapshots and helpers for wow-waypoint. Stdlib only.

Personal data lives in the *workspace* (never in this repo):
  <workspace>/notes/characters/   characters.json, <slug>/..., .health.json, .last_session
  <workspace>/notes/profile.json  player profile written by /wow-init
  <workspace>/notes/instances/    personal instance notes (override the repo's data/instances/)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SCRIPT = KIT / "scripts" / "wowchar.py"
DATA = KIT / "data"
THROTTLE_HOURS = 20
SLOTS = ["Head", "Neck", "Shoulders", "Back", "Chest", "Wrist", "Hands", "Waist", "Legs", "Feet",
         "Ring 1", "Ring 2", "Trinket 1", "Trinket 2", "Main Hand", "Off Hand", "Ranged"]
COSMETIC = {"Shirt", "Tabard"}  # never ranked as weak gear
QUALITY = {0: "poor", 1: "common", 2: "uncommon", 3: "rare", 4: "epic", 5: "legendary"}
LIST_FIELDS = {"playstyle", "goals", "addons", "roles"}

ROOT = BASE = CONFIG = None
SOURCE = None  # how ROOT was found: env, local, home, project or cwd
ANNOUNCE = ("everywhere", "home")  # where the session hook speaks up; "home" (notes folder only) is the default


def pointer_path():
    """Per-user file that remembers the notes folder, so Claude Code can start in any folder."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base).expanduser() / "wow-waypoint" / "config.json"


def read_pointer():
    try:
        d = json.loads(pointer_path().read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def write_pointer(**fields):
    d = {**read_pointer(), **{k: v for k, v in fields.items() if v is not None}}
    p = pointer_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2) + "\n")
    return d


def has_notes(d):
    return (d / "notes" / "characters" / "characters.json").exists()


def find_workspace(start=None, use_env=True, explain=False):
    """WOWCHAR_HOME, else a folder (or parent) that already has notes, else the remembered home, else the project folder."""
    def found(path, how):
        return (Path(path).expanduser().resolve(), how) if explain else Path(path).expanduser().resolve()
    if use_env and os.environ.get("WOWCHAR_HOME"):
        return found(os.environ["WOWCHAR_HOME"], "env")
    starts = [Path(start or Path.cwd()).resolve()]
    if use_env and os.environ.get("CLAUDE_PROJECT_DIR"):
        starts.insert(0, Path(os.environ["CLAUDE_PROJECT_DIR"]).expanduser().resolve())
    for s in starts:
        for d in (s, *s.parents):
            if has_notes(d):
                return found(d, "local")
    home = read_pointer().get("home")
    if home and Path(home).expanduser().is_dir():
        return found(home, "home")
    return found(starts[0], "project" if use_env and os.environ.get("CLAUDE_PROJECT_DIR") else "cwd")


def session_in_home():
    """True when this session was started inside the notes folder."""
    here = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    return here == ROOT or ROOT in here.parents


def announce_mode():
    """Where the session hook speaks up: 'home' (default, notes folder only) unless the user chose 'everywhere'."""
    m = read_pointer().get("announce")
    return m if m in ANNOUNCE else "home"


def opted_in_sessions():
    d = read_json(BASE / ".sessions.json", None) if BASE else None
    return d if isinstance(d, list) else []


def session_opted_in(session_id):
    """True when the user turned WoW on for this one session outside the notes folder (`session on`)."""
    return bool(session_id) and session_id in opted_in_sessions()


def set_root(path):
    global ROOT, BASE, CONFIG
    ROOT = Path(path).resolve()
    BASE = ROOT / "notes" / "characters"
    CONFIG = BASE / "characters.json"


ROOT_PATH, SOURCE = find_workspace(explain=True)
set_root(ROOT_PATH)


def now():
    return datetime.now(timezone.utc)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def slugify(name):
    return re.sub(r"\s+", "-", name.strip().lower())


def guard(path=None):
    """Never write personal data inside the tracker repo itself."""
    p = Path(path or BASE).resolve()
    if p == KIT or KIT in p.parents:
        raise SystemExit(f"refusing to store personal data inside the tracker repo ({KIT}). "
                         "Run from your own workspace folder or set WOWCHAR_HOME.")


def write_text(path, text):
    guard(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


# ---------- shared reference data (repo data/) ----------

_data = {}


def data(name):
    if name not in _data:
        _data[name] = read_json(DATA / f"{name}.json", {})
    return _data[name]


def version_of(char):
    return char.get("version") or "forever"


def version_info(char_or_version):
    v = char_or_version if isinstance(char_or_version, str) else version_of(char_or_version)
    return data("sources").get("versions", {}).get(v, {"label": v, "ruleset": "classic", "source": None})


def ruleset(char_or_version):
    return version_info(char_or_version).get("ruleset", "classic")


def rules(name, char_or_version):
    """The part of data/<name>.json for this character's ruleset ({} if none)."""
    return data(name).get(ruleset(char_or_version), {})


# ---------- config ----------

def load_config():
    return read_json(CONFIG, []) if CONFIG.exists() else []


def save_config(chars):
    write_text(CONFIG, json.dumps(chars, indent=2) + "\n")


def owned(chars=None):
    return [c for c in (load_config() if chars is None else chars) if not c.get("watch")]


def primary(chars=None):
    """The owned character flagged main=true (set with `wowchar main <char>`), or None."""
    return next((c for c in owned(chars) if c.get("main")), None)


def watched(chars=None):
    return [c for c in (load_config() if chars is None else chars) if c.get("watch")]


def find_char(key, chars=None):
    chars = load_config() if chars is None else chars
    k = key.strip().lower()
    for test in (lambda c: c["slug"] == k, lambda c: c["name"].lower() == k,
                 lambda c: c["name"].lower().split()[0] == k, lambda c: c["slug"].startswith(k)):
        hits = [c for c in chars if test(c)]
        if len(hits) == 1:
            return hits[0]
    return None


def char_dir(slug):
    d = BASE / slug
    guard(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------- profile ----------

def profile_path():
    return ROOT / "notes" / "profile.json"


def load_profile():
    return read_json(profile_path(), None)


def save_profile(p):
    p["updated"] = datetime.now().strftime("%Y-%m-%d")
    write_text(profile_path(), json.dumps(p, indent=2) + "\n")
    write_text(ROOT / "notes" / "profile.md", profile_md(p))


def parse_assignment(kv):
    if "=" not in kv:
        raise SystemExit(f"expected key=value, got {kv!r}")
    k, v = kv.split("=", 1)
    k, v = k.strip(), v.strip()
    leaf = k.split(".")[-1]
    if leaf in LIST_FIELDS:
        return k, [x.strip() for x in v.split(",") if x.strip()]
    if v.lower() in ("true", "false"):
        return k, v.lower() == "true"
    if v.lower() in ("", "null", "none", "skip"):
        return k, None
    return k, v


def set_path(obj, dotted, value):
    keys = dotted.split(".")
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    obj[keys[-1]] = value


def profile_line(p):
    if not p:
        return ""
    bits = [version_info(p.get("version") or "forever").get("label", p.get("version"))]
    if p.get("realmType"):
        bits.append(f"{p['realmType']} realm")
    if p.get("playstyle"):
        bits.append(" + ".join(p["playstyle"]))
    if p.get("hoursPerWeek"):
        bits.append(f"~{p['hoursPerWeek']}h/week")
    if p.get("answerStyle"):
        bits.append(f"{p['answerStyle']} answers")
    if p.get("spoilers") == "avoid":
        bits.append("avoid spoilers for new content")
    if p.get("recapVoice") and p["recapVoice"] != "light":
        bits.append(f"recap voice: {p['recapVoice']}")
    if p.get("goals"):
        bits.append("goals: " + ", ".join(p["goals"]))
    return "Player profile: " + "; ".join(b for b in bits if b) + ". Respect it in plans, recaps and briefings."


def profile_md(p):
    L = [f"_Written by wow-waypoint from notes/profile.json ({p.get('updated', '')}). Edit with `wowchar.py profile set key=value` or re-run /wow-init._", "", "# Player profile", ""]
    for k, v in p.items():
        if k == "updated":
            continue
        if isinstance(v, dict):
            v = ", ".join(f"{a}: {b}" for a, b in v.items() if b)
        elif isinstance(v, list):
            v = ", ".join(v)
        L.append(f"- **{k}**: {v if v not in (None, '') else '(skipped)'}")
    return "\n".join(L) + "\n"


# ---------- snapshots ----------

REALM_TYPES = {"pvp": "PvP", "pve": "PvE", "rp": "RP", "rppvp": "RP-PvP"}


def realm_key(s):
    """'PvP', 'RP-PvP', 'Normal'… -> pvp / pve / rp / rppvp (None if unknown)."""
    k = re.sub(r"[^a-z]", "", (s or "").lower())
    return {"normal": "pve", "roleplaying": "rp", "roleplayingpvp": "rppvp", "rpppvp": "rppvp"}.get(k, k) or None


def realm_label(s):
    """Display name for a realm type: 'Normal' -> 'PvE', 'pvp' -> 'PvP'; unknown values pass through."""
    return REALM_TYPES.get(realm_key(s), s) if s else s


def realm_filter(arg):
    """'pvp,rp' -> {'pvp','rp'}; exits on an unknown type."""
    keys = {realm_key(x) for x in (arg or "").split(",") if x.strip()}
    bad = keys - set(REALM_TYPES)
    if bad:
        sys.exit(f"unknown realm type {', '.join(sorted(bad))}; use {', '.join(REALM_TYPES)}")
    return keys


def history(slug, tail=None):
    p = BASE / slug / "history.jsonl"
    if not p.exists():
        return []
    if tail:
        with p.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - tail))
            lines = f.read().decode("utf-8", "replace").splitlines()
        if size > tail:
            lines = lines[1:]
    else:
        lines = p.read_text().splitlines()
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def latest(slug):
    """Normalized latest snapshot. Converts legacy raw wowf.io files on the fly."""
    raw = read_json(BASE / slug / "latest.json")
    if raw is None:
        return None
    if raw.get("items") and "slotName" in raw["items"][0]:
        from sources import wowfio
        return wowfio.normalize(raw)
    if raw.get("realmType"):
        raw["realmType"] = realm_label(raw["realmType"])
    return raw


def item_info(i):
    lines = i.get("lines", [])
    req = next((int(m.group(1)) for l in lines if (m := re.match(r"Requires Level (\d+)", l))), None)
    stats = [l for l in lines if re.match(r"^[+-]\d+ |^Equip:|^Use:|^\d+ Armor$|^Chance on hit", l)]
    ench = next((l.split(": ", 1)[1] for l in lines if l.startswith("Enchanted:")), None)
    dur = next((l.split(" ", 1)[1] for l in lines if l.startswith("Durability")), None)
    return {"name": i["name"], "ilvl": i.get("ilvl"), "quality": QUALITY.get(i.get("quality"), "?"),
            "id": i.get("id"), "icon": i.get("icon"),
            "req": req, "stats": stats, "enchant": ench, "durability": dur, "lines": lines}


def low_durability(info, frac=0.35):
    try:
        a, b = (int(x) for x in info["durability"].split(" / "))
        return a < frac * b
    except (AttributeError, ValueError, TypeError):
        return False


def gear(slug):
    n = latest(slug) or {}
    return {i["slot"]: item_info(i) for i in n.get("items", []) if i.get("slot") not in COSMETIC}


def resistances(items):
    out = {}
    for info in items.values():
        for l in info["lines"]:
            if m := re.match(r"^\+(\d+) (Fire|Frost|Nature|Shadow|Arcane) Resistance", l):
                out[m.group(2).lower()] = out.get(m.group(2).lower(), 0) + int(m.group(1))
    return out


def compact(n):
    v = n.get("stats") or {}
    return {
        "at": now().isoformat(timespec="seconds"),
        "slug": n["slug"], "name": n["name"], "race": n.get("race"), "class": n.get("class"),
        "faction": n.get("faction"), "level": n["level"], "itemLevel": n.get("itemLevel"),
        "lastLogin": n.get("lastLogin"), "quests": n.get("quests"),
        "talents": {t["name"]: t["points"] for t in n.get("trees", [])},
        "talentRanks": {t["name"]: t.get("ranks", {}) for t in n.get("trees", []) if t.get("points")},
        "professions": {p["name"]: f'{p["skill"]}/{p["max"]}' for p in n.get("professions", [])},
        "gear": {i["slot"]: i["name"] for i in n.get("items", []) if i.get("slot") not in COSMETIC},
        "gearIlvl": {i["slot"]: i.get("ilvl") for i in n.get("items", []) if i.get("slot") not in COSMETIC},
        "reps": {r["name"]: r["standing"] for r in n.get("reps", [])},
        "stats": {k: round(v[k], 2) if isinstance(v.get(k), float) else v.get(k)
                  for k in ("health", "power", "strength", "agility", "stamina", "intellect", "spirit",
                            "armor", "attack_power", "spell_power", "melee_crit", "dodge") if v.get(k) is not None},
        "kills": n.get("kills"),
        "achievements": [a["name"] if isinstance(a, dict) else a for a in n.get("achievements", [])],
        "mounts": n.get("mounts", []),
    }


def talent_ranks(snap):
    out = {}
    for ranks in (snap.get("talentRanks") or {}).values():
        out.update(ranks)
    return out


def diff(old, new, with_milestones=True):
    out = []
    for k in ("level", "itemLevel", "quests", "kills"):
        if old.get(k) != new.get(k):
            out.append(f"{k} {old.get(k)} → {new.get(k)}")
    for group in ("professions", "talents", "reps"):
        o, n = old.get(group, {}), new.get(group, {})
        for name in sorted(set(o) | set(n)):
            if o.get(name) != n.get(name):
                out.append(f"{name} {o.get(name, '—')} → {n.get(name, '—')}")
    o, n = old.get("gear", {}), new.get("gear", {})
    for slot in [s for s in SLOTS if s in o or s in n]:
        if o.get(slot) != n.get(slot):
            out.append(f"{slot}: {o.get(slot, 'empty')} → {n.get(slot, 'empty')}")
    for a in new.get("achievements", []) if "achievements" in old else []:
        if a not in old["achievements"]:
            out.append(f"achievement: {a}")
    for m in new.get("mounts", []) if "mounts" in old else []:
        if m not in old["mounts"]:
            out.append(f"mount: {m}")
    if with_milestones and isinstance(old.get("level"), int) and isinstance(new.get("level"), int) and new["level"] > old["level"]:
        import milestones
        out += [f"milestone: {e['what']} (lvl {e['level']})" for e in milestones.entries(new.get("class"), old["level"], new["level"], with_generated=False)]
    return out


def dedupe(snaps):
    """Drop consecutive snapshots that changed nothing (forced refreshes)."""
    out = [s for i, s in enumerate(snaps) if i == 0 or diff(snaps[i - 1], s, with_milestones=False)]
    if snaps and out[-1] is not snaps[-1]:
        out.append(snaps[-1])  # keep the newest point so lines reach "now"
    return out


def pace(snaps, days=7):
    """Levels and quests per day over the last `days` days of snapshots."""
    if len(snaps) < 2:
        return None
    end = snaps[-1]
    t_end = parse_time(end["at"])
    start = next((s for s in snaps if (t_end - parse_time(s["at"])).days <= days), snaps[0])
    span = (t_end - parse_time(start["at"])).total_seconds() / 86400
    if span < 0.5:
        return None
    return {"days": round(span, 1), "levels_per_day": round((end["level"] - start["level"]) / span, 2),
            "quests_per_day": round(((end.get("quests") or 0) - (start.get("quests") or 0)) / span, 1)}


def eta_days(snaps, levels, min_days=3):
    p = pace(snaps, days=14)
    if not p or p["days"] < min_days or p["levels_per_day"] <= 0:
        return None
    return max(1, round(levels / p["levels_per_day"]))


def spec(snap, version="forever"):
    """(class, spec key) from the tree with most points; spec None below 10."""
    cls = snap.get("class")
    trees = snap.get("talents") or {}
    if not trees or max(trees.values() or [0]) == 0:
        return cls, None
    top = max(trees, key=trees.get)
    return cls, rules("spec-stats", version).get("specs", {}).get(cls, {}).get(top, slugify(top))


# ---------- activity log ----------

def activity(slug):
    a = BASE / slug / "activity.md"
    return [l for l in a.read_text().splitlines() if re.match(r"- \d{4}-\d{2}-\d{2}", l)] if a.exists() else []


def open_questions(slug):
    return [l for l in activity(slug) if re.match(r"- \S+ \S+ \?", l)]


def last_recap(slug):
    j = BASE / slug / "journal.md"
    dates = re.findall(r"<!-- recap: (\d{4}-\d{2}-\d{2})", j.read_text()) if j.exists() else []
    return max(dates) if dates else "0000-00-00"


# ---------- parse health ----------

def health_path():
    return BASE / ".health.json"


def record_health(slug, problems):
    h = read_json(health_path(), {}) or {}
    cur = h.get(slug, {})
    t = now().isoformat(timespec="seconds")
    if problems:
        cur = {"last_ok": cur.get("last_ok"), "failing_since": cur.get("failing_since") or t, "problems": problems}
    else:
        cur = {"last_ok": t, "failing_since": None, "problems": []}
    h[slug] = cur
    write_text(health_path(), json.dumps(h, indent=1) + "\n")
    return cur


def failing():
    return {s: v for s, v in (read_json(health_path(), {}) or {}).items() if v.get("failing_since")}
