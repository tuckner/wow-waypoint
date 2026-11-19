"""wowf.io adapter (WoW Forever). Scrapes the Next.js flight payload on the player page."""
import json
import re
import socket
import urllib.error
import urllib.request

from .errors import NetworkError, ParseError

DEFAULT_URL = "https://wowf.io/en/players/{region}/{slug}"
ASSETS = "https://assets.wowf.io"
UA = "Mozilla/5.0 (wow-waypoint character notes)"
CHUNK_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', re.S)


def url_for(char, cfg):
    return (cfg.get("url") or DEFAULT_URL).format(region=char.get("region", "us"), slug=char["slug"])


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ParseError(f"404 at {url}: no such character (check name and region; wowf.io only knows a character after it logs out once)")
        raise NetworkError(f"HTTP {e.code} at {url}")
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        raise NetworkError(f"{type(e).__name__}: {getattr(e, 'reason', e)}")


def flight(html):
    chunks = CHUNK_RE.findall(html)
    return chunks, "".join(json.loads('"' + c + '"') for c in chunks)


def candidates(text, slug):
    """Objects containing "slug":"<slug>"; key order varies, so walk back to each enclosing '{'."""
    out = []
    for m in re.finditer(r'"slug":\s*"%s"' % re.escape(slug), text):
        depth, j = 0, m.start()
        while j > 0:
            j -= 1
            if text[j] == "}":
                depth += 1
            elif text[j] == "{":
                if depth == 0:
                    break
                depth -= 1
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[j:])
        except ValueError:
            continue
        out.append(obj)
    return out


def extract(html, slug):
    chunks, text = flight(html)
    if not chunks:
        raise ParseError("no __next_f flight chunks in page (site layout changed?)")
    objs = candidates(text, slug)
    if not objs:
        raise ParseError(f'slug anchor "{slug}" not found in flight data')
    for obj in objs:
        if "items" in obj and "level" in obj:
            return obj
    raise ParseError(f"found {len(objs)} objects with the slug but none has items+level (site layout changed?)")


REQUIRED = {"slug": str, "name": str, "level": int, "className": str, "items": list}
EXPECTED = ["itemLevel", "trees", "professions", "reputations", "stats", "lastLogin", "questsDone"]


def check(raw, max_level=60):
    problems = []
    for k, t in REQUIRED.items():
        if k not in raw:
            problems.append(f"missing {k}")
        elif not isinstance(raw[k], t):
            problems.append(f"{k} is {type(raw[k]).__name__}, expected {t.__name__}")
    for k in EXPECTED:
        if k not in raw:
            problems.append(f"missing {k}")
    if isinstance(raw.get("stats"), dict) and "values" not in raw["stats"]:
        problems.append("missing stats.values")
    if isinstance(raw.get("level"), int) and not 1 <= raw["level"] <= max_level:
        problems.append(f"level {raw['level']} out of range")
    items = raw.get("items") if isinstance(raw.get("items"), list) else []
    if len(items) > 19:
        problems.append(f"{len(items)} items (more than gear slots)")
    for i in items:
        missing = [k for k in ("slotName", "name", "itemLevel", "lines") if k not in i]
        if missing:
            problems.append(f"item missing {', '.join(missing)}")
            break
    lines = [l.get("text", "") for i in items for l in i.get("lines", []) if isinstance(l, dict)]
    if items and not any(re.match(r"^[+-]\d+ |^Requires Level|^\d+ Armor$", t) for t in lines):
        problems.append("no item stat or 'Requires Level' lines parse (tooltip format changed?)")
    return problems


def normalize(raw):
    guild = raw.get("guild")
    return {
        "slug": raw["slug"], "region": raw.get("region"),
        "name": f'{raw["name"]} {raw.get("surname") or ""}'.strip(),
        "race": raw.get("raceName"), "class": raw.get("className"), "faction": raw.get("faction"),
        "level": raw.get("level"), "itemLevel": raw.get("itemLevel"), "lastLogin": raw.get("lastLogin"),
        "quests": raw.get("questsDone"), "kills": (raw.get("pvp") or {}).get("kills"),
        "realmType": raw.get("ruleset"), "guild": guild.get("name") if isinstance(guild, dict) else guild,
        "trees": [{"name": t["name"], "points": t.get("points", 0), "ranks": t.get("ranks") or {}} for t in raw.get("trees", [])],
        "gender": raw.get("gender"), "avatar": raw.get("avatar"), "render": raw.get("render"),
        "professions": [{"name": p["name"], "skill": p.get("skill"), "max": p.get("max"), "secondary": p.get("secondary"),
                         "icon": ASSETS + p["icon"] if str(p.get("icon", "")).startswith("/") else p.get("icon")}
                        for p in raw.get("professions", [])],
        "reps": [{"name": r["name"], "standing": r.get("standing"), "value": r.get("value"), "max": r.get("max"), "tier": r.get("tier")}
                 for r in raw.get("reputations", [])],
        "stats": (raw.get("stats") or {}).get("values") or {},
        "items": [{"slot": i.get("slotName"), "name": i["name"], "ilvl": i.get("itemLevel"), "quality": i.get("quality"),
                   "id": i.get("id"), "icon": i.get("ic"),
                   "lines": [l.get("text", "") for l in i.get("lines", []) if isinstance(l, dict)]}
                  for i in raw.get("items", [])],
        "achievements": (raw.get("achievements") or {}).get("recent", []),
        "mounts": [m.get("name", m) if isinstance(m, dict) else m for m in raw.get("mounts", [])],
        "fetchedAt": raw.get("fetchedAt"),
    }


def fetch(char, cfg):
    _, html = fetch_html(url_for(char, cfg))
    raw = extract(html, char["slug"])
    return normalize(raw), check(raw)


def diagnose(char, cfg):
    """Step-by-step report. Returns (steps, html) where html is kept for debugging on failure."""
    steps, url = [], url_for(char, cfg)
    try:
        status, html = fetch_html(url)
    except (NetworkError, ParseError) as e:
        return [(False, "fetch", str(e))], None
    steps.append((True, "fetch", f"HTTP {status}, {len(html):,} bytes from {url}"))
    chunks, text = flight(html)
    steps.append((bool(chunks), "flight chunks", f"{len(chunks)} __next_f.push chunks"))
    if not chunks:
        return steps, html
    objs = candidates(text, char["slug"])
    steps.append((bool(objs), "slug anchor", f"{len(objs)} object(s) containing the slug decoded"))
    raw = next((o for o in objs if "items" in o and "level" in o), None)
    steps.append((raw is not None, "character object", "found (has items + level)" if raw else "none has items + level"))
    if raw is None:
        return steps, html
    problems = check(raw)
    steps.append((not problems, "shape check", "all keys present" if not problems else "; ".join(problems)))
    n = normalize(raw)
    first = n["items"][0] if n["items"] else None
    sample = f"level {n['level']} {n['race']} {n['class']}, {len(n['items'])} items"
    if first:
        stat_lines = [l for l in first["lines"] if re.match(r"^[+-]\d+ |^Requires Level", l)]
        sample += f"; first item {first['name']}: {', '.join(stat_lines) or 'no stat lines'}"
    steps.append((True, "sample parse", sample))
    return steps, (html if problems else None)
