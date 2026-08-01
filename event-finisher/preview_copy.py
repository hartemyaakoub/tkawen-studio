# -*- coding: utf-8 -*-
"""Show BEFORE/AFTER of every sentence the fix would change."""
import os, re, sys
sys.path.insert(0, "/tmp")
from fix_copy import fix, ROOT

TAG = re.compile(r"<[^>]+>")


def text_of(s):
    return re.sub(r"\s+", " ", TAG.sub(" ", s)).strip()


pairs = {}
for dirpath, _d, files in os.walk(ROOT):
    if "/.git" in dirpath:
        continue
    for fn in sorted(files):
        if not fn.endswith(".html") or ".bak" in fn:
            continue
        p = os.path.join(dirpath, fn)
        s = open(p, encoding="utf-8").read()
        s2, n = fix(s)
        if not n:
            continue
        a = text_of(s).split("۔")
        # compare sentence-ish chunks
        for chunk_a, chunk_b in zip(re.split(r"(?<=[.·|])\s", text_of(s)),
                                    re.split(r"(?<=[.·|])\s", text_of(s2))):
            if chunk_a != chunk_b:
                pairs.setdefault((chunk_a[:170], chunk_b[:170]), []).append(os.path.relpath(p, ROOT))

print(f"{len(pairs)} distinct changed sentences\n")
for (a, b), files in list(pairs.items())[:26]:
    print("-", ", ".join(sorted(set(files))[:3]))
    print("  BEFORE:", a)
    print("  AFTER :", b)
