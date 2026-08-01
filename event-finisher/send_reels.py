# -*- coding: utf-8 -*-
"""One sendVideo per clip with retries — an 82 MB media group gets the connection reset."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tg_send import post, CHAT

REEL = r"D:\f05\_out\reel"
files = sorted(os.listdir(REEL))
for i, n in enumerate(files, 1):
    p = os.path.join(REEL, n)
    mb = os.path.getsize(p) / 1048576
    cap = (f"<b>ريلز {i}/{len(files)}</b> · {mb:.1f} ميغابايت · 1080x1920" if i == 1 else
           f"{i}/{len(files)}")
    for attempt in (1, 2, 3):
        try:
            r = post("sendVideo", {"chat_id": CHAT, "caption": cap, "parse_mode": "HTML",
                                   "supports_streaming": "true"}, {"video": p})
            print(n, f"{mb:.1f}MB ok:", r.get("ok"), r.get("description", ""), flush=True)
            break
        except Exception as e:
            print(n, "attempt", attempt, "failed:", type(e).__name__, e, flush=True)
            time.sleep(4 * attempt)
