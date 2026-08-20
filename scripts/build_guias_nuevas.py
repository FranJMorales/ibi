#!/usr/bin/env python3
"""Genera las dos guias nacionales que faltaban, con datos oficiales y graficos propios.

  /impuesto-circulacion/  el IVTM: cuotas minimas del art. 95.1 TRLRHL, el
                          coeficiente municipal (tope 2), exenciones,
                          bonificaciones, prorrateo y lo que cobra realmente cada
                          uno de los 134 municipios.
  /valor-catastral/       que es, como se consulta, en que se diferencia del valor
                          de referencia, como llega al recibo del IBI a traves de
                          la base liquidable, cada cuanto se revisa y como se
                          corrige.

Toda afirmacion normativa lleva su articulo y su enlace al BOE. Las cifras
municipales salen de data/hacienda_impuestos.json y data/municipios.json, que es
lo que ya publican las fichas, los pilares y el comparador.

Los graficos son SVG propios generados aqui: texto real indexable, unos pocos kB y
sin dependencias externas.

Uso:  python3 scripts/build_guias_nuevas.py
"""
from __future__ import annotations

import html
import json
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_territory_pillars as tp  # noqa: E402

SITE = "https://tasasmunicipales.info"
TODAY = date.today().isoformat()
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")
HOY_ES = f"{date.today().day} {MESES[date.today().month - 1]} {date.today().year}"
ANO = date.today().year
PREFIX = "../"
TRLRHL = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214"
TRLCI = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4163"
LGT = "https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186"
CATASTRO = "https://www.sedecatastro.gob.es"
HACIENDA = ("https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/"
            "html/portadaconsultasm.aspx")

# Cuadro de tarifas del art. 95.1 TRLRHL (cuotas minimas, en euros).
TARIFA_LEGAL = [
    ("Turismos", [
        ("C18", "De menos de 8 caballos fiscales", 12.62),
        ("C19", "De 8 a 11,99 caballos fiscales", 34.08),
        ("C20", "De 12 a 15,99 caballos fiscales", 71.94),
        ("C21", "De 16 a 19,99 caballos fiscales", 89.61),
        ("C22", "De 20 caballos fiscales en adelante", 112.00),
    ]),
    ("Motocicletas y ciclomotores", [
        ("C36", "Ciclomotores", 4.42),
        ("C37", "Motocicletas hasta 125 cc", 4.42),
        ("C38", "Motocicletas de más de 125 hasta 250 cc", 7.57),
        ("C39", "Motocicletas de más de 250 hasta 500 cc", 15.15),
        ("C40", "Motocicletas de más de 500 hasta 1.000 cc", 30.29),
        ("C41", "Motocicletas de más de 1.000 cc", 60.58),
    ]),
    ("Camiones", [
        ("C26", "De menos de 1.000 kg de carga útil", 42.28),
        ("C27", "De 1.000 a 2.999 kg", 83.30),
        ("C28", "De más de 2.999 a 9.999 kg", 118.64),
        ("C29", "De más de 9.999 kg", 148.30),
    ]),
    ("Autobuses", [
        ("C23", "De menos de 21 plazas", 83.30),
        ("C24", "De 21 a 50 plazas", 118.64),
        ("C25", "De más de 50 plazas", 148.30),
    ]),
    ("Tractores", [
        ("C30", "De menos de 16 caballos fiscales", 17.67),
        ("C31", "De 16 a 25 caballos fiscales", 27.77),
        ("C32", "De más de 25 caballos fiscales", 83.30),
    ]),
    ("Remolques y semirremolques", [
        ("C33", "De más de 750 y menos de 1.000 kg de carga útil", 17.67),
        ("C34", "De 1.000 a 2.999 kg", 27.77),
        ("C35", "De más de 2.999 kg", 83.30),
    ]),
]

INK, ACCENT, ACCENT2 = "#1a1a2e", "#c8522a", "#2a7c6f"
PAPER, RULE, MID, CARD = "#f5f0e8", "#d8d0c0", "#6b6b7b", "#fffdf8"
FONT = "Georgia, 'Source Serif 4', serif"


# ─────────────────────────────── utilidades ────────────────────────────────

def datos() -> list[dict]:
    return json.loads((ROOT / "data" / "municipios.json").read_text(encoding="utf-8"))["municipios"]


def impuestos() -> dict:
    ruta = ROOT / "data" / "hacienda_impuestos.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def valor(imp: dict | None, codigo: str) -> float | None:
    if not imp:
        return None
    bruto = ((imp.get("conceptos") or {}).get(codigo) or {}).get("valor")
    if bruto in (None, "", "-"):
        return None
    try:
        return float(str(bruto).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def num(v: float, dec: int = 2) -> str:
    return f"{v:,.{dec}f}".replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def eur(v: float, dec: int = 2) -> str:
    return num(v, dec) + " €"


def pct(v: float) -> str:
    return f"{round(v, 4):g}".replace(".", ",") + "%"


def ficha(m: dict) -> str:
    return f"{PREFIX}{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"


def enlace(m: dict) -> str:
    return f'<a href="{ficha(m)}">{html.escape(m["nombre"])}</a>'


def figura(src: str, alt: str, pie: str, w: int, h: int, lazy: bool = True) -> str:
    carga = ' loading="lazy" decoding="async"' if lazy else ""
    return (
        f'    <figure class="infographic">\n'
        f'      <img src="{PREFIX}img/{src}" alt="{html.escape(alt)}" '
        f'width="{w}" height="{h}"{carga}>\n'
        f"      <figcaption>{pie}</figcaption>\n    </figure>"
    )


def pagina(slug: str, tag: str, title: str, description: str, h1: str, minutos: int,
           toc: list[tuple[str, str]], cuerpo: str, faq: list[tuple[str, str]],
           aside: str) -> None:
    canonical = f"{SITE}/{slug}/"
    indice = "\n".join(
        f'      <li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in toc
    )
    faq_html = "\n".join(
        f'    <div class="fi"><div class="fq">❓ {html.escape(q)}</div>'
        f'<div class="fa">{a}</div></div>'
        for q, a in faq
    )
    schema_art = {
        "@context": "https://schema.org", "@type": "Article", "headline": title,
        "description": description, "datePublished": TODAY, "dateModified": TODAY,
        "author": {"@type": "Person", "name": "Aithamy Rivero"},
        "publisher": {"@type": "Organization", "name": "TasasMunicipales.info",
                      "url": SITE},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "inLanguage": "es",
    }
    schema_faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer",
                                "text": tp.strip_tags(a)}}
            for q, a in faq
        ],
    }
    schema_bc = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": h1, "item": canonical},
        ],
    }
    bloques = "\n".join(
        '  <script type="application/ld+json">\n  '
        + json.dumps(s, ensure_ascii=False) + "\n  </script>"
        for s in (schema_art, schema_faq, schema_bc)
    )
    doc = (
        tp.head_block(title, description, canonical, PREFIX)
        + f'<div class="bc"><a href="{PREFIX}">Inicio</a><span>›</span>'
          f'<strong>{html.escape(h1.split(":")[0])}</strong></div>\n'
        + '<div class="wrap">\n<div class="al">\n<main>\n'
        + f'  <span class="tag t-r">{html.escape(tag)}</span>\n'
        + f"  <h1>{h1}</h1>\n"
        + f'  <p style="font-size:.77rem;color:var(--mid);margin-bottom:22px;">'
          f'Por Aithamy Rivero · Actualizado: {HOY_ES} · {minutos} min de lectura · '
          f'<a href="{PREFIX}metodologia/" style="color:var(--accent)">Metodología</a></p>\n'
        + '  <div class="toc">\n    <div class="toc-h">Contenido</div>\n    <ol>\n'
        + indice + "\n    </ol>\n  </div>\n\n  <article>\n"
        + cuerpo
        + '\n    <h2 id="faq">Preguntas frecuentes</h2>\n'
        + faq_html
        + "\n  </article>\n"
        + bloques
        + "\n</main>\n"
        + aside
        + "\n</div>\n</div>\n"
        + tp.footer_block(PREFIX)
    )
    destino = ROOT / slug / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(doc, encoding="utf-8")
    palabras = len(tp.strip_tags(doc.split("<footer>")[0]).split())
    print(f"  /{slug}/  ({palabras} palabras)")


