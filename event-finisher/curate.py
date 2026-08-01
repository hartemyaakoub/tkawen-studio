# -*- coding: utf-8 -*-
r"""Curate the 92 shots: many are 1-second bursts of the same handshake.

Groups near-identical consecutive frames (dHash + timestamp), keeps the sharpest
of each group, and copies those finished files to D:\f05\_out\best as 01..NN.
Nothing is deleted — the full set stays in _out\post.
"""
import json, os, shutil
from datetime import datetime
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageStat

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
SP = os.path.dirname(os.path.abspath(__file__))
HAM = 10          # bits of difference still counted as "same shot"
GAP = 150         # seconds


def dhash(im, s=8):
    g = np.asarray(im.convert("L").resize((s + 1, s), Image.LANCZOS), np.int16)
    return (g[:, 1:] > g[:, :-1]).flatten()


def stamp(name):
    try:
        return datetime.strptime(name[4:19], "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def main():
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
    meta = []
    for n in files:
        with Image.open(os.path.join(SRC, n)) as raw:
            im = ImageOps.exif_transpose(raw)
            small = im.copy()
            small.thumbnail((900, 900), Image.LANCZOS)
            sharp = ImageStat.Stat(small.convert("L").filter(ImageFilter.FIND_EDGES)).stddev[0]
            meta.append({"name": n, "hash": dhash(small), "sharp": round(sharp, 2),
                         "t": stamp(n)})

    groups, cur = [], [meta[0]]
    for prev, m in zip(meta, meta[1:]):
        close = (m["t"] and prev["t"] and (m["t"] - prev["t"]).total_seconds() <= GAP)
        same = int((m["hash"] != prev["hash"]).sum()) <= HAM
        if close and same:
            cur.append(m)
        else:
            groups.append(cur)
            cur = [m]
    groups.append(cur)

    best = os.path.join(OUT, "best")
    os.makedirs(best, exist_ok=True)
    for f in os.listdir(best):
        os.remove(os.path.join(best, f))

    picked, report = [], []
    for i, g in enumerate(groups, 1):
        win = max(g, key=lambda m: m["sharp"])
        picked.append(win["name"])
        report.append({"group": i, "kept": win["name"], "sharp": win["sharp"],
                       "dropped": [m["name"] for m in g if m is not win]})
        srcp = os.path.join(OUT, "post", win["name"])
        if os.path.exists(srcp):
            shutil.copy2(srcp, os.path.join(best, f"{i:02d}_{win['name']}"))

    with open(os.path.join(SP, "curate_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("shots:", len(files), "-> groups:", len(groups), "| kept:", len(picked))
    for r in report:
        if r["dropped"]:
            print(f"  group {r['group']:>2}: kept {r['kept']}  (dropped {len(r['dropped'])})")


if __name__ == "__main__":
    main()
