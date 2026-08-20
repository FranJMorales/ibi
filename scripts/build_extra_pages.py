#!/usr/bin/env python3
"""Genera las paginas transversales del sitio a partir de los datos verificados.

  /municipios/    comparador nacional: los 134 municipios con su tipo oficial de IBI
                  y su poblacion oficial, en una tabla ordenable. Antes era una lista
                  de 169 enlaces sin datos, el patron de pagina puente.
  /metodologia/   de donde sale cada dato, que esta contrastado y que no, como se
                  verifica y como se corrige. Es la pagina que sostiene el E-E-A-T.
  /sobre-nosotros/ quien esta detras, sin inventar credenciales.
  /provincias/    se retira: 783 palabras, un solo h2 y 161 enlaces. Redirige a
                  /comunidades/.

Uso:  python3 scripts/build_extra_pages.py
"""

from __future__ import annotations

import html
import json
import statistics
from datetime import date
from pathlib import Path

import build_territory_pillars as tp

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"
TODAY = date.today().isoformat()
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")
HOY_ES = f"{date.today().day} de {MESES[date.today().month - 1]} de {date.today().year}"
REF_VC = 50000

CCAA = {
    "aragon": "Aragón", "asturias": "Asturias", "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha", "castilla-y-leon": "Castilla y León",
    "extremadura": "Extremadura", "galicia": "Galicia", "la-rioja": "La Rioja",
    "murcia": "Murcia",
}


def datos() -> list[dict]:
    return json.loads((ROOT / "data" / "municipios.json").read_text(encoding="utf-8"))["municipios"]


def impuestos() -> dict:
    """Resto de tributos que publica Hacienda por municipio (ICIO, IVTM, IIVTNU)."""
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


def plusvalia_tipo(imp: dict | None) -> float | None:
    """Tipo de gravamen mas alto del IIVTNU, solo si la serie es la vigente.

    Mismo criterio que las fichas y los pilares: los coeficientes del art. 107.4
    TRLRHL van de 0,09 a 0,40, asi que una serie muy por debajo es el porcentaje
    anual del sistema anterior al RDL 26/2021 y no la publicamos.
    """
    coefs = [valor(imp, f"C{n}") for n in range(51, 72)]
    validos = [c for c in coefs if c is not None]
    if not validos or not (0.10 <= max(validos) <= 0.45):
        return None
    tipos = [valor(imp, f"C{n}") for n in range(72, 93)]
    validos_t = [t for t in tipos if t is not None]
    return max(validos_t) if validos_t else None


def num(v: float, dec: int = 2) -> str:
    return f"{v:,.{dec}f}".replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def pct(v: float) -> str:
    """Sin ceros de relleno: 30% y no 30,0%, igual que en las fichas."""
    return f"{round(v, 4):g}".replace(".", ",") + "%"


def pct2(v: float) -> str:
    """Para medias y medianas, donde cuatro decimales solo hacen ruido."""
    return f"{v:.2f}".replace(".", ",") + "%"


def euros(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".") + " €"


