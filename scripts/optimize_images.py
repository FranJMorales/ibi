#!/usr/bin/env python3
"""Reduce el peso de las infografías y las sirve en WebP con respaldo JPEG.

Las cuatro infografías pesaban entre 375 y 640 KB (2,2 MB en total) para mostrarse
a menos de 800 px de ancho, y además se declaraban con 800×500 cuando son
cuadradas: el navegador reservaba un hueco con la proporción equivocada, lo que
desplaza el contenido al cargar (CLS).

Qué hace:
  1. Reescala a MAX_LADO y genera un .webp y un .jpg optimizados.
  2. Sustituye cada <img> por un <picture> con el WebP primero y el JPEG detrás.
  3. Escribe width/height reales para que no haya salto de maquetación.

Uso:  python3 scripts/optimize_images.py [--max-lado 900] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
IMG_RE = re.compile(r'<img\s[^>]*?src="([^"]*?/img/[^"]+\.jpg)"[^>]*>', re.I)
ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')


def optimiza(path: Path, max_lado: int, dry: bool,
             force: bool = False) -> tuple[int, int, int, tuple[int, int]]:
    """Devuelve (bytes antes, bytes jpg, bytes webp, (ancho, alto))."""
    antes = path.stat().st_size
    webp = path.with_suffix(".webp")
    with Image.open(path) as im:
        ya_optimizada = webp.exists() and max(im.size) <= max_lado
        if ya_optimizada and not force:
            # Re-comprimir una imagen ya comprimida solo degrada la calidad.
            return antes, antes, webp.stat().st_size, im.size
        im = im.convert("RGB")
        if max(im.size) > max_lado:
            escala = max_lado / max(im.size)
            nuevo = (round(im.width * escala), round(im.height * escala))
            im = im.resize(nuevo, Image.LANCZOS)
        lado_w, lado_h = im.size
        if not dry:
            im.save(webp, "WEBP", quality=78, method=6)
            im.save(path, "JPEG", quality=80, optimize=True, progressive=True)
    return (antes, path.stat().st_size,
            webp.stat().st_size if webp.exists() else 0, (lado_w, lado_h))


def to_picture(tag: str, ancho: int, alto: int) -> str:
    attrs = dict(ATTR_RE.findall(tag))
    src = attrs["src"]
    attrs["width"] = str(ancho)
    attrs["height"] = str(alto)
    attrs.setdefault("loading", "lazy")
    attrs.setdefault("decoding", "async")
    orden = ["src", "alt", "width", "height", "loading", "decoding"]
    partes = [f'{k}="{attrs[k]}"' for k in orden if k in attrs]
    partes += [f'{k}="{v}"' for k, v in attrs.items() if k not in orden]
    img = "<img " + " ".join(partes) + ">"
    return (
        '<picture>'
        f'<source srcset="{src[:-4]}.webp" type="image/webp">'
        f'{img}'
        '</picture>'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-lado", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="vuelve a comprimir aunque ya exista el .webp")
    args = ap.parse_args()

    tamanos: dict[str, tuple[int, int]] = {}
    total_antes = total_jpg = total_webp = 0
    for jpg in sorted(IMG.glob("*.jpg")):
        antes, despues, webp, (w, h) = optimiza(
            jpg, args.max_lado, args.dry_run, args.force)
        tamanos[jpg.name] = (w, h)
        total_antes += antes
        total_jpg += despues
        total_webp += webp
        print(f"  {jpg.name:34} {antes // 1024:>4} KB → jpg {despues // 1024:>3} KB · "
              f"webp {webp // 1024:>3} KB · {w}×{h}")
    print(f"  {'TOTAL':34} {total_antes // 1024:>4} KB → jpg {total_jpg // 1024:>3} KB · "
          f"webp {total_webp // 1024:>3} KB")

    cambiadas = 0
    for html in ROOT.rglob("index.html"):
        if ".git" in html.parts:
            continue
        texto = original = html.read_text(encoding="utf-8")

        def reemplaza(m: re.Match) -> str:
            nombre = m.group(1).rsplit("/", 1)[-1]
            if nombre not in tamanos:
                return m.group(0)
            w, h = tamanos[nombre]
            return to_picture(m.group(0), w, h)

        # no envolver dos veces
        texto = re.sub(
            r'<picture><source srcset="[^"]+" type="image/webp">(<img [^>]*>)</picture>',
            r"\1", texto,
        )
        texto = IMG_RE.sub(reemplaza, texto)
        if texto != original:
            cambiadas += 1
            if not args.dry_run:
                html.write_text(texto, encoding="utf-8")
    print(f"  páginas actualizadas: {cambiadas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
