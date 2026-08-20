#!/usr/bin/env python3
"""Genera vercel.json con las redirecciones 301 reales.

El sitio se sirve desde Vercel, no desde GitHub Pages: eso significa que SI se
pueden emitir redirecciones 301 de verdad, sin depender de meta refresh ni de
Cloudflare. Este script convierte redirects-301.csv en la seccion "redirects" de
vercel.json, que Vercel aplica en el borde antes de servir cualquier fichero.

Las paginas de redireccion de cliente se mantienen en el repositorio como respaldo
inofensivo: con el 301 activo, Vercel responde antes de llegar a ellas.

Uso:  python3 scripts/build_vercel_config.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "redirects-301.csv"
OUT = ROOT / "vercel.json"
SITE = "https://tasasmunicipales.info"


def main() -> int:
    if not CSV.exists():
        print("[error] falta redirects-301.csv")
        return 1

    redirects = []
    for linea in CSV.read_text(encoding="utf-8").splitlines()[1:]:
        if not linea.strip():
            continue
        origen, destino, _ = linea.split(",")
        origen = origen.replace(SITE, "").rstrip("/")
        destino = destino.replace(SITE, "")
        # Vercel trata /ruta y /ruta/ como rutas distintas al hacer match, asi que se
        # declaran las dos formas para no dejar ninguna variante sin redirigir.
        for source in (origen, origen + "/"):
            redirects.append({"source": source, "destination": destino, "permanent": True})

    config = {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "redirects": redirects,
    }
    OUT.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"vercel.json → {len(redirects)} reglas 301 ({len(redirects) // 2} URLs, dos variantes cada una)")
    for r in redirects[:3]:
        print(f"  301  {r['source']}  ->  {r['destination']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
