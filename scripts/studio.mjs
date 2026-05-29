// TKAWEN Studio — generate a daily social post (caption + rendered 1080x1080 image).
// Deterministic rotation by day index (no randomness → reproducible). Optional
// AI copy if ANTHROPIC_API_KEY is set; otherwise a rich template bank (free).
import { readFileSync, writeFileSync } from "node:fs";
import { chromium } from "playwright";

const DAY = parseInt(process.env.DAY || "1", 10);           // day-of-year
const { projects } = JSON.parse(readFileSync("projects.json", "utf8"));

// pick project + feature + hook deterministically so every day differs and cycles
const project = projects[DAY % projects.length];
const feat = project.features[Math.floor(DAY / projects.length) % project.features.length];
const HOOKS = [
  { emoji: "💡", lead: "" },
  { emoji: "🚀", lead: "ميزة تحبّها: " },
  { emoji: "🎯", lead: "" },
  { emoji: "✅", lead: "لماذا يختارونها؟ " },
  { emoji: "🔥", lead: "" },
];
const hook = HOOKS[DAY % HOOKS.length];

// curated high-quality Pexels photo (no API key — direct CDN by ID, Pexels License)
const photoId = project.photos[Math.floor(DAY / projects.length) % project.photos.length];
const photoUrl = `https://images.pexels.com/photos/${photoId}/pexels-photo-${photoId}.jpeg?auto=compress&cs=tinysrgb&w=1600`;

// ---------- caption ----------
async function aiCaption() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return null;
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" },
      body: JSON.stringify({
        model: "claude-opus-4-8", max_tokens: 400,
        messages: [{ role: "user", content:
          `اكتب منشور سوشيال ميديا احترافياً بالعربية (لهجة فصيحة واضحة) عن ميزة "${feat.t}" لمنتج ${project.name} (${project.tagline}). الوصف: ${feat.d}. أضف CTA ورابط ${project.url} وفي النهاية الهاشتاغات: ${project.hashtags.join(" ")}. اجعله جذّاباً ومختصراً (أقل من 90 كلمة)، بإيموجي معتدل. أعد النص فقط.` }]
      })
    });
    const j = await r.json();
    return j?.content?.[0]?.text?.trim() || null;
  } catch { return null; }
}

function templateCaption() {
  return [
    `${hook.emoji} ${hook.lead}${feat.t}`,
    "",
    feat.d,
    "",
    `✅ ${project.tagline} ${project.flag}`,
    `🔗 ابدأ الآن: ${project.url}`,
    "",
    project.hashtags.join(" "),
  ].join("\n");
}

// ---------- design (1080x1080) — full-bleed photo + brand gradient overlay ----------
function buildHtml() {
  return `<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Inter:wght@700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1080px;overflow:hidden}
body{font-family:'Cairo',sans-serif;position:relative;background:#0f172a}
.photo{position:absolute;inset:0;background:url('${photoUrl}') center/cover no-repeat;transform:scale(1.05)}
.ov{position:absolute;inset:0;background:linear-gradient(135deg,rgba(8,12,24,.92) 0%,${project.accent2}e0 50%,${project.accent}9c 100%)}
.grain{position:absolute;inset:0;background:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1px);background-size:26px 26px}
.bar{position:absolute;top:0;right:0;left:0;height:14px;background:linear-gradient(90deg,#fff6,${project.accent})}
.wrap{position:absolute;inset:0;padding:92px 88px 84px;display:flex;flex-direction:column;color:#fff}
.top{display:flex;align-items:center;gap:14px;margin-bottom:48px}
.dot{width:46px;height:46px;border-radius:13px;background:#fff;display:flex;align-items:center;justify-content:center;font-size:26px;box-shadow:0 8px 22px rgba(0,0,0,.3)}
.brand{font-family:'Inter',sans-serif;font-weight:700;font-size:30px;letter-spacing:.01em;text-shadow:0 2px 10px rgba(0,0,0,.4)}
.kicker{font-family:'Inter',sans-serif;font-weight:700;font-size:19px;letter-spacing:.24em;text-transform:uppercase;color:#fff;opacity:.9;margin-bottom:22px;display:flex;align-items:center;gap:12px}
.kicker::before{content:"";width:44px;height:3px;background:#fff;border-radius:3px}
h1{font-weight:900;font-size:82px;line-height:1.1;letter-spacing:-.01em;text-shadow:0 4px 26px rgba(0,0,0,.45)}
.desc{margin-top:28px;font-size:36px;font-weight:600;line-height:1.55;color:#fff;opacity:.94;max-width:880px;text-shadow:0 2px 14px rgba(0,0,0,.4)}
.spacer{flex:1}
.foot{display:flex;align-items:center;justify-content:space-between;border-top:1px solid rgba(255,255,255,.25);padding-top:32px}
.cta{background:#fff;color:${project.accent2};font-weight:800;font-size:30px;padding:18px 44px;border-radius:16px;box-shadow:0 16px 34px rgba(0,0,0,.35)}
.url{font-family:'Inter',sans-serif;font-weight:700;font-size:30px;text-shadow:0 2px 10px rgba(0,0,0,.4)}
</style></head><body>
<div class="photo"></div><div class="ov"></div><div class="grain"></div><div class="bar"></div>
<div class="wrap">
 <div class="top"><span class="dot">${project.flag}</span><span class="brand">${project.name}</span></div>
 <div class="kicker">${project.name}</div>
 <h1>${feat.t}</h1>
 <div class="desc">${feat.d}</div>
 <div class="spacer"></div>
 <div class="foot"><span class="cta">ابدأ مجاناً</span><span class="url">${project.url}</span></div>
</div></body></html>`;
}

const caption = (await aiCaption()) || templateCaption();
writeFileSync("caption.txt", caption, "utf8");

const browser = await chromium.launch({ args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1080 }, deviceScaleFactor: 2 });
await page.setContent(buildHtml(), { waitUntil: "networkidle" });
await page.waitForTimeout(1600); // let webfonts + Pexels photo settle
await page.screenshot({ path: "out.png" });
await browser.close();

console.log(`project=${project.key} feature="${feat.t}" photo=${photoId} caption_len=${caption.length}`);
