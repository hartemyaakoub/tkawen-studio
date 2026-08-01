# -*- coding: utf-8 -*-
"""Side-by-side BEFORE | AFTER strips for judging the look."""
import os, sys
from PIL import Image, ImageOps, ImageDraw

SRC = r"D:\f05"
POST = os.path.join(SRC, "_out", "post")
SP = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
idx = [int(a) for a in sys.argv[1:]] or [19]
H = 900

tiles = []
for i in idx:
    n = files[i]
    with Image.open(os.path.join(SRC, n)) as b:
        b = ImageOps.exif_transpose(b)
        b.thumbnail((10000, H), Image.LANCZOS)
        tiles.append(("BEFORE " + str(i), b.copy()))
    p = os.path.join(POST, n)
    if os.path.exists(p):
        with Image.open(p) as a:
            a.thumbnail((10000, H), Image.LANCZOS)
            tiles.append(("AFTER " + str(i), a.copy()))

pad = 14
W = sum(t[1].width for t in tiles) + pad * (len(tiles) + 1)
sheet = Image.new("RGB", (W, H + 34), (16, 16, 18))
dr = ImageDraw.Draw(sheet)
x = pad
for label, t in tiles:
    sheet.paste(t, (x, 28))
    dr.text((x + 2, 8), label, fill=(200, 200, 210))
    x += t.width + pad
name = "cmp_" + "_".join(str(i) for i in idx) + ".jpg"
sheet.save(os.path.join(SP, name), quality=88)
print(name, sheet.size)
