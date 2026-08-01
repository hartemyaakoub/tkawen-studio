# -*- coding: utf-8 -*-
"""Export a few full-quality-judgement previews (1400px) + report EXIF/blur/WB."""
import os, sys
from PIL import Image, ImageOps, ImageFilter, ImageStat

SRC = r"D:\f05"
OUT = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
picks = [int(a) for a in sys.argv[1:]] or [0, 19, 76, 91]

for i in picks:
    name = files[i]
    p = os.path.join(SRC, name)
    with Image.open(p) as im:
        ex = im.getexif()
        im = ImageOps.exif_transpose(im)
        full = im.copy()
        # blur proxy: stddev of a Laplacian-ish edge filter on the luma
        g = full.convert("L")
        edge = g.filter(ImageFilter.FIND_EDGES)
        sharp = round(ImageStat.Stat(edge).stddev[0], 1)
        r, gg, b = ImageStat.Stat(full.convert("RGB")).mean
        print(f"[{i}] {name} {full.width}x{full.height} sharp={sharp} "
              f"R={r:.0f} G={gg:.0f} B={b:.0f} (R/B={r / max(b, 1):.2f})")
        for k, v in ex.items():
            if k in (271, 272, 274, 33434, 33437, 34855):
                print("     exif", k, "=", v)
        prev = full.copy()
        prev.thumbnail((1400, 1400))
        prev.save(os.path.join(OUT, f"prev_{i}.jpg"), quality=88)
