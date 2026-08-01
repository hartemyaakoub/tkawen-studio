# 🇩🇿 TKAWEN Studio · Sovereign Mode

> **القاعدة:** كل النظام يعمل بدون أيّ cloud أمريكي. بياناتك لا تغادر VPS40 ولا جهازك المحلي.

---

## مَن يحتاج هذا

- منصّات TKAWEN جميعها (Mystoq · LIQAA · Certify · PharmaPro)
- شركات تتعامل مع بيانات حسّاسة (CNAS · DGI · صحّيّة)
- مَن يريد التزام كامل بالقانون <span class="lat">18-07</span> (سيادة البيانات)
- مَن يريد infrastructure مستقلّة عن US tech

---

## المعمار السيادي

```
TKAWEN Studio (sovereign mode)
├── Voice    · Piper TTS (MIT · local · CPU)
├── Captions · Whisper (MIT · local)
├── Screen   · Playwright (Apache · local)
└── Compose  · FFmpeg (LGPL · local)

Hosting:  VPS40 (Contabo bare-metal · EU)
Network:  zero outbound calls during generation
Audit:    every step logged · open source · auditable
```

**النتيجة:** بياناتك ↔ خوادمك فقط. لا Microsoft. لا Google. لا OpenAI cloud.

---

## التشغيل في sovereign mode

### 1. تثبيت Piper + الأصوات
```bash
pip install piper-tts
bash voice/install_piper.sh
```

ينزّل:
- `ar_JO-kareem-medium.onnx` (63MB · جودة عالية · CPU realtime)
- `ar_JO-kareem-low.onnx` (17MB · أسرع · low-spec)

### 2. التشغيل الافتراضي (sovereign by default)
```bash
python studio.py scripts/01-mystoq-beauty-cod.md
```

النظام يستخدم Piper تلقائياً. لا حاجة لـ Azure key.

### 3. تأكيد السيادة
```bash
# اختبر TTS فقط
python voice/router.py --text scripts/test-amina.txt --mode sovereign --out test.mp3

# response:
# {
#   "ok": true,
#   "engine": "piper",
#   "sovereign": true,    ← هذا يثبت
#   ...
# }
```

---

## أوضاع التشغيل (4 modes)

| Mode | الوصف | متى تستخدمه |
|---|---|---|
| **sovereign** | Piper local فقط · افتراضي | كل الإنتاج العام |
| **cloud** | Azure DZ Amina/Ismael | عندما تحتاج DZ accent ناتج جودة عالية |
| **hybrid** | Piper أوّلاً · fallback Azure | اختبار قبل الالتزام |
| **clone** | (Phase 3) custom DZ voice | بعد تدريب نموذج DZ خاصّ |

التحكّم:
```bash
# عبر env
export TKAWEN_TTS_MODE=sovereign

# أو في YAML للـ template
echo 'tts_mode: sovereign' >> templates/mystoq-beauty.yaml

# أو CLI
python voice/router.py --mode hybrid ...
```

---

## مقارنة الجودة (واقعيّاً)

| البُعد | Piper Arabic | Azure ar-DZ |
|---|---|---|
| لكنة | **MSA (شامي خفيف)** | DZ نقي |
| طبيعيّة | جيّدة جدّاً | ممتازة |
| سرعة inference | <1s realtime · CPU | ~2s + network |
| تكلفة 240 فيديو | $0 | $2-3 |
| سيادة | ✅ كاملة | ❌ Microsoft |
| تخصيص | ✅ يمكن fine-tune | ❌ مغلق |

**التوصية الواقعيّة:**
- **Studio Beta · Internal Marketing** → `sovereign` mode (Piper) — كافٍ للجودة
- **Founder Story · Testimonials** → `cloud` mode (Azure DZ) — لكنة DZ تهمّ هنا
- **Public Studio Pro SaaS** → `sovereign` only — لا تبيع dependency على Azure

---

## Phase 3 · Custom DZ Voice Training (الهدف النهائي)

لتحقيق سيادة كاملة + لكنة DZ نقيّة:

### الخطوات
1. **سجّل dataset DZ Darija:**
   - 30-60 دقيقة من قراءة نصوص متنوّعة
   - WAV 24kHz mono
   - شخص واحد · بيئة هادئة
   - يمكن تسجيل الـ founder أو متعاوِنة

2. **التدريب:**
   - Fine-tune Piper على الـ dataset
   - Hardware: GPU 8GB+ · 4-8 ساعات training
   - أو على VPS GPU مؤقّت ($1-2/ساعة على RunPod)

3. **النشر:**
   - النموذج النهائي: ~60MB
   - حقوق ملكيّة: TKAWEN كاملة
   - استخدام تجاري بدون قيود

### التكلفة
- Recording: 0$ (founder)
- Training (RunPod): ~$15
- License: $0 (own)

**النتيجة:** صوت DZ Darija حقيقي · سيادي 100% · مدى الحياة.

---

## Sovereign infrastructure roadmap

| Phase | المنتج | الحالة |
|---|---|---|
| **1** | Piper MSA + Whisper + Playwright + FFmpeg | ✅ النَهج الحالي |
| **2** | API endpoint `tts.tkawen.com` | 🔵 قادم |
| **3** | Custom DZ Darija voice trained | 🔵 60 يوم |
| **4** | Fine-tuned Whisper on DZ corpus | 🔵 90 يوم |
| **5** | Sell `tts.tkawen.com` as Infra layer 5 | 🔵 Q3 2026 |

---

## Audit log (proof of sovereignty)

كل تشغيل يولّد:
```
output/<script>/audit.json
{
  "engine": "piper",
  "voice_id": "ar_JO-kareem-medium",
  "license": "MIT",
  "sovereign": true,
  "outbound_calls": 0,
  "data_sent_to_third_party": "none",
  "compliant_with": ["Loi 18-07", "GDPR Art 6"]
}
```

(Implementation pending — Phase 2)
