#!/usr/bin/env python3
"""Genera los articulos de analisis propios a partir de los datos oficiales.

El sitio no tenia contenido editorial: solo fichas municipales y guias genericas
que cualquiera puede escribir. Estos cuatro articulos son analisis que solo se
pueden hacer teniendo los 134 municipios normalizados en una tabla, y cada cifra
sale de una fuente citada (Ministerio de Hacienda, INE, BOE).

  /analisis/                              indice
  /analisis/ranking-ibi-municipios/       donde se paga mas y menos IBI
  /analisis/impuesto-circulacion-ivtm/    lo que cuesta el IVTM municipio a municipio
  /analisis/coeficientes-plusvalia/       quien aplica los coeficientes maximos
  /analisis/valores-catastrales-antiguos/ municipios con la ponencia mas vieja

Uso:  python3 scripts/build_analisis.py
"""
from __future__ import annotations

import html
import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import build_extra_pages as bx
import build_territory_pillars as tp

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"
TODAY = date.today().isoformat()
PREFIX = "../../"
HACIENDA = ("https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/"
            "html/portadaconsultasm.aspx")
BOE_TRLRHL = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214"
BOE_TRLCI = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4163"
REF_VC = 50000
AUTOR = "Aithamy Rivero"

# Coeficientes maximos del art. 107.4 TRLRHL (los que publicamos en /plusvalia/).
MAXIMOS_PLUSVALIA = [
    0.15, 0.15, 0.14, 0.14, 0.16, 0.18, 0.19, 0.20, 0.19, 0.15, 0.12,
    0.10, 0.09, 0.09, 0.09, 0.09, 0.10, 0.13, 0.17, 0.23, 0.40,
]
PERIODOS = ["Menos de 1 año"] + [f"{n} año{'s' if n > 1 else ''}" for n in range(1, 20)] \
    + ["20 años o más"]


def pct(v: float) -> str:
    texto = f"{round(v, 4):g}"
    return texto.replace(".", ",") + "%"


def num(v: float, dec: int = 2) -> str:
    return f"{v:,.{dec}f}".replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def euros(v: float) -> str:
    return num(v, 0) + " €"


def to_float(texto) -> float | None:
    if texto in (None, "", "-"):
        return None
    try:
        return float(str(texto).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def serie_plausible(coefs: list[float | None]) -> bool:
    """Mismo criterio que scripts/polish_fichas.py: los coeficientes del
    art. 107.4 TRLRHL van de 0,09 a 0,40. Series muy por debajo son, casi con
    seguridad, el porcentaje anual del sistema anterior al RDL 26/2021."""
    validos = [c for c in coefs if c is not None]
    return bool(validos) and 0.10 <= max(validos) <= 0.45


def municipios() -> list[dict]:
    filas = json.loads((ROOT / "data" / "municipios.json").read_text(encoding="utf-8"))
    return [m for m in filas["municipios"] if m.get("oficial_tipo_urbana")]


def impuestos() -> dict:
    ruta = ROOT / "data" / "hacienda_impuestos.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def ficha(m: dict) -> str:
    return f"{PREFIX}{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"


def enlace(m: dict) -> str:
    return f'<a href="{ficha(m)}">{html.escape(m["nombre"])}</a>'


def ccaa_nombre(m: dict) -> str:
    return bx.CCAA.get(m["ccaa"], m["ccaa"])


# ───────────────────────── figuras propias de cada analisis ─────────────────────────
# Cada analisis llevaba tablas pero ninguna imagen. Estos SVG se dibujan con los
# mismos datos que la pagina, llevan <title>/<desc> para lectores de pantalla, el
# texto va como texto (indexable) y pesan pocos kB.

INK, ACCENT, ACCENT2 = "#1a1a2e", "#c8522a", "#2a7c6f"
PAPER, RULE, MID = "#f5f0e8", "#d8d0c0", "#6b6b7b"
FONT = "Georgia, 'Source Serif 4', serif"


def guarda_svg(nombre: str, svg: str, alt: str, pie: str, *, prefix: str = PREFIX,
               lazy: bool = True) -> str:
    """Escribe el SVG en /img y devuelve el <figure> listo para insertar."""
    destino = ROOT / "img" / nombre
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(svg + "\n", encoding="utf-8")
    w, h = tp.svg_size(destino)
    print(f"    img/{nombre}  ({len(svg) // 1024 or 1} kB)")
    return tp.figure(f"{prefix}img/{nombre}", alt, pie, w, h, lazy=lazy)


def _marco(w: int, h: int, ident: str, titulo: str, desc: str, rotulo: str,
           subrotulo: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-labelledby="t-{ident} d-{ident}" '
        f'font-family="{FONT}">',
        f'<title id="t-{ident}">{html.escape(titulo)}</title>',
        f'<desc id="d-{ident}">{html.escape(desc)}</desc>',
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="24" y="38" font-size="21" font-weight="700" fill="{INK}">'
        f'{html.escape(rotulo)}</text>',
        f'<text x="24" y="61" font-size="13" fill="{MID}">{html.escape(subrotulo)}</text>',
    ]


def _pie_svg(w: int, h: int, texto: str) -> str:
    return (f'<text x="24" y="{h - 16}" font-size="11.5" fill="{MID}">'
            f'{html.escape(texto)}</text>')


def svg_distribucion_tipos(tipos: list[float], ejercicio: str) -> str:
    """Histograma del tipo de IBI urbano sobre la horquilla legal 0,40%-1,10%."""
    bordes = [0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10]
    cubos = []
    for i in range(len(bordes) - 1):
        desde, hasta = bordes[i], bordes[i + 1]
        ultimo = i == len(bordes) - 2
        n = sum(1 for t in tipos
                if (desde <= t <= hasta if ultimo else desde <= t < hasta))
        cubos.append((desde, hasta, n))
    bajo = sum(1 for t in tipos if t < 0.40)
    w, h = 900, 430
    base, top = h - 78, 104
    izq, alto = 70, base - top
    ancho = (w - izq - 40) / len(cubos)
    vmax = max(n for _, _, n in cubos) or 1
    partes = _marco(
        w, h, "dist",
        f"Distribución del tipo de IBI urbano en {len(tipos)} municipios, ejercicio {ejercicio}",
        f"Histograma. El eje horizontal recorre la horquilla legal del IBI urbano, del "
        f"0,40% al 1,10%, en tramos de una décima. El tramo más poblado reúne "
        f"{vmax} de los {len(tipos)} municipios analizados.",
        f"Dónde se sitúan los {len(tipos)} municipios dentro de la horquilla legal",
        f"Tipo de IBI urbano, ejercicio {ejercicio}. La ley permite del 0,40% al 1,10% "
        f"(art. 72.1 TRLRHL).",
    )
    partes.append(f'<line x1="{izq}" y1="{base}" x2="{w - 34}" y2="{base}" stroke="{INK}"/>')
    for frac in (0.5, 1.0):
        y = base - alto * frac
        partes.append(
            f'<line x1="{izq}" y1="{y:.0f}" x2="{w - 34}" y2="{y:.0f}" stroke="{RULE}" '
            f'stroke-dasharray="3 4"/>'
        )
        partes.append(
            f'<text x="{izq - 8}" y="{y + 4:.0f}" font-size="11.5" fill="{MID}" '
            f'text-anchor="end">{int(vmax * frac)}</text>'
        )
    for i, (desde, hasta, n) in enumerate(cubos):
        x = izq + i * ancho
        altura = alto * n / vmax
        color = ACCENT if n == vmax else ACCENT2
        partes.append(
            f'<rect x="{x + 8:.0f}" y="{base - altura:.0f}" width="{ancho - 16:.0f}" '
            f'height="{altura:.0f}" fill="{color}"/>'
        )
        partes.append(
            f'<text x="{x + ancho / 2:.0f}" y="{base - altura - 8:.0f}" font-size="13" '
            f'font-weight="700" fill="{INK}" text-anchor="middle">{n}</text>'
        )
        partes.append(
            f'<text x="{x + ancho / 2:.0f}" y="{base + 20:.0f}" font-size="12" '
            f'fill="{INK}" text-anchor="middle">{pct(desde)}</text>'
        )
        partes.append(
            f'<text x="{x + ancho / 2:.0f}" y="{base + 36:.0f}" font-size="11" '
            f'fill="{MID}" text-anchor="middle">a {pct(hasta)}</text>'
        )
    nota = (f"Ningún municipio de la muestra baja del mínimo legal."
            if not bajo else f"{bajo} municipios por debajo del 0,40%.")
    partes.append(_pie_svg(w, h, (
        "Elaboración propia de TasasMunicipales.info con los tipos que publica el "
        f"Ministerio de Hacienda. {nota}"
    )))
    partes.append("</svg>")
    return "\n".join(partes)


def svg_ivtm_distribucion(valores: list[float], minimo: float) -> str:
    """Tarifa del IVTM de cada municipio entre el suelo legal y el doble (art. 95.4)."""
    datos = sorted(valores)
    techo = minimo * 2
    w, h = 900, 420
    base, top, izq = h - 96, 108, 78
    alto = base - top
    ancho = w - izq - 44
    ymax = max(techo, max(datos)) * 1.04
    partes = _marco(
        w, h, "ivtm",
        "Tarifa del impuesto de circulación para un turismo de 8 a 11,99 caballos "
        "fiscales en los municipios analizados",
        f"Gráfico de área. Los municipios se ordenan de la tarifa más baja a la más alta, "
        f"de {num(datos[0])} a {num(datos[-1])} euros al año. Se marcan la cuota mínima "
        f"legal de {num(minimo)} euros y el máximo que resulta de aplicar el coeficiente "
        f"2 que permite el artículo 95.4 del TRLRHL, {num(techo)} euros.",
        f"El impuesto de circulación entre el suelo y el techo legal",
        f"Turismo de 8 a 11,99 CV. Cada punto es un municipio, ordenados de menor a mayor "
        f"tarifa anual.",
    )

    def px(i: int) -> float:
        return izq + ancho * (i / max(1, len(datos) - 1))

    def py(v: float) -> float:
        return base - alto * (v / ymax)

    # bandas legales
    partes.append(
        f'<rect x="{izq}" y="{py(techo):.0f}" width="{ancho}" '
        f'height="{py(minimo) - py(techo):.0f}" fill="{ACCENT2}" opacity="0.07"/>'
    )
    for valor, etiqueta, color in ((minimo, f"Cuota mínima legal: {num(minimo)} €", ACCENT2),
                                   (techo, f"Máximo con coeficiente 2: {num(techo)} €", ACCENT)):
        y = py(valor)
        partes.append(
            f'<line x1="{izq}" y1="{y:.0f}" x2="{w - 44}" y2="{y:.0f}" stroke="{color}" '
            f'stroke-width="1.5" stroke-dasharray="5 4"/>'
        )
        partes.append(
            f'<text x="{izq + 6}" y="{y - 7:.0f}" font-size="12" font-weight="700" '
            f'fill="{color}">{html.escape(etiqueta)}</text>'
        )
    puntos = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(datos))
    partes.append(
        f'<polygon points="{izq},{base} {puntos} {izq + ancho},{base}" '
        f'fill="{INK}" opacity="0.10"/>'
    )
    partes.append(
        f'<polyline points="{puntos}" fill="none" stroke="{INK}" stroke-width="2"/>'
    )
    partes.append(f'<line x1="{izq}" y1="{base}" x2="{w - 44}" y2="{base}" stroke="{INK}"/>')
    partes.append(
        f'<text x="{izq}" y="{base + 20}" font-size="12" fill="{MID}">'
        f'más barato ({num(datos[0])} €)</text>'
    )
    partes.append(
        f'<text x="{izq + ancho}" y="{base + 20}" font-size="12" fill="{MID}" '
        f'text-anchor="end">más caro ({num(datos[-1])} €)</text>'
    )
    partes.append(
        f'<text x="{izq + ancho / 2:.0f}" y="{base + 40}" font-size="12" fill="{MID}" '
        f'text-anchor="middle">{len(datos)} municipios ordenados por tarifa</text>'
    )
    partes.append(_pie_svg(w, h, (
        "Elaboración propia de TasasMunicipales.info con las tarifas del IVTM que publica "
        "el Ministerio de Hacienda y la cuota mínima del art. 95.1 del TRLRHL."
    )))
    partes.append("</svg>")
    return "\n".join(partes)


