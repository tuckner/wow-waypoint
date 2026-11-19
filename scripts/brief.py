"""/wow-waypoint:instance briefings: tagged instance notes x class ability matrix -> what *you* do.

Note format: see data/instances/FORMAT.md. Exit code 2 from cmd_brief = no notes yet.
"""
import re

import core

TAG_RE = re.compile(r"^\s*-\s*((?:\[[^\]]+\])+)\s*(.*)$")
ROLE_TAGS = {"tank", "heal", "dps"}
PREP_TAGS = {"quest", "key", "bring", "attune"}
ARMOR = {"cloth", "leather", "mail", "plate"}
GENERIC_SLOTS = {"cloak", "back", "ring", "neck", "trinket", "offhand", "relic", "any"}


def find_instance(name, version="forever"):
    k = name.strip().lower()
    for inst in core.rules("instances", version):
        if k in (inst["slug"], inst["name"].lower(), *inst.get("aliases", [])):
            return inst
    for inst in core.rules("instances", version):  # loose: prefix match on slug or name
        if inst["slug"].startswith(core.slugify(k)) or inst["name"].lower().startswith(k):
            return inst
    return None


def note_path(slug, version="forever"):
    personal = core.ROOT / "notes" / "instances" / f"{slug}.md"
    shipped = core.DATA / "instances" / core.ruleset(version) / f"{slug}.md"
    return next((p for p in (personal, shipped) if p.exists()), None)


