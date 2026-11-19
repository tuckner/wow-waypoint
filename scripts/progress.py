"""Progress page for the dashboard (Waypoint system): one page of boxes, all server-rendered SVG.

History comes from three places, so the page has something to show from day one:
- journal.md chapter headers  (`_Nov 13 · levels 1 → ~10 · ..._`) give dated level ranges before tracking began
- history.jsonl snapshots     give exact level, item level and quests from tracking on
- activity.md lines           give a dated count of what happened each day (from chat)
"""
import html
import re
from datetime import date, datetime, timedelta

import core

MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
CHAPTER = re.compile(r"^##\s+([IVXLC]+)\.\s+(.+)$")
ARROW = r"\s*(?:→|->|–|-)\s*"
CH_META = re.compile(r"^_~?([A-Z][a-z]{2})\s+(\d{1,2})(?:" + ARROW + r"(\d{1,2}))?\s*·\s*levels?\s*~?(\d+)(?:" + ARROW + r"~?(\d+))?\s*(?:·\s*(.+?))?_\s*$")
ACT = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} (.+)$")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def series(c):
    return f"var(--s{c['slot'] + 1})"


# ---------- history ----------

def journal(slug, today=None):
    """Parse journal.md into chapters (num, title, meta, day, lo, hi, body lines) and the closing 'where things stand' lines."""
    p = core.BASE / slug / "journal.md"
    if not p.exists():
        return [], []
    today = today or date.today()
    chapters, closing, cur, after_rule = [], [], None, False
    for line in p.read_text().splitlines():
        if line.startswith("<!--"):
            continue
        if m := CHAPTER.match(line):
            cur = {"num": m.group(1), "title": m.group(2).strip(), "body": [], "meta": ""}
            chapters.append(cur)
            after_rule = False
            continue
        if line.strip() == "---":
            if chapters:
                after_rule, cur = True, None
            continue
        if after_rule:
            if line.strip():
                closing.append(line.strip())
            continue
        if cur is None:
            continue
        if not cur["meta"] and (m := CH_META.match(line.strip())):
            mon = MONTHS.get(m.group(1))
            day = int(m.group(3) or m.group(2))
            if mon:
                year = today.year - (1 if mon > today.month else 0)
                lo = int(m.group(4))
                cur.update(day=date(year, mon, day), start=date(year, mon, int(m.group(2))), lo=lo, hi=int(m.group(5) or lo),
                           stage=(m.group(6) or "").strip())
            cur["meta"] = line.strip().strip("_")
            continue
        cur["body"].append(line)
    return chapters, closing


def journal_chapters(slug, today=None):
    return [c for c in journal(slug, today)[0] if "day" in c]


def activity_days(slug):
    p = core.BASE / slug / "activity.md"
    days = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if (m := ACT.match(line)) and not m.group(2).lstrip().startswith("?"):
                d = date.fromisoformat(m.group(1))
                days[d] = days.get(d, 0) + 1
    return days


def level_points(c):
    """(date, level, source) per day: journal chapters first, snapshots override on the same day."""
    pts = {}
    for i, ch in enumerate(c.get("chapters", [])):
        if i == 0 and ch["start"] < ch["day"]:
            pts.setdefault(ch["start"], (ch["start"], ch["lo"], "journal"))
        old = pts.get(ch["day"])
        if not old or old[1] < ch["hi"]:
            pts[ch["day"]] = (ch["day"], ch["hi"], "journal")
    for p in c["points"]:
        d = core.parse_time(p["t"]).astimezone().date()
        pts[d] = (d, p["level"], "snapshot")
    return [pts[d] for d in sorted(pts)]


def enrich(chars):
    today = date.today()
    for c in chars:
        c["chapters"] = journal_chapters(c["slug"], today) if not c["watch"] else []
        c["actDays"] = activity_days(c["slug"]) if not c["watch"] else {}
        c["levelPts"] = level_points(c)
        c["rate"] = recent_rate(c["levelPts"])
    return chars


