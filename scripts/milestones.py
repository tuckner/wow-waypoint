"""Level-up milestones and profession tier nudges (data/milestones.json)."""
import json

import core


def _rules(version="forever"):
    return core.rules("milestones", version)


def entries(cls, lo, hi, version="forever", with_generated=True):
    """Milestones with lo < level <= hi for this class (plus 'all'), sorted by level."""
    r = _rules(version)
    listed = [dict(e) for e in r.get("all", []) + r.get(cls or "", [])]
    out = [e for e in listed if lo < e["level"] <= hi]
    if with_generated and hi > lo:
        even = [l for l in range(lo + 1, hi + 1) if l % 2 == 0]
        if even:
            out.append({"level": even[0], "what": f"New spell ranks at your class trainer (level {', '.join(map(str, even))})", "kind": "training", "generated": True})
        pts = len([l for l in range(lo + 1, hi + 1) if l >= 10])
        if pts:
            out.append({"level": max(lo + 1, 10), "what": f"+{pts} talent point{'s' if pts > 1 else ''} to spend", "kind": "talent", "generated": True})
    return sorted(out, key=lambda e: (e["level"], e.get("generated", False)))


def upcoming(cls, level, n=2, version="forever"):
    return entries(cls, level, level + n, version)


def next_listed(cls, level, within=6, version="forever"):
    """The next hand-listed (not generated) milestone, for the status line."""
    e = entries(cls, level, level + within, version, with_generated=False)
    return e[0] if e else None


def _prof_pairs(professions):
    if isinstance(professions, dict):  # compact snapshot: {"Cooking": "130/150"}
        for name, s in professions.items():
            try:
                skill, mx = (int(x) for x in s.split("/"))
            except ValueError:
                continue
            yield name, skill, mx
    else:
        for p in professions or []:
            if p.get("skill") is not None and p.get("max") is not None:
                yield p["name"], p["skill"], p["max"]


def profession_nudges(professions, level, version="forever"):
    r = _rules(version)
    tiers = r.get("professionTiers", [])
    notes = r.get("professionNotes", {})
    out = []
    for name, skill, mx in _prof_pairs(professions):
        nxt = next((t for t in tiers if t["max"] > mx), None)
        if not nxt or skill < nxt["skill"]:
            continue
        how = notes.get(name, {}).get(nxt["tier"], "your profession trainer")
        if level >= nxt["level"]:
            out.append({"key": f"{name}:{nxt['tier']}", "ready": True,
                        "what": f"{name} {skill}/{mx}: learn {nxt['tier']} ({nxt['max']}) now ({how})"})
        else:
            out.append({"key": f"{name}:{nxt['tier']}:wait", "ready": False,
                        "what": f"{name} {skill}/{mx}: {nxt['tier']} needs level {nxt['level']} (you're {level}); skill is capped until then"})
    return out


# ---------- once-only announcements for the SessionStart hook ----------

def _state_path(slug):
    return core.BASE / slug / ".announced.json"


def announce(slug, snap, version="forever"):
    """Milestones crossed and new profession nudges since the last announcement. Marks them announced.
    First run only records the current level (no dump of past milestones)."""
    path = _state_path(slug)
    state = core.read_json(path, None)
    level = snap.get("level")
    out = []
    if state is None:
        state = {"level": level, "nudges": [n["key"] for n in profession_nudges(snap.get("professions"), level, version)]}
    else:
        if isinstance(level, int) and level > state.get("level", level):
            out += [e["what"] + f" (lvl {e['level']})" for e in entries(snap.get("class"), state["level"], level, version)]
            state["level"] = level
        for n in profession_nudges(snap.get("professions"), level, version):
            if n["key"] not in state.setdefault("nudges", []):
                out.append(n["what"])
                state["nudges"].append(n["key"])
    core.write_text(path, json.dumps(state, indent=1) + "\n")
    return out
