"""Status line: one short line about one character: this session's focus pin, else main, else the most recently played.
Never fetches, never writes."""
import json
import subprocess
import sys

import core

SEP = " · "


def render(stdin_json=None, show_all=False, ascii_only=False, width=80):
    info = stdin_json or {}
    ws = (info.get("workspace") or {}).get("project_dir") or (info.get("workspace") or {}).get("current_dir") or info.get("cwd")
    core.set_root(core.find_workspace(ws, use_env=False) if ws else core.find_workspace())
    if not core.CONFIG.exists():
        return ""
    chars = core.owned()
    rows = []
    for c in chars:
        h = core.history(c["slug"], tail=64_000)
        if h:
            rows.append((c, h))
    if not rows:
        return ""
    rows.sort(key=lambda r: r[1][-1].get("lastLogin") or "", reverse=True)
    rows.sort(key=lambda r: not r[0].get("main"))  # primary character first (stable: rest stay by last login)
    focus = core.read_json(core.BASE / ".focus.json", None) or {}
    if focus.get("slug") and (not focus.get("session_id") or focus["session_id"] == info.get("session_id")):
        rows.sort(key=lambda r: r[0]["slug"] != focus["slug"])  # pinned character first
    sep = " | " if ascii_only else SEP
    if show_all:
        return sep.join(f"{r[1][-1]['name'].split()[0]} {r[1][-1]['level']}" for r in rows)[:width]

    c, h = rows[0]
    cur = h[-1]
    import milestones
    head = [f"{cur['name'].split()[0]} {cur['level']} {cur.get('class') or ''}".strip()]
    if cur.get("itemLevel"):
        head.append(f"iLvl {cur['itemLevel']}")
    p = core.pace(h)
    if p and p["levels_per_day"] > 0:
        head.append(f"+{round(p['levels_per_day'] * p['days'])} lvl/{round(p['days'])}d")
    nxt = milestones.next_listed(cur.get("class"), cur["level"], version=core.version_of(c))
    nudge = next((n for n in milestones.profession_nudges(cur.get("professions"), cur["level"], core.version_of(c)) if n["ready"]), None)
    tail = []
    if (qs := len(core.open_questions(c["slug"]))):
        tail.append(f"{qs} open ?")
    if any(core.low_durability(i) for i in core.gear(c["slug"]).values()):
        tail.append("! repair gear" if ascii_only else "⚠ repair gear")
    if core.failing():
        tail.append("! parse" if ascii_only else "⚠ parse")
    mid = (f"next: {nxt['what'].split(' (')[0]} @{nxt['level']}" if nxt else
           ("train " + nudge["what"].split(": learn ")[-1].split(" (")[0] if nudge else ""))
    line = sep.join(head + ([mid] if mid else []) + tail)
    if len(line) > width and mid:  # truncate the milestone text first
        room = width - len(sep.join(head + tail)) - len(sep)
        mid = mid[:max(0, room - 1)] + "…" if room > 12 else ""
        line = sep.join(head + ([mid] if mid else []) + tail)
    if ascii_only:
        line = line.replace("…", "...").encode("ascii", "replace").decode()
    return line[:width]


def main(args):
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        info = json.loads(raw) if raw.strip() else {}
        prefix = ""
        if "--prefix-cmd" in args:
            cmd = args[args.index("--prefix-cmd") + 1]
            prefix = subprocess.run(cmd, shell=True, input=raw, capture_output=True, text=True, timeout=5).stdout.strip()
        line = render(info, "--all" in args, "--ascii" in args)
        print(SEP.join(x for x in (prefix, line) if x))
    except Exception:
        pass  # a broken tracker must never break the status line
    return 0
