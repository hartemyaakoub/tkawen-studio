# -*- coding: utf-8 -*-
r"""The showreel: every photo of the day, cut on the beat, over an original score.

Frames are composed in PIL and piped raw into ffmpeg, so the motion (Ken Burns,
dissolves, downbeat punch) is exact instead of approximated by filter chains.

Photo source = _out\post, with the bottom 11% cropped away — that removes the
still's own watermark, so the film carries ONE persistent mark of its own.

out: D:\f05\_out\film\tkawen-showreel.mp4        (with score)
     D:\f05\_out\film\tkawen-showreel-silent.mp4 (for platform audio)
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageOps

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
POST = os.path.join(OUT, "post")
SP = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(SP, "logo.png")

W, H, FPS = 1080, 1920, 30
BPM = 100.0
BEAT_F = round(60.0 / BPM * FPS)          # 18 frames = one beat
XF = 5                                    # dissolve frames
INTRO_BEATS, OUTRO_BEATS = 5, 5
ZOOM_MAX = 1.16


def prep(path):
    """4:5 still -> a 9:16 plate at zoom headroom, watermark cropped off."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        im = im.crop((0, 0, w, int(h * 0.89)))          # drop the still's watermark
        w, h = im.size
        tw = h * W / H                                   # target 9:16 window
        if tw <= w:
            x = (w - tw) / 2
            im = im.crop((int(x), 0, int(x + tw), h))
        else:
            th = w * H / W
            im = im.crop((0, 0, w, int(th)))
        return im.resize((int(W * ZOOM_MAX), int(H * ZOOM_MAX)), Image.LANCZOS)


def ken(plate, t, direction):
    """t in 0..1 -> one frame, zooming and drifting."""
    z = 1.0 + 0.13 * (t if direction > 0 else (1 - t))   # 1.00 -> 1.13
    # the plate is exactly ZOOM_MAX, so at z=1 the window equals it to within a
    # rounding fraction — clamp, or PIL rejects the box as negative
    cw = min(W * ZOOM_MAX / z, plate.width)
    ch = min(H * ZOOM_MAX / z, plate.height)
    max_x = max(plate.width - cw, 0.0)
    max_y = max(plate.height - ch, 0.0)
    px = 0.5 + 0.16 * (t - 0.5) * direction
    py = 0.42 + 0.10 * (t - 0.5) * direction
    x = float(np.clip(px * max_x, 0, max_x))
    y = float(np.clip(py * max_y, 0, max_y))
    return plate.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def card_plate(png):
    im = Image.open(png).convert("RGB").resize((int(W * ZOOM_MAX), int(H * ZOOM_MAX)), Image.LANCZOS)
    return im


def brand_layer():
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    lw = int(W * 0.20)
    lg = lg.resize((lw, round(lw * lg.height / lg.width)), Image.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(lg, (int(W * 0.045), H - lg.height - int(W * 0.055)), lg)
    a = np.asarray(layer).astype(np.float32)
    a[..., 3] *= 0.82
    return Image.fromarray(a.astype(np.uint8))


def main():
    sys.path.insert(0, SP)
    import montage                                   # reuse the Chrome card renderer
    os.makedirs(montage.WORK, exist_ok=True)
    intro_png, outro_png = montage.card_png("intro"), montage.card_png("outro")

    files = [os.path.join(POST, f) for f in sorted(os.listdir(POST)) if f.endswith(".jpg")]
    holds = []
    for f in files:
        with Image.open(f) as im:
            hero = im.width >= im.height * 0.95       # the group shots breathe longer
        holds.append(BEAT_F * (2 if hero else 1))
    total = INTRO_BEATS * BEAT_F + sum(holds) + OUTRO_BEATS * BEAT_F
    seconds = total / FPS
    print(f"{len(files)} photos | {seconds:.1f}s | {total} frames", flush=True)

    score = os.path.join(montage.WORK, "score.wav")
    subprocess.run([sys.executable, os.path.join(SP, "music.py"), f"{seconds:.2f}", score],
                   check=True)

    os.makedirs(os.path.join(OUT, "film"), exist_ok=True)
    silent = os.path.join(OUT, "film", "tkawen-showreel-silent.mp4")
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "23", "-preset", "slow",
         "-maxrate", "5500k", "-bufsize", "11000k",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    brand = brand_layer()
    prev_tail = []          # frames held back for the dissolve
    beat_i = 0

    def emit(arr):
        p.stdin.write(arr.astype(np.uint8).tobytes())

    def shot(plate, nframes, direction, punch=True, brandit=True):
        """Emits EXACTLY nframes so every cut stays on the beat. The XF extra
        frames are rendered only to be dissolved into by the next shot — if the
        dissolve ate frames out of the shot itself, the cadence would drift to
        (beat - XF) and the edit would fall off the music."""
        nonlocal prev_tail, beat_i
        frames = []
        for k in range(nframes + XF):
            t = k / max(nframes + XF - 1, 1)
            fr = ken(plate, t, direction)
            if brandit:
                fr = Image.alpha_composite(fr.convert("RGBA"), brand).convert("RGB")
            a = np.asarray(fr, np.float32)
            # a 2-frame lift on every downbeat: the eye reads it as rhythm
            if punch and k == 0 and beat_i % 4 == 0:
                a = np.clip(a * 1.10 + 8, 0, 255)
            elif punch and k == 1 and beat_i % 4 == 0:
                a = np.clip(a * 1.05 + 4, 0, 255)
            frames.append(a)
        beat_i += max(1, nframes // BEAT_F)
        for i, tail in enumerate(prev_tail):       # dissolve in from the last shot
            if i < nframes:
                w = (i + 1) / (len(prev_tail) + 1)
                frames[i] = tail * (1 - w) + frames[i] * w
        for fr in frames[:nframes]:
            emit(fr)
        prev_tail = frames[nframes:]               # rendered, never emitted

    shot(card_plate(intro_png), INTRO_BEATS * BEAT_F, 1, punch=False, brandit=False)
    for i, f in enumerate(files):
        shot(prep(f), holds[i], 1 if i % 2 == 0 else -1)
        if i % 10 == 0:
            print("  frame set", i, "/", len(files), flush=True)
    shot(card_plate(outro_png), OUTRO_BEATS * BEAT_F, -1, punch=False, brandit=False)

    p.stdin.close()
    p.wait()

    scored = os.path.join(OUT, "film", "tkawen-showreel.mp4")
    subprocess.run(["ffmpeg", "-y", "-i", silent, "-i", score,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", scored], capture_output=True)
    for f in (silent, scored):
        print(os.path.basename(f), round(os.path.getsize(f) / 1048576, 1), "MB")


if __name__ == "__main__":
    main()
