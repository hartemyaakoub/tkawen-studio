"""
TKAWEN Studio · Main pipeline orchestrator
script.md → voiceover + screen + captions → final.mp4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import frontmatter
import yaml

# Local modules
sys.path.insert(0, str(Path(__file__).parent))
from voice.router import RouterConfig, synthesize
from recorder.screen import RecordConfig, ScreenStep, record
from captions.whisper_gen import CaptionConfig, generate as gen_captions
from compositor.compose import ComposeConfig, compose


def parse_script(script_path: str) -> dict:
    """Parse a markdown script file into voiceover text + screen flow."""
    post = frontmatter.load(script_path)
    body = post.content

    # Extract # Voiceover section
    voice_match = re.search(
        r'#\s*Voiceover\s*\n(.+?)(?=\n#\s|\Z)',
        body,
        re.S | re.I,
    )
    voice_text = voice_match.group(1).strip() if voice_match else ""

    # Extract # Screen flow section as YAML list
    screen_match = re.search(
        r'#\s*Screen\s+flow\s*\n(.+?)(?=\n#\s|\Z)',
        body,
        re.S | re.I,
    )
    screen_yaml = screen_match.group(1).strip() if screen_match else ""
    screen_steps = yaml.safe_load(screen_yaml) if screen_yaml else []

    return {
        "frontmatter": dict(post.metadata),
        "voiceover": voice_text,
        "screen_steps": screen_steps,
    }


def load_template(template_name: str) -> dict:
    """Load a brand template YAML."""
    template_path = Path(__file__).parent / "templates" / f"{template_name}.yaml"
    if not template_path.exists():
        return {}
    with open(template_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


async def run_pipeline(script_path: str, output_dir: str, skip_captions: bool = False) -> dict:
    """Run the full pipeline for one script."""
    script_name = Path(script_path).stem
    out_dir = Path(output_dir) / script_name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[STUDIO] processing {script_name}")
    print(f"   output: {out_dir}\n")

    # 1. Parse script
    parsed = parse_script(script_path)
    fm = parsed["frontmatter"]

    # 2. Merge template + frontmatter
    template_name = fm.get("template", "mystoq-beauty")
    template = load_template(template_name)
    config = {**template, **fm}

    base_url = config.get("base_url", "https://mystoq.com")
    voice_choice = config.get("voice", "amina")
    preset = config.get("preset", "default")
    brand = config.get("brand", {})

    # 3. Generate voiceover via tts.tkawen.com API (default)
    mode = config.get("tts_mode", "api")
    api_remote_mode = config.get("api_remote_mode", "sovereign")
    api_key = os.environ.get("TKAWEN_API_KEY") or config.get("api_key")
    print(f"   [voice] mode={mode}/{api_remote_mode}")
    voice_path = str(out_dir / "voice.mp3")
    voice_cfg = RouterConfig(
        mode=mode,
        voice=voice_choice,
        preset=preset,
        output_path=voice_path,
        api_remote_mode=api_remote_mode,
        api_key=api_key,
    )
    voice_result = synthesize(parsed["voiceover"], voice_cfg)
    if not voice_result.get("ok"):
        return {"ok": False, "stage": "voice", "error": voice_result.get("error")}
    voice_duration_s = voice_result["duration_ms"] / 1000
    sov_tag = "sovereign" if voice_result.get("sovereign") else "cloud"
    elapsed = voice_result.get("elapsed_ms", 0)
    print(f"      [OK] {voice_duration_s:.1f}s audio · {elapsed}ms gen · {voice_result['engine']} · {sov_tag}")

    # 4. Record screen (target duration matches voice)
    print("   [screen]")
    steps = []
    for s in parsed["screen_steps"]:
        steps.append(ScreenStep(**s))

    # If steps total < voice duration, pad the last step
    total_step_duration = sum(s.duration for s in steps)
    if total_step_duration < voice_duration_s and steps:
        steps[-1].duration += voice_duration_s - total_step_duration
        print(f"      ↳ padded last step by {voice_duration_s - total_step_duration:.1f}s")

    screen_path = str(out_dir / "screen.mp4")
    rec_cfg = RecordConfig(
        output_path=screen_path,
        steps=steps,
        base_url=base_url,
        headless=True,
    )
    rec_result = await record(rec_cfg)
    if not rec_result.get("ok"):
        return {"ok": False, "stage": "screen", "error": "screen record failed"}
    print(f"      [OK] {rec_result['size_bytes']/1024:.0f} KB")

    # 5. Generate captions (Whisper local · sovereign)
    captions_path = None
    if not skip_captions:
        print("   [captions] whisper local")
        captions_path = str(out_dir / "captions.srt")
        cap_result = gen_captions(
            voice_path,
            CaptionConfig(output_path=captions_path),
        )
        if not cap_result.get("ok"):
            print(f"      [WARN] captions failed: {cap_result.get('error')}")
            captions_path = None
        else:
            print(f"      [OK] {cap_result['segments']} segments")

    # 6. Compose final video
    print("   [compose] ffmpeg")
    final_path = str(out_dir / "final.mp4")
    compose_cfg = ComposeConfig(
        screen_video=screen_path,
        voiceover_audio=voice_path,
        captions_srt=captions_path,
        output_path=final_path,
        target_duration=voice_duration_s,
        brand_color_overlay=brand.get("tint_overlay"),
        caption_font=brand.get("font", "Cairo"),
    )
    cmp_result = compose(compose_cfg)
    if not cmp_result.get("ok"):
        return {"ok": False, "stage": "compose", "error": cmp_result.get("error")}

    print(f"\n[DONE] {final_path}")
    print(f"   {cmp_result['size_bytes']/1024:.0f} KB · {cmp_result['duration']:.1f}s\n")

    return {
        "ok": True,
        "script": script_name,
        "output": final_path,
        "duration_s": cmp_result["duration"],
        "size_kb": cmp_result["size_bytes"] / 1024,
        "voice": voice_result["voice"],
        "captions": captions_path,
    }


def main():
    parser = argparse.ArgumentParser(
        description="TKAWEN Studio · script.md → vertical video"
    )
    parser.add_argument("script", help="Path to .md script file")
    parser.add_argument("--out-dir", default="output", help="Output directory")
    parser.add_argument("--skip-captions", action="store_true", help="Skip Whisper")
    args = parser.parse_args()

    if not Path(args.script).exists():
        print(f"[ERROR] script not found: {args.script}")
        sys.exit(1)

    result = asyncio.run(run_pipeline(args.script, args.out_dir, args.skip_captions))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
