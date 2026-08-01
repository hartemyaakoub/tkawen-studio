#!/bin/bash
# TKAWEN Studio · Piper sovereign TTS installer
# Downloads Arabic voice models from Hugging Face (rhasspy/piper-voices)

set -e

VOICES_DIR="${1:-voice/piper_voices}"
mkdir -p "$VOICES_DIR"
cd "$VOICES_DIR"

BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/ar"

echo "[piper] downloading Arabic voices to $VOICES_DIR"
echo ""

# ar-jordan-male · medium quality · ~63MB
if [ ! -f "ar_JO-kareem-medium.onnx" ]; then
    echo "  -> ar_JO-kareem-medium (63MB)"
    curl -sL "$BASE/jo/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx" -o ar_JO-kareem-medium.onnx
    curl -sL "$BASE/jo/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx.json" -o ar_JO-kareem-medium.onnx.json
fi

# ar-jordan-low · low quality · ~17MB · faster
if [ ! -f "ar_JO-kareem-low.onnx" ]; then
    echo "  -> ar_JO-kareem-low (17MB · faster)"
    curl -sL "$BASE/jo/ar_JO/kareem/low/ar_JO-kareem-low.onnx" -o ar_JO-kareem-low.onnx
    curl -sL "$BASE/jo/ar_JO/kareem/low/ar_JO-kareem-low.onnx.json" -o ar_JO-kareem-low.onnx.json
fi

echo ""
echo "[OK] voices installed in $VOICES_DIR"
echo ""
echo "test with:"
echo "  python voice/piper_tts.py --text scripts/test-amina.txt --out output/sovereign-test.mp3"
