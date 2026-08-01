"""
TKAWEN Studio · Voice Router
Dispatches TTS request to the right engine based on mode:
  - api        → tts.tkawen.com (RECOMMENDED · delegates to TKAWEN Voice infra)
  - sovereign  → Piper local (no network · MIT · self-contained)
  - cloud      → Azure direct (DZ Amina/Ismael · paid · for testing)
  - hybrid     → try Piper first, fallback to Azure if unavailable
  - clone      → custom DZ voice clone (future · Phase 3)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RouterConfig:
    mode: str = "api"                 # api | sovereign | cloud | hybrid | clone
    voice: str = "amina"              # logical name (engine maps internally)
    preset: str = "default"
    output_path: str = "output/voice.mp3"

    # API mode (default)
    api_url: str = "https://tts.tkawen.com"
    api_key: Optional[str] = None
    api_remote_mode: str = "sovereign"  # what mode the remote API uses

    # Direct engine modes
    azure_key: Optional[str] = None
    azure_region: str = "francecentral"
    piper_voice: str = "ar-jordan-male"
    piper_voices_dir: str = "voice/piper_voices"


def synthesize(text: str, config: RouterConfig) -> dict:
    """Route TTS request to the appropriate engine."""
    mode = (os.environ.get("TKAWEN_TTS_MODE") or config.mode).lower()

    if mode == "api":
        return _via_api(text, config)

    if mode == "sovereign":
        return _via_piper(text, config)

    if mode == "cloud":
        return _via_azure(text, config)

    if mode == "hybrid":
        result = _via_api(text, config)
        if result.get("ok"):
            return result
        print(f"   ↳ api unavailable ({result.get('error')}), falling back to local Piper")
        return _via_piper(text, config)

    if mode == "clone":
        return {
            "ok": False,
            "error": "clone mode not yet implemented (Phase 3 · custom DZ training)",
        }

    return {"ok": False, "error": f"unknown mode: {mode}"}


def _via_api(text: str, config: RouterConfig) -> dict:
    from voice.api_client import APIClientConfig, synthesize as api_synth

    api_cfg = APIClientConfig(
        api_url=config.api_url,
        api_key=config.api_key or "tkw_demo_internal",
        voice=config.voice,
        remote_mode=config.api_remote_mode,
        preset=config.preset,
        output_path=config.output_path,
    )
    return api_synth(text, api_cfg)


def _via_piper(text: str, config: RouterConfig) -> dict:
    # Use fast (library-mode) variant if available
    rate = {
        "default":   1.0,
        "energetic": 1.10,
        "calm":      0.92,
        "urgent":    1.15,
    }.get(config.preset, 1.0)

    try:
        from voice.piper_fast import PiperFastConfig, synthesize as piper_synth
        cfg_class = PiperFastConfig
    except ImportError:
        from voice.piper_tts import PiperConfig as cfg_class
        from voice.piper_tts import synthesize as piper_synth

    piper_cfg = cfg_class(
        voice=config.piper_voice,
        voices_dir=config.piper_voices_dir,
        rate=rate,
        output_path=config.output_path,
    )
    return piper_synth(text, config.output_path, piper_cfg)


def _via_azure(text: str, config: RouterConfig) -> dict:
    from voice.tts import VoiceConfig, synthesize as azure_synth

    azure_cfg = VoiceConfig(
        voice=config.voice,
        preset=config.preset,
        azure_key=config.azure_key or "",
        azure_region=config.azure_region,
    )
    result = azure_synth(text, config.output_path, azure_cfg)
    if result.get("ok"):
        result["engine"] = "azure"
        result["sovereign"] = False
    return result


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="TKAWEN Studio · Voice Router")
    parser.add_argument("--text", required=True)
    parser.add_argument("--out", default="output/voice.mp3")
    parser.add_argument("--mode", default="sovereign", choices=["sovereign", "cloud", "hybrid", "clone"])
    parser.add_argument("--voice", default="amina")
    parser.add_argument("--preset", default="default")
    args = parser.parse_args()

    text = args.text
    if Path(args.text).exists():
        text = Path(args.text).read_text(encoding="utf-8")

    config = RouterConfig(
        mode=args.mode,
        voice=args.voice,
        preset=args.preset,
        output_path=args.out,
    )
    print(json.dumps(synthesize(text, config), ensure_ascii=False, indent=2))
