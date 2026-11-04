#!/bin/sh
set -eu
# Sitio estático: restaura docs y el perfil; no hay base de datos ni migraciones.
cd "$(dirname "$0")"
repo=juanw2023/juanw2023.github.io
for tool in gh git python3; do command -v "$tool" >/dev/null; done
# El historial va de más reciente a más antiguo; los intentos fallidos no publican.
versions=$(gh api "repos/$repo/pages/builds?per_page=100" --jq \
    '[.[] | select(.status == "built")] | .[].commit')
versions=$(printf '%s\n' "$versions" | awk '!seen[$0]++ {print; if (++count == 2) exit}')
current=$(printf '%s\n' "$versions" | sed -n '1p')
case "$current" in ''|*[!0-9a-f]*) echo "El build actual no está publicado" >&2; exit 1;; esac
[ "${#current}" -eq 40 ] || exit 1
previous=$(printf '%s\n' "$versions" | sed -n '2p')
case "$previous" in ''|*[!0-9a-f]*) echo "No hay una versión anterior publicada válida" >&2; exit 1;; esac
[ "${#previous}" -eq 40 ] || exit 1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT HUP INT TERM
git clone --quiet "https://github.com/$repo.git" "$work/site"
cd "$work/site"
git cat-file -e "$previous^{commit}"
# Mantiene intactas las verificaciones de Search Console y el resto del checkout.
git diff --binary HEAD "$previous" -- docs perfil ':!docs/google*.html' > "$work/rollback.patch"
if [ ! -s "$work/rollback.patch" ]; then
    echo "El contenido ya coincide con la versión anterior"; exit 0
fi
git apply --index "$work/rollback.patch"
./verify.sh
git -c user.name='Pages rollback' -c user.email='juanw2023@users.noreply.github.com' \
    commit -m "Restaurar sitio publicado $previous" -- docs perfil
# Usa el publicador vigente: push sin force, espera Pages y sincroniza el perfil.
./publicar.sh
./comprobar.sh
