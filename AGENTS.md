# juanw2023.github.io — web personal de Juan Eduardo Wong Cavero

Sitio estático (HTML + CSS escritos a mano, sin build) publicado en
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

## Diseño 3D (P-1394, 2026-11-03)

Lenguaje visual de su repo `juanw2023/web_3d_jewc`: fondo hueso `#EBEAE8`, texto `#0F0F0F`,
acento `#FF4D00`, titulares gigantes en mayúsculas (Inter 900, tracking negativo), rótulos en
Space Mono, palabras enormes de fondo con paralaje y un núcleo de vidrio 3D que gira al bajar.

- **Todo el contenido vive en el HTML.** El único JavaScript es la escena decorativa
  `docs/3d/escena.js` (módulo ES + import map hacia `docs/vendor/three/`). Sin JS, sin WebGL o con
  «reducir movimiento», la página se lee completa y sin errores.
- **Sin recursos externos:** three.js r182 (`docs/vendor/three/`, MIT), Inter y Space Mono
  (`docs/fuentes/`, OFL) y el modelo (`docs/3d/nucleo.glb`) viven en el repo.
- **Crédito obligatorio del modelo** (CC BY 4.0, ver `docs/3d/LICENCIA.txt`): «Alliance Core»
  de OrangeSauceu, visible en el pie de cada página que muestre la escena.
- **Texto siempre legible:** nada de `mix-blend-mode` sobre el texto (en el repo original dejaba
  letras blancas sobre fondo claro). El canvas va detrás, `aria-hidden` y sin capturar clics.
- **Nada de «MIT» ni títulos o logros sin verificar:** el repo 3D los traía; aquí no.
