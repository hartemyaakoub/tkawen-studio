# -*- coding: utf-8 -*-
"""An original, rights-free score synthesised from scratch (numpy only).

Nothing sampled, nothing licensed: platforms cannot mute or claim it.
Uplifting Am–F–C–G at 100 BPM, arranged so the cut points land on the beat.

usage: music.py <seconds> <out.wav>
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 100.0
BEAT = 60.0 / BPM                      # 0.6 s
BAR = 4 * BEAT

# Am  F  C  G  — roots and triads (MIDI)
PROG = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def env(n, a, d, s, r, sus=0.75):
    """ADSR in samples-friendly seconds."""
    a, d, r = max(int(a * SR), 1), max(int(d * SR), 1), max(int(r * SR), 1)
    s = max(n - a - d - r, 0)
    return np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sus, d),
        np.full(s, sus),
        np.linspace(sus, 0, r),
    ])[:n]


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 13):                       # band-limited-ish
        out += np.sin(2 * np.pi * f * k * (1 + detune) * t) / k
    return out / 2.2


def pluck(f, n):
    t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * f * t) * 0.62
            + np.sin(2 * np.pi * f * 2 * t) * 0.24
            + np.sin(2 * np.pi * f * 3 * t) * 0.10)
    return tone * np.exp(-t * 7.5)


def kick(n):
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 26) + 44
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9.5)


def clap(n, rng):
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    # cheap band-pass: difference of two smoothings
    k1 = np.convolve(noise, np.ones(6) / 6, "same")
    k2 = np.convolve(noise, np.ones(28) / 28, "same")
    return (k1 - k2) * np.exp(-t * 17) * 1.5


def hat(n, rng):
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    hp = noise - np.convolve(noise, np.ones(4) / 4, "same")
    return hp * np.exp(-t * 55)


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i] * gain


def build(seconds):
    n = int(seconds * SR)
    pad = np.zeros(n)
    arp = np.zeros(n)
    bass = np.zeros(n)
    drum = np.zeros(n)
    rng = np.random.default_rng(7)

    bars = int(np.ceil(seconds / BAR))
    intro_bars, outro_bars = 1, 1
    for b in range(bars):
        t0 = b * BAR
        root, triad = PROG[b % 4]
        drums_on = intro_bars <= b < bars - outro_bars

        # pad: soft detuned stack, one long note per bar
        ln = int(BAR * SR)
        e = env(ln, 0.35, 0.25, 0, 0.55, sus=0.8)
        for m in triad:
            add(pad, saw(hz(m + 12), ln, 0.004) * e, t0, 0.16)
            add(pad, saw(hz(m + 12), ln, -0.004) * e, t0, 0.16)

        # bass: root on 1 and 3, an octave down
        for beat in (0, 2):
            bl = int(BEAT * 1.9 * SR)
            te = np.arange(bl) / SR
            add(bass, np.sin(2 * np.pi * hz(root - 12) * te) * np.exp(-te * 2.2), t0 + beat * BEAT, 0.5)

        # arpeggio: eighth notes climbing the triad, brighter in the main section
        notes = [triad[0] + 12, triad[1] + 12, triad[2] + 12, triad[1] + 24]
        for k in range(8):
            m = notes[k % 4] + (12 if (k >= 4 and drums_on) else 0)
            add(arp, pluck(hz(m), int(BEAT * 0.75 * SR)), t0 + k * BEAT / 2,
                0.30 if drums_on else 0.20)

        if drums_on:
            for beat in range(4):
                if beat in (0, 2):
                    add(drum, kick(int(0.34 * SR)), t0 + beat * BEAT, 0.95)
                else:
                    add(drum, clap(int(0.26 * SR), rng), t0 + beat * BEAT, 0.42)
                add(drum, hat(int(0.08 * SR), rng), t0 + beat * BEAT + BEAT / 2, 0.20)

        # riser into the first main bar
        if b == intro_bars - 1:
            rl = int(BAR * SR)
            te = np.arange(rl) / SR
            sweep = rng.normal(0, 1, rl) * (te / te[-1]) ** 2
            sweep = sweep - np.convolve(sweep, np.ones(8) / 8, "same")
            add(drum, sweep, t0, 0.20)

    # sidechain: duck the sustained layers on every kick — the modern "pump"
    duck = np.ones(n)
    for b in range(bars):
        if not (intro_bars <= b < bars - outro_bars):
            continue
        for beat in (0, 2):
            i = int((b * BAR + beat * BEAT) * SR)
            L = int(0.30 * SR)
            j = min(n, i + L)
            if i < n:
                duck[i:j] = np.minimum(duck[i:j], np.linspace(0.45, 1.0, j - i))
    pad *= duck
    bass *= duck

    mix = pad * 0.85 + arp * 0.85 + bass * 0.9 + drum * 0.8

    # tail fade + soft limiter
    fade = int(1.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    mix = np.tanh(mix / max(np.abs(mix).max(), 1e-6) * 1.6) / np.tanh(1.6)
    mix *= 0.89

    stereo = np.stack([mix, np.roll(mix, 90)], 1)      # tiny width
    return (stereo * 32767).astype(np.int16)


def main():
    seconds = float(sys.argv[1])
    out = sys.argv[2]
    data = build(seconds)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{out}  {len(data) / SR:.1f}s  peak={np.abs(data).max() / 32767:.2f}  "
          f"rms={np.sqrt((data.astype(float) ** 2).mean()) / 32767:.3f}")


if __name__ == "__main__":
    main()
