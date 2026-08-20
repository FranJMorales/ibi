#!/usr/bin/env python3
"""Genera los graficos SVG propios de cada pilar territorial a partir de
data/municipios.json.

Son imagenes originales del sitio (no stock, no genericas): se dibujan con los
datos publicados en la pagina, llevan <title> y <desc> para accesibilidad, el texto
es texto real (indexable) y pesan unos pocos kB, asi que no penalizan LCP.

Salida:
    img/{territorio}-ibi-urbano-2026.svg      ranking del tipo de IBI urbano
    img/{territorio}-valores-catastrales.svg  ano de los valores catastrales

Uso:  python3 scripts/build_charts.py --territorio murcia --nombre "Murcia"
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
IMG = ROOT / "img"

INK = "#1a1a2e"
ACCENT = "#c8522a"
ACCENT2 = "#2a7c6f"
PAPER = "#f5f0e8"
RULE = "#d8d0c0"
MID = "#6b6b7b"
CARD = "#fffdf8"

REFERENCE_VC = 50000
FONT = "Georgia, 'Source Serif 4', serif"


def load(territorio: str) -> list[dict]:
    records = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    out = []
    for m in records:
        if m["ccaa"] != territorio and f"{m['ccaa']}/{m['provincia_slug']}" != territorio:
            continue
        # El tipo oficial del Ministerio manda sobre el que se publicaba antes, para
        # que el grafico, la tabla del pilar y la ficha digan lo mismo.
        if m.get("oficial_tipo_urbana"):
            m["tipo_urbano"] = m["oficial_tipo_urbana"]
        if m.get("poblacion_oficial"):
            m["poblacion"] = m["poblacion_oficial"]
        if m.get("tipo_urbano"):
            out.append(m)
    return out


def euros(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + " €"


def pct(value: float) -> str:
    # Mismo formato que las tablas del pilar y las fichas: sin ceros de relleno.
    return f"{round(value, 4):g}".replace(".", ",") + "%"


def chart_tipos(municipios: list[dict], nombre: str) -> str:
    data = sorted(municipios, key=lambda m: -m["tipo_urbano"])
    row, top, left, right = 28, 96, 176, 74
    width = 900
    height = top + row * len(data) + 56
    bar_max = width - left - right
    vmax = max(m["tipo_urbano"] for m in data)
    vmin = min(m["tipo_urbano"] for m in data)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-labelledby="t-tipos d-tipos" font-family="{FONT}">',
        f'<title id="t-tipos">Tipo de gravamen del IBI urbano en los municipios de {html.escape(nombre)} para 2026</title>',
        f'<desc id="d-tipos">Gráfico de barras horizontales. Los tipos van del {pct(vmin)} al {pct(vmax)}. '
        f'Cada barra corresponde a un municipio de {html.escape(nombre)} recogido en la guía.</desc>',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        f'<text x="24" y="38" font-size="21" font-weight="700" fill="{INK}">'
        f"Tipo de IBI urbano 2026 · {html.escape(nombre)}</text>",
        f'<text x="24" y="62" font-size="13" fill="{MID}">'
        f"Porcentaje aplicado sobre el valor catastral. Horquilla legal para urbana: 0,40% – 1,10%.</text>",
        f'<line x1="{left}" y1="{top - 14}" x2="{width - right + 6}" y2="{top - 14}" stroke="{RULE}"/>',
    ]

    for i, m in enumerate(data):
        y = top + i * row
        w = max(6, bar_max * (m["tipo_urbano"] / vmax) * 0.98)
        color = ACCENT if i == 0 or i == len(data) - 1 else ACCENT2
        parts.append(
            f'<text x="{left - 10}" y="{y + 13}" font-size="13" fill="{INK}" text-anchor="end">'
            f"{html.escape(m['nombre'])}</text>"
        )
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.0f}" height="18" rx="2" fill="{color}"/>')
        parts.append(
            f'<text x="{left + w + 8:.0f}" y="{y + 13}" font-size="12.5" font-weight="700" fill="{INK}">'
            f"{pct(m['tipo_urbano'])}</text>"
        )

    parts.append(
        f'<text x="24" y="{height - 22}" font-size="11.5" fill="{MID}">'
        f"Elaboración propia de TasasMunicipales.info con los tipos que publica el Ministerio de Hacienda.</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def chart_valores(municipios: list[dict], nombre: str) -> str:
    """Antiguedad de los valores catastrales vigentes en cada municipio.

    Sustituye al grafico de «IBI + basuras»: la tasa de basuras se retiro por no
    tener fuente (scripts/retirar_datos_sin_fuente.py). El ano de los valores
    catastrales si esta verificado en el Ministerio de Hacienda y explica la otra
    mitad del recibo: la base sobre la que se aplica el tipo.
    """
    data = [
        m for m in municipios
        if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()
    ]
    if not data:
        return ""
    for m in data:
        m["_ano"] = int(m["oficial_ano_valores_catastrales"])
    data.sort(key=lambda m: m["_ano"])
    row, top, left, right = 28, 104, 176, 96
    width = 900
    height = top + row * len(data) + 56
    bar_max = width - left - right
    vmin = min(m["_ano"] for m in data)
    vmax = max(m["_ano"] for m in data)
    base = vmin - 2
    span = max(1, vmax - base)
    ejercicio = 2026

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-labelledby="t-val d-val" font-family="{FONT}">',
        f'<title id="t-val">Año de los valores catastrales vigentes en los municipios de '
        f'{html.escape(nombre)}</title>',
        f'<desc id="d-val">Gráfico de barras horizontales ordenado de la valoración más '
        f'antigua a la más reciente. Va de {vmin} a {vmax}. Cuanto más antigua es la '
        f'valoración, más desfasada está la base sobre la que se aplica el tipo del '
        f'IBI.</desc>',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        f'<text x="24" y="38" font-size="21" font-weight="700" fill="{INK}">'
        f"Antigüedad de los valores catastrales · {html.escape(nombre)}</text>",
        f'<text x="24" y="62" font-size="13" fill="{MID}">'
        f"Año de la última valoración vigente. El tipo de IBI se aplica sobre esa base, "
        f"no sobre el precio de mercado.</text>",
        f'<text x="24" y="82" font-size="12" fill="{MID}">'
        f"Naranja: valoraciones anteriores a 2010. Verde: de 2010 en adelante.</text>",
        f'<line x1="{left}" y1="{top - 14}" x2="{width - right + 6}" y2="{top - 14}" '
        f'stroke="{RULE}"/>',
    ]

    for i, m in enumerate(data):
        y = top + i * row
        w = max(8, bar_max * ((m["_ano"] - base) / span) * 0.98)
        color = ACCENT if m["_ano"] < 2010 else ACCENT2
        edad = ejercicio - m["_ano"]
        parts.append(
            f'<text x="{left - 10}" y="{y + 13}" font-size="13" fill="{INK}" '
            f'text-anchor="end">{html.escape(m["nombre"])}</text>'
        )
        parts.append(
            f'<rect x="{left}" y="{y}" width="{w:.0f}" height="18" rx="2" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{left + w + 8:.0f}" y="{y + 13}" font-size="12.5" '
            f'font-weight="700" fill="{INK}">{m["_ano"]}</text>'
        )
        parts.append(
            f'<text x="{left + w + 50:.0f}" y="{y + 13}" font-size="11.5" fill="{MID}">'
            f'{edad} años</text>'
        )

    parts.append(
        f'<text x="24" y="{height - 22}" font-size="11.5" fill="{MID}">'
        "Elaboración propia de TasasMunicipales.info con el año de los valores catastrales "
        "que publica el Ministerio de Hacienda en su consulta de información impositiva "
        "municipal.</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def diagrama_calculo() -> str:
    """Esquema del calculo de la cuota del IBI. Imagen propia, valida para todo el sitio."""
    w, h = 900, 300
    box = (
        '<rect x="{x}" y="{y}" width="{bw}" height="64" rx="4" fill="{fill}" stroke="{stroke}"/>'
        '<text x="{cx}" y="{ty}" font-size="13.5" font-weight="700" fill="{ink}" text-anchor="middle">{t1}</text>'
        '<text x="{cx}" y="{ty2}" font-size="12" fill="{mid}" text-anchor="middle">{t2}</text>'
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t-calc d-calc" font-family="{FONT}">',
        '<title id="t-calc">Esquema del cálculo de la cuota del IBI</title>',
        "<desc id=\"d-calc\">El valor catastral genera la base imponible; tras la reducción legal se obtiene "
        "la base liquidable; multiplicada por el tipo de gravamen municipal da la cuota íntegra; al restar "
        "las bonificaciones se obtiene la cuota líquida que se paga.</desc>",
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<text x="24" y="38" font-size="21" font-weight="700" fill="{INK}">Cómo se calcula la cuota del IBI</text>',
        f'<text x="24" y="61" font-size="13" fill="{MID}">Del valor catastral al importe que aparece en tu recibo.</text>',
    ]
    steps = [
        ("Valor catastral", "Lo asigna el Catastro"),
        ("Base liquidable", "Valor menos reducción legal"),
        ("× Tipo de gravamen", "Lo fija tu ayuntamiento"),
        ("= Cuota íntegra", "Antes de beneficios"),
        ("− Bonificaciones", "Solo si las solicitas"),
    ]
    bw, gap, x0, y0 = 152, 34, 26, 96
    for i, (t1, t2) in enumerate(steps):
        x = x0 + i * (bw + gap)
        fill = CARD if i < len(steps) - 1 else "#fdf3ee"
        parts.append(
            box.format(x=x, y=y0, bw=bw, fill=fill, stroke=RULE, cx=x + bw / 2,
                       ty=y0 + 27, ty2=y0 + 47, ink=INK, mid=MID, t1=t1, t2=t2)
        )
        if i < len(steps) - 1:
            ax = x + bw + 8
            parts.append(
                f'<path d="M{ax} {y0 + 32} L{ax + 18} {y0 + 32}" stroke="{ACCENT}" stroke-width="2"/>'
                f'<path d="M{ax + 18} {y0 + 32} l-6 -4 v8 z" fill="{ACCENT}"/>'
            )
    parts.append(
        f'<rect x="26" y="196" width="848" height="52" rx="4" fill="{ACCENT}" opacity="0.08"/>'
        f'<text x="46" y="219" font-size="14" font-weight="700" fill="{INK}">Cuota líquida = base liquidable × tipo − bonificaciones</text>'
        f'<text x="46" y="238" font-size="12.5" fill="{MID}">Ejemplo: 50.000 € × 0,64% = 320 € · con una bonificación del 50% por familia numerosa, 160 €.</text>'
    )
    parts.append(
        f'<text x="24" y="{h - 14}" font-size="11.5" fill="{MID}">'
        "Elaboración propia de TasasMunicipales.info según los artículos 65 a 74 del texto refundido de la "
        "Ley Reguladora de las Haciendas Locales.</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territorio", required=True)
    ap.add_argument("--nombre", required=True)
    args = ap.parse_args()

    municipios = load(args.territorio)
    if not municipios:
        print(f"[error] sin municipios para {args.territorio}")
        return 1

    slug = args.territorio.replace("/", "-")
    IMG.mkdir(exist_ok=True)
    for suffix, svg in (
        ("ibi-urbano-2026", chart_tipos(municipios, args.nombre)),
        ("valores-catastrales", chart_valores(municipios, args.nombre)),
    ):
        if not svg:
            continue
        path = IMG / f"{slug}-{suffix}.svg"
        path.write_text(svg + "\n", encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}  ({len(svg) // 1024 or 1} kB, {len(municipios)} municipios)")

    # El grafico anterior sumaba IBI y un importe de basuras sin fuente.
    viejo = IMG / f"{slug}-coste-anual-2026.svg"
    if viejo.exists():
        viejo.unlink()
        print(f"  eliminado {viejo.relative_to(ROOT)} (sumaba una tasa sin fuente)")

    esquema = IMG / "esquema-calculo-ibi.svg"
    esquema.write_text(diagrama_calculo() + "\n", encoding="utf-8")
    print(f"  {esquema.relative_to(ROOT)}  (esquema común del cálculo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
