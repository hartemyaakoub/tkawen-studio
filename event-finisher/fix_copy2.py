# -*- coding: utf-8 -*-
"""Mop up the six latin leftovers the first pass could not reach:
a highlight <span> (deleting it would leave an empty highlight) and
«sovereign,» where the comma defeated the \\s+ in the rule."""
import os, re, sys, time

ROOT = "/var/www/tkawen-corporate"
APPLY = "--apply" in sys.argv
STAMP = time.strftime("%Y%m%d-%H%M%S")

RULES = [
    # the highlighted word carries the headline — replace it, don't empty it
    (re.compile(r'A video conferencing platform\s*<span class="g">Sovereign</span>\s*—\s*built entirely in Algeria'),
     'A video conferencing platform <span class="g">built entirely in Algeria</span>'),
    (re.compile(r'Une plateforme de conférences vidéo\s*<span class="g">Souverain</span>\s*—\s*entièrement construit(?:e)? en Algérie'),
     'Une plateforme de conférences vidéo <span class="g">entièrement construite en Algérie</span>'),
    (re.compile(r'<span class="g">Sovereign</span>'), '<span class="g">Algerian</span>'),
    (re.compile(r'<span class="g">Souverain(?:e)?</span>'), '<span class="g">algérienne</span>'),
    (re.compile(r"\bA sovereign,\s*", re.I), "An "),
    (re.compile(r"\bsovereign,\s*", re.I), ""),
    (re.compile(r",\s*souverain(?:e|s|es)?\b", re.I), ""),
]


def main():
    total, touched = 0, []
    for dirpath, _d, files in os.walk(ROOT):
        if "/.git" in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith(".html") or ".bak" in fn:
                continue
            p = os.path.join(dirpath, fn)
            s = open(p, encoding="utf-8").read()
            s2, n = s, 0
            for rx, rep in RULES:
                s2, k = rx.subn(rep, s2)
                n += k
            if n:
                touched.append((os.path.relpath(p, ROOT), n))
                total += n
                if APPLY:
                    open(p + f".bak-copy2-{STAMP}", "w", encoding="utf-8").write(s)
                    open(p, "w", encoding="utf-8").write(s2)
    print(("APPLIED" if APPLY else "DRY-RUN") + f": {total} in {len(touched)} files", touched)


if __name__ == "__main__":
    main()
