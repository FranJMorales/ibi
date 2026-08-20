#!/usr/bin/env python3
"""Descarga TODOS los parámetros fiscales que Hacienda publica de cada municipio.

La «Consulta de información impositiva municipal» (Secretaría General de
Financiación Autonómica y Local, Ministerio de Hacienda) no solo publica los tipos
del IBI: también el tipo del ICIO, la tarifa completa del impuesto de circulación
(IVTM), los coeficientes y tipos de gravamen de la plusvalía municipal (IIVTNU) y
los coeficientes de situación del IAE.

Hasta ahora el sitio remitía a los «máximos legales» de la plusvalía porque no
teníamos los coeficientes reales de cada ayuntamiento. Están aquí, con fuente
oficial citable, ejercicio a ejercicio.

Salida: data/hacienda_impuestos.json
    { "22-048": { "municipio": ..., "ejercicio": "2025", "conceptos": {codigo: {...}} } }

Uso:
    python3 scripts/fetch_hacienda_impuestos.py                # los 134 municipios
    python3 scripts/fetch_hacienda_impuestos.py --solo 22-048  # uno concreto
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_hacienda_tipos import (  # noqa: E402
    LISTADO,
    build_opener,
    enter,
    get,
    hidden_fields,
    postback,
)

DATA = ROOT / "data" / "municipios.json"
SALIDA = ROOT / "data" / "hacienda_impuestos.json"
PREFIX = "ctl00$MainContentPlaceHolder$"

# Grupos tal y como los titula el formulario oficial.
GRUPOS = {
    "ibi": ["C02", "C03", "C04", "C05"],
    "iae": ["C06", "C07"],
    "icio": ["C17"],
    "ivtm_turismos": ["C18", "C19", "C20", "C21", "C22"],
    "ivtm_autobuses": ["C23", "C24", "C25"],
    "ivtm_camiones": ["C26", "C27", "C28", "C29"],
    "ivtm_tractores": ["C30", "C31", "C32"],
    "ivtm_remolques": ["C33", "C34", "C35"],
    "ivtm_otros": ["C36", "C37", "C38", "C39", "C40", "C41"],
    "plusvalia_coeficientes": [f"C{n}" for n in range(51, 72)],
    "plusvalia_tipos": [f"C{n}" for n in range(72, 93)],
    "plusvalia_reducciones": ["C12", "C93"],
}
ETIQUETAS_FIJAS = {
    "C12": "% de reducción del art. 107.3 TRLRHL sobre valores catastrales nuevos",
    "C93": "% de coeficiente reductor sobre el valor del terreno (art. 107.2.a TRLRHL)",
}
LABEL_RE = re.compile(
    r'<label for="MainContentPlaceHolder_(C\d+)"[^>]*>(.*?)</label>', re.S
)


def parse_todo(page: str) -> dict:
    limpio = htmllib.unescape(page)
    out: dict = {"conceptos": {}}

    muni = re.search(r"Municipio:\s*(?:<[^>]+>\s*)*([^<]+?)\s*-\s*Código", limpio)
    if muni:
        out["municipio"] = re.sub(r"\s+", " ", muni.group(1)).strip()
    cod = re.search(r"Código:\s*(?:<[^>]+>\s*)*(\d{2}-\d{3})", limpio)
    if cod:
        out["codigo_ine"] = cod.group(1)
    ej = re.search(r'id="MainContentPlaceHolder_LBL_ejer_act_BI_1"[^>]*>\s*(\d{4})', limpio)
    ej_ant = re.search(r'id="MainContentPlaceHolder_LBL_ejer_ant_BI_1"[^>]*>\s*(\d{4})', limpio)
    if ej:
        out["ejercicio"] = ej.group(1)
    if ej_ant:
        out["ejercicio_anterior"] = ej_ant.group(1)

    for m in LABEL_RE.finditer(limpio):
        codigo = m.group(1)
        etiqueta = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).strip()
        etiqueta = etiqueta or ETIQUETAS_FIJAS.get(codigo, "")
        actual = re.search(
            r'name="ctl00\$MainContentPlaceHolder\$' + codigo + r'"[^>]*value="([^"]*)"',
            limpio,
        )
        anterior = re.search(
            r'id="MainContentPlaceHolder_' + codigo + r'_ant"[^>]*>\s*([\d,.]*)', limpio
        )
        val = (actual.group(1) if actual else "").strip()
        ant = (anterior.group(1) if anterior else "").strip()
        if not val and not ant:
            continue
        out["conceptos"][codigo] = {
            "etiqueta": etiqueta,
            "valor": val or None,
            "valor_anterior": ant or None,
        }
    return out


def consulta(opener, provincia: str, municipio: str, ano: str) -> dict:
    page = enter(opener)
    page = postback(opener, page, PREFIX + "lbProvincias",
                    extra={PREFIX + "lbProvincias": provincia})
    fields = hidden_fields(page)
    fields.update({
        PREFIX + "lbProvincias": provincia,
        PREFIX + "lbMunicipios": municipio,
        PREFIX + "lbAno": ano,
        PREFIX + "Boton_aceptar": "Consulta web municipio",
    })
    page = get(opener, LISTADO, urllib.parse.urlencode(fields).encode(), LISTADO)
    return parse_todo(page)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", default="2025")
    ap.add_argument("--solo", default=None, help="código INE pp-mmm")
    ap.add_argument("--pausa", type=float, default=0.5)
    ap.add_argument("--reanudar", action="store_true",
                    help="salta los municipios que ya están descargados")
    args = ap.parse_args()

    municipios = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    objetivo = [m for m in municipios if m.get("oficial_codigo_ine")]
    if args.solo:
        objetivo = [m for m in objetivo if m["oficial_codigo_ine"] == args.solo]

    salida: dict[str, dict] = {}
    if SALIDA.exists() and not args.solo:
        salida = json.loads(SALIDA.read_text(encoding="utf-8"))

    opener = build_opener()
    ok = fail = 0
    for m in objetivo:
        codigo = m["oficial_codigo_ine"]
        if args.reanudar and salida.get(codigo, {}).get("conceptos"):
            continue
        prov, muni = codigo.split("-")
        try:
            datos = consulta(opener, prov, muni, args.ano)
        except Exception as exc:  # noqa: BLE001
            print(f"  [error] {m['nombre']} ({codigo}): {exc}")
            fail += 1
            continue
        if not datos.get("conceptos"):
            print(f"  [vacío] {m['nombre']} ({codigo})")
            fail += 1
            continue
        datos["slug"] = m["slug"]
        datos["nombre_sitio"] = m["nombre"]
        salida[codigo] = datos
        ok += 1
        n = len(datos["conceptos"])
        plus = sum(
            1 for c in datos["conceptos"] if c in GRUPOS["plusvalia_coeficientes"]
        )
        print(f"  {m['nombre']:28} {codigo}  conceptos={n:3d}  coef. plusvalía={plus}")
        time.sleep(args.pausa)

    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    print(f"\nDescargados: {ok}   fallidos: {fail}   → {SALIDA.relative_to(ROOT)}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