def recent_rate(pts, window=4):
    """Levels per day over the last `window` days of points (None if flat or unknown)."""
    if len(pts) < 2:
        return None
    last = pts[-1]
    first = next((p for p in pts if (last[0] - p[0]).days <= window), pts[0])
    if first is last:
        first = pts[-2]
    days = max(1, (last[0] - first[0]).days)
    r = (last[1] - first[1]) / days
    return r if r > 0 else None


# ---------- boxes ----------

def box(sid, label, title, body, aside=""):
    a = f"<span class='ch-r'>{aside}</span>" if aside else ""
    return (f"<section class='console pbox' id='{sid}'><header class='ch'><span class='lbl'>{esc(label)}</span>{a}</header>"
            f"<h3 class='pbox-h'>{esc(title)}</h3>{body}</section>")


def board(chars):
    rows = []
    for c in sorted(chars, key=lambda c: (-c["level"], -(c["quests"] or 0))):
        r = c["rate"]
        eta = "level 60" if c["level"] >= 60 else (f"~{(60 - c['level']) / r:.0f} days" if r else "–")
        rate = f"{r:.1f}" if r else "–"
        av = f"<img class='av' src='{c['avatar']}' alt=''>" if c.get("avatar") else "<span class='av'></span>"
        tag = "<span class='tag'>friend</span>" if c["watch"] else ""
        rows.append(
            f"<div class='bd-row' style='--cc:{c['colors'][0]};--ccl:{c['colors'][1]}'>{av}"
            f"<span class='bd-name'><b>{esc(c['name'])}</b>{tag}<span class='muted'>{esc(c['race'])} {esc(c['class'])}</span></span>"
            f"<span class='bd-lv'><b>{c['level']}</b><span class='meter meter-race'><span style='width:{c['level'] / 60 * 100:.1f}%'></span></span></span>"
            f"<span class='bd-n'><span class='lbl'>lv/day</span><b>{rate}</b></span>"
            f"<span class='bd-n'><span class='lbl'>to 60</span><b>{esc(eta)}</b></span>"
            f"<span class='bd-n'><span class='lbl'>ilvl</span><b>{esc(c['ilvl'])}</b></span>"
            f"<span class='bd-n'><span class='lbl'>quests</span><b>{esc(c['quests'])}</b></span></div>")
    recs = []
    if chars:
        top = max(chars, key=lambda c: c["level"])
        recs.append(("Highest", f"{top['first']} · {top['level']}"))
        q = max(chars, key=lambda c: c["quests"] or 0)
        recs.append(("Most quests", f"{q['first']} · {q['quests']}"))
        g = max(chars, key=lambda c: c["ilvl"] or 0)
        recs.append(("Best geared", f"{g['first']} · ilvl {g['ilvl']}"))
        fast = [c for c in chars if c["rate"]]
        if fast:
            f = max(fast, key=lambda c: c["rate"])
            recs.append(("Fastest climb", f"{f['first']} · {f['rate']:.1f} lv/day"))
        prof = max(chars, key=lambda c: sum(p.get("skill") or 0 for p in c["profs"]))
        recs.append(("Most crafted", f"{prof['first']} · {sum(p.get('skill') or 0 for p in prof['profs'])} skill"))
    rec = "".join(f"<div class='rec'><span class='lbl'>{esc(k)}</span><b>{esc(v)}</b></div>" for k, v in recs)
    return box("sec-board", "Overview", "Standings", f"<div class='recs'>{rec}</div><div class='bd'>{''.join(rows)}</div>")


