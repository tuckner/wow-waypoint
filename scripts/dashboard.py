"""Self-contained HTML dashboard in the Waypoint design system (design/README.md).

Three registers on one palette: trading cards for identity, a survey map for the journey to 60,
and console readouts for the numbers. Tokens come from design/tokens.css and are inlined.

Images (character renders and avatars, Wowhead item icons, profession icons)
are fetched once, cached in notes/cache/ and inlined as data URIs, so the page works offline and
inside a published artifact. Only image URLs go out; no character data leaves this computer.
"""
import html
import json
import math
import re
from datetime import datetime

import core
import milestones
import progress
import wowhead

LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"]
MIN_POINTS = 3
RENDER_MAX_AGE_H = 12  # renders change with gear but keep the same URL
TOKENS = core.KIT / "design" / "tokens.css"

# Blizzard class colors (card faces, dark theme) and a deeper variant for light paper.
CLASS = {
    "Druid": ("#ff7c0a", "#b95400"), "Warlock": ("#8788ee", "#4f51c4"), "Priest": ("#e8e8e8", "#6c7580"),
    "Mage": ("#3fc7eb", "#0f7894"), "Hunter": ("#aad372", "#55801f"), "Rogue": ("#fff468", "#8a7c00"),
    "Paladin": ("#f48cba", "#b83a72"), "Shaman": ("#2f8cff", "#0058b5"), "Warrior": ("#c69b6d", "#835a2e"),
}
QSCORE = {"poor": 0, "common": 1, "uncommon": 2, "rare": 3, "epic": 4, "legendary": 5}
STANDING = {"Hated": "hostile", "Hostile": "hostile", "Unfriendly": "unfriendly", "Neutral": "neutral",
            "Friendly": "friendly", "Honored": "friendly", "Revered": "revered", "Exalted": "exalted"}
SKIP_CLAUSE = re.compile(r"\b(plan|planned|planning|next|target|targets|want|heading|will|maybe)\b|^\s*\?", re.I)

# survey map geometry (viewBox units)
MW, MH, MX0, MX1 = 1000, 340, 46, 954
LANE_TOP, LANE_ROW = 22, 17  # waypoint label lane above the route
CHAR_W = 6.7  # mono 11px advance, for label packing


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def title_case(key):
    return " ".join(w.capitalize() if w not in ("of", "the") else w for w in key.replace("_", " ").split())


def num(v, pct=False):
    if v is None:
        return "–"
    if isinstance(v, str):
        return v
    if pct:
        return f"{v:.1f}%"
    return f"{v:,.0f}" if abs(v) >= 10 else f"{v:.1f}".rstrip("0").rstrip(".")


# ---------- data ----------

def doll_item(i, level):
    info = core.item_info(i)
    return {
        "slot": i.get("slot"), "name": info["name"], "ilvl": info["ilvl"], "quality": info["quality"],
        "icon": wowhead.icon_data_uri(info.get("icon")), "url": wowhead.item_url(info["id"]) if info.get("id") else None,
        "lines": [l for l in info["lines"] if not l.startswith("Item Level")], "low": core.low_durability(info),
        "req_high": bool(info["req"] and level and info["req"] > level),
    }


def visited_dungeons(slug, version="forever"):
    """Dungeons the activity log or journal says were run (clauses about plans are ignored)."""
    text = ""
    for f in ("activity.md", "journal.md"):
        p = core.BASE / slug / f
        if p.exists():
            text += p.read_text() + "\n"
    clauses = [c for line in text.splitlines() for c in re.split(r"[;.]\s", line) if c.strip() and not SKIP_CLAUSE.search(c)]
    out = set()
    for d in core.rules("instances", version):
        if d["type"] != "dungeon":
            continue
        names = [d["name"]] + [a for a in d.get("aliases", []) if len(a) >= 2 and a not in ("st", "dm", "vc")]
        pat = re.compile(r"(?<![\w'])(" + "|".join(re.escape(n) for n in names) + r")(?![\w'])", re.I)
        if any(pat.search(c) for c in clauses):
            out.add(d["slug"])
    return out


def collect(group=None):
    cfg = [c for c in core.load_config() if not group or c.get("group") == group or not c.get("watch")]
    out = []
    for idx, c in enumerate(cfg[:8]):
        snaps = core.history(c["slug"])
        if not snaps:
            continue
        pts = core.dedupe(snaps)
        cur = snaps[-1]
        lat = core.latest(c["slug"]) or {}
        days, prev = {}, None
        for s in snaps:  # quests gained per local day
            d = core.parse_time(s["at"]).astimezone().strftime("%Y-%m-%d")
            if prev is not None and s.get("quests") is not None and prev.get("quests") is not None:
                days[d] = days.get(d, 0) + max(0, s["quests"] - prev["quests"])
            prev = s
        changes = [{"at": b["at"][:10], "text": d} for a, b in zip(snaps, snaps[1:]) for d in core.diff(a, b)]
        level = cur["level"]
        cls = cur.get("class") or lat.get("class")
        version = core.version_of(c)
        out.append({
            "slug": c["slug"], "name": cur["name"], "first": cur["name"].split()[0], "watch": bool(c.get("watch")),
            "main": bool(c.get("main")), "slot": idx, "class": cls, "race": cur.get("race"), "level": level,
            "ilvl": cur.get("itemLevel"), "quests": cur.get("quests"), "roles": c.get("roles") or [],
            "faction": lat.get("faction"), "realmType": lat.get("realmType"), "guild": lat.get("guild"),
            "lastLogin": lat.get("lastLogin"), "colors": CLASS.get(cls, ("#c9a24a", "#8a6a1c")),
            "points": [{"t": s["at"], "level": s["level"], "ilvl": s.get("itemLevel"), "quests": s.get("quests")} for s in pts],
            "eta60": core.eta_days(snaps, max(0, 60 - level)), "pace": core.pace(snaps),
            "next": milestones.next_listed(cls, level, version=version),
            "waypoints": milestones.entries(cls, 0, 60, version, with_generated=False),
            "visited": visited_dungeons(c["slug"], version) if not c.get("watch") else set(),
            "questDays": days, "changes": changes[-14:],
            "items": {i.get("slot"): doll_item(i, level) for i in lat.get("items", [])},
            "stats": lat.get("stats") or {}, "trees": lat.get("trees") or [],
            "profs": lat.get("professions") or [], "reps": lat.get("reps") or [],
            "achievements": (lat.get("achievements") or [])[:5],
            "render": wowhead.image_uri(lat.get("render"), "renders", RENDER_MAX_AGE_H),
            "avatar": wowhead.image_uri(lat.get("avatar"), "renders", RENDER_MAX_AGE_H),
            "version": version,
        })
    return out


def worn(ch):
    return [i for s, i in ch["items"].items() if s not in core.COSMETIC]


def gear_grade(ch):
    w = worn(ch)
    if not w:
        return 0
    avg = sum(QSCORE.get(i["quality"], 1) for i in w) / len(w)
    return max(1, min(3, round(avg) - 0))  # common≈1, uncommon≈2, rare+≈3


def cvars(ch):
    cc, ccl = ch["colors"]
    return f"--cc:{cc};--ccl:{ccl}"


# ---------- card register ----------

ARCHETYPE = {  # (class, tree id or "_") -> archetype; the top talent tree decides the spec
    ("Warlock", "_"): "caster", ("Mage", "_"): "caster", ("Druid", "balance"): "caster", ("Priest", "shadow"): "caster",
    ("Shaman", "elemental"): "caster", ("Druid", "resto"): "healer", ("Priest", "_"): "healer", ("Shaman", "resto"): "healer",
    ("Paladin", "holy"): "healer", ("Druid", "feral"): "agility", ("Druid", "_"): "agility", ("Rogue", "_"): "agility",
    ("Hunter", "_"): "ranged", ("Warrior", "prot"): "tank", ("Paladin", "prot"): "tank", ("Warrior", "_"): "strength",
    ("Paladin", "_"): "strength", ("Shaman", "_"): "strength",
}
CARD_STATS = {
    "caster": [("SP", "spell_power", False), ("INT", "intellect", False), ("CRIT", "spell_crit", True)],
    "healer": [("HEAL", "spell_healing", False), ("INT", "intellect", False), ("MP5", "mana_regen", False)],
    "agility": [("AP", "attack_power", False), ("AGI", "agility", False), ("CRIT", "melee_crit", True)],
    "ranged": [("RAP", "ranged_attack_power", False), ("AGI", "agility", False), ("CRIT", "ranged_crit", True)],
    "strength": [("AP", "attack_power", False), ("STR", "strength", False), ("CRIT", "melee_crit", True)],
    "tank": [("ARM", "armor", False), ("STA", "stamina", False), ("DODGE", "dodge", True)],
}


def spec_of(ch):
    trees = [t for t in ch["trees"] if t.get("points")]
    top = max(trees, key=lambda t: t["points"]) if trees else None
    tid = (top or {}).get("id") or ""
    arch = ARCHETYPE.get((ch["class"], tid)) or ARCHETYPE.get((ch["class"], "_"), "strength")
    return (top["name"] if top else ch["class"]), arch


def card(ch, link=False, save=False):
    v = ch["stats"]
    spec, arch = spec_of(ch)
    stats = "".join(f"<div class='cs'><span>{k}</span><b>{num(v.get(key), pct) if v.get(key) is not None else '–'}</b></div>"
                    for k, key, pct in CARD_STATS[arch]) if v else ""
    pips = "".join(f"<i class='{'on' if n < gear_grade(ch) else ''}'></i>" for n in range(3))
    art = (f"<img class='art' data-crop src='{ch['render']}' alt='{esc(ch['name'])}, {esc(ch['race'])} {esc(ch['class'])}'>"
           if ch["render"] else "<div class='art-none'>No portrait yet. It appears after the next logout.</div>")
    ribbon = "<span class='ribbon'>Friend</span>" if ch["watch"] else ""
    roles = " · ".join({"heal": "Healer", "tank": "Tank", "dps": "DPS"}.get(r, r) for r in ch["roles"])
    w = [i for i in worn(ch) if i["ilvl"]]
    sig = max(w, key=lambda i: (i["ilvl"], QSCORE.get(i["quality"], 0))) if w else None
    sig_img = f"<img src='{sig['icon']}' alt=''>" if sig and sig["icon"] else ""
    sig_html = (f"<div class='sig'><span class='sig-ic q-{esc(sig['quality'])}'>{sig_img}</span>"
                f"<span class='sig-t'><span class='sig-l'>Signature · ilvl {sig['ilvl']}</span><span class='sig-n cq-{esc(sig['quality'])}'>{esc(sig['name'])}</span></span></div>") if sig else ""
    tag, attrs = ("a", f" href='#{esc(ch['slug'])}' data-goto='{esc(ch['slug'])}'") if link else ("div", "")
    last = ch["name"][len(ch["first"]):].strip()
    save_btn = (f"<button type='button' class='card-save' data-slug='{esc(ch['slug'])}' aria-label='Save card as image' title='Save card as image'>"
                "<svg viewBox='0 0 16 16' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
                "<path d='M8 2.5v7.5M4.8 7 8 10.2 11.2 7M3 13.5h10'/></svg></button>") if save and not link else ""
    return (f"<{tag} class='card' data-slug='{esc(ch['slug'])}' style='{cvars(ch)}'{attrs} aria-label='{esc(ch['name'])}, level {ch['level']} {esc(spec)} {esc(ch['class'])}'>"
            f"<div class='card-in'><div class='card-top'><span class='gem'>{ch['level']}</span>"
            f"<span class='cn'><b>{esc(ch['first'])}</b>{f'<small>{esc(last)}</small>' if last else ''}</span><span class='cls'>{esc(ch['class'])}</span>{save_btn}</div>"
            f"<div class='window' data-bg='{DEFAULT_SCENE.get(ch['class'], 'glow')}'><div class='scene' aria-hidden='true'></div><div class='glow'></div>{art}{ribbon}</div>"
            f"<div class='plate'><span>{esc(spec)} · {esc(ch['race'])}</span><span class='pips' title='Gear grade'>{pips}</span></div>"
            f"{sig_html}<div class='cstats'>{stats}</div>"
            f"<div class='card-foot'><span>WF·{ch['level']:03d}/060</span><span>{esc(roles) or esc((ch['faction'] or '').capitalize())}</span></div>"
            f"</div><div class='foil' aria-hidden='true'></div></{tag}>")