# ──────────────────────────────── gráficos ─────────────────────────────────

def svg_flujo_ivtm() -> str:
    """Esquema de como se llega a la cuota del IVTM."""
    w, h = 900, 340
    cajas = [
        (30, "Clase y potencia\ndel vehículo", "Ficha técnica"),
        (250, "Cuota mínima\nlegal", "Art. 95.1 TRLRHL"),
        (470, "× coeficiente\nmunicipal (máx. 2)", "Art. 95.4 TRLRHL"),
        (690, "Cuota a pagar\n− bonificaciones", "Art. 95.6 TRLRHL"),
    ]
    piezas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" '
        f'aria-labelledby="t-ivtm d-ivtm">',
        '<title id="t-ivtm">Cómo se calcula el impuesto de circulación</title>',
        '<desc id="d-ivtm">La clase y la potencia del vehículo determinan la cuota '
        'mínima que fija el artículo 95.1 del TRLRHL. El ayuntamiento puede '
        'multiplicarla por un coeficiente que no puede pasar de 2, y sobre el '
        'resultado se aplican las bonificaciones de su ordenanza.</desc>',
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="30" y="46" font-family="{FONT}" font-size="21" font-weight="bold" '
        f'fill="{INK}">Del vehículo a la cuota: cómo se calcula el IVTM</text>',
    ]
    for x, titulo, pie in cajas:
        piezas.append(f'<rect x="{x}" y="90" width="180" height="118" rx="6" '
                      f'fill="{CARD}" stroke="{RULE}" stroke-width="1.5"/>')
        for i, linea in enumerate(titulo.split("\n")):
            piezas.append(f'<text x="{x + 90}" y="{130 + i * 24}" '
                          f'font-family="{FONT}" font-size="15" font-weight="bold" '
                          f'text-anchor="middle" fill="{INK}">{linea}</text>')
        piezas.append(f'<text x="{x + 90}" y="188" font-family="{FONT}" '
                      f'font-size="11.5" text-anchor="middle" fill="{MID}">{pie}</text>')
        if x < 690:
            piezas.append(f'<path d="M{x + 188} 149 L{x + 240} 149" stroke="{ACCENT}" '
                          f'stroke-width="2.5" marker-end="url(#f)"/>')
    piezas.insert(4, '<defs><marker id="f" markerWidth="9" markerHeight="9" refX="7" '
                     f'refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 z" '
                     f'fill="{ACCENT}"/></marker></defs>')
    piezas.append(
        f'<text x="30" y="256" font-family="{FONT}" font-size="13.5" fill="{INK}">'
        f'Ejemplo: turismo de 10 caballos fiscales → cuota mínima 34,08 € × '
        f'coeficiente 2 = 68,16 € al año.</text>')
    piezas.append(
        f'<text x="30" y="284" font-family="{FONT}" font-size="12.5" fill="{MID}">'
        f'El coeficiente puede ser distinto para cada clase de vehículo y para cada '
        f'tramo dentro de la clase.</text>')
    piezas.append(
        f'<text x="30" y="316" font-family="{FONT}" font-size="11.5" fill="{MID}">'
        f'Fuente: artículo 95 del texto refundido de la Ley Reguladora de las '
        f'Haciendas Locales · TasasMunicipales.info</text>')
    piezas.append("</svg>")
    return "\n".join(piezas)


def svg_ivtm_turismos(tarifas: list[tuple[float, dict]]) -> str:
    """Reparto de la cuota del turismo mas comun entre los 134 municipios."""
    minimo = 34.08
    tramos = [(minimo, minimo * 1.2), (minimo * 1.2, minimo * 1.4),
              (minimo * 1.4, minimo * 1.6), (minimo * 1.6, minimo * 1.8),
              (minimo * 1.8, minimo * 2.001)]
    etiquetas = ["Coef. 1,0–1,2", "1,2–1,4", "1,4–1,6", "1,6–1,8", "1,8–2,0"]
    cuentas = []
    for desde, hasta in tramos:
        cuentas.append(sum(1 for v, _ in tarifas if desde <= v < hasta))
    total = sum(cuentas) or 1
    w, h = 900, 400
    top = max(cuentas) or 1
    ancho, hueco, base, alto_max = 120, 40, 300, 170
    piezas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-labelledby="t-tur d-tur">',
        '<title id="t-tur">Coeficiente que aplican los municipios al IVTM de un '
        'turismo de 8 a 11,99 caballos fiscales</title>',
        f'<desc id="d-tur">De los {total} municipios analizados, '
        + ", ".join(f"{c} están en el tramo {e}" for c, e in zip(cuentas, etiquetas))
        + ". El coeficiente máximo que permite la ley es 2.</desc>",
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="30" y="44" font-family="{FONT}" font-size="20" font-weight="bold" '
        f'fill="{INK}">Cuánto multiplican los ayuntamientos la cuota mínima</text>',
        f'<text x="30" y="68" font-family="{FONT}" font-size="13" fill="{MID}">'
        f'Turismo de 8 a 11,99 CV fiscales · cuota mínima legal 34,08 € · '
        f'{total} municipios</text>',
    ]
    for i, (c, etq) in enumerate(zip(cuentas, etiquetas)):
        x = 40 + i * (ancho + hueco)
        altura = max(4, alto_max * c / top)
        y = base - altura
        piezas.append(f'<rect x="{x}" y="{y}" width="{ancho}" height="{altura}" '
                      f'rx="3" fill="{ACCENT if i >= 3 else ACCENT2}"/>')
        piezas.append(f'<text x="{x + ancho / 2}" y="{y - 10}" font-family="{FONT}" '
                      f'font-size="16" font-weight="bold" text-anchor="middle" '
                      f'fill="{INK}">{c}</text>')
        piezas.append(f'<text x="{x + ancho / 2}" y="{base + 24}" '
                      f'font-family="{FONT}" font-size="13" text-anchor="middle" '
                      f'fill="{INK}">{etq}</text>')
        piezas.append(f'<text x="{x + ancho / 2}" y="{base + 44}" '
                      f'font-family="{FONT}" font-size="11.5" text-anchor="middle" '
                      f'fill="{MID}">{num(100 * c / total, 1)}%</text>')
    piezas.append(f'<line x1="30" y1="{base}" x2="{w - 30}" y2="{base}" '
                  f'stroke="{RULE}" stroke-width="1.5"/>')
    piezas.append(f'<text x="30" y="{base + 78}" font-family="{FONT}" font-size="12.5" '
                  f'fill="{MID}">Fuente: Ministerio de Hacienda, consulta de '
                  f'información impositiva municipal · TasasMunicipales.info</text>')
    piezas.append("</svg>")
    return "\n".join(piezas)


