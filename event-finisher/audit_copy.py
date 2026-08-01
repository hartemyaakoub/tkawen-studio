# -*- coding: utf-8 -*-
"""Report every place the corporate site cites decree 1275 or uses the
'sovereign' wording the founder rejected. Read-only."""
import os, re

ROOT = "/var/www/tkawen-corporate"
PATTERNS = {
    "1275": re.compile(r".{70}1275.{50}", re.S),
    "sovereign_ar": re.compile(r".{55}سياديّ?[ةا]?.{35}", re.S),
    "sovereign_lat": re.compile(r".{55}(?:[Ss]ouverain\w*|[Ss]overeign\w*).{35}", re.S),
}


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


seen = {k: {} for k in PATTERNS}
for dirpath, _d, files in os.walk(ROOT):
    if "/.git" in dirpath:
        continue
    for fn in sorted(files):
        if not fn.endswith(".html") or ".bak" in fn:
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT)
        s = open(p, encoding="utf-8").read()
        for key, rx in PATTERNS.items():
            for m in rx.finditer(s):
                seen[key].setdefault(clean(m.group(0)), []).append(rel)

for key in PATTERNS:
    print(f"\n########## {key} — {len(seen[key])} distinct")
    for txt, files in sorted(seen[key].items(), key=lambda kv: -len(kv[1])):
        print(f"[{len(files)}x] {', '.join(sorted(set(files))[:4])}")
        print("    ", txt[:190])
