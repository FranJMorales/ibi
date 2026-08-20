#!/usr/bin/env python3
"""Corrige errores de HTML heredados y reduce el texto repetido en las 134 fichas.

Acciones:
  1. Colapsa los avisos "[Importe orientativo...]" duplicados (hasta 6 por ficha).
  2. Repara el enlace de sede electrónica que quedó mal formado al mezclarse con
     el del Catastro (34 fichas en producción).
  3. Elimina el <li> del Catastro, redundante (ya se enlaza dos veces antes).
  4. Compacta el bloque "Fuentes oficiales y verificación".
  5. Reescribe el bloque de calendario de cobro sin frases genéricas repetidas.
  6. Personaliza la nota de límites legales de las bonificaciones.
  7. Rehace el resumen de la barra lateral: sumaba el IBI y un importe de basuras
     sin fuente, ahora muestra solo la cuota de IBI y el tipo aplicado.
  8. Inserta una sección comparativa con datos propios de cada municipio
     (posición provincial y autonómica, diferencia en euros, evolución del tipo).
  9. Retira el importe de la tasa de residuos y las fechas de cobro, que no tenían
     fuente primaria (ver scripts/retirar_basuras.py), y los sustituye por el marco
     legal verificado: art. 11.3 y 11.4 de la Ley 7/2022 y art. 62.3 de la LGT.

Uso: python3 scripts/polish_fichas.py [--dry-run]
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
REL = "../../../"
HACIENDA_URL = (
    "https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/"
    "html/portadaconsultasm.aspx"
)
CURRENT_YEAR = 2026


def fmt_pct(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") + "%"


def fmt_num(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}".replace(",", "\u0001").replace(".", ",")
    return text.replace("\u0001", ".")


def fmt_eur(value: float) -> str:
    # Redondeo comercial (al alza en el 0,5): round() de Python lo hace al par y
    # dejaba 290 € donde el resto del sitio y la calculadora muestran 291 €.
    return fmt_num(int(math.floor(value + 0.5))) + " €"


def ordinal(n: int) -> str:
    return f"{n}.º"


# Con 134 fichas enlazando lo mismo, repetir el ancla no aporta nada: se reparten
# de forma determinista por el slug para que cada destino reciba variedad.
ANCLAS_CATASTRO = [
    "cómo se calcula el valor catastral y cómo consultarlo",
    "qué es el valor catastral y cómo se corrige",
    "del valor catastral a la base liquidable del recibo",
    "valor catastral y valor de referencia: en qué se diferencian",
]
ANCLAS_IVTM = [
    "guía del impuesto de circulación: exenciones y bonificaciones",
    "cómo se calcula el impuesto de circulación",
    "qué vehículos están exentos del impuesto de circulación",
    "impuesto de circulación: cuotas mínimas y coeficiente municipal",
]


def ancla(opciones: list[str], clave: str) -> str:
    return opciones[sum(ord(c) for c in clave) % len(opciones)]


def page_path(row: dict) -> Path:
    return ROOT / row["ccaa"] / row["provincia_slug"] / row["slug"] / "index.html"


# Frases que afirman contenidos concretos de una ordenanza que no hemos verificado.
RIESGO_RE = re.compile(
    r"\d+\s?%|bonifi|exenci|tarifa reducida|subvenci|descuento|deduc", re.I
)


def build_checklist(row: dict, prov_rows: list[dict], imp: dict | None) -> str:
    """Comprobaciones concretas derivadas de los datos oficiales del municipio."""
    name = row["nombre"]
    prov = row["provincia"]
    tipo = float(row["oficial_tipo_urbana"])
    ejercicio = row.get("oficial_ejercicio", "2025")
    puntos = []

    ano_val = row.get("oficial_ano_valores_catastrales")
    if ano_val and str(ano_val).isdigit():
        antig = CURRENT_YEAR - int(ano_val)
        if antig >= 10:
            puntos.append(
                f"<li>Los valores catastrales de urbana de {name} son de {ano_val}, "
                f"de hace {antig} años: revisa en el Catastro que la superficie y el "
                f"uso de tu inmueble sean los correctos.</li>"
            )
        else:
            puntos.append(
                f"<li>{name} revisó sus valores catastrales en {ano_val}, así que la "
                f"base imponible de tu recibo es relativamente reciente. Si no "
                f"reconoces el valor que figura, contrástalo en la Sede del "
                f"Catastro.</li>"
            )

    rustico = row.get("oficial_tipo_rustica")
    if rustico:
        rustico = float(rustico)
        if abs(rustico - tipo) > 1e-9:
            puntos.append(
                f"<li>Las fincas rústicas de {name} tributan al {fmt_pct(rustico)}, "
                f"frente al {fmt_pct(tipo)} de urbana: comprueba en qué epígrafe está "
                f"tu parcela.</li>"
            )
        else:
            puntos.append(
                f"<li>En {name} rústica y urbana comparten tipo ({fmt_pct(tipo)}), así "
                f"que la diferencia de cuota vendrá solo del valor catastral.</li>"
            )

    prov_tipos = [float(r["oficial_tipo_urbana"]) for r in prov_rows]
    if len(prov_tipos) >= 3:
        mediana = statistics.median(prov_tipos)
        if tipo > mediana:
            puntos.append(
                f"<li>El tipo de {name} está por encima de la mediana de {prov}, así "
                f"que compensa comprobar si te corresponde alguna de las "
                f"bonificaciones previstas en el TRLRHL y solicitarla en plazo.</li>"
            )
        else:
            puntos.append(
                f"<li>El tipo de {name} está en la mitad baja de {prov}, pero las "
                f"bonificaciones nunca se aplican de oficio: hay que pedirlas.</li>"
            )

    bice = imp and to_float(val(imp, "C05"))
    if bice and abs(bice - tipo) > 1e-9:
        puntos.append(
            f"<li>Si tu inmueble es de características especiales (presas, autopistas, "
            f"centrales, aeropuertos), en {name} tributa al {fmt_pct(bice)}.</li>"
        )

    serie = row.get("poblacion_serie") or []
    if len(serie) >= 2 and serie[-1][1] < serie[0][1]:
        puntos.append(
            f"<li>{name} ha perdido población desde {serie[0][0]}: cuando el coste del "
            f"servicio de residuos se reparte entre menos vecinos, la tasa tiende a "
            f"subir. Vigila el importe de basuras del próximo recibo.</li>"
        )

    if not puntos:
        puntos.append(
            f"<li>Contrasta el tipo del {fmt_pct(tipo)} y el resto de datos de esta "
            f"ficha con la ordenanza fiscal de {name} antes de pagar.</li>"
        )

    return (
        "\n        <ul>\n          " + "\n          ".join(puntos)
        + f"\n        </ul>\n        <p style=\"font-size:.82rem;color:var(--mid)\">"
        f"A partir de los datos oficiales de {ejercicio}.</p>"
    )


def comparativa_otros_tributos(row: dict, prov_rows: list[dict], imp: dict | None,
                               impuestos: dict | None) -> str:
    """Compara el ICIO y el IVTM del municipio con el resto de su provincia."""
    if not imp or not impuestos:
        return ""
    name = row["nombre"]
    prov = row["provincia"]

    def dato(r: dict, codigo: str) -> float | None:
        d = impuestos.get(r.get("oficial_codigo_ine") or "")
        return to_float(val(d, codigo)) if d else None

    frases = []
    for codigo, plantilla in (
        ("C17", "icio"),
        ("C19", "ivtm"),
    ):
        propio = to_float(val(imp, codigo))
        if propio is None:
            continue
        otros = [dato(r, codigo) for r in prov_rows]
        otros = [x for x in otros if x is not None]
        if len(otros) < 3:
            continue
        mediana = statistics.median(otros)
        orden = sorted(otros, reverse=True)
        puesto = orden.index(propio) + 1
        if plantilla == "icio":
            rel = (
                "por encima" if propio > mediana
                else "por debajo" if propio < mediana else "igual"
            )
            frases.append(
                f"el ICIO de las obras es del {fmt_pct(propio)}, {rel} de la mediana "
                f"de {prov} ({fmt_pct(mediana)})"
            )
        else:
            frases.append(
                f"un turismo de 8 a 11,99 CV paga {fmt_num(propio, 2)} € al año, el "
                f"{ordinal(puesto)} más caro de los {len(otros)} municipios de {prov} "
                f"de la guía (mediana: {fmt_num(mediana, 2)} €)"
            )
    if not frases:
        return ""
    return f"<p>Más allá del IBI, en {name} " + " y ".join(frases) + ".</p>"


# --------------------------------------------------------------------------- #
# 1-7: limpieza
# --------------------------------------------------------------------------- #
ORIENT_SPAN = '<span style="color:var(--mid)">[Importe orientativo, sin contrastar.]</span>'
ORIENT_RE = re.compile(
    r'(?:<span style="color:var\(--mid\)">\[Importe orientativo, sin contrastar\.\]</span>\s*){2,}'
)

SEDE_MANGLED_RE = re.compile(
    r'<li><strong>Sede electrónica:</strong> <a href="(?P<url>[^"]+)"[^>]*>.*?</a>'
    r' para consultar el valor catastral de tu inmueble\.</li>'
)
SEDE_OK_RE = re.compile(
    r'<li><strong>Sede electrónica:</strong> <a href="(?P<url>[^"]+)"[^>]*>[^<]*</a></li>'
)
CATASTRO_LI_RE = re.compile(
    r'\s*<li><strong>Catastro:</strong>.*?</li>', re.S
)
TIPOS_LI_RE = re.compile(
    r'<li><strong>Tipos oficiales:</strong>.*?</li>', re.S
)
ESTADO_RE = re.compile(
    r'<h3>Estado de los datos de esta ficha</h3>\s*<p style="font-size:\.9rem">.*?</p>',
    re.S,
)
VERIFICA_RE = re.compile(
    r'<div class="note"><strong>⚠️ Verifica antes de pagar:</strong>.*?</div>', re.S
)
INE_GENERIC = (
    " Es el dato que se usa para clasificar al municipio en los tramos que "
    "aplican algunas ordenanzas fiscales."
)
BONI_MAX_RE = re.compile(
    r'Son los <strong>máximos legales</strong> \(arts\. 73 y 74 TRLRHL\); '
    r'el porcentaje concreto lo fija la ordenanza y hay que solicitarlo\.'
)
CALENDARIO_RE = re.compile(
    r'(<h2>Cuándo se paga el IBI en [^<]+ y quién lo cobra</h2>\s*)(.*?)(\s*</section>)',
    re.S,
)
RECAUDADOR_RE = re.compile(
    r'los presta <a href="(?P<url>[^"]+)"[^>]*>(?P<name>[^<]+)</a>'
)
SIDEBAR_RE = re.compile(
    r'<p style="font-size:0\.8rem;color:var\(--mid\);margin-bottom:6px">'
    r'(?:Coste|IBI) anual estimado[^<]*</p>\s*'
    r'<table style="width:100%;font-size:0\.8rem">\s*'
    r'<tr><td>IBI \(VC (?P<vc>[\d.]+) €\)</td>.*?</table>',
    re.S,
)
DATOS_PERIODO_RE = re.compile(
    r'<li><strong>Período de pago:</strong>[^<]*'
    r'<span style="color:var\(--mid\);font-size:\.85em">\(orientativo\)</span></li>'
)
DATOS_BASURA_RE = re.compile(
    r'\s*<li><strong>Basura vivienda:</strong>[^<]*'
    r'<span style="color:var\(--mid\);font-size:\.85em">\(orientativo\)</span></li>'
)
META_DESC_RE = re.compile(r'<meta name="description" content="[^"]*">')
FOOTER_VIEJO = "Datos orientativos basados en ordenanzas fiscales municipales."
FOOTER_NUEVO = (
    "Datos del Ministerio de Hacienda, el INE y el BOE, con la fecha de "
    "comprobación en cada página."
)
LGT_URL = "https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186"
CONTEXTO_ANCHOR_RE = re.compile(
    r'(\s*<section class="sec">\s*<h2>(?:Consejo práctico para|Qué revisar en tu '
    r'recibo de) )'
)
CONTEXTO_EXISTING_RE = re.compile(
    r'\s*<section class="sec" id="contexto">.*?</section>', re.S
)


def build_contexto(row: dict, prov_rows: list[dict], ccaa_rows: list[dict],
                   ccaa_label: str, imp: dict | None = None,
                   impuestos: dict | None = None) -> str:
    name = row["nombre"]
    prov = row["provincia"]
    tipo = float(row["oficial_tipo_urbana"])
    ejercicio = row.get("oficial_ejercicio", "2025")

    prov_sorted = sorted(prov_rows, key=lambda r: -float(r["oficial_tipo_urbana"]))
    pos = next(i for i, r in enumerate(prov_sorted, 1) if r["slug"] == row["slug"])
    prov_n = len(prov_sorted)
    prov_tipos = [float(r["oficial_tipo_urbana"]) for r in prov_rows]
    prov_median = statistics.median(prov_tipos)

    ccaa_tipos = [float(r["oficial_tipo_urbana"]) for r in ccaa_rows]
    ccaa_mean = sum(ccaa_tipos) / len(ccaa_tipos)
    ccaa_min = min(ccaa_rows, key=lambda r: float(r["oficial_tipo_urbana"]))
    ccaa_max = max(ccaa_rows, key=lambda r: float(r["oficial_tipo_urbana"]))

    vc = 50000
    cuota = vc * tipo / 100
    cuota_median = vc * prov_median / 100
    diff = cuota - cuota_median
    gap = abs(tipo - prov_median)

    parts = []

    # Párrafo 1: posición en la provincia
    if prov_n >= 3:
        if abs(gap) < 0.0005:
            comp = (
                f"coincide con la mediana provincial ({fmt_pct(prov_median)})"
            )
        elif tipo > prov_median:
            comp = (
                f"queda {fmt_num(gap, 3)} puntos por encima de la mediana provincial "
                f"({fmt_pct(prov_median)}), lo que para un valor catastral de 50.000 € "
                f"supone {fmt_eur(abs(diff))} más al año ({fmt_eur(cuota)} frente a "
                f"{fmt_eur(cuota_median)})"
            )
        else:
            comp = (
                f"queda {fmt_num(gap, 3)} puntos por debajo de la mediana provincial "
                f"({fmt_pct(prov_median)}), lo que para un valor catastral de 50.000 € "
                f"supone {fmt_eur(abs(diff))} menos al año ({fmt_eur(cuota)} frente a "
                f"{fmt_eur(cuota_median)})"
            )
        parts.append(
            f"<p>Con un tipo de gravamen urbano del {fmt_pct(tipo)}, {name} ocupa el "
            f"puesto {pos} de los {prov_n} municipios de {prov} que recoge esta guía "
            f"ordenados de mayor a menor. {name[0].upper() + name[1:]} {comp}.</p>"
        )
    else:
        parts.append(
            f"<p>El tipo de gravamen urbano de {name} es del {fmt_pct(tipo)} en el "
            f"ejercicio {ejercicio}. Para un valor catastral de 50.000 € la cuota "
            f"íntegra sería de {fmt_eur(cuota)} al año antes de bonificaciones.</p>"
        )

    # Párrafo 2: contexto autonómico
    if len(ccaa_rows) >= 3:
        parts.append(
            f"<p>En el conjunto de {ccaa_label} esta guía analiza "
            f"{len(ccaa_rows)} municipios: el tipo más bajo es el de "
            f"<a href=\"{REL}{ccaa_min['ccaa']}/{ccaa_min['provincia_slug']}/"
            f"{ccaa_min['slug']}/\">{ccaa_min['nombre']}</a> "
            f"({fmt_pct(float(ccaa_min['oficial_tipo_urbana']))}) y el más alto el de "
            f"<a href=\"{REL}{ccaa_max['ccaa']}/{ccaa_max['provincia_slug']}/"
            f"{ccaa_max['slug']}/\">{ccaa_max['nombre']}</a> "
            f"({fmt_pct(float(ccaa_max['oficial_tipo_urbana']))}), con una media de "
            f"{fmt_pct(round(ccaa_mean, 4))}.</p>"
        )

    # Párrafo 3: evolución y valores catastrales
    anterior = row.get("oficial_tipo_urbana_anterior")
    ej_ant = row.get("oficial_ejercicio_anterior", "2024")
    evo = ""
    if anterior is not None:
        anterior = float(anterior)
        if abs(anterior - tipo) < 1e-9:
            evo = (
                f"{name} mantiene el mismo tipo urbano que en {ej_ant} "
                f"({fmt_pct(tipo)}, sin variación)."
            )
        elif tipo > anterior:
            evo = (
                f"El tipo urbano de {name} subió del {fmt_pct(anterior)} de {ej_ant} "
                f"al {fmt_pct(tipo)} de {ejercicio}."
            )
        else:
            evo = (
                f"El tipo urbano de {name} bajó del {fmt_pct(anterior)} de {ej_ant} "
                f"al {fmt_pct(tipo)} de {ejercicio}."
            )
    ano_val = row.get("oficial_ano_valores_catastrales")
    val = ""
    if ano_val and str(ano_val).isdigit():
        antig = CURRENT_YEAR - int(ano_val)
        val = (
            f" Sus valores catastrales de urbana provienen de la ponencia de "
            f"{ano_val}, de hace {antig} años."
        )
    if evo or val:
        parts.append(f"<p>{evo}{val}</p>")

    # Párrafo 4: población y su evolución (serie oficial del INE)
    pob = row.get("poblacion_oficial")
    serie = row.get("poblacion_serie") or []
    if pob:
        pos_txt = ""
        if prov_n >= 3:
            prov_pob = sorted(
                (r for r in prov_rows if r.get("poblacion_oficial")),
                key=lambda r: -int(r["poblacion_oficial"]),
            )
            try:
                pos_pob = next(
                    i for i, r in enumerate(prov_pob, 1) if r["slug"] == row["slug"]
                )
                pos_txt = (
                    f" Es el {ordinal(pos_pob)} municipio más poblado de los "
                    f"{len(prov_pob)} de {prov} que recoge la guía."
                )
            except StopIteration:
                pass
        if len(serie) >= 2:
            (y0, p0), (y1, p1) = serie[0], serie[-1]
            delta = p1 - p0
            pct = (delta / p0 * 100) if p0 else 0
            if delta > 0:
                mov = (
                    f"ha ganado {fmt_num(delta)} habitantes desde {y0} "
                    f"(+{fmt_num(pct, 1)} %)"
                )
            elif delta < 0:
                mov = (
                    f"ha perdido {fmt_num(-delta)} habitantes desde {y0} "
                    f"({fmt_num(pct, 1)} %)"
                )
            else:
                mov = f"tiene los mismos habitantes que en {y0}"
            parts.append(
                f"<h3>Población de {name} y evolución del padrón</h3>\n"
                f"        <p>Con {fmt_num(p1)} habitantes en {y1}, {name} {mov}."
                f"{pos_txt}</p>"
            )
            trs = []
            prev = None
            for ano, valor in serie:
                if prev is None:
                    var = "—"
                else:
                    d = valor - prev
                    var = f"{'+' if d > 0 else ''}{fmt_num(d)}"
                trs.append(
                    f'            <tr><td>{ano}</td><td class="v">{fmt_num(valor)}</td>'
                    f'<td>{var}</td></tr>'
                )
                prev = valor
            fuente = row.get(
                "poblacion_fuente_url", "https://www.ine.es"
            )
            parts.append(
                '<table class="dt">\n'
                '          <thead><tr><th>Año</th><th>Habitantes</th>'
                '<th>Variación</th></tr></thead>\n'
                '          <tbody>\n' + "\n".join(trs) + "\n"
                '          </tbody>\n'
                '        </table>\n'
                f'        <p style="font-size:.82rem;color:var(--mid)">Fuente: '
                f'<a href="{fuente}" target="_blank" rel="nofollow noopener">INE</a>, '
                f'cifras oficiales del padrón municipal a 1 de enero de cada año. '
                f'<a href="{REL}municipios/" style="color:var(--accent);'
                f'font-weight:600">Comparador de los 134 municipios →</a></p>'
            )
        elif pos_txt:
            parts.append(
                f"<p>{name} tiene {fmt_num(int(pob))} habitantes.{pos_txt}</p>"
            )

    extra = comparativa_otros_tributos(row, prov_rows, imp, impuestos)
    if extra:
        parts.append(extra)

    body = "\n        ".join(parts)
    # Cuando el municipio da nombre a su provincia («Comparación con Ourense y
    # Galicia» en la ficha de Ourense) hay que desambiguar.
    prov_txt = f"la provincia de {prov}" if prov == name else prov
    return (
        f'\n      <section class="sec" id="contexto">\n'
        f'        <h2>¿Es alto el IBI de {name}? Comparación con {prov_txt} y '
        f'{ccaa_label}</h2>\n        {body}\n      </section>\n'
    )


def polish(row: dict, prov_rows: list[dict], ccaa_rows: list[dict],
           ccaa_label: str, stats: Counter, imp: dict,
           impuestos: dict) -> tuple[str, str]:
    path = page_path(row)
    text = original = path.read_text(encoding="utf-8")
    name = row["nombre"]

    # 1. avisos duplicados
    def collapse(m: re.Match) -> str:
        stats["orientativo_colapsado"] += 1
        return ORIENT_SPAN + " "

    text = ORIENT_RE.sub(collapse, text)

    # 2/3. sede + catastro
    sede_url = ""
    m = SEDE_MANGLED_RE.search(text)
    if m:
        sede_url = m.group("url")
        stats["sede_reparada"] += 1
        text = SEDE_MANGLED_RE.sub(
            f'<li><strong>Sede electrónica:</strong> <a href="{sede_url}" '
            f'target="_blank" rel="nofollow noopener">{sede_url}</a></li>',
            text,
        )
    else:
        m = SEDE_OK_RE.search(text)
        if m:
            sede_url = m.group("url")
    if CATASTRO_LI_RE.search(text):
        stats["catastro_li_eliminado"] += 1
        text = CATASTRO_LI_RE.sub("", text)

    # 4. bloque de fuentes compacto
    fecha = row.get("oficial_comprobado_el", "2026-07-25")
    try:
        y, mo, d = fecha.split("-")
        fecha_es = f"{d}/{mo}/{y}"
    except ValueError:
        fecha_es = fecha
    if ESTADO_RE.search(text):
        stats["estado_compactado"] += 1
        text = ESTADO_RE.sub(
            f'<p style="font-size:.9rem"><strong>Verificado</strong> en el Ministerio '
            f'de Hacienda el {fecha_es}: tipo urbano, tipo rústico y año de los valores '
            f'catastrales de {name}. <strong>No publicado</strong>: el importe de la '
            f'tasa de residuos y las fechas de cobro, porque no hay fuente primaria '
            f'que los respalde. '
            f'<a href="{REL}metodologia/" style="color:var(--accent);font-weight:600">'
            f'Cómo verificamos cada dato →</a></p>',
            text,
            count=1,
        )
    if TIPOS_LI_RE.search(text):
        stats["tipos_li_compactado"] += 1
        text = TIPOS_LI_RE.sub(
            f'<li><strong>Tipos de IBI:</strong> <a href="{HACIENDA_URL}" '
            f'target="_blank" rel="nofollow noopener">Ministerio de Hacienda</a>, '
            f'ejercicio {row.get("oficial_ejercicio", "2025")}.</li>',
            text,
            count=1,
        )
    if VERIFICA_RE.search(text):
        stats["verifica_compactado"] += 1
        text = VERIFICA_RE.sub(
            f'<div class="note"><strong>⚠️ Antes de pagar:</strong> el '
            f'{fmt_pct(float(row["oficial_tipo_urbana"]))} es el tipo que el Ministerio '
            f'de Hacienda publica para {name} en {row.get("oficial_ejercicio", "2025")}; '
            f'el pleno puede haberlo cambiado para 2026 y los porcentajes de '
            f'bonificación los fija la ordenanza. Contrástalo antes de pagar.'
            f'</div>',
            text,
            count=1,
        )

    # 4b. pie de página: ya no tomamos los datos de las ordenanzas
    if FOOTER_VIEJO in text:
        stats["footer_fuentes_corregido"] += 1
        text = text.replace(FOOTER_VIEJO, FOOTER_NUEVO)

    # 5. frase genérica del INE
    if INE_GENERIC in text:
        stats["frase_ine_eliminada"] += 1
        text = text.replace(INE_GENERIC, "")

    # 6. bonificaciones
    if BONI_MAX_RE.search(text):
        stats["boni_personalizado"] += 1
        text = BONI_MAX_RE.sub(
            f"Topes del TRLRHL (arts. 73-74); el porcentaje real lo fija la "
            f"ordenanza de {name} y siempre hay que solicitarlo.",
            text,
            count=1,
        )

    # 7. calendario de cobro
    def rewrite_cal(m: re.Match) -> str:
        head, body, tail = m.group(1), m.group(2), m.group(3)
        rec = RECAUDADOR_RE.search(body)
        if rec:
            first = (
                f'<p>En la provincia de {row["provincia"]} la recaudación de los '
                f'tributos municipales de buena parte de los ayuntamientos la gestiona '
                f'<a href="{rec.group("url")}" target="_blank" rel="nofollow noopener">'
                f'{rec.group("name")}</a>, que es donde se publica el calendario de '
                f'cobro.</p>'
            )
            donde = rec.group("name")
        else:
            first = (
                f'<p>En {name} la gestión y el cobro del IBI los lleva directamente el '
                f'ayuntamiento, que publica su calendario cada ejercicio.</p>'
            )
            donde = f"la web del Ayuntamiento de {name}"
        second = (
            f'<p>No damos fechas concretas: el calendario se aprueba cada ejercicio y '
            f'lo publica {donde}. Si la ordenanza no señala otro plazo, el del art. '
            f'62.3 de la <a href="{LGT_URL}" target="_blank" rel="nofollow noopener">'
            f'Ley General Tributaria</a> va del 1 de septiembre al 20 de noviembre.</p>'
        )
        third = (
            f'<p><a href="{REL}ibi-2026/#recargos" style="color:var(--accent);'
            f'font-weight:600">Qué recargo se aplica si pagas fuera de plazo →</a></p>'
        )
        stats["calendario_reescrito"] += 1
        return head + "\n        ".join([first, second, third]) + tail

    text = CALENDARIO_RE.sub(rewrite_cal, text, count=1)

    # 8. barra lateral: el resumen sumaba IBI + un importe de basuras sin fuente
    tipo = float(row["oficial_tipo_urbana"])

    def fix_resumen(m: re.Match) -> str:
        vc = int(m.group("vc").replace(".", ""))
        cuota = vc * tipo / 100
        stats["resumen_lateral_sin_basuras"] += 1
        return (
            f'<p style="font-size:0.8rem;color:var(--mid);margin-bottom:6px">IBI anual '
            f'estimado para un piso de valor catastral medio en {name}:</p>\n'
            f'        <table style="width:100%;font-size:0.8rem">\n'
            f'          <tr><td>IBI (VC {fmt_num(vc)} €)</td>'
            f'<td style="text-align:right;font-weight:700;color:var(--accent)">'
            f'{fmt_eur(cuota)}</td></tr>\n'
            f'          <tr><td>Equivalente mensual</td>'
            f'<td style="text-align:right;font-weight:700;color:var(--accent)">'
            f'{fmt_num(cuota / 12, 2)} €/mes</td></tr>\n'
            f'          <tr style="border-top:2px solid var(--ink)"><td><strong>Tipo '
            f'urbano {row.get("oficial_ejercicio", "2025")}</strong></td>'
            f'<td style="text-align:right;font-weight:900;color:var(--ink)">'
            f'{fmt_pct(tipo)}</td></tr>\n'
            f'        </table>'
        )

    text = SIDEBAR_RE.sub(fix_resumen, text, count=1)

    # 8a. «Datos clave»: fuera el importe de basuras y las fechas sin contrastar
    if DATOS_BASURA_RE.search(text):
        stats["datos_clave_basuras_retirada"] += 1
        ano_val = row.get("oficial_ano_valores_catastrales")
        nuevo = ""
        if ano_val:
            nuevo = (
                f'\n        <li><strong>Valores catastrales:</strong> '
                f'<span class="v">{ano_val}</span> '
                f'<span style="color:var(--mid);font-size:.85em">(año de los valores, '
                f'Hacienda)</span></li>'
            )
        text = DATOS_BASURA_RE.sub(nuevo, text, count=1)
    if DATOS_PERIODO_RE.search(text):
        stats["datos_clave_plazo_legal"] += 1
        text = DATOS_PERIODO_RE.sub(
            '<li><strong>Plazo de pago:</strong> lo fija la ordenanza '
            '<span style="color:var(--mid);font-size:.85em">(por defecto, 1 sep – '
            '20 nov: art. 62.3 LGT)</span></li>',
            text,
            count=1,
        )

    # 8b. meta description: citaba un importe de basuras y bonificaciones que la
    #     propia ficha ya no afirma. Se reconstruye solo con datos verificados.
    rustica = row.get("oficial_tipo_rustica")
    desc = (
        f"IBI de {name} 2026: tipo urbano {fmt_pct(tipo)}"
        + (f" y rústico {fmt_pct(float(rustica))}" if rustica else "")
        + " según el Ministerio de Hacienda, cuota según valor catastral, plusvalía, "
        "impuesto de circulación, bonificaciones y tasa de residuos."
    )
    nueva_meta = f'<meta name="description" content="{desc}">'
    if META_DESC_RE.search(text) and nueva_meta not in text:
        stats["meta_description_reescrita"] += 1
        text = META_DESC_RE.sub(nueva_meta, text, count=1)

    # 8b. normaliza las secciones con dos plantillas y quita lo no verificable
    text = normalise_sections(row, text, prov_rows, stats, imp)

    # 9. secciones propias: comparativa y resto de tributos municipales
    text = CONTEXTO_EXISTING_RE.sub("", text)
    text = OTROS_IMPUESTOS_EXISTING_RE.sub("", text)
    bloques = build_contexto(row, prov_rows, ccaa_rows, ccaa_label, imp, impuestos)
    otros = build_otros_impuestos(row, imp) if imp else None
    if otros:
        bloques += otros
        stats["otros_impuestos_insertado"] += 1
    if CONTEXTO_ANCHOR_RE.search(text):
        text = CONTEXTO_ANCHOR_RE.sub(bloques.replace("\\", "\\\\") + r"\1", text, count=1)
        stats["contexto_insertado"] += 1
    else:
        stats["contexto_SIN_ANCLA"] += 1

    # 10. FAQ: 73 fichas llevaban un FAQPage con la tasa de basuras, las fechas de
    #     cobro y unos porcentajes de bonificación sin fuente, y ninguna tenía FAQ
    #     visible: datos estructurados sin contenido visible, que las directrices
    #     de Google no admiten. Reescribirla con datos verificados obligaba a
    #     repetir lo que la propia ficha ya dice unos párrafos antes (el texto de
    #     plantilla subía del 35% al 48%), y desde 2023 Google reserva los
    #     resultados enriquecidos de FAQ a sitios oficiales de sanidad y
    #     administración, así que no aportaba nada. Se elimina de las fichas; los
    #     pilares autonómicos sí la conservan, porque allí cada respuesta se
    #     calcula con los datos de esa comunidad.
    text = FAQ_SECTION_RE.sub("", text)
    if FAQ_JSONLD_RE.search(text):
        text = FAQ_JSONLD_RE.sub("", text, count=1)
        stats["faq_jsonld_sin_respaldo_eliminado"] += 1

    # limpieza de espacios sobrantes
    text = re.sub(r"\n(?:[ \t]*\n){2,}", "\n\n", text)
    return original, text


# --------------------------------------------------------------------------- #
# Segunda pasada: normaliza las secciones que tenían dos plantillas y elimina
# las afirmaciones que no podemos sostener con una fuente.
# --------------------------------------------------------------------------- #
SECTION_END = "\n      </section>"


def replace_section(text: str, h2_pattern: str, new_body: str,
                    new_h2: str | None = None) -> tuple[str, bool]:
    """Sustituye el cuerpo (y opcionalmente el <h2>) de una sección."""
    m = re.search(h2_pattern, text)
    if not m:
        return text, False
    end = text.find("</section>", m.end())
    if end == -1:
        return text, False
    start_line = text.rfind("\n", 0, end)
    head = new_h2 if new_h2 is not None else m.group(0)
    return text[: m.start()] + head + new_body + text[start_line:], True


LEY7 = "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5809"

H2_BASURAS = [
    "Tasa de basuras en {n}: dónde está la tarifa",
    "Tasa de basuras en {n}: qué obliga la ley y dónde consultarla",
    "Tasa de residuos en {n}: cómo saber cuánto pagas",
]
NOTA_BASURAS = [
    "ninguna administración del Estado las publica municipio a municipio (la ley "
    "solo obliga a comunicarlas a la comunidad autónoma, art. 11.5), así que "
    "preferimos el hueco a una cifra sin respaldo.",
    "no hay registro estatal: la ley solo obliga a comunicar la tasa a la comunidad "
    "autónoma (art. 11.5), y la fuente de la que tomamos los tipos de IBI cubre "
    "impuestos, no tasas.",
    "la tarifa vive solo en la ordenanza del pleno, publicada en el boletín "
    "provincial; no existe fuente estatal que las reúna (art. 11.5), y no vamos a "
    "publicar un importe que no podamos justificar.",
]


def build_basuras(row: dict, text: str) -> tuple[str, str]:
    """Sección de basuras sin importe: marco legal verificado y dónde buscarlo.

    El importe que se publicaba antes no tenía fuente (ver
    scripts/retirar_basuras.py). Lo que sí está verificado es el artículo 11 de la
    Ley 7/2022, así que la sección explica la obligación, por qué no hay dato
    agregado y qué mirar para obtener el propio.
    """
    name = row["nombre"]
    slug = row["slug"]
    h2 = f"<h2>{ancla(H2_BASURAS, slug).format(n=name)}</h2>"

    # Dónde buscar: sede o web del ayuntamiento si la hemos comprobado; si no,
    # el organismo provincial que recauda, que es donde acaba el recibo.
    destino = f"la web del Ayuntamiento de {name}"
    m = SEDE_OK_RE.search(text)
    url = m.group("url") if m else None
    if not url and row.get("web_oficial") and row.get("web_http_status") in (200, 308):
        url = row["web_oficial"]
    if url:
        destino = (
            f'<a href="{url}" target="_blank" rel="nofollow noopener">la sede '
            f'electrónica del Ayuntamiento de {name}</a>'
        )

    nota = ancla(NOTA_BASURAS, slug + "n")
    body = (
        f'\n        <p>{name} tiene que cobrar una tasa de residuos <strong>específica, '
        f'diferenciada y no deficitaria</strong>: lo exige el artículo 11.3 de la '
        f'<a href="{LEY7}" target="_blank" rel="nofollow noopener">Ley 7/2022</a> y el '
        f'plazo venció el 10 de abril de 2025.</p>\n'
        f'        <div class="note"><strong>Aquí no verás un importe:</strong> {nota} '
        f'La tarifa de {name} está en su ordenanza fiscal de residuos, en {destino}, y '
        f'en el concepto de residuos de tu recibo.</div>\n'
        f'        <p><a href="{REL}tasa-basuras/" style="color:var(--accent);'
        f'font-weight:600">Qué obliga la Ley 7/2022, qué reducciones puedes pedir y '
        f'cómo localizar tu tarifa →</a></p>'
    )
    return body, h2


FAQ_JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">\s*\{\s*"@context"\s*:\s*"https://schema\.org",\s*'
    r'"@type"\s*:\s*"FAQPage".*?</script>\n?',
    re.S,
)
FAQ_SECTION_RE = re.compile(
    r'\s*<section class="sec" id="faq">.*?</section>', re.S
)
FUENTES_ANCHOR_RE = re.compile(r'(\s*<section class="sec">\s*<h2>Fuentes oficiales)')


def normalise_sections(row: dict, text: str, prov_rows: list[dict],
                       stats: Counter, imp: dict) -> str:
    name = row["nombre"]
    prov = row["provincia"]
    esc = re.escape(name)

    # --- IBI: quita el comentario de mercado sin fuente y unifica el enlace ---
    text2 = re.sub(
        r'<h3>¿Cómo consultar tu valor catastral en la Sede del Catastro\?</h3>\s*<p>.*?</p>',
        f'<p><a href="{REL}valor-catastral/" style="color:var(--accent);'
        f'font-weight:600">→ {ancla(ANCLAS_CATASTRO, row["slug"]).capitalize()}</a></p>',
        text,
        count=1,
        flags=re.S,
    )
    if text2 != text:
        stats["catastro_parrafo_normalizado"] += 1
        text = text2
    text2 = text.replace(
        f"<h3>Cuotas estimadas según valor catastral real en {name}</h3>",
        f"<h3>Cuota de IBI en {name} según el valor catastral</h3>",
    ).replace(
        "<h3>Cuotas estimadas según valor catastral real</h3>",
        f"<h3>Cuota de IBI en {name} según el valor catastral</h3>",
    )
    if text2 != text:
        stats["encabezado_cuotas_corregido"] += 1
        text = text2

    # --- Basuras: se retira el importe sin fuente y se explica dónde está ---
    body, nuevo_h2 = build_basuras(row, text)
    text, ok = replace_section(
        text, rf'<h2>Tasa de (?:basuras|residuos) en {esc}[^<]*</h2>', body,
        new_h2=nuevo_h2
    )
    if ok:
        stats["basuras_sin_importe"] += 1

    # --- Plusvalía ---
    nueva_plus = build_plusvalia(row, imp) if imp else None
    if nueva_plus:
        body = "\n        " + nueva_plus.split("</h2>\n        ", 1)[1]
        nuevo_h2 = nueva_plus.split("</h2>", 1)[0] + "</h2>"
        text, ok = replace_section(
            text,
            rf'<h2>Plusvalía municipal en {esc}[^<]*</h2>',
            body,
            new_h2=nuevo_h2,
        )
        if ok:
            stats["plusvalia_datos_oficiales"] += 1
    else:
        incoherente = bool(imp) and not serie_plausible(
            [to_float(val(imp, c)) for c in PLUS_COEF]
        ) and any(to_float(val(imp, c)) is not None for c in PLUS_COEF)
        aviso = (
            f'El dato que Hacienda publica para {name} no encaja con el sistema '
            f'vigente desde el RDL 26/2021 (parece el porcentaje anual del sistema '
            f'anterior), así que no lo reproducimos.'
            if incoherente else
            f'Hacienda no publica los coeficientes de {name}.'
        )
        body = (
            f'\n        <p>Al vender, donar o heredar un inmueble urbano de {name} se '
            f'liquida la plusvalía municipal (IIVTNU) ante su ayuntamiento. Plazos: 30 '
            f'días hábiles en compraventa y donación, 6 meses en herencia.</p>\n'
            f'        <div class="note"><strong>⚖️ Coeficientes:</strong> {aviso} '
            f'Los fija la ordenanza de {name} dentro de los máximos del art. 107.4 '
            f'TRLRHL. <a href="{REL}plusvalia/#coeficientes" '
            f'style="color:var(--accent);font-weight:600">Coeficientes máximos '
            f'vigentes →</a></div>\n'
            f'        <p><a href="{REL}plusvalia/" style="color:var(--accent);'
            f'font-weight:600">Guía de la plusvalía: los dos métodos de cálculo, modelos, '
            f'exenciones y calculadora →</a></p>'
        )
        text, ok = replace_section(
            text, rf'<h2>Plusvalía municipal en {esc}[^<]*</h2>', body,
            new_h2=f"<h2>Plusvalía municipal en {name}</h2>",
        )
        if ok:
            stats["plusvalia_normalizada"] += 1

    # --- Tabla oficial: añade BICE y elimina el párrafo/nota redundantes ---
    bice = row.get("oficial_tipo_bice")
    ejercicio = row.get("oficial_ejercicio", "2025")
    if bice and f"Tipo de BICE ({ejercicio})" not in text:
        text2, n = re.subn(
            r'(<tr><td>Población oficial \()',
            f'<tr><td>Tipo de BICE ({ejercicio})</td><td>{fmt_pct(float(bice))}</td>'
            f'<td>Bienes inmuebles de características especiales</td></tr>\n'
            f'            \\1',
            text,
            count=1,
        )
        if n:
            stats["bice_anadido"] += 1
            text = text2
    text2 = re.sub(
        r'<p>[^<]*tiene <strong>[\d.]+ habitantes</strong> según las cifras oficiales '
        r'del padrón municipal a 1 de enero de \d+, publicadas por el '
        r'<a href="[^"]+"[^>]*>INE</a>\.[^<]*</p>\s*'
        r'<div class="note"><strong>📌 Ejercicio 2026:</strong>.*?</div>',
        f'<p style="font-size:.85rem;color:var(--mid)">Fuentes: '
        f'<a href="{row.get("poblacion_fuente_url", "https://www.ine.es")}" '
        f'target="_blank" rel="nofollow noopener">INE</a> (padrón 1/1/'
        f'{row.get("poblacion_ejercicio", 2025)}) y '
        f'<a href="{HACIENDA_URL}" target="_blank" rel="nofollow noopener">Hacienda</a> '
        f'({ejercicio}).</p>',
        text,
        count=1,
        flags=re.S,
    )
    if text2 != text:
        stats["tabla_oficial_compactada"] += 1
        text = text2

    # --- Bonificaciones: requisitos más cortos y plazo sin inventar fecha ---
    text2 = text.replace(
        f"<td>Título vigente + vivienda habitual + empadronamiento en {name}</td>",
        f"<td>Título en vigor y vivienda habitual en {name}</td>",
    ).replace(
        "<td>Certificado instalador autorizado + boletín eléctrico + solicitud en el "
        "ejercicio siguiente a la instalación</td>",
        "<td>Instalación certificada y solicitud tras darla de alta</td>",
    )
    if text2 != text:
        stats["requisitos_acortados"] += 1
        text = text2
    text2 = re.sub(
        r'<div class="note"><strong>📅 Solicitud:</strong>.*?</div>',
        f'<div class="note"><strong>📅 Plazo:</strong> el que fije la ordenanza de '
        f'{name}. <a href="{REL}bonificaciones/" style="color:var(--accent);'
        f'font-weight:600">Requisitos, documentación y bonificaciones estatales '
        f'(VPO, rehabilitación, SEPA) →</a></div>',
        text,
        count=1,
        flags=re.S,
    )
    if text2 != text:
        stats["solicitud_sin_fecha_inventada"] += 1
        text = text2
    text2 = re.sub(
        r'\s*<p><a href="\.\./\.\./\.\./bonificaciones/"[^>]*>→ Guía completa de '
        r'bonificaciones del IBI</a></p>',
        "",
        text,
        count=1,
    )
    if text2 != text:
        stats["enlace_boni_duplicado_eliminado"] += 1
        text = text2

    # --- Entradilla del IBI: sólo el dato oficial, sin lecturas de mercado ---
    tipo_pct = fmt_pct(float(row["oficial_tipo_urbana"]))
    text2, n = re.subn(
        rf'(<h2>IBI 2026 en {esc}: cuánto se paga y cuándo</h2>\s*<p>)(?!El tipo del IBI '
        rf'urbano en )(.*?)(</p>)',
        lambda m: (
            m.group(1)
            + f'El tipo del IBI urbano en {name} es del <strong>{tipo_pct}</strong>, '
            f'según los datos del ejercicio {ejercicio} que publica el '
            f'<a href="{HACIENDA_URL}" target="_blank" rel="nofollow noopener">'
            f'Ministerio de Hacienda</a>.'
            + m.group(3)
        ),
        text,
        count=1,
        flags=re.S,
    )
    if n:
        stats["entradilla_ibi_sin_relato"] += 1
        text = text2

    # --- Consejo práctico: fuera las afirmaciones que no podemos sostener ---
    if RIESGO_RE.search(row.get("consejo") or ""):
        checklist = build_checklist(row, prov_rows, imp)
        text2, ok = replace_section(
            text,
            rf'<h2>(?:Consejo práctico para|Qué revisar en tu recibo de) {esc}</h2>',
            checklist,
            new_h2=f"<h2>Qué revisar en tu recibo de {name}</h2>",
        )
        if ok and text2 != text:
            stats["consejo_sustituido_por_checklist"] += 1
            text = text2

    # --- El enlace del Catastro ahora tiene guía propia ---
    # Apuntaba a /ibi-2026/#catastro, que es una sección dentro de otra guía.
    # /valor-catastral/ cubre el tema completo, así que las 134 fichas pasan a
    # enlazarla, con ancla repartida para no repetir 134 veces el mismo texto.
    text2, n = re.subn(
        r'<p><a href="(?:\.\./)+(?:ibi-2026/#catastro|valor-catastral/)"[^>]*>→ [^<]*</a></p>',
        f'<p><a href="{REL}valor-catastral/" style="color:var(--accent);'
        f'font-weight:600">→ '
        f'{ancla(ANCLAS_CATASTRO, row["slug"])[0].upper()}'
        f'{ancla(ANCLAS_CATASTRO, row["slug"])[1:]}</a></p>',
        text,
        count=1,
    )
    if n and text2 != text:
        stats["enlace_a_guia_del_valor_catastral"] += 1
        text = text2

    # --- Recortes finales de texto plantilla (idempotentes) ---
    recortes = [
        (
            r'(?:Son los <strong>máximos legales</strong> \(arts\. 73 y 74 TRLRHL\); '
            r'el porcentaje concreto lo fija la ordenanza y hay que solicitarlo\.'
            r'|Los porcentajes de la tabla son los <strong>topes que fija el '
            r'TRLRHL</strong> \(arts\. 73 y 74\):[^<]*?solicitarlo\.)',
            f"Topes del TRLRHL (arts. 73-74); el porcentaje real lo fija la ordenanza "
            f"de {name} y siempre hay que solicitarlo.",
            "topes_legales_acortados",
        ),
        (
            r'<div class="note"><strong>📅 (?:Solicitud|Cómo se piden):</strong>.*?</div>',
            f'<div class="note"><strong>📅 Plazo:</strong> el que fije la ordenanza de '
            f'{name}. <a href="{REL}bonificaciones/" style="color:var(--accent);'
            f'font-weight:600">Requisitos, documentación y bonificaciones estatales '
            f'(VPO, rehabilitación, SEPA) →</a></div>',
            "plazo_bonificaciones_acortado",
        ),
        (
            r'<p style="font-size:\.85rem;color:var\(--mid\)">Población: '
            r'<a href="([^"]+)"[^>]*>INE</a>, cifras oficiales del padrón a 1 de enero '
            r'de (\d+)\. Tipos: <a href="[^"]+"[^>]*>Ministerio de Hacienda</a>, '
            r'ejercicio \d+; si el pleno de [^<]*? constará en su ordenanza fiscal\.</p>',
            f'<p style="font-size:.85rem;color:var(--mid)">Fuentes: '
            f'<a href="\\1" target="_blank" rel="nofollow noopener">INE</a> '
            f'(padrón 1/1/\\2) y <a href="{HACIENDA_URL}" target="_blank" '
            f'rel="nofollow noopener">Hacienda</a> ({ejercicio}).</p>',
            "fuentes_tabla_acortadas",
        ),
    ]
    for patron, reemplazo, clave in recortes:
        text2, n = re.subn(patron, reemplazo, text, count=1, flags=re.S)
        if n:
            stats[clave] += 1
            text = text2

    # --- Bloque de fuentes: una línea de estado, la sede y un aviso ---
    fecha = row.get("oficial_comprobado_el", "2026-07-25")
    try:
        y, mo, d = fecha.split("-")
        fecha_es = f"{d}/{mo}/{y}"
    except ValueError:
        fecha_es = fecha
    rec = RECAUDADORES.get(row["provincia_slug"]) or {}
    # `sede` arrastra dominios *.sedelectronica.es que ya comprobamos que no existen.
    sede_propia = row.get("sede") or ""
    if "sedelectronica.es" in sede_propia:
        sede_propia = ""
    sede_url = rec.get("url") or sede_propia
    sede_nombre = rec.get("nombre") or f"Ayuntamiento de {name}"
    sede_html = ""
    if sede_url:
        sede_html = (
            f'\n        <p style="font-size:.9rem"><strong>Dónde consultar y pagar:'
            f'</strong> <a href="{sede_url}" target="_blank" rel="nofollow noopener">'
            f'{sede_nombre}</a> · <a href="https://www.sedecatastro.gob.es" '
            f'target="_blank" rel="nofollow noopener">Sede del Catastro</a> para el '
            f'valor catastral.</p>'
        )
    body = (
        f'\n        <p style="font-size:.9rem"><strong>Verificado</strong> el {fecha_es} '
        f'en Hacienda: tipos de IBI y valores catastrales. <strong>No publicamos</strong> '
        f'el importe de la tasa de residuos ni las fechas de cobro: no hay fuente '
        f'primaria accesible. <a href="{REL}metodologia/" style="color:var(--accent);'
        f'font-weight:600">Metodología →</a></p>'
        + sede_html
        + f'\n        <div class="note"><strong>⚠️ Antes de pagar:</strong> el '
        f'{fmt_pct(float(row["oficial_tipo_urbana"]))} es el tipo oficial de '
        f'{ejercicio}; el pleno puede haberlo modificado para 2026 y las '
        f'bonificaciones hay que solicitarlas.</div>'
    )
    text2, ok = replace_section(text, r'<h2>Fuentes oficiales y verificación</h2>', body)
    if ok and text2 != text:
        stats["fuentes_compactadas"] += 1
        text = text2

    # --- Gráfico autonómico: menos texto de relleno ---
    text2 = re.sub(
        r'<p>Tipo de IBI urbano de [^<]*frente al resto de municipios de ([^<]+?) '
        r'recogidos en la guía \(<a ([^>]+)>tabla comparativa completa →</a>\)\.</p>',
        r'<p>Frente al resto de \1 (<a \2>tabla completa →</a>).</p>',
        text,
        count=1,
    )
    text2 = re.sub(
        r'<p style="font-size:0\.82rem;color:var\(--mid\);margin-top:10px">Fuente: '
        r'Ordenanzas fiscales municipales publicadas en los boletines oficiales '
        r'correspondientes \(2025-2026\)\.</p>',
        f'<p style="font-size:0.82rem;color:var(--mid);margin-top:10px">Fuente: '
        f'Ministerio de Hacienda ({ejercicio}).</p>',
        text2,
        count=1,
    )
    if text2 != text:
        stats["grafico_aligerado"] += 1
        text = text2

    # --- "Otros municipios": tabla comparativa de cuotas con enlaces ---
    peers = [r for r in prov_rows if r["slug"] != row["slug"]]
    if peers:
        rows_sorted = sorted(prov_rows, key=lambda r: -float(r["oficial_tipo_urbana"]))
        trs = []
        for r in rows_sorted:
            tipo = float(r["oficial_tipo_urbana"])
            cuota = fmt_eur(50000 * tipo / 100)
            if r["slug"] == row["slug"]:
                trs.append(
                    f'            <tr style="background:rgba(0,0,0,.04)">'
                    f'<td><strong>{r["nombre"]}</strong> (esta ficha)</td>'
                    f'<td class="v">{fmt_pct(tipo)}</td><td>{cuota}</td></tr>'
                )
            else:
                href = f'{REL}{r["ccaa"]}/{r["provincia_slug"]}/{r["slug"]}/'
                trs.append(
                    f'            <tr><td><a href="{href}">{r["nombre"]}</a></td>'
                    f'<td class="v">{fmt_pct(tipo)}</td><td>{cuota}</td></tr>'
                )
        body = (
            f'\n        <p>Cuota anual con un valor catastral de 50.000 € y el tipo '
            f'oficial de {ejercicio}:</p>\n'
            f'        <table class="dt">\n'
            f'          <thead><tr><th>Municipio</th><th>Tipo urbano</th>'
            f'<th>Cuota (VC 50.000 €)</th></tr></thead>\n'
            f'          <tbody>\n' + "\n".join(trs) + "\n"
            f'          </tbody>\n'
            f'        </table>\n'
            f'        <p style="font-size:.82rem;color:var(--mid)">Fuente: Ministerio '
            f'de Hacienda, ejercicio {ejercicio}.</p>'
        )
        text2, ok = replace_section(
            text,
            r'<h2>(?:Otros municipios de|IBI urbano comparado en) [^<]+</h2>',
            body,
            new_h2=f"<h2>IBI urbano comparado en {prov}</h2>",
        )
        if ok:
            stats["tabla_provincial_insertada"] += 1
            text = text2
    return text


# --------------------------------------------------------------------------- #
# Datos oficiales de plusvalía, ICIO, IAE e IVTM (Ministerio de Hacienda)
# --------------------------------------------------------------------------- #
IMPUESTOS_PATH = ROOT / "data" / "hacienda_impuestos.json"
PLUS_COEF = [f"C{n}" for n in range(51, 72)]
PLUS_TIPO = [f"C{n}" for n in range(72, 93)]
PERIODOS = ["Menos de 1 año"] + [f"{n} año{'s' if n > 1 else ''}" for n in range(1, 20)] \
    + ["20 años o más"]
IVTM_ETIQUETAS = {
    "C18": "Menos de 8 CV", "C19": "8 – 11,99 CV", "C20": "12 – 15,99 CV",
    "C21": "16 – 19,99 CV", "C22": "20 CV o más",
    "C23": "Menos de 21 plazas", "C24": "21 – 50 plazas", "C25": "Más de 50 plazas",
    "C26": "Menos de 1.000 kg", "C27": "1.000 – 2.999 kg",
    "C28": "3.000 – 9.999 kg", "C29": "Más de 9.999 kg",
    "C30": "Menos de 16 CV", "C31": "16 – 25 CV", "C32": "Más de 25 CV",
    "C33": "750 – 999 kg", "C34": "1.000 – 2.999 kg", "C35": "Más de 2.999 kg",
    "C36": "Ciclomotores", "C37": "Hasta 125 cc", "C38": "125 – 250 cc",
    "C39": "250 – 500 cc", "C40": "500 – 1.000 cc", "C41": "Más de 1.000 cc",
}
IVTM_GRUPOS = [
    ("Turismos", ["C18", "C19", "C20", "C21", "C22"]),
    ("Motocicletas y ciclomotores", ["C36", "C37", "C38", "C39", "C40", "C41"]),
    ("Camiones", ["C26", "C27", "C28", "C29"]),
    ("Autobuses", ["C23", "C24", "C25"]),
    ("Tractores", ["C30", "C31", "C32"]),
    ("Remolques y semirremolques", ["C33", "C34", "C35"]),
]


RECAUDADORES = json.loads(
    (ROOT / "data" / "recaudadores.json").read_text(encoding="utf-8")
).get("provincias", {})


def load_impuestos() -> dict:
    if not IMPUESTOS_PATH.exists():
        return {}
    return json.loads(IMPUESTOS_PATH.read_text(encoding="utf-8"))


def val(imp: dict, codigo: str) -> str | None:
    c = (imp.get("conceptos") or {}).get(codigo) or {}
    v = c.get("valor")
    return v if v not in (None, "", "-") else None


def to_float(texto: str | None) -> float | None:
    if not texto:
        return None
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def serie_plausible(coefs: list[float | None]) -> bool:
    """¿La serie encaja con el sistema vigente desde el RDL 26/2021?

    Los coeficientes del art. 107.4 TRLRHL van de 0,09 a 0,40. Algunos
    ayuntamientos siguen declarando el porcentaje anual del sistema anterior
    (valores de 0,01 a 0,04): reproducirlos como coeficientes daría un cálculo
    falso, así que en esos casos preferimos no publicar la tabla.
    """
    validos = [c for c in coefs if c is not None]
    return bool(validos) and 0.10 <= max(validos) <= 0.45


def build_plusvalia(row: dict, imp: dict) -> str | None:
    """Sección de plusvalía con los coeficientes y tipos reales del municipio."""
    name = row["nombre"]
    ejercicio = imp.get("ejercicio") or row.get("oficial_ejercicio", "2025")
    coefs = [to_float(val(imp, c)) for c in PLUS_COEF]
    tipos = [to_float(val(imp, c)) for c in PLUS_TIPO]
    if not any(c is not None for c in coefs) or not serie_plausible(coefs):
        return None

    trs = []
    for periodo, coef, tipo in zip(PERIODOS, coefs, tipos):
        if coef is None and tipo is None:
            continue
        coef_txt = fmt_num(coef, 2) if coef is not None else "—"
        tipo_txt = fmt_pct(tipo) if tipo is not None else "—"
        trs.append(
            f'            <tr><td>{periodo}</td><td class="v">{coef_txt}</td>'
            f'<td>{tipo_txt}</td></tr>'
        )

    # Ejemplo con los datos del propio municipio (10 años de tenencia).
    ejemplo = ""
    coef10, tipo10 = coefs[10], tipos[10]
    if coef10 and tipo10:
        suelo = 30000
        base = suelo * coef10
        cuota = base * tipo10 / 100
        ejemplo = (
            f'        <p><strong>Ejemplo en {name}:</strong> suelo de {fmt_num(suelo)} € '
            f'vendido a los 10 años → base {fmt_num(suelo)} × {fmt_num(coef10, 2)} = '
            f'{fmt_eur(base)}; cuota al {fmt_pct(tipo10)} = '
            f'<strong>{fmt_eur(cuota)}</strong>.</p>\n'
        )

    red107_3 = val(imp, "C12")
    red107_2 = val(imp, "C93")
    reducciones = ""
    extras = []
    if red107_3:
        extras.append(
            f"una reducción del {red107_3}% sobre los valores catastrales resultantes "
            f"de una valoración colectiva (art. 107.3 TRLRHL)"
        )
    if red107_2:
        extras.append(
            f"un coeficiente reductor del {red107_2}% sobre el valor del terreno "
            f"(art. 107.2.a TRLRHL)"
        )
    if extras:
        reducciones = (
            f'        <p>La ordenanza de {name} aplica además {" y ".join(extras)}.</p>\n'
        )

    return (
        f'<h2>Plusvalía municipal en {name}: coeficientes y tipos oficiales '
        f'{ejercicio}</h2>\n'
        f'        <p>Coeficientes y tipos del IIVTNU aprobados por {name} para '
        f'{ejercicio}: los reales, no los máximos estatales.</p>\n'
        f'        <table class="dt">\n'
        f'          <thead><tr><th>Años transcurridos</th><th>Coeficiente</th>'
        f'<th>Tipo de gravamen</th></tr></thead>\n'
        f'          <tbody>\n' + "\n".join(trs) + "\n"
        f'          </tbody>\n'
        f'        </table>\n'
        + ejemplo
        + reducciones
        + f'        <p><strong>Plazos:</strong> 30 días hábiles en compraventa y '
        f'donación, 6 meses en herencia. '
        f'<a href="{REL}plusvalia/" style="color:var(--accent);font-weight:600">'
        f'Los dos métodos de cálculo, modelos y exenciones →</a></p>'
    )


def build_otros_impuestos(row: dict, imp: dict) -> str | None:
    """ICIO, coeficientes de situación del IAE y tarifa completa del IVTM."""
    name = row["nombre"]
    ejercicio = imp.get("ejercicio") or row.get("oficial_ejercicio", "2025")
    icio = to_float(val(imp, "C17"))
    iae_max = to_float(val(imp, "C06"))
    iae_min = to_float(val(imp, "C07"))
    bloques = []

    filas = []
    if icio is not None:
        filas.append(
            f'            <tr><td>ICIO · construcciones, instalaciones y obras</td>'
            f'<td class="v">{fmt_pct(icio)}</td>'
            f'<td>Sobre el coste real y efectivo de la obra</td></tr>'
        )
    if iae_min is not None or iae_max is not None:
        rango = (
            f"{fmt_num(iae_min, 2)} – {fmt_num(iae_max, 2)}"
            if iae_min is not None and iae_max is not None
            else fmt_num(iae_max if iae_max is not None else iae_min, 2)
        )
        filas.append(
            f'            <tr><td>IAE · coeficiente de situación</td>'
            f'<td class="v">{rango}</td>'
            f'<td>Según la categoría de la calle donde está el local</td></tr>'
        )
    if filas:
        bloques.append(
            f'        <table class="dt">\n'
            f'          <thead><tr><th>Tributo</th><th>Valor {ejercicio}</th>'
            f'<th>Se aplica sobre</th></tr></thead>\n'
            f'          <tbody>\n' + "\n".join(filas) + "\n"
            f'          </tbody>\n        </table>'
        )

    ivtm_filas = []
    for titulo, codigos in IVTM_GRUPOS:
        sub = []
        for codigo in codigos:
            importe = to_float(val(imp, codigo))
            if importe is None:
                continue
            etiqueta = IVTM_ETIQUETAS.get(
                codigo, (imp["conceptos"][codigo].get("etiqueta") or "").rstrip(":")
            )
            sub.append(
                f'            <tr><td>{etiqueta}</td>'
                f'<td class="v">{fmt_num(importe, 2)} €/año</td></tr>'
            )
        if sub:
            ivtm_filas.append(
                f'            <tr><td colspan="2" style="background:rgba(0,0,0,.04)">'
                f'<strong>{titulo}</strong></td></tr>'
            )
            ivtm_filas.extend(sub)
    if ivtm_filas:
        bloques.append(
            f'        <h3>Impuesto de circulación (IVTM) en {name} {ejercicio}</h3>\n'
            f'        <p style="font-size:.85rem;color:var(--mid)">'
            f'<a href="{REL}impuesto-circulacion/" style="color:var(--accent);'
            f'font-weight:600">{ancla(ANCLAS_IVTM, name).capitalize()} →</a></p>\n'

            f'        <table class="dt">\n'
            f'          <thead><tr><th>Vehículo</th><th>Cuota anual</th></tr></thead>\n'
            f'          <tbody>\n' + "\n".join(ivtm_filas) + "\n"
            f'          </tbody>\n        </table>'
        )
    if not bloques:
        return None

    return (
        f'\n      <section class="sec" id="otros-impuestos">\n'
        f'        <h2>Otros impuestos municipales en {name}</h2>\n'
        f'        <p>Tipos y tarifas vigentes en {name} ({ejercicio}):</p>\n'
        + "\n".join(bloques)
        + f'\n        <p style="font-size:.82rem;color:var(--mid)">Fuente: '
        f'<a href="{HACIENDA_URL}" target="_blank" rel="nofollow noopener">Ministerio '
        f'de Hacienda</a> ({ejercicio}).</p>\n      </section>\n'
    )


OTROS_IMPUESTOS_EXISTING_RE = re.compile(
    r'\s*<section class="sec" id="otros-impuestos">.*?</section>', re.S
)
OTROS_H2_RE = re.compile(r'<h2>Otros municipios de ([^<]+)</h2>')
CCAA_LABEL_RE = re.compile(r'<h2>Comparativa IBI urbano en ([^<]+)</h2>')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    rows = [r for r in rows if r.get("oficial_tipo_urbana")]
    by_prov: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_ccaa: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_prov[(r["ccaa"], r["provincia_slug"])].append(r)
        by_ccaa[r["ccaa"]].append(r)

    labels: dict[str, str] = {}
    for r in rows:
        if r["ccaa"] in labels:
            continue
        m = CCAA_LABEL_RE.search(page_path(r).read_text(encoding="utf-8"))
        if m:
            labels[r["ccaa"]] = m.group(1)

    impuestos = load_impuestos()
    stats: Counter[str] = Counter()
    changed = 0
    for r in rows:
        label = labels.get(r["ccaa"], r["ccaa"].replace("-", " ").title())
        imp = impuestos.get(r.get("oficial_codigo_ine") or "", {})
        original, text = polish(
            r, by_prov[(r["ccaa"], r["provincia_slug"])], by_ccaa[r["ccaa"]],
            label, stats, imp, impuestos,
        )
        if text != original:
            changed += 1
            if not args.dry_run:
                page_path(r).write_text(text, encoding="utf-8")

    print(f"Fichas procesadas: {len(rows)}  modificadas: {changed}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
