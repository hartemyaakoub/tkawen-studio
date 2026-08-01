#!/bin/bash
# Serve the two share cards from the apex block. `location =` beats the catch-all
# proxy to the Rust service, so no rebuild and no behaviour change anywhere else.
set -e
CONF=/etc/nginx/sites-enabled/tkawen.com
BAK="$CONF.bak-ogimage-$(date +%s)"
cp "$CONF" "$BAK"
echo "backup: $BAK"

if grep -q 'location = /og-image.png' "$CONF"; then
  echo "already present — nothing to do"
  exit 0
fi

python3 - "$CONF" <<'PY'
import sys, re
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
# anchor on the apex block's own /proof rule (unique, apex-only)
anchor = '    location = /proof    { root /var/www/tkawen-corporate; try_files /proof.html =404;'
i = s.find(anchor)
assert i != -1, 'apex anchor not found'
block = (
    '    location = /og-image.png    { root /var/www/tkawen-corporate; '
    'expires 7d; add_header Cache-Control "public, max-age=604800"; access_log off; }\n'
    '    location = /og-image-en.png { root /var/www/tkawen-corporate; '
    'expires 7d; add_header Cache-Control "public, max-age=604800"; access_log off; }\n'
)
s = s[:i] + block + s[i:]
open(p, 'w', encoding='utf-8').write(s)
print('inserted 2 locations')
PY

nginx -t && systemctl reload nginx && echo "nginx reloaded"
