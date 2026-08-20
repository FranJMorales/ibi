#!/usr/bin/env python3
"""Verifica y registra los enlaces oficiales de cada municipio y las fuentes legales.

Motivo: el sitio publicaba como «sede electrónica del Ayuntamiento» direcciones del
tipo https://{municipio}.sedelectronica.es que NO pertenecen a esos ayuntamientos.
Todas devuelven una pagina generica titulada «Sede Electronica Indeterminada».
Este script sustituye esos enlaces por la web oficial real de cada ayuntamiento,
comprueba con una peticion HTTP que responden y anota el codigo, el titulo de la
pagina y la fecha de comprobacion en data/municipios.json.

Uso:  python3 scripts/verify_official_links.py [--territorio murcia]
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
LEGAL = ROOT / "data" / "fuentes_legales.json"
TODAY = date.today().isoformat()

UA = "Mozilla/5.0 (compatible; TasasMunicipales/1.0; +https://tasasmunicipales.info)"

# Webs oficiales localizadas y comprobadas una por una.
OFICIALES: dict[str, dict[str, str]] = {
    "murcia/murcia/murcia": {
        "url": "https://amt.murcia.es",
        "nombre": "Agencia Municipal Tributaria de Murcia",
    },
    "murcia/murcia/cartagena": {
        "url": "https://www.cartagena.es",
        "nombre": "Ayuntamiento de Cartagena",
    },
    "murcia/murcia/lorca": {
        "url": "https://www.lorca.es",
        "nombre": "Ayuntamiento de Lorca",
    },
    "murcia/murcia/molina-de-segura": {
        "url": "https://portal.molinadesegura.es",
        "nombre": "Ayuntamiento de Molina de Segura",
    },
    "murcia/murcia/alcantarilla": {
        "url": "https://www.alcantarilla.es",
        "nombre": "Ayuntamiento de Alcantarilla",
    },
    "murcia/murcia/torre-pacheco": {
        "url": "https://sede.torrepacheco.es",
        "nombre": "Sede electrónica de Torre-Pacheco",
    },
    "murcia/murcia/mazarron": {
        "url": "https://www.mazarron.es",
        "nombre": "Ayuntamiento de Mazarrón",
    },
    "murcia/murcia/aguilas": {
        "url": "https://www.aguilas.es",
        "nombre": "Ayuntamiento de Águilas",
    },
    "murcia/murcia/cieza": {
        "url": "https://www.cieza.es",
        "nombre": "Ayuntamiento de Cieza",
    },
    "murcia/murcia/san-javier": {
        "url": "https://www.sanjavier.es",
        "nombre": "Ayuntamiento de San Javier",
    },
    "murcia/murcia/yecla": {
        "url": "https://www.yecla.es",
        "nombre": "Ayuntamiento de Yecla",
    },
    "murcia/murcia/totana": {
        "url": "https://www.totana.es",
        "nombre": "Ayuntamiento de Totana",
    },
    "murcia/murcia/san-pedro-del-pinatar": {
        "url": "https://www.sanpedrodelpinatar.es",
        "nombre": "Ayuntamiento de San Pedro del Pinatar",
    },
    "murcia/murcia/jumilla": {
        "url": "https://www.jumilla.org",
        "nombre": "Ayuntamiento de Jumilla",
    },
    "murcia/murcia/caravaca-de-la-cruz": {
        "url": "https://caravaca.sedipualba.es",
        "nombre": "Sede electrónica de Caravaca de la Cruz",
    },
    "murcia/murcia/alhama-de-murcia": {
        "url": "https://www.alhamademurcia.es",
        "nombre": "Ayuntamiento de Alhama de Murcia",
    },
    # Municipios con mas trafico organico fuera de Murcia (Search Console, 3 meses)
    "galicia/ourense/ourense": {"url": "https://www.ourense.gal", "nombre": "Concello de Ourense"},
    "castilla-la-mancha/toledo/talavera-de-la-reina": {
        "url": "https://www.talavera.org", "nombre": "Ayuntamiento de Talavera de la Reina",
    },
    "galicia/a-coruna/ferrol": {"url": "https://www.ferrol.gal", "nombre": "Concello de Ferrol"},
    "castilla-la-mancha/guadalajara/azuqueca-de-henares": {
        "url": "https://www.azuqueca.es", "nombre": "Ayuntamiento de Azuqueca de Henares",
    },
    "aragon/huesca/jaca": {"url": "https://www.jaca.es", "nombre": "Ayuntamiento de Jaca"},
    "extremadura/caceres/plasencia": {
        "url": "https://www.plasencia.es", "nombre": "Ayuntamiento de Plasencia",
    },
    "galicia/pontevedra/vilagarcia-de-arousa": {
        "url": "https://www.vilagarcia.gal", "nombre": "Concello de Vilagarcía de Arousa",
    },
    "castilla-la-mancha/toledo/sesena": {
        "url": "https://www.ayto-sesena.org", "nombre": "Ayuntamiento de Seseña",
    },
    "castilla-y-leon/segovia/segovia": {
        "url": "https://www.segovia.es", "nombre": "Ayuntamiento de Segovia",
    },
    "galicia/lugo/lugo": {"url": "https://www.lugo.gal", "nombre": "Concello de Lugo"},
    "asturias/asturias/gijon": {"url": "https://www.gijon.es", "nombre": "Ayuntamiento de Gijón"},
    "asturias/asturias/oviedo": {"url": "https://www.oviedo.es", "nombre": "Ayuntamiento de Oviedo"},
    "castilla-la-mancha/cuenca/cuenca": {
        "url": "https://www.cuenca.es", "nombre": "Ayuntamiento de Cuenca",
    },
    "castilla-la-mancha/ciudad-real/alcazar-de-san-juan": {
        "url": "https://alcazardesanjuan.es", "nombre": "Ayuntamiento de Alcázar de San Juan",
    },
    "castilla-y-leon/palencia/palencia": {
        "url": "https://www.aytopalencia.es", "nombre": "Ayuntamiento de Palencia",
    },
    "castilla-y-leon/avila/avila": {"url": "https://www.avila.es", "nombre": "Ayuntamiento de Ávila"},
    "asturias/asturias/siero": {
        "url": "https://www.ayto-siero.es", "nombre": "Ayuntamiento de Siero",
    },
    "asturias/asturias/aviles": {"url": "https://www.aviles.es", "nombre": "Ayuntamiento de Avilés"},
    # Tomelloso: 8.812 impresiones por consultas sobre su ordenanza de plusvalia
    "castilla-la-mancha/ciudad-real/tomelloso": {
        "url": "https://www.tomelloso.es", "nombre": "Ayuntamiento de Tomelloso",
    },
}

# Municipios cuya recaudacion de IBI gestiona la Agencia Tributaria de la Region de
# Murcia (ATRM). Segun el calendario del contribuyente publicado por la propia ATRM,
# Aguilas, Mazarron, Molina de Segura, Los Alcazares y San Pedro del Pinatar tienen
# calendario propio.
CALENDARIO_PROPIO = {
    "murcia/murcia/aguilas",
    "murcia/murcia/mazarron",
    "murcia/murcia/molina-de-segura",
    "murcia/murcia/san-pedro-del-pinatar",
}

# Organismo que presta el servicio de gestion y recaudacion a los ayuntamientos de
# cada provincia. Es donde se publica el calendario de cobro de la mayoria de
# municipios (los ayuntamientos grandes suelen gestionarlo ellos mismos).
RECAUDADORES: dict[str, dict[str, str]] = {
    "a-coruna": {"nombre": "Deputación da Coruña", "url": "https://www.dacoruna.gal"},
    "lugo": {"nombre": "Deputación de Lugo", "url": "https://www.deputacionlugo.gal"},
    "ourense": {"nombre": "Deputación Provincial de Ourense", "url": "https://www.depourense.gal"},
    "pontevedra": {"nombre": "Deputación de Pontevedra", "url": "https://www.depo.gal"},
    "huesca": {"nombre": "Diputación Provincial de Huesca", "url": "https://www.dphuesca.es"},
    "teruel": {"nombre": "Diputación Provincial de Teruel", "url": "https://www.dpteruel.es"},
    "zaragoza": {"nombre": "Diputación Provincial de Zaragoza", "url": "https://www.dpz.es"},
    "albacete": {"nombre": "Diputación de Albacete", "url": "https://www.dipualba.es"},
    "ciudad-real": {"nombre": "Diputación Provincial de Ciudad Real", "url": "https://www.dipucr.es"},
    "cuenca": {"nombre": "Diputación Provincial de Cuenca", "url": "https://www.dipucuenca.es"},
    "guadalajara": {"nombre": "Diputación de Guadalajara", "url": "https://www.dguadalajara.es"},
    "toledo": {
        "nombre": "Organismo Autónomo Provincial de Gestión Tributaria de Toledo (OAPGT)",
        "url": "https://www.oapgt.es",
    },
    "avila": {"nombre": "Diputación de Ávila", "url": "https://www.diputacionavila.es"},
    "burgos": {"nombre": "Diputación Provincial de Burgos", "url": "https://www.burgos.es"},
    "leon": {"nombre": "Diputación de León", "url": "https://www.dipuleon.es"},
    "palencia": {"nombre": "Diputación de Palencia", "url": "https://www.diputaciondepalencia.es"},
    "salamanca": {
        "nombre": "REGTSA, Organismo Autónomo de Recaudación de la Diputación de Salamanca",
        "url": "https://www.regtsa.es",
    },
    "segovia": {"nombre": "Diputación de Segovia", "url": "https://www.dipsegovia.es"},
    "soria": {"nombre": "Diputación Provincial de Soria", "url": "https://www.dipsoria.es"},
    "valladolid": {
        "nombre": "Diputación de Valladolid", "url": "https://www.diputaciondevalladolid.es",
    },
    "zamora": {"nombre": "Diputación de Zamora", "url": "https://www.diputaciondezamora.es"},
    "badajoz": {
        "nombre": "OAR, Organismo Autónomo de Recaudación de la Diputación de Badajoz",
        "url": "https://oar.dip-badajoz.es",
    },
    "caceres": {"nombre": "Diputación de Cáceres", "url": "https://www.dip-caceres.es"},
    "asturias": {
        "nombre": "Servicios Tributarios del Principado de Asturias",
        "url": "https://www.tributasenasturias.es",
    },
    "murcia": {
        "nombre": "Agencia Tributaria de la Región de Murcia (ATRM)",
        "url": "https://agenciatributaria.carm.es/calendario-del-contribuyente",
    },
    "la-rioja": {"nombre": "Gobierno de La Rioja", "url": "https://www.larioja.org"},
    "cantabria": {"nombre": "", "url": ""},  # sin organismo provincial: cada ayuntamiento
}

FUENTES_LEGALES = [
    {
        "clave": "trlrhl",
        "titulo": "Real Decreto Legislativo 2/2004 (texto refundido de la Ley Reguladora de las Haciendas Locales)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214",
    },
    {
        "clave": "trlci",
        "titulo": "Real Decreto Legislativo 1/2004 (texto refundido de la Ley del Catastro Inmobiliario)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4163",
    },
    {
        "clave": "ley_residuos",
        "titulo": "Ley 7/2022, de 8 de abril, de residuos y suelos contaminados para una economía circular",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5809",
    },
    {
        "clave": "rdl_plusvalia",
        "titulo": "Real Decreto-ley 26/2021, de 8 de noviembre (adaptación del IIVTNU a la jurisprudencia constitucional)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2021-18276",
    },
    {
        "clave": "stc_182_2021",
        "titulo": "Sentencia del Tribunal Constitucional 182/2021, de 26 de octubre",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2021-19511",
    },
    {
        "clave": "lgt",
        "titulo": "Ley 58/2003, de 17 de diciembre, General Tributaria",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186",
    },
    {
        "clave": "catastro",
        "titulo": "Sede Electrónica del Catastro",
        "url": "https://www.sedecatastro.gob.es",
    },
]


def check(url: str) -> tuple[int, str]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as resp:
            body = resp.read(60000).decode("utf-8", errors="ignore")
            title = re.search(r"<title[^>]*>([^<]*)", body, re.I)
            return resp.status, re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception as exc:  # noqa: BLE001
        return 0, type(exc).__name__


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territorio", default="murcia")
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    ok = fail = 0

    for m in payload["municipios"]:
        key = f"{m['ccaa']}/{m['provincia_slug']}/{m['slug']}"
        entry = OFICIALES.get(key)
        if not entry:
            continue
        status, title = check(entry["url"])
        m["web_oficial"] = entry["url"]
        m["web_oficial_nombre"] = entry["nombre"]
        m["web_http_status"] = status
        m["web_titulo_detectado"] = title
        m["web_comprobada_el"] = TODAY
        if m["ccaa"] == "murcia":
            m["recaudacion"] = (
                "Calendario de cobro propio del ayuntamiento"
                if key in CALENDARIO_PROPIO
                else "Recaudación integrada en el calendario de la Agencia Tributaria de la Región de Murcia"
            )
        # El enlace anterior (…​.sedelectronica.es) no pertenecia al ayuntamiento.
        m["sede_descartada"] = m.pop("sede", "")
        state = "OK " if status == 200 else "REV"
        print(f"  {state} {status:3d}  {m['nombre']:24} {entry['url']}  {title[:45]}")
        ok += status == 200
        fail += status != 200

    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # organismos de recaudacion por provincia
    recaudadores = {}
    for prov, datos in RECAUDADORES.items():
        if not datos["url"]:
            recaudadores[prov] = {**datos, "http_status": None, "comprobado_el": TODAY}
            print(f"  --  ---  {prov}: sin organismo provincial (gestión municipal)")
            continue
        status, title = check(datos["url"])
        recaudadores[prov] = {
            **datos, "http_status": status, "titulo_detectado": title, "comprobado_el": TODAY,
        }
        print(f"  {'OK ' if status == 200 else 'REV'} {status:3d}  {prov}: {datos['nombre'][:44]}")
    (ROOT / "data" / "recaudadores.json").write_text(
        json.dumps({"provincias": recaudadores, "comprobados_el": TODAY}, ensure_ascii=False, indent=1)
        + "\n",
        encoding="utf-8",
    )

    legal = []
    for src in FUENTES_LEGALES:
        status, title = check(src["url"])
        legal.append({**src, "http_status": status, "comprobada_el": TODAY})
        print(f"  {'OK ' if status == 200 else 'REV'} {status:3d}  {src['clave']}")
    LEGAL.write_text(
        json.dumps({"fuentes": legal, "comprobadas_el": TODAY}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    print(f"\nwebs municipales: {ok} responden 200, {fail} requieren revisión")
    print(f"fuentes legales comprobadas: {sum(1 for f in legal if f['http_status'] == 200)}/{len(legal)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
