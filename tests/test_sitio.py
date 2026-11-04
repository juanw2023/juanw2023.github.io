"""Contrato local de #2316: sólo lectura, sin red ni cuentas externas."""

import datetime
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "https://juanw2023.github.io/"
NAME = "Juan Eduardo Wong Cavero"
DNI = "46098608"
GITHUB = "https://github.com/juanw2023"
ROUTES = ("", "sobre-mi/", "proyectos/", "proyectos/origi-song/",
          "proyectos/origi-vision/", "proyectos/context-vault/",
          "dni-46098608/", "contacto/")


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "text": "",
                "parents": tuple(self.stack)}
        self.nodes.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img",
                       "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def find(self, tag, **attrs):
        return [node for node in self.nodes if node["tag"] == tag and all(
            node["attrs"].get(key) == value for key, value in attrs.items())]


class SitioTests(unittest.TestCase):
    def read(self, relative):
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"Falta el recurso requerido: {relative}")
        return path.read_text(encoding="utf-8")

    def page(self, route):
        relative = "docs/404.html" if route == "404.html" else f"docs/{route}index.html"
        source = self.read(relative)
        return source, Page(source)

    def one(self, nodes, message):
        self.assertEqual(len(nodes), 1, message)
        return nodes[0]

    def meta(self, page, key, value):
        return self.one(page.find("meta", **{key: value}), value)["attrs"].get("content", "")

    def test_ocho_paginas_y_metadatos_unicos(self):
        titles, descriptions = [], []
        for route in ROUTES:
            with self.subTest(route=route):
                _, page = self.page(route)
                self.one(page.find("html", lang="es-PE"), "Idioma es-PE")
                title = self.one(page.find("title"), "Un título")["text"].strip()
                description = self.meta(page, "name", "description")
                self.assertIn(NAME, title)
                self.assertIn(NAME, description)
                self.assertTrue(120 <= len(description) <= 160, description)
                titles.append(title)
                descriptions.append(description)
                h1 = self.one(page.find("h1"), "Exactamente un H1")
                self.assertIn(NAME, h1["text"])
                canonical = self.one(page.find("link", rel="canonical"), "Canonical único")
                self.assertEqual(canonical["attrs"].get("href"), BASE + route)
                for meta in page.find("meta"):
                    self.assertNotIn("noindex", meta["attrs"].get("content", "").lower())
                if not route:
                    self.assertEqual(title, NAME + " — Desarrollador de software y emprendedor en Lima, Perú")
        self.assertEqual(len(set(titles)), 8)
        self.assertEqual(len(set(descriptions)), 8)

    def test_tarjetas_sociales(self):
        for route in ROUTES:
            with self.subTest(route=route):
                _, page = self.page(route)
                for key in ("title", "description", "url", "type", "locale", "image"):
                    self.assertTrue(self.meta(page, "property", "og:" + key))
                self.assertEqual(self.meta(page, "property", "og:url"), BASE + route)
                self.assertEqual(self.meta(page, "property", "og:locale"), "es_PE")
                self.assertEqual(self.meta(page, "name", "twitter:card"), "summary_large_image")
                self.assertEqual(self.meta(page, "property", "og:image"), BASE + "og.png")

    def test_identidad_json_ld(self):
        for route in ROUTES:
            with self.subTest(route=route):
                _, page = self.page(route)
                scripts = page.find("script", type="application/ld+json")
                self.assertTrue(scripts, "Falta JSON-LD")
                graph = []
                for script in scripts:
                    try:
                        data = json.loads(script["text"])
                    except json.JSONDecodeError as error:
                        self.fail(f"JSON-LD inválido: {error}")
                    self.assertIsInstance(data, dict)
                    self.assertEqual(data.get("@context"), "https://schema.org")
                    self.assertIsInstance(data.get("@graph"), list)
                    graph.extend(data["@graph"])
                def typed(kind):
                    return [node for node in graph if kind in (
                        node.get("@type", []) if isinstance(node.get("@type"), list)
                        else [node.get("@type")])]
                person = self.one(typed("Person"), "Person único")
                self.assertEqual(person.get("@id"), BASE + "#person")
                self.assertEqual(person.get("name"), NAME)
                self.assertEqual(set(person.get("alternateName", [])),
                                 {"Juan Wong Cavero", "Juan Eduardo Wong", "Juan Wong"})
                identifier = person.get("identifier", {})
                self.assertEqual(identifier.get("@type"), "PropertyValue")
                self.assertEqual(identifier.get("propertyID"), "DNI")
                self.assertEqual(str(identifier.get("value")), DNI)
                address = person.get("address", {})
                self.assertEqual(address.get("addressLocality"), "Lima")
                self.assertEqual(address.get("addressCountry"), "PE")
                self.assertTrue(person.get("jobTitle"))
                self.assertTrue(person.get("knowsAbout"))
                self.assertEqual(person.get("url"), BASE)
                self.assertEqual(person.get("sameAs"), [GITHUB])
                self.assertTrue(typed("WebSite"))
                self.assertTrue(typed("WebPage") or typed("ProfilePage"))
                self.assertTrue(typed("BreadcrumbList"))

    def test_navegacion_pie_y_recursos_locales(self):
        for route in (*ROUTES, "404.html"):
            with self.subTest(route=route):
                _, page = self.page(route)
                footer = self.one(page.find("footer"), "Pie único")
                footer_links = [node for node in page.find("a") if footer in node["parents"]]
                self.assertTrue(any(
                    " ".join(node["text"].split()) == NAME + " · DNI " + DNI + " · Lima, Perú"
                    and urljoin(BASE + route, node["attrs"].get("href", "")) == BASE + "dni-46098608/"
                    for node in footer_links), "Pie enlazado a identidad")
                self.assertTrue(page.find("nav"), "Navegación interna")
                self.assertTrue(any(node["attrs"].get("aria-label", "").lower() in
                                    {"migas", "migas de pan", "breadcrumb", "breadcrumbs"}
                                    for node in page.find("nav")), "Migas accesibles")
                if route != "404.html":
                    self.assertTrue(any(node["attrs"].get("aria-current") == "page"
                                        and urljoin(BASE + route, node["attrs"].get("href", "")) == BASE + route
                                        for node in page.find("a")), "Menú marca página actual")
                for node in page.nodes:
                    attrs = node["attrs"]
                    if node["tag"] == "img":
                        self.assertIn("alt", attrs)
                    if node["tag"] == "script":
                        self.assertEqual(attrs.get("type"), "application/ld+json", "Sin JavaScript")
                    for key in ("href", "src"):
                        if not attrs.get(key):
                            continue
                        url = urlsplit(urljoin(BASE + route, attrs[key]))
                        self.assertNotIn(url.scheme, {"mailto", "tel", "javascript"})
                        if key == "src" or node["tag"] == "link":
                            self.assertEqual(url.netloc, urlsplit(BASE).netloc, "Sin recursos externos")
                        if url.netloc != urlsplit(BASE).netloc:
                            continue
                        target = DOCS / unquote(url.path).lstrip("/")
                        if url.path.endswith("/"):
                            target /= "index.html"
                        self.assertTrue(target.is_file(), f"Enlace roto: {attrs[key]}")
                        if url.fragment:
                            destination = Page(target.read_text(encoding="utf-8"))
                            self.assertTrue(any(n["attrs"].get("id") == unquote(url.fragment)
                                                for n in destination.nodes), attrs[key])

    def test_contenido_editorial_e_identidad(self):
        for route in (*ROUTES, "404.html"):
            with self.subTest(route=route):
                source, _ = self.page(route)
                self.assertNotRegex(source.lower(), r"market|compras-peru|@gmail|mailto:|tel:")
        _, identity = self.page("dni-46098608/")
        self.assertEqual(self.one(identity.find("title"), "Título identidad")["text"], NAME + " — DNI " + DNI)
        self.assertIn(DNI, self.one(identity.find("h1"), "H1 identidad")["text"])
        text = " ".join(node["text"] for node in identity.find("body"))
        for term in ("oficial", "Lima", "Perú", DNI):
            self.assertIn(term, text)
        links = {urljoin(BASE, n["attrs"].get("href", "")) for n in identity.find("a")}
        self.assertTrue({BASE, GITHUB} <= links)
        _, contact = self.page("contacto/")
        external = {n["attrs"].get("href") for n in contact.find("a")
                    if urlsplit(n["attrs"].get("href", "")).netloc not in {"", urlsplit(BASE).netloc}}
        self.assertEqual(external, {GITHUB})

    def test_proyectos(self):
        requirements = {
            "origi-song": ("ORIGI-SONG", "HarmonyKicks E.I.R.L.", "zapatillas", "Rails", "Vue", "Python", "ventas", "inventario"),
            "origi-vision": ("Origi Vision", "Python", "YOLO", "zonas", "desarrollo"),
            "context-vault": ("Context Vault", "SQLite", "vectores", "desarrollo"),
        }
        _, listing = self.page("proyectos/")
        hrefs = {urljoin(BASE + "proyectos/", node["attrs"].get("href", "")) for node in listing.find("a")}
        for slug, terms in requirements.items():
            with self.subTest(project=slug):
                self.assertIn(BASE + f"proyectos/{slug}/", hrefs)
                _, page = self.page(f"proyectos/{slug}/")
                text = " ".join(node["text"] for node in page.find("body"))
                for term in terms:
                    self.assertIn(term.casefold(), text.casefold())
                self.assertTrue(any(urljoin(BASE + f"proyectos/{slug}/", n["attrs"].get("href", ""))
                                    == BASE + "proyectos/" for n in page.find("a")))
                if slug == "origi-song":
                    self.assertTrue(page.find("a", href="https://www.origi-song.com"))
                    self.assertIn("operación", text.casefold())
                elif slug == "origi-vision":
                    self.assertRegex(text.casefold(), r"re[- ]?identifica")
                    self.assertIn("multicámara", text.casefold())
                    self.assertIn("tienda", text.casefold())
                else:
                    self.assertIn("semántico", text.casefold())
                    self.assertIn("personal", text.casefold())

    def test_sitemap_robots_y_404(self):
        source = self.read("docs/sitemap.xml")
        try:
            root = ET.fromstring(source)
        except ET.ParseError as error:
            self.fail(f"Sitemap inválido: {error}")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall("s:url", ns)
        self.assertCountEqual([node.findtext("s:loc", namespaces=ns) for node in urls],
                              [BASE + route for route in ROUTES])
        for node in urls:
            lastmod = node.findtext("s:lastmod", namespaces=ns)
            self.assertTrue(lastmod, "Cada URL lleva lastmod")
            try:
                datetime.datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
            except ValueError:
                self.fail(f"lastmod inválido: {lastmod}")
        robots = self.read("docs/robots.txt")
        for directive in ("User-agent: *", "Allow: /", "Sitemap: " + BASE + "sitemap.xml"):
            self.assertIn(directive.lower(), robots.lower().splitlines())
        self.assertNotRegex(robots.lower(), r"(?m)^disallow:\s*/\s*$")
        _, page = self.page("404.html")
        self.assertIn("noindex", self.meta(page, "name", "robots").lower())

    def test_imagen_favicon_y_css(self):
        image = DOCS / "og.png"
        self.assertTrue(image.is_file(), "Falta imagen social")
        data = image.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreaterEqual(len(data), 24)
        self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 630))
        favicon = self.read("docs/favicon.svg")
        try:
            self.assertEqual(ET.fromstring(favicon).tag.split("}")[-1], "svg")
        except ET.ParseError as error:
            self.fail(f"Favicon inválido: {error}")
        css = self.read("docs/estilos.css")
        self.assertIn("prefers-color-scheme", css)
        self.assertRegex(css, r":focus(?:-visible)?")
        self.assertNotRegex(css, r"@import|https?://")
        self.assertEqual(list(DOCS.rglob("*.css")), [DOCS / "estilos.css"])
        self.assertTrue((DOCS / ".nojekyll").is_file())

    def test_readme_enlaza_las_ocho_paginas(self):
        readme = self.read("perfil/README.md")
        for term in (NAME, "desarrollador", "Lima", "Perú"):
            self.assertIn(term.casefold(), readme.casefold())
        links = re.findall(r"\]\((https://[^\s)]+)\)", readme)
        for route in ROUTES:
            self.assertIn(BASE + route, links)

    def test_reversion_falla_cerrada_sin_historial_o_con_respuesta_invalida(self):
        # Proveedor simulado: jamás llama a GitHub ni toca el Git del checkout.
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            gh = temp / "gh"
            gh.write_text('#!/bin/sh\ncase "$*" in *latest*) printf "%s\\n" "$LATEST";; *) printf "%s\\n" "$HISTORY";; esac\n')
            git = temp / "git"
            git.write_text('#!/bin/sh\ntouch "$MUTATION"\nexit 99\n')
            gh.chmod(0o755)
            git.chmod(0o755)
            current = "a" * 40
            for latest, history in ((current, current), (current, "invalid-sha"), ("", "b" * 40)):
                with self.subTest(latest=latest, history=history):
                    marker = temp / "mutation"
                    env = dict(os.environ, PATH=str(temp) + os.pathsep + os.environ["PATH"],
                               LATEST=latest, HISTORY=history, MUTATION=str(marker))
                    result = subprocess.run(["sh", str(ROOT / "revertir.sh")], env=env,
                                            capture_output=True, text=True, timeout=10)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(marker.exists(), "No debe modificar sin una versión anterior válida")

    def test_reversion_ignora_intentos_fallidos_y_builds_duplicados(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            history = [
                {"status": "errored", "commit": "f" * 40},
                {"status": "building", "commit": "e" * 40},
                {"status": "built", "commit": "a" * 40},
                {"status": "built", "commit": "a" * 40},
                {"status": "built", "commit": "b" * 40},
            ]
            (temp / "history.json").write_text(json.dumps(history))
            # Simula sólo la lectura del proveedor; Git se detiene antes de mutar.
            gh = temp / "gh"
            gh.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ["REQUEST"]).write_text(" ".join(sys.argv[1:]))