def svg_curva_plusvalia(medianas: list[float | None]) -> str:
    """Coeficiente maximo legal frente a la mediana de lo aprobado por los municipios."""
    w, h = 900, 440
    base, top, izq = h - 92, 112, 74
    alto = base - top
    ancho = w - izq - 40
    serie = [(i, MAXIMOS_PLUSVALIA[i], medianas[i] if i < len(medianas) else None)
             for i in range(len(MAXIMOS_PLUSVALIA))]
    ymax = max(MAXIMOS_PLUSVALIA) * 1.12
    partes = _marco(
        w, h, "plus",
        "Coeficiente máximo legal de la plusvalía municipal por años de tenencia frente a "
        "la mediana de los coeficientes aprobados por los municipios analizados",
        "Gráfico de dos líneas sobre los 21 tramos de tenencia del artículo 107.4 del "
        "TRLRHL. La línea superior es el coeficiente máximo que permite la ley, con su "
        "forma de doble joroba: sube hasta el séptimo año, cae en la franja de 12 a 16 "
        "años y se dispara a 0,40 a partir de los 20. La línea inferior es la mediana de "
        "lo que tienen aprobado los municipios de la muestra.",
        "La curva legal de la plusvalía y lo que aprueban los municipios",
        "Coeficiente aplicable al valor catastral del suelo según los años transcurridos "
        "desde la compra (art. 107.4 TRLRHL).",
    )

    def px(i: int) -> float:
        return izq + ancho * (i / (len(MAXIMOS_PLUSVALIA) - 1))

    def py(v: float) -> float:
        return base - alto * (v / ymax)

    for valor in (0.10, 0.20, 0.30, 0.40):
        y = py(valor)
        partes.append(
            f'<line x1="{izq}" y1="{y:.0f}" x2="{w - 34}" y2="{y:.0f}" stroke="{RULE}" '
            f'stroke-dasharray="3 4"/>'
        )
        partes.append(
            f'<text x="{izq - 8}" y="{y + 4:.0f}" font-size="11.5" fill="{MID}" '
            f'text-anchor="end">{num(valor)}</text>'
        )
    max_pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v, _ in serie)
    partes.append(
        f'<polyline points="{max_pts}" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>'
    )
    med_pts = [(px(i), py(mv)) for i, _, mv in serie if mv is not None]
    if len(med_pts) >= 2:
        partes.append(
            '<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in med_pts)
            + f'" fill="none" stroke="{ACCENT2}" stroke-width="2.5" '
              f'stroke-dasharray="6 4"/>'
        )
    for i, v, _ in serie:
        partes.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="3" fill="{ACCENT}"/>')
    for i in (0, 6, 12, 20):
        partes.append(
            f'<text x="{px(i):.0f}" y="{base + 20}" font-size="12" fill="{INK}" '
            f'text-anchor="middle">{html.escape(PERIODOS[i])}</text>'
        )
    partes.append(f'<line x1="{izq}" y1="{base}" x2="{w - 34}" y2="{base}" stroke="{INK}"/>')
    partes.append(f'<rect x="24" y="76" width="13" height="13" fill="{ACCENT}"/>')
    partes.append(
        f'<text x="43" y="87" font-size="12.5" fill="{INK}">Máximo legal (art. 107.4)</text>'
    )
    if med_pts:
        partes.append(f'<rect x="238" y="76" width="13" height="13" fill="{ACCENT2}"/>')
        partes.append(
            f'<text x="257" y="87" font-size="12.5" fill="{INK}">Mediana de los '
            f'municipios analizados</text>'
        )
    partes.append(_pie_svg(w, h, (
        "Elaboración propia de TasasMunicipales.info. Máximos: texto consolidado del "
        "TRLRHL en el BOE. Coeficientes municipales: Ministerio de Hacienda."
    )))
    partes.append("</svg>")
    return "\n".join(partes)


