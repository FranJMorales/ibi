#!/usr/bin/env python3
"""Descarga la poblacion oficial de cada municipio desde el INE.

Fuente: operacion DPOP del INE, «Cifras Oficiales de Poblacion de los Municipios
Espanoles: Revision del Padron Municipal». Es la cifra con valor oficial, aprobada
por Real Decreto cada ano, y la que se cita en cualquier documento administrativo.

Por que importa:
  1. Las cifras que publicaba el sitio no venian de ninguna fuente citada y varias
     no coinciden (Molina de Segura: 72.654 publicado frente a 78.458 oficial).
  2. Search Console muestra cientos de impresiones sin un solo clic en consultas del
     tipo «habitantes {municipio} 2026»: el sitio aparece por las frases de contexto
     de las fichas pero no ofrece el dato.

Salida: data/municipios.json se enriquece con poblacion_oficial, su ejercicio, la
tabla del INE de la que sale y la fecha de comprobacion. Ademas se escribe el
informe data/DISCREPANCIAS_POBLACION.md.

Uso:  python3 scripts/sync_ine_poblacion.py
"""

from __future__ import annotations

import json
import re
import ssl
import time
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
INFORME = ROOT / "data" / "DISCREPANCIAS_POBLACION.md"
API = "https://servicios.ine.es/wstempus/js/ES"
TABLAS = f"{API}/TABLAS_OPERACION/DPOP"
TODAY = date.today().isoformat()

# Nombre de la provincia tal y como lo titula el INE, por carpeta del sitio.
PROVINCIAS_INE = {
    "a-coruna": "Coruña, A",
    "albacete": "Albacete",
    "asturias": "Asturias",
    "avila": "Ávila",
    "badajoz": "Badajoz",
    "burgos": "Burgos",
    "caceres": "Cáceres",
    "cantabria": "Cantabria",
    "ciudad-real": "Ciudad Real",
    "cuenca": "Cuenca",
    "guadalajara": "Guadalajara",
    "huesca": "Huesca",
    "la-rioja": "Rioja, La",
    "leon": "León",
    "lugo": "Lugo",
    "murcia": "Murcia",
    "ourense": "Ourense",
    "palencia": "Palencia",
    "pontevedra": "Pontevedra",
    "salamanca": "Salamanca",
    "segovia": "Segovia",
    "soria": "Soria",
    "teruel": "Teruel",
    "toledo": "Toledo",
    "valladolid": "Valladolid",
    "zamora": "Zamora",
    "zaragoza": "Zaragoza",
}

ARTICULOS = ("El", "La", "Los", "Las", "A", "O", "As", "Os")


def normaliza(nombre: str) -> str:
    texto = nombre.strip()
    parentesis = re.match(r"^(.*?)\s*\((" + "|".join(ARTICULOS) + r")\)$", texto)
    if parentesis:
        texto = f"{parentesis.group(2)} {parentesis.group(1)}"
    elif "," in texto:
        cuerpo, _, articulo = texto.rpartition(",")
        if articulo.strip() in ARTICULOS:
            texto = f"{articulo.strip()} {cuerpo.strip()}"
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9/]+", " ", texto.lower()).split())


def claves(nombre: str) -> list[str]:
    base = normaliza(nombre)
    salida = {base, base.replace("/", " ")}
    for parte in base.split("/"):
        if parte.strip():
            salida.add(parte.strip())
    palabras = base.split()
    if palabras and palabras[0] in {a.lower() for a in ARTICULOS}:
        salida.add(" ".join(palabras[1:]))
    return [k for k in salida if k]


def pide(url: str) -> list | dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "TasasMunicipales/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def tabla_por_provincia() -> dict[str, int]:
    """Localiza el id de la tabla «X: Población por municipios y sexo» de cada provincia."""
    tablas = pide(TABLAS)
    indice = {}
    for t in tablas:
        nombre = t.get("Nombre") or ""
        m = re.match(r"^(.*?):\s*Población por municipios y sexo", nombre)
        if m:
            indice[normaliza(m.group(1))] = t["Id"]
    return indice


