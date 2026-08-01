# -*- coding: utf-8 -*-
r"""Finish the 10 course videos with ffmpeg.

per clip:  light denoise -> tone/contrast/saturation -> unsharp -> TKAWEN watermark
           -> h264 CRF 20 faststart  (audio kept)
plus       a 9:16 reel (photo over its own blurred zoom) for every clip <= 75 s

out:  D:\f05\_out\video\<name>.mp4        (native frame, enhanced + watermark)
      D:\f05\_out\reel\<name>.mp4         (1080x1920)
"""
import json, os, subprocess, sys
from PIL import Image

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
SP = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(SP, "logo.png")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_streams", "-show_format", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    fr = v.get("r_frame_rate", "30/1").split("/")
    return {
        "w": v["width"], "h": v["height"], "rot": rot,
        "dur": float(j["format"].get("duration", 0)),
        "fps": round(float(fr[0]) / float(fr[1] or 1), 2),
        "audio": any(s["codec_type"] == "audio" for s in j["streams"]),
        "codec": v["codec_name"],
    }


def logo_png(width):
    """Watermark sized for this video, cached on disk."""
    p = os.path.join(SP, f"logo_{width}.png")
    if not os.path.exists(p):
        lg = Image.open(LOGO).convert("RGBA")
        lg = lg.crop(lg.getbbox())
        lg = lg.resize((width, round(width * lg.height / lg.width)), Image.LANCZOS)
        lg.save(p)
    return p


# brighter, phone-like: gamma lifts the mid-tones (faces) instead of contrast
# crushing them, which is what made the first pass look dark.
GRADE = "hqdn3d=1.2:1.2:4:4,eq=contrast=1.04:brightness=0.045:saturation=1.14:gamma=1.10," \
        "unsharp=5:5:0.7:3:3:0.35"


def run(cmd, log):
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n$ " + " ".join(cmd) + "\n")
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode


def main():
    os.makedirs(os.path.join(OUT, "video"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "reel"), exist_ok=True)
    log = os.path.join(SP, "video.log")
    vids = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
    report = []
    for n in vids:
        src = os.path.join(SRC, n)
        info = probe(src)
        # displayed geometry after rotation metadata is applied
        dw, dh = (info["h"], info["w"]) if info["rot"] in (90, -90, 270) else (info["w"], info["h"])
        wm = logo_png(max(140, int(dw * 0.17)))
        mar = int(dw * 0.030)
        stem = os.path.splitext(n)[0]

        dst = os.path.join(OUT, "video", stem + ".mp4")
        cmd = ["ffmpeg", "-y", "-i", src, "-i", wm,
               "-filter_complex", f"[0:v]{GRADE}[v];[v][1:v]overlay=W-w-{mar}:H-h-{mar}",
               "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        cmd += (["-c:a", "aac", "-b:a", "128k"] if info["audio"] else ["-an"])
        cmd += [dst]
        rc = run(cmd, log)

        rc2 = None
        if info["dur"] <= 75:
            rdst = os.path.join(OUT, "reel", stem + ".mp4")
            wm2 = logo_png(300)
            reel = (
                "[0:v]split=2[bg][fg];"
                "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,gblur=sigma=26,eq=brightness=-0.10[bgb];"
                f"[fg]{GRADE},scale=1040:-2[fgs];"
                "[bgb][fgs]overlay=(W-w)/2:(H-h)/2[base];"
                "[base][1:v]overlay=W-w-40:H-h-70"
            )
            c2 = ["ffmpeg", "-y", "-i", src, "-i", wm2, "-filter_complex", reel,
                  "-c:v", "libx264", "-crf", "21", "-preset", "veryfast",
                  "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
            c2 += (["-c:a", "aac", "-b:a", "128k"] if info["audio"] else ["-an"])
            c2 += [rdst]
            rc2 = run(c2, log)

        report.append({"name": n, **info, "disp": f"{dw}x{dh}", "rc": rc, "reel_rc": rc2,
                       "out_mb": round(os.path.getsize(dst) / 1048576, 1) if rc == 0 else None})
        print(json.dumps(report[-1], ensure_ascii=False), flush=True)

    with open(os.path.join(SP, "video_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())