def svg_valores_vs_tipo(puntos: list[tuple[int, float, str]]) -> str:
    """Dispersion ano de los valores catastrales (x) frente a tipo de IBI (y)."""
    w, h = 900, 470
    base, top, izq = h - 92, 108, 74
    alto, ancho = base - top, w - izq - 44
    anos = [a for a, _, _ in puntos]
    tipos = [t for _, t, _ in puntos]
    x0, x1 = min(anos) - 1, max(anos) + 1
    y0, y1 = 0.35, max(1.10, max(tipos) + 0.05)
    partes = _marco(
        w, h, "disp",
        "Relación entre el año de los valores catastrales y el tipo de IBI urbano de cada "
        "municipio",
        f"Gráfico de dispersión con {len(puntos)} municipios. El eje horizontal es el año "
        f"de la última valoración catastral vigente ({min(anos)} a {max(anos)}) y el "
        f"vertical el tipo de IBI urbano. Los puntos se reparten por todo el gráfico: no "
        f"hay una relación clara entre tener valores antiguos y aplicar un tipo más alto.",
        "Valores catastrales antiguos y tipos altos no van de la mano",
        "Cada punto es un municipio. Naranja: valoraciones anteriores a 2010.",
    )

    def px(a: float) -> float:
        return izq + ancho * (a - x0) / (x1 - x0)

    def py(t: float) -> float:
        return base - alto * (t - y0) / (y1 - y0)

    for t in (0.4, 0.6, 0.8, 1.0):
        y = py(t)
        partes.append(
            f'<line x1="{izq}" y1="{y:.0f}" x2="{w - 44}" y2="{y:.0f}" stroke="{RULE}" '
            f'stroke-dasharray="3 4"/>'
        )
        partes.append(
            f'<text x="{izq - 8}" y="{y + 4:.0f}" font-size="11.5" fill="{MID}" '
            f'text-anchor="end">{pct(t)}</text>'
        )
    for ano in range(((x0 // 5) + 1) * 5, int(x1) + 1, 5):
        x = px(ano)
        partes.append(
            f'<text x="{x:.0f}" y="{base + 20}" font-size="11.5" fill="{MID}" '
            f'text-anchor="middle">{ano}</text>'
        )
    for ano, tipo, nombre in puntos:
        color = ACCENT if ano < 2010 else ACCENT2
        partes.append(
            f'<circle cx="{px(ano):.1f}" cy="{py(tipo):.1f}" r="4.5" fill="{color}" '
            f'opacity="0.72"><title>{html.escape(nombre)}: {pct(tipo)}, valores de '
            f'{ano}</title></circle>'
        )
    partes.append(f'<line x1="{izq}" y1="{base}" x2="{w - 44}" y2="{base}" stroke="{INK}"/>')
    partes.append(
        f'<text x="{izq + ancho / 2:.0f}" y="{base + 40}" font-size="12" fill="{MID}" '
        f'text-anchor="middle">Año de entrada en vigor de los valores catastrales</text>'
    )
    partes.append(_pie_svg(w, h, (
        "Elaboración propia de TasasMunicipales.info con el tipo de IBI urbano y el año de "
        "los valores catastrales que publica el Ministerio de Hacienda."
    )))
    partes.append("</svg>")
    return "\n".join(partes)


def svg_medianas_ccaa(datos: list[tuple[str, int, float]]) -> str:
    """Mediana del tipo de IBI urbano por comunidad autonoma."""
    w = 900
    fila = 34
    top, izq, der = 112, 210, 96
    h = top + fila * len(datos) + 74
    ancho = w - izq - der
    vmax = max(v for _, _, v in datos)
    partes = _marco(
        w, h, "ccaa",
        "Mediana del tipo de IBI urbano por comunidad autónoma en los municipios "
        "analizados",
        "Gráfico de barras horizontales. Cada barra es la mediana del tipo de IBI urbano "
        "de los municipios que la guía cubre en esa comunidad autónoma, con el número de "
        "municipios entre paréntesis. El IBI es un tributo municipal: la comunidad "
        "autónoma no fija el tipo.",
        "Mediana del tipo de IBI urbano por comunidad",
        "El IBI lo fija cada ayuntamiento; las diferencias entre comunidades reflejan la "
        "muestra, no una regulación autonómica.",
    )
    for i, (nombre, n, valor) in enumerate(datos):
        y = top + i * fila
        largo = max(10, ancho * valor / vmax * 0.97)
        color = ACCENT if i == 0 or i == len(datos) - 1 else ACCENT2
        partes.append(
            f'<text x="{izq - 10}" y="{y + 15}" font-size="13" fill="{INK}" '
            f'text-anchor="end">{html.escape(nombre)}</text>'
        )
        partes.append(
            f'<rect x="{izq}" y="{y}" width="{largo:.0f}" height="21" rx="2" fill="{color}"/>'
        )
        partes.append(
            f'<text x="{izq + largo + 8:.0f}" y="{y + 15}" font-size="12.5" '
            f'font-weight="700" fill="{INK}">{pct(valor)}</text>'
        )
        partes.append(
            f'<text x="{izq + largo + 62:.0f}" y="{y + 15}" font-size="11.5" fill="{MID}">'
            f'{n} municipios</text>'
        )
    partes.append(
        f'<line x1="{izq}" y1="{top - 14}" x2="{w - der + 6}" y2="{top - 14}" '
        f'stroke="{RULE}"/>'
    )
    partes.append(_pie_svg(w, h, (
        "Elaboración propia de TasasMunicipales.info con los tipos del Ministerio de "
        "Hacienda. La muestra tiene sesgo hacia los municipios más poblados."
    )))
    partes.append("</svg>")
    return "\n".join(partes)


def articulo(slug: str, title: str, description: str, h1: str, lead: str,
             cuerpo: str, *, ordenable: bool = False,
             seccion: str = "Análisis") -> None:
    canonical = f"{SITE}/analisis/{slug}/" if slug else f"{SITE}/analisis/"
    prefix = PREFIX if slug else "../"
    if not slug:
        cuerpo = cuerpo.replace(PREFIX, prefix)
        lead = lead.replace(PREFIX, prefix)
        migas = (
            f'<div class="bc"><a href="{prefix}">Inicio</a><span>›</span>'
            f'<strong>Análisis</strong></div>'
        )
    else:
        migas = (
            f'<div class="bc"><a href="{prefix}">Inicio</a><span>›</span>'
            f'<a href="{prefix}analisis/">Análisis</a><span>›</span>'
            f'<strong>{html.escape(seccion)}</strong></div>'
        )
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": canonical,
            "inLanguage": "es-ES",
            "author": {"@type": "Person", "name": AUTOR},
            "publisher": {"@type": "Organization", "name": "TasasMunicipales.info"},
            "datePublished": TODAY,
            "dateModified": TODAY,
            "isBasedOn": HACIENDA,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Análisis",
                 "item": f"{SITE}/analisis/"},
                {"@type": "ListItem", "position": 3, "name": seccion, "item": canonical},
            ],
        },
    ]
    bloque = "".join(
        '<script type="application/ld+json">\n'
        + json.dumps(s, ensure_ascii=False, indent=1) + "\n</script>\n"
        for s in schema
    )
    pagina = (
        tp.head_block(title, description, canonical, prefix)
        + migas
        + '<div class="wrap">\n'
        + f"  <h1>{h1}</h1>\n"
        + f'  <p class="lead">{lead}</p>\n'
        + f'  <p style="font-size:.85rem;color:var(--mid)">Por {AUTOR} · '
          f'Actualizado el {bx.HOY_ES} · '
          f'<a href="{prefix}metodologia/">Metodología y fuentes</a></p>\n'
        + cuerpo
        + "</div>\n"
        + (tp.SORT_SCRIPT if ordenable else "")
        + bloque
        + tp.footer_block(prefix)
    )
    rel = f"analisis/{slug}" if slug else "analisis"
    destino = ROOT / rel / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    palabras = len(tp.strip_tags(pagina.split("<footer>")[0]).split())
    print(f"  /{rel}/  ({palabras} palabras)")


# ─────────────────────── 1. ranking del IBI ───────────────────────