def poblacion_de_tabla(tabla_id: int) -> tuple[dict[str, tuple[int, int]], str]:
    """Devuelve {clave municipio: (habitantes, año)} de la última revisión publicada."""
    series = pide(f"{API}/DATOS_TABLA/{tabla_id}?nult=1")
    salida: dict[str, tuple[int, int]] = {}
    for serie in series:
        nombre = serie.get("Nombre") or ""
        if ". Total. Total habitantes" not in nombre:
            continue
        municipio = nombre.split(". Total.")[0].strip()
        datos = serie.get("Data") or []
        if not datos:
            continue
        valor, ano = datos[0].get("Valor"), datos[0].get("Anyo")
        if valor is None:
            continue
        # La tabla empieza por el total provincial, que se llama igual que la capital
        # («Murcia. Total…» aparece dos veces). Nos quedamos con la ÚLTIMA aparición,
        # que es siempre la del municipio, no la del agregado provincial.
        for clave in claves(municipio):
            salida[clave] = (int(valor), int(ano))
    return salida, f"{API}/DATOS_TABLA/{tabla_id}"


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    municipios = payload["municipios"]

    print("Localizando las tablas provinciales del INE…")
    indice = tabla_por_provincia()
    print(f"  {len(indice)} tablas provinciales encontradas\n")

    por_provincia: dict[str, list[dict]] = {}
    for m in municipios:
        por_provincia.setdefault(m["provincia_slug"], []).append(m)

    resueltos = fallidos = 0
    for prov_slug, lista in sorted(por_provincia.items()):
        nombre_ine = PROVINCIAS_INE.get(prov_slug)
        tabla_id = indice.get(normaliza(nombre_ine or prov_slug))
        if not tabla_id:
            print(f"[aviso] sin tabla del INE para {prov_slug}")
            fallidos += len(lista)
            continue
        datos, fuente = poblacion_de_tabla(tabla_id)
        print(f"{prov_slug} (tabla {tabla_id}): {len(datos)} municipios en el INE")
        for m in sorted(lista, key=lambda x: x["nombre"]):
            encontrado = next((datos[c] for c in claves(m["nombre"]) if c in datos), None)
            if not encontrado:
                print(f"  [sin coincidencia] {m['nombre']}")
                fallidos += 1
                continue
            habitantes, ano = encontrado
            m["poblacion_oficial"] = habitantes
            m["poblacion_ejercicio"] = ano
            m["poblacion_fuente"] = (
                "INE · Cifras oficiales de población de los municipios españoles "
                "(revisión del padrón municipal)"
            )
            m["poblacion_fuente_url"] = "https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177011"
            m["poblacion_comprobada_el"] = TODAY
            resueltos += 1
            antigua = m.get("poblacion")
            marca = "=" if antigua == habitantes else "≠"
            print(f"  {marca} {m['nombre']:26} INE {ano}: {habitantes:>8,}".replace(",", ".")
                  + f"   publicado: {antigua if antigua else '—'}")
        time.sleep(0.3)

    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    con_dato = [m for m in municipios if m.get("poblacion_oficial")]
    distintos = [m for m in con_dato if m.get("poblacion") and m["poblacion"] != m["poblacion_oficial"]]
    distintos.sort(key=lambda m: -abs(m["poblacion_oficial"] - m["poblacion"]))

    lineas = [
        "# Población: lo publicado frente a la cifra oficial del INE",
        "",
        "Generado por `scripts/sync_ine_poblacion.py`.",
        "",
        f"- Municipios con cifra oficial descargada: **{len(con_dato)}** de {len(municipios)}",
        f"- Municipios cuya cifra publicada **no coincide** con la oficial: **{len(distintos)}**",
        f"- Fecha de consulta: {TODAY}",
        "",
        "Fuente: INE, Cifras oficiales de población de los municipios españoles "
        "(revisión del padrón municipal), operación DPOP.",
        "",
        "| Municipio | Publicado | Oficial INE | Diferencia |",
        "|---|---|---|---|",
    ]
    for m in distintos:
        dif = m["poblacion_oficial"] - m["poblacion"]
        lineas.append(
            f"| {m['nombre']} ({m.get('provincia') or m['provincia_slug']}) | "
            f"{m['poblacion']:,} | {m['poblacion_oficial']:,} | {dif:+,} |".replace(",", ".")
        )
    INFORME.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"\nresueltos: {resueltos} · sin dato: {fallidos}")
    print(f"discrepancias documentadas en data/DISCREPANCIAS_POBLACION.md: {len(distintos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