def parse_note(text):
    """-> header dict, sections [(title, [(tags, text)])]."""
    header, sections, cur = {}, [], None
    for line in text.splitlines():
        if line.startswith("_") and not sections and "·" in line:
            for part in line.strip("_ ").split("·"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    header[k.strip().lower()] = v.strip().strip("_")
        elif line.startswith("## "):
            title = line[3:].strip()
            if title.lower() == "sources":
                cur = None
                header["sources"] = []
                continue
            cur = (title, [])
            sections.append(cur)
        elif "sources" in header and cur is None and line.lstrip().startswith("-"):
            header["sources"].append(line.lstrip()[1:].strip())
        elif cur is not None and line.lstrip().startswith("-"):
            m = TAG_RE.match(line)
            if m:
                tags = re.findall(r"\[([^\]]+)\]", m.group(1))
                cur[1].append((tags, m.group(2).strip()))
            else:
                cur[1].append(([], line.lstrip()[1:].strip()))
    return header, sections


STALE_DAYS, STALE_DAYS_NEW = 30, 14


def freshness(header, inst, sections, today=None):
    """Warnings that tell the skill to refresh the note per data/instances/RESEARCH.md."""
    from datetime import date
    out = []
    limit = STALE_DAYS_NEW if (inst or {}).get("verify") else STALE_DAYS
    try:
        age = ((today or date.today()) - date.fromisoformat(header.get("last updated", "")[:10])).days
        if age > limit:
            out.append(f"STALE: notes are {age} days old (limit {limit}); refresh version changes and loot per RESEARCH.md")
    except ValueError:
        out.append("STALE: no 'Last updated' date in the header; refresh per RESEARCH.md")
    empty = [t for t, items in sections if any("not recorded yet" in x[1] for x in items)]
    if empty:
        out.append("INCOMPLETE: no mechanics recorded for " + ", ".join(empty) + "; research them per RESEARCH.md before briefing")
    if not header.get("sources"):
        out.append("UNSOURCED: no ## Sources section; add sources when you next refresh this note")
    return out


def usable(abilities, level, ranks, role=None):
    """First ability in the list the character has (trained at this level, has the talent, matching role)."""
    for a in abilities or []:
        if a.get("level", 1) > level:
            continue
        if a.get("talent") and not ranks.get(a["talent"]):
            continue
        if a.get("role") and role and a["role"] != role:
            continue
        return a
    return None


def not_yet(abilities, level):
    later = [a for a in abilities or [] if a.get("level", 1) > level and not a.get("talent")]
    return min(later, key=lambda a: a["level"]) if later else None


def loot_ok(tag, cls, spec_key, version):
    """tag like 'loot:leather,agi,str'. True if wearable and stats fit the spec (or no stats given)."""
    parts = [p.strip().lower() for p in tag.split(":", 1)[1].split(",") if p.strip()]
    if not parts:
        return True
    r = core.rules("spec-stats", version)
    kind, stats = parts[0], set(parts[1:])
    if kind in ARMOR and kind not in r.get("armor", {}).get(cls, ARMOR):
        return False
    if kind not in ARMOR and kind not in GENERIC_SLOTS and kind not in r.get("weapons", {}).get(cls, [kind]):
        return False
    wants = r.get("wants", {})
    w = wants.get(spec_key or "") or wants.get(r.get("classKind", {}).get(cls, ""), {})
    if not stats or not w:
        return True
    return bool(stats & set(w.get("want", []))) and not (stats & set(w.get("avoid", [])))


def default_roles(cls, spec_key, version):
    r = core.rules("spec-stats", version).get("roles", {}).get(cls, {})
    return r.get(spec_key or "_") or r.get("_") or ["dps"]


def consumables(snap, wants, version):
    level = snap.get("level") or 0
    skills = {}
    for name, s in (snap.get("professions") or {}).items():
        try:
            skills[name] = int(s.split("/")[0])
        except ValueError:
            pass
    out = []
    for c in core.rules("consumables", version) or []:
        if skills.get(c["profession"], -1) >= c["skill"] and c["from"] <= level + 2 and level <= c["to"]:
            if "any" in c["for"] or set(c["for"]) & set(wants):
                out.append(f"{c['name']} ({c['profession']}, if you know the recipe)")
    return out


def build(char, inst_key, role=None):
    """Returns (lines, exit_code)."""
    version = core.version_of(char)
    snaps = core.history(char["slug"])
    if not snaps:
        return [f"no snapshot for {char['slug']}; run update first"], 1
    snap = snaps[-1]
    inst = find_instance(inst_key, version)
    slug = inst["slug"] if inst else core.slugify(inst_key)
    path = note_path(slug, version)
    if not path:
        what = f"{inst['name']} ({inst['type']}, levels {inst['min']}–{inst['max']})" if inst else f"unknown instance {inst_key!r}"
        return [f"no notes yet for {what}.",
                f"Research it with {core.DATA / 'instances' / 'RESEARCH.md'}, write {core.ROOT / 'notes' / 'instances' / (slug + '.md')} "
                f"in the tagged format ({core.DATA / 'instances' / 'FORMAT.md'}), then rerun."], 2
    header, sections = parse_note(path.read_text())
    cls, spec_key = core.spec(snap, version)
    level, ranks = snap["level"], core.talent_ranks(snap)
    roles = char.get("roles") or default_roles(cls, spec_key, version)
    role = role or roles[0]
    kit = core.rules("class-abilities", version).get(cls, {})
    sr = core.rules("spec-stats", version)
    w = sr.get("wants", {}).get(spec_key or "") or sr.get("wants", {}).get(sr.get("classKind", {}).get(cls, ""), {})
    is_raid = (header.get("type") or (inst or {}).get("type")) == "raid"
    name = inst["name"] if inst else slug

    jobs, per_boss, prep, loot, watch = [], [], [], [], []
    for title, items in sections:
        mine = []
        for tags, text in items:
            kinds = {t.split(":", 1)[0] for t in tags}
            if kinds & PREP_TAGS or title.lower().startswith("before"):
                prep.append(text)
                continue
            loot_tags = [t for t in tags if t.startswith("loot:")]
            if loot_tags:
                if loot_ok(loot_tags[0], cls, spec_key, version):
                    loot.append(f"{text} ({title})")
                continue
            handled = False
            for t in tags:
                k, _, arg = t.partition(":")
                abil = None
                if k == "dispel":
                    abil = usable(kit.get("dispel", {}).get(arg), level, ranks)
                    later = not_yet(kit.get("dispel", {}).get(arg), level)
                elif k == "interrupt":
                    abil = usable(kit.get("interrupt"), level, ranks)
                    later = not_yet(kit.get("interrupt"), level)
                elif k == "cc":
                    abil = usable(kit.get("cc", {}).get(arg), level, ranks) or usable(kit.get("cc", {}).get("any"), level, ranks)
                    later = not_yet(kit.get("cc", {}).get(arg), level)
                elif k in ("enrage", "fear", "purge", "battle-res"):
                    abil = usable(kit.get("utility", {}).get(k), level, ranks)
                    later = not_yet(kit.get("utility", {}).get(k), level)
                elif k == "assign":
                    if arg.lower() == (cls or "").lower():
                        jobs.append(f"{title}: {text}")
                        mine.append(f"[your assignment] {text}")
                    handled = True
                    continue
                elif k in ROLE_TAGS:
                    if k == role:
                        mine.append(f"[{role}] {text}")
                    handled = True
                    continue
                elif k == "threat":
                    mine.append(f"[threat] {text}" if role == "tank" else f"[watch threat] {text}")
                    handled = True
                    continue
                elif k in ("position", "resist", "move"):
                    mine.append(f"[{t}] {text}")
                    handled = True
                    continue
                else:
                    continue
                if abil:
                    line = f"{text} → you: {abil['spell']}" + (" (verify on Forever)" if abil.get("verify") else "")
                    mine.append(f"[{k}{':' + arg if arg else ''}] {line}")
                    jobs.append(f"{title}: {line}")
                    handled = True
                elif k in ("dispel", "interrupt", "cc"):
                    hint = f" (you get {later['spell']} at {later['level']})" if later else ""
                    watch.append(f"{title}: {text}{hint}")
                    handled = True
            if not tags:
                mine.append(text)
            elif not handled:
                mine.append(text)
        if mine and not title.lower().startswith("before"):
            per_boss.append((title, mine))

    gear = core.gear(char["slug"])
    out = [f"BRIEFING {name} ({'raid' if is_raid else 'dungeon'}"
           + ((f", levels {inst['min']}–{inst['max']}" if inst['min'] != inst['max'] else f", level {inst['min']}") if inst else "") + f") for {snap['name']}: level {level} {cls}"
           + (f" ({spec_key})" if spec_key else "") + f", role {role}" + (f" (other roles: {', '.join(r for r in roles if r != role)})" if len(roles) > 1 else ""),
           f"notes: {path}" + (f" · updated {header['last updated']}" if header.get("last updated") else "")]
    out += freshness(header, inst, sections)
    out.append("\nYOUR JOBS")
    out += [f"- {j}" for j in jobs] or ["- nothing class-specific; play your role cleanly"]
    out.append("\nPER BOSS")
    for title, mine in per_boss:
        out.append(f"## {title}")
        out += [f"- {m}" for m in mine]
    if watch:
        out.append("\nWATCH OUT (no answer in your kit right now)")
        out += [f"- {x}" for x in watch]
    out.append("\nBEFORE YOU GO")
    out += [f"- {p}" for p in prep] or ["- nothing listed"]
    low = [f"{s} ({i['durability']})" for s, i in gear.items() if core.low_durability(i)]
    weakest = sorted(gear.items(), key=lambda kv: kv[1]["ilvl"] or 0)[:3]
    empty = [s for s in core.SLOTS if s not in gear and s != "Off Hand"]
    out.append("- gear check: " + "; ".join(filter(None, [
        ("repair: " + ", ".join(low)) if low else "durability ok",
        ("empty: " + ", ".join(empty)) if empty else "",
        "weakest: " + ", ".join(f"{s} {i['name']} (iLvl {i['ilvl']})" for s, i in weakest)])))
    cons = consumables(snap, w.get("want", []), version)
    if cons:
        out.append("- you can make: " + "; ".join(cons))
    if is_raid:
        res = core.resistances(gear)
        needed = sorted({t.split(":", 1)[1] for _, items in sections for tags, _ in items for t in tags if t.startswith("resist:")})
        out.append("\nRAID")
        out.append("- resistances needed: " + (", ".join(f"{s} (you have {res.get(s, 0)} from gear)" for s in needed) if needed else "none tagged"))
        out.append("- attunement/keys: see BEFORE YOU GO; the snapshot can't show them, so ask the user and log the answer")
    out.append("\nLOOT FOR YOU")
    out += [f"- {l}" for l in loot] or ["- nothing tagged for your spec"]
    return out, 0
