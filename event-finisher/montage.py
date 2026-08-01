# -*- coding: utf-8 -*-
r"""One organised 9:16 film out of the day's clips.

title card -> best segment of each clip (fade in/out, loudness-normalised)
-> closing card with the verification QR.

Everything is re-encoded to identical parameters first, so the final join is a
stream copy (fast, frame-accurate, no drift).

out: D:\f05\_out\film\tkawen-barber-graduation.mp4
"""
import base64, json, os, subprocess, tempfile

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
REEL = os.path.join(OUT, "reel")
SP = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FONTS = r"D:\PROJECTS\04-TKAWEN-ECOSYSTEM\tkawen-blog\dist\fonts"
CAIRO_AR = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscQyyS4J0.woff2"
CAIRO_LA = "SLXVc1nY6HkvangtZmpQdkhzfH5lkSscRiyS.woff2"
LOGO = os.path.join(SP, "logo.png")
W, H, FPS = 1080, 1920, 30
SEG = 8.0            # seconds taken from each clip
VERIFY = "https://tkawen.com/verify"
WORK = os.path.join(tempfile.gettempdir(), "tkawen_film")


def b64(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def qr_png():
    import qrcode
    p = os.path.join(WORK, "qr.png")
    if not os.path.exists(p):
        q = qrcode.QRCode(box_size=14, border=1,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(VERIFY)
        q.make(fit=True)
        q.make_image(fill_color="#0b1a3a", back_color="#ffffff").save(p)
    return p


def card_png(kind):
    """kind = 'intro' | 'outro' -> a 1080x1920 PNG rendered by Chrome (Arabic/RTL)."""
    ar, la = (b64(os.path.join(FONTS, f), "font/woff2") for f in (CAIRO_AR, CAIRO_LA))
    logo = b64(LOGO, "image/png")
    qr = b64(qr_png(), "image/png")
    if kind == "intro":
        middle = """
        <div class="kicker">حفل التخرّج وتسليم الشهادات</div>
        <div class="big">دورة الحلاقة<br>العصرية</div>
        <div class="rule"></div>
        <div class="meta">29 جويلية 2026 · عنّابة · الجزائر</div>"""
        foot = '<div class="site">tkawen.com</div>'
    else:
        middle = """
        <div class="kicker">كلّ شهادة قابلة للتحقّق</div>
        <div class="big">مبروك<br>للمتخرّجين</div>
        <div class="rule"></div>
        <div class="meta">امسح الرمز للتحقّق من أيّ شهادة</div>
        <img class="qr" src="%s">""" % qr
        foot = '<div class="site">tkawen.com/verify</div>'
    doc = f"""<meta charset="utf-8"><style>
 @font-face{{font-family:'Cairo';src:url('{ar}') format('woff2');font-weight:200 1000}}
 @font-face{{font-family:'Cairo';src:url('{la}') format('woff2');font-weight:200 1000;
            unicode-range:U+0000-00FF,U+2000-206F}}
 *{{margin:0;padding:0;box-sizing:border-box}}
 body{{width:{W}px;height:{H}px;direction:rtl;font-family:'Cairo',sans-serif;
   background:radial-gradient(120% 80% at 20% 8%,#12326b 0%,#0a1a3c 45%,#050c1e 100%);
   color:#fff;display:flex;flex-direction:column;align-items:center;
   justify-content:space-between;padding:130px 80px 110px;text-align:center}}
 .logo{{height:96px}}
 .kicker{{font-size:38px;font-weight:700;color:rgba(214,229,255,.80)}}
 .big{{margin-top:26px;font-size:104px;font-weight:900;line-height:1.08;letter-spacing:-2px}}
 .rule{{width:150px;height:7px;border-radius:5px;background:#f5b13d;margin:40px auto 34px}}
 .meta{{font-size:36px;font-weight:600;color:rgba(214,229,255,.78)}}
 .qr{{width:250px;height:250px;background:#fff;border-radius:20px;padding:14px;margin-top:52px}}
 .site{{font-size:40px;font-weight:800;letter-spacing:.5px;direction:ltr}}
</style>
<img class="logo" src="{logo}">
<div>{middle}</div>
{foot}"""
    hp = os.path.join(WORK, f"{kind}.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(doc)
    png = os.path.join(WORK, f"{kind}.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={W},{H}",
                    "--virtual-time-budget=4000", f"--screenshot={png}",
                    "file:///" + hp.replace("\\", "/")], capture_output=True)
    return png


VENC = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-video_track_timescale", "30000",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", "-show_streams", path], capture_output=True, text=True)
    j = json.loads(r.stdout)
    return float(j["format"]["duration"]), any(s["codec_type"] == "audio" for s in j["streams"])


def card_clip(png, seconds, out):
    """Still -> clip with a slow push-in, silent stereo track for concat parity."""
    zoom = f"zoompan=z='min(zoom+0.0006,1.06)':d={int(seconds * FPS)}:s={W}x{H}:fps={FPS}"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(seconds), "-i", png,
                    "-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", f"{zoom},fade=t=in:st=0:d=0.4,fade=t=out:st={seconds - 0.4:.2f}:d=0.4",
                    *VENC, "-shortest", out], capture_output=True)


def segment(src, out):
    d, has_audio = dur(src)
    if d < 1.0:
        return None
    take = min(SEG, max(1.0, d - 0.3))
    start = max(0.0, min(d * 0.15, d - take))
    fade = min(0.30, take / 6)
    cmd = ["ffmpeg", "-y", "-ss", f"{start:.2f}", "-t", f"{take:.2f}", "-i", src]
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{take:.2f}", "-i", "anullsrc=r=48000:cl=stereo"]
    # fps first, then TIME-based fades: frame-indexed fades assume 30 fps, but the
    # clips run at 33 and 60 fps, so a frame index landed mid-clip and stayed black.
    cmd += ["-vf", f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
                   f"crop={W}:{H},fade=t=in:st=0:d={fade:.2f},"
                   f"fade=t=out:st={take - fade:.2f}:d={fade:.2f}",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11" if has_audio else "anull",
            *VENC, "-shortest", out]
    subprocess.run(cmd, capture_output=True)
    return out if os.path.exists(out) and os.path.getsize(out) > 10000 else None


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.join(OUT, "film"), exist_ok=True)
    parts = []

    intro = os.path.join(WORK, "intro.mp4")
    card_clip(card_png("intro"), 3.4, intro)
    parts.append(intro)

    for i, n in enumerate(sorted(os.listdir(REEL))):
        seg = segment(os.path.join(REEL, n), os.path.join(WORK, f"seg{i:02d}.mp4"))
        if seg:
            parts.append(seg)
            print("segment", n, flush=True)
        else:
            print("skipped (too short/broken):", n, flush=True)

    outro = os.path.join(WORK, "outro.mp4")
    card_clip(card_png("outro"), 4.0, outro)
    parts.append(outro)

    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '" + p.replace("\\", "/") + "'\n")
    dst = os.path.join(OUT, "film", "tkawen-barber-graduation.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-movflags", "+faststart", dst], capture_output=True)
    print("film:", dst, round(os.path.getsize(dst) / 1048576, 1), "MB",
          round(dur(dst)[0], 1), "s")


if __name__ == "__main__":
    main()