history = json.loads(Path(os.environ["FIXTURE"]).read_text())
if "latest" in sys.argv[2]:
    history = history[:1]
for build in history:
    if build["status"] == "built":
        print(build["commit"])
''')
            git = temp / "git"
            git.write_text('''#!/bin/sh
if [ "$1" = clone ]; then mkdir -p "$4"; exit 0; fi
printf '%s\\n' "$*" >> "$GIT_LOG"
exit 99
''')
            gh.chmod(0o755)
            git.chmod(0o755)
            env = dict(os.environ, PATH=str(temp) + os.pathsep + os.environ["PATH"],
                       FIXTURE=str(temp / "history.json"), REQUEST=str(temp / "request"),
                       GIT_LOG=str(temp / "git.log"))
            result = subprocess.run(["sh", str(ROOT / "revertir.sh")], env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 99, result.stderr)
            self.assertIn("pages/builds?per_page=100", (temp / "request").read_text())
            self.assertEqual((temp / "git.log").read_text(),
                             "cat-file -e " + "b" * 40 + "^{commit}\n")

    def test_reversion_disponible_sin_ejecutar_publicacion(self):
        source = self.read("revertir.sh")
        self.assertTrue(source.startswith("#!/bin/sh\n"))
        self.assertRegex(source, r"(?m)^set -eu\s*$")
        self.assertTrue((ROOT / "revertir.sh").stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
