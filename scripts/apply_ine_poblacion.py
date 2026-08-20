#!/usr/bin/env python3
"""Publica en las fichas la poblacion oficial del INE y retira la cifra sin fuente.

Dos objetivos:
  1. Dejar de publicar cifras de poblacion que no venian de ninguna fuente citada y
     que en 133 de 134 municipios no coincidian con las oficiales.
  2. Responder a la intencion «habitantes {municipio} 2026», que acumula cientos de
     impresiones sin un solo clic porque el dato no estaba.

Uso:  python3 scripts/apply_ine_poblacion.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"


def miles(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def procesa(m: dict, dry: bool) -> list[str]:
    ruta = ROOT / m["ccaa"] / m["provincia_slug"] / m["slug"] / "index.html"
    if not ruta.exists() or not m.get("poblacion_oficial"):
        return []
    texto = ruta.read_text(encoding="utf-8")
    original = texto
    cambios: list[str] = []

    oficial = m["poblacion_oficial"]
    ano = m.get("poblacion_ejercicio", 2025)
    antigua = m.get("poblacion")
    nombre = m["nombre"]

    # 1. Línea de metadatos del encabezado
    texto, n = re.subn(
        r"(· Población: )[\d.]+( hab\.)",
        lambda mo: f"{mo.group(1)}{miles(oficial)}{mo.group(2)} (INE, {ano})",
        texto,
    )
    if n:
        cambios.append(f"meta×{n}")

    # 2. Cualquier otra mención de la cifra antigua (lead, resumen lateral, FAQ…)
    if antigua and antigua != oficial:
        for variante in {miles(antigua), str(antigua)}:
            texto, n = re.subn(re.escape(variante), miles(oficial), texto)
            if n:
                cambios.append(f"cifra-antigua×{n}")

    # 3. Fila en la tabla de datos oficiales + frase con la fuente
    if "Población oficial" not in texto:
        fila = (
            f'<tr><td>Población oficial ({ano})</td><td>{miles(oficial)} habitantes</td>'
            f"<td>Cifras oficiales del padrón municipal a 1 de enero de {ano}</td></tr>"
        )
        texto, n = re.subn(
            r"(<tr><td>Valores catastrales en vigor desde</td>)",
            lambda mo: fila + "\n            " + mo.group(1),
            texto,
            count=1,
        )
        if not n:
            texto, n = re.subn(
                r"(</tbody>\s*</table>\s*<div class=\"note\"><strong>📌 Ejercicio)",
                lambda mo: fila + "\n          " + mo.group(1),
                texto,
                count=1,
            )
        if n:
            cambios.append("fila-poblacion")

    # 4. Frase con la fuente, que además responde a «habitantes {municipio} {año}»
    if "según las cifras oficiales del padrón" not in texto:
        frase = (
            f'<p>{nombre} tiene <strong>{miles(oficial)} habitantes</strong> según las cifras '
            f"oficiales del padrón municipal a 1 de enero de {ano}, publicadas por el "
            f'<a href="{m["poblacion_fuente_url"]}" target="_blank" rel="nofollow noopener">INE</a>. '
            "Es el dato que se usa para clasificar al municipio en los tramos que aplican "
            "algunas ordenanzas fiscales.</p>"
        )
        texto, n = re.subn(
            r'(<div class="note"><strong>📌 Ejercicio)',
            lambda mo: frase + "\n        " + mo.group(1),
            texto,
            count=1,
        )
        if n:
            cambios.append("frase-poblacion")

    if texto != original and not dry:
        ruta.write_text(texto, encoding="utf-8")
    return cambios


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    municipios = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    total = aplicadas = 0
    for m in municipios:
        cambios = procesa(m, args.dry_run)
        if cambios:
            aplicadas += 1
            total += len(cambios)
    print(f"fichas actualizadas con la población oficial: {aplicadas} · sustituciones: {total}")
    sin_dato = [m["nombre"] for m in municipios if not m.get("poblacion_oficial")]
    if sin_dato:
        print(f"  sin cifra oficial: {', '.join(sin_dato)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