# ---------- survey register ----------

def mx(level):
    return MX0 + (max(1, min(60, level)) - 1) / 59 * (MX1 - MX0)


def my(level):
    return 300 - (level - 1) / 59 * 165 + 8 * math.sin(level * 0.55) + 4 * math.sin(level * 1.3 + 1)


def route_path(lo, hi):
    pts = []
    l = lo
    while l <= hi + 1e-9:
        pts.append(f"{mx(l):.1f},{my(l):.1f}")
        l += 0.25
    return "M" + " L".join(pts)


def contours():
    out = []
    for k in range(17):
        base = 318 - k * 21
        pts = []
        for x in range(0, MW + 1, 20):
            y = base - x * 0.05 + 7 * math.sin(x * 0.011 + k * 0.9) + 4 * math.sin(x * 0.029 + k * 1.7)
            pts.append(f"{x},{y:.1f}")
        cls = "ct ct-i" if k % 5 == 0 else "ct"
        out.append(f"<path class='{cls}' d='M{' L'.join(pts)}'/>")
    return "".join(out)


def survey_map(chars, focus=None):
    """Route to 60. With focus: that character's waypoints and dungeon strip. Without: everyone's pins."""
    lv = focus["level"] if focus else max(c["level"] for c in chars)
    grid = "".join(f"<line class='lg' x1='{mx(l):.1f}' x2='{mx(l):.1f}' y1='18' y2='{MH - 22}'/>"
                   f"<text class='ll' x='{mx(l):.1f}' y='{MH - 6}'>{l}</text>" for l in (1, 10, 20, 30, 40, 50, 60))
    walked = route_path(1, lv)
    ahead = route_path(lv, 60)
    pins = ""
    labels = ""
    if focus:
        seen = {}
        for w in focus["waypoints"]:
            seen.setdefault(w["level"], []).append(w["what"])
        rows_end = []  # right edge of the last label in each lane row
        for l, whats in sorted(seen.items()):
            x, y = mx(l), my(l)
            past = l <= lv
            pins += f"<circle class='wp{' wp-past' if past else ''}' cx='{x:.1f}' cy='{y:.1f}' r='4.5'><title>Level {l}: {esc('; '.join(whats))}</title></circle>"
            if past:
                continue
            txt = whats[0] if len(whats) == 1 else f"{whats[0]} +{len(whats) - 1}"
            txt = txt if len(txt) <= 30 else txt[:29] + "…"
            label = f"{l} · {txt}"
            w = len(label) * CHAR_W
            lx = min(x - 4, MW - 8 - w)  # start just left of the pin, kept inside the frame
            row = next((r for r, e in enumerate(rows_end) if e < lx - 10), None)
            if row is None:
                rows_end.append(0)
                row = len(rows_end) - 1
            rows_end[row] = lx + w
            ty = LANE_TOP + row * LANE_ROW
            labels += (f"<line class='wl' x1='{x:.1f}' x2='{x:.1f}' y1='{ty + 4:.1f}' y2='{y - 6:.1f}'/>"
                       f"<text class='wt' x='{lx:.1f}' y='{ty:.1f}'>{esc(label)}</text>")
        x, y = mx(lv), my(lv)
        pins += (f"<circle class='here-ring' cx='{x:.1f}' cy='{y:.1f}' r='13'/><circle class='here' cx='{x:.1f}' cy='{y:.1f}' r='7'/>"
                 f"<text class='here-t' x='{x:.1f}' y='{y + 30:.1f}'>YOU · {lv}</text>")
    else:
        for n, c in enumerate(sorted(chars, key=lambda c: c["level"])):
            x, y = mx(c["level"]), my(c["level"])
            dy = 26 + (n % 3) * 15
            pins += (f"<g style='{cvars(c)}'><circle class='pin' cx='{x:.1f}' cy='{y:.1f}' r='6.5'/>"
                     f"<line class='wl' x1='{x:.1f}' x2='{x:.1f}' y1='{y + 7:.1f}' y2='{y + dy - 11:.1f}'/>"
                     f"<text class='pin-t' x='{x:.1f}' y='{y + dy:.1f}'>{esc(c['first'].upper())} {c['level']}</text></g>")
    svg = (f"<svg class='map' viewBox='0 0 {MW} {MH}' role='img' aria-label='Route to level 60, currently level {lv}'>"
           f"<g>{contours()}</g>{grid}<path class='route-ahead' d='{ahead}'/><path class='route' d='{walked}'/>{labels}{pins}</svg>")
    strip = dungeon_strip(focus or {"level": lv, "visited": set().union(*(c["visited"] for c in chars)), "faction": None}, chars)
    return f"<div class='mapwrap'><div class='mapscroll'>{svg}{strip}</div></div>"


def dungeon_strip(focus, chars):
    fac = {c.get("faction") for c in chars if c.get("faction")}
    ds = [d for d in core.rules("instances", (chars[0] if chars else {}).get("version", "forever"))
          if d["type"] == "dungeon" and (not d.get("faction") or d["faction"] in fac)]
    RH, CW = 30, 7.3  # row height; 12px mono advance
    rows, placed = [], []
    for d in sorted(ds, key=lambda d: (d["min"], d["max"])):
        x0, x1 = mx(d["min"]), mx(d["max"])
        done = d["slug"] in focus["visited"]
        label = d["name"] + (" ✓" if done else "")
        w = len(label) * CW + 16
        px = min(x0, MW - 4 - w)
        right = max(px + w, x1)
        r = next((i for i, e in enumerate(rows) if e < px - 6), None)
        if r is None:
            rows.append(0)
            r = len(rows) - 1
        rows[r] = right
        placed.append((d, r, x0, x1, px, w, label, done))
    lv = focus["level"]
    parts = []
    for d, r, x0, x1, px, w, label, done in placed:
        y = 4 + r * RH
        state = "done" if done else "now" if d["min"] - 2 <= lv <= d["max"] else "later" if d["min"] > lv else "past"
        parts.append(f"<g class='dg dg-{state}'><rect class='dg-pill' x='{px:.1f}' y='{y}' width='{w:.1f}' height='19' rx='4'/>"
                     f"<text x='{px + 8:.1f}' y='{y + 13.5}'>{esc(label)}</text>"
                     f"<rect class='dg-range' x='{x0:.1f}' y='{y + 22}' width='{max(4, x1 - x0):.1f}' height='3' rx='1.5'/>"
                     f"<title>{esc(d['name'])}: levels {d['min']}–{d['max']}{' (run)' if done else ''}</title></g>")
    h = len(rows) * RH + 6
    return f"<svg class='strip' viewBox='0 0 {MW} {h}' role='img' aria-label='Dungeons by level range'>{''.join(parts)}</svg>"


# ---------- console register ----------

