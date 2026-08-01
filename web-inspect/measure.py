# -*- coding: utf-8 -*-
"""Measure horizontal overflow on a live page without the browser extension:
fetch it, inject a measuring script, render it headless and read the DOM back.
"""
import os, re, subprocess, sys, tempfile, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SP = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[1] if len(sys.argv) > 1 else "https://id.tkawen.com/"
W = int(sys.argv[2]) if len(sys.argv) > 2 else 390
H = int(sys.argv[3]) if len(sys.argv) > 3 else 844

PROBE = """
<script>
window.addEventListener('load', function(){
  setTimeout(function(){
    var de=document.documentElement, out=[];
    out.push('viewport='+window.innerWidth+'x'+window.innerHeight);
    out.push('scrollWidth='+de.scrollWidth+'  overflow='+(de.scrollWidth-window.innerWidth));
    var vw=window.innerWidth, bad=[];
    document.querySelectorAll('*').forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.width===0&&r.height===0) return;
      var right=r.right+window.scrollX, left=r.left+window.scrollX;
      if(right>vw+1 || left<-1){
        var cs=getComputedStyle(el);
        bad.push({t:el.tagName.toLowerCase()+(el.className&&typeof el.className==='string'?'.'+el.className.trim().split(/\\s+/).join('.'):''),
                  l:Math.round(left),r:Math.round(right),w:Math.round(r.width),
                  pos:cs.position,ov:cs.overflow});
      }
    });
    bad.sort(function(a,b){return b.r-a.r});
    bad.slice(0,14).forEach(function(b){
      out.push('OVER '+b.t.slice(0,70)+' | left='+b.l+' right='+b.r+' w='+b.w+' pos='+b.pos+' ov='+b.ov);
    });
    var p=document.createElement('pre'); p.id='__probe__'; p.textContent=out.join('\\n');
    document.body.appendChild(p);
  }, 900);
});
</script>
"""

html = urllib.request.urlopen(urllib.request.Request(
    URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read().decode("utf-8", "replace")
html = html.replace("</body>", PROBE + "</body>") if "</body>" in html else html + PROBE
# make relative asset urls absolute so layout matches production
base = re.match(r"(https?://[^/]+)", URL).group(1)
html = html.replace("<head>", f'<head><base href="{base}/">', 1)

tmp = os.path.join(tempfile.gettempdir(), "probe.html")
open(tmp, "w", encoding="utf-8").write(html)
# --screenshot forces the viewport to --window-size; without it Chrome opens at
# the OS minimum window width (504 px here) and every measurement is wrong.
shot = os.path.join(tempfile.gettempdir(), "probe.png")
r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={W},{H}", "--virtual-time-budget=9000",
                    f"--screenshot={shot}",
                    "--dump-dom", "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
m = re.search(r'<pre id="__probe__">(.*?)</pre>', r.stdout or "", re.S)
print(m.group(1).replace("&amp;", "&").replace("&lt;", "<") if m else
      "(probe did not run)\n" + (r.stdout or "")[:400])