def miles(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def escribe(rel: str, contenido: str) -> None:
    destino = ROOT / rel / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    palabras = len(tp.strip_tags(contenido.split("<footer>")[0]).split())
    print(f"  /{rel}/  escrita ({palabras} palabras)")


# ───────────────────────────── comparador nacional ─────────────────────────────

# El buscador de la portada tiene como respaldo sin JavaScript un formulario que
# apunta a /municipios/?q=…, y el SearchAction de la portada declara esa misma URL.
# Hasta ahora la tabla ignoraba el parametro: el visitante aterrizaba en las 134
# filas sin filtrar. Este filtro lo lee y ademas permite buscar dentro de la tabla.
FILTRO_SCRIPT = """<script>
(function () {
  var input = document.getElementById('tm-filtro');
  var tabla = document.querySelector('table.sortable');
  var estado = document.getElementById('tm-filtro-estado');
  if (!input || !tabla || !tabla.tBodies.length) return;
  var filas = Array.prototype.slice.call(tabla.tBodies[0].rows);
  var total = filas.length;
  function norm(s) {
    return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  }
  function aplica() {
    var q = norm(input.value.trim());
    var n = 0;
    filas.forEach(function (tr) {
      var texto = norm(tr.cells[0].textContent + ' ' + tr.cells[1].textContent
                       + ' ' + tr.cells[2].textContent);
      var visible = !q || texto.indexOf(q) !== -1;
      tr.hidden = !visible;
      if (visible) n++;
    });
    estado.textContent = q
      ? n + ' de ' + total + ' municipios coinciden con «' + input.value.trim() + '»'
      : total + ' municipios';
  }
  input.addEventListener('input', aplica);
  try {
    var q = new URLSearchParams(window.location.search).get('q');
    if (q) { input.value = q; aplica(); }
  } catch (e) { /* navegador sin URLSearchParams: el filtro sigue funcionando */ }
})();
</script>
"""


def comparador() -> str:
    municipios = [m for m in datos() if m.get("oficial_tipo_urbana")]
    municipios.sort(key=lambda m: -m["oficial_tipo_urbana"])
    tipos = [m["oficial_tipo_urbana"] for m in municipios]
    media = statistics.mean(tipos)
    mediana = statistics.median(tipos)
    caro, barato = municipios[0], municipios[-1]
    ejercicio = municipios[0].get("oficial_ejercicio", "2025")
    poblacion = sum(m.get("poblacion_oficial") or 0 for m in municipios)

    imps = impuestos()
    filas = []
    icios, ivtms, anos, plus = [], [], [], []
    for m in municipios:
        cuota = REF_VC * m["oficial_tipo_urbana"] / 100
        hab = m.get("poblacion_oficial")
        ficha = f"../{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"
        imp = imps.get(m.get("oficial_codigo_ine") or "")
        icio = valor(imp, "C17")
        ivtm = valor(imp, "C19")
        ptipo = plusvalia_tipo(imp)
        ano = m.get("oficial_ano_valores_catastrales")
        ano = int(ano) if str(ano or "").isdigit() else None
        rustica = m.get("oficial_tipo_rustica")
        if icio is not None:
            icios.append(icio)
        if ivtm is not None:
            ivtms.append(ivtm)
        if ano:
            anos.append(ano)
        if ptipo is not None:
            plus.append(ptipo)
        filas.append(
            "<tr>"
            f'<td data-sort="{html.escape(m["nombre"])}"><a href="{ficha}"><strong>{html.escape(m["nombre"])}</strong></a></td>'
            f'<td data-sort="{html.escape(m.get("provincia") or "")}">{html.escape(m.get("provincia") or "—")}</td>'
            f'<td data-sort="{html.escape(CCAA.get(m["ccaa"], m["ccaa"]))}">{html.escape(CCAA.get(m["ccaa"], m["ccaa"]))}</td>'
            f'<td data-sort="{hab or 0}">{miles(hab) if hab else "—"}</td>'
            f'<td data-sort="{m["oficial_tipo_urbana"]}" class="v">{pct(m["oficial_tipo_urbana"])}</td>'
            f'<td data-sort="{rustica or 0}">{pct(rustica) if rustica else "—"}</td>'
            f'<td data-sort="{cuota:.2f}">{euros(cuota)}</td>'
            f'<td data-sort="{ano or 0}">{ano or "—"}</td>'
            f'<td data-sort="{icio if icio is not None else 0}">{pct(icio) if icio is not None else "—"}</td>'
            f'<td data-sort="{ivtm if ivtm is not None else 0}">{num(ivtm) + " €" if ivtm is not None else "—"}</td>'
            f'<td data-sort="{ptipo if ptipo is not None else 0}">{pct(ptipo) if ptipo is not None else "—"}</td>'
            "</tr>"
        )
    ano_mediana = int(statistics.median(anos)) if anos else None
    ano_actual = date.today().year

    prefix = "../"
    title = f"IBI 2026: compara los tipos oficiales de {len(municipios)} municipios"
    description = (
        f"Compara {len(municipios)} municipios con datos oficiales del Ministerio de "
        f"Hacienda (ejercicio {ejercicio}, el último publicado): tipo de IBI del "
        f"{pct(barato['oficial_tipo_urbana'])} al {pct(caro['oficial_tipo_urbana'])}, "
        f"cuota estimada, año de los valores catastrales, ICIO, impuesto de circulación "
        f"y plusvalía. Tabla ordenable."
    )

    cuerpo = f"""<div class="bc"><a href="{prefix}">Inicio</a><span>›</span><strong>Municipios</strong></div>
<div class="wrap">
  <h1>IBI 2026 por municipios: comparativa con datos oficiales</h1>
  <p class="lead">Los tipos de gravamen del IBI de <strong>{len(municipios)} municipios</strong> ({miles(poblacion)} habitantes en total), tomados de la consulta de información impositiva municipal del <strong>Ministerio de Hacienda</strong>. Ordena la tabla por cualquier columna para comparar.</p>

  <div class="ed">
    <h2 class="sec" id="resumen">Qué dicen los datos</h2>
    <p>El tipo medio de estos {len(municipios)} municipios es del <strong>{pct2(media)}</strong> y la mediana del <strong>{pct2(mediana)}</strong>. El más alto es <strong>{caro['nombre']}</strong> con {pct(caro['oficial_tipo_urbana'])} y el más bajo <strong>{barato['nombre']}</strong> con {pct(barato['oficial_tipo_urbana'])}: sobre un valor catastral de {euros(REF_VC)}, la diferencia es de <strong>{euros(REF_VC * (caro['oficial_tipo_urbana'] - barato['oficial_tipo_urbana']) / 100)} al año</strong> por el mismo inmueble.</p>
    <p>La ley permite a los ayuntamientos moverse entre el <strong>0,40%</strong> y el <strong>1,10%</strong> en bienes urbanos (art. 72.1 del <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214" target="_blank" rel="nofollow noopener">TRLRHL</a>), así que casi todos estos municipios se sitúan en la mitad baja de la horquilla legal. Un tipo alto no implica un recibo alto: la cuota depende del valor catastral de cada inmueble, y ese valor cambia mucho según cuándo se hizo la última valoración colectiva del municipio.</p>
    <p><strong>Los tipos son los del ejercicio {ejercicio}</strong>, el último que publica Hacienda, y son los que se aplican a los recibos de 2026 salvo que el pleno los haya modificado después: en ese caso el cambio aparece antes en la ordenanza municipal que en la estadística estatal.</p>
    <p>La tabla no se queda en el IBI. También compara el <strong>año de la última valoración catastral</strong> (que decide la base sobre la que se aplica el tipo), el tipo del <strong>ICIO</strong> de las obras, la cuota del <strong>impuesto de circulación</strong> para el turismo más común y el <strong>tipo de gravamen de la plusvalía</strong> municipal:</p>
    <ul>
      <li><strong>Valores catastrales:</strong> la mediana está en {ano_mediana}, es decir {ano_actual - ano_mediana} años de antigüedad. <a href="{prefix}valor-catastral/">Qué es el valor catastral y cómo se corrige →</a> · <a href="{prefix}analisis/valores-catastrales-antiguos/">Por qué pesa más que el tipo →</a></li>
      <li><strong>ICIO:</strong> del {pct(min(icios))} al {pct(max(icios))}, con una mediana del {pct2(statistics.median(icios))}.</li>
      <li><strong>IVTM (turismo de 8 a 11,99 CV):</strong> de {num(min(ivtms))} € a {num(max(ivtms))} € al año. La cuota mínima legal es de 34,08 €, así que el más caro aplica el coeficiente máximo que permite la ley. <a href="{prefix}impuesto-circulacion/">Guía del impuesto de circulación →</a> · <a href="{prefix}analisis/impuesto-circulacion-ivtm/">Comparativa completa →</a></li>
      <li><strong>Plusvalía:</strong> el tipo máximo declarado va del {pct(min(plus))} al {pct(max(plus))} (el techo legal es el 30%). <a href="{prefix}analisis/coeficientes-plusvalia/">Quién aplica el coeficiente máximo →</a></li>
    </ul>
    <p><strong>Cómo usar esta tabla:</strong> la columna «cuota» aplica el tipo de cada municipio a un valor catastral común de {euros(REF_VC)} para que la comparación sea homogénea. Para calcular tu caso concreto, usa la <a href="{prefix}calculadora-ibi/">calculadora con tu valor catastral</a>.</p>
  </div>

  <h2 class="sec" id="tabla">Tabla comparativa: IBI, valores catastrales, ICIO, circulación y plusvalía</h2>
  <p>Escribe en el filtro para quedarte con los municipios que te interesan y pulsa en cualquier encabezado para ordenar. El nombre del municipio lleva a su ficha, con las bonificaciones, la plusvalía y los enlaces oficiales. <strong>Todas las columnas salen de la consulta del Ministerio de Hacienda</strong> para el ejercicio {ejercicio}: no hay ninguna columna estimada ni tomada de terceros. Aquí no verás la tasa de residuos porque no existe fuente estatal que la publique (<a href="{prefix}tasa-basuras/">por qué y dónde encontrar la tuya</a>).</p>
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:0 0 14px">
    <label for="tm-filtro" style="font-size:.85rem;font-weight:600">Filtrar la tabla:</label>
    <input type="search" id="tm-filtro" placeholder="Municipio, provincia o comunidad…"
           autocomplete="off" aria-describedby="tm-filtro-estado"
           style="flex:1 1 240px;max-width:340px;padding:9px 12px;border:1px solid var(--rule);border-radius:4px;font-family:inherit;font-size:.9rem;background:#fff;color:var(--ink)">
    <span id="tm-filtro-estado" role="status" aria-live="polite" style="font-size:.82rem;color:var(--mid)">{len(municipios)} municipios</span>
  </div>
  <div class="table-scroll">
    <table class="dt sortable">
      <thead>
        <tr>
          <th data-col="0">Municipio</th>
          <th data-col="1">Provincia</th>
          <th data-col="2">Comunidad</th>
          <th data-col="3">Habitantes</th>
          <th data-col="4">IBI urbano</th>
          <th data-col="5">IBI rústico</th>
          <th data-col="6">Cuota con VC de {euros(REF_VC)}</th>
          <th data-col="7">Valores catastrales</th>
          <th data-col="8">ICIO</th>
          <th data-col="9">IVTM 8–11,99 CV</th>
          <th data-col="10">Plusvalía: tipo máx.</th>
        </tr>
      </thead>
      <tbody>
            {chr(10).join('            ' + f for f in filas).strip()}
      </tbody>
    </table>
  </div>

  <section class="sec">
    <h2 id="fuentes">De dónde salen estos datos</h2>
    <p>El tipo de IBI, el año de los valores catastrales, el ICIO, la tarifa del IVTM y los tipos de la plusvalía proceden de la <strong>consulta de información impositiva municipal</strong> del Ministerio de Hacienda, que recoge lo aprobado en la ordenanza fiscal de cada ayuntamiento, y corresponden al ejercicio <strong>{ejercicio}</strong>, el último publicado. Las cifras de población son las <strong>oficiales del padrón municipal</strong> que publica el INE.</p>
    <p><strong>Aquí no hay ninguna columna sin fuente.</strong> Hasta julio de 2026 esta tabla incluía una columna de tasa de basuras marcada como orientativa: la hemos retirado porque no pudimos contrastarla contra ninguna fuente primaria y un dato sin respaldo no debería estar publicado, ni siquiera con aviso. Un guion en cualquier celda significa que la fuente no publica ese dato para ese municipio: preferimos el hueco al relleno. Todo enlazado y fechado en la <a href="{prefix}metodologia/">página de metodología</a>.</p>
    <p>Si tu ayuntamiento modificó el tipo para el ejercicio siguiente, el cambio aparece antes en su ordenanza fiscal que en la estadística estatal: en la ficha de cada municipio enlazamos su web oficial para que puedas comprobarlo.</p>
    <p style="font-size:.85rem;color:var(--mid)">Última actualización de esta tabla: {HOY_ES}.</p>
  </section>

  <h2 class="sec">Explora por comunidad autónoma</h2>
  <div class="ct-grid">
    {"".join(f'<a href="{prefix}{slug}/" class="ct">{nombre}</a>' for slug, nombre in sorted(CCAA.items(), key=lambda kv: kv[1]))}
  </div>
</div>
"""

    schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"Tributos municipales de {len(municipios)} municipios españoles ({ejercicio})",
        "variableMeasured": [
            "Tipo de gravamen del IBI urbano",
            "Año de entrada en vigor de los valores catastrales",
            "Tipo del ICIO",
            "Cuota del IVTM para turismos de 8 a 11,99 caballos fiscales",
            "Tipo de gravamen del IIVTNU",
            "Población oficial",
        ],
        "description": description,
        "url": f"{SITE}/municipios/",
        "creator": {"@type": "Organization", "name": "TasasMunicipales.info"},
        "isBasedOn": "https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/html/portadaconsultasm.aspx",
        "temporalCoverage": str(ejercicio),
        "dateModified": TODAY,
    }
    bloque = ('<script type="application/ld+json">\n'
              + json.dumps(schema, ensure_ascii=False, indent=1) + "\n</script>\n")
    return (tp.head_block(title, description, f"{SITE}/municipios/", prefix)
            + cuerpo + tp.SORT_SCRIPT + FILTRO_SCRIPT + bloque
            + tp.footer_block(prefix))


