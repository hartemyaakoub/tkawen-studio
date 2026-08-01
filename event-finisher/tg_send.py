# -*- coding: utf-8 -*-
"""Send a review album to the founder's Telegram.
usage: tg_send.py "caption" file1 file2 ...
Uses sendMediaGroup (albums, <=10) so the phone shows them inline as one post.
"""
import json, mimetypes, os, sys, urllib.request, uuid

ENVP = r"C:\Users\YAAKOUB DEV\tkawen-remote-bot\bot.env"
d = {}
for line in open(ENVP, encoding="utf-8-sig"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
TOKEN, CHAT = d["TKAWEN_BOT_TOKEN"], d["TKAWEN_OWNER_CHAT_ID"]


def multipart(fields, files):
    b = "----" + uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += (f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    for name, path in files.items():
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        out += (f"--{b}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                f"filename=\"{os.path.basename(path)}\"\r\n"
                f"Content-Type: {mime}\r\n\r\n").encode()
        with open(path, "rb") as f:
            out += f.read()
        out += b"\r\n"
    out += f"--{b}--\r\n".encode()
    return out, "multipart/form-data; boundary=" + b


def post(method, fields, files):
    body, ctype = multipart(fields, files)
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}",
                                data=body, headers={"Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def send_album(caption, paths):
    for i in range(0, len(paths), 10):
        batch = paths[i:i + 10]
        media, files = [], {}
        for j, p in enumerate(batch):
            key = f"f{j}"
            files[key] = p
            item = {"type": "photo", "media": f"attach://{key}"}
            if i == 0 and j == 0 and caption:
                item["caption"] = caption
                item["parse_mode"] = "HTML"
            media.append(item)
        r = post("sendMediaGroup", {"chat_id": CHAT, "media": json.dumps(media)}, files)
        print("ok:", r.get("ok"), r.get("description", ""))


if __name__ == "__main__":
    cap, paths = sys.argv[1], [p for p in sys.argv[2:] if os.path.exists(p)]
    missing = [p for p in sys.argv[2:] if not os.path.exists(p)]
    if missing:
        print("MISSING:", missing)
    send_album(cap, paths)
