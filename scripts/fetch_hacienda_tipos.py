#!/usr/bin/env python3
"""Descarga los tipos de gravamen del IBI publicados por el Ministerio de Hacienda.

Fuente oficial: «Consulta de informacion impositiva municipal» de la Secretaria
General de Financiacion Autonomica y Local (Ministerio de Hacienda), accesible
desde https://sede.hacienda.gob.es (procedimiento «Entidades Locales. Tipos de
gravamen, indices y coeficientes»).

Es la unica fuente que publica, municipio a municipio y ejercicio a ejercicio, los
tipos aprobados en las ordenanzas fiscales. Sirve para contrastar los datos del
sitio sin depender de citas de boletin no verificables.

Uso:
    python3 scripts/fetch_hacienda_tipos.py --explorar
    python3 scripts/fetch_hacienda_tipos.py --provincia 30 --municipio 030 --ano 2025
"""

from __future__ import annotations

import argparse
import html as htmllib
import http.cookiejar
import re
import ssl
import urllib.parse
import urllib.request

BASE = "https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos"
PORTADA = f"{BASE}/html/portadaconsultasm.aspx"
LISTADO = f"{BASE}/aspx/listado_municipiosm.aspx"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def build_opener() -> urllib.request.OpenerDirector:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
    )


def get(opener, url: str, data: bytes | None = None, referer: str = "") -> str:
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers)
    with opener.open(req, timeout=40) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def hidden_fields(page: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for tag in re.findall(r"<input[^>]*type=\"hidden\"[^>]*>", page):
        name = re.search(r'name="([^"]+)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if name:
            fields[name.group(1)] = htmllib.unescape(value.group(1)) if value else ""
    return fields


def enter(opener) -> str:
    page = get(opener, PORTADA)
    fields = hidden_fields(page)
    fields["ctl00$MainContentPlaceHolder$BT_entrar"] = "Entrar"
    try:
        get(opener, PORTADA, urllib.parse.urlencode(fields).encode(), PORTADA)
    except urllib.error.HTTPError:
        pass
    return get(opener, LISTADO, referer=PORTADA)


def options(page: str, name_fragment: str) -> list[tuple[str, str]]:
    sel = re.search(
        r'<select[^>]*name="[^"]*' + name_fragment + r'"[^>]*>(.*?)</select>', page, re.S
    )
    if not sel:
        return []
    return [
        (v, re.sub(r"\s+", " ", htmllib.unescape(t)).strip())
        for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', sel.group(1))
    ]


def postback(opener, page: str, target: str, argument: str = "", extra: dict | None = None) -> str:
    fields = hidden_fields(page)
    fields["__EVENTTARGET"] = target
    fields["__EVENTARGUMENT"] = argument
    for sel_name in re.findall(r'<select[^>]*name="([^"]+)"', page):
        opts = re.findall(
            r'<option[^>]*selected[^>]*value="([^"]*)"',
            re.search(r'<select[^>]*name="' + re.escape(sel_name) + r'"[^>]*>(.*?)</select>', page, re.S).group(1),
        )
        if opts:
            fields[sel_name] = opts[0]
    if extra:
        fields.update(extra)
    return get(opener, LISTADO, urllib.parse.urlencode(fields).encode(), LISTADO)


def explore() -> None:
    opener = build_opener()
    page = enter(opener)
    print("título:", (re.search(r"<title>([^<]*)", page) or ["", ""])[1])
    for frag in ("lbProvincias", "lbMunicipios", "lbAno"):
        opts = options(page, frag)
        print(f"\n{frag}: {len(opts)} opciones")
        print("   primeras:", opts[:4])
        print("   últimas :", opts[-4:])
    print("\ncontroles no ocultos:")
    for tag in re.findall(r"<input[^>]*>", page):
        if "hidden" not in tag:
            print("  ", re.sub(r"\s+", " ", tag)[:150])
    print("\npostbacks declarados:")
    for target in sorted({t for t in re.findall(r"__doPostBack\('([^']+)'", page)}):
        print("  ", target)
    print("\nenlaces:")
    for href in sorted({h for h in re.findall(r'href="([^"]{4,90})"', page)}):
        print("  ", href)


def consulta(provincia: str, municipio: str, ano: str) -> None:
    opener = build_opener()
    page = enter(opener)
    prefix = "ctl00$MainContentPlaceHolder$"
    extra = {
        prefix + "lbProvincias": provincia,
        prefix + "lbMunicipios": municipio,
        prefix + "lbAno": ano,
    }
    # 1) seleccionar provincia (recarga el listado de municipios)
    page = postback(opener, page, prefix + "lbProvincias", extra={prefix + "lbProvincias": provincia})
    munis = options(page, "lbMunicipios")
    print(f"municipios de la provincia {provincia}: {len(munis)}")
    elegido = next((m for m in munis if m[0] == municipio), None)
    print("municipio seleccionado:", elegido)
    # 2) pulsar «Consulta web municipio»
    fields = hidden_fields(page)
    fields.update(extra)
    fields[prefix + "Boton_aceptar"] = "Consulta web municipio"
    page = get(opener, LISTADO, urllib.parse.urlencode(fields).encode(), LISTADO)

    datos = parse_resultado(page)
    print("\n--- datos oficiales ---")
    for k, v in datos.items():
        print(f"  {k:52} {v}")


CONCEPTOS = {
    "tipo de gravamen urbana": "tipo_urbana",
    "tipo de gravamen rústica": "tipo_rustica",
    "tipo de gravamen de características especiales": "tipo_bice",
    "año de entrada en vigor de valores catastrales": "ano_valores_catastrales",
}


def parse_resultado(page: str) -> dict[str, str]:
    """Extrae los conceptos del formulario de resultado.

    Cada concepto se identifica con un codigo (C02, C03, C43...). El valor del
    ejercicio consultado esta en el <input name="...$Cxx"> y el del ejercicio
    anterior en el <span id="MainContentPlaceHolder_Cxx_ant">.
    """
    out: dict[str, str] = {}
    limpio = htmllib.unescape(page)

    muni = re.search(r'id="MainContentPlaceHolder_LBL_municipio"[^>]*>\s*([^<]+)', limpio)
    if not muni:
        muni = re.search(r"Municipio:.*?<span[^>]*>\s*([^<]+)", limpio, re.S)
    if muni:
        out["municipio"] = re.sub(r"\s+", " ", muni.group(1)).strip()
    cod = re.search(r"Código:.*?(\d{2}-\d{3})", limpio, re.S)
    if cod:
        out["codigo_ine"] = cod.group(1)

    ejer_act = re.search(r'id="MainContentPlaceHolder_LBL_ejer_act_BI_1"[^>]*>\s*(\d{4})', limpio)
    ejer_ant = re.search(r'id="MainContentPlaceHolder_LBL_ejer_ant_BI_1"[^>]*>\s*(\d{4})', limpio)
    if ejer_act:
        out["ejercicio"] = ejer_act.group(1)
    if ejer_ant:
        out["ejercicio_anterior"] = ejer_ant.group(1)

    for match in re.finditer(
        r'<label for="MainContentPlaceHolder_(C\d+)"[^>]*>\s*(.*?)\s*</label>', limpio, re.S
    ):
        codigo, etiqueta = match.group(1), re.sub(r"\s+", " ", match.group(2)).strip()
        clave = next((v for k, v in CONCEPTOS.items() if k in etiqueta.lower()), None)
        if not clave:
            continue
        actual = re.search(
            r'name="ctl00\$MainContentPlaceHolder\$' + codigo + r'"[^>]*value="([^"]*)"', limpio
        )
        anterior = re.search(
            r'id="MainContentPlaceHolder_' + codigo + r'_ant"[^>]*>\s*([\d,.]+)', limpio
        )
        if actual and actual.group(1).strip():
            out[clave] = actual.group(1).strip().replace(",", ".")
        if anterior:
            out[clave + "_anterior"] = anterior.group(1).replace(",", ".")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--explorar", action="store_true")
    ap.add_argument("--provincia")
    ap.add_argument("--municipio")
    ap.add_argument("--ano", default="2025")
    args = ap.parse_args()
    if args.explorar or not (args.provincia and args.municipio):
        explore()
    else:
        consulta(args.provincia, args.municipio, args.ano)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