def ranking_ibi() -> None:
    ms = sorted(municipios(), key=lambda m: -m["oficial_tipo_urbana"])
    tipos = [m["oficial_tipo_urbana"] for m in ms]
    ejercicio = ms[0].get("oficial_ejercicio", "2025")
    media, mediana = statistics.mean(tipos), statistics.median(tipos)
    caro, barato = ms[0], ms[-1]
    brecha = REF_VC * (caro["oficial_tipo_urbana"] - barato["oficial_tipo_urbana"]) / 100

    # reparto por tramos
    tramos = [(0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.11)]
    reparto = []
    for desde, hasta in tramos:
        n = sum(1 for t in tipos if desde <= t < hasta)
        reparto.append(
            f'            <tr><td>{"Hasta " + pct(hasta) if not desde else pct(desde) + " – " + pct(min(hasta, 1.10))}</td>'
            f'<td class="v">{n}</td><td>{num(100 * n / len(tipos), 1)}%</td></tr>'
        )

    # medianas por comunidad
    por_ccaa: dict[str, list[float]] = defaultdict(list)
    for m in ms:
        por_ccaa[ccaa_nombre(m)].append(m["oficial_tipo_urbana"])
    filas_ccaa = "\n".join(
        f'            <tr><td>{c}</td><td class="v">{len(v)}</td>'
        f'<td>{pct(statistics.median(v))}</td>'
        f'<td>{euros(REF_VC * statistics.median(v) / 100)}</td></tr>'
        for c, v in sorted(por_ccaa.items(), key=lambda kv: -statistics.median(kv[1]))
    )

    def tabla_extremos(lista: list[dict], desc: bool) -> str:
        filas = []
        for i, m in enumerate(lista, 1):
            puesto = i if desc else len(ms) - len(lista) + i
            cuota = REF_VC * m["oficial_tipo_urbana"] / 100
            filas.append(
                f'            <tr><td>{puesto}</td><td>{enlace(m)}</td>'
                f'<td>{html.escape(m.get("provincia") or "—")}</td>'
                f'<td class="v">{pct(m["oficial_tipo_urbana"])}</td>'
                f'<td>{euros(cuota)}</td></tr>'
            )
        return (
            '        <table class="dt">\n'
            '          <thead><tr><th>#</th><th>Municipio</th><th>Provincia</th>'
            f'<th>Tipo urbano</th><th>Cuota con VC de {euros(REF_VC)}</th></tr></thead>\n'
            '          <tbody>\n' + "\n".join(filas) + "\n          </tbody>\n"
            '        </table>'
        )

    # subidas y bajadas respecto al ejercicio anterior
    subidas = [m for m in ms if m.get("oficial_tipo_urbana_anterior")
               and m["oficial_tipo_urbana"] > m["oficial_tipo_urbana_anterior"]]
    bajadas = [m for m in ms if m.get("oficial_tipo_urbana_anterior")
               and m["oficial_tipo_urbana"] < m["oficial_tipo_urbana_anterior"]]
    ej_ant = ms[0].get("oficial_ejercicio_anterior", "2024")
    detalle_cambios = ""
    if subidas or bajadas:
        filas = []
        for m in sorted(subidas + bajadas,
                        key=lambda x: -abs(x["oficial_tipo_urbana"]
                                           - x["oficial_tipo_urbana_anterior"])):
            ant = m["oficial_tipo_urbana_anterior"]
            act = m["oficial_tipo_urbana"]
            signo = "Sube" if act > ant else "Baja"
            filas.append(
                f'            <tr><td>{enlace(m)}</td><td>{pct(ant)}</td>'
                f'<td class="v">{pct(act)}</td><td>{signo} '
                f'{num(abs(act - ant), 3)} puntos</td></tr>'
            )
        detalle_cambios = (
            '    <table class="dt">\n'
            f'      <thead><tr><th>Municipio</th><th>{ej_ant}</th><th>{ejercicio}</th>'
            '<th>Variación</th></tr></thead>\n'
            '      <tbody>\n' + "\n".join(filas) + "\n      </tbody>\n    </table>"
        )

    figura_dist = guarda_svg(
        "analisis-distribucion-tipos-ibi.svg",
        svg_distribucion_tipos(tipos, ejercicio),
        f"Histograma de los tipos de IBI urbano de {len(ms)} municipios dentro de la "
        f"horquilla legal del 0,40% al 1,10%",
        f"Reparto de los {len(ms)} municipios por tramos de tipo de IBI urbano, ejercicio "
        f"{ejercicio}. Gráfico propio con los datos de esta página.",
        lazy=False,
    )

    cuerpo = f"""  <section class="sec">
    <h2 id="resumen">Lo que dicen los datos</h2>
    <p>Hemos normalizado el tipo de gravamen del IBI urbano de <strong>{len(ms)} municipios</strong> tal y como lo publica el Ministerio de Hacienda para el ejercicio <strong>{ejercicio}</strong>. El resultado: la mediana está en el <strong>{pct(mediana)}</strong> y la media en el {pct(media)}.</p>
    <p>Entre el municipio con el tipo más alto ({enlace(caro)}, {pct(caro['oficial_tipo_urbana'])}) y el más bajo ({enlace(barato)}, {pct(barato['oficial_tipo_urbana'])}) hay <strong>{num(caro['oficial_tipo_urbana'] - barato['oficial_tipo_urbana'], 3)} puntos</strong>. Traducido: por un inmueble con el mismo valor catastral de {euros(REF_VC)}, la diferencia es de <strong>{euros(brecha)} al año</strong>.</p>
    <p>La comparación del tipo tiene un límite importante que conviene decir antes de seguir: <strong>un tipo alto no significa un recibo alto</strong>. La cuota es valor catastral × tipo, y el valor catastral depende de cuándo hizo el municipio su última valoración colectiva. Un ayuntamiento con valores de 1996 puede aplicar un tipo del 0,9% y cobrar menos que otro con valores de 2015 al 0,5%. Lo analizamos en <a href="{PREFIX}analisis/valores-catastrales-antiguos/">el artículo sobre la antigüedad de las ponencias catastrales</a>.</p>
{figura_dist}
    <p>El gráfico deja ver algo que las tablas esconden: los municipios no se reparten por igual dentro de la horquilla legal. Se concentran en la mitad baja, y el techo del 1,10% queda muy lejos incluso para el más gravado de la muestra. Es decir, casi todos los ayuntamientos conservan margen para subir el tipo sin necesidad de ninguna reforma estatal.</p>
  </section>

  <section class="sec">
    <h2 id="mas-caros">Los 15 municipios con el tipo de IBI más alto</h2>
{tabla_extremos(ms[:15], True)}
  </section>

  <section class="sec">
    <h2 id="mas-baratos">Los 15 municipios con el tipo de IBI más bajo</h2>
{tabla_extremos(ms[-15:], False)}
    <p>El suelo legal está en el <strong>0,40%</strong> para urbana (art. 72.1 del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a>), así que los municipios que aparecen con ese tipo exacto están aplicando el mínimo que la ley les permite.</p>
  </section>

  <section class="sec">
    <h2 id="reparto">Cómo se reparten los {len(ms)} municipios</h2>
    <table class="dt">
      <thead><tr><th>Tramo de tipo urbano</th><th>Municipios</th><th>% del total</th></tr></thead>
      <tbody>
{chr(10).join(reparto)}
      </tbody>
    </table>
    <p>La horquilla legal para urbana va del 0,40% al 1,10%. El tipo más alto de la muestra es el {pct(caro['oficial_tipo_urbana'])} de {enlace(caro)}, todavía {num(1.10 - caro['oficial_tipo_urbana'], 3)} puntos por debajo del techo, y {sum(1 for t in tipos if abs(t - 0.40) < 1e-9)} municipios aplican exactamente el mínimo del 0,40%. El margen que la ley deja sin usar es amplio: por eso las subidas de IBI se pueden aprobar en el pleno sin tocar la ley estatal.</p>
  </section>

  <section class="sec">
    <h2 id="por-comunidad">Mediana por comunidad autónoma</h2>
    <p>El IBI es un impuesto municipal: la comunidad autónoma no lo regula. Aun así, las medianas por territorio son distintas porque también lo son el tamaño de los municipios de la muestra y la antigüedad de sus valores catastrales.</p>
    <table class="dt">
      <thead><tr><th>Comunidad</th><th>Municipios analizados</th><th>Mediana del tipo</th><th>Cuota con VC de {euros(REF_VC)}</th></tr></thead>
      <tbody>
{filas_ccaa}
      </tbody>
    </table>
    <p style="font-size:.85rem;color:var(--mid)">La muestra no es representativa del total de municipios de cada comunidad: recoge los que tienen ficha en esta guía, con sesgo hacia los más poblados.</p>
  </section>

  <section class="sec">
    <h2 id="cambios">Quién ha cambiado el tipo entre {ej_ant} y {ejercicio}</h2>
    <p>De los {len(ms)} municipios, <strong>{len(subidas)} han subido</strong> el tipo y <strong>{len(bajadas)} lo han bajado</strong>; los {len(ms) - len(subidas) - len(bajadas)} restantes lo mantienen igual.</p>
{detalle_cambios}
  </section>

  <section class="sec">
    <h2 id="fuentes">Metodología y fuentes</h2>
    <p>Los tipos proceden de la <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a> del Ministerio de Hacienda, que recoge lo aprobado en la ordenanza fiscal de cada ayuntamiento. Es la única fuente estatal que publica el dato municipio a municipio y ejercicio a ejercicio, y el último disponible es {ejercicio}.</p>
    <p>La «cuota con VC de {euros(REF_VC)}» es un cálculo nuestro para comparar en igualdad de condiciones: tipo × {euros(REF_VC)}. Es la cuota <em>íntegra</em>, sin bonificaciones ni recargos. Para tu caso concreto usa la <a href="{PREFIX}calculadora-ibi/">calculadora con tu valor catastral</a>.</p>
    <p>Si un pleno ha modificado el tipo para {int(ejercicio) + 1}, el cambio aparece antes en la ordenanza municipal que en la estadística estatal. En la ficha de cada municipio enlazamos su organismo de recaudación para comprobarlo.</p>
    <p><a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Ver la tabla completa y ordenable de los {len(ms)} municipios →</a></p>
  </section>
"""
    articulo(
        "ranking-ibi-municipios",
        f"¿Dónde se paga más IBI? Ranking de {len(ms)} municipios",
        f"Ranking del tipo de IBI urbano en {len(ms)} municipios con datos oficiales del "
        f"Ministerio de Hacienda ({ejercicio}): del {pct(barato['oficial_tipo_urbana'])} de "
        f"{barato['nombre']} al {pct(caro['oficial_tipo_urbana'])} de {caro['nombre']}, "
        f"{euros(brecha)} de diferencia al año por el mismo inmueble.",
        f"¿Dónde se paga más IBI? Ranking de {len(ms)} municipios",
        f"Entre el municipio que más grava y el que menos hay <strong>{euros(brecha)} al año</strong> "
        f"de diferencia por un inmueble con el mismo valor catastral. Análisis del tipo de gravamen "
        f"oficial de {len(ms)} municipios, ejercicio {ejercicio}.",
        cuerpo,
        seccion="Ranking del IBI",
    )


# ─────────────────────── 2. IVTM ───────────────────────