def spark(values, w=112, h=28):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return f"<svg class='spark' viewBox='0 0 {w} {h}' aria-hidden='true'><line class='sp-flat' x1='2' x2='{w - 6}' y1='{h / 2}' y2='{h / 2}'/><circle class='sp-end' cx='{w - 6}' cy='{h / 2}' r='3'/></svg>"
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pts = [(2 + i / (len(vals) - 1) * (w - 8), h - 4 - (v - lo) / span * (h - 8)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{pts[0][0]:.1f},{h} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f},{h} Z"
    return (f"<svg class='spark' viewBox='0 0 {w} {h}' aria-hidden='true'><path class='sp-area' d='{area}'/>"
            f"<polyline class='sp-line' points='{line}'/><circle class='sp-end' cx='{pts[-1][0]:.1f}' cy='{pts[-1][1]:.1f}' r='3'/></svg>")


def light(state, word, detail=""):
    d = f"<span class='ld'>{esc(detail)}</span>" if detail else ""
    return f"<div class='light l-{state}'><i></i><span class='lw'>{esc(word)}</span>{d}</div>"


def status_lights(ch):
    w = worn(ch)
    low = [i["slot"] for i in w if i["low"]]
    empty = [s for s in core.SLOTS if s not in ch["items"] and s not in ("Off Hand",)]
    capped = [p["name"] for p in ch["profs"] if p.get("max") and p.get("skill", 0) >= p["max"] and p["max"] < 300]
    out = [light("bad" if low else "ok", "Repair" if low else "Durability", ", ".join(low) if low else "all good"),
           light("warn" if empty else "ok", f"{len(empty)} empty" if empty else "All slots", ", ".join(empty) if empty else "filled"),
           light("warn" if capped else "ok", "Train" if capped else "Professions", ", ".join(capped) + " at cap" if capped else "room to skill up")]
    return f"<div class='lights'>{''.join(out)}</div>"


def spark_or_note(values, note):
    vals = [v for v in values if v is not None]
    if len(set(vals)) >= 2:
        return spark(vals)
    return f"<span class='tm-sub'>{esc(note)}</span>"


def readouts(ch):
    P = ch["points"]
    w = [i for i in worn(ch) if i["ilvl"]]
    best = max(w, key=lambda i: i["ilvl"]) if w else None
    low = min(w, key=lambda i: i["ilvl"]) if w else None
    r = ch.get("rate")
    eta = "Level 60 reached" if ch["level"] >= 60 else (f"60 in about {(60 - ch['level']) / r:.0f} days" if r else "60: needs a few days of history")
    today = datetime.now().strftime("%Y-%m-%d")
    tiles = [
        ("Level", num(ch["level"]), f"<span class='meter meter-lv'><span style='width:{ch['level'] / 60 * 100:.1f}%'></span></span><span class='tm-sub'>{60 - ch['level']} to go</span>"),
        ("Item level", num(ch["ilvl"]), spark_or_note([p["ilvl"] for p in P], f"best {best['ilvl']} · low {low['ilvl']}" if best else "no gear")),
        ("Quests", num(ch["quests"]), spark_or_note([p["quests"] for p in P], f"+{ch['questDays'].get(today, 0)} today")),
        ("Pace", f"{r:.1f}" if r else "–", f"<span class='tm-unit'>levels / day</span><span class='tm-sub'>{esc(eta)}</span>"),
    ]
    return "<div class='tms'>" + "".join(f"<div class='tm'><span class='lbl'>{k}</span><b>{v}</b>{s}</div>" for k, v, s in tiles) + "</div>"


PLAN_ITEM = re.compile(r"^\s*\d+\.\s+(.+)$")


def plan_next(slug):
    p = core.BASE / slug / "plan.md"
    if not p.exists():
        return [], None
    text = p.read_text()
    written = re.search(r"_Plan written (\d{4}-\d{2}-\d{2})", text)
    items, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip().lower().startswith("## next session")
            continue
        if inside and (m := PLAN_ITEM.match(line)):
            items.append(m.group(1).strip())
    return items, written.group(1) if written else None


def kind_of(text):
    s = text.lower()
    for k, words in (("Dungeon", ("run ", "dungeon", "rfk", "sm ", "bfd", "sfk", "graveyard")), ("Train", ("train", "talent")),
                     ("Quest", ("quest", "pick up")), ("Errand", ("buy", "sell", "repair", "bank", "mail")), ("Gear", ("gear", "slot"))):
        if any(w in s for w in words):
            return k
    return "Plan"


def up_next(ch):
    items = []
    low = [i["slot"] for i in worn(ch) if i["low"]]
    if low:
        items.append(("Errand", "Repair before the next run", f"{', '.join(low)} are below 35% durability."))
    plan, written = ([], None) if ch["watch"] else plan_next(ch["slug"])
    for it in plan:
        parts = re.split(r"(?<=[.:])\s+", it, maxsplit=1)
        head, rest = parts[0], parts[1] if len(parts) > 1 else ""
        items.append((kind_of(it), progress.inline_md(head.rstrip(".:")), progress.inline_md(rest) if rest else ""))
    if not plan:
        for m in milestones.entries(ch["class"], ch["level"], ch["level"] + 6, ch["version"], with_generated=False)[:2]:
            items.append(("Train" if m["kind"] in ("spell", "talent") else "Quest" if m["kind"] == "quest" else "Goal",
                          esc(m["what"]), f"Unlocks at level {m['level']}" + (f", {m['level'] - ch['level']} to go." if m["level"] > ch["level"] else ".")))
        fac = ch.get("faction")
        for d in core.rules("instances", ch["version"]):
            if d["type"] == "dungeon" and d["min"] - 1 <= ch["level"] <= d["max"] - 2 and d["slug"] not in ch["visited"] and (not d.get("faction") or d["faction"] == fac):
                items.append(("Dungeon", esc(d["name"]), f"Levels {d['min']}–{d['max']}. Not in your log yet."))
                if sum(1 for i in items if i[0] == "Dungeon") >= 2:
                    break
        empty = [s for s in core.SLOTS if s not in ch["items"] and s not in ("Off Hand",)]
        if empty:
            items.append(("Gear", f"Fill {len(empty)} empty slot{'s' if len(empty) > 1 else ''}", f"{', '.join(empty)}. Check the auction house or quest rewards."))
        for pr in ch["profs"]:
            if pr.get("max") and (pr.get("skill") or 0) >= pr["max"] and pr["max"] < 300:
                items.append(("Train", f"Train the next {esc(pr['name'])} rank", f"Stuck at {pr['skill']}/{pr['max']}."))
    if not items:
        return ""
    rows = "".join(f"<li><span class='un-k un-{k.lower()}'>{k}</span><div><b>{title}</b>" + (f"<span>{detail}</span>" if detail else "") + "</div></li>"
                   for k, title, detail in items[:6])
    src = (f"From your plan ({written}). Run /plan to refresh." if plan else
           "Suggested from level, gear and your log." + ("" if ch["watch"] else " Run /plan for a full route."))
    return (f"<div class='un'><div class='un-h'><span class='lbl'>Up next</span><span class='ch-r'>{esc(src)}</span></div>"
            f"<ol class='un-list'>{rows}</ol></div>")


def subject(ch):
    meta = " · ".join(x for x in (f"{ch['race']} {ch['class']}", (ch["faction"] or "").capitalize(), ch["realmType"],
                                  ch["guild"] and f"<{ch['guild']}>") if x)
    seen = f"<span class='seen' data-ts='{esc(ch['lastLogin'])}'>seen {esc(str(ch['lastLogin'] or '')[:10])}</span>" if ch["lastLogin"] else ""
    v = ch["stats"]
    roles = "".join(f"<span class='role'>{esc({'heal': 'Healer', 'tank': 'Tank', 'dps': 'DPS'}.get(r, r))}</span>" for r in ch["roles"])
    vit = (f"<div class='vits'><div class='vit'><span class='lbl'>Health</span><b>{num(v.get('health'))}</b><span class='bar hp'></span></div>"
           f"<div class='vit'><span class='lbl'>Mana</span><b>{num(v.get('power'))}</b><span class='bar mp'></span></div></div>") if v.get("health") else ""
    return (f"<section class='console subj'><header class='ch'><span class='lbl'>{'Friend' if ch['watch'] else 'Hero'}</span>{seen}</header>"
            f"<div class='subj-top'><div class='subj-id'><h1 class='sname'>{esc(ch['name'])}</h1><div class='smeta'>{esc(meta)}</div>"
            f"<div class='roles'>{roles}</div></div>{vit}</div>"
            f"{readouts(ch)}{status_lights(ch)}{up_next(ch)}</section>")


def tooltip(it):
    rows = []
    for l in it["lines"]:
        k = "eq" if l.startswith(("Equip:", "Use:", "Chance on hit", "Enchanted:")) else ""
        if (l.startswith("Durability") and it["low"]) or (l.startswith("Requires Level") and it["req_high"]):
            k = "bad"
        rows.append(f"<div class='{k}'>{esc(l)}</div>")
    link = "<div class='tt-link'>Click to open on Wowhead</div>" if it["url"] else ""
    return (f"<div class='tt' role='tooltip'><div class='tt-name q-{esc(it['quality'])}'>{esc(it['name'])}</div>"
            f"<div class='tt-ilvl'>ITEM LEVEL {esc(it['ilvl'])}</div>{''.join(rows)}{link}</div>")


def icon(it, small=False):
    img = f"<img src='{it['icon']}' alt=''>" if it["icon"] else ""
    tag, href = ("a", f" href='{esc(it['url'])}' target='_blank' rel='noopener'") if it["url"] else ("span", " tabindex='0'")
    return (f"<span class='tip-host'><{tag} class='ic{' ic-sm' if small else ''} q-{esc(it['quality'])}'{href} "
            f"aria-label='{esc(it['slot'])}: {esc(it['name'])}'>{img}</{tag}>{tooltip(it)}</span>")


def gear_readout(ch):
    w = worn(ch)
    top = max([i["ilvl"] or 0 for i in w] + [ch["level"] + 5])
    weakest = {i["slot"] for i in sorted((i for i in w if i["ilvl"]), key=lambda i: i["ilvl"])[:2]}
    rows = []
    for s in core.SLOTS:
        it = ch["items"].get(s)
        if not it:
            if s in ("Off Hand",):
                continue
            rows.append(f"<div class='gr gr-empty'><span class='ic ic-empty'></span><span class='gs'>{esc(s)}</span>"
                        f"<span class='gn muted'>empty</span><span class='gm'></span>{light('warn', 'empty')}</div>")
            continue
        st = ("bad", "repair") if it["low"] else ("warn", "weak") if s in weakest else ("ok", "ok")
        pct = (it["ilvl"] or 0) / top * 100
        rows.append(f"<div class='gr'>{icon(it)}<span class='gs'>{esc(s)}</span>"
                    f"<span class='gn q-{esc(it['quality'])}'>{esc(it['name'])}</span>"
                    f"<span class='gm'><span class='meter'><span style='width:{pct:.0f}%'></span></span><b>{esc(it['ilvl'])}</b></span>"
                    f"{light(*st)}</div>")
    return (f"<section class='console'><header class='ch'><span class='lbl'>Gear readout</span>"
            f"<span class='ch-r'>avg ilvl {esc(ch['ilvl'])} · meter vs best {top}</span></header><div class='grs'>{''.join(rows)}</div></section>")


def stats_console(ch):
    v = ch["stats"]
    if not v:
        return ""
    groups = [
        ("Attributes", [("STR", v.get("strength")), ("AGI", v.get("agility")), ("STA", v.get("stamina")), ("INT", v.get("intellect")), ("SPI", v.get("spirit"))]),
        ("Melee", [("Attack power", v.get("attack_power")), ("Crit", num(v.get("melee_crit"), True)), ("MH DPS", num(v.get("main_hand_dps"))), ("MH speed", num(v.get("main_hand_speed")))]),
        ("Spell", [("Spell power", v.get("spell_power")), ("Healing", v.get("spell_healing")), ("Crit", num(v.get("spell_crit"), True)), ("Mana regen", v.get("mana_regen"))]),
        ("Defense", [("Armor", v.get("armor")), ("Defense", v.get("defense")), ("Dodge", num(v.get("dodge"), True)), ("Parry", num(v.get("parry"), True))]),
    ]
    res = [(n[:3].upper(), v.get(f"{n.lower()}_resistance")) for n in ("Fire", "Frost", "Nature", "Shadow", "Arcane")]
    if any(r for _, r in res):
        groups.append(("Resist", [(n, r) for n, r in res if r]))
    body = "".join(f"<div class='rg'><div class='lbl'>{g}</div>" + "".join(
        f"<div class='ro'><span>{esc(k)}</span><b>{esc(num(x))}</b></div>" for k, x in rows) + "</div>" for g, rows in groups)
    return f"<section class='console'><header class='ch'><span class='lbl'>Stats</span></header><div class='rgs'>{body}</div></section>"


def talents_console(ch):
    trees = ch["trees"]
    total = sum(t["points"] for t in trees)
    if not trees or not total:
        return ""
    split = "/".join(str(t["points"]) for t in trees)
    segs = "".join(f"<span class='seg' style='flex:{t['points']};background:var(--tree-{n + 1})'></span>" for n, t in enumerate(trees) if t["points"])
    legend = "".join(f"<span class='tl'><i style='background:var(--tree-{n + 1})'></i>{esc(t['name'])} <b>{t['points']}</b></span>" for n, t in enumerate(trees))
    chips = "".join(f"<span class='chip'>{esc(title_case(k))}<b>{r}</b></span>"
                    for t in sorted(trees, key=lambda t: -t["points"]) for k, r in (t.get("ranks") or {}).items())
    return (f"<section class='console'><header class='ch'><span class='lbl'>Talents</span><span class='ch-r'>{split} · {total} pts</span></header>"
            f"<div class='tbar'>{segs}</div><div class='tlegend'>{legend}</div><div class='chips'>{chips}</div></section>")


def profs_console(ch):
    rows = []
    for p in sorted(ch["profs"], key=lambda p: (bool(p.get("secondary")), -(p.get("skill") or 0))):
        skill, mx_ = p.get("skill") or 0, p.get("max") or 0
        ico = wowhead.image_uri(p.get("icon"), "icons-prof")
        img = f"<img class='pi' src='{ico}' alt=''>" if ico else "<span class='pi'></span>"
        capped = mx_ and skill >= mx_ and mx_ < 300
        sec = "<span class='tag'>secondary</span>" if p.get("secondary") else ""
        rows.append(f"<div class='pr'>{img}<div class='pb'><div class='pt'><span>{esc(p['name'])}{sec}</span>"
                    f"<b>{skill}<span class='muted'>/{mx_}</span></b></div>"
                    f"<div class='meter meter-cap'><span class='cap' style='width:{min(100, mx_ / 3):.1f}%'></span><span style='width:{min(100, skill / 3):.1f}%'></span></div>"
                    + (light("warn", "at cap", "train the next rank") if capped else "") + "</div></div>")
    if not rows:
        return ""
    return f"<section class='console'><header class='ch'><span class='lbl'>Professions</span><span class='ch-r'>of 300</span></header>{''.join(rows)}</section>"


def reps_console(ch):
    reps = sorted(ch["reps"], key=lambda r: (-(r.get("tier") or 0), -(r.get("value") or 0)))[:6]
    if not reps:
        return ""
    rows = []
    for r in reps:
        val, mx_ = r.get("value") or 0, r.get("max") or 0
        tone = STANDING.get(r.get("standing"), "neutral")
        rows.append(f"<div class='rp' style='--rc:var(--rep-{tone})'><div class='pt'><span>{esc(r['name'])}</span><b class='rs'>{esc(r.get('standing'))}</b></div>"
                    f"<div class='meter meter-rep'><span style='width:{0 if not mx_ else min(100, val / mx_ * 100):.1f}%'></span></div>"
                    f"<div class='rv'>{val:,} / {mx_:,}</div></div>")
    return f"<section class='console'><header class='ch'><span class='lbl'>Reputation</span></header><div class='rps'>{''.join(rows)}</div></section>"


def log_console(ch):
    ev = list(reversed(ch["changes"]))[:8]
    ach = [a for a in ch["achievements"] if isinstance(a, dict)]
    if not ev and not ach:
        return ""
    items = "".join(f"<li><time>{esc(e['at'][5:])}</time><span>{esc(e['text'])}</span></li>" for e in ev)
    achs = "".join(f"<li><time>{esc(str(a.get('at', ''))[5:10])}</time><span>{esc(a.get('name'))}</span></li>" for a in ach)
    out = "<section class='console'><header class='ch'><span class='lbl'>Log</span></header>"
    out += f"<ul class='log'>{items}</ul>" if items else "<div class='muted small'>Nothing new since tracking started.</div>"
    if achs:
        out += f"<div class='lbl sub-lbl'>Achievements</div><ul class='log'>{achs}</ul>"
    return out + "</section>"


def character_view(ch):
    return (f"<div class='view' data-view='{esc(ch['slug'])}' style='{cvars(ch)}'>"
            f"<div class='hero'><div class='hero-card'>{card(ch, save=True)}{scene_picker(ch, PHOTOS)}</div>{subject(ch)}</div>"
            f"<section class='survey'><header class='sh'><span class='lbl'>Survey</span><h2>Route to 60</h2>"
            f"<span class='sh-r'>Dungeon bars share the level scale · green ✓ = in your log · outlined = your level now</span></header>{survey_map([ch], ch)}</section>"
            f"<div class='cols'><div class='col'>{gear_readout(ch)}{talents_console(ch)}</div>"
            f"<div class='col'>{stats_console(ch)}{profs_console(ch)}{reps_console(ch)}{log_console(ch)}</div></div></div>")


def binder_view(chars):
    friends = [c for c in chars if c["watch"]]
    if not friends:
        return ("<div class='view' data-view='friends'><header class='vh'><span class='lbl'>Binder</span><h2>Friends</h2></header>"
                "<div class='console empty'>No friends watched yet. Add one with /party.</div></div>")
    mine = [c for c in chars if not c["watch"]]
    cards = "".join(f"<div class='slotcard'>{card(c, link=True)}</div>" for c in friends)
    rows = "".join(
        f"<div class='race-row' style='{cvars(c)}'><span class='rn'>{esc(c['first'])}{' <span class=tag>friend</span>' if c['watch'] else ''}</span>"
        f"<span class='meter meter-race'><span style='width:{c['level'] / 60 * 100:.1f}%'></span></span><b>{c['level']}</b>"
        f"<span class='muted rd'>{esc(c['class'])} · ilvl {esc(c['ilvl'])}</span></div>"
        for c in sorted(friends, key=lambda c: -c["level"]))
    return (f"<div class='view' data-view='friends'><header class='vh'><span class='lbl'>Binder</span><h2>Friends</h2></header>"
            f"<div class='binder'>{cards}</div>"
            f"<section class='survey'><header class='sh'><span class='lbl'>Survey</span><h2>Where they are</h2></header>{survey_map(friends)}</section>"
            f"<section class='console'><header class='ch'><span class='lbl'>Level race</span><span class='ch-r'>to 60</span></header>{rows}</section>"
            "</div>")


def table(headers, rows):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in rows)
    return f"<div class='tw'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"


