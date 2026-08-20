#!/usr/bin/env python3
"""Pone la portada al dia con las paginas y los datos que hay ahora.

Que arregla, con la evidencia de por que:

1. La rejilla «Que impuesto quieres consultar?» se quedo en cuatro tarjetas y el
   sitio ya tiene seis guias: faltaban /impuesto-circulacion/ y /valor-catastral/,
   que si estan en la cabecera pero no en la portada. Con seis tarjetas la rejilla
   automatica dejaba una fila de cuatro y otra de dos, asi que la portada usa la
   variante de tres columnas (dos filas iguales).

2. Textos que contradicen al resto del sitio despues de retirar los datos sin
   fuente (ver scripts/retirar_datos_sin_fuente.py):
     - la tarjeta de basuras prometia «importe anual» y la de IBI «fecha de cobro»,
       que es justo lo que ya no publicamos;
     - la FAQ afirmaba que el periodo voluntario «va del 1 de octubre al 30 de
       noviembre» en la mayoria de municipios: ese dato salia de los periodos que
       hemos retirado. Lo verificable es el plazo por defecto del art. 62.3 LGT;
     - el bloque «Por que pagar de mas?» decia que los ayuntamientos «estan
       obligados» a bonificar a familias numerosas y a las renovables. El art. 74.4
       y el 74.5 del TRLRHL dicen «podran»: son potestativas. Las obligatorias son
       las del art. 73 (VPO y cooperativas agrarias);
     - «basada en las ordenanzas fiscales aprobadas por cada ayuntamiento» y
       «ordenanzas actualizadas» ya no describen la fuente real, que es la consulta
       de informacion impositiva del Ministerio de Hacienda mas el INE y el BOE;
     - el texto de «Sobre esta guia» seguia enumerando cuatro impuestos y hablaba
       de una estructura «por provincia» que se retiro al eliminar /provincias/.

Es idempotente: se puede ejecutar tantas veces como se quiera.

Uso:  python3 scripts/fix_home.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = ROOT / "index.html"

TARJETAS_NUEVAS = """    <a href="impuesto-circulacion/" class="type-card">
      <div class="type-icon">🚗</div><h3>Impuesto de Circulación</h3>
      <p>Tarifa del IVTM por caballos fiscales, quién está exento y cómo se paga al comprar o vender un coche.</p>
    </a>
    <a href="valor-catastral/" class="type-card">
      <div class="type-icon">📐</div><h3>Valor Catastral</h3>
      <p>Qué es, cómo consultarlo gratis, en qué se diferencia del precio de mercado y cómo recurrirlo.</p>
    </a>
"""

CIERRE_REJILLA = """      <p>Familia numerosa, placas solares, domiciliación… descubre todas las reducciones posibles en tu IBI.</p>
    </a>
  </div>
