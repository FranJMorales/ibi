#!/usr/bin/env python3
"""Reescribe la cabecera de todo el sitio con el menu agrupado por intencion.

El menu anterior era una fila plana de ocho enlaces que mezclaba tres ejes
(territorio, impuestos, herramienta y editorial) con el mismo peso visual, no
marcaba nunca la pagina activa —el CSS ya tenia `nav a.on` y ninguna de las 162
paginas lo usaba— y no escalaba: con las guias nuevas habrian sido doce.

Ahora son cinco entradas y un boton:
    Mi municipio ▾   Impuestos ▾   Comparativas   Metodologia   [Calcular mi IBI]

El HTML del menu vive en un solo sitio (`nav_block` de build_territory_pillars),
asi que los generadores de pilares, comparador y analisis producen la misma
cabecera que este script aplica al resto.

Uso:  python3 scripts/rebuild_header.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_territory_pillars import nav_block  # noqa: E402

NAV_RE = re.compile(r"[ \t]*<nav(?: [^>]*)?>.*?</nav>", re.S)
# Rutas que el menu enlaza, para saber cual es la pagina activa.
DESTINOS = [
    "municipios/", "comunidades/", "ibi-2026/", "tasa-basuras/", "plusvalia/",
    "bonificaciones/", "impuesto-circulacion/", "valor-catastral/",
    "analisis/", "metodologia/", "calculadora-ibi/",
]


def prefijo(rel: Path) -> str:
    return "../" * (len(rel.parts) - 1)


def activo_de(rel: Path) -> str:
    """La ruta del menu que corresponde a esta pagina, si es una de ellas."""
    carpeta = "/".join(rel.parts[:-1])
    ruta = f"{carpeta}/" if carpeta else ""
    return ruta if ruta in DESTINOS else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cambiadas = activas = sin_nav = 0
    for html in sorted(ROOT.rglob("index.html")):
        if ".git" in html.parts:
            continue
        rel = html.relative_to(ROOT)
        texto = original = html.read_text(encoding="utf-8")
        if not NAV_RE.search(texto):
            sin_nav += 1
            continue
        activo = activo_de(rel)
        if activo:
            activas += 1
        # Solo el primer <nav>: el de la cabecera. Los <nav> internos (si los
        # hubiera) no se tocan.
        texto = NAV_RE.sub(lambda m: nav_block(prefijo(rel), activo), texto, count=1)
        if texto != original:
            cambiadas += 1
            if not args.dry_run:
                html.write_text(texto, encoding="utf-8")

    print(f"  cabeceras reescritas: {cambiadas}")
    print(f"  páginas que marcan su entrada activa: {activas}")
    print(f"  páginas sin cabecera (no se tocan): {sin_nav}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
