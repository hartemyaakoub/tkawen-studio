# -*- coding: utf-8 -*-
"""Phone-width measurement that does not depend on the OS window minimum:
the page is loaded in an iframe of the exact viewport, so vw/vmax units and
media queries resolve exactly as they would on the device.
"""
import os, re, subprocess, sys, tempfile, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = sys.argv[1] if len(sys.argv) > 1 else "https://id.tkawen.com/"
W = int(sys.argv[2]) if len(sys.argv) > 2 else 390
H = int(sys.argv[3]) if len(sys.argv) > 3 else 844
TMP = tempfile.gettempdir()

html = urllib.request.urlopen(urllib.request.Request(
    URL, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}),
    timeout=40).read().decode("utf-8", "replace")
base = re.match(r"(https?://[^/]+)", URL).group(1)
html = html.replace("<head>", f'<head><base href="{base}/">', 1)
inner = os.path.join(TMP, "inner.html")
open(inner, "w", encoding="utf-8").write(html)

WRAP = f"""<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;background:#222}} iframe{{width:{W}px;height:{H}px;border:0;display:block}}</style>
<iframe id="f" src="file:///{inner.replace(chr(92), '/')}"></iframe>
<pre id="out" style="color:#ddd;font:12px monospace;white-space:pre-wrap"></pre>
<script>
const f=document.getElementById('f');
f.addEventListener('load',()=>setTimeout(()=>{{
  const d=f.contentDocument, w=f.contentWindow, out=[];
  out.push('viewport='+w.innerWidth+'x'+w.innerHeight);
  out.push('scrollWidth='+d.documentElement.scrollWidth+'  overflow='+(d.documentElement.scrollWidth-w.innerWidth));
  const vw=w.innerWidth, bad=[];
  d.querySelectorAll('*').forEach(el=>{{
    const r=el.getBoundingClientRect();
    if(!r.width&&!r.height) return;
    const left=r.left+w.scrollX, right=r.right+w.scrollX;
    if(right>vw+1||left<-1){{
      const cs=w.getComputedStyle(el);
      bad.push({{t:el.tagName.toLowerCase()+(typeof el.className==='string'&&el.className?'.'+el.className.trim().split(/\\s+/).join('.'):''),
               l:Math.round(left),r:Math.round(right),wd:Math.round(r.width),pos:cs.position,ov:cs.overflow}});
    }}
  }});
  bad.sort((a,b)=>b.r-a.r);
  bad.slice(0,16).forEach(b=>out.push('OVER '+b.t.slice(0,64)+' | left='+b.l+' right='+b.r+' w='+b.wd+' pos='+b.pos+' ov='+b.ov));
  document.getElementById('out').textContent=out.join('\\n');
}},1200));
</script>"""
wrap = os.path.join(TMP, "wrap.html")
open(wrap, "w", encoding="utf-8").write(WRAP)

r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--window-size=1200,1400",
                    "--virtual-time-budget=12000", "--dump-dom",
                    "file:///" + wrap.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
m = re.search(r'<pre id="out"[^>]*>(.*?)</pre>', r.stdout or "", re.S)
print(m.group(1).replace("&amp;", "&").replace("&lt;", "<") if m else "(no output)")
