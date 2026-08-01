# -*- coding: utf-8 -*-
"""Survey D:\f05 — EXIF, size, orientation, brightness/contrast stats, contact sheets."""
import os, json, math
from PIL import Image, ImageOps, ImageStat, ImageDraw

SRC = r"D:\f05"
OUT = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith((".jpg", ".jpeg", ".png")))
rows = []

for name in files:
    p = os.path.join(SRC, name)
    with Image.open(p) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        g = im.convert("L")
        st = ImageStat.Stat(g)
        hist = g.histogram()
        total = sum(hist)
        # clipping + tonal spread
        shadow = sum(hist[:8]) / total
        blown = sum(hist[248:]) / total
        lo = next(i for i in range(256) if sum(hist[:i + 1]) / total > 0.005)
        hi = next(i for i in range(255, -1, -1) if sum(hist[i:]) / total > 0.005)
        rows.append({
            "name": name, "w": w, "h": h,
            "orient": "portrait" if h > w else ("square" if h == w else "landscape"),
            "mean": round(st.mean[0], 1), "stddev": round(st.stddev[0], 1),
            "shadow_clip": round(shadow * 100, 2), "highlight_clip": round(blown * 100, 2),
            "range_lo": lo, "range_hi": hi,
        })

with open(os.path.join(OUT, "survey.json"), "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

# ---- contact sheets: 8 columns, thumbs 260px wide, labelled by index
COLS, TW = 8, 260
per_sheet = 48
for s in range(math.ceil(len(files) / per_sheet)):
    chunk = files[s * per_sheet:(s + 1) * per_sheet]
    rowsn = math.ceil(len(chunk) / COLS)
    TH = int(TW * 0.75)
    sheet = Image.new("RGB", (COLS * TW, rowsn * (TH + 18)), (18, 18, 20))
    dr = ImageDraw.Draw(sheet)
    for i, name in enumerate(chunk):
        with Image.open(os.path.join(SRC, name)) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((TW, TH))
            x = (i % COLS) * TW + (TW - im.width) // 2
            y = (i // COLS) * (TH + 18) + (TH - im.height) // 2
            sheet.paste(im, (x, y))
        dr.text(((i % COLS) * TW + 4, (i // COLS) * (TH + 18) + TH + 3),
                f"{s * per_sheet + i}  {name[4:19]}", fill=(150, 150, 160))
    sheet.save(os.path.join(OUT, f"sheet{s + 1}.jpg"), quality=82)
    print("sheet", s + 1, sheet.size)

print("photos:", len(files))
por = sum(1 for r in rows if r["orient"] == "portrait")
print("portrait:", por, "landscape:", len(rows) - por)
print("dark (mean<80):", sum(1 for r in rows if r["mean"] < 80))
print("flat (stddev<45):", sum(1 for r in rows if r["stddev"] < 45))
print("blown (>1% highlights):", sum(1 for r in rows if r["highlight_clip"] > 1))