# ──────────────────────────────── metodología ────────────────────────────────

def metodologia() -> str:
    municipios = datos()
    con_tipo = sum(1 for m in municipios if m.get("oficial_tipo_urbana"))
    imps = impuestos()
    def imp_de(m: dict) -> dict | None:
        return imps.get(m.get("oficial_codigo_ine") or "")
    plus_ok = sum(1 for m in municipios if plusvalia_tipo(imp_de(m)) is not None)
    plus_sin = sum(1 for m in municipios
                   if all(valor(imp_de(m), f"C{n}") is None for n in range(51, 72)))
    plus_raro = len(municipios) - plus_ok - plus_sin
    icio_ok = sum(1 for m in municipios if valor(imp_de(m), "C17") is not None)
    ivtm_ok = sum(1 for m in municipios if valor(imp_de(m), "C19") is not None)
    serie_ok = sum(1 for m in municipios if len(m.get("poblacion_serie") or []) >= 2)
    con_poblacion = sum(1 for m in municipios if m.get("poblacion_oficial"))
    con_web = sum(1 for m in municipios if m.get("web_oficial"))
    web_ok = sum(1 for m in municipios if m.get("web_http_status") == 200)
    legales = json.loads((ROOT / "data" / "fuentes_legales.json").read_text(encoding="utf-8"))["fuentes"]
    recaudadores = json.loads((ROOT / "data" / "recaudadores.json").read_text(encoding="utf-8"))["provincias"]
    rec_ok = sum(1 for r in recaudadores.values() if r.get("http_status") == 200)
    rec_total = sum(1 for r in recaudadores.values() if r.get("url"))
    fuentes_lista = "\n      ".join(
        f'<li><a href="{f["url"]}" target="_blank" rel="nofollow noopener">{html.escape(f["titulo"])}</a></li>'
        for f in legales
    )

    prefix = "../"
    title = "Metodología: de dónde salen nuestros datos y cómo se verifican"
    description = (
        "Qué fuente oficial respalda cada dato del sitio, qué hemos podido contrastar y "
        "qué no publicamos por no tener fuente, cómo se comprueba y cómo pedir una "
        "corrección. Con el registro de errores ya corregidos."
    )

    cuerpo = f"""<div class="bc"><a href="{prefix}">Inicio</a><span>›</span><strong>Metodología</strong></div>
<div class="wrap">
  <h1>Metodología: de dónde salen los datos y cómo los verificamos</h1>
  <p class="lead">Publicamos información fiscal municipal, y en ese terreno una cifra sin fuente no vale nada. Esta página explica <strong>qué respalda cada dato</strong>, qué hemos podido contrastar y qué no, y cómo corregimos cuando nos equivocamos.</p>

  <section class="sec">
    <h2 id="fuentes-por-dato">Qué fuente respalda cada dato</h2>
    <table class="dt">
      <thead><tr><th>Dato</th><th>Fuente</th><th>Cobertura</th></tr></thead>
      <tbody>
        <tr><td>Tipo de gravamen del IBI urbano y rústico</td><td>Ministerio de Hacienda, consulta de información impositiva municipal</td><td><strong>{con_tipo} de {len(municipios)}</strong> municipios, con enlace y fecha de consulta</td></tr>
        <tr><td>Año de entrada en vigor de los valores catastrales</td><td>La misma consulta del Ministerio</td><td><strong>{con_tipo} de {len(municipios)}</strong></td></tr>
        <tr><td>Población</td><td>INE, cifras oficiales del padrón municipal</td><td><strong>{con_poblacion} de {len(municipios)}</strong></td></tr>
        <tr><td>Coeficientes máximos de la plusvalía</td><td>Texto consolidado del TRLRHL en el BOE, art. 107.4</td><td>21 tramos, <a href="{prefix}plusvalia/#coeficientes">publicados aquí</a></td></tr>
        <tr><td>Coeficientes y tipos <em>reales</em> de la plusvalía</td><td>Ministerio de Hacienda, consulta de información impositiva municipal</td><td><strong>{plus_ok} de {len(municipios)}</strong>: los 21 tramos aprobados por cada ayuntamiento. En {plus_sin} no se publica el dato y en {plus_raro} lo que se publica no encaja con el sistema vigente desde el RDL 26/2021, así que remitimos al máximo legal</td></tr>
        <tr><td>Tipo del ICIO y coeficientes de situación del IAE</td><td>La misma consulta del Ministerio</td><td><strong>{icio_ok} de {len(municipios)}</strong></td></tr>
        <tr><td>Tarifa del impuesto de circulación (IVTM)</td><td>La misma consulta del Ministerio</td><td><strong>{ivtm_ok} de {len(municipios)}</strong>: las 24 tarifas por tipo de vehículo</td></tr>
        <tr><td>Serie de población (últimas 6 revisiones del padrón)</td><td>INE, API de la operación DPOP</td><td><strong>{serie_ok} de {len(municipios)}</strong></td></tr>
        <tr><td>Recargos por pago fuera de plazo</td><td>Ley General Tributaria, art. 28</td><td><a href="{prefix}ibi-2026/#recargos">explicados aquí</a></td></tr>
        <tr><td>Web oficial de cada ayuntamiento</td><td>Localizada una a una y comprobada por HTTP</td><td><strong>{web_ok} de {con_web}</strong> respondían correctamente en la última comprobación</td></tr>
        <tr><td>Organismo que publica el calendario de cobro</td><td>Diputaciones y organismos provinciales de recaudación</td><td><strong>{rec_ok} de {rec_total}</strong> comprobados</td></tr>
        <tr><td>Plazo de pago del IBI</td><td>Ley General Tributaria, art. 62.3</td><td>Publicamos el <strong>plazo por defecto</strong> (1 de septiembre a 20 de noviembre) y enlazamos al organismo que publica el calendario del año. <a href="#no-publicamos">Por qué no damos fechas por municipio</a></td></tr>
        <tr><td>Obligación de cobrar la tasa de residuos</td><td>Ley 7/2022, arts. 11.3 a 11.5</td><td>Publicamos la obligación, el plazo que venció el 10 de abril de 2025 y las reducciones que permite la ley. <strong>No publicamos el importe</strong> de ningún municipio: <a href="#no-publicamos">aquí explicamos por qué</a></td></tr>
        <tr><td><strong>Bonificaciones</strong></td><td>TRLRHL, arts. 73 y 74</td><td>Publicamos el <strong>límite legal</strong>, no el porcentaje municipal: ese lo fija cada ordenanza</td></tr>
      </tbody>
    </table>
    <p>En la ficha de cada municipio repetimos este resumen aplicado a sus datos, para que sepas qué puedes dar por bueno sin comprobarlo y qué no.</p>
  </section>

  <section class="sec">
    <h2 id="como-verificamos">Cómo lo verificamos</h2>
    <p>La verificación no es manual ni ocasional, es un proceso que se ejecuta y deja registro:</p>
    <ul>
      <li>Los datos viven en <strong>un único fichero</strong> del que se generan todas las páginas. Antes el mismo dato estaba escrito en cinco sitios distintos y no coincidían entre sí.</li>
      <li>Cada enlace oficial que publicamos se comprueba con una <strong>petición HTTP</strong> y se guarda el código de respuesta y la fecha. Si un enlace deja de responder, aparece en el informe.</li>
      <li>Antes de publicar se pasa una <strong>auditoría automática</strong> del sitio completo: estructura HTML, todos los enlaces internos y sus anclas, imágenes, datos estructurados, sitemap y metadatos duplicados. Si algo apunta a una página o a un ancla que no existe, la publicación se detiene.</li>
      <li>Se ejecutan además <strong>pruebas funcionales en un navegador</strong>: que la calculadora calcule bien, que las tablas ordenen, que los datos de cada página coincidan con la fuente y que las redirecciones lleven a donde deben.</li>
    </ul>
  </section>

  <section class="sec">
    <h2 id="errores-corregidos">Errores que hemos corregido</h2>
    <p>Publicar el registro de errores es incómodo, pero es la única forma de que la palabra «verificado» signifique algo. Esto es lo que hemos encontrado y arreglado en nuestros propios datos:</p>
    <table class="dt">
      <thead><tr><th>Problema</th><th>Alcance</th><th>Estado</th></tr></thead>
      <tbody>
        <tr><td>Tipos de IBI que no coincidían con la fuente oficial</td><td>133 de 134 municipios</td><td>Corregidos con el dato del Ministerio</td></tr>
        <tr><td>Cifras de población sin fuente y sin coincidir con el padrón</td><td>133 de 134</td><td>Corregidas con el dato del INE</td></tr>
        <tr><td>El mismo dato publicado con valores distintos en varias páginas</td><td>920 contradicciones detectadas</td><td>Eliminadas al unificar la fuente de datos</td></tr>
        <tr><td>Enlaces a «sedes electrónicas» que no pertenecían a esos ayuntamientos</td><td>Todas las fichas</td><td>Sustituidos por webs oficiales comprobadas</td></tr>
        <tr><td>Citas de boletines oficiales que no se podían comprobar</td><td>Todas las fichas</td><td>Retiradas y sustituidas por fuentes enlazables</td></tr>
        <tr><td>URLs antiguas que devolvían error 404</td><td>25 direcciones</td><td>Redirigidas a la ficha correspondiente</td></tr>
        <tr><td>Municipios archivados en la provincia equivocada</td><td>Villarrobledo y Lalín</td><td>Movidos a su provincia real</td></tr>
        <tr><td>Importe de la tasa de basuras publicado sin ninguna fuente</td><td>134 de 134 fichas</td><td>Retirado en julio de 2026 (<a href="#no-publicamos">motivo</a>)</td></tr>
        <tr><td>Fechas de cobro presentadas como propias de cada municipio cuando 117 de 134 repetían el mismo intervalo</td><td>134 de 134 fichas</td><td>Retiradas y sustituidas por el plazo legal del art. 62.3 LGT</td></tr>
        <tr><td>Gráfico que sumaba la cuota de IBI y una tasa de basuras sin fuente</td><td>9 pilares autonómicos</td><td>Sustituido por un gráfico del año de los valores catastrales</td></tr>
        <tr><td>Enlace al calendario de la Agencia Tributaria de Murcia en municipios de otras ocho comunidades</td><td>Secciones municipales de los pilares</td><td>Cada municipio enlaza ahora a su organismo recaudador</td></tr>
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2 id="no-publicamos">Qué no publicamos y por qué</h2>
    <p>Hay dos datos que un sitio como este «debería» tener y que aquí no vas a encontrar: <strong>el importe de la tasa de basuras de cada municipio</strong> y <strong>las fechas exactas de cobro</strong>. Hasta julio de 2026 los publicábamos marcados como orientativos. Los hemos retirado, y merece la pena explicar el proceso porque es la parte menos visible de trabajar con datos públicos.</p>
    <h3>La tasa de residuos no está en ninguna fuente agregada</h3>
    <p>El artículo 11.3 de la <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2022-5809" target="_blank" rel="nofollow noopener">Ley 7/2022</a> obliga a todas las entidades locales a aprobar una tasa de residuos «específica, diferenciada y no deficitaria», y el 11.5 solo les exige comunicarla —con sus cálculos— <strong>a su comunidad autónoma</strong>. No hay registro estatal. La consulta de información impositiva del Ministerio de Hacienda, que es nuestra fuente para el resto de tributos, cubre impuestos locales: IBI, IAE, IVTM, ICIO y plusvalía. Las tasas quedan fuera.</p>
    <p>Eso deja una única vía: leer la ordenanza fiscal de cada ayuntamiento. Lo intentamos y estos fueron los obstáculos concretos:</p>
    <ul>
      <li>Las ordenanzas se publican casi siempre como <strong>PDF escaneado o maquetado</strong> colgado de la web municipal o del boletín provincial, no como texto.</li>
      <li>Varias <strong>sedes electrónicas no respondían</strong> en el momento de la consulta, con errores de servidor en la propia página de la tasa.</li>
      <li>Algunos <strong>boletines oficiales autonómicos</strong> presentaban problemas en su certificado de seguridad, lo que impide una descarga automática fiable.</li>
      <li>Las búsquedas devuelven <strong>noticias de prensa</strong>, no la ordenanza. Una cifra de un periódico no es una fuente primaria: no dice a qué epígrafe corresponde, ni si incluye impuestos, ni si sigue vigente.</li>
    </ul>
    <p>Con ese material se puede escribir un número, pero no se puede sostener. Y hay una razón de fondo para no hacerlo: desde 2025 las tarifas están cambiando en masa precisamente por esta ley, así que un importe heredado tiene todas las papeletas de estar mal. En cada ficha explicamos qué obliga la norma y dónde buscar la tarifa concreta; en la <a href="{prefix}tasa-basuras/">guía de la tasa de residuos</a>, cómo se construye y cómo reclamarla.</p>
    <h3>Las fechas de cobro se aprueban cada año</h3>
    <p>El calendario de pago no lo fija la ley, lo aprueba cada ayuntamiento u organismo provincial de recaudación para cada ejercicio y lo publica en su propio anuncio. Lo que sí es verificable es el marco: cuando la ordenanza no señala otro plazo, el pago en período voluntario de los tributos de notificación colectiva y periódica —el IBI lo es— va del <strong>1 de septiembre al 20 de noviembre</strong>, y quien lo modifique no puede dejarlo en menos de dos meses (art. 62.3 de la <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186" target="_blank" rel="nofollow noopener">Ley General Tributaria</a>). Eso es lo que publicamos, junto al enlace al organismo que publica las fechas del año.</p>
    <p>Si tienes delante la ordenanza de tu municipio y quieres que publiquemos su tarifa con la fuente citada, <a href="{prefix}contacto/">mándanosla</a>: es la vía por la que este hueco se puede ir cerrando municipio a municipio.</p>
  </section>

  <section class="sec">
    <h2 id="que-no-hacemos">Qué no hacemos</h2>
    <p>No prestamos asesoramiento fiscal, jurídico ni financiero, y no estamos habilitados para ello. No emitimos recibos, no tramitamos bonificaciones y no representamos a ningún ayuntamiento. La información de este sitio es <strong>informativa y comparativa</strong>.</p>
    <p>Ante cualquier discrepancia entre lo que leas aquí y lo que diga tu ayuntamiento, <strong>manda el ayuntamiento</strong>: la ordenanza fiscal publicada en el boletín oficial es la única fuente con valor jurídico. Y para decisiones que impliquen dinero (recurrir, autoliquidar una plusvalía, solicitar una bonificación) consulta con un profesional habilitado o directamente con el organismo que gestiona el tributo.</p>
  </section>

  <section class="sec">
    <h2 id="correcciones">Política de correcciones</h2>
    <p>Si detectas un dato incorrecto o desactualizado, escríbenos desde la <a href="{prefix}contacto/">página de contacto</a> indicando el municipio, el dato y, si lo tienes, el enlace a la ordenanza o a la fuente. Nuestro compromiso:</p>
    <ul>
      <li><strong>Respondemos en un máximo de 48 horas laborables.</strong></li>
      <li>Si el dato es incorrecto, <strong>lo corregimos y actualizamos la fecha de revisión</strong> de la ficha afectada.</li>
      <li>Si el error afectaba a varias páginas, se corrige en la fuente de datos, de modo que se arregla en todas a la vez.</li>
      <li>Si no podemos contrastar un dato, <strong>no lo publicamos</strong>: dejamos el hueco y explicamos qué falta y dónde buscarlo. Un número con un aviso de «orientativo» sigue siendo un número que alguien va a copiar.</li>
    </ul>
  </section>

  <section class="sec">
    <h2 id="actualizacion">Cada cuánto se actualiza</h2>
    <p>Los tipos de gravamen se revisan cuando el Ministerio publica un nuevo ejercicio, normalmente a lo largo del año siguiente al de aprobación de las ordenanzas. Las cifras de población, cuando el INE publica la revisión anual del padrón. La normativa citada se comprueba contra el texto consolidado del BOE, que incorpora las reformas vigentes.</p>
    <p>Cada página muestra su <strong>fecha de última revisión</strong>. Si ves una fecha antigua en un dato que crees que ha cambiado, avísanos y lo miramos.</p>
    <h3>Normativa que citamos</h3>
    <ul>
      {fuentes_lista}
    </ul>
    <p style="font-size:.85rem;color:var(--mid)">Última revisión de esta página: {HOY_ES}.</p>
  </section>
</div>
"""

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": f"{SITE}/metodologia/",
        "dateModified": TODAY,
        "publisher": {"@type": "Organization", "name": "TasasMunicipales.info", "url": SITE + "/"},
    }
    bloque = ('<script type="application/ld+json">\n'
              + json.dumps(schema, ensure_ascii=False, indent=1) + "\n</script>\n")
    return (tp.head_block(title, description, f"{SITE}/metodologia/", prefix)
            + cuerpo + bloque + tp.footer_block(prefix))


