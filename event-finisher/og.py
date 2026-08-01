# -*- coding: utf-8 -*-
r"""The share card for tkawen.com — 1200x630, rendered by Chrome (Arabic/RTL).

Scale is shown, not claimed: the eleven real product marks in one row under the
mother mark. Only facts that are on the site already appear as text.
"""
import base64, os, subprocess, sys, tempfile

SP = os.path.dirname(os.path.abspath(__file__))
BRAND = r"D:\PROJECTS\04-TKAWEN-ECOSYSTEM\tkawen-brand\exports"
FONTS = r"D:\PROJECTS\04-TKAWEN-ECOSYSTEM\tkawen-blog\dist\fonts"
CAIRO_AR = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscQyyS4J0.woff2"
CAIRO_LA = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscRiyS.woff2"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1200, 630

PRODUCTS = ["mystoq", "liqaa", "certify", "academy", "pharmapro", "facture",
            "id", "trust", "voice", "studio", "connect"]


def b64(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def build(out_png, variant="ar"):
    ar, la = (b64(os.path.join(FONTS, f), "font/woff2") for f in (CAIRO_AR, CAIRO_LA))
    logo = b64(os.path.join(SP, "logo.png"), "image/png")
    marks = "".join(
        f'<img class="m" src="{b64(os.path.join(BRAND, p, "mark-512.png"), "image/png")}">'
        for p in PRODUCTS)

    if variant == "ar":
        head = "منظومة رقمية جزائرية واحدة"
        sub = "نبني · نُكوّن · نُوثّق · نُقرّب المسافات"
        # every claim here is already published on the site itself
        chips = ["علامة مؤسّسة ناشئة · 0108242769", "D-U-N-S® 35-355-1313", "عنّابة · الجزائر"]
        direction = "rtl"
    else:
        head = "One Algerian digital ecosystem"
        sub = "We build · we train · we certify · we connect"
        chips = ["Startup label · 0108242769", "D-U-N-S® 35-355-1313", "Annaba · Algeria"]
        direction = "ltr"

    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    doc = f"""<meta charset="utf-8"><style>
 @font-face{{font-family:'Cairo';src:url('{ar}') format('woff2');font-weight:200 1000}}
 @font-face{{font-family:'Cairo';src:url('{la}') format('woff2');font-weight:200 1000;
            unicode-range:U+0000-00FF,U+2000-206F}}
 *{{margin:0;padding:0;box-sizing:border-box}}
 body{{width:{W}px;height:{H}px;direction:{direction};font-family:'Cairo',sans-serif;
   background:#050c1e;color:#fff;overflow:hidden}}
 .card{{position:relative;width:100%;height:100%;padding:54px 64px 46px;
   display:flex;flex-direction:column;justify-content:space-between;
   background:
     radial-gradient(58% 78% at 82% 6%,rgba(59,130,246,.34),transparent 62%),
     radial-gradient(46% 62% at 8% 96%,rgba(29,78,216,.30),transparent 64%),
     linear-gradient(150deg,#081633 0%,#0a1c3f 46%,#050c1e 100%)}}
 .grid{{position:absolute;inset:0;opacity:.16;
   background-image:radial-gradient(rgba(147,197,253,.55) 1px,transparent 1px);
   background-size:26px 26px}}
 .top{{display:flex;align-items:center;justify-content:space-between;z-index:1}}
 .logo{{height:62px}}
 .badge{{font-size:19px;font-weight:700;color:rgba(214,229,255,.86);
   border:1px solid rgba(147,197,253,.34);border-radius:999px;padding:9px 20px;
   background:rgba(147,197,253,.08)}}
 .mid{{z-index:1;margin-top:-6px}}
 h1{{font-size:{62 if variant == 'ar' else 56}px;font-weight:900;line-height:1.16;
   letter-spacing:-1.4px}}
 .sub{{margin-top:14px;font-size:27px;font-weight:600;color:rgba(206,224,255,.82)}}
 .rule{{width:118px;height:6px;border-radius:4px;background:#f5b13d;margin-top:22px}}
 .row{{display:flex;gap:15px;align-items:center;z-index:1;margin-top:6px}}
 .m{{width:86px;height:86px;filter:drop-shadow(0 9px 18px rgba(0,0,0,.48))}}
 .foot{{display:flex;align-items:center;justify-content:space-between;z-index:1;
   border-top:1px solid rgba(147,197,253,.20);padding-top:18px}}
 .chips{{display:flex;gap:10px;flex-wrap:wrap}}
 .chip{{font-size:17px;font-weight:700;color:rgba(214,229,255,.80);
   border:1px solid rgba(147,197,253,.26);border-radius:999px;padding:7px 15px}}
 .site{{font-size:29px;font-weight:900;letter-spacing:.4px;direction:ltr}}
</style>
<div class="card">
  <div class="grid"></div>
  <div class="top">
    <img class="logo" src="{logo}">
    <div class="badge">Engineering Trust, Empowering Minds</div>
  </div>
  <div class="mid">
    <h1>{head}</h1>
    <div class="sub">{sub}</div>
    <div class="rule"></div>
  </div>
  <div class="row">{marks}</div>
  <div class="foot">
    <div class="chips">{chip_html}</div>
    <div class="site">tkawen.com</div>
  </div>
</div>"""
    hp = os.path.join(tempfile.gettempdir(), f"og_{variant}.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(doc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={W},{H}",
                    "--virtual-time-budget=5000", f"--screenshot={out_png}",
                    "file:///" + hp.replace("\\", "/")], capture_output=True)
    return out_png


if __name__ == "__main__":
    for v in (sys.argv[1:] or ["ar", "en"]):
        p = build(os.path.join(SP, f"og-tkawen-{v}.png"), v)
        print(p, os.path.getsize(p) // 1024, "KB")
