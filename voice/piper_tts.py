"""
TKAWEN Studio · Sovereign TTS via Piper (MIT)
100% local · runs on CPU · 15x faster than XTTS-v2
https://github.com/rhasspy/piper
"""
from __future__ import annotations

import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

# Arabic voices available in Piper
PIPER_VOICES = {
    # MSA voices (best baseline for now until DZ-specific is trained)
    "ar-jordan-male":   "ar_JO-kareem-medium",
    "ar-jordan-low":    "ar_JO-kareem-low",       # smaller, faster
}

# Default for TKAWEN Studio — closest to DZ until custom model
DEFAULT_VOICE = "ar-jordan-male"


@dataclass
class PiperConfig:
    voice: str = DEFAULT_VOICE
    voices_dir: str = "voice/piper_voices"
    rate: float = 1.0           # 1.0 = normal · 0.85 = slower · 1.15 = faster
    output_path: str = "output/voice.mp3"


def check_piper() -> bool:
    """Verify piper binary is available."""
    return shutil.which("piper") is not None


def get_voice_paths(voice_id: str, voices_dir: str) -> tuple[str, str]:
    """Return paths to .onnx and .json voice files."""
    base = Path(voices_dir) / PIPER_VOICES[voice_id]
    return str(base.with_suffix(".onnx")), str(base) + ".onnx.json"


def synthesize_to_wav(text: str, voice_id: str, voices_dir: str, output_wav: str) -> bool:
    """Run piper and produce WAV. Returns True on success."""
    onnx, _config = get_voice_paths(voice_id, voices_dir)
    if not Path(onnx).exists():
        print(f"⚠️  voice not found: {onnx}")
        print(f"   download:  https://huggingface.co/rhasspy/piper-voices/tree/main/ar")
        return False

    Path(output_wav).parent.mkdir(parents=True, exist_ok=True)

    process = subprocess.Popen(
        ["piper", "--model", onnx, "--output_file", output_wav],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate(input=text.encode("utf-8"))

    if process.returncode != 0:
        print(f"⚠️  piper error: {stderr.decode('utf-8', errors='ignore')[-300:]}")
        return False
    return Path(output_wav).exists()


def wav_duration_seconds(wav_path: str) -> float:
    """Return duration of a WAV file."""
    with wave.open(wav_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / rate if rate else 0.0


def wav_to_mp3(wav_path: str, mp3_path: str, rate: float = 1.0) -> bool:
    """Convert WAV → MP3 with optional speed adjustment via ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", wav_path,
    ]
    if rate != 1.0:
        cmd += ["-filter:a", f"atempo={rate}"]
    cmd += ["-c:a", "libmp3lame", "-b:a", "192k", mp3_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def synthesize(text: str, output_path: str, config: PiperConfig) -> dict:
    """Generate MP3 voiceover via Piper. Returns dict with duration + path."""
    if not check_piper():
        return {
            "ok": False,
            "error": "piper binary not in PATH. install: pip install piper-tts",
        }

    # Strip TKAWEN === markers (used for pauses) — replace with periods for natural breath
    clean_text = text.replace("===", ".").replace("\n\n", " ").strip()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tmp_wav = output_path + ".tmp.wav"

    ok = synthesize_to_wav(clean_text, config.voice, config.voices_dir, tmp_wav)
    if not ok:
        return {"ok": False, "error": "piper synthesis failed"}

    duration_s = wav_duration_seconds(tmp_wav)

    ok = wav_to_mp3(tmp_wav, output_path, rate=config.rate)
    Path(tmp_wav).unlink(missing_ok=True)

    if not ok:
        return {"ok": False, "error": "ffmpeg WAV→MP3 conversion failed"}

    return {
        "ok": True,
        "path": output_path,
        "duration_ms": duration_s * 1000 / config.rate,
        "voice": PIPER_VOICES[config.voice],
        "engine": "piper",
        "sovereign": True,
    }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TKAWEN Studio · Piper sovereign TTS")
    parser.add_argument("--text", required=True, help="Arabic text or path to .txt")
    parser.add_argument("--out", default="output/voice.mp3")
    parser.add_argument("--voice", default=DEFAULT_VOICE, choices=list(PIPER_VOICES.keys()))
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--voices-dir", default="voice/piper_voices")
    args = parser.parse_args()

    text = args.text
    if Path(args.text).exists():
        text = Path(args.text).read_text(encoding="utf-8")

    config = PiperConfig(voice=args.voice, voices_dir=args.voices_dir, rate=args.rate, output_path=args.out)
    result = synthesize(text, args.out, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
