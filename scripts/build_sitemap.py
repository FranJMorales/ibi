#!/usr/bin/env python3
"""Regenera sitemap.xml de forma determinista.

Motivo: el sitemap se editaba a mano en cada rama y eso provoca conflictos de
fusion constantes (dos ramas cambian el mismo <lastmod> y Git no puede decidir).
Generandolo siempre igual, cualquier conflicto se resuelve regenerando el fichero.

Reglas:
  - Se incluyen todas las paginas indexables: se excluyen las paginas de
    redireccion (meta refresh) y las marcadas con noindex.
  - El <lastmod> es la fecha del ultimo commit que toco ese fichero, asi que el
    valor es reproducible y no depende de cuando se ejecute el script.
  - El orden es estable: home, guias nacionales, hubs, pilares y fichas.

Uso:  python3 scripts/build_sitemap.py [--check]
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"

GUIAS = ["ibi-2026", "calculadora-ibi", "plusvalia", "tasa-basuras", "bonificaciones",
         "comunidades", "municipios", "provincias", "sobre-nosotros", "contacto",
         "aviso-legal", "privacidad", "cookies"]

PRIORIDAD = {0: ("1.0", "weekly"), 1: ("0.9", "weekly"), 2: ("0.8", "monthly"), 3: ("0.7", "monthly")}


def ultima_modificacion(path: Path) -> str:
    try:
        salida = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip()
        return salida or date.today().isoformat()
    except Exception:  # noqa: BLE001
        return date.today().isoformat()


def indexable(path: Path) -> bool:
    texto = path.read_text(encoding="utf-8", errors="ignore")
    if 'http-equiv="refresh"' in texto:
        return False
    return 'name="robots" content="noindex' not in texto


def clave_orden(rel: str) -> tuple:
    partes = [p for p in rel.split("/") if p]
    if not partes:
        return (0, "")
    if len(partes) == 1:
        return (1 if partes[0] in GUIAS else 2, partes[0])
    return (2 + len(partes) - 1, rel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="solo comprueba, no escribe")
    args = ap.parse_args()

    entradas = []
    for path in sorted(ROOT.rglob("index.html")):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        if not indexable(path):
            continue
        rel = str(path.parent.relative_to(ROOT))
        rel = "" if rel == "." else rel + "/"
        entradas.append((clave_orden(rel), rel, ultima_modificacion(path)))

    entradas.sort(key=lambda e: e[0])
    profundidad = {0: 0, 1: 1, 2: 2}
    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for (orden, _), rel, lastmod in entradas:
        nivel = min(orden, 3)
        prioridad, frecuencia = PRIORIDAD[profundidad.get(nivel, 3)] if nivel in profundidad else PRIORIDAD[3]
        lineas += [
            "  <url>",
            f"    <loc>{SITE}/{rel}</loc>",
            f"    <lastmod>{lastmod}</lastmod>",
            f"    <changefreq>{frecuencia}</changefreq>",
            f"    <priority>{prioridad}</priority>",
            "  </url>",
        ]
    lineas.append("</urlset>")
    nuevo = "\n".join(lineas) + "\n"

    destino = ROOT / "sitemap.xml"
    actual = destino.read_text(encoding="utf-8") if destino.exists() else ""
    if args.check:
        print("sitemap.xml está " + ("al día" if actual == nuevo else "DESACTUALIZADO"))
        print(f"  URLs que corresponden: {len(entradas)}")
        return 0 if actual == nuevo else 1

    destino.write_text(nuevo, encoding="utf-8")
    print(f"sitemap.xml regenerado con {len(entradas)} URLs indexables")
    print("  excluidas: páginas de redirección y páginas con noindex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
