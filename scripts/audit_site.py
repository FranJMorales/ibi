#!/usr/bin/env python3
"""Auditoria tecnica del sitio. Comprueba que todo funciona antes de publicar.

Verifica:
  1. Estructura HTML (etiquetas mal cerradas o sin cerrar).
  2. Enlaces internos y anclas (#) que no existen.
  3. Imagenes: que el fichero exista y que tenga alt, width y height.
  4. Bloques JSON-LD: que sean JSON valido.
  5. sitemap.xml: XML valido, sin URLs que sean paginas de redireccion y sin URLs
     que no existan como fichero.
  6. Titles y meta descriptions duplicados entre paginas.
  7. Con --external, el codigo HTTP de todos los enlaces externos publicados.

Uso:  python3 scripts/audit_site.py [--external]
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"
VOID = {"meta", "link", "img", "br", "hr", "input", "source", "col", "area", "base", "wbr"}
UA = "Mozilla/5.0 (compatible; TasasMunicipales-audit/1.0)"


class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
            self.errors.append(f"cierre desordenado de <{tag}>")
        else:
            self.errors.append(f"</{tag}> sin apertura")


def pages() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)


def is_redirect_stub(html_text: str) -> bool:
    return 'http-equiv="refresh"' in html_text


def main() -> int:  # noqa: C901, PLR0912, PLR0915
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true", help="comprobar enlaces externos por HTTP")
    args = ap.parse_args()

    files = pages()
    problems: list[str] = []
    ids_by_file: dict[Path, set[str]] = {}
    texts: dict[Path, str] = {}

    for path in files:
        texts[path] = path.read_text(encoding="utf-8")
        ids_by_file[path] = set(re.findall(r'id="([^"]+)"', texts[path]))

    # 1. estructura
    bad_structure = 0
    for path, html_text in texts.items():
        parser = Structure()
        parser.feed(html_text)
        if parser.errors or parser.stack:
            bad_structure += 1
            detail = "; ".join(parser.errors[:2]) or f"sin cerrar: {parser.stack[:3]}"
            problems.append(f"[html] {path.relative_to(ROOT)}: {detail}")
    print(f"1. estructura HTML .............. {len(files) - bad_structure}/{len(files)} correctas")

    # 2. enlaces internos y anclas
    internal = broken = 0
    for path, html_text in texts.items():
        base = path.parent
        for href in re.findall(r'href="([^"]+)"', html_text):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
                continue
            if "${" in href:
                continue  # plantilla de JavaScript, se resuelve en el navegador
            target, _, frag = href.partition("#")
            if not target:
                if frag and frag not in ids_by_file[path]:
                    broken += 1
                    problems.append(f"[ancla] {path.relative_to(ROOT)} -> #{frag} no existe")
                continue
            internal += 1
            resolved = (base / target).resolve()
            candidate = resolved if resolved.is_file() else resolved / "index.html"
            if not candidate.exists():
                broken += 1
                problems.append(f"[enlace] {path.relative_to(ROOT)} -> {href}")
                continue
            if frag:
                target_ids = ids_by_file.get(candidate, set(re.findall(r'id="([^"]+)"', candidate.read_text(encoding="utf-8"))))
                if frag not in target_ids:
                    broken += 1
                    problems.append(f"[ancla] {path.relative_to(ROOT)} -> {href} no existe en destino")
    print(f"2. enlaces internos y anclas .... {internal} comprobados, {broken} roto(s)")

    # 3. imagenes
    imgs = missing = sin_alt = sin_dim = 0
    for path, html_text in texts.items():
        for tag in re.findall(r"<img[^>]*>", html_text):
            imgs += 1
            src = re.search(r'src="([^"]+)"', tag)
            if not src:
                problems.append(f"[img] {path.relative_to(ROOT)}: <img> sin src")
                continue
            if not src.group(1).startswith("http"):
                resolved = (path.parent / src.group(1)).resolve()
                if not resolved.exists():
                    missing += 1
                    problems.append(f"[img] {path.relative_to(ROOT)} -> {src.group(1)} no existe")
            if 'alt="' not in tag:
                sin_alt += 1
                problems.append(f"[img] {path.relative_to(ROOT)} -> {src.group(1)} sin alt")
            if 'width="' not in tag or 'height="' not in tag:
                sin_dim += 1
                problems.append(f"[img] {path.relative_to(ROOT)} -> {src.group(1)} sin width/height")
    print(f"3. imágenes .................... {imgs} etiquetas · {missing} inexistentes · {sin_alt} sin alt · {sin_dim} sin dimensiones")

    # 4. JSON-LD
    blocks = invalid = 0
    for path, html_text in texts.items():
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S):
            blocks += 1
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                invalid += 1
                problems.append(f"[jsonld] {path.relative_to(ROOT)}: {exc}")
    print(f"4. bloques JSON-LD ............. {blocks} encontrados, {invalid} inválido(s)")

    # 5. sitemap
    try:
        tree = ET.parse(ROOT / "sitemap.xml")
        locs = [el.text.strip() for el in tree.getroot().iter() if el.tag.endswith("loc") and el.text]
        stubs = ausentes = 0
        for loc in locs:
            rel = loc.replace(SITE, "").strip("/")
            candidate = ROOT / rel / "index.html" if rel else ROOT / "index.html"
            if not candidate.exists():
                ausentes += 1
                problems.append(f"[sitemap] {loc} no existe como fichero")
            elif is_redirect_stub(candidate.read_text(encoding="utf-8")):
                stubs += 1
                problems.append(f"[sitemap] {loc} es una página de redirección y no debe estar en el sitemap")
        print(f"5. sitemap ..................... {len(locs)} URLs · {ausentes} inexistentes · {stubs} redirecciones")
    except ET.ParseError as exc:
        problems.append(f"[sitemap] XML inválido: {exc}")
        print("5. sitemap ..................... XML INVÁLIDO")

    # 6. titles y descriptions duplicados (solo paginas indexables)
    titles: Counter = Counter()
    descs: Counter = Counter()
    for path, html_text in texts.items():
        if is_redirect_stub(html_text) or 'name="robots" content="noindex' in html_text:
            continue
        title = re.search(r"<title>([^<]*)</title>", html_text)
        desc = re.search(r'name="description" content="([^"]*)"', html_text)
        if title:
            titles[title.group(1).strip()] += 1
        if desc:
            descs[desc.group(1).strip()] += 1
    dup_t = {k: v for k, v in titles.items() if v > 1}
    dup_d = {k: v for k, v in descs.items() if v > 1}
    for k, v in dup_t.items():
        problems.append(f"[title] duplicado en {v} páginas: {k[:70]}")
    for k, v in dup_d.items():
        problems.append(f"[description] duplicada en {v} páginas: {k[:70]}")
    print(f"6. metadatos ................... {len(titles)} títulos únicos · {len(dup_t)} duplicados · {len(dup_d)} descripciones duplicadas")

    # 7. enlaces externos
    if args.external:
        externals: dict[str, list[str]] = defaultdict(list)
        for path, html_text in texts.items():
            for href in re.findall(r'href="(https?://[^"]+)"', html_text):
                if "tasasmunicipales.info" in href or "fonts.googleapis" in href:
                    continue
                externals[href].append(str(path.relative_to(ROOT)))
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ok = ko = 0
        for url in sorted(externals):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=25, context=ctx) as resp:
                    status = resp.status
            except urllib.error.HTTPError as exc:
                status = exc.code
            except Exception:  # noqa: BLE001
                status = 0
            if status == 200:
                ok += 1
            else:
                ko += 1
                problems.append(f"[externo] {status} {url} (en {externals[url][0]})")
        print(f"7. enlaces externos ............ {ok} responden 200 · {ko} requieren revisión")

    print()
    if problems:
        print(f"INCIDENCIAS: {len(problems)}")
        for line in problems[:60]:
            print("  -", line)
        if len(problems) > 60:
            print(f"  … y {len(problems) - 60} más")
        return 1
    print("Sin incidencias.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
