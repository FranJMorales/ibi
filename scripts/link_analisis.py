#!/usr/bin/env python3
"""Enlaza la seccion /analisis/ desde el resto del sitio.

Una pagina a la que no apunta nadie no la rastrea nadie. Este script:
  1. Anade el enlace a la barra lateral de navegacion de las fichas municipales.
  2. Coloca un bloque con los cuatro analisis en la portada.

La cabecera ya no se toca aqui: la genera scripts/rebuild_header.py, que es el
unico sitio donde se decide el menu principal.

Uso:  python3 scripts/link_analisis.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAV_ANCLA = re.compile(r'(\s*)<a href="((?:\.\./)*)municipios/">Municipios</a>')
SIDE_ANCLA = re.compile(
    r'(\s*)<li><a href="((?:\.\./)*)municipios/">Todos los municipios</a></li>'
)

ARTICULOS = [
    ("ranking-ibi-municipios", "📊", "¿Dónde se paga más IBI?",
     "Ranking del tipo de gravamen de los 134 municipios, con la cuota comparada."),
    ("impuesto-circulacion-ivtm", "🚗", "Lo que cuesta el impuesto de circulación",
     "La tarifa del IVTM municipio a municipio, del mínimo legal al doble."),
    ("coeficientes-plusvalia", "📉", "¿Quién aplica el coeficiente máximo de plusvalía?",
     "Los coeficientes reales de cada ayuntamiento frente a los topes del TRLRHL."),
    ("valores-catastrales-antiguos", "🏚️", "Valores catastrales sin revisar",
     "Por qué comparar tipos de IBI no dice cuánto se paga."),
]

# El bloque usaba section.sec (tarjeta estrecha con su propio borde), que en la
# portada quedaba descuadrado: el resto de secciones son section.section, con el
# contenedor de 1140 px y la cabecera con la regla inferior. Ahora comparte
# maquetacion con «Que impuesto quieres consultar?».
BLOQUE_HOME_RE = re.compile(
    r'\n<section class="(?:sec|section)(?: ruled)?" id="analisis-destacados">.*?'
    r'</section>\n',
    re.S,
)


def bloque_home() -> str:
    tarjetas = "\n".join(
        f'    <a href="analisis/{slug}/" class="type-card">\n'
        f'      <div class="type-icon">{icono}</div><h3>{titulo}</h3>\n'
        f'      <p>{resumen}</p>\n'
        f'    </a>'
        for slug, icono, titulo, resumen in ARTICULOS
    )
    return (
        '\n<section class="section ruled" id="analisis-destacados">\n'
        '  <div class="section-header">\n'
        '    <h2>Análisis con datos oficiales</h2>\n'
        '    <a href="analisis/">Todos los análisis →</a>\n'
        '  </div>\n'
        '  <div style="max-width:860px;line-height:1.9;font-size:0.92rem;'
        'color:var(--mid);margin-bottom:26px;">\n'
        '    <p>Comparativas hechas con los 134 municipios normalizados en una misma '
        'tabla: lo que no se puede sacar mirando una ordenanza suelta. Cada análisis '
        'lleva sus propios gráficos y cita la fuente de cada cifra.</p>\n'
        '  </div>\n'
        '  <div class="types-grid">\n' + tarjetas + '\n  </div>\n'
        '</section>\n'
    )


def main() -> int:
    side = 0
    for html in sorted(ROOT.rglob("index.html")):
        if ".git" in html.parts:
            continue
        texto = original = html.read_text(encoding="utf-8")

        if ">Análisis y comparativas</a></li>" not in texto:
            def add_side(m: re.Match) -> str:
                return (m.group(0) + m.group(1)
                        + f'<li><a href="{m.group(2)}analisis/">Análisis y '
                          f'comparativas</a></li>')
            texto, n = SIDE_ANCLA.subn(add_side, texto, count=1)
            if n:
                side += 1

        if texto != original:
            html.write_text(texto, encoding="utf-8")

    print(f"  barra lateral de fichas: {side} páginas")

    # ── portada ──
    home = ROOT / "index.html"
    texto = original = home.read_text(encoding="utf-8")
    bloque = bloque_home()
    if BLOQUE_HOME_RE.search(texto):
        texto = BLOQUE_HOME_RE.sub(lambda _: bloque, texto, count=1)
        accion = "bloque de análisis regenerado"
    else:
        for marca in ("\n<footer>", "</div>\n<footer>"):
            if marca in texto:
                texto = texto.replace(marca, bloque + marca, 1)
                accion = "bloque de análisis añadido"
                break
        else:
            print("  [aviso] no se ha encontrado dónde insertar el bloque en la portada")
            return 0
    if texto != original:
        home.write_text(texto, encoding="utf-8")
    print(f"  portada: {accion}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
