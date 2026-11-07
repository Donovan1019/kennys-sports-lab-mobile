#!/usr/bin/env python3
"""Fail closed on broken NBA/NFL/NHL navigation and duplicate visible navigation."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ("nba.html", "nfl.html", "nhl.html")
NBA_TABS = {"projections", "stats", "research", "ml", "sgp"}
errors = []

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.navs = []
        self.hidden_depth = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "nav":
            self.navs.append(a)
        if tag == "button" and a.get("data-nba-tab"):
            self.ids.append("tab:"+a["data-nba-tab"])

def inspect(name):
    p = ROOT / name
    doc = p.read_text(encoding="utf-8")
    parsed = Inspect()
    parsed.feed(doc)
    ids = set(parsed.ids)
    duplicates = {i for i in ids if parsed.ids.count(i) > 1}
    if duplicates:
        errors.append(f"{name}: duplicate IDs: {sorted(duplicates)}")
    for href in parsed.links:
        u = urlsplit(href)
        if u.scheme in ("http", "https", "mailto", "tel") or href.startswith("//"):
            continue
        target = (p.parent / unquote(u.path)).resolve() if u.path else p
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            errors.append(f"{name}: missing destination {href}")
            continue
        if u.fragment:
            fragment = unquote(u.fragment)
            if target == p and name == "nba.html" and fragment in NBA_TABS:
                if "tab:"+fragment not in ids:
                    errors.append(f"{name}: missing NBA tab handler for #{fragment}")
            else:
                dest = Inspect()
                dest.feed(target.read_text(encoding="utf-8"))
                if fragment not in dest.ids:
                    errors.append(f"{name}: missing anchor {href}")
    if sum(n.get("class") == "ksl-unified-sections" for n in parsed.navs) != 1:
        errors.append(f"{name}: expected exactly one sport section navigation")
    if any(n.get("class") == "ksl-research-destinations" for n in parsed.navs):
        errors.append(f"{name}: duplicate research navigation")
    if name == "nba.html":
        if 'class="nba-tabs" aria-label="Legacy NBA section controls" hidden style="display:none"' not in doc:
            errors.append("nba.html: legacy NBA tabs must not be visible")
        for tab in ("projections", "stats", "ml", "research"):
            if 'href="#' + tab + '"' not in doc:
                errors.append(f"nba.html: unified navigation missing #{tab}")
        if "window.addEventListener('hashchange'" not in doc:
            errors.append("nba.html: missing hash navigation handler")

for name in SPORTS:
    inspect(name)
if errors:
    print("\n".join("FAIL "+e for e in errors))
    sys.exit(1)
print("PASS: NBA/NFL/NHL local destinations, tab anchors and navigation structure")