def svg_flujo_catastro() -> str:
    w, h = 900, 360
    pasos = [
        ("Valor del suelo", "+"),
        ("Valor de la\nconstrucción", "="),
        ("Valor catastral\n= base imponible", "−"),
        ("Reducción\n(9 años)", "="),
        ("Base liquidable\n× tipo", ""),
    ]
    piezas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-labelledby="t-vc d-vc">',
        '<title id="t-vc">Del valor catastral a la cuota del IBI</title>',
        '<desc id="d-vc">El valor catastral suma el valor del suelo y el de la '
        'construcción y es la base imponible del IBI. Cuando sube por una '
        'valoración colectiva se le resta una reducción que dura nueve años y '
        'decrece 0,1 cada ejercicio; el resultado es la base liquidable, sobre la '
        'que se aplica el tipo de gravamen municipal.</desc>',
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="30" y="44" font-family="{FONT}" font-size="21" font-weight="bold" '
        f'fill="{INK}">Del valor catastral al importe del recibo</text>',
    ]
    ancho, hueco = 150, 30
    for i, (titulo, signo) in enumerate(pasos):
        x = 30 + i * (ancho + hueco)
        relleno = CARD if i != 2 else "#fff6ef"
        borde = RULE if i != 2 else ACCENT
        piezas.append(f'<rect x="{x}" y="88" width="{ancho}" height="112" rx="6" '
                      f'fill="{relleno}" stroke="{borde}" stroke-width="1.5"/>')
        for j, linea in enumerate(titulo.split("\n")):
            piezas.append(f'<text x="{x + ancho / 2}" y="{132 + j * 22}" '
                          f'font-family="{FONT}" font-size="14" font-weight="bold" '
                          f'text-anchor="middle" fill="{INK}">{linea}</text>')
        if signo:
            piezas.append(f'<text x="{x + ancho + hueco / 2}" y="152" '
                          f'font-family="{FONT}" font-size="22" font-weight="bold" '
                          f'text-anchor="middle" fill="{ACCENT}">{signo}</text>')
    piezas.append(
        f'<text x="30" y="248" font-family="{FONT}" font-size="13.5" fill="{INK}">'
        f'La reducción arranca con un coeficiente de 0,9 y baja 0,1 cada año hasta '
        f'desaparecer al noveno (arts. 67 y 68 TRLRHL).</text>')
    piezas.append(
        f'<text x="30" y="276" font-family="{FONT}" font-size="13.5" fill="{INK}">'
        f'Por eso un recibo puede subir cada ejercicio sin que el pleno haya tocado '
        f'el tipo de gravamen.</text>')
    piezas.append(
        f'<text x="30" y="330" font-family="{FONT}" font-size="11.5" fill="{MID}">'
        f'Fuente: artículos 65 a 70 del TRLRHL y artículos 22 y 23 del texto '
        f'refundido de la Ley del Catastro Inmobiliario · TasasMunicipales.info</text>')
    piezas.append("</svg>")
    return "\n".join(piezas)


def svg_antiguedad(decadas: dict[int, int], total: int) -> str:
    w, h = 900, 400
    claves = sorted(decadas)
    top = max(decadas.values()) or 1
    ancho = min(120, int((w - 100) / max(1, len(claves))) - 20)
    hueco = 20
    base, alto_max = 300, 170
    piezas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-labelledby="t-ant d-ant">',
        '<title id="t-ant">Década de la última valoración catastral de los '
        'municipios de la guía</title>',
        f'<desc id="d-ant">Reparto de {total} municipios según la década en que '
        "entraron en vigor sus valores catastrales actuales: "
        + ", ".join(f"{d}: {decadas[d]}" for d in claves) + ".</desc>",
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="30" y="44" font-family="{FONT}" font-size="20" font-weight="bold" '
        f'fill="{INK}">Cuándo se revisaron por última vez los valores catastrales'
        f'</text>',
        f'<text x="30" y="68" font-family="{FONT}" font-size="13" fill="{MID}">'
        f'{total} municipios · la ley prevé revisarlos a partir de los 10 años '
        f'(art. 28 TRLCI)</text>',
    ]
    for i, d in enumerate(claves):
        c = decadas[d]
        x = 40 + i * (ancho + hueco)
        altura = max(4, alto_max * c / top)
        y = base - altura
        antiguo = ANO - (d + 9) >= 20
        piezas.append(f'<rect x="{x}" y="{y}" width="{ancho}" height="{altura}" '
                      f'rx="3" fill="{ACCENT if antiguo else ACCENT2}"/>')
        piezas.append(f'<text x="{x + ancho / 2}" y="{y - 10}" font-family="{FONT}" '
                      f'font-size="16" font-weight="bold" text-anchor="middle" '
                      f'fill="{INK}">{c}</text>')
        piezas.append(f'<text x="{x + ancho / 2}" y="{base + 24}" '
                      f'font-family="{FONT}" font-size="13" text-anchor="middle" '
                      f'fill="{INK}">{d}–{d + 9}</text>')
    piezas.append(f'<line x1="30" y1="{base}" x2="{w - 30}" y2="{base}" '
                  f'stroke="{RULE}" stroke-width="1.5"/>')
    piezas.append(f'<rect x="40" y="{base + 44}" width="14" height="14" '
                  f'fill="{ACCENT}"/>')
    piezas.append(f'<text x="62" y="{base + 56}" font-family="{FONT}" '
                  f'font-size="12.5" fill="{INK}">Valores de hace 20 años o más'
                  f'</text>')
    piezas.append(f'<text x="30" y="{base + 88}" font-family="{FONT}" '
                  f'font-size="11.5" fill="{MID}">Fuente: Ministerio de Hacienda, '
                  f'año de entrada en vigor de los valores catastrales de urbana · '
                  f'TasasMunicipales.info</text>')
    piezas.append("</svg>")
    return "\n".join(piezas)


# ──────────────────────── guía del impuesto de circulación ────────────────────