def ivtm() -> None:
    ms = municipios()
    imps = impuestos()
    datos = []
    for m in ms:
        imp = imps.get(m.get("oficial_codigo_ine") or "")
        if not imp:
            continue
        c = imp.get("conceptos", {})
        fila = {
            "m": m,
            "turismo_bajo": to_float((c.get("C18") or {}).get("valor")),
            "turismo_medio": to_float((c.get("C19") or {}).get("valor")),
            "turismo_alto": to_float((c.get("C20") or {}).get("valor")),
            "ciclomotor": to_float((c.get("C36") or {}).get("valor")),
            "moto_grande": to_float((c.get("C41") or {}).get("valor")),
            "ejercicio": imp.get("ejercicio", "2025"),
        }
        if fila["turismo_medio"] is not None:
            datos.append(fila)
    datos.sort(key=lambda f: -f["turismo_medio"])
    ejercicio = datos[0]["ejercicio"]
    medios = [f["turismo_medio"] for f in datos]
    mediana = statistics.median(medios)
    caro, barato = datos[0], datos[-1]
    # Cuota mínima legal del art. 95.1 TRLRHL para 8-11,99 CV
    MINIMO_LEGAL = 34.08

    filas = "\n".join(
        f'            <tr>'
        f'<td data-sort="{html.escape(f["m"]["nombre"])}">{enlace(f["m"])}</td>'
        f'<td data-sort="{html.escape(f["m"].get("provincia") or "")}">'
        f'{html.escape(f["m"].get("provincia") or "—")}</td>'
        f'<td data-sort="{f["turismo_bajo"] or 0}">'
        f'{num(f["turismo_bajo"]) + " €" if f["turismo_bajo"] else "—"}</td>'
        f'<td data-sort="{f["turismo_medio"]}" class="v">{num(f["turismo_medio"])} €</td>'
        f'<td data-sort="{f["turismo_alto"] or 0}">'
        f'{num(f["turismo_alto"]) + " €" if f["turismo_alto"] else "—"}</td>'
        f'<td data-sort="{f["ciclomotor"] or 0}">'
        f'{num(f["ciclomotor"]) + " €" if f["ciclomotor"] else "—"}</td>'
        f'<td data-sort="{f["moto_grande"] or 0}">'
        f'{num(f["moto_grande"]) + " €" if f["moto_grande"] else "—"}</td>'
        f'</tr>'
        for f in datos
    )
    en_minimo = [f for f in datos if abs(f["turismo_medio"] - MINIMO_LEGAL) < 0.6]
    coeficiente_max = max(medios) / MINIMO_LEGAL
    figura_ivtm = guarda_svg(
        "analisis-ivtm-horquilla.svg",
        svg_ivtm_distribucion(medios, MINIMO_LEGAL),
        f"Gráfico de la tarifa del impuesto de circulación de un turismo de 8 a 11,99 CV en "
        f"{len(datos)} municipios, entre la cuota mínima legal y el doble",
        f"Tarifa anual del IVTM para un turismo de 8 a 11,99 CV en los {len(datos)} "
        f"municipios analizados, ordenados de menor a mayor. Gráfico propio con los datos de "
        f"esta página.",
        lazy=False,
    )

    cuerpo = f"""  <section class="sec">
    <h2 id="resumen">Un mismo coche, {num(min(medios))} € o {num(max(medios))} € según dónde lo matricules</h2>
    <p>El impuesto de vehículos de tracción mecánica (IVTM), el «impuesto de circulación», lo cobra el ayuntamiento donde consta tu domicilio, y cada uno fija su propia tarifa. La ley (art. 95 del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a>) establece unas <strong>cuotas mínimas</strong> y permite multiplicarlas por un coeficiente de hasta <strong>2</strong>.</p>
    <p>Para el turismo más común, el de <strong>8 a 11,99 caballos fiscales</strong>, la cuota mínima legal es de {num(MINIMO_LEGAL)} €. En los {len(datos)} municipios analizados la mediana es de <strong>{num(mediana)} €</strong>, el más barato cobra {num(barato['turismo_medio'])} € ({enlace(barato['m'])}) y el más caro {num(caro['turismo_medio'])} € ({enlace(caro['m'])}). El más caro aplica un coeficiente de <strong>{num(coeficiente_max)}</strong> sobre el mínimo: prácticamente el techo legal.</p>
    <p>{len(en_minimo)} de los {len(datos)} municipios cobran la <strong>cuota mínima legal o algo muy próximo</strong>, es decir, renuncian a subir este impuesto.</p>
{figura_ivtm}
    <p>El gráfico ordena los {len(datos)} municipios de la tarifa más baja a la más alta y sitúa las dos referencias que fija la ley: el suelo de {num(MINIMO_LEGAL)} € y el techo de {num(MINIMO_LEGAL * 2)} € que resulta de aplicar el coeficiente máximo. La curva sube de forma escalonada, sin saltos bruscos, y ningún municipio se sale de la banda legal: la variación no viene de fórmulas distintas, sino de la decisión política de cada pleno sobre un único número.</p>
  </section>

  <section class="sec">
    <h2 id="tabla">Tarifa del IVTM municipio a municipio ({ejercicio})</h2>
    <p>Pulsa en cualquier encabezado para ordenar. Los importes son la cuota anual por vehículo antes de exenciones y bonificaciones (vehículos históricos, personas con discapacidad, vehículos menos contaminantes: cada ordenanza las regula por su cuenta).</p>
    <div class="table-scroll">
      <table class="dt sortable">
        <thead>
          <tr>
            <th data-col="0">Municipio</th>
            <th data-col="1">Provincia</th>
            <th data-col="2">Turismo &lt;8 CV</th>
            <th data-col="3">Turismo 8–11,99 CV</th>
            <th data-col="4">Turismo 12–15,99 CV</th>
            <th data-col="5">Ciclomotor</th>
            <th data-col="6">Moto &gt;1.000 cc</th>
          </tr>
        </thead>
        <tbody>
{filas}
        </tbody>
      </table>
    </div>
  </section>

  <section class="sec">
    <h2 id="como-funciona">Cómo se calcula el IVTM y por qué varía tanto</h2>
    <p>El IVTM no se calcula sobre el valor del coche ni sobre sus emisiones: se calcula sobre la <strong>potencia fiscal</strong> (caballos fiscales, un dato que figura en la ficha técnica) en el caso de los turismos, sobre las plazas en autobuses, sobre la carga útil en camiones y remolques, y sobre la cilindrada en motocicletas.</p>
    <p>La ley fija una tabla de cuotas mínimas y deja que cada ayuntamiento la multiplique por un coeficiente que no puede pasar de 2. De ahí sale toda la variación: no hay diferencias de método, solo de coeficiente. Por eso la comparación entre municipios es limpia, a diferencia del IBI, donde el valor catastral distorsiona cualquier ranking de tipos.</p>
    <h3>Quién paga y cuándo</h3>
    <p>Paga quien figura como titular en el permiso de circulación a 1 de enero. Si vendes el coche en febrero, el recibo de ese año es tuyo. La cuota <strong>solo se prorratea por trimestres</strong> en la primera adquisición, en la baja definitiva y en la baja temporal por sustracción o robo (art. 96.3 del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a>).</p>
    <p>El municipio que cobra es el del <strong>domicilio que consta en el permiso de circulación</strong>, no el de residencia real. Cambiar el domicilio del permiso es un trámite de la DGT, y es lo que determina qué tarifa te aplican.</p>
  </section>

  <section class="sec">
    <h2 id="fuentes">Metodología y fuentes</h2>
    <p>Las tarifas proceden de la <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a> del Ministerio de Hacienda, que publica las 24 tarifas del IVTM aprobadas por cada ayuntamiento en el ejercicio {ejercicio}. Las cuotas mínimas legales están en el art. 95.1 del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a>.</p>
    <p>Lo que esta consulta <strong>no</strong> recoge son las exenciones y bonificaciones de cada ordenanza, que en el IVTM son relevantes (vehículos eléctricos, híbridos, históricos y adaptados). Para eso hay que leer la ordenanza fiscal del municipio: en cada ficha enlazamos su organismo de recaudación.</p>
    <p>En la ficha de cada municipio publicamos su tarifa completa, con camiones, autobuses, tractores y remolques. <a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio →</a> · <a href="{PREFIX}impuesto-circulacion/">Guía del impuesto de circulación: exenciones, bonificaciones y prorrateo →</a></p>
  </section>
"""
    articulo(
        "impuesto-circulacion-ivtm",
        f"Impuesto de circulación: el IVTM en {len(datos)} municipios",
        f"Cuánto cuesta el IVTM en {len(datos)} municipios con datos oficiales del Ministerio "
        f"de Hacienda: de {num(barato['turismo_medio'])} € a {num(caro['turismo_medio'])} € por "
        f"el mismo turismo de 8 a 11,99 CV. Tabla ordenable con turismos, ciclomotores y motos.",
        f"Impuesto de circulación: lo que cuesta el IVTM en {len(datos)} municipios",
        f"Por el mismo turismo de 8 a 11,99 CV, un ayuntamiento cobra {num(barato['turismo_medio'])} € "
        f"y otro {num(caro['turismo_medio'])} €. Comparativa de la tarifa oficial del IVTM en "
        f"{len(datos)} municipios, ejercicio {ejercicio}.",
        cuerpo,
        ordenable=True,
        seccion="Comparativa del IVTM",
    )


# ─────────────────────── 3. coeficientes de plusvalía ───────────────────────

