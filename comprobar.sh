#!/usr/bin/env bash
# Comprueba el sitio EN VIVO: cada URL del sitemap da 200, es indexable, nombra a Juan
# y su canonical es ella misma. Sin IA.
set -euo pipefail
BASE=${BASE:-https://juanw2023.github.io}
NOMBRE="Juan Eduardo Wong Cavero"
fallo() { echo "FALLO: $*"; exit 1; }
n=0
for intento in $(seq 1 40); do   # el CDN de Pages cachea hasta 10 min; ?v= lo salta
    locs=$(curl -fsS "$BASE/sitemap.xml?v=$intento$RANDOM" 2>/dev/null | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g' || true)
    n=$(grep -c . <<<"$locs" || true)
    [ "$n" -ge 5 ] && break
    sleep 15
done
[ "$n" -ge 5 ] || fallo "sitemap con $n URLs (mínimo 5)"
robots=$(curl -fsS "$BASE/robots.txt?v=$RANDOM") || fallo "sin robots.txt"
grep -qiE '^disallow:\s*/\s*$' <<<"$robots" && fallo "robots.txt bloquea todo"
grep -qi "^sitemap: $BASE/sitemap.xml" <<<"$robots" || fallo "robots.txt no declara el sitemap"
dni=0
while read -r u; do
    html=$(curl -fsSL "$u?v=$RANDOM") || fallo "$u no responde 200"
    grep -q "<title>[^<]*$NOMBRE" <<<"$html" || fallo "$u: el <title> no lleva el nombre"
    grep -qi 'noindex' <<<"$html" && fallo "$u: tiene noindex"
    grep -q "rel=\"canonical\" href=\"$u\"" <<<"$html" || fallo "$u: canonical distinto"
    grep -q '46098608' <<<"$html" && dni=$((dni+1))
    echo "ok $u"
done <<<"$locs"
[ "$dni" -ge 1 ] || fallo "ninguna página menciona 46098608"
curl -fsS "https://raw.githubusercontent.com/juanw2023/juanw2023/main/README.md?v=$RANDOM" | grep -q 'juanw2023.github.io' ||
    fallo "el README del perfil no enlaza el sitio"
echo "COMPROBADO: $n páginas en vivo, $dni con el DNI"