def chart_block(cid, title, key, chars, unit):
    sec = f" id='sec-{key}'"
    enough = any(len(c["points"]) >= MIN_POINTS for c in chars)
    rows = [(c["first"], p["t"][:16].replace("T", " "), p.get(key)) for c in chars for p in c["points"]]
    tbl = f"<details><summary>Show table</summary>{table(['Character', 'Snapshot (UTC)', unit], rows)}</details>"
    head = f"<header class='ch'><span class='lbl'>{esc(title)}</span></header>"
    if not enough:
        return (f"<section class='console'{sec}>{head}<div class='empty'>Not enough history yet. Check back after a few sessions "
                f"(snapshots are taken at most once a day).</div>{tbl}</section>")
    return (f"<section class='console'{sec}>{head}<div class='legend' data-legend></div>"
            f"<div class='chart' id='{cid}' data-key='{key}' data-unit='{esc(unit)}'></div>{tbl}</section>")


def bars_block(chars):
    dates = sorted({d for c in chars for d in c["questDays"]})[-14:]
    head = "<header class='ch'><span class='lbl'>Quests per day</span></header>"
    if not dates:
        return f"<section class='console' id='sec-quests'>{head}<div class='empty'>Not enough history yet.</div></section>"
    rows = [(c["first"], d, c["questDays"].get(d, 0)) for d in dates for c in chars]
    return (f"<section class='console' id='sec-quests'>{head}<div class='legend' data-legend></div><div class='chart' id='c-quests' data-bars='1'></div>"
            f"<details><summary>Show table</summary>{table(['Character', 'Day', 'Quests'], rows)}</details></section>")


def changes_block(chars):
    ev = sorted(((e["at"], c, e["text"]) for c in chars for e in c["changes"]), key=lambda x: x[0], reverse=True)[:24]
    if not ev:
        return ""
    return ("<section class='console' id='sec-changes'><header class='ch'><span class='lbl'>All changes</span></header><ul class='log'>" + "".join(
        f"<li><time>{esc(a[5:])}</time><span><span class='sw' style='background:var(--s{c['slot'] + 1})'></span><b>{esc(c['first'])}</b> {esc(t)}</span></li>"
        for a, c, t in ev) + "</ul></section>")


def progress_view(chars):
    return ("<div class='view' data-view='progress'><header class='vh'><span class='lbl'>Console</span><h2>Progress</h2>"
            "<span class='muted'>From daily snapshots. Each logout adds a point.</span></header><div class='pgrid'>"
            + chart_block("c-level", "Level over time", "level", chars, "Level")
            + chart_block("c-ilvl", "Item level over time", "ilvl", chars, "Item level")
            + bars_block(chars) + changes_block(chars) + "</div></div>")


