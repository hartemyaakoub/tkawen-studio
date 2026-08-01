"""
TKAWEN Studio · Video Compositor
FFmpeg pipeline: combines screen + voiceover + captions + brand outro.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ComposeConfig:
    screen_video: str
    voiceover_audio: str
    captions_srt: Optional[str] = None
    output_path: str = "output/final.mp4"
    width: int = 1080
    height: int = 1920
    target_duration: Optional[float] = None  # if set, screen is trimmed/extended

    # Caption styling (libass)
    caption_font: str = "Cairo"
    caption_size: int = 22
    caption_color: str = "&H00FFFFFF"        # white
    caption_outline_color: str = "&H00000000" # black
    caption_outline: int = 3

    # Brand template
    brand_logo: Optional[str] = None
    brand_color_overlay: Optional[str] = None  # rgba hex e.g. "ec489922"
    background_music: Optional[str] = None
    music_volume: float = 0.08  # 8% of voice


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def get_audio_duration(path: str) -> float:
    """Get audio duration via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip()) if result.returncode == 0 else 0.0


def build_filter_complex(config: ComposeConfig) -> str:
    """Build the FFmpeg -filter_complex string."""
    filters = []

    # Scale screen to vertical if needed
    filters.append(f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=cover,"
                   f"crop={config.width}:{config.height}[scaled]")

    last_video = "scaled"

    # Color overlay (soft brand tint)
    if config.brand_color_overlay:
        filters.append(
            f"color=c=#{config.brand_color_overlay}:s={config.width}x{config.height}:d=999"
            f"[overlay_color];"
            f"[{last_video}][overlay_color]overlay=format=auto[tinted]"
        )
        last_video = "tinted"

    # Captions burn-in
    if config.captions_srt and Path(config.captions_srt).exists():
        srt_escaped = config.captions_srt.replace("\\", "/").replace(":", "\\:")
        style = (
            f"FontName={config.caption_font},FontSize={config.caption_size},"
            f"PrimaryColour={config.caption_color},"
            f"OutlineColour={config.caption_outline_color},"
            f"Outline={config.caption_outline},Alignment=2,MarginV=140,"
            f"Bold=1,Shadow=0"
        )
        filters.append(
            f"[{last_video}]subtitles='{srt_escaped}':force_style='{style}'[captioned]"
        )
        last_video = "captioned"

    # Audio mixing
    if config.background_music and Path(config.background_music).exists():
        filters.append(
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume={config.music_volume}[bg];"
            f"[voice][bg]amix=inputs=2:duration=longest[audio_out]"
        )
    else:
        filters.append("[1:a]anull[audio_out]")

    return ";".join(filters), last_video


def compose(config: ComposeConfig) -> dict:
    """Run FFmpeg to compose final video."""
    if not check_ffmpeg():
        return {"ok": False, "error": "ffmpeg not found in PATH"}

    if not Path(config.screen_video).exists():
        return {"ok": False, "error": f"screen video missing: {config.screen_video}"}
    if not Path(config.voiceover_audio).exists():
        return {"ok": False, "error": f"voiceover missing: {config.voiceover_audio}"}

    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    voice_duration = get_audio_duration(config.voiceover_audio)
    target_duration = config.target_duration or voice_duration

    filter_complex, last_video = build_filter_complex(config)

    cmd = [
        "ffmpeg", "-y",
        "-i", config.screen_video,
        "-i", config.voiceover_audio,
    ]

    if config.background_music and Path(config.background_music).exists():
        cmd += ["-stream_loop", "-1", "-i", config.background_music]

    cmd += [
        "-filter_complex", filter_complex,
        "-map", f"[{last_video}]",
        "-map", "[audio_out]",
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        config.output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {
            "ok": False,
            "error": "ffmpeg failed",
            "stderr": result.stderr[-1500:],  # last 1500 chars
        }

    return {
        "ok": True,
        "path": config.output_path,
        "size_bytes": Path(config.output_path).stat().st_size,
        "duration": target_duration,
    }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TKAWEN Studio · Compositor")
    parser.add_argument("--screen", required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--captions", default=None)
    parser.add_argument("--out", default="output/final.mp4")
    parser.add_argument("--music", default=None)
    parser.add_argument("--brand-tint", default=None, help="rgba hex like ec489922")
    args = parser.parse_args()

    config = ComposeConfig(
        screen_video=args.screen,
        voiceover_audio=args.voice,
        captions_srt=args.captions,
        output_path=args.out,
        background_music=args.music,
        brand_color_overlay=args.brand_tint,
    )
    print(json.dumps(compose(config), ensure_ascii=False, indent=2))