def plusvalia() -> None:
    ms = municipios()
    imps = impuestos()
    con_datos, sin_datos, incoherentes = [], [], []
    for m in ms:
        imp = imps.get(m.get("oficial_codigo_ine") or "")
        c = (imp or {}).get("conceptos", {})
        coefs = [to_float((c.get(f"C{n}") or {}).get("valor")) for n in range(51, 72)]
        tipos = [to_float((c.get(f"C{n}") or {}).get("valor")) for n in range(72, 93)]
        if not any(x is not None for x in coefs):
            sin_datos.append(m)
            continue
        if not serie_plausible(coefs):
            incoherentes.append(m)
            continue
        aplica_max = all(
            x is not None and abs(x - mx) < 1e-9
            for x, mx in zip(coefs, MAXIMOS_PLUSVALIA)
        )
        validos = [t for t in tipos if t is not None]
        con_datos.append({
            "m": m, "coefs": coefs, "tipos": tipos, "max": aplica_max,
            "tipo_max": max(validos) if validos else None,
            "tipo_min": min(validos) if validos else None,
            "ejercicio": (imp or {}).get("ejercicio", "2025"),
        })

    ejercicio = con_datos[0]["ejercicio"]
    en_maximo = [d for d in con_datos if d["max"]]
    tipos_max = [d["tipo_max"] for d in con_datos if d["tipo_max"] is not None]
    al_30 = [d for d in con_datos if d["tipo_max"] is not None and abs(d["tipo_max"] - 30) < 1e-9]
    mediana_tipo = statistics.median(tipos_max)
    planos = [d for d in con_datos
              if d["tipo_max"] is not None and d["tipo_min"] is not None
              and abs(d["tipo_max"] - d["tipo_min"]) < 1e-9]

    # ejemplo comparado con 10 años de tenencia
    suelo = 30000
    ejemplos = []
    for d in con_datos:
        coef, tipo = d["coefs"][10], d["tipos"][10]
        if coef and tipo:
            ejemplos.append((suelo * coef * tipo / 100, d["m"], coef, tipo))
    ejemplos.sort(key=lambda e: -e[0])
    filas_ejemplo = "\n".join(
        f'            <tr><td>{enlace(m)}</td><td>{num(coef, 2)}</td>'
        f'<td>{pct(tipo)}</td><td class="v">{euros(cuota)}</td></tr>'
        for cuota, m, coef, tipo in ejemplos[:10] + ejemplos[-10:]
    )

    filas_tipos = "\n".join(
        f'            <tr><td>{pct(t)}</td><td class="v">{n}</td></tr>'
        for t, n in sorted(Counter(tipos_max).items(), key=lambda kv: -kv[0])
    )

    filas_max = "\n".join(
        f'            <tr><td>{PERIODOS[i]}</td><td class="v">{num(MAXIMOS_PLUSVALIA[i], 2)}</td></tr>'
        for i in range(len(PERIODOS))
    )

    escalonados = [d for d in con_datos if d not in planos
                   and d["tipo_max"] is not None and d["tipo_min"] is not None]
    escalonados.sort(key=lambda d: -(d["tipo_max"] - d["tipo_min"]))
    filas_escalonados = "\n".join(
        f'            <tr><td>{enlace(d["m"])}</td><td>{pct(d["tipo_min"])}</td>'
        f'<td class="v">{pct(d["tipo_max"])}</td>'
        f'<td>{num(d["tipo_max"] - d["tipo_min"], 2)} puntos</td></tr>'
        for d in escalonados
    ) or '            <tr><td colspan="4">Ninguno en la muestra.</td></tr>'

    # Mediana, tramo a tramo, de los coeficientes realmente aprobados.
    medianas_coef: list[float | None] = []
    for i in range(len(MAXIMOS_PLUSVALIA)):
        serie = [d["coefs"][i] for d in con_datos if d["coefs"][i] is not None]
        medianas_coef.append(statistics.median(serie) if serie else None)
    figura_plus = guarda_svg(
        "analisis-curva-plusvalia.svg",
        svg_curva_plusvalia(medianas_coef),
        "Gráfico de líneas con el coeficiente máximo legal de la plusvalía municipal por "
        "años de tenencia y la mediana de los coeficientes aprobados por los municipios",
        f"Coeficientes del art. 107.4 del TRLRHL frente a la mediana de lo aprobado en los "
        f"{len(con_datos)} municipios con dato. Gráfico propio con los datos de esta página.",
        lazy=False,
    )

    sin_lista = ", ".join(enlace(m) for m in sin_datos) if sin_datos else "ninguno"
    nombres_inc = [enlace(m) for m in incoherentes]
    inc_lista = (" y ".join(nombres_inc) if len(nombres_inc) <= 2
                 else ", ".join(nombres_inc[:-1]) + " y " + nombres_inc[-1])
    parrafo_inc = (
        f'    <p><strong>Dos series que hemos descartado.</strong> {inc_lista} '
        f'aparecen en la consulta con coeficientes de entre 0,01 y 0,04, muy por debajo '
        f'de cualquier máximo legal. Todo apunta a que siguen declarando el '
        f'<em>porcentaje anual</em> del sistema anterior al RDL 26/2021 en lugar de los '
        f'coeficientes actuales. Reproducirlos como si fueran coeficientes daría una '
        f'cuota falsa, así que en sus fichas lo advertimos y remitimos a la ordenanza.</p>'
        if incoherentes else ""
    )

    cuerpo = f"""  <section class="sec">
    <h2 id="resumen">Qué hemos encontrado</h2>
    <p>Desde que el Tribunal Constitucional anuló el método de cálculo anterior (sentencia 182/2021) y el Real Decreto-ley 26/2021 lo reformó, la base imponible de la plusvalía municipal por el método objetivo se obtiene multiplicando el <strong>valor catastral del suelo</strong> por un <strong>coeficiente</strong> que depende de los años transcurridos. La ley fija unos coeficientes máximos y cada ayuntamiento puede aprobar los suyos por debajo.</p>
    <p>La pregunta práctica es: ¿los aplica al máximo? Hemos comparado los coeficientes reales de <strong>{len(con_datos)} municipios</strong> con los máximos del art. 107.4 del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a>. Resultado: <strong>{len(en_maximo)} de {len(con_datos)}</strong> ({num(100 * len(en_maximo) / len(con_datos), 1)}%) aplican exactamente los máximos legales en los 21 tramos.</p>
    <p>En el tipo de gravamen, el techo legal es el <strong>30%</strong> (art. 108.1 TRLRHL). La mediana de los municipios analizados está en el <strong>{pct(mediana_tipo)}</strong> y <strong>{len(al_30)}</strong> aplican el 30% máximo. {len(planos)} de ellos usan un <strong>tipo único</strong> para todos los períodos de tenencia, en lugar de escalonarlo.</p>
{figura_plus}
    <p>La forma de la curva legal explica bastante del impuesto. El coeficiente sube hasta el séptimo año, cae en la franja de los 12 a los 16 años —los años del pinchazo inmobiliario, cuando comprar salió caro y vender no dio beneficio— y se dispara a 0,40 en las tenencias de veinte años o más. La mediana de lo que los ayuntamientos tienen aprobado se pega a esa curva casi punto por punto: la política municipal apenas se separa del máximo que le permite la ley.</p>
  </section>

  <section class="sec">
    <h2 id="ejemplo">La misma venta, distinta factura</h2>
    <p>Un inmueble con un <strong>valor catastral del suelo de {euros(suelo)}</strong> vendido a los <strong>10 años</strong> de haberlo comprado, calculado por el método objetivo con los coeficientes y tipos reales de cada municipio. Los diez más caros y los diez más baratos:</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Coeficiente a 10 años</th><th>Tipo de gravamen</th><th>Cuota</th></tr></thead>
      <tbody>
{filas_ejemplo}
      </tbody>
    </table>
    <p>Recuerda que puedes elegir el <strong>método real</strong> (la ganancia efectiva entre escrituras, multiplicada por el peso del suelo en el valor catastral) si sale menor, y que <strong>si vendes con pérdidas no hay impuesto</strong>. <a href="{PREFIX}plusvalia/" style="color:var(--accent);font-weight:600">Cómo comparar los dos métodos →</a></p>
  </section>

  <section class="sec">
    <h2 id="tipos">Reparto de los tipos de gravamen</h2>
    <table class="dt">
      <thead><tr><th>Tipo de gravamen máximo aplicado</th><th>Municipios</th></tr></thead>
      <tbody>
{filas_tipos}
      </tbody>
    </table>
    <p>Cuando un municipio escalona el tipo, suele hacerlo para gravar menos las transmisiones a corto plazo, o al contrario, para penalizarlas. Cuando lo deja plano, el coeficiente es lo único que diferencia una venta rápida de una a veinte años.</p>
  </section>

  <section class="sec">
    <h2 id="escalonados">Los municipios que escalonan el tipo de gravamen</h2>
    <p>La ley permite fijar <strong>un tipo distinto para cada tramo de años</strong> (art. 108.1 TRLRHL). La mayoría no lo usa: {len(planos)} de los {len(con_datos)} municipios aplican el mismo porcentaje a una venta de un año y a una de veinte. Estos son los que sí diferencian, con el recorrido entre su tipo más bajo y el más alto:</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Tipo más bajo</th><th>Tipo más alto</th><th>Recorrido</th></tr></thead>
      <tbody>
{filas_escalonados}
      </tbody>
    </table>
    <p>Que un ayuntamiento grave más las transmisiones a largo plazo tiene una lógica: el coeficiente ya castiga menos las ventas rápidas desde la reforma de 2021, y escalonar el tipo permite corregirlo. Al revés —tipo alto en el corto plazo— es una medida contra la compraventa especulativa.</p>
  </section>

  <section class="sec">
    <h2 id="comprobar">Cómo comprobar los coeficientes de tu municipio</h2>
    <p>Los datos que publicamos son los que el ayuntamiento comunica al Ministerio, y el último ejercicio disponible es {ejercicio}. Si necesitas la cifra exacta para una escritura, hay tres sitios donde mirar, en este orden:</p>
    <ol>
      <li><strong>La ordenanza fiscal del IIVTNU de tu ayuntamiento.</strong> Es la fuente primaria y la única que vale ante una liquidación. Suele estar en la web municipal, en el apartado de ordenanzas o de normativa fiscal.</li>
      <li><strong>El boletín oficial de la provincia</strong> donde se publicó la aprobación definitiva de esa ordenanza. Es lo que acredita la fecha de entrada en vigor.</li>
      <li><strong>La <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta del Ministerio de Hacienda</a></strong>, que es de donde salen estas tablas. Va con retraso respecto a la ordenanza, pero permite comparar municipios sin abrir 134 webs.</li>
    </ol>
    <p>Y un detalle que se pasa por alto: los coeficientes máximos del art. 107.4 <strong>se actualizan por la Ley de Presupuestos</strong>. Si tu ordenanza dice «se aplicarán los máximos legales» en lugar de listar números, los tuyos cambian cuando cambia la ley estatal, sin que el pleno tenga que aprobar nada.</p>
  </section>

  <section class="sec">
    <h2 id="maximos">Los coeficientes máximos de referencia</h2>
    <p>Estos son los topes del art. 107.4 del TRLRHL. Se actualizan por la Ley de Presupuestos, así que conviene comprobar la versión consolidada antes de hacer cuentas.</p>
    <table class="dt">
      <thead><tr><th>Años transcurridos</th><th>Coeficiente máximo</th></tr></thead>
      <tbody>
{filas_max}
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2 id="fuentes">Metodología y fuentes</h2>
    <p>Los coeficientes y tipos reales de cada municipio proceden de la <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a> del Ministerio de Hacienda, ejercicio {ejercicio}. Los máximos legales, del texto consolidado del <a href="{BOE_TRLRHL}" target="_blank" rel="nofollow noopener">TRLRHL</a> en el BOE.</p>
{parrafo_inc}
    <p><strong>Lo que no cubre este análisis:</strong> la consulta del Ministerio no publica los coeficientes de {len(sin_datos)} de los {len(ms)} municipios de la guía ({sin_lista}). En sus fichas remitimos al máximo legal y lo advertimos. Tampoco recoge las reducciones potestativas ni las exenciones (herencias entre familiares directos en algunos municipios, dación en pago, transmisiones con pérdidas), que hay que buscar en la ordenanza.</p>
    <p>En la ficha de cada municipio publicamos sus 21 coeficientes y su tipo, con un ejemplo de cálculo. <a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio →</a></p>
  </section>
"""
    articulo(
        "coeficientes-plusvalia",
        "Coeficientes de plusvalía: quién aplica el máximo legal",
        f"Comparamos los coeficientes reales de plusvalía municipal de {len(con_datos)} "
        f"ayuntamientos con los máximos del art. 107.4 TRLRHL: {len(en_maximo)} aplican el tope "
        f"en los 21 tramos y {len(al_30)} usan el tipo máximo del 30%. Con ejemplo de cálculo "
        "comparado.",
        "Coeficientes de plusvalía municipal: quién aplica el máximo legal",
        f"La ley fija unos coeficientes máximos para la plusvalía municipal y deja que cada "
        f"ayuntamiento baje de ahí. Hemos comprobado cuántos lo hacen: "
        f"<strong>{len(en_maximo)} de {len(con_datos)}</strong> aplican el tope en los 21 tramos.",
        cuerpo,
        seccion="Coeficientes de plusvalía",
    )


# ─────────────────── 4. antigüedad de los valores catastrales ───────────────────