PAGE_CSS = """
/* Layout: sticky tab strip; each character view = hero (card | subject console), survey band, two console columns. */
:root{%DARK_S%}
:root{%LIGHT_S%}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){%DARK_S%}}
:root[data-theme="dark"]{%DARK_S%}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--paper);color:var(--ink);font:var(--t-body)/1.5 var(--font-body);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--sheet)}
a{color:inherit}
.wrap{max-width:1200px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.muted{color:var(--ink-3)}.small{font-size:var(--t-small)}
.lbl{font:600 var(--t-micro)/1 var(--font-mono);letter-spacing:var(--track-label);text-transform:uppercase;color:var(--ink-3)}
.tag{font:600 9.5px/1 var(--font-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);border:1px solid var(--rule-2);border-radius:3px;padding:2px 4px;margin-left:6px;vertical-align:2px}
h1,h2{text-wrap:balance}

/* sidebar shell: groups Heroes / Friends / Progress with their options underneath */
.shell{display:grid;grid-template-columns:232px minmax(0,1fr)}
.side{position:sticky;top:0;align-self:start;height:100vh;height:100dvh;background:var(--sheet);border-right:1px solid var(--rule);
  padding-left:max(0px,env(safe-area-inset-left,0px));overflow-y:auto}
.side-in{display:flex;flex-direction:column;gap:22px;padding:20px 14px 20px 16px;min-height:100%}
.brand{font:800 22px/1 var(--font-display);letter-spacing:.12em;text-transform:uppercase;display:flex;align-items:center;gap:9px;padding-left:4px}
.brand i{width:10px;height:10px;border-radius:50%;background:var(--signal);box-shadow:0 0 0 3px color-mix(in srgb,var(--signal) 25%,transparent)}
.nav{display:grid;gap:18px}
.ng-h{display:block;padding:0 8px 7px;border-bottom:1px dashed var(--rule-2);margin-bottom:6px}
.ng-items{display:grid;gap:2px}
.tab{display:flex;align-items:center;gap:9px;padding:5px 8px;border-radius:var(--r-2);color:var(--ink-2);font-weight:600;text-decoration:none}
.tab:hover{background:var(--sheet-2);color:var(--ink)}
.tab[aria-selected="true"]{background:var(--ink);color:var(--paper)}
.tab[aria-selected="true"] .lv{color:color-mix(in srgb,var(--paper) 65%,transparent)}
.tn{flex:1;min-width:0;display:grid;line-height:1.15}.tn>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tn-l{font:500 11px/1.2 var(--font-body);color:var(--ink-3)}.tab[aria-selected="true"] .tn-l{color:color-mix(in srgb,var(--paper) 65%,transparent)}
.tab .lv{font:500 12px/1 var(--font-mono);color:var(--ink-3)}
.tab-sub{padding-left:12px;font-weight:500}
.tab-sub::before{content:"";width:5px;height:5px;border-radius:1px;background:var(--rule-2);flex:none}
.av{width:26px;height:26px;border-radius:6px;object-fit:cover;flex:none;border:1px solid var(--c,var(--rule-2));background:var(--sheet-2)}
.gen{margin-top:auto;font:500 11px/1.4 var(--font-mono);color:var(--ink-3);padding-left:6px}
:focus-visible{outline:2px solid var(--signal);outline-offset:2px}
.main{min-width:0;padding-block:24px 60px;padding-left:max(24px,env(safe-area-inset-left,0px));padding-right:max(24px,env(safe-area-inset-right,0px));max-width:1240px}
.view>section{scroll-margin-top:16px}
@media (max-width:860px){
  .shell{grid-template-columns:minmax(0,1fr)}
  .side{position:sticky;top:env(safe-area-inset-top,0px);height:auto;z-index:6;border-right:0;border-bottom:1px solid var(--rule);overflow:visible;padding-left:0}
  .side-in{flex-direction:row;align-items:center;gap:14px;padding:10px max(16px,env(safe-area-inset-right,0px)) 10px max(16px,env(safe-area-inset-left,0px));min-height:0;overflow-x:auto}
  .brand{font-size:18px}.nav{display:flex;gap:16px}.ng{display:flex;align-items:center;gap:6px}
  .ng-h{border:0;padding:0;margin:0}.ng-items{display:flex;gap:2px}.tab{white-space:nowrap}.tab-sub::before{display:none}.gen{display:none}
  .main{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
  .view>section{scroll-margin-top:70px}
}
.view{display:grid;gap:18px}
.view[hidden]{display:none!important}
.vh{display:grid;gap:4px}.vh h2,.sh h2{font:800 var(--t-h1)/1 var(--font-display);letter-spacing:.02em;text-transform:uppercase;margin:0}

/* hero */
.hero{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:18px;align-items:stretch}
.hero-card{display:flex;flex-direction:column;align-items:center;gap:10px}

/* card register */
.card{position:relative;display:block;width:100%;max-width:300px;aspect-ratio:5/7;border-radius:var(--r-card);padding:7px;text-decoration:none;color:var(--card-ink);
  background:linear-gradient(135deg,var(--cc),color-mix(in srgb,var(--cc) 40%,#111) 45%,var(--cc) 70%,color-mix(in srgb,var(--cc) 55%,#fff));
  box-shadow:var(--shadow-card);transform:perspective(900px) rotateX(var(--ry,0deg)) rotateY(var(--rx,0deg));transition:transform .25s ease;will-change:transform}
.card-in{position:relative;height:100%;border-radius:calc(var(--r-card) - 5px);background:var(--card-face);display:grid;grid-template-rows:auto 1fr auto auto auto auto;overflow:hidden}
.sig{display:flex;align-items:center;gap:8px;margin:6px 8px 0;padding:5px 7px;border-radius:4px;background:linear-gradient(90deg,color-mix(in srgb,var(--cc) 22%,transparent),rgba(255,255,255,.03))}
.sig-ic{width:26px;height:26px;border-radius:4px;border:1.5px solid #e6e6e6;overflow:hidden;flex:none;background:#000}.sig-ic img{width:100%;height:100%;display:block}
.sig-ic.q-uncommon{border-color:#1eff00}.sig-ic.q-rare{border-color:#3b93ff}.sig-ic.q-epic{border-color:#b66af2}.sig-ic.q-poor{border-color:#9d9d9d}
.sig-t{display:grid;min-width:0;line-height:1.2}.sig-l{font:600 8.5px/1.3 var(--font-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--card-ink-2)}
.sig-n{font-weight:600;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#eee}
.cq-uncommon{color:#1eff00}.cq-rare{color:#4c9dff}.cq-epic{color:#c084fc}.cq-poor{color:#9d9d9d}
.card-top{display:flex;align-items:center;gap:8px;padding:9px 10px 7px}
.gem{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--cc);color:#111;font:700 13px/1 var(--font-mono);box-shadow:inset 0 -2px 0 rgba(0,0,0,.25)}
.cn{display:grid;flex:1;min-width:0;line-height:1}.cn b,.cn small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.cn b{font:800 24px/1 var(--font-display);text-transform:uppercase;letter-spacing:.03em}.cn small{font:700 13px/1.15 var(--font-display);text-transform:uppercase;letter-spacing:.16em;color:var(--card-ink-2);margin-top:2px}
.cls{font:600 10px/1 var(--font-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--cc)}
.window{position:relative;margin:0 8px;border-radius:6px;overflow:hidden;background:#0a0e0c;isolation:isolate;min-height:120px;
  background-image:repeating-radial-gradient(circle at 30% 120%,transparent 0 14px,rgba(255,255,255,.035) 14px 15px)}
.glow{position:absolute;inset:0;z-index:-1;background:radial-gradient(70% 55% at 50% 45%,color-mix(in srgb,var(--cc) 40%,transparent),transparent 70%)}
.art{position:absolute;inset:12% 6% 0;width:88%;height:93%;object-fit:contain;object-position:50% 100%;filter:drop-shadow(0 8px 14px rgba(0,0,0,.55))}
.art-none{position:absolute;inset:0;display:grid;place-items:center;text-align:center;padding:16px;color:var(--card-ink-2);font-size:12px}
.ribbon{position:absolute;top:8px;right:-30px;transform:rotate(35deg);background:var(--cc);color:#111;font:700 9.5px/1 var(--font-mono);letter-spacing:.14em;text-transform:uppercase;padding:4px 34px}
.plate{display:flex;justify-content:space-between;align-items:center;margin:7px 8px 0;padding:5px 8px;border-radius:4px;background:rgba(255,255,255,.06);font-size:12px;color:var(--card-ink-2)}
.pips{display:flex;gap:3px}.pips i{width:9px;height:9px;transform:rotate(45deg);border:1px solid var(--cc)}.pips i.on{background:var(--cc)}
.cstats{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:7px 8px 0}
.cs{background:rgba(255,255,255,.04);border-radius:4px;padding:4px 6px;display:grid}
.cs span{font:600 9px/1.2 var(--font-mono);letter-spacing:.12em;color:var(--card-ink-2)}.cs b{font:600 15px/1.2 var(--font-mono)}
.card-foot{display:flex;justify-content:space-between;padding:7px 10px 9px;font:500 9.5px/1 var(--font-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--card-ink-2)}
.foil{position:absolute;inset:0;border-radius:var(--r-card);pointer-events:none;mix-blend-mode:overlay;opacity:.55;
  background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.55) var(--fx,45%),transparent calc(var(--fx,45%) + 18%))}
a.card:hover{--lift:1}

/* console register */
.console{background:var(--sheet);border:1px solid var(--rule);border-radius:var(--r-2);padding:14px 16px;min-width:0}
.ch{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:-2px 0 12px;padding-bottom:9px;border-bottom:1px dashed var(--rule-2)}
.ch-r{font:500 11px/1 var(--font-mono);color:var(--ink-3)}
.seen{font:500 11px/1 var(--font-mono);color:var(--ink-3)}
.subj{display:grid;align-content:start;gap:4px}
.sname{font:800 var(--t-hero)/.95 var(--font-display);text-transform:uppercase;letter-spacing:.01em;margin:2px 0 0}
.sname::after{content:"";display:block;height:3px;width:64px;margin-top:10px;background:var(--c)}
.smeta{color:var(--ink-2);font-size:15px;margin-top:4px}
.subj-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.subj-id{min-width:0}
.roles{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.role{font:600 10px/1 var(--font-mono);letter-spacing:.12em;text-transform:uppercase;padding:4px 7px;border-radius:4px;border:1px solid var(--rule-2);color:var(--ink-2)}
.tm-unit{font:500 11px/1.2 var(--font-mono);color:var(--ink-3);margin-top:-2px}
.meter-lv{height:5px;margin-top:6px;flex:none}
.un{margin-top:16px;padding-top:12px;border-top:1px dashed var(--rule-2)}
.un-h{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.un-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:8px 18px;counter-reset:un}
.un-list li{display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:start;padding:8px 10px;border-radius:6px;background:var(--sheet-2);counter-increment:un}
.un-list li div{display:grid;gap:2px;font-size:13px;line-height:1.4}.un-list li b{font-weight:600;color:var(--ink)}.un-list li span{color:var(--ink-2)}
.un-k{font:700 9.5px/1 var(--font-mono);letter-spacing:.1em;text-transform:uppercase;padding:4px 6px;border-radius:3px;margin-top:2px;color:var(--ink-2);border:1px solid var(--rule-2);min-width:64px;text-align:center}
.un-k::before{content:counter(un) " ";color:var(--ink-3)}
.un-dungeon{color:var(--route);border-color:color-mix(in srgb,var(--route) 45%,transparent)}
.un-train,.un-quest{color:var(--c);border-color:color-mix(in srgb,var(--c) 45%,transparent)}
.un-errand{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.tms{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:16px}
.tm{background:var(--sheet-2);border-radius:6px;padding:9px 10px 6px;display:grid;gap:3px;min-width:0}
.tm b{font:600 24px/1.1 var(--font-mono);font-variant-numeric:tabular-nums}.tm b.sm{font-size:15px;line-height:1.6}
.tm-sub{font:500 11px/1.2 var(--font-mono);color:var(--ink-3)}
.spark{width:100%;height:26px;display:block}
.sp-line{fill:none;stroke:var(--c);stroke-width:1.8;stroke-linejoin:round}.sp-area{fill:color-mix(in srgb,var(--c) 16%,transparent)}
.sp-end{fill:var(--c);stroke:var(--sheet-2);stroke-width:1.5}.sp-flat{stroke:var(--rule-2);stroke-width:1.5;stroke-dasharray:3 3}
.vits{display:grid;gap:8px;width:min(100%,240px)}
.vit{background:var(--sheet-2);border-radius:6px;padding:8px 10px;display:grid;grid-template-columns:1fr auto;align-items:center;gap:2px 8px}
.vit b{font:600 18px/1 var(--font-mono)}.vit .bar{grid-column:1/-1;height:4px;border-radius:2px}
.bar.hp{background:var(--ok)}.bar.mp{background:#3b7ddd}
.lights{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.light{display:inline-flex;align-items:center;gap:7px;font-size:12px;padding:4px 9px 4px 7px;border-radius:999px;border:1px solid var(--rule);background:var(--sheet);min-width:0}
.light i{width:8px;height:8px;border-radius:50%;flex:none;background:var(--idle)}
.l-ok i{background:var(--ok)}.l-warn i{background:var(--warn);box-shadow:0 0 0 3px color-mix(in srgb,var(--warn) 22%,transparent)}
.l-bad i{background:var(--bad);box-shadow:0 0 0 3px color-mix(in srgb,var(--bad) 22%,transparent)}
.lw{font-weight:600}.ld{color:var(--ink-3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:240px}
.meter{position:relative;display:block;height:6px;border-radius:3px;background:var(--sheet-2);overflow:hidden;flex:1}
.meter>span{position:absolute;inset:0 auto 0 0;background:var(--c);border-radius:3px}
.meter-cap .cap{background:color-mix(in srgb,var(--c) 22%,transparent)!important}
.meter-rep>span{background:var(--rc)}
.meter-race{height:10px;border-radius:5px}.meter-race>span{border-radius:5px}

/* gear readout */
.grs{display:grid}
.gr{display:grid;grid-template-columns:40px 78px minmax(0,1fr) 120px 74px;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid var(--rule)}
.gr:last-child{border-bottom:0}
.gs{font:600 var(--t-micro)/1.2 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
.gn{font-weight:600;font-size:13px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gm{display:flex;align-items:center;gap:8px}.gm b{font:600 13px/1 var(--font-mono);min-width:22px;text-align:right}
.gr .light{border:0;padding:0;background:none;justify-self:start}
.ic{position:relative;display:block;width:36px;height:36px;border-radius:6px;border:2px solid var(--q-common);background:var(--sheet-2);overflow:hidden}
.ic img{width:100%;height:100%;display:block}.ic-sm{width:30px;height:30px;border-radius:5px}
.ic-empty{border:1px dashed var(--rule-2);background:transparent}
.q-poor{border-color:var(--q-poor);color:var(--q-poor)}.q-common{border-color:var(--q-common)}.q-uncommon{border-color:var(--q-uncommon);color:var(--q-uncommon)}
.q-rare{border-color:var(--q-rare);color:var(--q-rare)}.q-epic{border-color:var(--q-epic);color:var(--q-epic)}.q-legendary{border-color:var(--q-legendary);color:var(--q-legendary)}
.gn.q-common{color:var(--ink)}
.tip-host{position:relative;display:inline-block}
.tt{position:absolute;z-index:20;left:calc(100% + 8px);top:-4px;width:max-content;max-width:min(280px,70vw);padding:10px 12px;border-radius:var(--r-2);
  background:var(--sheet);border:1px solid var(--rule-2);box-shadow:0 14px 34px -10px rgba(0,0,0,.35);font-size:12px;line-height:1.5;color:var(--ink-2);
  opacity:0;visibility:hidden;transform:translateX(-3px);transition:opacity .12s,transform .12s;pointer-events:none}
.tip-host:hover .tt,.tip-host:focus-within .tt{opacity:1;visibility:visible;transform:none}
.tt-name{font-weight:700;font-size:13px}.tt-name.q-common{color:var(--ink)}
.tt-ilvl{font:600 10.5px/1.6 var(--font-mono);letter-spacing:.1em;color:var(--ink-3);border-bottom:1px dashed var(--rule-2);margin-bottom:4px;padding-bottom:3px}
.tt .eq{color:var(--ok)}.tt .bad{color:var(--bad)}.tt-link{margin-top:6px;font:500 10.5px/1 var(--font-mono);color:var(--route)}

/* stats, talents, professions, reps, log */
.rgs{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px 20px}
.rg .lbl{display:block;margin-bottom:5px}
.ro{display:flex;justify-content:space-between;gap:8px;padding:3px 0;border-bottom:1px dotted var(--rule-2);font-size:13px;color:var(--ink-2)}
.ro b{font:600 13px/1.5 var(--font-mono);color:var(--ink)}
.tbar{display:flex;gap:2px;height:10px;border-radius:5px;overflow:hidden;background:var(--sheet-2)}
.tlegend{display:flex;gap:14px;flex-wrap:wrap;margin:9px 0 10px;font-size:12px;color:var(--ink-2)}
.tl i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px;vertical-align:-1px}.tl b{font-family:var(--font-mono);color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{display:inline-flex;align-items:center;gap:7px;font-size:12px;padding:3px 3px 3px 8px;border-radius:5px;border:1px solid var(--rule);background:var(--sheet-2)}
.chip b{font:600 11px/1.4 var(--font-mono);padding:0 5px;border-radius:3px;background:var(--sheet);color:var(--ink)}
.pr{display:flex;gap:11px;align-items:center;padding:6px 0}
.pi{width:32px;height:32px;border-radius:6px;border:1px solid var(--rule-2);flex:none;background:var(--sheet-2)}
.pb{flex:1;min-width:0;display:grid;gap:5px}
.pt{display:flex;justify-content:space-between;gap:8px;font-size:13px;font-weight:600}.pt b{font:600 13px/1.4 var(--font-mono)}
.pr .light{border:0;padding:0;background:none}
.rps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 18px}
.rp{display:grid;gap:4px}.rp .pt{font-weight:500}.rs{font:700 10.5px/1.4 var(--font-mono)!important;letter-spacing:.06em;text-transform:uppercase;color:var(--rc)}
.rv{font:500 11px/1 var(--font-mono);color:var(--ink-3)}
ul.log{list-style:none;margin:0;padding:0}
ul.log li{display:grid;grid-template-columns:46px 1fr;gap:10px;font-size:13px;padding:5px 0;border-bottom:1px solid var(--rule);color:var(--ink-2)}
ul.log li:last-child{border-bottom:0}ul.log time{font:500 11.5px/1.6 var(--font-mono);color:var(--ink-3)}
.sub-lbl{display:block;margin:14px 0 4px}
.sw{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px;vertical-align:middle}
.cols{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:18px;align-items:start}
.col{display:grid;gap:18px;min-width:0}

/* survey register */
.survey{background:var(--sheet);border:1px solid var(--rule);border-radius:var(--r-2);padding:14px 16px 10px;min-width:0}
.sh{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:6px}.sh h2{font-size:var(--t-h2)}
.sh-r{margin-left:auto;font:500 11px/1.3 var(--font-mono);color:var(--ink-3)}
.mapwrap{overflow-x:auto;max-width:100%}.mapscroll{min-width:720px}
.map,.strip{display:block;width:100%;height:auto}
.ct{fill:none;stroke:var(--contour);stroke-width:1}.ct-i{stroke:var(--contour-2);stroke-width:1.6}
.lg{stroke:var(--rule-2);stroke-dasharray:2 5}.ll{font:600 11px var(--font-mono);fill:var(--ink-3);text-anchor:middle}
.route{fill:none;stroke:var(--route);stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
.route-ahead{fill:none;stroke:var(--ink-3);stroke-width:2;stroke-dasharray:6 7;stroke-linecap:round;opacity:.8}
.wp{fill:var(--sheet);stroke:var(--ink-2);stroke-width:2}.wp-past{fill:var(--route);stroke:var(--sheet)}
.wl{stroke:var(--ink-3);stroke-width:1;stroke-dasharray:2 2}.wt{font:600 11px var(--font-mono);fill:var(--ink);paint-order:stroke;stroke:var(--sheet);stroke-width:4px;stroke-linejoin:round}
.here{fill:var(--signal);stroke:var(--sheet);stroke-width:2.5}.here-ring{fill:color-mix(in srgb,var(--signal) 18%,transparent);stroke:var(--signal);stroke-width:1}
.here-t{font:700 12px var(--font-mono);fill:var(--signal);text-anchor:middle;letter-spacing:.1em}
.pin{fill:var(--c);stroke:var(--sheet);stroke-width:2.5}.pin-t{font:700 11.5px var(--font-mono);fill:var(--ink);text-anchor:middle;letter-spacing:.06em}
.strip{margin-top:4px}
.dg .dg-pill{fill:var(--sheet-2);stroke:var(--rule-2)}.dg text{font:600 12px var(--font-mono);fill:var(--ink-2)}.dg .dg-range{fill:var(--ink-3);opacity:.55}
.dg-done .dg-pill{fill:var(--route);stroke:none}.dg-done text{fill:var(--sheet)}.dg-done .dg-range{fill:var(--route);opacity:1}
.dg-now .dg-pill{fill:color-mix(in srgb,var(--c) 18%,var(--sheet));stroke:var(--c);stroke-width:1.5}.dg-now text{fill:var(--ink)}.dg-now .dg-range{fill:var(--c);opacity:1}
.dg-past{opacity:.55}

/* binder */
.binder{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:18px}
.slotcard{display:grid;gap:10px;justify-items:center;align-content:start}
.race-row{display:grid;grid-template-columns:150px minmax(0,1fr) 30px 170px;gap:12px;align-items:center;padding:6px 0}
.rn{font-weight:600}.race-row b{font:600 14px var(--font-mono);text-align:right}.rd{font-size:12px}

/* progress */
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));gap:18px}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;margin-bottom:8px;color:var(--ink-2);font-size:13px}
.chart{position:relative;width:100%;height:240px}.chart svg{display:block;width:100%;height:100%;overflow:visible}
.tick{fill:var(--ink-3);font:11px var(--font-mono)}.gridline{stroke:var(--rule);stroke-width:1}.baseline{stroke:var(--rule-2);stroke-width:1}
.endlabel{font:600 12px var(--font-mono);fill:var(--ink-2)}.cross{stroke:var(--rule-2);stroke-width:1}
.tip{position:absolute;pointer-events:none;background:var(--sheet);border:1px solid var(--rule-2);border-radius:6px;padding:6px 8px;font-size:12px;box-shadow:0 6px 18px rgba(0,0,0,.18);white-space:nowrap;display:none;z-index:2}
.empty{color:var(--ink-3);padding:22px 0;text-align:center}
details{margin-top:10px}summary{cursor:pointer;color:var(--ink-2);font-size:13px}
.tw{overflow-x:auto;max-width:100%}
table{border-collapse:collapse;font:12px var(--font-mono);margin-top:6px}th,td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--rule)}

@media (max-width:960px){.cols{grid-template-columns:minmax(0,1fr)}}
@media (max-width:760px){
  .hero{grid-template-columns:minmax(0,1fr)}.hero-card .card{max-width:260px}
  .tms{grid-template-columns:repeat(2,minmax(0,1fr));min-width:0}
  .gr{grid-template-columns:36px minmax(0,1fr) 70px;grid-template-areas:"i n m" "i s l";row-gap:2px}
  .gr>.tip-host,.gr>.ic{grid-area:i}.gr .gn{grid-area:n}.gr .gs{grid-area:s}.gr .gm{grid-area:m}.gr>.light{grid-area:l;justify-self:end}
  .gm .meter{display:none}
  .rps{grid-template-columns:minmax(0,1fr)}
  .race-row{grid-template-columns:100px minmax(0,1fr) 28px}.rd{display:none}
  .tt{left:auto;right:auto;left:0;top:calc(100% + 6px)}
}
@media (prefers-reduced-motion:reduce){.card{transition:none;transform:none!important}.tt{transition:none}}
"""

