# -*- coding: utf-8 -*-
"""Add the og:image block to every corporate page (idempotent, per-file backup)."""
import os, re, sys, time

ROOT = "/var/www/tkawen-corporate"
STAMP = time.strftime("%Y%m%d-%H%M%S")
AR = "https://tkawen.com/og-image.png"
EN = "https://tkawen.com/og-image-en.png"
ALT_AR = "TKAWEN — منظومة رقمية جزائرية واحدة"
ALT_EN = "TKAWEN — one Algerian digital ecosystem"


def block(url, alt):
    return (
        f'<meta property="og:image" content="{url}">\n'
        f'    <meta property="og:image:secure_url" content="{url}">\n'
        f'    <meta property="og:image:type" content="image/png">\n'
        f'    <meta property="og:image:width" content="1200">\n'
        f'    <meta property="og:image:height" content="630">\n'
        f'    <meta property="og:image:alt" content="{alt}">\n'
        f'    <meta name="twitter:image" content="{url}">\n'
        f'    <meta name="twitter:image:alt" content="{alt}">'
    )


def main():
    changed, skipped, failed = [], [], []
    for dirpath, _dirs, files in os.walk(ROOT):
        if "/.git" in dirpath:
            continue
        for fn in files:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dirpath, fn)
            s = open(p, encoding="utf-8").read()
            if "og:image" in s:
                skipped.append(p)
                continue
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            latin = rel.startswith(("en/", "fr/")) or "-en.html" in fn or "-fr.html" in fn
            blk = block(EN if latin else AR, ALT_EN if latin else ALT_AR)

            # put it right after og:url, else after og:site_name, else before </head>
            for pat in (r'<meta property="og:url"[^>]*>',
                        r'<meta property="og:site_name"[^>]*>'):
                m = re.search(pat, s)
                if m:
                    s2 = s[:m.end()] + "\n    " + blk + s[m.end():]
                    break
            else:
                m = re.search(r"</head>", s, re.I)
                if not m:
                    failed.append(p)
                    continue
                s2 = s[:m.start()] + "    " + blk + "\n" + s[m.start():]

            open(p + f".bak-og-{STAMP}", "w", encoding="utf-8").write(s)
            open(p, "w", encoding="utf-8").write(s2)
            changed.append(rel)

    print("changed:", len(changed))
    for c in sorted(changed):
        print("  +", c)
    print("already had og:image:", len(skipped), "| no <head>:", len(failed))
    for f in failed:
        print("  !", f)


if __name__ == "__main__":
    sys.exit(main())
