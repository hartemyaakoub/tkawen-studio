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

// ---------- design (1080x1080) ----------
function buildHtml() {
  return `<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Inter:wght@700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1080px;overflow:hidden}
body{font-family:'Cairo',sans-serif;color:#0f172a;background:#fff;
 background-image:radial-gradient(#e9eef5 1.5px,transparent 1.5px);background-size:30px 30px;position:relative}
.bar{position:absolute;top:0;right:0;left:0;height:14px;background:linear-gradient(90deg,${project.accent},${project.accent2})}
.blob{position:absolute;bottom:-160px;left:-160px;width:420px;height:420px;border-radius:50%;
 background:radial-gradient(circle at 30% 30%,${project.accent}22,transparent 70%)}
.wrap{position:absolute;inset:0;padding:96px 92px 88px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;gap:18px;margin-bottom:54px}
.top img{height:60px;width:auto}
.brand{font-family:'Inter',sans-serif;font-weight:700;font-size:26px;letter-spacing:.02em;color:#0f172a}
.kicker{font-family:'Inter',sans-serif;font-weight:700;font-size:18px;letter-spacing:.2em;text-transform:uppercase;color:${project.accent};margin-bottom:22px;display:flex;align-items:center;gap:12px}
.kicker::before{content:"";width:40px;height:3px;background:${project.accent};border-radius:3px}
h1{font-weight:900;font-size:78px;line-height:1.12;letter-spacing:-.01em;
 background:linear-gradient(135deg,${project.accent},${project.accent2});-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.desc{margin-top:30px;font-size:36px;font-weight:600;color:#475569;line-height:1.55}
.spacer{flex:1}
.foot{display:flex;align-items:center;justify-content:space-between;border-top:2px solid #eef2f7;padding-top:34px}
.cta{background:${project.accent};color:#fff;font-weight:800;font-size:30px;padding:18px 42px;border-radius:16px;box-shadow:0 14px 30px ${project.accent}3d}
.url{font-family:'Inter',sans-serif;font-weight:700;font-size:30px;color:#0f172a}
</style></head><body>
<div class="bar"></div><div class="blob"></div>
<div class="wrap">
 <div class="top"><img src="${project.logo}" onerror="this.style.display='none'"><span class="brand">${project.name} ${project.flag}</span></div>
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
await page.waitForTimeout(800); // let webfonts settle
await page.screenshot({ path: "out.png" });
await browser.close();

console.log(`project=${project.key} feature="${feat.t}" caption_len=${caption.length}`);
