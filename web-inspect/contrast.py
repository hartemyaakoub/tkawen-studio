# -*- coding: utf-8 -*-
"""WCAG contrast of the login page's text against its own background."""
import os, re, subprocess, sys, tempfile, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = sys.argv[1] if len(sys.argv) > 1 else "https://id.tkawen.com/"
TMP = tempfile.gettempdir()
html = urllib.request.urlopen(urllib.request.Request(
    URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read().decode("utf-8", "replace")
base = re.match(r"(https?://[^/]+)", URL).group(1)
html = html.replace("<head>", f'<head><base href="{base}/">', 1)
inner = os.path.join(TMP, "c_inner.html")
open(inner, "w", encoding="utf-8").write(html)

wrap = f"""<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0}}iframe{{width:1280px;height:800px;border:0}}</style>
<iframe src="file:///{inner.replace(chr(92), '/')}"></iframe>
<pre id="out" style="font:12px monospace;white-space:pre-wrap"></pre>
<script>
const f=document.querySelector('iframe');
f.addEventListener('load',()=>setTimeout(()=>{{
 const d=f.contentDocument,w=f.contentWindow,out=[];
 const lum=c=>{{const [r,g,b]=c.map(v=>{{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}});
   return .2126*r+.7152*g+.0722*b}};
 const parse=s=>(s.match(/[\\d.]+/g)||[0,0,0]).slice(0,3).map(Number);
 const bgOf=el=>{{let n=el;while(n&&n!==d.documentElement){{const c=w.getComputedStyle(n).backgroundColor;
   if(c&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c))return parse(c);n=n.parentElement}}return [11,15,25]}};
 const ratio=(a,b)=>{{const L1=lum(a),L2=lum(b);return ((Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05))}};
 const targets=[['.panel-sub','sub-heading'],['.hint','hint under button'],['label','field label'],
   ['.panel-h','heading'],['.hero-sub','hero text'],['.hero-foot','footer'],['.panel-back','back link'],
   ['.hero-feats li','feature item'],['.hero-eco-label','services label']];
 targets.forEach(([sel,name])=>{{const el=d.querySelector(sel);if(!el)return;
   const cs=w.getComputedStyle(el);const fg=parse(cs.color);const bg=bgOf(el);
   out.push(name.padEnd(20)+' '+cs.fontSize.padStart(7)+'  ratio '+ratio(fg,bg).toFixed(2)+
     (ratio(fg,bg)<4.5?'   ⚠ below 4.5':''));}});
 const inp=d.querySelector('input[type=email]');
 if(inp){{const ph=w.getComputedStyle(inp,'::placeholder');const fg=parse(ph.color);
   const bg=parse(w.getComputedStyle(inp).backgroundColor);
   out.push('placeholder'.padEnd(20)+' '+ph.fontSize.padStart(7)+'  ratio '+ratio(fg,bg).toFixed(2)+
     (ratio(fg,bg)<4.5?'   ⚠ below 4.5':''));}}
 document.getElementById('out').textContent=out.join('\\n');
}},1200));
</script>"""
wp = os.path.join(TMP, "c_wrap.html")
open(wp, "w", encoding="utf-8").write(wrap)
r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--window-size=1400,1000",
                    "--virtual-time-budget=12000", "--dump-dom",
                    "file:///" + wp.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
m = re.search(r'<pre id="out"[^>]*>(.*?)</pre>', r.stdout or "", re.S)
print(m.group(1) if m else "(no output)")