# ──────────────────────────────── sobre nosotros ────────────────────────────────

def sobre_nosotros() -> str:
    municipios = datos()
    con_tipo = sum(1 for m in municipios if m.get("oficial_tipo_urbana"))
    prefix = "../"
    title = "Sobre nosotros: quién está detrás de TasasMunicipales"
    description = (
        "Quién edita este sitio, por qué existe, cómo se obtienen y verifican los datos "
        "fiscales municipales, cómo se financia y qué no ofrecemos. Sin credenciales "
        "inventadas."
    )

    cuerpo = f"""<div class="bc"><a href="{prefix}">Inicio</a><span>›</span><strong>Sobre nosotros</strong></div>
<div class="wrap">
  <h1>Quién está detrás de TasasMunicipales</h1>
  <p class="lead">Este sitio lo edita <strong>Aithamy Rivero</strong>, desde Las Palmas. Voy a ser claro desde el principio: <strong>no soy asesor fiscal, ni abogado, ni economista</strong>, y este sitio no da asesoramiento. Es un proyecto de recopilación y comparación de datos fiscales municipales, y su valor está en de dónde saca esos datos y en decir siempre lo que no puede confirmar.</p>

  <section class="sec">
    <h2 id="por-que">Por qué existe este sitio</h2>
    <p>Empezó por un problema propio: averiguar cuánto se paga de IBI en un municipio concreto es sorprendentemente difícil. El tipo está en una ordenanza fiscal publicada en un boletín provincial, el calendario de cobro en la web de una diputación, el valor catastral en la Sede del Catastro y las bonificaciones repartidas entre la ley estatal y la ordenanza municipal. Nada está junto y casi nada está explicado en un idioma normal.</p>
    <p>La idea del sitio es reunir eso: para cada municipio, qué tipo se aplica, quién cobra, qué bonificaciones existen y dónde comprobarlo en la fuente oficial. Hoy son <strong>{con_tipo} municipios</strong> en nueve comunidades autónomas, con los tipos de IBI urbano y rústico, el año de los valores catastrales, el ICIO, las tarifas del impuesto de circulación y los coeficientes de plusvalía que cada ayuntamiento tiene aprobados.</p>
    <p>Voy añadiendo territorios cuando puedo documentarlos completos, no cuando me interesa tener más páginas: un municipio cuyos datos no puedo enlazar a una fuente oficial no entra. Prefiero cubrir menos y que cada cifra tenga su enlace y su fecha.</p>
  </section>

  <section class="sec">
    <h2 id="como-trabajo">Cómo trabajo con los datos</h2>
    <p>Al no ser profesional del sector, mi criterio no puede ser la autoridad: tiene que ser la <strong>trazabilidad</strong>. Por eso:</p>
    <ul>
      <li>Los tipos de gravamen se toman de la <strong>consulta de información impositiva municipal del Ministerio de Hacienda</strong>, que publica lo aprobado en cada ordenanza. Cada ficha enlaza la fuente y la fecha en que se consultó.</li>
      <li>Las cifras de población son las <strong>oficiales del padrón municipal que publica el INE</strong>, con la serie de las últimas revisiones para que se vea la tendencia.</li>
      <li>Cada afirmación normativa se enlaza al <strong>texto consolidado del BOE</strong>, con el artículo concreto. Si la ley cambia, cambia la página.</li>
      <li>Lo que <strong>no</strong> puedo contrastar no se publica. En julio de 2026 retiré de las 134 fichas el importe de la tasa de basuras y las fechas de cobro por este motivo: no encontré ninguna fuente primaria accesible que los respaldara. <a href="{prefix}metodologia/#no-publicamos">Aquí está el detalle de lo que intenté y por qué falló</a>.</li>
      <li>Los porcentajes de bonificación que publico son los <strong>límites que fija la ley</strong>, no los de cada ordenanza, y lo digo en cada ficha. Prometer un 50% que tu ayuntamiento no aplica sería peor que no decir nada.</li>
    </ul>
    <p>El proceso completo, con la cobertura de cada fuente y el registro de errores que ya he corregido, está en la <a href="{prefix}metodologia/">página de metodología</a>. Incluye los fallos que tenía este mismo sitio y que he ido arreglando: no me parece serio pedir confianza y esconder eso.</p>
  </section>

  <section class="sec">
    <h2 id="como-esta-hecho">Cómo está hecho el sitio</h2>
    <p>No hay redacción externa ni contenido comprado. El sitio es <strong>HTML estático generado a partir de un único fichero de datos</strong>: cuando corrijo un tipo de gravamen, la corrección aparece a la vez en la ficha del municipio, en el comparador nacional, en la página de su comunidad autónoma, en los gráficos y en la calculadora. Antes ese mismo dato estaba escrito a mano en cinco sitios distintos y no coincidía entre sí; de ahí salieron cientos de contradicciones que tuve que arreglar.</p>
    <p>Los gráficos son <strong>propios</strong>: se dibujan con los datos publicados en cada página, llevan el texto como texto (no como imagen) y citan la fuente en el pie. No uso imágenes de stock ni ilustraciones decorativas, entre otras cosas porque no aportan nada a alguien que viene a saber cuánto va a pagar.</p>
    <p>Antes de publicar cualquier cambio se ejecutan tres comprobaciones automáticas: una auditoría de todo el HTML y de todos los enlaces internos, una batería de pruebas en un navegador real (que la calculadora calcule bien, que las tablas ordenen, que los datos coincidan con la fuente) y una revisión del enlazado interno. Si algo apunta a una página que no existe, no se publica.</p>
  </section>

  <section class="sec">
    <h2 id="financiacion">Cómo se financia y qué no compro ni vendo</h2>
    <p>El sitio se sostiene con <strong>publicidad</strong>. Es la única fuente de ingresos y conviene que se sepa, porque afecta a la lectura de cualquier página: si hay anuncios, tienes derecho a saber quién paga.</p>
    <p>Lo que no hay: no cobro por aparecer, ningún ayuntamiento ni organismo paga por su ficha, no hay contenido patrocinado disfrazado de artículo, no vendo datos de nadie y no gano comisión si contratas algo. Tampoco hay enlaces de afiliación en las guías. Si algún día apareciera contenido pagado, iría identificado como tal.</p>
    <p>La publicidad no decide qué se publica. Los municipios que hay son los que he podido documentar con fuente oficial, y el orden de las tablas lo decide el dato, no el interés de nadie. El uso de cookies publicitarias y el consentimiento se explican en la <a href="{prefix}cookies/" rel="nofollow">política de cookies</a>.</p>
  </section>

  <section class="sec">
    <h2 id="para-quien">Para quién es esto</h2>
    <p>Este sitio está pensado para alguien que acaba de recibir un recibo y quiere entenderlo: cuánto se paga en su municipio, por qué su vecino paga distinto, si le corresponde alguna bonificación y dónde comprobarlo en la fuente oficial. También para quien está comprando en otra provincia y quiere saber a qué se compromete.</p>
    <p>Cuando la respuesta a una pregunta es «depende de tu ordenanza», eso es lo que pone, con el enlace a donde mirarlo. Preferimos una respuesta incómoda y correcta a una redonda e inventada. Si buscas una interpretación jurídica de tu caso, este no es el sitio: eso es trabajo de un profesional habilitado.</p>
  </section>

  <section class="sec">
    <h2 id="que-no-soy">Qué no soy y qué no ofrezco</h2>
    <p>No soy asesor fiscal ni tengo habilitación profesional para asesorar. Este sitio <strong>no presta asesoramiento fiscal, jurídico ni financiero</strong>, no tramita nada ante ninguna administración y no está vinculado a ningún ayuntamiento ni organismo público.</p>
    <p>Si tu decisión implica dinero —recurrir un recibo, autoliquidar una plusvalía, solicitar una bonificación con plazo— consulta con un profesional habilitado o directamente con el organismo que gestiona el tributo. Y ante cualquier discrepancia, la ordenanza fiscal publicada en el boletín oficial es la que manda.</p>
  </section>

  <section class="sec">
    <h2 id="contacto">Contacto y correcciones</h2>
    <p>Si encuentras un dato mal, quieres que añada tu municipio o necesitas cualquier aclaración, escríbeme desde la <a href="{prefix}contacto/">página de contacto</a> o a <a href="mailto:soporte@tasasmunicipales.info">soporte@tasasmunicipales.info</a>. Respondo en un máximo de 48 horas laborables.</p>
    <p>Los datos de identificación fiscal y el domicilio del titular, exigidos por el artículo 10 de la LSSI, están en el <a href="{prefix}aviso-legal/" rel="nofollow">aviso legal</a>.</p>
    <p style="font-size:.85rem;color:var(--mid)">Última revisión de esta página: {HOY_ES}.</p>
  </section>
</div>
"""

    schema = {
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "url": f"{SITE}/sobre-nosotros/",
        "name": title,
        "description": description,
        "dateModified": TODAY,
        "mainEntity": {
            "@type": "Person",
            "name": "Aithamy Rivero",
            "url": f"{SITE}/sobre-nosotros/",
            "description": "Editor de TasasMunicipales.info. No es asesor fiscal: el sitio recopila "
                           "y compara datos fiscales municipales a partir de fuentes oficiales.",
        },
        "publisher": {"@type": "Organization", "name": "TasasMunicipales.info", "url": SITE + "/"},
    }
    bloque = ('<script type="application/ld+json">\n'
              + json.dumps(schema, ensure_ascii=False, indent=1) + "\n</script>\n")
    return (tp.head_block(title, description, f"{SITE}/sobre-nosotros/", prefix)
            + cuerpo + bloque + tp.footer_block(prefix))


