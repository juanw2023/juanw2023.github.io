#!/usr/bin/env bash
# Publica docs/ en GitHub Pages y el README del perfil. Sin IA; idempotente.
set -euo pipefail
cd "$(dirname "$0")"
REPO=juanw2023/juanw2023.github.io
./verify.sh
git push origin HEAD:main
gh api "repos/$REPO/pages" >/dev/null 2>&1 ||
    gh api -X POST "repos/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/docs' >/dev/null

if [ -f perfil/README.md ]; then
    PERFIL=juanw2023/juanw2023
    gh repo view "$PERFIL" >/dev/null 2>&1 ||
        gh repo create "$PERFIL" --public -d "Juan Eduardo Wong Cavero" >/dev/null
    nuevo=$(base64 -w0 perfil/README.md)
    actual=$(gh api "repos/$PERFIL/contents/README.md" 2>/dev/null || echo '{}')
    sha=$(jq -r '.sha // empty' <<<"$actual")
    if [ "$(jq -r '.content // ""' <<<"$actual" | tr -d '\n')" != "$nuevo" ]; then
        gh api -X PUT "repos/$PERFIL/contents/README.md" -f message="perfil: README" \
            -f content="$nuevo" ${sha:+-f sha="$sha"} >/dev/null
    fi
fi

sha=$(git rev-parse HEAD)
for _ in $(seq 1 60); do
    estado=$(gh api "repos/$REPO/pages/builds/latest" --jq '.status + " " + .commit' 2>/dev/null || echo "pendiente")
    case "$estado" in
        "built $sha") echo "Pages publicado: $sha"; exit 0 ;;
        errored*) echo "FALLO build de Pages: $estado"; exit 1 ;;
    esac
    sleep 10
done
echo "FALLO: Pages no terminó el build de $sha en 10 min"; exit 1
