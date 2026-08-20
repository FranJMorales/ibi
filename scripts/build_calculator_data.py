#!/usr/bin/env python3
"""Genera /municipios.js, el fichero de datos que consume la calculadora.

Antes, la calculadora llevaba su propio array de municipios incrustado en el HTML
con valores de IBI que NO coincidian con los de las fichas (Aguilas 0,66 frente a
0,63; Caravaca 0,64 frente a 0,61; Mazarron 0,65 frente a 0,63...). Era una quinta
copia de los mismos datos y por tanto una quinta fuente de contradicciones.

Ahora los datos salen de data/municipios.json, la unica fuente de verdad, y el
enlace de cada municipio se calcula solo: si su ficha ya es una pagina de
redireccion hacia un pilar territorial, se enlaza directamente el ancla del pilar
para no pasar por una redireccion.

Uso:  python3 scripts/build_calculator_data.py
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
OUT = ROOT / "municipios.js"
SITE = "https://tasasmunicipales.info"

CCAA_NAMES = {
    "aragon": "Aragón",
    "asturias": "Asturias",
    "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha",
    "castilla-y-leon": "Castilla y León",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "la-rioja": "La Rioja",
    "murcia": "Murcia",
}


def target_url(m: dict) -> str:
    """Ruta relativa a la raiz del sitio para el municipio."""
    ficha = ROOT / m["ccaa"] / m["provincia_slug"] / m["slug"] / "index.html"
    if ficha.exists():
        html_text = ficha.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in html_text:
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html_text)
            if canonical:
                return canonical.group(1).replace(SITE + "/", "")
    return f"{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"


def main() -> int:
    records = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    salida = []
    for m in sorted(records, key=lambda x: x["nombre"]):
        if not m.get("tipo_urbano"):
            continue
        salida.append(
            {
                "nombre": m["nombre"],
                "ccaa": CCAA_NAMES.get(m["ccaa"], m["ccaa"]),
                "url": target_url(m),
                # el tipo oficial del Ministerio manda sobre el publicado antes
                "ibiU": m.get("oficial_tipo_urbana") or m["tipo_urbano"],
                "ibiR": m.get("oficial_tipo_rustica") or m.get("tipo_rustico"),
                "ejercicio": m.get("oficial_ejercicio", ""),
                # No se publican ni la tasa de basuras ni el periodo de pago: no
                # tenian fuente (scripts/retirar_datos_sin_fuente.py). Tampoco los
                # usaba la calculadora, asi que salen tambien del dataset publico.
                "anoValores": m.get("oficial_ano_valores_catastrales", ""),
                "boniFamilia": m.get("boni_familia", ""),
                "boniSolar": m.get("boni_solar", ""),
            }
        )

    body = json.dumps(salida, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(
        "/* Datos municipales para la calculadora.\n"
        "   GENERADO AUTOMÁTICAMENTE por scripts/build_calculator_data.py\n"
        "   desde data/municipios.json. No editar a mano: cualquier cambio debe\n"
        f"   hacerse en la fuente de datos. Última generación: {date.today().isoformat()} */\n"
        f"window.TM_MUNICIPIOS = {body};\n",
        encoding="utf-8",
    )
    print(f"municipios.js → {len(salida)} municipios ({OUT.stat().st_size // 1024} kB)")
    anclas = sum(1 for m in salida if "#" in m["url"])
    print(f"  enlaces directos a pilar territorial (sin redirección): {anclas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
