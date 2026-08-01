# -*- coding: utf-8 -*-
"""Two follow-ups found by looking at the rendered pages, not the source:

1) The generic «سياديّة»→«جزائريّة» highlight swap was right for the LIQAA
   headline but produced «منظومةً رقميّةً جزائريّة للجزائر» on /about — the
   adjective and the complement now say the same thing. Move the highlight.
2) «السيادة التقنيّة» in the values block is the same rejected family as
   «سيادي»; the French/English side was already mapped to independence.
"""
import os, sys, time

ROOT = "/var/www/tkawen-corporate"
APPLY = "--apply" in sys.argv
STAMP = time.strftime("%Y%m%d-%H%M%S")

RULES = [
    ('منظومةً رقميّةً <span class="g">جزائريّة</span> للجزائر',
     'منظومةً رقميّةً <span class="g">للجزائر</span>'),
    ("السيادة التقنيّة", "الاستقلال التقنيّ"),
    ("السيادة التقنية", "الاستقلال التقني"),
]

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
        for a, b in RULES:
            if a in s2:
                n += s2.count(a)
                s2 = s2.replace(a, b)
        if n:
            touched.append((os.path.relpath(p, ROOT), n))
            total += n
            if APPLY:
                open(p + f".bak-copy5-{STAMP}", "w", encoding="utf-8").write(s)
                open(p, "w", encoding="utf-8").write(s2)
print(("APPLIED" if APPLY else "DRY-RUN") + f": {total}", touched)
