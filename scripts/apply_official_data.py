#!/usr/bin/env python3
"""Aplica a las fichas municipales los tipos oficiales del Ministerio de Hacienda.

Sustituye el tipo publicado (que en 133 de 134 municipios no coincidia con el
oficial) por el dato del Ministerio, recalcula todas las cifras derivadas (cuotas
de ejemplo, resumen fiscal, grafico comparativo, respuestas del FAQ y metadatos),
retira las citas de boletin no comprobables y los enlaces a sedes electronicas
inexistentes, y anade un bloque con la evolucion del tipo y la fuente citable.

Uso:
    python3 scripts/apply_official_data.py --top 20          # las de mas trafico
    python3 scripts/apply_official_data.py --municipio galicia/ourense/ourense
    python3 scripts/apply_official_data.py --top 20 --dry-run
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
TODAY = date.today().isoformat()
MESES = ("enero","febrero","marzo","abril","mayo","junio","julio","agosto",
         "septiembre","octubre","noviembre","diciembre")
HOY_ES = f"{date.today().day} de {MESES[date.today().month - 1]} de {date.today().year}"
FUENTE_NOMBRE = "Ministerio de Hacienda · Consulta de información impositiva municipal"

# Fichas ordenadas por clics en Search Console (últimos 3 meses).
TOP_TRAFICO = [
    ("galicia/ourense/ourense", 109),
    ("castilla-la-mancha/toledo/talavera-de-la-reina", 86),
    ("murcia/murcia/molina-de-segura", 80),
    ("galicia/a-coruna/ferrol", 60),
    ("castilla-la-mancha/guadalajara/azuqueca-de-henares", 58),
    ("aragon/huesca/jaca", 57),
    ("extremadura/caceres/plasencia", 52),
    ("galicia/pontevedra/vilagarcia-de-arousa", 49),
    ("castilla-la-mancha/toledo/sesena", 48),
    ("castilla-y-leon/segovia/segovia", 47),
    ("galicia/lugo/lugo", 47),
    ("asturias/asturias/gijon", 45),
    ("asturias/asturias/oviedo", 41),
    ("castilla-la-mancha/cuenca/cuenca", 39),
    ("murcia/murcia/aguilas", 39),
    ("castilla-la-mancha/ciudad-real/alcazar-de-san-juan", 39),
    ("castilla-y-leon/palencia/palencia", 38),
    ("castilla-y-leon/avila/avila", 37),
    ("asturias/asturias/siero", 37),
    ("asturias/asturias/aviles", 35),
]


def pct(valor: float) -> str:
    texto = f"{valor:.4f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + "%"


def euros(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".") + " €"


def cuota(vc: float, tipo: float) -> float:
    return vc * tipo / 100


def num(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", ".")) if "," in texto else float(texto.replace(".", ""))


def registro_por_nombre(municipios: list[dict]) -> dict[str, dict]:
    return {m["nombre"]: m for m in municipios}


def bloque_oficial(m: dict, prefix: str) -> str:
    """Bloque nuevo: tipo oficial, evolucion y fuente citable."""
    ejercicio = m.get("oficial_ejercicio", "2025")
    anterior = m.get("oficial_tipo_urbana_anterior")
    ejer_ant = m.get("oficial_ejercicio_anterior", str(int(ejercicio) - 1))
    actual = m["oficial_tipo_urbana"]
    nombre = html.escape(m["nombre"])

    filas = [
        f"<tr><td>Tipo de IBI urbano ({ejercicio})</td><td class=\"v\">{pct(actual)}</td>"
        f"<td>{euros(cuota(50000, actual))}/año con un valor catastral de {euros(50000)}</td></tr>"
    ]
    if anterior:
        diferencia = actual - anterior
        if abs(diferencia) < 1e-9:
            evolucion = "sin cambios respecto al ejercicio anterior"
        else:
            signo = "subida" if diferencia > 0 else "bajada"
            evolucion = (
                f"{signo} de {abs(diferencia):.4f}".rstrip("0").rstrip(".").replace(".", ",")
                + f" puntos ({euros(abs(cuota(50000, actual) - cuota(50000, anterior)))} al año"
                + " más)" if diferencia > 0 else " menos)"
            )
        filas.append(
            f"<tr><td>Tipo de IBI urbano ({ejer_ant})</td><td>{pct(anterior)}</td>"
            f"<td>{evolucion}</td></tr>"
        )
    rustica = m.get("oficial_tipo_rustica")
    if rustica:
        if 0.3 <= rustica <= 0.9:
            detalle = "Fincas de naturaleza rústica"
        else:
            detalle = (
                "Valor publicado por el Ministerio, por encima del rango general del "
                "0,30%–0,90% que fija el art. 72.1 TRLRHL: puede responder a un recargo "
                "o a un supuesto específico, confírmalo en la ordenanza"
            )
        filas.append(
            f"<tr><td>Tipo de IBI rústico ({ejercicio})</td><td>{pct(rustica)}</td>"
            f"<td>{detalle}</td></tr>"
        )
    if m.get("oficial_ano_valores_catastrales"):
        filas.append(
            "<tr><td>Valores catastrales en vigor desde</td>"
            f"<td>{m['oficial_ano_valores_catastrales']}</td>"
            "<td>Año de la última valoración colectiva de urbana</td></tr>"
        )

    return f"""      <section class="sec">
        <h2>Tipo oficial del IBI en {nombre} y su evolución</h2>
        <table class="dt">
          <thead><tr><th>Concepto</th><th>Valor</th><th>Detalle</th></tr></thead>
          <tbody>
            {chr(10).join('            ' + f for f in filas).strip()}
          </tbody>
        </table>
        <div class="note"><strong>📌 Ejercicio {int(ejercicio) + 1}:</strong> el último dato oficial es el de {ejercicio}; si el pleno de {nombre} lo ha cambiado, estará en su ordenanza. <a href="{m['oficial_fuente_url']}" target="_blank" rel="nofollow noopener">Fuente</a>.</div>
      </section>
