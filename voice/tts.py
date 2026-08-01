"""
TKAWEN Studio · Voice Engine
Azure Neural TTS with native Algerian Arabic voices (ar-DZ-Amina, ar-DZ-Ismael).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk


# Native DZ voices — only Azure has these
DZ_VOICES = {
    "amina": "ar-DZ-AminaNeural",   # Female — primary for Beauty/Cosmetics
    "ismael": "ar-DZ-IsmaelNeural", # Male — primary for LIQAA/PharmaPro
}

# Pacing / emotion presets
PRESETS = {
    "default": {"rate": "0.95", "pitch": "+0%", "style": "general"},
    "energetic": {"rate": "1.05", "pitch": "+8%", "style": "cheerful"},
    "calm": {"rate": "0.90", "pitch": "-3%", "style": "general"},
    "urgent": {"rate": "1.10", "pitch": "+5%", "style": "general"},
}


@dataclass
class VoiceConfig:
    voice: str = "amina"          # "amina" or "ismael"
    preset: str = "default"
    azure_key: str = ""
    azure_region: str = "francecentral"


def build_ssml(text: str, config: VoiceConfig) -> str:
    """
    Build SSML for natural DZ delivery.
    Multi-line scripts with === markers become separate <break> sections.
    """
    voice_name = DZ_VOICES[config.voice]
    preset = PRESETS[config.preset]

    # Split text on === markers for natural pauses
    sections = [s.strip() for s in text.split("===") if s.strip()]

    body_parts = []
    for i, section in enumerate(sections):
        body_parts.append(
            f'<prosody rate="{preset["rate"]}" pitch="{preset["pitch"]}">'
            f'{escape_ssml(section)}'
            f'</prosody>'
        )
        if i < len(sections) - 1:
            body_parts.append('<break time="400ms"/>')

    body = "".join(body_parts)

    return (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="ar-DZ">'
        f'<voice name="{voice_name}">{body}</voice>'
        '</speak>'
    )


def escape_ssml(text: str) -> str:
    """Escape special chars for SSML."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def synthesize(script_text: str, output_path: str, config: VoiceConfig) -> dict:
    """
    Generate voiceover MP3 from script. Returns dict with duration + path.
    """
    if not config.azure_key:
        config.azure_key = os.environ.get("AZURE_SPEECH_KEY", "")
        if not config.azure_key:
            raise ValueError(
                "Azure key required. Set AZURE_SPEECH_KEY env or pass via config."
            )

    speech_config = speechsdk.SpeechConfig(
        subscription=config.azure_key,
        region=config.azure_region,
    )
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    audio_output = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_output,
    )

    ssml = build_ssml(script_text, config)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return {
            "ok": True,
            "path": output_path,
            "duration_ms": result.audio_duration.total_seconds() * 1000,
            "voice": DZ_VOICES[config.voice],
        }

    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        return {
            "ok": False,
            "error": f"Canceled: {cancellation.reason} · {cancellation.error_details}",
        }

    return {"ok": False, "error": f"Unexpected reason: {result.reason}"}


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TKAWEN Studio TTS")
    parser.add_argument("--text", required=True, help="Arabic text or path to .txt")
    parser.add_argument("--out", default="output/voice.mp3", help="MP3 output path")
    parser.add_argument("--voice", default="amina", choices=list(DZ_VOICES.keys()))
    parser.add_argument("--preset", default="default", choices=list(PRESETS.keys()))
    args = parser.parse_args()

    text = args.text
    if Path(args.text).exists():
        text = Path(args.text).read_text(encoding="utf-8")

    config = VoiceConfig(voice=args.voice, preset=args.preset)
    result = synthesize(text, args.out, config)

    print(json.dumps(result, ensure_ascii=False, indent=2))
