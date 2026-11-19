"""Gear sets by role. The armory only shows what was worn at logout, so each snapshot records one set.

Each snapshot is classed as a physical, healer or caster set (from item stat lines when we have them,
else from character stats). The newest snapshot of each kind is that kind's set, mapped to the
character's roles: physical -> tank/dps, healer -> heal, caster -> dps.
"""
import re

import core

HEAL = re.compile(r"Spell Healing|Healing Spells|Increases healing done", re.I)  # healing-only, not "damage and healing"
CASTER = re.compile(r"Intellect|Spirit|Spell Damage|Spell Power|mana per 5|Healing", re.I)
PHYS = re.compile(r"Agility|Strength|Attack Power|Defense|Dodge|Parry|Block", re.I)
HEALERS = {"Druid", "Priest", "Paladin", "Shaman"}
ROLE_NAME = {"tank": "Tank", "heal": "Healer", "dps": "DPS"}


def _positive(lines):
    return [l for l in lines if re.match(r"^\+\d|^Equip:", l)]


def item_tag(lines):
    """'heal', 'caster', 'phys' or None (neutral, e.g. Stamina only)."""
    pos = _positive(lines or [])
    phys = sum(bool(PHYS.search(l)) for l in pos)
    cast = sum(bool(CASTER.search(l)) for l in pos)
    if phys > cast:
        return "phys"
    if cast and cast >= phys:
        return "heal" if any(HEAL.search(l) for l in pos) else "caster"
    return None


def snapshot_kind(snap, lines_by_slot=None):
    if lines_by_slot:
        tags = [item_tag(l) for l in lines_by_slot.values()]
        phys, heal, cast = tags.count("phys"), tags.count("heal"), tags.count("caster")
        if phys or heal or cast:
            if phys > heal + cast:
                return "phys"
            return "heal" if heal else "caster"
    s = snap.get("stats") or {}
    if not s:
        return None
    caster = (s.get("intellect") or 0) + (s.get("spirit") or 0)
    phys = (s.get("agility") or 0) + (s.get("strength") or 0)
    return "caster" if (s.get("spell_power") or 0) > 0 and caster > phys else "phys"


def roles_for(kind, char, cls):
    roles = char.get("roles") or []
    if kind == "phys":
        return [r for r in roles if r in ("tank", "dps")] or ["dps"]
    if kind == "heal":
        return ["heal"] if cls in HEALERS else ["dps"]
    # caster gear without a healing line: a healer class that heals counts it as its healer set
    return ["heal"] if "heal" in roles and cls in HEALERS else ["dps"]


def label(s, cls):
    name = " + ".join(ROLE_NAME.get(r, r) for r in s["roles"]) + " set"
    if cls == "Druid":
        name += {"phys": " (feral)", "caster": " (caster)"}.get(s["kind"], "") if s["roles"] != ["heal"] else ""
    return name


def item_cache(slug):
    return core.read_json(core.BASE / slug / "items.json", {}) or {}


def remember_items(slug, norm):
    """Keep stat lines for every item ever seen, so older sets still show stats."""
    cache = item_cache(slug)
    for i in norm.get("items", []):
        if i.get("slot") in core.COSMETIC or not i.get("name"):
            continue
        cache[i["name"]] = {k: i.get(k) for k in ("name", "ilvl", "quality", "id", "icon", "lines")}
    core.write_text(core.BASE / slug / "items.json", core.json.dumps(cache, indent=1))


def item_record(slug, name, slot, ilvl=None, cache=None):
    """Raw item dict (as in latest.json) for a name, from the cache; a bare stub if never seen with stats."""
    rec = dict((cache if cache is not None else item_cache(slug)).get(name) or {"name": name, "ilvl": ilvl, "lines": []})
    rec["slot"] = slot
    rec.setdefault("ilvl", ilvl)
    return rec


