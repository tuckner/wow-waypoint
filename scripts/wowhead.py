"""Wowhead lookups for WoW Forever: item tooltips (JSON) and icons, cached under notes/cache/.

Only item IDs and icon names are sent (no character data). Every call fails soft: a network
error returns None and the caller renders without the icon or tooltip.
"""
import base64
import hashlib
import json
import re
import time
import urllib.request

import core

TOOLTIP_URL = "https://nether.wowhead.com/{env}/tooltip/item/{id}"
ICON_URL = "https://wow.zamimg.com/images/wow/icons/{size}/{icon}.jpg"
ITEM_PAGE = "https://www.wowhead.com/{env}/item={id}"
UA = "Mozilla/5.0 (wow-waypoint)"
SAFE = re.compile(r"^[a-z0-9_\-]+$")


def cache_dir(kind):
    d = core.BASE.parent / "cache" / kind
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read() if r.status == 200 else None
    except Exception:
        return None


def item_url(item_id, env="forever"):
    return ITEM_PAGE.format(env=env, id=item_id)


def icon_bytes(icon, size="medium"):
    """JPEG bytes for an icon name (e.g. inv_helmet_31); sizes: small 18px, medium 36px, large 56px."""
    if not icon or not SAFE.match(icon.lower()):
        return None
    return cached(ICON_URL.format(size=size, icon=icon.lower()), f"icons-{size}", f"{icon.lower()}.jpg")


def icon_data_uri(icon, size="medium"):
    return data_uri(icon_bytes(icon, size))


def cached(url, kind, name, max_age_hours=None):
    """Fetch url once into notes/cache/<kind>/<name>; refetch when older than max_age_hours. Stale beats nothing."""
    if not url or not SAFE.match(name.rsplit(".", 1)[0].lower()):
        return None
    f = cache_dir(kind) / name
    if f.exists() and (max_age_hours is None or time.time() - f.stat().st_mtime < max_age_hours * 3600):
        return f.read_bytes()
    data = _get(url)
    if data:
        f.write_bytes(data)
        return data
    return f.read_bytes() if f.exists() else None


def image_uri(url, kind="images", max_age_hours=None):
    """Data URI for any image URL (character renders, avatars, profession icons), cached by URL."""
    if not url or not url.startswith("https://"):
        return None
    ext = url.rsplit(".", 1)[-1].lower()
    name = hashlib.sha1(url.encode()).hexdigest()[:16] + "." + (ext if ext in ("png", "jpg", "jpeg", "webp") else "img")
    return data_uri(cached(url, kind, name, max_age_hours), ext)


def data_uri(data, ext="jpg"):
    if not data:
        return None
    mime = {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def tooltip(item_id, env="forever"):
    """Parsed tooltip: name, quality, icon, lines (plain text). Cached per item."""
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return None
    f = cache_dir(f"tooltips-{env}") / f"{item_id}.json"
    if f.exists():
        return json.loads(f.read_text())
    raw = _get(TOOLTIP_URL.format(env=env, id=item_id))
    try:
        j = json.loads(raw) if raw else None
    except ValueError:
        j = None
    if not j or "name" not in j:
        return None
    out = {"id": item_id, "name": j["name"], "quality": core.QUALITY.get(j.get("quality"), "?"),
           "icon": j.get("icon"), "lines": tooltip_lines(j.get("tooltip", "")), "url": item_url(item_id, env)}
    f.write_text(json.dumps(out))
    return out


def tooltip_lines(html):
    t = re.sub(r"<!--.*?-->", "", html)
    t = re.sub(r"<br\s*/?>|<table[^>]*>|</tr>|</table>|</div>", "\n", t)
    t = re.sub(r"</t[dh]>\s*<t[dh][^>]*>", "  ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    return [l.strip() for l in t.split("\n") if l.strip()]