JS_EXTRA = r"""
/* tabs, routed on the hash */
const views=[...document.querySelectorAll('.view')],tabs=[...document.querySelectorAll('.tab')];
function show(id){if(!views.some(v=>v.dataset.view===id))id=document.querySelector('.app').dataset.start;
  views.forEach(v=>v.hidden=v.dataset.view!==id);tabs.forEach(t=>t.setAttribute('aria-selected',t.dataset.target===id&&!t.dataset.scroll));
  scrollTo({top:0})}
document.querySelectorAll('[data-target],[data-goto]').forEach(t=>t.addEventListener('click',e=>{const id=t.dataset.target||t.dataset.goto;e.preventDefault();
  history.replaceState(null,'','#'+id);show(id);if(t.dataset.scroll){tabs.forEach(x=>x.setAttribute('aria-selected',x===t));
  document.getElementById(t.dataset.scroll)?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})}}));
addEventListener('hashchange',()=>show(location.hash.slice(1)));
show(location.hash.slice(1)||document.querySelector('.app').dataset.start);

/* trim the empty transparent margin around each render so every race fills its card */
function crop(img){try{const w=160,h=Math.round(img.naturalHeight/img.naturalWidth*w)||120,c=document.createElement('canvas');c.width=w;c.height=h;
  const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(img,0,0,w,h);const d=x.getImageData(0,0,w,h).data;
  let x0=w,y0=h,x1=0,y1=0;for(let y=0;y<h;y++)for(let i=0;i<w;i++)if(d[(y*w+i)*4+3]>16){if(i<x0)x0=i;if(i>x1)x1=i;if(y<y0)y0=y;if(y>y1)y1=y}
  if(x1<=x0||y1<=y0)return;const s=img.naturalWidth/w,p=5;const sx=Math.max(0,(x0-p)*s),sy=Math.max(0,(y0-p)*s),
  sw=Math.min(img.naturalWidth-sx,(x1-x0+2*p)*s),sh=Math.min(img.naturalHeight-sy,(y1-y0+2*p)*s);
  const o=document.createElement('canvas');o.width=Math.round(sw);o.height=Math.round(sh);o.getContext('2d').drawImage(img,sx,sy,sw,sh,0,0,o.width,o.height);
  img.removeAttribute('data-crop');img.src=o.toDataURL('image/png')}catch(e){}}
document.querySelectorAll('img[data-crop]').forEach(i=>i.complete?crop(i):i.addEventListener('load',()=>crop(i),{once:true}));

/* cards tilt toward the pointer; the foil streak follows */
if(!matchMedia('(prefers-reduced-motion: reduce)').matches)document.querySelectorAll('.card').forEach(c=>{
  c.addEventListener('pointermove',e=>{const r=c.getBoundingClientRect(),px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;
    c.style.setProperty('--rx',((px-.5)*10).toFixed(2)+'deg');c.style.setProperty('--ry',((.5-py)*10).toFixed(2)+'deg');c.style.setProperty('--fx',(px*100).toFixed(0)+'%')});
  c.addEventListener('pointerleave',()=>{c.style.setProperty('--rx','0deg');c.style.setProperty('--ry','0deg')})});

/* card backdrops: per character, remembered in this browser only */
function setScene(slug,k,save){document.querySelectorAll(`.card[data-slug="${slug}"] .window`).forEach(w=>w.dataset.bg=k);
  document.querySelectorAll(`.scenes[data-slug="${slug}"] .sc-b`).forEach(b=>b.setAttribute('aria-pressed',b.dataset.scene===k));
  if(save)try{localStorage.setItem('waypoint-scene-'+slug,k)}catch(e){}}
document.querySelectorAll('.scenes').forEach(g=>{const slug=g.dataset.slug;let k=null;try{k=localStorage.getItem('waypoint-scene-'+slug)}catch(e){}
  if(k&&g.querySelector(`[data-scene="${k}"]`))setScene(slug,k,false);
  g.querySelectorAll('.sc-b').forEach(b=>b.addEventListener('click',()=>setScene(slug,b.dataset.scene,true)))});

/* journal: one book at a time; chapter links scroll inside the book */
document.querySelectorAll('.jpick').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.jpick').forEach(x=>x.setAttribute('aria-pressed',x===b));
  document.querySelectorAll('.jbook').forEach(j=>j.hidden=j.dataset.book!==b.dataset.book)}));
document.querySelectorAll('.jbook').forEach((j,i)=>j.hidden=i>0);
document.querySelectorAll('[data-jump]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const el=document.getElementById(a.dataset.jump);
  if(el){const box=el.closest('.jpages');box.scrollTo({top:el.offsetTop-box.offsetTop,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}}));

/* save a card as a PNG (html-to-image from cdnjs, loaded on first use) */
const H2I='https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js';
/* web fonts for the exported image: fetch the Google Fonts CSS and inline its font files (both send CORS headers) */
let fontCSS;async function embedFonts(){if(fontCSS!==undefined)return fontCSS;fontCSS='';
  try{const link=document.querySelector('link[href*="fonts.googleapis.com/css"]');if(!link)return fontCSS;
    let css=await (await fetch(link.href)).text();const urls=[...new Set([...css.matchAll(/url\((https:[^)]+)\)/g)].map(m=>m[1]))];
    await Promise.all(urls.map(async u=>{const b=await (await fetch(u)).blob();const d=await new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)});css=css.split(u).join(d)}));
    fontCSS=css}catch(e){fontCSS=''}return fontCSS}
let h2i;function loadH2I(){return h2i||(h2i=new Promise((ok,no)=>{const s=document.createElement('script');s.src=H2I;s.onload=()=>ok(window.htmlToImage);s.onerror=no;document.head.appendChild(s)}))}
function shot(src,name){const o=document.createElement('div');o.className='shot';o.innerHTML=`<div class="shot-in" role="dialog" aria-label="Card image"><img alt="Card image" src="${src}">
  <div class="shot-row"><a href="${src}" download="${name}">Download PNG</a><button type="button">Close</button></div>
  <p>If the download button does nothing (for example on a shared page), right-click or long-press the image and save it.</p></div>`;
  const close=()=>o.remove();o.querySelector('button').onclick=close;o.addEventListener('click',e=>{if(e.target===o)close()});
  addEventListener('keydown',function k(e){if(e.key==='Escape'){close();removeEventListener('keydown',k)}});document.body.appendChild(o);o.querySelector('a').focus()}
document.querySelectorAll('.card-save').forEach(b=>b.addEventListener('click',async e=>{e.preventDefault();e.stopPropagation();const card=b.closest('.card');if(!card)return;
  const label=b.getAttribute('aria-label');b.disabled=true;b.classList.remove('err');b.setAttribute('aria-label','Rendering card image');
  try{const [lib,fonts]=await Promise.all([loadH2I(),embedFonts()]);
    const png=await lib.toPng(card,{pixelRatio:2,cacheBust:false,style:{transform:'none'},fontEmbedCSS:fonts||undefined,skipFonts:!fonts,filter:n=>!(n.classList&&n.classList.contains('card-save'))});
    shot(png,b.dataset.slug+'-card.png')}
  catch(err){b.classList.add('err');b.title="Couldn't render the image. Click to try again"}
  b.disabled=false;b.setAttribute('aria-label',label)}));

/* relative "seen" */
document.querySelectorAll('.seen[data-ts]').forEach(s=>{const t=Date.parse(s.dataset.ts);if(!t)return;const m=(Date.now()-t)/6e4;
  s.textContent='seen '+(m<60?Math.max(1,Math.round(m))+'m ago':m<2880?Math.round(m/60)+'h ago':Math.round(m/1440)+'d ago')});
"""


