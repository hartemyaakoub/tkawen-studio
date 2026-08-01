# 🎬 TKAWEN Studio

> Sovereign video production for TKAWEN Group platforms.
> One markdown script → vertical TikTok-ready mp4. **100% local. MIT-licensed. Zero cloud by default.**

📖 [SOVEREIGN.md](./SOVEREIGN.md) — sovereign-by-default architecture.

---

## ⚡ End-to-end usage (sovereign mode · default)

```bash
# Setup (one-time)
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
bash voice/install_piper.sh   # download Arabic voices ~80MB

# Generate one video — zero cloud, zero outbound calls
python studio.py scripts/01-mystoq-beauty-cod.md
```

**Cloud mode (optional · Azure DZ accent):**
```bash
$env:AZURE_SPEECH_KEY = "your-azure-key"
$env:TKAWEN_TTS_MODE = "cloud"
python studio.py scripts/01-mystoq-beauty-cod.md
```

**Output:** `output/01-mystoq-beauty-cod/final.mp4` — 1080×1920 vertical, ready for TikTok/Reels/Shorts.

---

## 🧠 How it works

```
script.md (frontmatter + sections)
     │
     ├──► voice/tts.py ────────► voice.mp3 (Azure ar-DZ-Amina)
     │
     ├──► recorder/screen.py ──► screen.mp4 (Playwright vertical)
     │
     ├──► captions/whisper_gen.py ► captions.srt (Whisper local)
     │
     └──► compositor/compose.py ─► final.mp4 (FFmpeg + libass)
```

---

## 📝 Script format

```markdown
---
template: mystoq-beauty
voice: amina       # or ismael
preset: default    # default | energetic | calm | urgent
title: "Hook title"
target_length: 35
---

# Voiceover

وقّفي.
===
إذا تبيعي مكياج بـ COD...
===
Mystoq dot com slash beauty.

# Screen flow

- url: /beauty
  duration: 4
  action: wait

- action: scroll
  scroll_to: 600
  duration: 3

- action: highlight
  selector: ".pricing-card"
  duration: 5
```

`===` markers in voiceover = natural 400ms pauses (mid-sentence).

---

## 🎨 Brand templates (`templates/*.yaml`)

| Template | Voice | Accent | Domain |
|----------|-------|--------|--------|
| `mystoq-beauty` | Amina (DZ female) | Rose `#ec4899` | mystoq.com/beauty |
| `liqaa` | Ismael (DZ male) | Cyan `#06b6d4` | liqaa.io |

Add more YAMLs for PharmaPro, Certify, Academy, Trust, ID.

---

## 🔧 Per-module usage

### Voice only
```bash
python voice/tts.py --text scripts/test-amina.txt --voice amina --out voice.mp3
```

### Screen only
```bash
python recorder/screen.py --flow flow.yaml --out screen.mp4
```

### Captions only
```bash
python captions/whisper_gen.py --audio voice.mp3 --model medium --out captions.srt
```

### Compose only
```bash
python compositor/compose.py --screen screen.mp4 --voice voice.mp3 \
       --captions captions.srt --out final.mp4
```

---

## 📊 Cost (verified)

| Item | Cost |
|------|------|
| Azure TTS (300 videos × 200 chars) | ~$1/month |
| Whisper (local, free) | $0 |
| Playwright (local, free) | $0 |
| FFmpeg (local, free) | $0 |
| **Total** | **~$1-3/month** |

---

## 📋 7-day MVP — what was built

- ✅ Day 1-2 · `voice/tts.py` (Azure TTS · 2 DZ voices · 4 presets)
- ✅ Day 3 · `recorder/screen.py` (Playwright · 5 actions · cursor + highlights)
- ✅ Day 4 · `compositor/compose.py` (FFmpeg + libass + brand tint)
- ✅ Day 5 · `captions/whisper_gen.py` (local Whisper · auto SRT)
- ✅ Day 6 · `templates/*.yaml` + `scripts/*.md` (per-platform configs)
- ✅ Day 7 · `studio.py` (end-to-end orchestrator)

---

## 🚀 Future extensions (post-MVP)

- Auto-publishing (TikTok/IG/YouTube APIs)
- Scheduling + cron
- Analytics harvester (views/engagement → optimize)
- AI script generation (GPT-4 from feature list)
- A/B variant generation (8 variants per script)
- Public SaaS at `studio.tkawen.com`