def guia_ivtm(ms: list[dict], imps: dict) -> None:
    ejercicio = ms[0].get("oficial_ejercicio", "2025")
    por_codigo: dict[str, list[tuple[float, dict]]] = {}
    for _, filas in TARIFA_LEGAL:
        for codigo, _, _ in filas:
            datos_c = []
            for m in ms:
                v = valor(imps.get(m.get("oficial_codigo_ine") or ""), codigo)
                if v is not None:
                    datos_c.append((v, m))
            por_codigo[codigo] = sorted(datos_c, key=lambda par: -par[0])

    turismos = por_codigo["C19"]
    (svg := ROOT / "img" / "esquema-ivtm.svg").write_text(svg_flujo_ivtm() + "\n",
                                                          encoding="utf-8")
    (svg2 := ROOT / "img" / "ivtm-turismos-2026.svg").write_text(
        svg_ivtm_turismos(turismos) + "\n", encoding="utf-8")
    print(f"  {svg.relative_to(ROOT)}  ·  {svg2.relative_to(ROOT)}")

    # tabla del cuadro legal con lo que se observa de verdad
    filas_tarifa = []
    for grupo, filas in TARIFA_LEGAL:
        filas_tarifa.append(
            f'          <tr><td colspan="5" style="background:rgba(0,0,0,.04)">'
            f"<strong>{grupo}</strong></td></tr>")
        for codigo, etiqueta, minimo in filas:
            obs = [v for v, _ in por_codigo.get(codigo, [])]
            med = eur(statistics.median(obs)) if obs else "—"
            mx = eur(max(obs)) if obs else "—"
            filas_tarifa.append(
                f"          <tr><td>{etiqueta}</td>"
                f'<td class="v">{eur(minimo)}</td><td>{eur(minimo * 2)}</td>'
                f"<td>{med}</td><td>{mx}</td></tr>")

    valores_t = [v for v, _ in turismos]
    mediana_t = statistics.median(valores_t)
    caro, barato = turismos[0], turismos[-1]
    en_minimo = [m for v, m in turismos if abs(v - 34.08) < 0.6]
    al_tope = [m for v, m in turismos if v >= 34.08 * 2 - 0.6]

    def tabla_ranking(sub: list[tuple[float, dict]], titulo: str) -> str:
        filas = "\n".join(
            f"        <tr><td>{enlace(m)}</td>"
            f'<td>{html.escape(m.get("provincia") or "—")}</td>'
            f'<td class="v">{eur(v)}</td><td>{num(v / 34.08, 2)}</td></tr>'
            for v, m in sub
        )
        return (
            f"      <tr><td colspan=\"4\" style=\"background:rgba(0,0,0,.04)\">"
            f"<strong>{titulo}</strong></td></tr>\n{filas}"
        )

    cuerpo = f"""{figura("esquema-ivtm.svg", "Esquema del cálculo del impuesto de circulación: clase y potencia del vehículo, cuota mínima legal, coeficiente municipal y bonificaciones", "Del vehículo a la cuota. Esquema propio según el artículo 95 del TRLRHL.", 900, 340, lazy=False)}

    <h2 id="que-es">Qué es el impuesto de circulación y quién lo paga</h2>
    <p>El <strong>impuesto sobre vehículos de tracción mecánica (IVTM)</strong>, que casi todo el mundo llama «impuesto de circulación» o «numerario», es un tributo municipal que grava la titularidad de un vehículo apto para circular por vías públicas. Lo regula el <a href="{TRLRHL}" target="_blank" rel="nofollow noopener">texto refundido de la Ley Reguladora de las Haciendas Locales</a> y lo cobra tu ayuntamiento, no la DGT ni Hacienda.</p>
    <p>El sujeto pasivo es quien figura como titular en el <strong>permiso de circulación</strong> (art. 94). Ojo a la consecuencia práctica: si vendiste el coche pero no se tramitó el cambio de titularidad, el recibo te sigue llegando a ti, porque el ayuntamiento se guía por el registro de la DGT y ahí el titular sigues siendo tú.</p>
    <div class="hb">
      <strong>📌 ¿Qué ayuntamiento cobra?</strong>
      El del <strong>domicilio que consta en el permiso de circulación</strong>, no el de tu residencia real (art. 97). Si te has mudado y no has actualizado el permiso, sigues pagando en el municipio anterior y con su tarifa. Cambiarlo es un trámite de la DGT.
    </div>

    <h2 id="calculo">Cómo se calcula: cuota mínima y coeficiente municipal</h2>
    <p>El IVTM <strong>no se calcula sobre el valor del coche ni sobre sus emisiones</strong>. El artículo 95.1 fija un cuadro de cuotas mínimas según la clase de vehículo y un parámetro técnico distinto en cada clase:</p>
    <ul>
      <li><strong>Turismos y tractores:</strong> los <em>caballos fiscales</em> (potencia fiscal), un dato que figura en la ficha técnica y que no coincide con los caballos de potencia del motor.</li>
      <li><strong>Autobuses:</strong> el número de plazas.</li>
      <li><strong>Camiones, remolques y semirremolques:</strong> los kilos de carga útil.</li>
      <li><strong>Motocicletas y ciclomotores:</strong> la cilindrada.</li>
    </ul>
    <p>Sobre esa cuota mínima, el ayuntamiento puede aplicar un <strong>coeficiente que no puede superar el 2</strong> (art. 95.4). Y puede fijar un coeficiente distinto para cada clase de vehículo, e incluso para cada tramo dentro de una misma clase. Si no aprueba ninguno, se paga la cuota mínima tal cual (art. 95.5).</p>
    <p>De ahí sale toda la variación entre municipios: no hay diferencias de método, solo de coeficiente. Por eso comparar el IVTM entre ayuntamientos es limpio, a diferencia del <a href="{PREFIX}ibi-2026/">IBI</a>, donde el valor catastral distorsiona cualquier comparación de tipos.</p>

    <h2 id="tarifas">Cuadro de tarifas: mínimo legal, tope y lo que se cobra de verdad</h2>
    <p>Las dos primeras columnas son la ley; las dos últimas, lo que hemos encontrado en los <strong>{len(ms)} municipios</strong> de la guía según los datos que el Ministerio de Hacienda publica para el ejercicio {ejercicio}.</p>
    <div class="table-scroll">
      <table class="dt">
        <thead><tr><th>Vehículo</th><th>Cuota mínima (art. 95.1)</th><th>Tope legal (×2)</th><th>Mediana observada</th><th>Máximo observado</th></tr></thead>
        <tbody>
{chr(10).join(filas_tarifa)}
        </tbody>
      </table>
    </div>
    <p style="font-size:.85rem;color:var(--mid)">El cuadro de cuotas mínimas puede modificarse por la Ley de Presupuestos Generales del Estado (art. 95.2). Fuente de las columnas observadas: <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a>.</p>

    <h2 id="cuanto">Cuánto cuesta el mismo coche según dónde vivas</h2>
    <p>Para el turismo más habitual, el de <strong>8 a 11,99 caballos fiscales</strong>, la cuota mínima legal es de {eur(34.08)} y el tope de {eur(68.16)}. Entre los {len(turismos)} municipios con dato:</p>
    <ul>
      <li>La mediana está en <strong>{eur(mediana_t)}</strong>, es decir un coeficiente medio de {num(mediana_t / 34.08, 2)}.</li>
      <li><strong>{len(en_minimo)} municipios</strong> cobran la cuota mínima legal o algo muy próximo: renuncian a subir este impuesto.</li>
      <li><strong>{len(al_tope)}</strong> están en el tope de la ley, con el coeficiente 2 agotado.</li>
      <li>El más caro es {enlace(caro[1])} ({eur(caro[0])}) y el más barato {enlace(barato[1])} ({eur(barato[0])}). La diferencia por el mismo coche es de <strong>{eur(caro[0] - barato[0])} al año</strong>.</li>
    </ul>
{figura("ivtm-turismos-2026.svg", "Gráfico del coeficiente que aplican los municipios al impuesto de circulación de un turismo de 8 a 11,99 caballos fiscales", "Reparto de los municipios de la guía según el coeficiente que aplican sobre la cuota mínima. Gráfico propio elaborado con los datos de esta página.", 900, 400)}
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Provincia</th><th>Cuota anual</th><th>Coeficiente</th></tr></thead>
      <tbody>
{tabla_ranking(turismos[:12], "Los 12 más caros")}
{tabla_ranking(turismos[-12:], "Los 12 más baratos")}
      </tbody>
    </table>
    <p><a href="{PREFIX}analisis/impuesto-circulacion-ivtm/" style="color:var(--accent);font-weight:600">Tabla ordenable con los {len(turismos)} municipios y todas las clases de vehículo →</a></p>

    <h2 id="exenciones">Vehículos exentos (art. 93)</h2>
    <p>La ley exime del impuesto, sin que el ayuntamiento pueda decidir lo contrario:</p>
    <ul>
      <li>Los vehículos <strong>oficiales</strong> del Estado, comunidades autónomas y entidades locales adscritos a la defensa nacional o a la seguridad ciudadana.</li>
      <li>Los de <strong>representaciones diplomáticas</strong> y organismos internacionales, en las condiciones del artículo.</li>
      <li>Los que resulten exentos por <strong>tratados o convenios internacionales</strong>.</li>
      <li>Las <strong>ambulancias</strong> y demás vehículos destinados directamente a la asistencia sanitaria o al traslado de heridos o enfermos.</li>
      <li>Los vehículos para <strong>personas de movilidad reducida</strong> y los matriculados a nombre de personas con discapacidad para su uso exclusivo, con grado reconocido igual o superior al 33%. Aquí hay un límite que se pasa por alto: <strong>no cabe la exención por más de un vehículo simultáneamente</strong>, y hay que solicitarla aportando el certificado y justificando el destino del vehículo.</li>
      <li>Los <strong>autobuses y microbuses</strong> del transporte público urbano con más de nueve plazas, incluida la del conductor.</li>
      <li>Los <strong>tractores, remolques, semirremolques y maquinaria</strong> provistos de Cartilla de Inspección Agrícola.</li>
    </ul>
    <div class="hb red">
      <strong>⚠️ Las dos últimas y la de discapacidad no son automáticas</strong>
      El artículo 93.2 exige <strong>solicitarlas</strong> indicando las características del vehículo, la matrícula y la causa. Hasta que el ayuntamiento las declara y expide el documento acreditativo, el recibo se gira.
    </div>

    <h2 id="bonificaciones">Bonificaciones que puede aprobar tu ayuntamiento</h2>
    <p>Además de las exenciones, el artículo 95.6 permite que la ordenanza regule tres bonificaciones sobre la cuota, ya esté incrementada por el coeficiente o no:</p>
    <table class="dt">
      <thead><tr><th>Bonificación</th><th>Tope legal</th><th>Base</th></tr></thead>
      <tbody>
        <tr><td>Según la clase de carburante, por su incidencia en el medio ambiente</td><td class="v">Hasta 75%</td><td>Art. 95.6.a</td></tr>
        <tr><td>Según las características del motor y su incidencia en el medio ambiente</td><td class="v">Hasta 75%</td><td>Art. 95.6.b</td></tr>
        <tr><td>Vehículos históricos o con 25 años o más de antigüedad</td><td class="v">Hasta 100%</td><td>Art. 95.6.c</td></tr>
      </tbody>
    </table>
    <p>Las dos primeras son la vía por la que muchos ayuntamientos bonifican <strong>eléctricos, híbridos y de gas</strong>: la ley no habla de «coche eléctrico», habla de carburante y de características del motor, y es la ordenanza la que concreta qué tecnologías entran y con qué porcentaje.</p>
    <p>La antigüedad de 25 años se cuenta desde la <strong>fecha de fabricación</strong> y, si no se conoce, desde la primera matriculación o, en su defecto, desde que se dejó de fabricar ese tipo o variante. Y sí, puede llegar al 100%: hay municipios donde un coche de 25 años no paga IVTM.</p>

    <h2 id="cuando">Cuándo se paga y cuándo se prorratea</h2>
    <p>El período impositivo es el año natural y el impuesto <strong>se devenga el 1 de enero</strong> (art. 96). Quien sea titular ese día paga el año completo, aunque venda el coche en febrero.</p>
    <p>La cuota <strong>solo se prorratea por trimestres naturales</strong> en tres casos:</p>
    <ul>
      <li><strong>Primera adquisición</strong> del vehículo: el período empieza el día de la adquisición.</li>
      <li><strong>Baja definitiva.</strong></li>
      <li><strong>Baja temporal por sustracción o robo</strong>, desde el momento en que se produce la baja en el registro correspondiente.</li>
    </ul>
    <p>Fuera de esos tres supuestos no hay devolución de la parte del año, y en particular <strong>una compraventa entre particulares no prorratea nada</strong>: quien lo pague y cómo se reparta es cosa del contrato entre las partes.</p>
    <div class="hb gold">
      <strong>🔑 Si vas a vender o comprar un coche de segunda mano</strong>
      El artículo 99.2 impide a las Jefaturas Provinciales de Tráfico tramitar el <strong>cambio de titularidad</strong> mientras el titular registral no acredite el pago del impuesto del <strong>año anterior</strong> al del trámite. Es el motivo por el que en la compraventa siempre se pide el último recibo del IVTM: sin él, la transferencia se queda parada.
    </div>

    <h2 id="reclamar">Qué hacer si el recibo está mal</h2>
    <p>Los errores más frecuentes son de datos del vehículo (clase, potencia fiscal, cilindrada) o de titularidad después de una venta o una baja. El cauce es el mismo que en el resto de tributos locales:</p>
    <ul>
      <li><strong>Recurso de reposición</strong> ante el ayuntamiento u organismo que gestione la recaudación, en el plazo de <strong>un mes</strong> desde la notificación.</li>
      <li>O <strong>reclamación económico-administrativa</strong>, en los municipios que tienen órgano propio para resolverlas.</li>
      <li>Si el error está en los datos del vehículo, el arreglo de fondo está en la DGT: mientras el registro diga otra cosa, el ayuntamiento seguirá liquidando con ese dato.</li>
      <li>Salvo que se suspenda con garantía, conviene pagar dentro del plazo mientras se reclama para no sumar los recargos del <a href="{LGT}" target="_blank" rel="nofollow noopener">artículo 28 de la Ley General Tributaria</a>. <a href="{PREFIX}ibi-2026/#recargos">Cómo funcionan esos recargos →</a></li>
    </ul>

    <h2 id="municipios">El IVTM en tu municipio</h2>
    <p>En la ficha de cada uno de los {len(ms)} municipios publicamos su <strong>tarifa completa</strong>: las 24 cuotas por clase de vehículo tal y como las recoge el Ministerio de Hacienda, junto con el tipo del IBI, el ICIO y los coeficientes de plusvalía.</p>
    <p><a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio entre los {len(ms)} →</a> · <a href="{PREFIX}comunidades/">Ver por comunidad autónoma →</a></p>
    <p style="font-size:.85rem;color:var(--mid)">Lo que la consulta del Ministerio <strong>no</strong> publica son las exenciones y bonificaciones de cada ordenanza, que en el IVTM son especialmente relevantes. Para eso hay que leer la ordenanza fiscal: en cada ficha enlazamos el organismo que la gestiona.</p>
"""
    faq = [
        ("¿Cuánto se paga de impuesto de circulación por un coche normal?",
         f"Para un turismo de 8 a 11,99 caballos fiscales, la cuota mínima legal es de "
         f"34,08 € y el tope que permite la ley, 68,16 €. En los {len(turismos)} "
         f"municipios que analizamos la mediana está en {eur(mediana_t)} al año."),
        ("¿Quién paga el IVTM si vendo el coche a mitad de año?",
         "Lo paga quien fuera titular a 1 de enero, y por el año completo: la cuota no "
         "se prorratea en una compraventa. Solo hay prorrateo por trimestres en la "
         "primera adquisición, en la baja definitiva y en la baja temporal por robo."),
        ("¿Qué ayuntamiento me cobra el impuesto de circulación?",
         "El del domicilio que figure en el permiso de circulación, no el de tu "
         "residencia real. Si te mudas y no actualizas el permiso en la DGT, sigues "
         "pagando en el municipio anterior."),
        ("¿Los coches eléctricos están exentos del IVTM?",
         "Exentos no: la ley no los incluye entre las exenciones del artículo 93. Lo "
         "que sí permite es que la ordenanza los bonifique hasta el 75% por las "
         "características del motor o por el carburante. Depende de tu municipio."),
        ("¿Un coche de más de 25 años paga impuesto de circulación?",
         "Depende de la ordenanza. El artículo 95.6.c permite bonificarlo hasta el "
         "100% por ser histórico o tener 25 años o más, contados desde su fabricación, "
         "pero es potestativo y hay que solicitarlo."),
        ("¿Puedo cambiar el coche de nombre si debo el IVTM?",
         "No. Tráfico no tramita el cambio de titularidad mientras el titular no "
         "acredite el pago del impuesto del año anterior al del trámite (art. 99.2 "
         "TRLRHL). Por eso en la compraventa se pide el último recibo."),
    ]
    aside_filas = "".join(
        f'<li><a href="{ficha(m)}">IVTM {html.escape(m["nombre"])} · {eur(v)}</a></li>'
        for v, m in turismos[:12]
    )
    aside = f"""<aside>
  <div class="sb"><div class="sbh">🚗 Los más caros en IVTM</div>
  <div class="sbb"><ul>{aside_filas}</ul>
  <p style="font-size:.78rem;margin-top:10px"><a href="{PREFIX}analisis/impuesto-circulacion-ivtm/" style="color:var(--accent);font-weight:600">Comparativa completa →</a></p>
  </div></div>
  <div class="sb"><div class="sbh">📊 En un dato</div>
  <div class="sbb"><p style="font-size:.85rem">Cuota mínima legal para un turismo de 8 a 11,99 CV: <strong>{eur(34.08)}</strong>. Tope con el coeficiente máximo: <strong>{eur(68.16)}</strong>. Mediana de los municipios de la guía: <strong>{eur(mediana_t)}</strong>.</p></div></div>
</aside>"""
    pagina(
        "impuesto-circulacion",
        f"Impuesto de circulación · Guía {ANO}",
        f"Impuesto de circulación {ANO}: tarifas, exenciones y cuotas",
        f"Cuánto se paga de IVTM en {ANO}: cuadro de cuotas mínimas del art. 95 TRLRHL, "
        f"el coeficiente municipal (tope 2), exenciones, bonificaciones de eléctricos e "
        f"históricos, prorrateo y la tarifa real de {len(ms)} municipios.",
        f"Impuesto de circulación {ANO}: cuánto se paga, exenciones y tarifas por municipio",
        11,
        [("que-es", "Qué es y quién lo paga"), ("calculo", "Cómo se calcula"),
         ("tarifas", "Cuadro de tarifas"), ("cuanto", "Cuánto cuesta según dónde vivas"),
         ("exenciones", "Vehículos exentos"), ("bonificaciones", "Bonificaciones"),
         ("cuando", "Cuándo se paga y prorrateo"), ("reclamar", "Si el recibo está mal"),
         ("municipios", "El IVTM en tu municipio"), ("faq", "Preguntas frecuentes")],
        cuerpo, faq, aside,
    )


