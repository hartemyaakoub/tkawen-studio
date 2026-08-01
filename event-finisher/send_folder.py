# -*- coding: utf-8 -*-
"""Send a folder to Telegram in small albums, with retries and a resume marker.

usage: send_folder.py <folder> [per_album] [caption]
Small batches on purpose: this uplink drops the connection past ~20 MB per request.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tg_send import post, CHAT

folder = sys.argv[1]
per = int(sys.argv[2]) if len(sys.argv) > 2 else 3
caption = sys.argv[3] if len(sys.argv) > 3 else ""
files = [os.path.join(folder, f) for f in sorted(os.listdir(folder))
         if f.lower().endswith((".jpg", ".jpeg", ".png"))]
done_marker = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "sent_" + os.path.basename(folder.rstrip("\\/")) + ".txt")
sent = set()
if os.path.exists(done_marker):
    sent = set(open(done_marker, encoding="utf-8").read().split("\n"))
files = [f for f in files if os.path.basename(f) not in sent]
print("to send:", len(files), "in albums of", per, flush=True)

for i in range(0, len(files), per):
    batch = files[i:i + per]
    mb = sum(os.path.getsize(p) for p in batch) / 1048576
    media, attach = [], {}
    for j, p in enumerate(batch):
        attach[f"f{j}"] = p
        item = {"type": "photo", "media": f"attach://f{j}"}
        if i == 0 and j == 0 and caption:
            item.update(caption=caption, parse_mode="HTML")
        media.append(item)
    for attempt in (1, 2, 3):
        try:
            r = post("sendMediaGroup", {"chat_id": CHAT, "media": json.dumps(media)}, attach)
            ok = r.get("ok")
            print(f"album {i // per + 1}: {len(batch)} files, {mb:.1f} MB ->", ok,
                  r.get("description", ""), flush=True)
            if ok:
                with open(done_marker, "a", encoding="utf-8") as f:
                    for p in batch:
                        f.write(os.path.basename(p) + "\n")
            break
        except Exception as e:
            print(f"album {i // per + 1} attempt {attempt}: {type(e).__name__}", flush=True)
            time.sleep(6 * attempt)
    time.sleep(2)          # stay under the per-chat flood limit
print("finished", flush=True)
