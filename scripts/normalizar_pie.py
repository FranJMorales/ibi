#!/usr/bin/env python3
"""Pone al dia las frases del pie que seguian diciendo «datos orientativos».

Los datos del sitio ya no salen de ordenanzas transcritas a mano: los tipos son
del Ministerio de Hacienda, la poblacion del INE y la normativa del BOE, y lo que
no se puede verificar directamente no se publica (ver
scripts/retirar_datos_sin_fuente.py). El pie de las paginas estaticas todavia
arrastraba las dos frases antiguas, que ahora contradicen a la propia pagina.

Las paginas generadas reciben el pie nuevo de tp.footer_block(); este script
cubre las que no pasan por ningun generador (contacto, calculadora, legales,
guias historicas).

Uso:  python3 scripts/normalizar_pie.py [--dry-run]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SALTAR = {".git", "node_modules", "scripts", "img", ".qa"}

CAMBIOS = (
    (
        "Datos orientativos. Consulta siempre tu ayuntamiento.",
        "Datos del Ministerio de Hacienda, el INE y el BOE. La ordenanza de tu "
        "ayuntamiento es la que manda.",
    ),
    (
        "Datos orientativos basados en ordenanzas fiscales municipales.",
        "Datos del Ministerio de Hacienda, el INE y el BOE, con la fecha de "
        "comprobación en cada página.",
    ),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tocadas = 0
    for path in sorted(ROOT.rglob("index.html")):
        if SALTAR & set(path.relative_to(ROOT).parts):
            continue
        texto = original = path.read_text(encoding="utf-8")
        for viejo, nuevo in CAMBIOS:
            texto = texto.replace(viejo, nuevo)
        if texto != original:
            tocadas += 1
            if not args.dry_run:
                path.write_text(texto, encoding="utf-8")

    print(f"pies actualizados: {tocadas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