def redireccion_provincias() -> str:
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Municipios y comunidades — TasasMunicipales</title>
  <link rel="canonical" href="https://tasasmunicipales.info/comunidades/">
  <meta http-equiv="refresh" content="0; url=../comunidades/">
  <link rel="stylesheet" href="../styles.css">
  <script>window.location.replace("../comunidades/");</script>
</head>
<body>
<div class="wrap" style="padding:60px 24px;text-align:center">
  <h1>Esta página se ha unificado</h1>
  <p class="lead">El listado por provincias se ha integrado en el índice de comunidades autónomas y en el comparador nacional de municipios.</p>
  <p><a href="../comunidades/" style="color:var(--accent);font-weight:600">Ir a comunidades autónomas →</a> ·
     <a href="../municipios/" style="color:var(--accent);font-weight:600">comparador de municipios →</a></p>
</div>
</body>
</html>
"""


def main() -> int:
    print("Generando páginas transversales:")
    escribe("municipios", comparador())
    escribe("metodologia", metodologia())
    escribe("sobre-nosotros", sobre_nosotros())
    (ROOT / "provincias" / "index.html").write_text(redireccion_provincias(), encoding="utf-8")
    print("  /provincias/  convertida en redirección a /comunidades/")

    csv = ROOT / "redirects-301.csv"
    lineas = csv.read_text(encoding="utf-8").rstrip("\n").splitlines()
    regla = f"{SITE}/provincias/,{SITE}/comunidades/,301"
    if regla not in lineas:
        lineas.append(regla)
        csv.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        print("  regla 301 de /provincias/ añadida a redirects-301.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
