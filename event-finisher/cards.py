# -*- coding: utf-8 -*-
r"""TKAWEN graduation cards — 1080x1350, rendered by headless Chrome.

Chrome (not PIL) does the Arabic: PIL draws letters isolated and left-to-right,
which is exactly the RTL trap. Cairo woff2 is embedded as base64 so the render
never depends on the network.

Photo source = D:\f05\_out\post (already graded). Cropped square FROM THE TOP,
which also leaves the post watermark outside the card, so the mark appears once.

out: D:\f05\_out\cards\<theme>\<name>.png
"""
import base64, os, subprocess, sys, tempfile
from PIL import Image

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
POST = os.path.join(OUT, "post")
SP = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FONTS = r"D:\PROJECTS\04-TKAWEN-ECOSYSTEM\tkawen-blog\dist\fonts"
CAIRO_AR = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscQyyS4J0.woff2"   # arabic subset
CAIRO_LA = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscRiyS.woff2"      # latin subset
LOGO = os.path.join(SP, "logo.png")

W, H = 1080, 1350
COURSE = "دورة الحلاقة العصرية"
DATE = "29 جويلية 2026"
PLACE = "عنّابة · الجزائر"
# HEAD-checked 200 with a real title («تحقّق من صحّة أيّ شهادة معتمدة») before printing it
VERIFY = "https://tkawen.com/verify"


