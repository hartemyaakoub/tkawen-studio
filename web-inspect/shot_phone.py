# -*- coding: utf-8 -*-
r"""True phone-width screenshot.

--window-size below the OS minimum (504 px on Windows) does NOT shrink the
render: Chrome lays out at 504 and the saved PNG is cropped to the requested
width, which in an RTL page slices off the right — it looks like an overflow
bug that isn't there. Rendering inside an exact-width iframe avoids that.
"""
import os, re, subprocess, sys, tempfile, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL, W, H, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
TMP = tempfile.gettempdir()

html = urllib.request.urlopen(urllib.request.Request(
    URL, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}),
    timeout=40).read().decode("utf-8", "replace")
base = re.match(r"(https?://[^/]+)", URL).group(1)
html = html.replace("<head>", f'<head><base href="{base}/">', 1)
inner = os.path.join(TMP, "phone_inner.html")
open(inner, "w", encoding="utf-8").write(html)

wrap = os.path.join(TMP, "phone_wrap.html")
open(wrap, "w", encoding="utf-8").write(
    f"""<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;background:#0b0f19}}
iframe{{width:{W}px;height:{H}px;border:0;display:block}}</style>
<iframe src="file:///{inner.replace(chr(92), '/')}" scrolling="no"></iframe>""")

subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--allow-file-access-from-files", f"--window-size={W},{H}",
                "--virtual-time-budget=12000", f"--screenshot={OUT}",
                "file:///" + wrap.replace("\\", "/")], capture_output=True)
print(OUT, os.path.getsize(OUT) // 1024, "KB")