"""


def limites_grafico(texto: str) -> tuple[int, int] | None:
    """Localiza el grafico comparativo contando etiquetas <div> hasta cerrarlo.

    Hace falta un recorrido equilibrado porque cada barra contiene divs anidados y
    una expresion regular perezosa corta el bloque en la primera barra.
    """
    inicio = texto.find('<div class="chart-container">')
    if inicio == -1:
        return None
    profundidad = 0
    for etiqueta in re.finditer(r"<div\b|</div>", texto[inicio:]):
        profundidad += 1 if etiqueta.group(0).startswith("<div") else -1
        if profundidad == 0:
            return inicio, inicio + etiqueta.end()
    return None


def recaudadores() -> dict[str, dict]:
    path = ROOT / "data" / "recaudadores.json"
    return json.loads(path.read_text(encoding="utf-8"))["provincias"] if path.exists() else {}


def bloque_calendario(m: dict, recaudador: dict | None) -> str:
    """Quien recauda, donde esta el calendario y que cuesta pagar tarde.

    Responde a la intencion «cuándo se paga el IBI en X» sin inventar fechas: se
    enlaza el organismo que publica el calendario oficial.
    """
    nombre = html.escape(m["nombre"])
    web = m.get("web_oficial")
    web_nombre = html.escape(m.get("web_oficial_nombre") or f"Ayuntamiento de {m['nombre']}")

    if recaudador and recaudador.get("url"):
        quien = (
            f"En la provincia de {html.escape(m.get('provincia') or '')}, la gestión y el cobro de "
            f"los tributos municipales de buena parte de los ayuntamientos los presta "
            f'<a href="{recaudador["url"]}" target="_blank" rel="nofollow noopener">'
            f"{html.escape(recaudador['nombre'])}</a>, que es donde se publica el calendario "
            "de cobro. Los municipios más grandes suelen gestionarlo por su cuenta."
        )
    else:
        quien = (
            f"En {nombre} la gestión y el cobro del IBI los realiza directamente el propio "
            "ayuntamiento, que publica su calendario de cobro cada ejercicio."
        )

    donde = (
        f'Consulta las fechas exactas en <a href="{web}" target="_blank" rel="nofollow noopener">'
        f"{web_nombre}</a>."
        if web
        else "Consulta las fechas exactas en la web de tu ayuntamiento."
    )

    periodo = m.get("periodo", "")
    orientativo = (
        f"<p>El período que veníamos publicando para {nombre} es <strong>{html.escape(periodo)}</strong>, "
        "pero es un dato orientativo tomado de la ordenanza: <strong>no lo hemos podido contrastar</strong> "
        "y cada ejercicio puede cambiar. Antes de organizar el pago, confírmalo en la fuente oficial.</p>"
        if periodo
        else ""
    )

    # La explicacion de los recargos y de la domiciliacion es identica para cualquier
    # municipio: vive una sola vez en /ibi-2026/#recargos y aqui solo se enlaza. Asi el
    # bloque no se convierte en 134 copias del mismo texto.
    return f"""      <section class="sec">
        <h2>Cuándo se paga el IBI en {nombre} y quién lo cobra</h2>
        <p>{quien} {donde}</p>
        {orientativo}
        <p><a href="{prefix_de(m)}ibi-2026/#recargos" style="color:var(--accent);font-weight:600">Qué recargo se aplica si pagas fuera de plazo →</a></p>
      </section>