"""

SUSTITUCIONES: list[tuple[str, str, str]] = [
    # ── rejilla de impuestos: tres columnas para que las dos filas cuadren ──
    (
        '    <h2>¿Qué impuesto quieres consultar?</h2>\n  </div>\n'
        '  <div class="types-grid">',
        '    <h2>¿Qué impuesto quieres consultar?</h2>\n  </div>\n'
        '  <div class="types-grid cols-3">',
        "rejilla de impuestos a tres columnas",
    ),
    # ── descripciones que prometian datos que ya no publicamos ──
    (
        "<p>Tipo impositivo, cuánto se paga, fecha de cobro y cómo fraccionar el "
        "pago en tu municipio.</p>",
        "<p>Tipo impositivo de tu municipio, cómo se calcula la cuota, qué plazo "
        "marca la ley y cómo fraccionar el pago.</p>",
        "tarjeta de IBI sin prometer la fecha de cobro",
    ),
    (
        "<p>Importe anual, quién la paga en alquiler y cómo reclamar si hay errores "
        "en el recibo.</p>",
        "<p>Qué obliga la Ley 7/2022, quién la paga en un alquiler, cómo reclamar y "
        "dónde localizar la tarifa de tu municipio.</p>",
        "tarjeta de basuras sin prometer el importe",
    ),
    # ── hero ──
    (
        "<p>Consulta cuánto pagas, cuándo se cobra y qué bonificaciones puedes "
        "solicitar en cualquiera de los <strong>134 municipios</strong> incluidos "
        "en esta guía.</p>",
        "<p>Consulta el tipo de IBI, la plusvalía, el impuesto de circulación y las "
        "bonificaciones que puedes solicitar en cualquiera de los "
        "<strong>134 municipios</strong> de esta guía, con la fuente oficial de cada "
        "dato.</p>",
        "entradilla de la portada",
    ),
    # ── FAQ de la portada ──
    (
        '<div class="faq-a">Cada municipio fija su período voluntario. En la mayoría '
        'va del 1 de octubre al 30 de noviembre. Busca tu municipio para las fechas '
        'exactas.</div>',
        '<div class="faq-a">Cada ayuntamiento aprueba su calendario cada año. Si su '
        'ordenanza no fija otro plazo, se aplica el del art. 62.3 de la Ley General '
        'Tributaria: del 1 de septiembre al 20 de noviembre.</div>',
        "FAQ del plazo de pago con el art. 62.3 LGT",
    ),
    (
        '<div class="faq-a">La mayoría de ayuntamientos lo permiten sin intereses si '
        'se solicita antes del período voluntario.</div>',
        '<div class="faq-a">Muchos ayuntamientos lo permiten en dos plazos sin '
        'intereses si lo pides antes de que empiece el período voluntario. Depende de '
        'la ordenanza: compruébalo en tu ayuntamiento.</div>',
        "FAQ del fraccionamiento sin dar por hecho «la mayoría»",
    ),
    # ── bloque editorial: las bonificaciones del art. 74 son potestativas ──
    (
        "<p>Muchos propietarios desconocen las bonificaciones que les corresponden. "
        "En España, los ayuntamientos están obligados a aplicar reducciones en el IBI "
        "para familias numerosas, viviendas con instalaciones de energía renovable o "
        "inmuebles de interés histórico.</p>",
        "<p>Muchos propietarios no piden bonificaciones que sí podrían pedir. La ley "
        "distingue dos tipos: las <strong>obligatorias</strong>, que todo ayuntamiento "
        "tiene que aplicar (vivienda de protección oficial durante tres años, "
        "cooperativas agrarias), y las <strong>potestativas</strong>, que cada pleno "
        "decide si aprueba y con qué porcentaje: familia numerosa hasta el 90%, "
        "instalaciones de aprovechamiento solar hasta el 50%, punto de recarga de "
        "vehículo eléctrico hasta el 50%.</p>",
        "corrige que las bonificaciones del art. 74 sean obligatorias",
    ),
    (
        "<p>Nuestra guía te muestra, municipio a municipio, qué bonificaciones puedes "
        "solicitar, cuándo pedirlas y cómo hacerlo paso a paso, sin letra pequeña. La "
        "información está basada en las ordenanzas fiscales aprobadas por cada "
        "ayuntamiento y se actualiza cada año coincidiendo con la aprobación de los "
        "presupuestos municipales.</p>",
        "<p>En la ficha de cada municipio verás el tope legal de cada bonificación, "
        "qué hay que acreditar y por qué ninguna se aplica de oficio: todas hay que "
        "solicitarlas. Los tipos de gravamen salen de la consulta de información "
        "impositiva del Ministerio de Hacienda, la población del INE y cada "
        "afirmación legal del texto consolidado en el BOE, con la fecha de "
        'comprobación a la vista. <a href="metodologia/" style="color:var(--accent);'
        'font-weight:600">Cómo verificamos cada dato →</a></p>',
        "declara las fuentes reales en lugar de «las ordenanzas»",
    ),
    # ── «Sobre esta guia»: seis impuestos y la estructura real ──
    (
        '<p style="margin-bottom:14px;"><strong style="color:var(--ink);">'
        "TasasMunicipales</strong> es la guía de referencia sobre impuestos y tasas "
        "locales en España. Recogemos y actualizamos cada año las ordenanzas fiscales "
        "de <strong>134 municipios</strong>, con información precisa sobre el "
        "<strong>IBI 2026</strong>, la <strong>tasa de basuras</strong>, la "
        "<strong>plusvalía municipal</strong> y las <strong>bonificaciones "
        "disponibles</strong>.</p>",
        '<p style="margin-bottom:14px;"><strong style="color:var(--ink);">'
        "TasasMunicipales</strong> reúne los impuestos y tasas locales de "
        "<strong>134 municipios</strong> españoles con la fuente oficial de cada "
        'cifra: el <a href="ibi-2026/" style="color:var(--accent);">IBI 2026</a>, la '
        '<a href="tasa-basuras/" style="color:var(--accent);">tasa de residuos</a>, la '
        '<a href="plusvalia/" style="color:var(--accent);">plusvalía municipal</a>, '
        'las <a href="bonificaciones/" style="color:var(--accent);">bonificaciones del '
        'IBI</a>, el <a href="impuesto-circulacion/" style="color:var(--accent);">'
        'impuesto de circulación</a> y el <a href="valor-catastral/" '
        'style="color:var(--accent);">valor catastral</a> sobre el que se calcula '
        "todo.</p>",
        "«Sobre esta guía» con las seis guías y sin «ordenanzas»",
    ),
    (
        '<p style="margin-bottom:14px;">Nuestra estructura está organizada por '
        '<a href="comunidades/" style="color:var(--accent);">Comunidad Autónoma</a>, '
        '<a href="municipios/" style="color:var(--accent);">provincia</a> y municipio. '
        "Cada página de municipio enlaza con artículos específicos sobre cómo pagar el "
        "IBI, cómo reclamar la tasa de basuras o cómo calcular la plusvalía.</p>",
        '<p style="margin-bottom:14px;">Puedes entrar por '
        '<a href="comunidades/" style="color:var(--accent);">comunidad autónoma</a>, '
        'comparar los 134 municipios en una '
        '<a href="municipios/" style="color:var(--accent);">misma tabla ordenable</a> '
        'o leer los <a href="analisis/" style="color:var(--accent);">análisis</a> que '
        "salen de cruzar todos esos datos. Cuando no hemos podido verificar un dato no "
        'lo publicamos: <a href="metodologia/#no-publicamos" '
        'style="color:var(--accent);">aquí explicamos qué falta y por qué</a>.</p>',
        "«Sobre esta guía»: estructura real y qué no publicamos",
    ),
    # ── el buscador declarado en el JSON-LD apuntaba a /buscar/, que no existe ──
    (
        '"target": "https://tasasmunicipales.info/buscar/?q={search_term_string}",',
        '"target": "https://tasasmunicipales.info/municipios/?q={search_term_string}",',
        "SearchAction apuntando a una URL que sí existe",
    ),
    # ── metadatos ──
    (
        'content="IBI, tasa de basuras y plusvalía de 134 municipios en España 2026. '
        '9 comunidades autónomas, ordenanzas actualizadas, calculadora y '
        'bonificaciones.">',
        'content="IBI, plusvalía, impuesto de circulación y bonificaciones de 134 '
        'municipios en España 2026, con los tipos oficiales del Ministerio de '
        'Hacienda, calculadora y comparador.">',
        "meta description de la portada",
    ),
    (
        'content="Consulta el IBI, tasa de basuras, plusvalía y bonificaciones de '
        'cualquier municipio de España.">',
        'content="Consulta el IBI, la plusvalía, el impuesto de circulación y las '
        'bonificaciones de 134 municipios españoles, con la fuente oficial de cada '
        'dato.">',
        "og:description de la portada",
    ),
    (
        '"description": "Guía completa de IBI, tasa de basuras, plusvalía y '
        'bonificaciones por municipio en España 2026",',
        '"description": "IBI, plusvalía municipal, impuesto de circulación, valor '
        'catastral y bonificaciones de 134 municipios españoles, con los datos '
        'oficiales del Ministerio de Hacienda",',
        "descripción del JSON-LD de la portada",
    ),
]

# La rejilla de tres columnas no existia: solo estaba la automatica, que con seis
# tarjetas deja una fila incompleta.
CSS_BASE = (
    ".types-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }\n"
)
CSS_MEDIA = (
    ("  .types-grid { grid-template-columns: 1fr 1fr; }\n",
     "  .types-grid { grid-template-columns: 1fr 1fr; }\n"
     "  .types-grid.cols-3 { grid-template-columns: 1fr 1fr; }\n"),
    ("  .types-grid { grid-template-columns: 1fr; }\n",
     "  .types-grid { grid-template-columns: 1fr; }\n"
     "  .types-grid.cols-3 { grid-template-columns: 1fr; }\n"),
)


def actualiza_css(hechos: Counter, dry: bool) -> None:
    ruta = ROOT / "styles.css"
    css = original = ruta.read_text(encoding="utf-8")
    if ".types-grid.cols-3" not in css:
        css = css.replace(
            ".type-card p { font-size: 0.82rem; color: var(--mid); line-height: 1.55; "
            "margin: 0; }\n",
            ".type-card p { font-size: 0.82rem; color: var(--mid); line-height: 1.55; "
            "margin: 0; }\n" + CSS_BASE,
            1,
        )
        for viejo, nuevo in CSS_MEDIA:
            css = css.replace(viejo, nuevo, 1)
        hechos["styles.css: variante de rejilla a tres columnas"] += 1
    if css != original and not dry:
        ruta.write_text(css, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    texto = original = HOME.read_text(encoding="utf-8")
    hechos: Counter = Counter()

    # 1. las dos guias que faltaban en la rejilla
    if 'href="impuesto-circulacion/" class="type-card"' not in texto:
        if CIERRE_REJILLA in texto:
            texto = texto.replace(
                CIERRE_REJILLA,
                CIERRE_REJILLA.rsplit("  </div>\n", 1)[0] + TARJETAS_NUEVAS + "  </div>\n",
                1,
            )
            hechos["portada: tarjetas de impuesto de circulación y valor catastral"] += 1
        else:
            print("  [aviso] no se localiza el final de la rejilla de impuestos")

    # 2. textos
    for viejo, nuevo, clave in SUSTITUCIONES:
        if viejo in texto:
            texto = texto.replace(viejo, nuevo)
            hechos[f"portada: {clave}"] += 1

    if texto != original and not args.dry_run:
        HOME.write_text(texto, encoding="utf-8")

    actualiza_css(hechos, args.dry_run)

    for k in sorted(hechos):
        print(f"  {k}")
    if not hechos:
        print("  (la portada ya estaba al día)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
