# 🎨 TKAWEN Studio

A 24/7 design machine on free GitHub Actions. Every day it picks a TKAWEN
project + content angle (deterministic rotation), writes an Arabic social post,
**renders a 1080×1080 branded design** (HTML → Playwright/chromium screenshot),
and **delivers it to the founder's private Telegram** — while you sleep.

## How it works
- `projects.json` — your projects (Mystoq, Algeria Certify, LIQAA, PharmaPro, Catalogue, TKAWEN): logo, accent color, tagline, features, hashtags.
- `scripts/studio.mjs` — picks `projects[day % N]` + a rotating feature + hook, builds the caption and the design HTML, renders `out.png` via Playwright.
- `.github/workflows/studio-daily.yml` — daily 06:00 UTC: install chromium → generate → `sendPhoto` to Telegram → archive to `.data/studio/`.

## Secrets
| Secret | Required | Purpose |
|--------|----------|---------|
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | yes | deliver to your private chat |
| `ANTHROPIC_API_KEY` | optional | AI-written copy (Claude). Without it, a rich template bank is used (free). |

## Make it yours
- Add projects/features by editing `projects.json` (more features = longer rotation before repeat).
- Trigger on demand: Actions → run workflow (optional `day` input to preview a specific rotation).
- Designs are square (IG/FB feed). Extend `buildHtml()` for story (1080×1920) or cover (1640×624) variants.
