"""
TKAWEN Studio · Auto-captions
Uses OpenAI Whisper (local) to transcribe Arabic voiceover into SRT.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CaptionConfig:
    model_size: str = "medium"        # tiny | base | small | medium | large
    language: str = "ar"
    max_chars_per_line: int = 30      # short lines for vertical 9:16
    output_path: str = "output/captions.srt"


def format_timestamp(seconds: float) -> str:
    """SRT timestamp format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_long_line(text: str, max_chars: int) -> str:
    """Insert newlines in long captions for vertical readability."""
    words = text.split()
    lines, current = [], []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_chars and current:
            lines.append(" ".join(current))
            current, current_len = [word], len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def generate(audio_path: str, config: CaptionConfig) -> dict:
    """Transcribe audio to SRT. Returns dict with path + segment count."""
    try:
        import whisper
    except ImportError:
        return {"ok": False, "error": "openai-whisper not installed"}

    if not Path(audio_path).exists():
        return {"ok": False, "error": f"audio not found: {audio_path}"}

    model = whisper.load_model(config.model_size)
    result = model.transcribe(
        audio_path,
        language=config.language,
        word_timestamps=False,
        verbose=False,
    )

    srt_lines = []
    for i, seg in enumerate(result["segments"], start=1):
        text = split_long_line(seg["text"].strip(), config.max_chars_per_line)
        srt_lines.append(str(i))
        srt_lines.append(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}")
        srt_lines.append(text)
        srt_lines.append("")

    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(config.output_path).write_text("\n".join(srt_lines), encoding="utf-8")

    return {
        "ok": True,
        "path": config.output_path,
        "segments": len(result["segments"]),
        "duration": result["segments"][-1]["end"] if result["segments"] else 0,
    }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TKAWEN Studio · Whisper Captions")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--out", default="output/captions.srt")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"])
    args = parser.parse_args()

    config = CaptionConfig(
        model_size=args.model,
        output_path=args.out,
    )
    print(json.dumps(generate(args.audio, config), ensure_ascii=False, indent=2))