def qr_uri(data, dark="#0b1a3a", light="#ffffff"):
    """A card that claims 'verified' has to carry the way to verify it."""
    import qrcode
    path = os.path.join(tempfile.gettempdir(), "card_qr_%x.png" % (hash(data + dark) & 0xffffff))
    if not os.path.exists(path):
        q = qrcode.QRCode(version=None, box_size=12, border=1,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(data)
        q.make(fit=True)
        q.make_image(fill_color=dark, back_color=light).save(path)
    return b64(path, "image/png")


def b64(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def square_top(path, size=1000):
    """Square crop from the top of the 4:5 post frame -> heads + certificate,
    watermark excluded."""
    with Image.open(path) as im:
        w, h = im.size
        side = min(w, h)
        im = im.crop((max(0, (w - side) // 2), 0, max(0, (w - side) // 2) + side, side))
        im = im.resize((size, size), Image.LANCZOS)
        tmp = os.path.join(tempfile.gettempdir(), "card_photo.jpg")
        im.save(tmp, quality=94)
        return b64(tmp, "image/jpeg")


THEMES = {
    # name: (page bg, card bg, ink, muted, hair-line, accent)
    "navy": ("#050b1a", "linear-gradient(160deg,#0b1a3a 0%,#102a5c 48%,#0a1730 100%)",
             "#ffffff", "rgba(226,236,255,.72)", "rgba(147,197,253,.22)", "#f5b13d"),
    "light": ("#eef2f8", "linear-gradient(160deg,#ffffff 0%,#f4f7fc 100%)",
              "#0b1533", "rgba(28,45,84,.66)", "rgba(11,26,58,.10)", "#c98a14"),
}


def html(photo_uri, theme):
    bg, card, ink, muted, line, accent = THEMES[theme]
    ar = b64(os.path.join(FONTS, CAIRO_AR), "font/woff2")
    la = b64(os.path.join(FONTS, CAIRO_LA), "font/woff2")
    logo = b64(LOGO, "image/png")
    qr = qr_uri(VERIFY, dark="#0b1a3a" if theme == "navy" else "#12203f")
    logo_filter = "" if theme == "navy" else "filter:brightness(.42) saturate(1.5);"
    return f"""<meta charset="utf-8">
<style>
  @font-face {{ font-family:'Cairo'; src:url('{ar}') format('woff2');
               font-weight:200 1000; font-display:block; }}
  @font-face {{ font-family:'Cairo'; src:url('{la}') format('woff2');
               font-weight:200 1000; font-display:block;
               unicode-range:U+0000-00FF,U+2000-206F; }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{width:{W}px;height:{H}px;background:{bg};font-family:'Cairo',sans-serif;
        direction:rtl;-webkit-font-smoothing:antialiased}}
  .card{{position:relative;width:100%;height:100%;background:{card};overflow:hidden;
         display:flex;flex-direction:column;padding:44px 44px 34px}}
  .glow{{position:absolute;width:760px;height:760px;border-radius:50%;
         background:radial-gradient(circle,rgba(59,130,246,.30),transparent 65%);
         top:-330px;left:-240px;pointer-events:none}}
  .head{{display:flex;align-items:center;justify-content:space-between;
         padding-bottom:18px;border-bottom:1px solid {line}}}
  .logo{{height:52px;{logo_filter}}}
  .kicker{{font-size:22px;font-weight:700;color:{muted};letter-spacing:.2px}}
  .frame{{margin-top:22px;border-radius:22px;overflow:hidden;
          border:1px solid {line};box-shadow:0 26px 60px rgba(0,0,0,.34)}}
  .frame img{{display:block;width:100%;height:772px;object-fit:cover;object-position:50% 22%}}
  .body{{flex:1;display:flex;flex-direction:column;justify-content:center;
         align-items:center;text-align:center;padding-top:20px}}
  .title{{font-size:62px;font-weight:900;color:{ink};line-height:1.05;
          letter-spacing:-1px}}
  .rule{{width:96px;height:5px;border-radius:4px;background:{accent};margin:16px 0 14px}}
  .course{{font-size:31px;font-weight:800;color:{ink};opacity:.95}}
  .meta{{margin-top:8px;font-size:21px;font-weight:600;color:{muted}}}
  .foot{{display:flex;align-items:center;justify-content:space-between;
         padding-top:16px;border-top:1px solid {line}}}
  .badge{{display:flex;align-items:center;gap:9px;font-size:19px;font-weight:700;
          color:{ink};background:rgba(245,177,61,.14);border:1px solid {accent};
          padding:8px 15px;border-radius:999px}}
  .dot{{width:9px;height:9px;border-radius:50%;background:{accent}}}
  .site{{font-size:23px;font-weight:800;color:{ink};letter-spacing:.4px;direction:ltr}}
  .verify{{display:flex;align-items:center;gap:13px}}
  .qr{{width:84px;height:84px;background:#fff;border-radius:10px;padding:5px;
        box-shadow:0 6px 18px rgba(0,0,0,.28)}}
  .vt{{font-size:19px;font-weight:800;color:{ink};line-height:1.25}}
  .vu{{font-size:17px;font-weight:700;color:{muted};direction:ltr;text-align:right;
       letter-spacing:.2px}}
</style>
<div class="card">
  <div class="glow"></div>
  <div class="head">
    <img class="logo" src="{logo}">
    <div class="kicker">حفل التخرّج وتسليم الشهادات</div>
  </div>
  <div class="frame"><img src="{photo_uri}"></div>
  <div class="body">
    <div class="title">مبروك التخرّج</div>
    <div class="rule"></div>
    <div class="course">{COURSE}</div>
    <div class="meta">{DATE} &nbsp;·&nbsp; {PLACE}</div>
  </div>
  <div class="foot">
    <div class="verify">
      <img class="qr" src="{qr}">
      <div>
        <div class="vt">تحقّق من الشهادة</div>
        <div class="vu">tkawen.com/verify</div>
      </div>
    </div>
    <div class="badge"><span class="dot"></span>شهادة رقميّة موثّقة</div>
  </div>
</div>"""


def render(name, theme="navy"):
    dst_dir = os.path.join(OUT, "cards", theme)
    os.makedirs(dst_dir, exist_ok=True)
    doc = html(square_top(os.path.join(POST, name)), theme)
    tmp = os.path.join(tempfile.gettempdir(), f"card_{theme}.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc)
    dst = os.path.join(dst_dir, os.path.splitext(name)[0] + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={W},{H}",
                    "--virtual-time-budget=4000", f"--screenshot={dst}",
                    "file:///" + tmp.replace("\\", "/")],
                   capture_output=True)
    return dst


if __name__ == "__main__":
    args = sys.argv[1:]
    themes = [a[2:] for a in args if a.startswith("--")] or ["navy", "light"]
    names = [a for a in args if not a.startswith("--")]
    if not names:
        names = sorted(os.listdir(POST))
    for n in names:
        for t in themes:
            print(render(n, t), flush=True)
