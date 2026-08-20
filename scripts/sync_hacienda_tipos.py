#!/usr/bin/env python3
"""Sincroniza los tipos oficiales del IBI de los 134 municipios del sitio.

Fuente: «Consulta de informacion impositiva municipal» del Ministerio de Hacienda
(Secretaria General de Financiacion Autonomica y Local), que publica los tipos de
gravamen aprobados por cada ayuntamiento, ejercicio a ejercicio.

Que hace:
  1. Resuelve el codigo INE (provincia + municipio) de cada municipio del sitio
     contra el listado oficial, tolerando acentos y articulos pospuestos
     («Coruña, A» = «A Coruña»).
  2. Descarga los tipos del ejercicio indicado y del anterior.
  3. Guarda el resultado en data/hacienda_tipos.json (cache reanudable).
  4. Vuelca los datos oficiales en data/municipios.json y genera el informe
     data/DISCREPANCIAS_OFICIALES.md comparando lo publicado con lo oficial.

Uso:
    python3 scripts/sync_hacienda_tipos.py --ano 2025
    python3 scripts/sync_hacienda_tipos.py --ano 2025 --solo murcia
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import urllib.parse
from datetime import date
from pathlib import Path

import fetch_hacienda_tipos as hac  # mismo directorio

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
CACHE = ROOT / "data" / "hacienda_tipos.json"
INFORME = ROOT / "data" / "DISCREPANCIAS_OFICIALES.md"
PREFIX = "ctl00$MainContentPlaceHolder$"
FUENTE = (
    "https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/html/"
    "portadaconsultasm.aspx"
)
TODAY = date.today().isoformat()

# codigo INE de provincia por carpeta del sitio
PROVINCIAS = {
    "huesca": "22", "teruel": "44", "zaragoza": "50",
    "asturias": "33",
    "cantabria": "39",
    "albacete": "02", "ciudad-real": "13", "cuenca": "16", "guadalajara": "19", "toledo": "45",
    "avila": "05", "burgos": "09", "leon": "24", "palencia": "34", "salamanca": "37",
    "segovia": "40", "soria": "42", "valladolid": "47", "zamora": "49",
    "badajoz": "06", "caceres": "10",
    "a-coruna": "15", "lugo": "27", "ourense": "32", "pontevedra": "36",
    "la-rioja": "26",
    "murcia": "30",
}

ARTICULOS = ("El", "La", "Los", "Las", "A", "O", "As", "Os")


def normaliza(nombre: str) -> str:
    """Clave comparable: sin acentos, sin puntuacion y con el articulo delante.

    El listado oficial escribe el articulo pospuesto entre parentesis o tras coma
    («Coruña (A)», «Astillero (El)», «Carballiño (O)») y los nombres bilingues con
    barra («Gijón/Xixón»).
    """
    texto = nombre.strip()
    parentesis = re.match(r"^(.*?)\s*\((" + "|".join(ARTICULOS) + r")\)$", texto)
    if parentesis:
        texto = f"{parentesis.group(2)} {parentesis.group(1)}"
    elif "," in texto:
        cuerpo, _, articulo = texto.rpartition(",")
        if articulo.strip() in ARTICULOS:
            texto = f"{articulo.strip()} {cuerpo.strip()}"
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-z0-9/]+", " ", texto.lower())
    return " ".join(texto.split())


def claves(nombre: str) -> list[str]:
    """Todas las formas con las que puede aparecer un municipio.

    Incluye las variantes de los nombres bilingues separados por barra y la version
    sin articulo, para poder cruzar «Gijón/Xixón» con «Gijón» o «A Coruña» con
    «Coruña».
    """
    base = normaliza(nombre)
    salida = {base, base.replace("/", " ")}
    for parte in base.split("/"):
        parte = parte.strip()
        if parte:
            salida.add(parte)
    palabras = base.split()
    if palabras and palabras[0] in {a.lower() for a in ARTICULOS}:
        salida.add(" ".join(palabras[1:]))
    return [k for k in salida if k]


def listado_provincia(opener, page: str, provincia: str) -> tuple[str, dict[str, str]]:
    """Selecciona la provincia y devuelve (pagina, {clave normalizada: codigo})."""
    page = hac.postback(opener, page, PREFIX + "lbProvincias", extra={PREFIX + "lbProvincias": provincia})
    mapa: dict[str, str] = {}
    for codigo, texto in hac.options(page, "lbMunicipios"):
        nombre = re.sub(r"^\d+\s*", "", texto).strip()
        for clave in claves(nombre):
            mapa.setdefault(clave, codigo)
    return page, mapa


def consulta(opener, page: str, provincia: str, municipio: str, ano: str) -> dict:
    campos = hac.hidden_fields(page)
    campos.update({
        PREFIX + "lbProvincias": provincia,
        PREFIX + "lbMunicipios": municipio,
        PREFIX + "lbAno": ano,
        PREFIX + "Boton_aceptar": "Consulta web municipio",
    })
    resultado = hac.get(opener, hac.LISTADO, urllib.parse.urlencode(campos).encode(), hac.LISTADO)
    return hac.parse_resultado(resultado)


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", default="2025")
    ap.add_argument("--solo", help="limita a una comunidad autónoma (slug)")
    ap.add_argument("--pausa", type=float, default=0.4)
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    municipios = payload["municipios"]
    if args.solo:
        municipios = [m for m in municipios if m["ccaa"] == args.solo]

    cache: dict = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}

    por_provincia: dict[str, list[dict]] = {}
    for m in municipios:
        por_provincia.setdefault(m["provincia_slug"], []).append(m)

    opener = hac.build_opener()
    base = hac.enter(opener)
    resueltos = fallidos = 0

    for prov_slug, lista in sorted(por_provincia.items()):
        codigo_prov = PROVINCIAS.get(prov_slug)
        if not codigo_prov:
            print(f"[aviso] provincia sin código INE: {prov_slug}")
            continue
        page, mapa = listado_provincia(opener, base, codigo_prov)
        print(f"\n{prov_slug} ({codigo_prov}): {len(mapa)} municipios en el listado oficial")

        for m in sorted(lista, key=lambda x: x["nombre"]):
            clave_cache = f"{prov_slug}/{m['slug']}/{args.ano}"
            if clave_cache in cache:
                datos = cache[clave_cache]
            else:
                codigo_mun = None
                prov_real, page_real = codigo_prov, page
                for clave in claves(m["nombre"]) + claves(m["slug"].replace("-", " ")):
                    if clave in mapa:
                        codigo_mun = mapa[clave]
                        break
                if not codigo_mun:
                    # El municipio puede estar mal asignado de provincia en el sitio
                    # (p. ej. Lalín figura en Ourense y es de Pontevedra).
                    for otra_slug, otra_cod in PROVINCIAS.items():
                        if otra_cod == codigo_prov:
                            continue
                        page_otra, mapa_otra = listado_provincia(opener, base, otra_cod)
                        for clave in claves(m["nombre"]):
                            if clave in mapa_otra:
                                codigo_mun, prov_real, page_real = mapa_otra[clave], otra_cod, page_otra
                                print(
                                    f"  [provincia corregida] {m['nombre']}: el sitio lo sitúa en "
                                    f"{prov_slug} y es de {otra_slug}"
                                )
                                break
                        if codigo_mun:
                            break
                if not codigo_mun:
                    print(f"  [sin coincidencia] {m['nombre']}")
                    fallidos += 1
                    continue
                try:
                    datos = consulta(opener, page_real, prov_real, codigo_mun, args.ano)
                except Exception as exc:  # noqa: BLE001
                    print(f"  [error] {m['nombre']}: {type(exc).__name__}")
                    fallidos += 1
                    continue
                datos["codigo_provincia"] = prov_real
                datos["codigo_municipio"] = codigo_mun
                cache[clave_cache] = datos
                CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                time.sleep(args.pausa)

            oficial = datos.get("tipo_urbana")
            if not oficial:
                print(f"  [sin dato] {m['nombre']}")
                fallidos += 1
                continue
            resueltos += 1
            publicado = m.get("tipo_urbano")
            marca = "=" if publicado and abs(float(oficial) - publicado) < 1e-9 else "≠"
            print(
                f"  {marca} {m['nombre']:26} oficial {oficial:>8}%  publicado "
                f"{publicado if publicado is not None else '—'}%"
            )

    # volcado a la fuente de verdad
    for m in payload["municipios"]:
        datos = cache.get(f"{m['provincia_slug']}/{m['slug']}/{args.ano}")
        if not datos or not datos.get("tipo_urbana"):
            continue
        m["oficial_ejercicio"] = datos.get("ejercicio", args.ano)
        m["oficial_tipo_urbana"] = float(datos["tipo_urbana"])
        if datos.get("tipo_urbana_anterior"):
            m["oficial_tipo_urbana_anterior"] = float(datos["tipo_urbana_anterior"])
            m["oficial_ejercicio_anterior"] = datos.get("ejercicio_anterior")
        if datos.get("tipo_rustica"):
            m["oficial_tipo_rustica"] = float(datos["tipo_rustica"])
        if datos.get("tipo_bice"):
            m["oficial_tipo_bice"] = float(datos["tipo_bice"])
        if datos.get("ano_valores_catastrales"):
            m["oficial_ano_valores_catastrales"] = datos["ano_valores_catastrales"]
        m["oficial_codigo_ine"] = datos.get("codigo_ine", "")
        m["oficial_fuente"] = "Ministerio de Hacienda · Consulta de información impositiva municipal"
        m["oficial_fuente_url"] = FUENTE
        m["oficial_comprobado_el"] = TODAY

    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # informe de discrepancias
    con_oficial = [m for m in payload["municipios"] if m.get("oficial_tipo_urbana")]
    distintos = [
        m for m in con_oficial
        if m.get("tipo_urbano") and abs(m["oficial_tipo_urbana"] - m["tipo_urbano"]) > 1e-9
    ]
    distintos.sort(key=lambda m: -abs(m["oficial_tipo_urbana"] - m["tipo_urbano"]))

    lineas = [
        "# Tipos del IBI: lo publicado frente al dato oficial",
        "",
        "Generado por `scripts/sync_hacienda_tipos.py`.",
        "",
        f"- Municipios con dato oficial descargado: **{len(con_oficial)}** de {len(payload['municipios'])}",
        f"- Municipios cuyo tipo publicado **no coincide** con el oficial: **{len(distintos)}**",
        f"- Ejercicio oficial consultado: **{args.ano}** · fecha de consulta: {TODAY}",
        "",
        "Fuente: Ministerio de Hacienda, Consulta de información impositiva municipal "
        f"({FUENTE}).",
        "",
        "| Municipio | Publicado | Oficial | Diferencia | Cuota sobre 50.000 € (publicado → oficial) |",
        "|---|---|---|---|---|",
    ]
    for m in distintos:
        pub, ofi = m["tipo_urbano"], m["oficial_tipo_urbana"]
        lineas.append(
            f"| {m['nombre']} ({m['provincia'] or m['provincia_slug']}) | {pub:.4f}% | {ofi:.4f}% | "
            f"{ofi - pub:+.4f} pp | {50000 * pub / 100:.0f} € → {50000 * ofi / 100:.0f} € |"
        )
    coincidentes = [m for m in con_oficial if m not in distintos]
    if coincidentes:
        lineas += ["", "## Municipios en los que el dato publicado ya era correcto", ""]
        lineas += [f"- {m['nombre']} ({m['oficial_tipo_urbana']:.4f}%)" for m in coincidentes]
    INFORME.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(
        f"\nresueltos: {resueltos} · sin dato o sin coincidencia: {fallidos}\n"
        f"con dato oficial en data/municipios.json: {len(con_oficial)}\n"
        f"discrepancias documentadas en data/DISCREPANCIAS_OFICIALES.md: {len(distintos)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