# ─────────────────────────── guía del valor catastral ─────────────────────────

def guia_valor_catastral(ms: list[dict]) -> None:
    anos = [int(m["oficial_ano_valores_catastrales"]) for m in ms
            if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()]
    mediana = int(statistics.median(anos))
    antig_mediana = ANO - mediana
    mas_20 = sum(1 for a in anos if ANO - a >= 20)
    mas_10 = sum(1 for a in anos if ANO - a >= 10)
    decadas: dict[int, int] = {}
    for a in anos:
        decadas[(a // 10) * 10] = decadas.get((a // 10) * 10, 0) + 1
    (svg := ROOT / "img" / "esquema-valor-catastral.svg").write_text(
        svg_flujo_catastro() + "\n", encoding="utf-8")
    (svg2 := ROOT / "img" / "valor-catastral-antiguedad.svg").write_text(
        svg_antiguedad(decadas, len(anos)) + "\n", encoding="utf-8")
    print(f"  {svg.relative_to(ROOT)}  ·  {svg2.relative_to(ROOT)}")

    viejos = sorted(
        ((int(m["oficial_ano_valores_catastrales"]), m) for m in ms
         if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()),
        key=lambda par: par[0],
    )
    filas_viejos = "\n".join(
        f"        <tr><td>{enlace(m)}</td>"
        f'<td>{html.escape(m.get("provincia") or "—")}</td>'
        f'<td class="v">{a}</td><td>{ANO - a} años</td></tr>'
        for a, m in viejos[:12]
    )
    filas_decadas = "\n".join(
        f"        <tr><td>{d}–{d + 9}</td><td class=\"v\">{decadas[d]}</td>"
        f"<td>{num(100 * decadas[d] / len(anos), 1)}%</td></tr>"
        for d in sorted(decadas)
    )
    reduccion = "\n".join(
        f"        <tr><td>Año {i + 1}</td><td class=\"v\">{num(0.9 - i * 0.1, 1)}</td>"
        f"<td>{num((0.9 - i * 0.1) * 100, 0)}% del incremento sigue sin tributar</td></tr>"
        for i in range(9)
    )

    cuerpo = f"""{figura("esquema-valor-catastral.svg", "Esquema del cálculo: valor del suelo más valor de la construcción igual a valor catastral, menos la reducción igual a base liquidable, por el tipo de gravamen", "Del valor catastral al importe del recibo. Esquema propio según los artículos 65 a 70 del TRLRHL.", 900, 360, lazy=False)}

    <h2 id="que-es">Qué es el valor catastral</h2>
    <p>El <strong>valor catastral</strong> es el valor administrativo que el Catastro asigna a cada inmueble, y se compone de dos partes que conviene tener separadas en la cabeza: el <strong>valor del suelo</strong> y el <strong>valor de la construcción</strong>. Esa distinción no es teórica: la plusvalía municipal se calcula solo sobre el valor del suelo, así que en una venta necesitarás el desglose, no el total.</p>
    <p>Lo determina la Dirección General del Catastro con los criterios del artículo 23 del <a href="{TRLCI}" target="_blank" rel="nofollow noopener">texto refundido de la Ley del Catastro Inmobiliario</a>: la localización y las circunstancias urbanísticas del suelo, el coste de ejecución de la construcción, su uso, calidad y antigüedad, los gastos y beneficios de la promoción y las circunstancias del mercado.</p>
    <p>Y tiene un límite legal expreso: <strong>el valor catastral no puede superar el valor de mercado</strong>. Para garantizarlo se aplica un <em>coeficiente de referencia al mercado</em> que se fija por orden ministerial (art. 23.2). Es la razón por la que el valor catastral de una vivienda suele estar bastante por debajo de lo que costaría venderla.</p>
    <div class="hb">
      <strong>📌 Por qué te importa esta cifra</strong>
      Del valor catastral salen la cuota del <a href="{PREFIX}ibi-2026/">IBI</a>, la base objetiva de la <a href="{PREFIX}plusvalia/">plusvalía municipal</a>, la imputación de rentas inmobiliarias del IRPF de las segundas residencias y la valoración de inmuebles en el Impuesto sobre el Patrimonio. Un error en el valor catastral se multiplica por todos ellos, año tras año.
    </div>

    <h2 id="consultar">Cómo consultar tu valor catastral</h2>
    <p>Hay tres vías, y solo dos te dan la cifra:</p>
    <ol>
      <li><strong>Tu último recibo del IBI.</strong> Aparece como «valor catastral» o «base imponible», junto con la referencia catastral de 20 caracteres. Es la vía más rápida.</li>
      <li><strong>La <a href="{CATASTRO}" target="_blank" rel="nofollow noopener">Sede Electrónica del Catastro</a> con identificación digital</strong> (Cl@ve, certificado electrónico o DNIe): «Consulta de datos catastrales» → «Consulta de un inmueble». Verás el valor total <em>y su desglose</em> entre suelo y construcción, además del uso, la superficie y el año de construcción.</li>
      <li><strong>La consulta libre, sin identificarte</strong>, te da superficie, uso y año, pero <strong>no el valor catastral</strong>: es un dato protegido que solo se muestra al titular. Si no puedes identificarte, pídelo en tu ayuntamiento o en la Gerencia Territorial del Catastro.</li>
    </ol>

    <h2 id="valor-referencia">Valor catastral y valor de referencia: no son lo mismo</h2>
    <p>Es la confusión más extendida desde 2022, y cuesta dinero cuando se mezclan. Los dos los calcula el Catastro, pero sirven para cosas distintas:</p>
    <table class="dt">
      <thead><tr><th>&nbsp;</th><th>Valor catastral</th><th>Valor de referencia</th></tr></thead>
      <tbody>
        <tr><td><strong>Para qué sirve</strong></td><td>Base imponible del IBI y base objetiva de la plusvalía municipal</td><td>Base imponible del ITP y del Impuesto sobre Sucesiones y Donaciones</td></tr>
        <tr><td><strong>Cómo se calcula</strong></td><td>Ponencia de valores del municipio, con módulos de suelo y construcción</td><td>Del análisis de los <strong>precios comunicados por los notarios</strong> en las compraventas, con un informe anual y un mapa de valores</td></tr>
        <tr><td><strong>Límite</strong></td><td>No puede superar el valor de mercado (art. 23.2 TRLCI)</td><td>No puede superar el valor de mercado (disposición final tercera TRLCI)</td></tr>
        <tr><td><strong>Cada cuánto cambia</strong></td><td>Solo con una valoración colectiva o una actualización por coeficientes</td><td>Se determina <strong>cada año</strong></td></tr>
        <tr><td><strong>Es público</strong></td><td>No: dato protegido, solo para el titular</td><td>Sí: cualquiera puede consultarlo</td></tr>
      </tbody>
    </table>
    <p>Traducido: el valor de referencia <strong>no cambia tu IBI</strong>, y el valor catastral <strong>no determina lo que pagas al comprar</strong>. Que el valor de referencia de tu vivienda sea alto no encarece el recibo del IBI; encarece el impuesto de quien la compre o la herede.</p>

    <h2 id="al-recibo">Del valor catastral al recibo: la base liquidable</h2>
    <p>La cuota del IBI no es «valor catastral × tipo» sin más. El valor catastral es la <strong>base imponible</strong> (art. 65 TRLRHL); sobre ella se aplica una reducción y el resultado es la <strong>base liquidable</strong>, que es la cifra que se multiplica por el tipo de gravamen municipal.</p>
    <p>Esa reducción existe para amortiguar las subidas de las valoraciones colectivas. Dura <strong>nueve años</strong> y decrece sola: arranca con un coeficiente de 0,9 y baja 0,1 cada ejercicio hasta desaparecer (arts. 67 y 68 TRLRHL).</p>
    <table class="dt">
      <thead><tr><th>Ejercicio desde la revisión</th><th>Coeficiente reductor</th><th>Efecto</th></tr></thead>
      <tbody>
{reduccion}
      </tbody>
    </table>
    <div class="hb gold">
      <strong>💡 Aquí está la respuesta a «¿por qué me sube el IBI si el tipo no ha cambiado?»</strong>
      Si tu municipio hizo una valoración colectiva hace pocos años, cada ejercicio se reduce menos el incremento, así que la base liquidable sube sola. El pleno no ha tocado nada: se está agotando la reducción.
    </div>

    <h2 id="revision">Cada cuánto se revisan y qué dice la ley</h2>
    <p>Una <strong>valoración colectiva de carácter general</strong> es un procedimiento completo: el Catastro aprueba una ponencia de valores para todo el término municipal, la somete a información pública y la publica en el boletín oficial de la provincia. Se inicia de oficio o <strong>a solicitud del ayuntamiento</strong>.</p>
    <p>El artículo 28 del TRLCI marca dos plazos que casi nadie cita: solo puede iniciarse <strong>una vez transcurridos al menos cinco años</strong> desde la entrada en vigor de los valores anteriores, y <strong>«se realizará, en todo caso, a partir de los 10 años»</strong> desde esa fecha.</p>
    <p>Contrastemos ese «en todo caso» con la realidad de los {len(anos)} municipios que cubrimos: la antigüedad mediana de la última valoración es de <strong>{antig_mediana} años</strong>, <strong>{mas_10}</strong> superan los diez y <strong>{mas_20}</strong> arrastran valores de hace veinte o más.</p>
{figura("valor-catastral-antiguedad.svg", "Gráfico del reparto de los municipios de la guía según la década de su última valoración catastral", "Década en la que entraron en vigor los valores catastrales vigentes. Gráfico propio con datos del Ministerio de Hacienda.", 900, 400)}
    <table class="dt">
      <thead><tr><th>Década de la última valoración</th><th>Municipios</th><th>% del total</th></tr></thead>
      <tbody>
{filas_decadas}
      </tbody>
    </table>
    <h3>Los municipios con la ponencia más antigua de la guía</h3>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Provincia</th><th>Año de la valoración</th><th>Antigüedad</th></tr></thead>
      <tbody>
{filas_viejos}
      </tbody>
    </table>
    <p><a href="{PREFIX}analisis/valores-catastrales-antiguos/" style="color:var(--accent);font-weight:600">Análisis completo: por qué comparar tipos de IBI no dice cuánto se paga →</a></p>

    <h2 id="actualizacion">La otra vía: actualización por coeficientes</h2>
    <p>Sin abrir una valoración colectiva, los valores catastrales pueden actualizarse aplicando <strong>coeficientes aprobados en la Ley de Presupuestos Generales del Estado</strong> (art. 32.1 TRLCI). Es la vía rápida, y puede ser al alza o a la baja.</p>
    <p>Además, el artículo 32.2 permite actualizar los valores urbanos de un municipio concreto en función del año de su ponencia, pero <strong>solo si el ayuntamiento lo solicita</strong> y se cumplen tres requisitos:</p>
    <ul>
      <li>Que hayan pasado <strong>al menos cinco años</strong> desde la entrada en vigor de los valores de la anterior valoración colectiva general.</li>
      <li>Que existan <strong>diferencias sustanciales</strong> entre los valores de mercado y los que sirvieron de base a los valores vigentes, y que afecten de modo homogéneo a todo el municipio.</li>
      <li>Que la solicitud se comunique a la Dirección General del Catastro <strong>antes del 31 de mayo</strong> del ejercicio anterior al de aplicación.</li>
    </ul>
    <p>De aquí sale una consecuencia política interesante: la actualización a la baja también existe, y en los años posteriores a 2008 se usó. Cuando un ayuntamiento no pide nada, los valores se quedan donde están.</p>

    <h2 id="corregir">Qué revisar y cómo corregirlo</h2>
    <p>Conviene separar dos problemas distintos, porque el trámite y el plazo no son los mismos.</p>
    <h3>Los datos del inmueble no coinciden con la realidad</h3>
    <p>Superficie que no cuadra, un uso que ya no es el que consta, una reforma o una demolición no registradas, una titularidad sin actualizar tras una compra o una herencia. Se corrige ante el <strong>Catastro</strong>, y el artículo 18 del TRLCI regula el <strong>procedimiento de subsanación de discrepancias</strong>, que la Administración puede iniciar de oficio cuando conoce la falta de concordancia. Los efectos van desde la resolución, no hacia atrás, así que cuanto antes se detecte, mejor.</p>
    <h3>No estás de acuerdo con el valor asignado</h3>
    <p>Aquí sí corre el plazo: contra la notificación del nuevo valor catastral cabe <strong>recurso de reposición o reclamación económico-administrativa ante el TEAR en el plazo de un mes</strong>, y son excluyentes entre sí. Pasado ese mes el valor queda firme y solo podrá discutirse en la siguiente valoración.</p>
    <div class="hb red">
      <strong>⚠️ Recurrir el recibo del IBI no sirve para discutir el valor catastral</strong>
      Son dos administraciones distintas: el ayuntamiento gestiona el IBI y el Catastro fija el valor. El ayuntamiento <strong>no puede</strong> modificar la base imponible que le viene dada. Si el problema es el valor, el expediente va al Catastro; si es el recibo (titularidad, bonificación no aplicada, error de cálculo), al ayuntamiento.
    </div>
    <p style="font-size:.85rem;color:var(--mid)">Este apartado resume el procedimiento general y no es asesoramiento jurídico: los plazos y el órgano competente concretos figuran en la notificación que recibas.</p>

    <h2 id="municipios">El año de tu valoración catastral, municipio a municipio</h2>
    <p>En la ficha de cada uno de los {len(ms)} municipios publicamos el <strong>año de entrada en vigor de sus valores catastrales de urbana</strong>, tal y como lo recoge el Ministerio de Hacienda, junto con el tipo de IBI que se aplica sobre ellos.</p>
    <p><a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Comparador con el año de valoración de los {len(ms)} municipios →</a> · <a href="{PREFIX}calculadora-ibi/">Calcular mi IBI con mi valor catastral →</a></p>
"""
    faq = [
        ("¿Dónde veo el valor catastral de mi casa?",
         "En el recibo del IBI, donde aparece como valor catastral o base imponible, o "
         "en la Sede Electrónica del Catastro identificándote con Cl@ve, certificado o "
         "DNIe. La consulta libre sin identificación no muestra el valor: es un dato "
         "protegido."),
        ("¿Es lo mismo el valor catastral que el valor de referencia?",
         "No. El valor catastral es la base del IBI y de la plusvalía municipal y solo "
         "cambia con una valoración colectiva o una actualización por coeficientes. El "
         "valor de referencia se calcula cada año a partir de los precios que comunican "
         "los notarios y es la base del ITP y del Impuesto sobre Sucesiones y "
         "Donaciones."),
        ("¿Por qué me sube el IBI si mi ayuntamiento no ha subido el tipo?",
         "Lo más probable es que se esté agotando la reducción de la base liquidable. "
         "Tras una valoración colectiva al alza, la reducción dura nueve años y baja "
         "0,1 cada ejercicio, así que la base liquidable sube sola sin que el pleno "
         "toque nada."),
        ("¿Cada cuánto tiempo se revisa el valor catastral?",
         f"La ley permite iniciar una valoración colectiva general a partir de los cinco "
         f"años y dice que se realizará en todo caso a partir de los diez. En la "
         f"práctica, la antigüedad mediana de los {len(anos)} municipios que analizamos "
         f"es de {antig_mediana} años."),
        ("¿Puedo pedir que me bajen el valor catastral?",
         "Puedes recurrir la notificación del valor en el plazo de un mes, y puedes "
         "pedir en cualquier momento la subsanación de discrepancias si los datos "
         "físicos del inmueble no coinciden con la realidad. Lo que no cabe es "
         "solicitar una rebaja del valor sin más: la actualización a la baja de todo un "
         "municipio la pide el ayuntamiento al Catastro."),
        ("¿El valor catastral puede ser superior al precio de mercado?",
         "No debe: el artículo 23.2 del texto refundido de la Ley del Catastro "
         "Inmobiliario lo prohíbe expresamente y para garantizarlo se aplica un "
         "coeficiente de referencia al mercado. Si tras una caída de precios tu valor "
         "catastral supera el de mercado, es motivo para recurrir."),
    ]
    aside_filas = "".join(
        f'<li><a href="{ficha(m)}">{html.escape(m["nombre"])} · {a} '
        f"({ANO - a} años)</a></li>"
        for a, m in viejos[:12]
    )
    aside = f"""<aside>
  <div class="sb"><div class="sbh">🏚️ Las ponencias más antiguas</div>
  <div class="sbb"><ul>{aside_filas}</ul>
  <p style="font-size:.78rem;margin-top:10px"><a href="{PREFIX}analisis/valores-catastrales-antiguos/" style="color:var(--accent);font-weight:600">Análisis completo →</a></p>
  </div></div>
  <div class="sb"><div class="sbh">📊 En un dato</div>
  <div class="sbb"><p style="font-size:.85rem">Antigüedad mediana de la última valoración catastral en los {len(anos)} municipios de la guía: <strong>{antig_mediana} años</strong>. La ley prevé revisarlas a partir de los 10.</p></div></div>
</aside>"""
    pagina(
        "valor-catastral",
        "Valor catastral · Guía 2026",
        "Valor catastral: qué es, cómo consultarlo y cómo corregirlo",
        f"Qué es el valor catastral y en qué se diferencia del valor de referencia, cómo "
        f"consultarlo, cómo llega al recibo del IBI a través de la base liquidable, cada "
        f"cuánto se revisa —{antig_mediana} años de mediana en {len(anos)} municipios— y "
        f"cómo corregirlo.",
        "Valor catastral: qué es, cómo consultarlo y cómo corregirlo",
        12,
        [("que-es", "Qué es el valor catastral"), ("consultar", "Cómo consultarlo"),
         ("valor-referencia", "Valor catastral y valor de referencia"),
         ("al-recibo", "Del valor catastral al recibo"),
         ("revision", "Cada cuánto se revisan"),
         ("actualizacion", "Actualización por coeficientes"),
         ("corregir", "Qué revisar y cómo corregirlo"),
         ("municipios", "Municipio a municipio"), ("faq", "Preguntas frecuentes")],
        cuerpo, faq, aside,
    )


def main() -> int:
    ms = [m for m in datos() if m.get("oficial_tipo_urbana")]
    imps = impuestos()
    print("Generando las guías nuevas:")
    guia_ivtm(ms, imps)
    guia_valor_catastral(ms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
