# -*- coding: utf-8 -*-
"""TKAWEN course-photo finisher.

Real photographic retouch (no AI face regeneration — these are real trainees):
  white balance -> tonal stretch -> shadow lift -> soft S-curve -> shadow denoise
  -> clarity -> saturation -> sharpen -> smart crop -> TKAWEN watermark.

Outputs   D:\f05\_out\post   (4:5 feed, portraits smart-cropped; landscapes kept)
          D:\f05\_out\story (9:16, photo over its own blurred background)
Originals in D:\f05 are never modified.
"""
import os, sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

SRC = r"D:\f05"
OUT = os.path.join(SRC, "_out")
SP = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(SP, "logo.png")
FONT = r"C:\Windows\Fonts\seguisb.ttf"
Image.MAX_IMAGE_PIXELS = None

# ---------- tone ----------

LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


TARGET = 0.60          # where a phone puts the subject's mid-tone: bright, not washed


def _base_layer(Y, w, h):
    """Heavily blurred luminance = the 'where is it dark' map, computed at 1/8
    scale so a 100+ px blur costs nothing."""
    sw, sh = max(8, w // 8), max(8, h // 8)
    small = Image.fromarray((np.clip(Y, 0, 1) * 255).astype(np.uint8)).resize((sw, sh), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(max(6, sw // 10)))
    up = small.resize((w, h), Image.BILINEAR)
    return np.asarray(up, np.float32) / 255.0


def enhance(im, strength=1.0):
    """iPhone-style finish: local (not global) tone mapping, so faces come up
    without the scene going flat — and skin never gets darker than it was."""
    a = np.asarray(im.convert("RGB"), np.float32) / 255.0
    h, w, _ = a.shape

    # 1) white balance — damped gray-world, then a warm nudge (phones bias warm;
    #    a neutral grey-world on a white wall leaves skin cold and grey)
    core = a[h // 10:h * 9 // 10, w // 10:w * 9 // 10].reshape(-1, 3)
    means = core.mean(0)
    gain = (means.mean() / np.maximum(means, 1e-4)) ** 0.45
    a *= np.clip(gain, 0.95, 1.05)
    a *= np.array([1.022, 1.0, 0.982], np.float32)

    Y = np.maximum(a @ LUMA, 1e-4)

    # 2) black point only — never lift the white point (that is what burned skin)
    lo = np.percentile(Y, 0.3)
    a = np.clip((a - lo * 0.85) / (1 - lo * 0.85), 0, 1)
    Y = np.maximum(a @ LUMA, 1e-4)

    # 3) LOCAL tone map: lift dark neighbourhoods toward TARGET, leave bright ones
    Yb = _base_layer(Y, w, h)
    lift = np.clip((TARGET / np.maximum(Yb, 0.05)) ** (0.45 * strength), 0.95, 2.6)
    Ys = Y * lift
    # smooth shoulder so highlights roll off instead of clipping
    knee = 0.86
    Ys = np.where(Ys > knee, knee + (1 - knee) * np.tanh((Ys - knee) / (1 - knee)), Ys)

    # 4) auto-exposure on the subject area, gamma-style (cannot clip)
    cy, cx = slice(int(h * .15), int(h * .80)), slice(int(w * .12), int(w * .88))
    m = float(np.clip(Ys[cy, cx].mean(), 0.05, 0.95))
    g = np.log(max(TARGET, 1e-3)) / np.log(m)
    Ys = np.clip(Ys, 0, 1) ** np.clip(g, 0.72, 1.05)

    a = np.clip(a * (Ys / Y)[..., None], 0, 1)

    # 5) vibrance: boost dull colours, spare the already-saturated banner blue
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    Yb2 = (a @ LUMA)[..., None]
    boost = (1 + 0.26 * strength * (1 - sat))[..., None]
    a = np.clip(Yb2 + (a - Yb2) * boost, 0, 1)
    Ys = np.clip(a @ LUMA, 0, 1)

    out = Image.fromarray((a * 255 + 0.5).astype(np.uint8))

    # 6) denoise only where the lift raised noise (the dark 35%)
    med = out.filter(ImageFilter.MedianFilter(3))
    mask = np.clip((0.40 - Ys) / 0.40, 0, 1) ** 1.5
    o, m = np.asarray(out, np.float32), np.asarray(med, np.float32)
    out = Image.fromarray((o + (m - o) * (mask * 0.55)[..., None]).astype(np.uint8))

    # 7) clarity (big-radius local contrast) then edge sharpening
    out = out.filter(ImageFilter.UnsharpMask(radius=28, percent=int(22 * strength), threshold=2))
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=int(85 * strength), threshold=3))
    return out


# ---------- framing ----------

def energy_centroid_x(im):
    g = np.asarray(im.convert("L").resize((im.width // 8, im.height // 8)), np.float32)
    e = np.abs(np.diff(g, axis=1)).sum(0) + 1e-6
    xs = np.arange(e.size)
    return float((e * xs).sum() / e.sum()) / e.size          # 0..1


def crop_feed(im):
    """Portrait -> 4:5, trimming the ceiling dead space and centring on the subjects.
    Landscape group shots keep their frame (a 4:5 crop would cut people off)."""
    w, h = im.size
    if h <= w:
        return im.crop((int(w * .02), int(h * .02), int(w * .98), int(h * .98)))
    top = int(h * 0.115)                    # ceiling / corner
    bot = int(h * 0.995)
    nh = bot - top
    nw = int(nh * 0.8)
    if nw > w:
        nw = w
        nh = int(nw / 0.8)
        bot = min(h, top + nh)
        nh = bot - top
    cx = energy_centroid_x(im) * w
    left = int(min(max(cx - nw / 2, 0), w - nw))
    return im.crop((left, top, left + nw, bot))


def story(im):
    """9:16 without cutting anyone: the photo sits over a blurred zoom of itself."""
    W = 1080
    H = 1920
    bg = ImageOps.fit(im, (W, H), method=Image.LANCZOS, centering=(0.5, 0.42))
    bg = bg.filter(ImageFilter.GaussianBlur(38))
    bg = Image.fromarray((np.asarray(bg, np.float32) * 0.62).astype(np.uint8))
    fg = im.copy()
    fg.thumbnail((W - 40, int(H * 0.80)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


# ---------- watermark ----------

_logo_cache = {}


def logo_for(width):
    if width in _logo_cache:
        return _logo_cache[width]
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    lg = lg.resize((width, max(1, round(width * lg.height / lg.width))), Image.LANCZOS)
    _logo_cache[width] = lg
    return lg


def watermark(im, scale=0.19, opacity=0.92):
    im = im.convert("RGB")
    W, H = im.size
    lw = int(W * scale)
    lg = logo_for(lw)
    pad = int(W * 0.035)
    x, y = W - lw - pad, H - lg.height - pad - int(W * 0.028)

    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer.paste(lg, (x, y), lg)
    # soft shadow so the white wordmark survives a white wall
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", lg.size, (0, 0, 0, 190)), (x, y + max(2, lw // 90)), lg)
    sh = sh.filter(ImageFilter.GaussianBlur(max(2, lw // 55)))

    base = im.convert("RGBA")
    base = Image.alpha_composite(base, sh)
    if opacity < 1:
        r, g, b, al = layer.split()
        layer = Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * opacity))))
    base = Image.alpha_composite(base, layer)

    # domain line under the mark (the roll-up banners still show the OLD .online)
    out = base.convert("RGB")
    dr = ImageDraw.Draw(out)
    fs = max(12, int(lw * 0.145))
    try:
        font = ImageFont.truetype(FONT, fs)
    except Exception:
        font = ImageFont.load_default()
    txt = "tkawen.com"
    tw = dr.textlength(txt, font=font)
    tx, ty = x + lw - tw, y + lg.height + int(fs * 0.35)
    dr.text((tx + 2, ty + 2), txt, font=font, fill=(0, 0, 0))
    dr.text((tx, ty), txt, font=font, fill=(255, 255, 255))
    return out


# ---------- driver ----------

def process(name, strength=1.0, want_story=True):
    with Image.open(os.path.join(SRC, name)) as raw:
        im = ImageOps.exif_transpose(raw)
        eh = enhance(im, strength)
        post = watermark(crop_feed(eh))
        os.makedirs(os.path.join(OUT, "post"), exist_ok=True)
        stem = os.path.splitext(name)[0]
        post.save(os.path.join(OUT, "post", stem + ".jpg"), quality=93, subsampling=1,
                  optimize=True)
        if want_story:
            os.makedirs(os.path.join(OUT, "story"), exist_ok=True)
            watermark(story(eh), scale=0.30).save(
                os.path.join(OUT, "story", stem + ".jpg"), quality=92, optimize=True)
    return post


if __name__ == "__main__":
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
    idx = [int(a) for a in sys.argv[1:]] or range(len(files))
    for i in idx:
        process(files[i])
        print("done", files[i])
