# -*- coding: utf-8 -*-
"""Locate the hero headline's typography rules."""
import re
p = "/var/www/tkawen-corporate/index.html"
s = open(p, encoding="utf-8").read()
for rx in (r"\.whero-copy\s+h1\s*\{[^}]*\}", r"\.whero\s+h1\s*\{[^}]*\}",
           r"\.whero-copy h1[^{]*\{[^}]*\}", r"h1\s*\{[^}]*line-height[^}]*\}"):
    for m in re.finditer(rx, s):
        print(">>", re.sub(r"\s+", " ", m.group(0))[:300], "\n")
# any line-height under 1.1 anywhere
for m in re.finditer(r"[^{};]*line-height\s*:\s*(0?\.\d+|1(\.0\d?)?)\s*[;}]", s):
    frag = re.sub(r"\s+", " ", m.group(0)).strip()
    if len(frag) < 120:
        print("tight:", frag)
