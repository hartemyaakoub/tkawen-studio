# -*- coding: utf-8 -*-
"""The last three: the word sits inside the <span class="g"> highlight of an h1,
so the highlight has to move to another phrase rather than be emptied."""
import os, sys, time

ROOT = "/var/www/tkawen-corporate"
APPLY = "--apply" in sys.argv
STAMP = time.strftime("%Y%m%d-%H%M%S")

EDITS = {
    "fr/about.html": [
        ('<h1>Nous bâtissons un écosystème numérique <span class="g">souverain</span> pour l\'Algérie</h1>',
         '<h1>Nous bâtissons un écosystème numérique <span class="g">pour l\'Algérie</span></h1>')],
    "en/about.html": [
        ('<h1>We build a <span class="g">sovereign</span> digital ecosystem for Algeria</h1>',
         '<h1>We build a digital ecosystem <span class="g">for Algeria</span></h1>')],
    "en/products.html": [
        ('<h1>A complete ecosystem — <span class="g">ten sovereign</span> products</h1>',
         '<h1>A complete ecosystem — <span class="g">ten products</span></h1>')],
}

for rel, pairs in EDITS.items():
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8").read()
    n = 0
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b)
            n += 1
        else:
            print("!! anchor not found in", rel)
    print(rel, "->", n)
    if n and APPLY:
        open(p + f".bak-copy3-{STAMP}", "w", encoding="utf-8").write(open(p, encoding="utf-8").read())
        open(p, "w", encoding="utf-8").write(s)