def elevation(chars):
    """Level over time as terrain: area under each line, journal chapters as flags, a dashed projection to 60."""
    W, H, L, R, T, B = 1000, 340, 44, 120, 16, 30
    all_pts = [p for c in chars for p in c["levelPts"]]
    if not all_pts:
        return box("sec-level", "Survey", "Elevation", "<div class='empty'>Not enough history yet.</div>")
    d0 = min(p[0] for p in all_pts) - timedelta(days=1)
    today = date.today()
    proj_days = 0
    for c in chars:
        if c["rate"] and c["level"] < 60:
            proj_days = max(proj_days, min(14, (60 - c["level"]) / c["rate"]))
    d1 = today + timedelta(days=max(2, round(proj_days)))
    span = max(1, (d1 - d0).days)

    def x(d):
        return L + (d - d0).days / span * (W - L - R)

    def y(lv):
        return H - B - lv / 60 * (H - T - B)

    g = []
    for lv in range(0, 61, 10):
        cls = "ct-i" if lv in (0, 60) else "ct"
        g.append(f"<line class='{cls}' x1='{L}' x2='{W - R}' y1='{y(lv):.1f}' y2='{y(lv):.1f}'/><text class='ll' x='{L - 8}' y='{y(lv) + 4:.1f}' text-anchor='end'>{lv}</text>")
    for lv in range(5, 60, 10):
        g.append(f"<line class='ct ct-m' x1='{L}' x2='{W - R}' y1='{y(lv):.1f}' y2='{y(lv):.1f}'/>")
    step = max(1, span // 10)
    d = d0
    while d <= d1:
        g.append(f"<text class='ll' x='{x(d):.1f}' y='{H - 8}'>{d:%b} {d.day}</text>")
        d += timedelta(days=step)
    g.append(f"<line class='today' x1='{x(today):.1f}' x2='{x(today):.1f}' y1='{T}' y2='{H - B}'/><text class='today-t' x='{x(today) + 4:.1f}' y='{T + 10}'>TODAY</text>")

    layers, lines, flags, ends = [], [], [], []
    for c in sorted(chars, key=lambda c: -c["level"]):
        P = c["levelPts"]
        col = series(c)
        pts = [(x(p[0]), y(p[1])) for p in P]
        if len(pts) == 1:
            pts = [(pts[0][0] - 6, pts[0][1]), pts[0]]
        path = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        layers.append(f"<path d='{path} L{pts[-1][0]:.1f},{H - B} L{pts[0][0]:.1f},{H - B} Z' style='fill:{col};opacity:.14'/>")
        lines.append(f"<path class='el-line' d='{path}' style='stroke:{col}'/>")
        for p in P:
            lines.append(f"<circle class='el-pt' cx='{x(p[0]):.1f}' cy='{y(p[1]):.1f}' r='{3.5 if p[2] == 'snapshot' else 3}' style='fill:{col}'>"
                         f"<title>{esc(c['first'])}: level {p[1]} on {p[0]:%b} {p[0].day} ({p[2]})</title></circle>")
        for ch in c["chapters"]:
            fx, fy = x(ch["day"]), y(ch["hi"])
            flags.append(f"<g class='flag'><line x1='{fx:.1f}' x2='{fx:.1f}' y1='{fy:.1f}' y2='{fy - 26:.1f}'/>"
                         f"<path d='M{fx:.1f},{fy - 26:.1f} h18 l-4,5 l4,5 h-18 z' style='fill:{col}'/>"
                         f"<text x='{fx + 2:.1f}' y='{fy - 18:.1f}'>{esc(ch['num'])}</text>"
                         f"<title>{esc(c['first'])} · {esc(ch['num'])}. {esc(ch['title'])} (levels {ch['lo']}→{ch['hi']}, {ch['day']:%b} {ch['day'].day})</title></g>")
        last = P[-1]
        lx, ly = x(last[0]), y(last[1])
        if c["rate"] and c["level"] < 60:
            days = (60 - c["level"]) / c["rate"]
            eta = last[0] + timedelta(days=days)
            ex = x(min(eta, d1))
            ey = y(min(60, last[1] + c["rate"] * (min(eta, d1) - last[0]).days))
            lines.append(f"<line class='el-proj' x1='{lx:.1f}' y1='{ly:.1f}' x2='{ex:.1f}' y2='{ey:.1f}' style='stroke:{col}'/>")
            if eta <= d1:
                lines.append(f"<circle class='el-goal' cx='{ex:.1f}' cy='{ey:.1f}' r='5' style='stroke:{col}'/>")
            ends.append((ly, f"{c['first']} {c['level']}", f"60 ~{eta:%b} {eta.day}", col))
        else:
            ends.append((ly, f"{c['first']} {c['level']}", "", col))
    ends.sort()
    lab, prev = [], -99
    for ly, a, b, col in ends:
        ly = max(ly, prev + 30)
        prev = ly
        lab.append(f"<text class='el-end' x='{W - R + 10}' y='{ly + 4:.1f}' style='fill:{col}'>{esc(a)}</text>"
                   + (f"<text class='el-eta' x='{W - R + 10}' y='{ly + 17:.1f}'>{esc(b)}</text>" if b else ""))
    svg = (f"<div class='mapwrap'><svg class='elev' viewBox='0 0 {W} {H}' role='img' aria-label='Level over time'>"
           f"{''.join(g)}{''.join(layers)}{''.join(lines)}{''.join(flags)}{''.join(lab)}</svg></div>")
    key = "<div class='el-key'><span><i class='k-line'></i>level</span><span><i class='k-proj'></i>projection at the last 4 days' pace</span><span><i class='k-flag'></i>journal chapter</span></div>"
    return box("sec-level", "Survey", "Elevation", svg + key, "level 0–60 · hover points and flags")


def gear_ladder(chars):
    rows = [s for s in core.SLOTS if any(s in c["items"] for c in chars)]
    vals = [c["items"][s]["ilvl"] for c in chars for s in rows if s in c["items"] and c["items"][s]["ilvl"]]
    if not vals:
        return box("sec-gear", "Console", "Gear ladder", "<div class='empty'>No gear data yet.</div>")
    lo, hi = min(vals) - 2, max(vals) + 2
    W, L, R, RH, T = 1000, 96, 20, 22, 22
    H = T + RH * len(rows) + 10

    def x(v):
        return L + (v - lo) / (hi - lo) * (W - L - R)

    g = []
    for v in range(lo - lo % 5 + 5, hi + 1, 5):
        g.append(f"<line class='lg' x1='{x(v):.1f}' x2='{x(v):.1f}' y1='{T - 6}' y2='{H - 8}'/><text class='ll' x='{x(v):.1f}' y='{T - 9}'>{v}</text>")
    n = max(1, len(chars))
    for i, s in enumerate(rows):
        cy = T + i * RH + RH / 2
        g.append(f"<text class='gl-slot' x='{L - 12}' y='{cy + 4:.1f}' text-anchor='end'>{esc(s.upper())}</text>"
                 f"<line class='gl-row' x1='{L}' x2='{W - R}' y1='{cy:.1f}' y2='{cy:.1f}'/>")
        here = [(c, c["items"][s]) for c in chars if s in c["items"] and c["items"][s]["ilvl"]]
        if len(here) > 1:
            xs = [x(it["ilvl"]) for _, it in here]
            g.append(f"<line class='gl-span' x1='{min(xs):.1f}' x2='{max(xs):.1f}' y1='{cy:.1f}' y2='{cy:.1f}'/>")
        for j, (c, it) in enumerate(here):
            off = (j - (len(here) - 1) / 2) * 3
            g.append(f"<circle class='gl-dot' cx='{x(it['ilvl']) + off:.1f}' cy='{cy:.1f}' r='6' style='fill:{series(c)}'>"
                     f"<title>{esc(c['first'])} · {esc(s)}: {esc(it['name'])} (ilvl {it['ilvl']})</title></circle>")
    del n
    legend = "".join(f"<span><i style='background:{series(c)}'></i>{esc(c['first'])} <b>avg {esc(c['ilvl'])}</b></span>" for c in chars)
    return box("sec-gear", "Console", "Gear ladder",
               f"<div class='el-key gl-key'>{legend}</div><div class='mapwrap'><svg class='ladder' viewBox='0 0 {W} {H}' role='img' aria-label='Item level by slot'>{''.join(g)}</svg></div>",
               "item level by slot · hover a dot")


def activity(chars):
    today = date.today()
    starts = [min(c["actDays"]) for c in chars if c["actDays"]] + [ch["day"] for c in chars for ch in c["chapters"]]
    start = min(starts + [today - timedelta(days=13)])
    start = max(start, today - timedelta(days=41))
    days = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    head = "".join(f"<span class='hm-d{' hm-wk' if d.weekday() == 0 else ''}'>{d.day if d.day == 1 or d == start or d.weekday() == 0 else ''}</span>" for d in days)
    rows = []
    for c in chars:
        score = {}
        for d, n in c["actDays"].items():
            score[d] = score.get(d, 0) + n
        for ch in c["chapters"]:
            score[ch["day"]] = score.get(ch["day"], 0) + 3 + max(0, ch["hi"] - ch["lo"]) // 2
        for d, q in c["questDays"].items():
            dd = date.fromisoformat(d)
            score[dd] = score.get(dd, 0) + q // 10
        cells = []
        for d in days:
            v = score.get(d, 0)
            lvl = 0 if not v else 1 if v < 3 else 2 if v < 6 else 3 if v < 10 else 4
            cells.append(f"<span class='hm-c hm-{lvl}' style='--sc:{series(c)}' title='{esc(c['first'])} · {d:%a %b} {d.day}: {v or 'nothing'} logged'></span>")
        rows.append(f"<div class='hm-row'><span class='hm-n'>{esc(c['first'])}</span><div class='hm-cells' style='--n:{len(days)}'>{''.join(cells)}</div></div>")
    scale = "".join(f"<span class='hm-c hm-{i}' style='--sc:var(--ink-2)'></span>" for i in range(5))
    body = (f"<div class='hm'><div class='hm-row hm-head'><span class='hm-n'>{start:%b}</span><div class='hm-cells' style='--n:{len(days)}'>{head}</div></div>"
            f"{''.join(rows)}</div><div class='el-key'><span>less</span>{scale}<span>more</span>"
            "<span class='muted'>· activity notes, journal chapters and quests turned in</span></div>")
    return box("sec-activity", "Console", "Activity", body, f"{days[0]:%b} {days[0].day} – today")


def professions(chars):
    names = sorted({p["name"] for c in chars for p in c["profs"]},
                   key=lambda n: (any(p.get("secondary") for c in chars for p in c["profs"] if p["name"] == n), n))
    if not names:
        return box("sec-profs", "Console", "Professions", "<div class='empty'>No professions yet.</div>")
    groups = []
    for n in names:
        bars = []
        for c in chars:
            p = next((p for p in c["profs"] if p["name"] == n), None)
            if not p:
                continue
            s, m = p.get("skill") or 0, p.get("max") or 0
            bars.append(f"<div class='pc-bar'><span class='pc-who'>{esc(c['first'])}</span>"
                        f"<span class='meter pc-m'><span class='cap' style='width:{min(100, m / 3):.1f}%;background:color-mix(in srgb,{series(c)} 22%,transparent)'></span>"
                        f"<span style='width:{min(100, s / 3):.1f}%;background:{series(c)}'></span></span><b>{s}<span class='muted'>/{m}</span></b></div>")
        groups.append(f"<div class='pc'><div class='pc-h'>{esc(n)}</div>{''.join(bars)}</div>")
    return box("sec-profs", "Console", "Professions", f"<div class='pcs'>{''.join(groups)}</div>", "skill of 300 · light track = current cap")


def timeline(chars):
    ev = []
    for c in chars:
        for ch in c["chapters"]:
            ev.append((ch["day"], 0, c, f"{ch['num']}. {ch['title']}", f"levels {ch['lo']} → {ch['hi']}", "chapter"))
        for e in c["changes"]:
            ev.append((date.fromisoformat(e["at"]), 1, c, e["text"], "", "change"))
    if not ev:
        return box("sec-changes", "Survey", "Timeline", "<div class='empty'>Nothing logged yet.</div>")
    ev.sort(key=lambda e: (e[0], e[1]), reverse=True)
    out, last = [], None
    for d, _, c, text, sub, kind in ev[:40]:
        if d != last:
            out.append(f"<li class='tl-day'><span>{d:%a} {d:%b} {d.day}</span></li>")
            last = d
        out.append(f"<li class='tl-ev tl-{kind}'><i style='background:{series(c)}'></i><div><b>{esc(c['first'])}</b> "
                   f"<span class='{'tl-title' if kind == 'chapter' else ''}'>{esc(text)}</span>"
                   + (f"<span class='muted'> · {esc(sub)}</span>" if sub else "") + "</div></li>")
    return box("sec-changes", "Survey", "Timeline", f"<ul class='tl'>{''.join(out)}</ul>", "journal chapters and tracked changes")


def inline_md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<i>\1</i>", s)
    return s


def md_block(lines):
    """Paragraphs and (nested) bullet lists."""
    out, stack = [], []
    for raw in lines:
        if not raw.strip():
            continue
        m = re.match(r"^(\s*)[-*] (.+)$", raw)
        if m:
            depth = len(m.group(1)) // 2
            while len(stack) > depth + 1:
                out.append("</ul>"); stack.pop()
            if len(stack) < depth + 1:
                out.append("<ul>"); stack.append(depth)
            out.append(f"<li>{inline_md(m.group(2))}</li>")
        else:
            while stack:
                out.append("</ul>"); stack.pop()
            out.append(f"<p>{inline_md(raw.strip())}</p>")
    while stack:
        out.append("</ul>"); stack.pop()
    return "".join(out)


def journal_box(chars):
    mine = [c for c in chars if not c["watch"]]
    books = []
    for c in mine:
        chapters, closing = journal(c["slug"])
        if not chapters:
            continue
        toc = "".join(f"<a class='jt' href='#progress' data-jump='j-{esc(c['slug'])}-{esc(ch['num'])}'><span>{esc(ch['num'])}</span>{esc(ch['title'])}</a>" for ch in chapters)
        body = "".join(
            f"<article class='jc' id='j-{esc(c['slug'])}-{esc(ch['num'])}'><div class='jn'>{esc(ch['num'])}</div><div class='jb'>"
            f"<h4>{esc(ch['title'])}</h4><div class='jm'>{esc(ch['meta'])}</div>{md_block(ch['body'])}</div></article>"
            for ch in chapters)
        stand = f"<div class='jstand'>{md_block(closing)}</div>" if closing else ""
        books.append((c, f"<div class='jbook' data-book='{esc(c['slug'])}' style='--cc:{c['colors'][0]};--ccl:{c['colors'][1]}'>"
                         f"<nav class='jtoc' aria-label='Chapters'>{toc}</nav><div class='jpages'>{body}{stand}</div></div>"))
    if not books:
        return box("sec-journal", "Survey", "Journal", "<div class='empty'>No journal yet. Run /recap to start one.</div>")
    pick = "".join(f"<button type='button' class='jpick' data-book='{esc(c['slug'])}' aria-pressed='{str(i == 0).lower()}'>{esc(c['first'])}</button>"
                   for i, (c, _) in enumerate(books))
    return box("sec-journal", "Survey", "Journal", f"<div class='jpicks'>{pick}</div>" + "".join(b for _, b in books),
               "written by /recap · oldest first")


PAGES = [  # (hash, sidebar name, title)
    ("standings", "Standings", "Standings"),
    ("leveling", "Leveling", "Leveling"),
    ("gear", "Gear", "Gear"),
    ("activity", "Activity", "Activity"),
    ("journal", "Journal", "Journal"),
]


def views(chars):
    """One view per progress page; the sidebar links to each by its hash."""
    body = {
        "standings": board(chars) + professions(chars),
        "leveling": elevation(chars),
        "gear": gear_ladder(chars),
        "activity": activity(chars) + timeline(chars),
        "journal": journal_box(chars),
    }
    return "".join(f"<div class='view' data-view='{k}'><header class='vh'><span class='lbl'>Progress</span><h2>{esc(title)}</h2></header>{body[k]}</div>"
                   for k, _, title in PAGES)


CSS = """
/* progress page */
.pbox-h{font:800 var(--t-h2)/1 var(--font-display);text-transform:uppercase;letter-spacing:.02em;margin:-2px 0 12px}
.pbox{scroll-margin-top:16px}
.recs{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:12px}
.rec{background:var(--sheet-2);border-radius:6px;padding:8px 10px;display:grid;gap:4px}.rec b{font:600 14px/1.2 var(--font-mono)}
.bd{display:grid}
.bd-row{display:grid;grid-template-columns:30px minmax(120px,1.2fr) minmax(140px,1.6fr) repeat(4,minmax(64px,.6fr));gap:14px;align-items:center;padding:9px 0;border-top:1px solid var(--rule)}
.bd-row .av{width:30px;height:30px}
.bd-name{display:grid;line-height:1.25}.bd-name b{font:800 19px/1 var(--font-display);text-transform:uppercase;letter-spacing:.03em}.bd-name .muted{font-size:12px}
.bd-name .tag{justify-self:start;margin:3px 0 1px}
.bd-lv{display:flex;align-items:center;gap:10px}.bd-lv b{font:600 22px/1 var(--font-mono);min-width:30px}
.bd-n{display:grid;gap:3px}.bd-n b{font:600 14px/1 var(--font-mono)}
.elev,.ladder{display:block;width:100%;height:auto;min-width:640px}
.ct-m{stroke:var(--contour);stroke-dasharray:2 4}
.today{stroke:var(--signal);stroke-width:1.2;stroke-dasharray:3 3}.today-t{font:700 10px var(--font-mono);fill:var(--signal);letter-spacing:.12em}
.el-line{fill:none;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}
.el-pt{stroke:var(--sheet);stroke-width:1.5}
.el-proj{stroke-width:2;stroke-dasharray:5 6;opacity:.85}.el-goal{fill:var(--sheet);stroke-width:2}
.el-end{font:700 12.5px var(--font-mono)}.el-eta{font:500 11px var(--font-mono);fill:var(--ink-3)}
.flag line{stroke:var(--ink-3);stroke-width:1}.flag text{font:700 9px var(--font-mono);fill:#fff}
.el-key{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center;margin-top:8px;font-size:12px;color:var(--ink-2)}
.el-key i{display:inline-block;width:16px;height:0;border-top:2.5px solid var(--ink-2);margin-right:6px;vertical-align:middle}
.el-key .k-proj{border-top-style:dashed}.el-key .k-flag{width:10px;height:9px;border:0;background:var(--ink-2);clip-path:polygon(0 0,100% 0,75% 50%,100% 100%,0 100%)}
.gl-key{margin:0 0 6px}.gl-key i{width:10px;height:10px;border:0;border-radius:50%}.gl-key b{font:500 11px var(--font-mono);color:var(--ink-3)}
.gl-slot{font:600 10px var(--font-mono);fill:var(--ink-3);letter-spacing:.08em}
.gl-row{stroke:var(--rule)}.gl-span{stroke:var(--ink-3);stroke-width:2;opacity:.45}.gl-dot{stroke:var(--sheet);stroke-width:2}
.hm{display:grid;gap:5px;overflow-x:auto}
.hm-row{display:grid;grid-template-columns:84px minmax(0,1fr);gap:8px;align-items:center}
.hm-n{font:600 12px var(--font-mono);color:var(--ink-2)}
.hm-cells{display:grid;grid-template-columns:repeat(var(--n),minmax(12px,1fr));gap:3px}
.hm-c{aspect-ratio:1;border-radius:3px;background:var(--sheet-2);border:1px solid var(--rule)}
.hm-1{background:color-mix(in srgb,var(--sc) 25%,var(--sheet-2))}.hm-2{background:color-mix(in srgb,var(--sc) 48%,var(--sheet-2))}
.hm-3{background:color-mix(in srgb,var(--sc) 72%,var(--sheet-2))}.hm-4{background:var(--sc)}
.hm-head .hm-n{color:var(--ink-3)}.hm-d{font:500 9.5px/1 var(--font-mono);color:var(--ink-3);text-align:center}
.el-key .hm-c{width:12px;display:inline-block}
.pcs{display:grid;gap:12px}
.pc-h{font-weight:700;font-size:13px;margin-bottom:4px}
.pc-bar{display:grid;grid-template-columns:80px minmax(0,1fr) 64px;gap:10px;align-items:center;padding:2px 0}
.pc-who{font:500 12px var(--font-mono);color:var(--ink-2)}.pc-m{height:8px}.pc-bar b{font:600 12.5px var(--font-mono);text-align:right}
.tl{list-style:none;margin:0;padding:0}
.tl-day{position:sticky;top:0;background:var(--sheet);padding:8px 0 4px;font:700 10.5px var(--font-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);border-bottom:1px dashed var(--rule-2)}
.tl-ev{display:grid;grid-template-columns:12px 1fr;gap:10px;align-items:start;padding:6px 0;font-size:13px;color:var(--ink-2)}
.tl-ev i{width:9px;height:9px;border-radius:50%;margin-top:5px}.tl-chapter i{border-radius:2px;transform:rotate(45deg)}
.tl-title{font-weight:600;color:var(--ink)}.tl-ev b{color:var(--ink)}
.jpicks{display:flex;gap:6px;margin-bottom:12px}
.jpick{font:600 12px var(--font-mono);letter-spacing:.06em;text-transform:uppercase;padding:6px 12px;border-radius:6px;border:1px solid var(--rule-2);background:transparent;color:var(--ink-2);cursor:pointer}
.jpick[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.jbook{display:grid;grid-template-columns:220px minmax(0,1fr);gap:20px}
.jbook[hidden]{display:none!important}
.jtoc{display:grid;gap:2px;align-content:start;position:sticky;top:16px}
.jt{display:grid;grid-template-columns:30px 1fr;gap:6px;padding:6px 8px;border-radius:6px;text-decoration:none;font-size:13px;color:var(--ink-2);line-height:1.3}
.jt span{font:700 11px/1.5 var(--font-mono);color:var(--c)}.jt:hover{background:var(--sheet-2);color:var(--ink)}
.jpages{display:grid;gap:4px;max-height:calc(100dvh - 220px);min-height:420px;overflow-y:auto;padding-right:6px}
.jc{display:grid;grid-template-columns:52px minmax(0,1fr);gap:14px;padding:16px 0;border-bottom:1px dashed var(--rule-2);scroll-margin-top:8px}
.jn{font:800 30px/1 var(--font-display);color:var(--c);text-align:right}
.jb h4{font:800 22px/1.05 var(--font-display);text-transform:uppercase;letter-spacing:.02em;margin:0}
.jm{font:500 11.5px/1.5 var(--font-mono);color:var(--ink-3);margin:4px 0 10px}
.jb p{margin:0 0 8px;font-size:15px;line-height:1.6;color:var(--ink);max-width:68ch;font-style:italic}
.jb ul{margin:0 0 4px;padding-left:18px;max-width:68ch}.jb li{margin:3px 0;line-height:1.55;color:var(--ink-2)}.jb li b{color:var(--ink)}
.jb ul ul{margin-top:2px}
.jstand{margin-top:12px;padding:12px 14px;border-radius:6px;background:var(--sheet-2);font-size:13px}.jstand p{margin:3px 0}
@media (max-width:760px){
  .jbook{grid-template-columns:minmax(0,1fr)}.jtoc{position:static;display:flex;overflow-x:auto;gap:4px}.jt{white-space:nowrap;display:flex}
  .jc{grid-template-columns:34px minmax(0,1fr)}.jn{font-size:22px}
}
@media (max-width:760px){
  .bd-row{grid-template-columns:30px minmax(0,1fr) 70px;grid-template-areas:"a n l" "a s s"}
  .bd-row .av{grid-area:a}.bd-name{grid-area:n}.bd-lv{grid-area:l}.bd-lv .meter{display:none}
  .bd-n{display:none}
  .hm-row{grid-template-columns:60px minmax(0,1fr)}
}
"""
