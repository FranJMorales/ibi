#!/usr/bin/env python3
"""Descarga la serie de población oficial (últimos N años) de cada municipio.

Reutiliza la misma tabla del INE que `sync_ine_poblacion.py` (operación DPOP,
«Cifras Oficiales de Población de los Municipios Españoles»), pero pidiendo
varias revisiones del padrón en lugar de una sola. Con la serie podemos publicar
en cada ficha un dato propio y contrastable —cómo ha evolucionado la población—
en lugar de repetir el mismo texto en 134 páginas.

Salida: `poblacion_serie` en data/municipios.json, como lista de [año, habitantes]
ordenada de más antiguo a más reciente.

Uso:  python3 scripts/sync_ine_serie.py [--anos 6]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_ine_poblacion import (  # noqa: E402
    API,
    DATA,
    PROVINCIAS_INE,
    TODAY,
    claves,
    normaliza,
    pide,
    tabla_por_provincia,
)


def serie_de_tabla(tabla_id: int, anos: int) -> dict[str, list[list[int]]]:
    series = pide(f"{API}/DATOS_TABLA/{tabla_id}?nult={anos}")
    salida: dict[str, list[list[int]]] = {}
    for serie in series:
        nombre = serie.get("Nombre") or ""
        if ". Total. Total habitantes" not in nombre:
            continue
        municipio = nombre.split(". Total.")[0].strip()
        datos = [
            [int(d["Anyo"]), int(d["Valor"])]
            for d in (serie.get("Data") or [])
            if d.get("Valor") is not None
        ]
        if not datos:
            continue
        datos.sort()
        for clave in claves(municipio):
            salida[clave] = datos
    return salida


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anos", type=int, default=6)
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    municipios = payload["municipios"]

    print("Localizando las tablas provinciales del INE…")
    indice = tabla_por_provincia()
    print(f"  {len(indice)} tablas provinciales\n")

    por_provincia: dict[str, list[dict]] = {}
    for m in municipios:
        por_provincia.setdefault(m["provincia_slug"], []).append(m)

    ok = fail = 0
    for prov_slug, lista in sorted(por_provincia.items()):
        nombre_ine = PROVINCIAS_INE.get(prov_slug)
        tabla_id = indice.get(normaliza(nombre_ine or prov_slug))
        if not tabla_id:
            print(f"[aviso] sin tabla para {prov_slug}")
            fail += len(lista)
            continue
        datos = serie_de_tabla(tabla_id, args.anos)
        print(f"{prov_slug} (tabla {tabla_id}): {len(datos)} municipios")
        for m in sorted(lista, key=lambda x: x["nombre"]):
            serie = next((datos[c] for c in claves(m["nombre"]) if c in datos), None)
            if not serie:
                print(f"  [sin coincidencia] {m['nombre']}")
                fail += 1
                continue
            m["poblacion_serie"] = serie
            m["poblacion_serie_comprobada_el"] = TODAY
            ok += 1
            print(f"  {m['nombre']:26} {serie[0][0]}: {serie[0][1]:>8,} → "
                  f"{serie[-1][0]}: {serie[-1][1]:>8,}".replace(",", "."))
        time.sleep(0.3)

    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"\nSeries descargadas: {ok}   sin resolver: {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
