# -*- coding: utf-8 -*-
"""Two corrections across the corporate site. Dry-run unless --apply.

1) The state startup label was cited as «قرار وزاري 1275». That decision belongs
   to the Ministry of Higher Education and governs a STUDENT diploma; the label
   comes from Executive Decree 20-254 (art. 11), JO 55. The site's OTHER 1275
   mentions (UBMA-STARTUP-2023-00062, the university diploma) are correct and
   are left untouched.

2) «سيادي/سياديّة» — wording the founder rejected as puffery. It is always an
   adjective here, so deleting it leaves grammatical copy; the few places where
   it carries meaning are rewritten to say the fact instead.
"""
import os, re, sys, time

ROOT = "/var/www/tkawen-corporate"
APPLY = "--apply" in sys.argv
STAMP = time.strftime("%Y%m%d-%H%M%S")

# ---- 1) the mis-cited decree (state label only) -------------------------------
DECREE = [
    ("مرخّصة من الدولة الجزائريّة (قرار وزاري 1275)",
     "مرخّصة من الدولة الجزائريّة (المرسوم التنفيذيّ 20-254 · علامة رقم 0108242769)"),
    ("licensed by the Algerian State (Ministerial Decree 1275)",
     "licensed by the Algerian State (Executive Decree 20-254 · label No. 0108242769)"),
    ("agréée par l'État algérien (décret ministériel 1275)",
     "agréée par l'État algérien (décret exécutif 20-254 · label n° 0108242769)"),
    ("agréée par l’État algérien (décret ministériel 1275)",
     "agréée par l’État algérien (décret exécutif 20-254 · label n° 0108242769)"),
    ("ⴰⵙⵓⵎⴻⵔ ⵏ ⵓⵙⴻⵇⵇⴰⵎⵓ 1275",
     "ⴰⵙⵓⵎⴻⵔ ⵏ ⵓⵙⴻⵇⵇⴰⵎⵓ 20-254"),
]

# ---- 2) sovereign wording -----------------------------------------------------
# phrase-level first (meaning-bearing), then plain adjective deletion
PHRASES = [
    ('<span class="g">سياديّة</span>', '<span class="g">جزائريّة</span>'),
    ("كلّها جزائريّة السيادة", "كلّها جزائريّة"),
    ("تبقى بنيتنا التحتية سياديّة ومستضافة على خوادم نتحكّم فيها",
     "تبقى بنيتنا التحتية مستضافة على خوادم نتحكّم فيها"),
    ("داخل بنيتنا السياديّة", "داخل بنيتنا التحتيّة"),
    ("استضافة سياديّة جزائريّة", "استضافة جزائريّة"),
    ("هويّة سياديّة مستضافة ذاتيّاً", "هويّة مستضافة ذاتيّاً"),
    ("Souveraineté technologique", "Indépendance technologique"),
    ("Technological sovereignty", "Technological independence"),
    ("tous souverainement algériens", "tous entièrement algériens"),
    ("all sovereignly Algerian", "all entirely Algerian"),
    ("Our infrastructure remains sovereign, hosted on servers we control",
     "Our infrastructure is hosted on servers we control"),
    ("Notre infrastructure reste souveraine, hébergée sur des serveurs que nous",
     "Notre infrastructure est hébergée sur des serveurs que nous"),
    ("within our sovereign infrastructure", "within our own infrastructure"),
    ("au sein de notre infrastructure souveraine", "au sein de notre propre infrastructure"),
]

# adjective deletion (the word always follows/precedes a noun it merely decorates)
HARAKAT = "ً-ْ"          # tanwin, shadda, sukun …
ADJ = [
    # \b is useless after an Arabic diacritic (marks are not word characters), so
    # the engine backtracks and leaves an orphan shadda: «عربيّ سياديّ» -> «عربيّّ».
    # Consume any trailing diacritics explicitly and end on a real delimiter.
    (re.compile(rf"\s+(?:ال)?سيادي[{HARAKAT}]*(?:ة|ات|اً|ا|ين|ون)?[{HARAKAT}]*"
                rf"(?=[\s<.,،:;·—()\[\]]|$)"), ""),
    (re.compile(r"\s+souverain(?:es|e|s)?\b", re.I), ""),
    (re.compile(r"\bsovereign\s+", re.I), ""),
]
# English article agreement after removing the adjective
ARTICLE = [
    (re.compile(r"\ba (Algerian|AI|API|Arabic|identity|infrastructure|ecosystem)\b"), r"an \1"),
    (re.compile(r"\bA (Algerian|AI|API|Arabic)\b"), r"An \1"),
]
# No whitespace "tidying": the adjective rules already swallow their own leading
# space, and a global rule stripped the space before every «·» on the site.
TIDY = []


def fix(s):
    n = 0
    for a, b in DECREE + PHRASES:
        if a in s:
            n += s.count(a)
            s = s.replace(a, b)
    for rx, rep in ADJ:
        s, k = rx.subn(rep, s)
        n += k
    for rx, rep in ARTICLE + TIDY:
        s = rx.sub(rep, s)
    return s, n


def main():
    total, touched = 0, []
    for dirpath, _d, files in os.walk(ROOT):
        if "/.git" in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith(".html") or ".bak" in fn:
                continue
            p = os.path.join(dirpath, fn)
            s = open(p, encoding="utf-8").read()
            s2, n = fix(s)
            if n and s2 != s:
                rel = os.path.relpath(p, ROOT)
                touched.append((rel, n))
                total += n
                if APPLY:
                    open(p + f".bak-copy-{STAMP}", "w", encoding="utf-8").write(s)
                    open(p, "w", encoding="utf-8").write(s2)
    print(("APPLIED" if APPLY else "DRY-RUN") + f": {total} replacements in {len(touched)} files")
    for rel, n in sorted(touched, key=lambda t: -t[1]):
        print(f"  {n:>3}  {rel}")


if __name__ == "__main__":
    main()