def sets(slug, char=None):
    """Newest worn set per role group, current first. Each: kind, roles, at, level, gear, ilvl, current, filled."""
    char = char or core.find_char(slug) or {}
    snaps = core.history(slug)
    if not snaps:
        return []
    latest = core.latest(slug) or {}
    cache = item_cache(slug)
    for i in latest.get("items", []):
        cache.setdefault(i["name"], {k: i.get(k) for k in ("name", "ilvl", "quality", "id", "icon", "lines")})
    cls = snaps[-1].get("class")
    best = {}
    for n, s in enumerate(snaps):
        lines = {slot: cache[name]["lines"] for slot, name in (s.get("gear") or {}).items() if name in cache and cache[name].get("lines")}
        kind = snapshot_kind(s, lines if len(lines) >= len(s.get("gear") or {}) // 2 else None)
        if not kind:
            continue
        roles = roles_for(kind, char, cls)
        key = "/".join(roles)
        best[key] = {"kind": kind, "roles": roles, "at": s["at"], "level": s.get("level"),
                     "gear": dict(s.get("gear") or {}), "ilvl": dict(s.get("gearIlvl") or {}),
                     "current": n == len(snaps) - 1, "filled": {}}
    out = sorted(best.values(), key=lambda x: (not x["current"], x["at"]), reverse=False)
    cur = next((x for x in out if x["current"]), None)
    if cur:
        # pieces worn now that suit an older set (e.g. a feral cloak kept on while healing) are its newer picks
        for old in out:
            if old is cur:
                continue
            for slot, name in cur["gear"].items():
                tag = item_tag((cache.get(name) or {}).get("lines"))
                fits = tag == old["kind"] or (old["kind"] in ("heal", "caster") and tag in ("heal", "caster"))
                if fits and old["gear"].get(slot) != name:
                    old["gear"][slot] = name
                    old["ilvl"][slot] = cur["ilvl"].get(slot)
                    old["filled"][slot] = True
    for s in out:
        s["items"] = {slot: item_record(slug, name, slot, s["ilvl"].get(slot), cache) for slot, name in s["gear"].items()}
        s["stats"] = {slot: core.item_info(rec)["stats"] for slot, rec in s["items"].items()}
        s["label"] = label(s, cls)
    return out


def wants_sets(char, cls):
    roles = char.get("roles") or []
    return len(roles) > 1 and not (set(roles) <= {"dps"})


def summary_lines(slug, char):
    cur_snap = (core.history(slug, tail=8000) or [{}])[-1]
    cls = cur_snap.get("class")
    if not wants_sets(char, cls):
        return []
    ss = sets(slug, char)
    if not ss:
        return []
    L = ["", "## Gear sets by role",
         "_Each logout records the set you're wearing. Shared items appear in every set. "
         "\"newer\" = a piece you wore with another set that suits this one._"]
    shared = set.intersection(*(set(s["gear"].items()) for s in ss)) if len(ss) > 1 else set()
    for s in ss:
        when = f"worn now ({s['at'][:10]}, level {s['level']})" if s["current"] else f"last worn {s['at'][:10]}, level {s['level']}"
        L += ["", f"### {s['label']}: {when}", "| Slot | Item | iLvl | Stats | |", "|---|---|---|---|---|"]
        for slot in [x for x in core.SLOTS if x in s["gear"]]:
            name = s["gear"][slot]
            note = "shared" if (slot, name) in shared else ("newer" if s["filled"].get(slot) else "")
            L.append(f"| {slot} | {name} | {s['ilvl'].get(slot) or ''} | {', '.join(s['stats'].get(slot) or [])} | {note} |")
    missing = [r for r in (char.get("roles") or []) if not any(r in s["roles"] for s in ss)]
    if missing:
        L += ["", f"- No set seen yet for: {', '.join(ROLE_NAME.get(r, r) for r in missing)}. Log out wearing it once to record it."]
    old = [s for s in ss if not s["current"]]
    if old:
        L.append("- Older sets only refresh when you log out in them; upgrades since then may be missing.")
    return L
