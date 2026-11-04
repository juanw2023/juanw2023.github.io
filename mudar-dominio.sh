#!/bin/sh
# Muda el sitio de juanw2023.github.io a un dominio propio, cuando Juan lo haya comprado.
#   ./mudar-dominio.sh juaneduardowongcavero.com
# Antes: en el DNS del dominio, 4 registros A (185.199.108-111.153), 4 AAAA
# (2606:50c0:8000-8003::153) y CNAME www -> juanw2023.github.io (docs.github.com, Pages).
# GitHub redirige solo de juanw2023.github.io al dominio; Google pasa lo indexado.
set -eu
cd "$(dirname "$0")"
D=${1:?uso: ./mudar-dominio.sh dominio.com}
REPO=juanw2023/juanw2023.github.io

for ip in 185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153; do
    dig +short A "$D" | grep -qx "$ip" || { echo "Falta el registro A $ip en $D" >&2; exit 1; }
done

grep -rl 'https://juanw2023.github.io/' docs tests perfil comprobar.sh |
    xargs sed -i "s#https://juanw2023.github.io/#https://$D/#g"
echo "$D" > docs/CNAME
./verify.sh

git add docs tests perfil comprobar.sh
git commit -m "feat: sitio en https://$D/"
gh api -X PUT "repos/$REPO/pages" -f cname="$D" >/dev/null
./publicar.sh
# HTTPS: GitHub emite el certificado en minutos; luego forzarlo.
timeout 3600 sh -c "until gh api -X PUT repos/$REPO/pages -F https_enforced=true >/dev/null 2>&1; do sleep 30; done"
./comprobar.sh
# IndexNow (Bing, Yandex…): avisa de todas las URLs del sitemap en el dominio nuevo.
K=$(basename "$(ls docs/*.txt | grep -E '/[0-9a-f]{32}\.txt$')" .txt)
grep -o "https://$D/[^<]*" docs/sitemap.xml | python3 -c "import json,sys; print(json.dumps({'host':'$D','key':'$K','urlList':sys.stdin.read().split()}))" |
    curl -s -o /dev/null -w "IndexNow %{http_code}\n" -H 'Content-Type: application/json' --data-binary @- https://api.indexnow.org/indexnow
echo "Listo. Falta en Search Console: propiedad https://$D/ (gsc.py add + verify) y «Cambio de dirección»."