def valores_catastrales() -> None:
    ms = [m for m in municipios() if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()]
    ano_actual = date.today().year
    for m in ms:
        m["_ano"] = int(m["oficial_ano_valores_catastrales"])
        m["_antig"] = ano_actual - m["_ano"]
    ms.sort(key=lambda m: m["_ano"])
    antigs = [m["_antig"] for m in ms]
    mediana = statistics.median(antigs)
    mas_20 = [m for m in ms if m["_antig"] >= 20]
    mas_10 = [m for m in ms if m["_antig"] >= 10]
    recientes = [m for m in ms if m["_antig"] < 10]

    filas_viejos = "\n".join(
        f'            <tr><td>{enlace(m)}</td>'
        f'<td>{html.escape(m.get("provincia") or "—")}</td>'
        f'<td class="v">{m["_ano"]}</td><td>{m["_antig"]} años</td>'
        f'<td>{pct(m["oficial_tipo_urbana"])}</td></tr>'
        for m in ms[:20]
    )
    filas_nuevos = "\n".join(
        f'            <tr><td>{enlace(m)}</td>'
        f'<td>{html.escape(m.get("provincia") or "—")}</td>'
        f'<td class="v">{m["_ano"]}</td><td>{m["_antig"]} años</td>'
        f'<td>{pct(m["oficial_tipo_urbana"])}</td></tr>'
        for m in ms[-10:][::-1]
    )
    # decadas
    decadas = Counter((m["_ano"] // 10) * 10 for m in ms)
    filas_dec = "\n".join(
        f'            <tr><td>{d}–{d + 9}</td><td class="v">{n}</td>'
        f'<td>{num(100 * n / len(ms), 1)}%</td></tr>'
        for d, n in sorted(decadas.items())
    )
    # correlacion informal: los que tienen valores viejos, ¿aplican tipos mas altos?
    tipo_viejos = statistics.median([m["oficial_tipo_urbana"] for m in mas_20]) if mas_20 else 0
    tipo_nuevos = statistics.median([m["oficial_tipo_urbana"] for m in recientes]) if recientes else 0
    figura_disp = guarda_svg(
        "analisis-valores-vs-tipo.svg",
        svg_valores_vs_tipo([(m["_ano"], m["oficial_tipo_urbana"], m["nombre"]) for m in ms]),
        f"Gráfico de dispersión del año de los valores catastrales frente al tipo de IBI "
        f"urbano en {len(ms)} municipios",
        f"Cada punto es uno de los {len(ms)} municipios analizados. Gráfico propio con el año "
        f"de los valores catastrales y el tipo de IBI que publica el Ministerio de Hacienda.",
        lazy=False,
    )

    cuerpo = f"""  <section class="sec">
    <h2 id="resumen">La mitad de la factura no es el tipo, es el valor</h2>
    <p>Todo el debate público sobre el IBI gira alrededor del tipo de gravamen, que es lo que el pleno vota cada año. Pero la cuota es <strong>valor catastral × tipo</strong>, y el valor catastral lo fija el Catastro en una <em>ponencia de valores</em> que puede tener décadas.</p>
    <p>De los {len(ms)} municipios analizados, la antigüedad mediana de la última valoración colectiva de urbana es de <strong>{num(mediana, 0)} años</strong>. <strong>{len(mas_20)} municipios</strong> arrastran valores de hace 20 años o más y <strong>{len(mas_10)}</strong> de hace 10 o más. Solo {len(recientes)} los han revisado en la última década.</p>
    <p>Esto tiene una consecuencia que casi nadie explica: comparar tipos de IBI entre municipios <strong>no dice cuánto se paga</strong>. La mediana del tipo entre los que llevan 20 años o más sin revisar es del {pct(tipo_viejos)}, y entre los que han revisado en la última década, del {pct(tipo_nuevos)}. Cuando un municipio revisa sus valores al alza, suele bajar el tipo para compensar; y al revés.</p>
{figura_disp}
    <p>Puesto uno frente al otro, el patrón se ve mejor que en cualquier tabla: la nube de puntos no dibuja ninguna línea. Hay municipios con valores de los años noventa aplicando tipos bajos y municipios recién revisados en la mitad alta de la horquilla. Esa dispersión es la prueba de que el tipo, por sí solo, no permite ordenar municipios por lo que cuesta el recibo: hacen falta las dos variables, y solo el propietario conoce el valor catastral de su inmueble.</p>
  </section>

  <section class="sec">
    <h2 id="mas-antiguos">Los 20 municipios con la ponencia más antigua</h2>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Provincia</th><th>Año de la valoración</th><th>Antigüedad</th><th>Tipo urbano</th></tr></thead>
      <tbody>
{filas_viejos}
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2 id="mas-recientes">Los 10 que han revisado más recientemente</h2>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Provincia</th><th>Año de la valoración</th><th>Antigüedad</th><th>Tipo urbano</th></tr></thead>
      <tbody>
{filas_nuevos}
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2 id="decadas">Reparto por década de la última valoración</h2>
    <table class="dt">
      <thead><tr><th>Década</th><th>Municipios</th><th>% del total</th></tr></thead>
      <tbody>
{filas_dec}
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2 id="que-significa">Qué significa para tu recibo</h2>
    <h3>Una ponencia antigua no se corrige sola</h3>
    <p>Si el valor catastral de tu vivienda se fijó hace 25 años, los datos físicos que se usaron entonces —superficie, año de construcción, uso, estado de la reforma— son los de entonces. Los errores se arrastran ejercicio tras ejercicio. Merece la pena entrar en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">Sede Electrónica del Catastro</a> y comprobar la descripción de tu inmueble: si no coincide con la realidad, se puede pedir la subsanación de discrepancias.</p>
    <h3>Los coeficientes de actualización del art. 32.2</h3>
    <p>El Estado puede actualizar los valores catastrales de un municipio por coeficientes, sin hacer una valoración colectiva nueva, a petición del ayuntamiento. Se aprueban en la Ley de Presupuestos y afectan a los municipios que lo solicitan y que cumplen los requisitos del art. 32.2 del <a href="{BOE_TRLCI}" target="_blank" rel="nofollow noopener">texto refundido de la Ley del Catastro Inmobiliario</a>. Es la vía habitual para corregir valores desfasados sin abrir un procedimiento completo.</p>
    <h3>Cuando llega la revisión, llega la reducción</h3>
    <p>Tras una valoración colectiva general al alza, la base liquidable no salta de golpe: el art. 67 del TRLRHL prevé una <strong>reducción que se aplica durante nueve años</strong> y va desapareciendo poco a poco. Es la razón por la que muchos recibos suben cada año «sin que el ayuntamiento haya subido nada»: lo que sube es la base liquidable, porque la reducción se agota.</p>
    <p><a href="{PREFIX}ibi-2026/" style="color:var(--accent);font-weight:600">Cómo se calcula el IBI paso a paso →</a> · <a href="{PREFIX}valor-catastral/">Guía del valor catastral: consultarlo, entenderlo y corregirlo →</a></p>
  </section>

  <section class="sec">
    <h2 id="ponencia">Qué es una ponencia de valores y por qué tarda tanto</h2>
    <p>Una <strong>valoración colectiva de carácter general</strong> no es una actualización automática: es un procedimiento completo. El Catastro elabora una <em>ponencia de valores</em> para todo el término municipal, con los módulos de suelo por polígono y los de construcción por tipología, la somete a información pública y la publica en el boletín oficial de la provincia antes del 1 de julio del año anterior a su entrada en vigor (arts. 25 a 27 del <a href="{BOE_TRLCI}" target="_blank" rel="nofollow noopener">texto refundido de la Ley del Catastro Inmobiliario</a>).</p>
    <p>Se inicia de oficio o <strong>a solicitud del ayuntamiento</strong>, y ahí está la clave política del asunto: la ley pide que hayan pasado al menos cinco años desde la anterior, pero <strong>no obliga a revisar</strong> pasado un plazo. Una revisión al alza sube la base de todos los recibos a la vez, así que no hay muchos incentivos para pedirla en un año electoral. De ahí que la mediana de la muestra esté en {num(mediana, 0)} años.</p>
    <h3>La consecuencia menos intuitiva</h3>
    <p>Cuando los valores llevan décadas congelados, dejan de reflejar las diferencias reales entre zonas del municipio: el barrio que se ha revalorizado y el que se ha degradado siguen tributando con los módulos de entonces. La desactualización no solo abarata el IBI en conjunto, también lo vuelve <strong>menos equitativo entre vecinos</strong>.</p>
  </section>

  <section class="sec">
    <h2 id="recursos">Qué hacer si tu valor catastral está mal</h2>
    <p>Conviene separar dos cosas distintas, porque el trámite y el plazo no son los mismos:</p>
    <h3>Los datos del inmueble no coinciden con la realidad</h3>
    <p>Superficie equivocada, un uso que ya no es el que consta, una reforma o una demolición no registradas. Se corrige con una <strong>solicitud de subsanación de discrepancias</strong> ante el Catastro, sin plazo: se puede pedir en cualquier momento. Los efectos son desde el día siguiente a la resolución, no retroactivos, así que cuanto antes se detecte, mejor.</p>
    <h3>No estás de acuerdo con el valor asignado</h3>
    <p>Aquí sí hay plazo. Contra la notificación del nuevo valor catastral cabe <strong>recurso de reposición o reclamación económico-administrativa ante el TEAR en un mes</strong>, y son excluyentes: si presentas reposición, la reclamación espera. Pasado ese mes el valor queda firme y ya solo se puede discutir en la siguiente valoración.</p>
    <p>Y una advertencia práctica: <strong>recurrir el recibo del IBI no sirve para discutir el valor catastral</strong>. Son dos administraciones distintas —el ayuntamiento gestiona el IBI, el Catastro fija el valor— y el ayuntamiento no puede modificar la base imponible que le viene dada. Si el problema es el valor, el expediente va al Catastro.</p>
    <p style="font-size:.85rem;color:var(--mid)">Esta sección resume el procedimiento general; no es asesoramiento jurídico. Los plazos concretos figuran en la notificación que recibas.</p>
  </section>

  <section class="sec">
    <h2 id="fuentes">Metodología y fuentes</h2>
    <p>El año de entrada en vigor de los valores catastrales resultantes del último procedimiento de valoración colectiva de carácter general sale de la <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a> del Ministerio de Hacienda, que lo publica municipio a municipio.</p>
    <p>«Antigüedad» es la diferencia entre {ano_actual} y ese año. La comparación de medianas de tipo entre grupos es descriptiva: con {len(ms)} municipios y un sesgo hacia los más poblados no permite concluir una relación causal, solo señalar el patrón.</p>
    <p>Este dato aparece en la ficha de cada municipio, en la tabla de tipos oficiales. <a href="{PREFIX}municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio →</a></p>
  </section>
"""
    articulo(
        "valores-catastrales-antiguos",
        "Valores catastrales: quién lleva 20 años sin revisarlos",
        f"De {len(ms)} municipios analizados, {len(mas_20)} arrastran valores catastrales de hace "
        f"20 años o más y la antigüedad mediana es de {num(mediana, 0)} años. Por qué comparar "
        "tipos de IBI no dice cuánto se paga, y qué puedes revisar en el Catastro.",
        "Valores catastrales: los municipios que llevan 20 años sin revisarlos",
        f"La cuota del IBI es valor catastral × tipo, y de {len(ms)} municipios analizados "
        f"<strong>{len(mas_20)} arrastran valores de hace 20 años o más</strong>. Por eso comparar "
        "tipos de gravamen entre municipios no dice cuánto se paga realmente.",
        cuerpo,
        seccion="Valores catastrales",
    )


# ─────────────────────────────── índice ───────────────────────────────

def indice() -> None:
    ms = municipios()
    imps = impuestos()
    tipos = [m["oficial_tipo_urbana"] for m in ms]
    ejercicio = ms[0].get("oficial_ejercicio", "2025")
    poblacion = sum(m.get("poblacion_oficial") or 0 for m in ms)
    por_ccaa: dict[str, list[float]] = defaultdict(list)
    for m in ms:
        por_ccaa[ccaa_nombre(m)].append(m["oficial_tipo_urbana"])
    orden_ccaa = sorted(
        ((c, len(v), statistics.median(v)) for c, v in por_ccaa.items()),
        key=lambda t: -t[2],
    )
    anos = [int(m["oficial_ano_valores_catastrales"]) for m in ms
            if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()]
    ivtm_datos = [
        v for v in (
            to_float(((imps.get(m.get("oficial_codigo_ine") or "") or {})
                      .get("conceptos", {}).get("C19") or {}).get("valor"))
            for m in ms
        ) if v is not None
    ]
    figura_ccaa = guarda_svg(
        "analisis-medianas-ccaa.svg",
        svg_medianas_ccaa(orden_ccaa),
        "Gráfico de barras con la mediana del tipo de IBI urbano en cada una de las nueve "
        "comunidades autónomas cubiertas",
        f"Mediana del tipo de IBI urbano por comunidad autónoma en los {len(ms)} municipios "
        f"analizados, ejercicio {ejercicio}. Gráfico propio.",
        lazy=False,
    )
    fichas = [
        ("ranking-ibi-municipios", "¿Dónde se paga más IBI?",
         f"Ranking del tipo de gravamen en {len(ms)} municipios, con la cuota comparada para un "
         "mismo valor catastral y quién ha subido el tipo este ejercicio."),
        ("impuesto-circulacion-ivtm", "Lo que cuesta el impuesto de circulación",
         "La tarifa del IVTM municipio a municipio: por el mismo turismo hay municipios que cobran "
         "el mínimo legal y otros que casi duplican esa cuota."),
        ("coeficientes-plusvalia", "Coeficientes de plusvalía: quién aplica el máximo",
         "Comparamos los coeficientes reales de cada ayuntamiento con los topes del art. 107.4 "
         "TRLRHL, con un ejemplo de la misma venta en cada municipio."),
        ("valores-catastrales-antiguos", "Valores catastrales sin revisar",
         "La antigüedad de la última valoración colectiva explica por qué comparar tipos de IBI "
         "no dice cuánto se paga."),
    ]
    tarjetas = "\n".join(
        f'    <article class="sec" style="border-left:3px solid var(--accent);padding-left:16px">\n'
        f'      <h2 style="margin-bottom:6px"><a href="{PREFIX}analisis/{slug}/">{titulo}</a></h2>\n'
        f'      <p>{resumen}</p>\n'
        f'      <p><a href="{PREFIX}analisis/{slug}/" style="color:var(--accent);'
        f'font-weight:600">Leer el análisis →</a></p>\n'
        f'    </article>'
        for slug, titulo, resumen in fichas
    )
    cuerpo = f"""  <section class="sec">
    <h2 id="que-es">Qué encontrarás aquí</h2>
    <p>Las guías explican cómo funciona cada impuesto y las fichas municipales dan el dato de un municipio concreto. Esta sección es distinta: son <strong>análisis que solo se pueden hacer teniendo los {len(ms)} municipios en la misma tabla</strong>, comparando lo que cada ayuntamiento ha aprobado.</p>
    <p>Todas las cifras salen de fuentes oficiales citadas —la consulta de información impositiva municipal del Ministerio de Hacienda, el INE y el BOE— y cada artículo dice al final qué no cubre. Cuando un dato no está contrastado, lo decimos: <a href="{PREFIX}metodologia/">así trabajamos</a>.</p>
    <p>La muestra sobre la que trabajan todos los análisis es la misma: <strong>{len(ms)} municipios</strong> de nueve comunidades autónomas, {bx.miles(poblacion)} habitantes en total, con el ejercicio <strong>{ejercicio}</strong> como último publicado por Hacienda. En ella el tipo de IBI urbano va del {pct(min(tipos))} al {pct(max(tipos))} (mediana: {pct(statistics.median(tipos))}), las valoraciones catastrales vigentes van de {min(anos)} a {max(anos)} y la tarifa del impuesto de circulación de un turismo medio, de {num(min(ivtm_datos))} € a {num(max(ivtm_datos))} € al año.</p>
    <p>No es una muestra representativa del conjunto de España: son los municipios que hemos podido documentar por completo, con sesgo hacia los más poblados de cada provincia. Lo decimos aquí y en cada artículo, porque cambia lo que se puede concluir: sirve para comparar municipios entre sí y para ver patrones, no para calcular medias nacionales.</p>
  </section>

  <section class="sec">
    <h2 id="mapa">La muestra de un vistazo</h2>
{figura_ccaa}
    <p>El IBI es un tributo estrictamente municipal: la comunidad autónoma no fija el tipo ni participa en su recaudación. Que las medianas por comunidad salgan distintas no indica ninguna política autonómica, sino la mezcla de municipios que hay en cada una y, sobre todo, la antigüedad de sus valores catastrales. La comunidad con la mediana más alta de la muestra es {orden_ccaa[0][0]} ({pct(orden_ccaa[0][2])} en {orden_ccaa[0][1]} municipios) y la más baja {orden_ccaa[-1][0]} ({pct(orden_ccaa[-1][2])} en {orden_ccaa[-1][1]}).</p>
    <p>Para leer bien cualquiera de estas comparaciones hay una regla que conviene tener presente: <strong>el tipo de gravamen no es el precio del recibo</strong>. La cuota es valor catastral por tipo, y un municipio con valores de los años noventa puede aplicar un tipo alto y seguir cobrando menos que su vecino recién revisado. Por eso la sección tiene un artículo dedicado precisamente a la antigüedad de las valoraciones.</p>
  </section>

{tarjetas}

  <section class="sec">
    <h2 id="como-se-hacen">Cómo se hacen estos análisis</h2>
    <p>El punto de partida es la <a href="{HACIENDA}" target="_blank" rel="nofollow noopener">consulta de información impositiva municipal</a> del Ministerio de Hacienda, la única fuente estatal que publica, municipio a municipio y ejercicio a ejercicio, lo que cada ayuntamiento tiene aprobado: tipos del IBI, tarifa del impuesto de circulación, tipo del ICIO, coeficientes de la plusvalía y año de la última valoración catastral. A eso sumamos las cifras oficiales de población del INE y el texto consolidado de la normativa en el BOE.</p>
    <p>Descargamos esos datos, los normalizamos en una única tabla y a partir de ahí calculamos rankings, medianas y ejemplos comparados. Los cálculos derivados —una cuota para un valor catastral común, una diferencia en euros— se explican siempre en el apartado de metodología de cada artículo, para que se puedan reproducir.</p>
    <h3>Qué no hacemos</h3>
    <p>No rellenamos huecos. Cuando la fuente no publica un dato lo decimos y contamos a cuántos municipios afecta; cuando lo que publica no encaja con la normativa vigente, lo advertimos en lugar de reproducirlo. El caso más claro es la <a href="{PREFIX}tasa-basuras/">tasa de residuos</a>: no existe fuente estatal que la recoja, así que no publicamos importes por municipio y <a href="{PREFIX}metodologia/#no-publicamos">explicamos por qué</a>. Y ningún análisis sustituye a la ordenanza fiscal del municipio, que es la que vale ante una liquidación: en cada ficha municipal enlazamos dónde consultarla.</p>
    <h3>Los gráficos son propios</h3>
    <p>Cada figura de esta sección se dibuja con los datos de la propia página, lleva el texto como texto —se puede seleccionar, buscar e indexar— y cita la fuente en el pie. No hay imágenes de archivo ni gráficos tomados de terceros. Si encuentras una diferencia entre un gráfico y su tabla, es un error nuestro y queremos saberlo: <a href="{PREFIX}contacto/">avísanos</a>.</p>
    <h3>Qué se actualiza y cuándo</h3>
    <p>Estos análisis se rehacen cuando cambia el dato de origen: cuando el Ministerio publica un ejercicio nuevo, cuando el INE actualiza el padrón o cuando una reforma legal mueve los límites que usamos como referencia. Al regenerarse desde la misma tabla que las fichas, ningún artículo se queda con cifras viejas mientras el resto del sitio avanza.</p>
  </section>
"""
    articulo(
        "", "Análisis: comparativas de impuestos municipales",
        f"Análisis propios a partir de los datos oficiales de {len(ms)} municipios: ranking del "
        "IBI, comparativa del impuesto de circulación, coeficientes reales de plusvalía y "
        "antigüedad de los valores catastrales.",
        "Análisis de impuestos municipales",
        f"Comparativas hechas con los datos oficiales de {len(ms)} municipios normalizados en una "
        "misma tabla. Cada cifra con su fuente y cada artículo con sus límites.",
        cuerpo,
        seccion="Análisis",
    )


def main() -> int:
    print("Generando los análisis…")
    ranking_ibi()
    ivtm()
    plusvalia()
    valores_catastrales()
    indice()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
