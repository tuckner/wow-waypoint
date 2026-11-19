"""Character data sources, one adapter per armory site.

An adapter module exposes:
  fetch(char, cfg) -> (normalized dict, problems list)    problems = shape-check warnings
  diagnose(char, cfg) -> (steps, html_or_None)            steps = [(ok, label, detail)]
`cfg` is the site's entry in data/sources.json ("sources" map). Which site a character uses comes
from its own "source" field, else from its game version's default in data/sources.json.
"""
from . import wowfio
from .errors import NetworkError, ParseError, SourceError, Unsupported  # noqa: F401

ADAPTERS = {"wowfio": wowfio}


def resolve(char, sources_cfg):
    version = char.get("version") or "forever"
    vinfo = sources_cfg.get("versions", {}).get(version, {})
    sid = char.get("source") or vinfo.get("source")
    if not sid:
        raise Unsupported(f"character tracking isn't available for {vinfo.get('label', version)} yet (no armory site configured)")
    if sid not in ADAPTERS:
        raise Unsupported(f"armory source {sid!r} has no adapter yet")
    return sid, ADAPTERS[sid], sources_cfg.get("sources", {}).get(sid, {})


def fetch(char, sources_cfg):
    sid, adapter, cfg = resolve(char, sources_cfg)
    norm, problems = adapter.fetch(char, cfg)
    norm["source"] = sid
    return norm, problems


def diagnose(char, sources_cfg):
    sid, adapter, cfg = resolve(char, sources_cfg)
    return sid, adapter.diagnose(char, cfg)
