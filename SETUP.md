# 🎬 TKAWEN Studio · Setup

## 1. Azure account (مطلوب — لـ DZ voices)

Azure هو **الوحيد** اللي عنده `ar-DZ-AminaNeural` و `ar-DZ-IsmaelNeural`.

### Sign-up (مجّاني — 5 ساعات شهرياً مجّاناً)

1. روح [azure.microsoft.com/free](https://azure.microsoft.com/free)
2. Sign in بحساب Microsoft (أو أنشئ واحد بـ بريد TKAWEN)
3. Free account = $200 credit + 12 شهر مجّاناً

### إنشاء Speech resource

1. Azure Portal → "Create a resource"
2. ابحث عن **"Speech"** → Create
3. اختر:
   - Subscription: Free (أو Pay-as-you-go)
   - Resource group: `tkawen-studio`
   - Region: **`France Central`** ⚠️ (أقرب datacenter للـ DZ)
   - Name: `tkawen-studio-tts`
   - Pricing tier: **Free F0** (5 ساعات/شهر مجّاناً) أو **Standard S0** (16$ لكل مليون حرف)

4. بعد الإنشاء → Keys and Endpoint → انسخ **Key 1**

### حفظ المفتاح

```bash
# Windows PowerShell (permanent)
[Environment]::SetEnvironmentVariable("AZURE_SPEECH_KEY", "your-key-here", "User")

# أو في session واحدة:
$env:AZURE_SPEECH_KEY = "your-key-here"
```

أعد فتح PowerShell بعد الـ permanent set.

---

## 2. Python environment

```bash
cd D:/F/tkawen-studio

# إنشاء venv (أوّل مرّة)
python -m venv venv
venv\Scripts\activate

# تثبيت dependencies
pip install -r requirements.txt

# Playwright browsers (بعد install)
playwright install chromium
```

---

## 3. اختبار صوت Amina (Day 1)

```bash
# تأكّد من activate venv
venv\Scripts\activate

# اختبار سريع
python voice/tts.py --text scripts/test-amina.txt --out output/amina-test.mp3

# اسمع النتيجة
start output/amina-test.mp3
```

**النتيجة المتوقَّعة:** ملف MP3 بطول ~30 ثانية بصوت Amina الجزائري.

### اختبار صوت Ismael
```bash
python voice/tts.py --text scripts/test-amina.txt --out output/ismael-test.mp3 --voice ismael
```

### تجربة presets مختلفة
```bash
python voice/tts.py --text scripts/test-amina.txt --out output/amina-energetic.mp3 --preset energetic
```

---

## 4. تقييم الصوت (مهمّ)

افتح كل ملف في output/ واسمعه. اسأل نفسك:
- [ ] هل اللكنة جزائريّة فعلاً (ليست شاميّة/مصريّة)؟
- [ ] هل ينطق "بـ COD" صحيحاً؟
- [ ] هل ينطق "Mystoq" صحيحاً؟
- [ ] هل الـ pacing مريح للأذن (ليس سريع/بطيء)؟
- [ ] هل ينطق الأرقام بـ الجزائريّة (1500 = "ألف وخمسمائة")؟

إذا 4/5 ✓ → نمضي إلى Day 3 (screen recorder).
إذا أقل → نضبط SSML rate/pitch + نختبر.

---

## 5. Troubleshooting

### "Authentication failed"
→ تأكّد من `AZURE_SPEECH_KEY` set + region = `francecentral`

### "Quota exceeded"
→ Free F0 = 5 ساعات/شهر. ترقى إلى Standard S0.

### الصوت غير طبيعي
→ جرّب presets: `--preset energetic` أو `calm` أو `urgent`
→ أضف `===` في الـ script لـ pauses طبيعيّة

### Region not available
→ جرّب `westeurope` بدلاً من `francecentral` (ضع في `voice/tts.py`)

---

## ✅ بعد Day 1-2

عندك ملفّات mp3 بصوت DZ حقيقي + جودة 192kbps + duration معروف.

**التالي:** Day 3 — Screen recorder بـ Playwright.
