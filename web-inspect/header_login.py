# -*- coding: utf-8 -*-
"""What exactly does the header's user icon link to?"""
import re
s = open("/var/www/tkawen-corporate/index.html", encoding="utf-8").read()
head = s[:s.find("</header>") + 9] if "</header>" in s else s[:40000]
for m in re.finditer(r"<a\b[^>]*href=\"([^\"]*)\"[^>]*>(.{0,120}?)</a>", head, re.S):
    href, inner = m.group(1), re.sub(r"\s+", " ", m.group(2))
    if any(k in href for k in ("id.tkawen", "login", "/join", "auth")) or "user" in inner.lower():
        print("HREF:", href)
        print("   inner:", inner[:110], "\n")