def chart_payload(chars):
    keys = ("slug", "first", "watch", "slot", "level", "points", "questDays")
    return [{k: c[k] for k in keys} for c in chars]


def chart_js():
    """Line and bar chart code shared with the previous dashboard (tokens renamed)."""
    return CHART_JS


CHART_JS = r"""
const D=JSON.parse(document.getElementById('data').textContent);
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS='http://www.w3.org/2000/svg';
const el=(t,a={},p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e};
const fmtD=t=>new Date(t).toLocaleDateString(undefined,{month:'short',day:'numeric'});
document.querySelectorAll('[data-legend]').forEach(l=>{if(D.length<2){l.remove();return}
  l.innerHTML=D.map(c=>`<span><span class="sw" style="background:var(--s${c.slot+1})"></span>${c.first}${c.watch?' (friend)':''}</span>`).join('')});
function ticks(lo,hi,n){const s=Math.max(1,Math.ceil((hi-lo)/n));const out=[];for(let v=Math.ceil(lo/s)*s;v<=hi;v+=s)out.push(v);return out}
function line(div){
  const key=div.dataset.key,unit=div.dataset.unit;div.innerHTML='';
  const W=div.clientWidth,H=div.clientHeight;if(!W)return;const m={l:34,r:D.length<=4?92:12,t:10,b:24};
  const S=D.filter(c=>c.points.some(p=>p[key]!=null));
  const ts=S.flatMap(c=>c.points.map(p=>+new Date(p.t)));let t0=Math.min(...ts),t1=Math.max(...ts);if(t1-t0<864e5){t0-=432e5;t1+=432e5}
  const vs=S.flatMap(c=>c.points.map(p=>p[key]).filter(v=>v!=null));const v0=Math.floor(Math.min(...vs))-1,v1=Math.ceil(Math.max(...vs))+1;
  const x=t=>m.l+(t-t0)/(t1-t0)*(W-m.l-m.r),y=v=>H-m.b-(v-v0)/(v1-v0)*(H-m.t-m.b);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':unit+' over time'},div);
  for(const v of ticks(v0,v1,5)){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),class:'gridline'},svg);el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end',class:'tick'},svg).textContent=v}
  el('line',{x1:m.l,x2:W-m.r,y1:H-m.b,y2:H-m.b,class:'baseline'},svg);
  const days=Math.max(1,Math.round((t1-t0)/864e5)),step=Math.max(1,Math.ceil(days/Math.max(2,Math.floor((W-m.l-m.r)/80))));
  for(let t=t0;t<=t1+1;t+=step*864e5){el('text',{x:x(t),y:H-6,'text-anchor':'middle',class:'tick'},svg).textContent=fmtD(t)}
  const ends=[];
  for(const c of S){const P=c.points.filter(p=>p[key]!=null);const col=`var(--s${c.slot+1})`;
    let d=`M${x(+new Date(P[0].t))},${y(P[0][key])}`;for(let i=1;i<P.length;i++){d+=`H${x(+new Date(P[i].t))}V${y(P[i][key])}`}d+=`H${x(t1)}`;
    el('path',{d,fill:'none',stroke:col,'stroke-width':2,'stroke-linejoin':'round'},svg);
    for(const p of P)el('circle',{cx:x(+new Date(p.t)),cy:y(p[key]),r:4,fill:col,stroke:css('--sheet'),'stroke-width':2},svg);
    ends.push({c,y:y(P[P.length-1][key]),v:P[P.length-1][key]})}
  if(D.length<=4){ends.sort((a,b)=>a.y-b.y);for(let i=1;i<ends.length;i++)if(ends[i].y-ends[i-1].y<14)ends[i].y=ends[i-1].y+14;
    for(const e of ends)el('text',{x:x(t1)+8,y:e.y+4,class:'endlabel'},svg).textContent=`${e.c.first} ${e.v}`}
  const cross=el('line',{y1:m.t,y2:H-m.b,class:'cross',visibility:'hidden'},svg);
  const tip=document.createElement('div');tip.className='tip';div.appendChild(tip);
  const hit=el('rect',{x:m.l,y:0,width:W-m.l-m.r,height:H,fill:'transparent'},svg);
  const move=ev=>{const r=svg.getBoundingClientRect(),px=ev.clientX-r.left;const t=t0+(px-m.l)/(W-m.l-m.r)*(t1-t0);if(t<t0||t>t1)return hide();
    cross.setAttribute('x1',px);cross.setAttribute('x2',px);cross.setAttribute('visibility','visible');
    const rows=S.map(c=>{const P=c.points.filter(p=>p[key]!=null&&+new Date(p.t)<=t);return P.length?`<div><span class="sw" style="background:var(--s${c.slot+1})"></span>${c.first}: <b>${P[P.length-1][key]}</b></div>`:''}).join('');
    tip.innerHTML=`<div class="muted">${fmtD(t)}</div>${rows}`;tip.style.display='block';const tw=tip.offsetWidth;tip.style.left=Math.min(W-tw,Math.max(0,px+12))+'px';tip.style.top='8px'};
  const hide=()=>{tip.style.display='none';cross.setAttribute('visibility','hidden')};
  hit.addEventListener('pointermove',move);hit.addEventListener('pointerleave',hide)}
function bars(div){div.innerHTML='';const W=div.clientWidth,H=div.clientHeight;if(!W)return;const m={l:34,r:12,t:10,b:24};
  const dates=[...new Set(D.flatMap(c=>Object.keys(c.questDays)))].sort().slice(-14);const vmax=Math.max(1,...D.flatMap(c=>dates.map(d=>c.questDays[d]||0)));
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'quests per day'},div);const y=v=>H-m.b-v/vmax*(H-m.t-m.b);
  for(const v of ticks(0,vmax,4)){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),class:'gridline'},svg);el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end',class:'tick'},svg).textContent=v}
  el('line',{x1:m.l,x2:W-m.r,y1:H-m.b,y2:H-m.b,class:'baseline'},svg);
  const band=(W-m.l-m.r)/dates.length,bw=Math.max(3,Math.min(24,(band*0.7-2*(D.length-1))/D.length));
  const tip=document.createElement('div');tip.className='tip';div.appendChild(tip);
  dates.forEach((d,i)=>{const gx=m.l+i*band+(band-(bw*D.length+2*(D.length-1)))/2;
    el('text',{x:m.l+i*band+band/2,y:H-6,'text-anchor':'middle',class:'tick'},svg).textContent=fmtD(d+'T12:00:00');
    D.forEach((c,j)=>{const v=c.questDays[d]||0;if(!v)return;const bx=gx+j*(bw+2),by=y(v),bh=H-m.b-by,r=Math.min(4,bw/2,bh);
      el('path',{d:`M${bx},${H-m.b}V${by+r}Q${bx},${by} ${bx+r},${by}H${bx+bw-r}Q${bx+bw},${by} ${bx+bw},${by+r}V${H-m.b}Z`,fill:`var(--s${c.slot+1})`},svg);
      const h=el('rect',{x:bx-3,y:Math.min(by,H-m.b-16),width:bw+6,height:Math.max(bh,16),fill:'transparent'},svg);
      h.addEventListener('pointerenter',()=>{tip.innerHTML=`<div class="muted">${fmtD(d+'T12:00:00')}</div><span class="sw" style="background:var(--s${c.slot+1})"></span>${c.first}: <b>${v}</b> quests`;tip.style.display='block';tip.style.left=Math.min(W-tip.offsetWidth,bx+bw+6)+'px';tip.style.top=Math.max(0,by-10)+'px'});
      h.addEventListener('pointerleave',()=>tip.style.display='none')})})}
function draw(){document.querySelectorAll('.chart[data-key]').forEach(line);document.querySelectorAll('.chart[data-bars]').forEach(bars)}
let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(draw,150)});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
"""