"""


def prefix_de(m: dict) -> str:
    return "../" * 3


def bloque_estado_datos(m: dict) -> str:
    """Que dato es oficial y que dato es orientativo, dicho sin rodeos."""
    web = m.get("web_oficial")
    enlace = (
        f'<a href="{web}" target="_blank" rel="nofollow noopener">'
        f"{html.escape(m.get('web_oficial_nombre') or 'la web del ayuntamiento')}</a>"
        if web
        else "la web de tu ayuntamiento"
    )
    # Version compacta: dos frases en lugar de una tabla repetida en 134 fichas.
    return f"""        <p style="font-size:.9rem"><strong>Contrastado</strong> con el Ministerio de Hacienda
        el {m.get('oficial_comprobado_el', TODAY)}: tipos de IBI y valores catastrales.
        <strong>Sin contrastar</strong> (orientativo): basuras y período de pago. Referencia: {enlace}.</p>
"""


def actualiza_grafico(texto: str, oficiales: dict[str, float]) -> tuple[str, int]:
    """Recalcula el grafico comparativo con los tipos oficiales."""
    limites = limites_grafico(texto)
    if not limites:
        return texto, 0
    ini, fin = limites
    bloque = re.match(r'(?s)<div class="chart-container">(.*)</div>$', texto[ini:fin])
    if not bloque:
        return texto, 0
    filas = re.findall(
        r'<div class="chart-bar-row">\s*<span class="chart-label"([^>]*)>([^<]+)</span>.*?'
        r'<div class="chart-bar" style="width:[\d.]+%;([^"]*)"><span>([\d.,]+)%</span>',
        bloque.group(1),
        re.S,
    )
    if not filas:
        return texto, 0
    datos = []
    for attrs, nombre, estilo, _ in filas:
        valor = oficiales.get(nombre.strip())
        if valor is None:
            return texto, 0
        datos.append((attrs, nombre.strip(), estilo, valor))
    datos.sort(key=lambda x: x[3])
    tope = max(d[3] for d in datos)
    nuevas = []
    for attrs, nombre, estilo, valor in datos:
        ancho = 55 + 45 * valor / tope
        nuevas.append(
            '  <div class="chart-bar-row">\n'
            f'    <span class="chart-label"{attrs}>{html.escape(nombre)}</span>\n'
            '    <div class="chart-bar-wrap">\n'
            f'      <div class="chart-bar" style="width:{ancho:.0f}%;{estilo}"><span>{pct(valor)}</span></div>\n'
            "    </div>\n  </div>"
        )
    nuevo = '<div class="chart-container">\n' + "\n".join(nuevas) + "\n</div>"
    return texto[:ini] + nuevo + texto[fin:], len(datos)


def procesa(clave: str, municipios: list[dict], por_nombre: dict[str, dict], dry: bool) -> dict:
    ruta = ROOT / clave / "index.html"
    m = next((x for x in municipios if f"{x['ccaa']}/{x['provincia_slug']}/{x['slug']}" == clave), None)
    resultado = {"clave": clave, "cambios": [], "aviso": ""}
    if not m or not ruta.exists():
        resultado["aviso"] = "ficha o registro no encontrado"
        return resultado
    if not m.get("oficial_tipo_urbana"):
        resultado["aviso"] = "sin dato oficial"
        return resultado

    texto = ruta.read_text(encoding="utf-8")
    nuevo_tipo = m["oficial_tipo_urbana"]
    # El tipo rustico solo se publica si cae dentro del rango general del art. 72.1
    # TRLRHL (0,30%-0,90%). Fuera de ese rango el dato del Ministerio puede
    # responder a un recargo o a un supuesto especifico, y se advierte en lugar de
    # presentarlo como el tipo aplicable.
    rustica = m.get("oficial_tipo_rustica")
    nuevo_rust = rustica if rustica and 0.3 <= rustica <= 0.9 else None
    rustica_atipica = rustica if rustica and not nuevo_rust else None
    antiguo = m.get("tipo_urbano")
    nombre = m["nombre"]
    prefix = "../" * len(clave.split("/"))
    web = m.get("web_oficial") or ""
    web_nombre = m.get("web_oficial_nombre") or f"Ayuntamiento de {nombre}"

    def cambio(etiqueta: str, n: int) -> None:
        if n:
            resultado["cambios"].append(f"{etiqueta}×{n}")

    # 1. Lista «Datos clave»
    texto, n = re.subn(
        r'(<li><strong>IBI urbano:</strong> <span class="v">)[\d.,]+%(</span>)',
        lambda mo: mo.group(1) + pct(nuevo_tipo) + mo.group(2),
        texto,
    )
    cambio("datos-clave-urbano", n)
    if nuevo_rust:
        texto, n = re.subn(
            r'(<li><strong>IBI rústico:</strong> <span class="v">)[\d.,]+%(</span>)',
            lambda mo: mo.group(1) + pct(nuevo_rust) + mo.group(2),
            texto,
        )
        cambio("datos-clave-rustico", n)
    elif rustica_atipica:
        texto, n = re.subn(
            r'<li><strong>IBI rústico:</strong> <span class="v">[\d.,]+%</span></li>',
            '<li><strong>IBI rústico:</strong> <span class="v">consultar ordenanza</span></li>',
            texto,
        )
        cambio("rustico-atipico", n)

    # 2. Frase de apertura con la cita de boletín no comprobable
    texto, n = re.subn(
        r"<p>El tipo del IBI urbano en [^<]*? es del <strong>[\d.,]+%</strong>,[^<]*?"
        r'<a href="https?://[^"]*"[^>]*>[^<]*</a>\.',
        f"<p>El tipo del IBI urbano en {html.escape(nombre)} es del "
        f"<strong>{pct(nuevo_tipo)}</strong>, según los datos del ejercicio "
        f"{m.get('oficial_ejercicio', '2025')} que publica el "
        f'<a href="{m["oficial_fuente_url"]}" target="_blank" rel="nofollow noopener">'
        f"Ministerio de Hacienda</a>.",
        texto,
    )
    cambio("frase-apertura", n)

    # 3. Nota de la fórmula
    texto, n = re.subn(
        r"(<em>Cuota íntegra = Valor catastral × )[\d.,]+%(</em>)",
        lambda mo: mo.group(1) + pct(nuevo_tipo) + mo.group(2),
        texto,
    )
    cambio("formula", n)

    # 4. Tabla de cuotas de ejemplo: se recalcula con el tipo oficial
    def recalcula_fila(mo: re.Match) -> str:
        vc = num(mo.group(2))
        anual = cuota(vc, nuevo_tipo)
        return (
            f"{mo.group(1)}{mo.group(2)} €</td><td class=\"v\">{anual:,.0f} €</td>".replace(",", ".")
            + f"<td>{anual / 12:,.0f} €/mes</td>".replace(",", ".")
        )

    texto, n = re.subn(
        r'(<tr><td>[^<]*</td><td>)([\d.]+) €</td><td class="v">[\d.]+ €</td><td>[\d.]+ €/mes</td>',
        recalcula_fila,
        texto,
    )
    cambio("cuotas-ejemplo", n)

    # 5. Resumen fiscal de la barra lateral
    def recalcula_resumen(mo: re.Match) -> str:
        vc = num(mo.group(2))
        return f"{mo.group(1)}{mo.group(2)} €)</td><td style=\"text-align:right;font-weight:700;color:var(--accent)\">{cuota(vc, nuevo_tipo):,.0f} €</td>".replace(",", ".")

    texto, n = re.subn(
        r'(<tr><td>IBI \(VC )([\d.]+) €\)</td><td style="text-align:right;font-weight:700;color:var\(--accent\)">[\d.]+ €</td>',
        recalcula_resumen,
        texto,
    )
    cambio("resumen-lateral", n)

    basuras = m.get("basuras_eur") or 0
    total = cuota(42000, nuevo_tipo) + basuras
    texto, n = re.subn(
        r'(<td><strong>Total estimado</strong></td><td style="text-align:right;font-weight:900;color:var\(--ink\)">)[\d.]+ €/año',
        lambda mo: mo.group(1) + f"{total:,.0f} €/año".replace(",", "."),
        texto,
    )
    cambio("total-lateral", n)

    # 6. Gráfico comparativo con los tipos oficiales de toda la provincia
    oficiales = {
        r["nombre"]: r["oficial_tipo_urbana"]
        for r in municipios
        if r.get("oficial_tipo_urbana")
    }
    texto, n = actualiza_grafico(texto, oficiales)
    cambio("grafico", 1 if n else 0)

    # 7. Metadatos
    texto, n = re.subn(r"IBI urbano [\d.,]+%", f"IBI urbano {pct(nuevo_tipo)}", texto)
    cambio("meta-descripcion", n)
    texto, n = re.subn(r"(<meta property=\"og:description\" content=\"IBI )[\d.,]+%", lambda mo: mo.group(1) + pct(nuevo_tipo), texto)
    cambio("og-description", n)

    # 8. FAQ estructurado
    texto, n = re.subn(
        r"(El tipo del IBI urbano en [^\"]*? es del )[\d.,]+%",
        lambda mo: mo.group(1) + pct(nuevo_tipo),
        texto,
    )
    cambio("faq-tipo", n)
    texto, n = re.subn(
        r"(con un valor catastral de 50\.000 € la cuota anual sería de )[\d.]+ €",
        lambda mo: mo.group(1) + f"{cuota(50000, nuevo_tipo):,.0f} €".replace(",", "."),
        texto,
    )
    cambio("faq-cuota", n)
    texto, n = re.subn(
        r'("dateModified":\s*")[\d-]+(")',
        lambda mo: mo.group(1) + TODAY + mo.group(2),
        texto,
    )
    cambio("date-modified", n)

    # 8b. Cualquier otra mención del tipo antiguo en el texto visible, excepto en el
    #     gráfico comparativo (que se recalcula aparte con los datos de todos los
    #     municipios de la provincia).
    if antiguo:
        variantes = {f"{antiguo:.4f}".rstrip("0").rstrip(".")}
        variantes.add(f"{antiguo:.2f}")
        patrones = [v.replace(".", r"[.,]") + "%" for v in variantes]
        limites = limites_grafico(texto)
        tramos = (
            [texto[: limites[0]], texto[limites[0]: limites[1]], texto[limites[1]:]]
            if limites
            else [texto]
        )
        total = 0
        for i, tramo in enumerate(tramos):
            if tramo.startswith('<div class="chart-container">'):
                continue  # el gráfico ya se ha recalculado con los datos de todos
            for patron in patrones:
                tramo, k = re.subn(patron, pct(nuevo_tipo), tramo)
                total += k
            tramos[i] = tramo
        texto = "".join(tramos)
        cambio("otras-menciones", total)

    # 9. Autoría: la cita de boletín se sustituye por la fuente oficial
    texto, n = re.subn(
        r'(<div class="author-box">.*?· Fuente: )<a href="https?://[^"]*"[^>]*>[^<]*</a>',
        lambda mo: mo.group(1)
        + f'<a href="{m["oficial_fuente_url"]}" target="_blank" rel="nofollow noopener">'
        + f"Ministerio de Hacienda, ejercicio {m.get('oficial_ejercicio', '2025')}</a>",
        texto,
        flags=re.S,
    )
    cambio("autoria-fuente", n)

    # 10. Sección de fuentes: ordenanza -> Ministerio; sede falsa -> web oficial
    texto, n = re.subn(
        r"<li><strong>Ordenanza fiscal:</strong>\s*<a href=\"https?://[^\"]*\"[^>]*>[^<]*</a></li>",
        f'<li><strong>Tipos oficiales:</strong> <a href="{m["oficial_fuente_url"]}" '
        f'target="_blank" rel="nofollow noopener">{FUENTE_NOMBRE}</a>, ejercicio '
        f"{m.get('oficial_ejercicio', '2025')} (consultado el {HOY_ES}).</li>",
        texto,
    )
    cambio("fuente-ordenanza", n)

    if web:
        texto, n = re.subn(
            r"<li><strong>Sede electrónica(?: del Ayuntamiento)?:</strong>\s*<a href=\"[^\"]*\"[^>]*>[^<]*</a></li>",
            f'<li><strong>Web oficial:</strong> <a href="{web}" target="_blank" '
            f'rel="nofollow noopener">{html.escape(web_nombre)}</a>, donde se publica la '
            "ordenanza fiscal y el calendario de cobro.</li>",
            texto,
        )
        cambio("fuente-web", n)
        texto, n = re.subn(r'https://[a-z0-9\-]+\.sedelectronica\.es[^"]*', web, texto)
        cambio("sede-falsa", n)
        # El enlace ya no es una sede electronica sino la web oficial: se ajusta el
        # texto del enlace para no afirmar algo que no es.
        if "sede." not in web and "sedelectronica" not in web and "sedipualba" not in web:
            texto, n = re.subn(
                r"sede electrónica de " + re.escape(nombre),
                f"web oficial de {nombre}",
                texto,
            )
            cambio("texto-enlace", n)
    else:
        # Sin web municipal verificada: el enlace falso se sustituye por el organismo
        # provincial de recaudacion, que si esta comprobado. Nunca se deja un enlace
        # a una direccion que no pertenece al ayuntamiento.
        rec = recaudadores().get(m["provincia_slug"]) or {}
        if rec.get("url"):
            texto, n = re.subn(r'https://[a-z0-9\-]+\.sedelectronica\.es[^"]*', rec["url"], texto)
            cambio("sede-falsa", n)
            texto, n = re.subn(
                r"sede electrónica de " + re.escape(nombre), html.escape(rec["nombre"]), texto
            )
            texto, n2 = re.subn(r">sede electrónica<", f">{html.escape(rec['nombre'])}<", texto)
            cambio("texto-enlace", n + n2)
            texto, n = re.subn(
                r"<li><strong>Sede electrónica(?: del Ayuntamiento)?:</strong>\s*<a href=\"[^\"]*\"[^>]*>[^<]*</a></li>",
                f'<li><strong>Organismo de recaudación:</strong> <a href="{rec["url"]}" '
                f'target="_blank" rel="nofollow noopener">{html.escape(rec["nombre"])}</a>, '
                "donde se publica el calendario de cobro de los municipios de la provincia.</li>",
                texto,
            )
            cambio("fuente-organismo", n)
        else:
            # Ni web municipal ni organismo provincial: se retira el enlace y se deja
            # el texto, para no enlazar a ningun sitio que no sea el correcto.
            texto, n = re.subn(
                r'<a href="https://[a-z0-9\-]+\.sedelectronica\.es[^"]*"[^>]*>([^<]*)</a>',
                lambda mo: mo.group(1),
                texto,
            )
            cambio("enlace-retirado", n)
            texto, n = re.subn(
                r"<li><strong>Sede electrónica(?: del Ayuntamiento)?:</strong>[^<]*</li>",
                "<li><strong>Sede electrónica municipal:</strong> búscala en la web oficial de tu "
                "ayuntamiento; es donde se publican la ordenanza fiscal y el calendario de cobro.</li>",
                texto,
            )
            cambio("fuente-generica", n)

    # 10b. Lista «Otros municipios»: sus tipos tambien deben ser los oficiales, o la
    #      ficha volveria a contradecir a las demas paginas del sitio.
    def actualiza_cita(mo: re.Match) -> str:
        valor = oficiales.get(mo.group(2).strip())
        return mo.group(0) if valor is None else f"{mo.group(1)}{mo.group(2)}{mo.group(3)}{pct(valor)}"

    texto, n = re.subn(
        r'(<li><a href="[^"]+">)([^<]+)(</a> — IBI )[\d.,]+%',
        actualiza_cita,
        texto,
    )
    cambio("citas-otros-municipios", n)

    # 11. Aviso final
    texto, n = re.subn(
        r'<div class="note"><strong>⚠️ Verifica antes de pagar:</strong>[^<]*'
        r'(<a[^>]*>[^<]*</a>)?[^<]*\.?</div>',
        f'<div class="note"><strong>⚠️ Verifica antes de pagar:</strong> el tipo '
        f"{pct(nuevo_tipo)} corresponde al ejercicio {m.get('oficial_ejercicio', '2025')} "
        f"según el Ministerio de Hacienda. Los importes de basuras y las bonificaciones "
        f"proceden de la ordenanza municipal y pueden haberse modificado: confírmalos en "
        + (f'<a href="{web}" target="_blank" rel="nofollow noopener">{html.escape(web_nombre)}</a>.' if web else "la web de tu ayuntamiento.")
        + "</div>",
        texto,
    )
    cambio("aviso-final", n)

    # 11b. Tasa de basuras y bonificaciones: son los datos que NO podemos contrastar.
    #      Se marcan como orientativos y las bonificaciones pasan a expresar el límite
    #      legal, en lugar de afirmar un porcentaje municipal sin fuente.
    texto, n = re.subn(
        r'(<li><strong>Basura vivienda:</strong> [\d.,]+ €/año)(</li>)',
        lambda mo: mo.group(1) + ' <span style="color:var(--mid);font-size:.85em">(orientativo)</span>' + mo.group(2),
        texto,
    )
    cambio("basuras-orientativo", n)
    texto, n = re.subn(
        r'(<li><strong>Período de pago:</strong> [^<]+)(</li>)',
        lambda mo: mo.group(1) + ' <span style="color:var(--mid);font-size:.85em">(orientativo)</span>' + mo.group(2),
        texto,
    )
    cambio("periodo-orientativo", n)

    for etiqueta, limite, articulo in (
        ("Bonif. familia numerosa", "Hasta 90%", "art. 74.4 TRLRHL"),
        ("Bonif. energía solar", "Hasta 50%", "art. 74.5 TRLRHL"),
    ):
        texto, n = re.subn(
            r"(<li><strong>" + re.escape(etiqueta) + r":</strong> )[^<]+(</li>)",
            lambda mo, lim=limite, art=articulo: mo.group(1)
            + f'{lim} <span style="color:var(--mid);font-size:.85em">(límite legal, {art})</span>'
            + mo.group(2),
            texto,
        )
        cambio("boni-limite", n)

    texto, n = re.subn(
        r'(<tr><td>Familia numerosa[^<]*</td><td class="v">)[^<]+(</td>)',
        lambda mo: mo.group(1) + "Hasta 90%" + mo.group(2),
        texto,
    )
    texto, n2 = re.subn(
        r'(<tr><td>Energía solar / renovables</td><td class="v">)[^<]+(</td>)',
        lambda mo: mo.group(1) + "Hasta 50%" + mo.group(2),
        texto,
    )
    cambio("tabla-bonificaciones", n + n2)
    if (n or n2) and "el porcentaje concreto lo fija la ordenanza" not in texto:
        texto = texto.replace(
            '<div class="note"><strong>📅 Solicitud:</strong>',
            '<p style="font-size:.85rem;color:var(--mid)">Los porcentajes indicados son el '
            "<strong>máximo que permite la ley</strong> (arts. 73 y 74 del texto refundido de la "
            "Ley Reguladora de las Haciendas Locales): el porcentaje concreto lo fija la ordenanza "
            "fiscal de cada ayuntamiento y hay que solicitarlo, nunca se aplica de oficio.</p>\n"
            '        <div class="note"><strong>📅 Solicitud:</strong>',
            1,
        )
        resultado["cambios"].append("nota-limite-legal")

    texto, n = re.subn(
        r"(<h2>Tasa de basuras en [^<]*</h2>\s*<p>)",
        lambda mo: mo.group(1)
        + '<span style="color:var(--mid)">[Importe orientativo: no existe una fuente estatal '
        "que publique las tasas de residuos, así que este dato procede de la ordenanza municipal "
        "y no lo hemos podido contrastar.]</span> ",
        texto,
    )
    cambio("aviso-basuras", n)

    # 11c. Migracion: las primeras versiones de estos bloques eran demasiado largas y,
    #      multiplicadas por 134 fichas, volvian a generar texto duplicado. Se eliminan
    #      para reinsertar la version compacta.
    for marca in ("<h2>Cuándo se paga el IBI en", "<h2>Tipo oficial del IBI en"):
        while True:
            pos = texto.find(marca)
            if pos == -1:
                break
            ini = texto.rfind("<section", 0, pos)
            fin = texto.find("</section>", pos)
            if ini == -1 or fin == -1:
                break
            texto = texto[:ini] + texto[fin + len("</section>"):]
            resultado["cambios"].append("bloque-compactado")
    texto = re.sub(
        r'\s*<p style="font-size:.82rem;color:var\(--mid\)">Fuente: <a href="https://serviciostelematicos'
        r'[^<]*</a>[^<]*</p>',
        "",
        texto,
    )
    texto = re.sub(
        r"\s*<h3>Estado de los datos de esta ficha</h3>\s*(?:<table class=\"dt\">.*?</table>\s*"
        r"<p[^>]*>.*?</p>|<p[^>]*>.*?</p>)",
        "",
        texto,
        flags=re.S,
    )

    # Notas genericas: se acortan y se remiten a la guia canonica
    texto, n = re.subn(
        r'<p style="font-size:.85rem;color:var\(--mid\)">Los porcentajes indicados son el '
        r"<strong>máximo que permite la ley</strong>.*?</p>",
        f'<p style="font-size:.85rem;color:var(--mid)">Son los <strong>máximos legales</strong> '
        f'(arts. 73 y 74 TRLRHL); el porcentaje concreto lo fija la ordenanza y hay que solicitarlo. '
        f'<a href="{prefix}bonificaciones/">Requisitos y plazos →</a></p>',
        texto,
        flags=re.S,
    )
    cambio("nota-limite-compacta", n)
    texto, n = re.subn(
        r'<span style="color:var\(--mid\)">\[Importe orientativo: no existe una fuente estatal.*?\]</span>',
        '<span style="color:var(--mid)">[Importe orientativo, sin contrastar.]</span>',
        texto,
        flags=re.S,
    )
    cambio("aviso-basuras-compacto", n)

    # 12. Bloques nuevos: calendario de cobro y tipo oficial, antes de las fuentes
    # la indentación de la plantilla varía entre variantes, así que el ancla es laxa
    patron_fuentes = re.compile(r'[ \t]*<section class="sec">\s*<h2>Fuentes oficiales')
    ancla = patron_fuentes.search(texto)
    if ancla and "<h2>Cuándo se paga el IBI en" not in texto:
        recaudador = recaudadores().get(m["provincia_slug"])
        texto = texto[: ancla.start()] + bloque_calendario(m, recaudador) + texto[ancla.start():]
        resultado["cambios"].append("bloque-calendario")
        ancla = patron_fuentes.search(texto)
    if ancla and "Tipo oficial del IBI en" not in texto:
        texto = texto[: ancla.start()] + bloque_oficial(m, prefix) + texto[ancla.start():]
        resultado["cambios"].append("bloque-oficial")

    # 12b. Estado de los datos dentro de la sección de fuentes
    if "Estado de los datos de esta ficha" not in texto:
        texto, n = re.subn(
            r"(<h2>Fuentes oficiales y verificación</h2>)",
            lambda mo: mo.group(1)
            + "\n        <h3>Estado de los datos de esta ficha</h3>\n"
            + bloque_estado_datos(m),
            texto,
        )
        cambio("estado-datos", n)

    # 13. Fecha de revisión visible (hay dos formatos en las plantillas antiguas:
    #     «Actualizado: 2026-05-10» y «Actualizado: abril 2026»)
    texto, n = re.subn(
        r"(· Actualizado: )(?:[\d-]{8,10}|[A-Za-záéíóúñ]+ \d{4})",
        lambda mo: mo.group(1) + HOY_ES,
        texto,
    )
    cambio("fecha-visible", n)

    if not dry:
        ruta.write_text(texto, encoding="utf-8")

    resultado["antiguo"] = antiguo
    resultado["nuevo"] = nuevo_tipo
    return resultado


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, help="número de fichas con más tráfico")
    ap.add_argument("--all", action="store_true", help="todas las fichas del sitio")
    ap.add_argument("--municipio", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    municipios = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    por_nombre = registro_por_nombre(municipios)

    objetivos = list(args.municipio)
    if args.top:
        objetivos += [clave for clave, _ in TOP_TRAFICO[: args.top]]
    if args.all:
        # primero las de más tráfico, después el resto
        orden = [c for c, _ in TOP_TRAFICO]
        todas = [f"{m['ccaa']}/{m['provincia_slug']}/{m['slug']}" for m in municipios]
        objetivos += orden + [c for c in todas if c not in orden]
    if not objetivos:
        ap.error("indica --top N, --all o --municipio <ruta>")

    clics = dict(TOP_TRAFICO)
    print(f"{'municipio':34} {'clics':>6} {'publicado':>10} {'oficial':>10}  cambios")
    total_cambios = 0
    for clave in objetivos:
        r = procesa(clave, municipios, por_nombre, args.dry_run)
        if r["aviso"]:
            print(f"{clave:34} [aviso] {r['aviso']}")
            continue
        total_cambios += len(r["cambios"])
        print(
            f"{clave.split('/')[-1]:34} {clics.get(clave, 0):6} "
            f"{pct(r['antiguo']) if r['antiguo'] else '—':>10} {pct(r['nuevo']):>10}  "
            + ", ".join(r["cambios"])
        )
    print(f"\nfichas procesadas: {len(objetivos)} · sustituciones aplicadas: {total_cambios}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
