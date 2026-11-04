# juanw2023.github.io — web personal de Juan Eduardo Wong Cavero

Sitio estático (HTML + CSS escritos a mano, sin build ni dependencias) publicado en
GitHub Pages desde `docs/` → https://juanw2023.github.io/

Objetivo: que en Google las búsquedas «Juan Eduardo Wong Cavero» y «46098608» (su DNI)
muestren varias páginas de este sitio y su perfil de GitHub. Pedido P-1386 (antes P-0855).

- `docs/` = lo publicado, tal cual. `perfil/README.md` = README del perfil github.com/juanw2023.
- `verify.sh` = pruebas (`tests/test_*.py`, unittest de la biblioteca estándar).
- `publicar.sh` = push a GitHub + espera el build de Pages + sincroniza el README del perfil.
- `comprobar.sh` = revisa el sitio EN VIVO (200, indexable, canonical, sitemap).
- Solo datos reales de Juan. Nada de reseñas, cifras ni logros inventados.
- No enlazar ni nombrar el proyecto Market / compras-peru (Juan no quiere su nombre ahí).
- Archivos `docs/google*.html` = verificación de Search Console: no tocarlos ni borrarlos.
