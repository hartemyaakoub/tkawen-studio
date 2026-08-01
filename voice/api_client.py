"""
TKAWEN Studio · TTS API client
Calls tts.tkawen.com instead of running TTS locally.
This makes Studio a pure consumer of TKAWEN Voice infrastructure.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


# Default endpoint (production)
DEFAULT_API_URL = "https://tts.tkawen.com"

# Default API key (replace via env)
DEFAULT_API_KEY = "tkw_demo_internal"


@dataclass
class APIClientConfig:
    api_url: str = DEFAULT_API_URL
    api_key: str = DEFAULT_API_KEY
    timeout_seconds: int = 60
    voice: str = "amina"               # logical voice name
    remote_mode: str = "sovereign"      # mode the REMOTE API should use
    preset: str = "default"
    output_path: str = "output/voice.mp3"


def synthesize(text: str, config: APIClientConfig) -> dict:
    """Synthesize via tts.tkawen.com API. Saves MP3 to output_path."""
    api_url = (os.environ.get("TKAWEN_TTS_URL") or config.api_url).rstrip("/")
    api_key = os.environ.get("TKAWEN_API_KEY") or config.api_key

    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.post(
            f"{api_url}/v1/synthesize",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "tkawen-studio/0.2",
            },
            json={
                "text": text,
                "voice": config.voice,
                "mode": config.remote_mode,
                "preset": config.preset,
                "format": "mp3",
            },
            timeout=config.timeout_seconds,
        )
    except requests.exceptions.ConnectionError as e:
        return {"ok": False, "error": f"connection_failed: {e}", "engine": "api"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "timeout", "engine": "api"}

    if response.status_code == 401:
        return {"ok": False, "error": "invalid_api_key", "engine": "api"}
    if response.status_code == 429:
        return {"ok": False, "error": "rate_limit_exceeded", "engine": "api"}
    if response.status_code != 200:
        return {
            "ok": False,
            "error": f"api_error_{response.status_code}: {response.text[:200]}",
            "engine": "api",
        }

    Path(config.output_path).write_bytes(response.content)

    duration_ms = int(response.headers.get("X-Duration-Ms", 0))
    elapsed_ms = int(response.headers.get("X-Elapsed-Ms", 0))
    sovereign = response.headers.get("X-Sovereign") == "true"
    request_id = response.headers.get("X-Request-Id", "")
    engine_used = response.headers.get("X-Engine", "?")
    voice_used = response.headers.get("X-Voice", config.voice)

    return {
        "ok": True,
        "path": config.output_path,
        "duration_ms": duration_ms,
        "elapsed_ms": elapsed_ms,
        "voice": voice_used,
        "engine": f"api/{engine_used}",
        "sovereign": sovereign,
        "request_id": request_id,
        "size_bytes": len(response.content),
    }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TKAWEN Studio · TTS API client")
    parser.add_argument("--text", required=True)
    parser.add_argument("--out", default="output/voice.mp3")
    parser.add_argument("--voice", default="amina")
    parser.add_argument("--remote-mode", default="sovereign", choices=["sovereign", "cloud", "hybrid"])
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    args = parser.parse_args()

    text = args.text
    if Path(args.text).exists():
        text = Path(args.text).read_text(encoding="utf-8")

    config = APIClientConfig(
        api_url=args.api_url,
        api_key=args.api_key,
        voice=args.voice,
        remote_mode=args.remote_mode,
        output_path=args.out,
    )
    print(json.dumps(synthesize(text, config), ensure_ascii=False, indent=2))