# ---------- card backdrops: the class glow, plus photos from photo_scenes() ----------

SCENES = [  # drawn scenes; photo backdrops come from photo_scenes()
    ("glow", "Class glow", "radial-gradient(70% 55% at 50% 45%, color-mix(in srgb, var(--cc) 40%, transparent), transparent 70%), #0a0e0c"),
]
PHOTOS = []  # set per render by photo_scenes()
DEFAULT_SCENE = {}  # class -> scene key; every class starts on the class glow


PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic")
PHOTO_W, PHOTO_H = 640, 512  # 2x the card's art window, which is about 5:4


def photo_dirs():
    """Shipped backdrops (design/backdrops, original art only) and your own (notes/backdrops, never committed)."""
    return [core.KIT / "design" / "backdrops", core.ROOT / "notes" / "backdrops"]


def optimize_photo(src):
    """Crop to the card window and save a small JPEG once, in notes/cache/backdrops. Uses macOS sips or Pillow."""
    import hashlib
    import shutil
    import subprocess
    st = src.stat()
    key = hashlib.sha1(f"{src.resolve()}:{st.st_mtime_ns}:{st.st_size}".encode()).hexdigest()[:16]
    out = wowhead.cache_dir("backdrops") / f"{key}.jpg"
    if out.exists():
        return out.read_bytes()
    try:
        from PIL import Image  # optional
        with Image.open(src) as im:
            im = im.convert("RGB")
            s = max(PHOTO_W / im.width, PHOTO_H / im.height)
            im = im.resize((max(PHOTO_W, round(im.width * s)), max(PHOTO_H, round(im.height * s))))
            l, tp = (im.width - PHOTO_W) // 2, (im.height - PHOTO_H) // 2
            im.crop((l, tp, l + PHOTO_W, tp + PHOTO_H)).save(out, "JPEG", quality=72, optimize=True, progressive=True)
            return out.read_bytes()
    except ImportError:
        pass
    except Exception:
        return None
    if shutil.which("sips"):
        try:
            dims = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(src)], capture_output=True, text=True, timeout=20).stdout
            w, h = (int(x.split(":")[1]) for x in dims.strip().splitlines()[1:3])
            s = max(PHOTO_W / w, PHOTO_H / h)
            rw, rh = max(PHOTO_W, round(w * s)), max(PHOTO_H, round(h * s))
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72", "-z", str(rh), str(rw), str(src), "--out", str(out)],
                           capture_output=True, timeout=30, check=True)
            subprocess.run(["sips", "-c", str(PHOTO_H), str(PHOTO_W), str(out)], capture_output=True, timeout=30, check=True)
            return out.read_bytes()
        except Exception:
            out.unlink(missing_ok=True)
            return None
    return src.read_bytes() if src.suffix.lower() in (".jpg", ".jpeg") and src.stat().st_size < 400_000 else None


def photo_scenes():
    """[(key, name, data_uri)] for every backdrop image found; the name comes from the file name."""
    seen, out = set(), []
    for d in photo_dirs():
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in PHOTO_EXT or f.name.startswith("."):
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")[:40] or "photo"
            key = f"photo-{slug}"
            if key in seen:
                continue
            data = optimize_photo(f)
            if not data:
                continue
            seen.add(key)
            name = re.sub(r"[-_]+", " ", f.stem).strip().capitalize()
            out.append((key, name, wowhead.data_uri(data, "jpg")))
    return out


def scene_picker(ch, photos=()):
    sel = DEFAULT_SCENE.get(ch["class"], "glow")
    opts = [(k, n) for k, n, _ in SCENES] + [(k, n) for k, n, _ in photos]
    btns = "".join(f"<button type='button' class='sc-b{' sc-photo' if k.startswith('photo-') else ''}' data-scene='{k}' aria-label='Card background: {esc(n)}' title='{esc(n)}' aria-pressed='{str(k == sel).lower()}'>"
                   f"<span class='sc-sw' data-bg='{k}'></span></button>" for k, n in opts)
    return (f"<div class='scenes' data-slug='{esc(ch['slug'])}' role='group' aria-label='Card background'><span class='lbl'>Backdrop</span>"
            f"<div class='sc-row'>{btns}</div></div>")


def photos_css(photos):
    roots = "".join(f"--{k}:url({uri});" for k, _, uri in photos)
    rules = "".join(f".window[data-bg='{k}']{{background:linear-gradient(180deg,rgba(0,0,0,.08) 35%,rgba(0,0,0,.6)),var(--{k}) center/cover}}"
                    f".sc-sw[data-bg='{k}']{{background:var(--{k}) center/cover}}" for k, _, _ in photos)
    return (f":root{{{roots}}}" + rules) if photos else ""


SCENES_CSS = "".join(f".window[data-bg='{k}'],.sc-sw[data-bg='{k}']{{background:{bg};background-size:cover;background-position:center bottom}}" for k, _, bg in SCENES) + """
.window[data-bg]:not([data-bg='glow']) .glow{opacity:.35}
.scenes{display:grid;justify-items:center;gap:6px}
.sc-row{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.sc-b{padding:2px;border-radius:50%;border:2px solid transparent;background:none;cursor:pointer;line-height:0}
.sc-b[aria-pressed='true']{border-color:var(--ink)}
.card-save{flex:none;display:grid;place-items:center;width:26px;height:26px;margin-left:2px;border-radius:50%;border:1px solid rgba(255,255,255,.2);
  background:rgba(255,255,255,.07);color:var(--card-ink);cursor:pointer;padding:0;transition:background .15s,border-color .15s}
.card-save:hover{background:color-mix(in srgb,var(--cc) 35%,transparent);border-color:var(--cc)}
.card-save svg{width:14px;height:14px}.card-save[disabled]{opacity:.55;cursor:progress}.card-save.err{border-color:#ef5b49}
.shot{position:fixed;inset:0;z-index:30;display:grid;place-items:center;background:rgba(5,8,7,.72);padding:max(16px,env(safe-area-inset-top,0px)) 16px}
.shot-in{background:var(--sheet);border-radius:12px;padding:16px;display:grid;gap:12px;justify-items:center;max-width:min(92vw,460px);max-height:92vh;overflow:auto}
.shot-in img{max-width:100%;max-height:62vh;border-radius:10px}.shot-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
.shot-in p{margin:0;font-size:12px;color:var(--ink-3);text-align:center;max-width:40ch}
.shot-row a,.shot-row button{font:600 12px var(--font-mono);text-transform:uppercase;letter-spacing:.06em;padding:8px 14px;border-radius:6px;border:1px solid var(--rule-2);background:var(--sheet-2);color:var(--ink);text-decoration:none;cursor:pointer}
.shot-row a{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.sc-sw{display:block;width:24px;height:24px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)}
"""


def tab_avatar(c):
    if c["avatar"]:
        return f"<img class='av' src='{c['avatar']}' alt=''>"
    return ""


def render(group=None, fragment=False):
    """Full HTML document, or (fragment=True) the body-level page an Artifact publish wraps in its own skeleton."""
    chars = collect(group)
    n = datetime.now()
    gen = f"{n:%b} {n.day} · {n:%H:%M}"
    tokens = TOKENS.read_text() if TOKENS.exists() else ""
    page = (PAGE_CSS.replace("%LIGHT_S%", ";".join(f"--s{i + 1}:{c}" for i, c in enumerate(LIGHT)))
                    .replace("%DARK_S%", ";".join(f"--s{i + 1}:{c}" for i, c in enumerate(DARK))))
    # series colors: light on bare :root, dark in the dark blocks (the first bare-root DARK line is dropped)
    page = page.replace(":root{" + ";".join(f"--s{i + 1}:{c}" for i, c in enumerate(DARK)) + "}\n", "", 1)
    progress.enrich(chars)
    global PHOTOS
    PHOTOS = photo_scenes()
    payload = json.dumps(chart_payload(chars)).replace("</", "<\\/")
    mine = [c for c in chars if not c["watch"]]
    friends = [c for c in chars if c["watch"]]
    if not chars:
        tabs_html, views, start = "", "<div class='view' data-view='none'><div class='console empty'>No tracked characters yet. Run /wow-init.</div></div>", "none"
    else:
        start = next((c["slug"] for c in mine if c["main"]), (mine or chars)[0]["slug"])
        def person(c):
            last = c["name"][len(c["first"]):].strip()
            sub_name = f"<span class='tn-l'>{esc(last)}</span>" if last else ""
            return (f"<a class='tab' href='#{esc(c['slug'])}' data-target='{esc(c['slug'])}' style='{cvars(c)}'>"
                    f"{tab_avatar(c)}<span class='tn'><span class='tn-f'>{esc(c['first'])}</span>{sub_name}</span><span class='lv'>{c['level']}</span></a>")
        groups = [("Heroes", "".join(person(c) for c in mine))]
        groups.append(("Friends", "<a class='tab tab-sub' href='#friends' data-target='friends'><span class='tn'>All friends</span>"
                                  f"<span class='lv'>{len(friends)}</span></a>" + "".join(person(c) for c in friends)))
        groups.append(("Progress", "".join(
            f"<a class='tab tab-sub' href='#{k}' data-target='{k}'><span class='tn'>{n}</span></a>" for k, n, _ in progress.PAGES)))
        tabs_html = "".join(f"<div class='ng'><div class='lbl ng-h'>{g}</div><div class='ng-items'>{items}</div></div>" for g, items in groups)
        views = "".join(character_view(c) for c in mine + friends) + binder_view(chars) + progress.views(chars)
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap">')
    head = (f'<title>Waypoint Field Log</title><meta name="claude:viewport-fit-sides" content="cover">\n{fonts}\n'
            f'<style>{tokens}\n{page}{progress.CSS}{SCENES_CSS}{photos_css(PHOTOS)}</style>')
    app = (f'<div class="app" data-start="{esc(start)}"><div class="shell"><aside class="side"><div class="side-in"><span class="brand"><i></i>Waypoint</span>\n'
           f'<nav class="nav" aria-label="Views">{tabs_html}</nav><span class="gen">Updated {esc(gen)}</span></div></aside>\n'
           f'<main class="main">{views}</main></div></div><script id="data" type="application/json">{payload}</script><script>{JS_EXTRA}</script>')
    if fragment:
        return f"{head}\n{app}"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f"{head}</head><body>{app}</body></html>")


def write(out=None, group=None, fragment=False):
    path = out or (core.BASE / ("waypoint-artifact.html" if fragment else "dashboard.html"))
    core.write_text(path, render(group, fragment))
    return path
