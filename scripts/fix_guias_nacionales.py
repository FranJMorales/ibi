#!/usr/bin/env python3
"""Corrige las cuatro guias nacionales: datos obsoletos, tablas falsas e higiene.

Lo que arregla, con la evidencia de por que:

1. Tablas «por municipio» congeladas. Cuando aplicamos los datos oficiales del
   Ministerio a las 134 fichas, estas tablas no se tocaron: en /ibi-2026/ 31 de
   los 32 tipos contradecian la ficha del propio municipio (Santander 0,64%
   frente al 0,4% oficial, Monzon 0,58% frente al 0,88%) y su columna «cuota
   media anual» usaba un valor catastral distinto en cada fila sin decirlo. En
   /tasa-basuras/, 23 de 32 importes no coincidian con la ficha.
   Se sustituyen por los extremos calculados desde data/municipios.json mas el
   enlace al comparador. No se replican las 134 filas: eso duplicaria
   /municipios/ cuatro veces.

2. Dos tablas legales falsas, cada una contradicha por su propia pagina:
   - /plusvalia/ daba coeficientes de 0,14 / 0,13 / 0,045 para mas de 20 anos.
     El art. 107.4 TRLRHL dice 0,15 / 0,15 / 0,40, y la tabla correcta ya estaba
     mas abajo en la misma pagina.
   - /ibi-2026/ daba los recargos por meses de retraso. El art. 28 LGT no va por
     meses sino por el momento procesal, y la seccion #recargos lo explicaba bien.

3. /bonificaciones/ desactualizada frente al texto consolidado del TRLRHL
   (ultima actualizacion 21/03/2026): faltaban el art. 74.6 (hasta 95% para
   alquiler con renta limitada) y el 74.7 (hasta 50% por punto de recarga de
   vehiculo electrico), no recogia la novedad del RDL 7/2026 sobre comunidades
   energeticas, decia que el maximo de familia numerosa «no esta fijado
   legalmente» cuando el art. 74.4 fija el 90%, inventaba una bonificacion de
   «inicio de actividad» y confundia BIC con BICE.

4. Higiene: la fecha «1 febrero 2026» escrita a mano en las cuatro y los dos h2
   casi iguales sobre la calculadora en /plusvalia/.

Uso:  python3 scripts/fix_guias_nacionales.py [--dry-run]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
IMPUESTOS = ROOT / "data" / "hacienda_impuestos.json"
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")
HOY_ES = f"{date.today().day} {MESES[date.today().month - 1]} {date.today().year}"
REF_VC = 50000
TRLRHL = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214"
LGT = "https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186"
GUIAS = ("ibi-2026", "plusvalia", "bonificaciones", "tasa-basuras")


def municipios() -> list[dict]:
    return [m for m in json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
            if m.get("oficial_tipo_urbana")]


def impuestos() -> dict:
    return json.loads(IMPUESTOS.read_text(encoding="utf-8")) if IMPUESTOS.exists() else {}


def pct(v: float) -> str:
    return f"{round(v, 4):g}".replace(".", ",") + "%"


def pct2(v: float) -> str:
    return f"{v:.2f}".replace(".", ",") + "%"


def euros(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".") + " €"


def ficha(m: dict) -> str:
    return f"../{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"


def enlace(m: dict) -> str:
    return f'<a href="{ficha(m)}">{html.escape(m["nombre"])}</a>'


def tabla_extremos(filas_alto: list[tuple], filas_bajo: list[tuple],
                   cabeceras: list[str], etq_alto: str, etq_bajo: str) -> str:
    """Tabla con los extremos, separados por una fila de encabezado interior."""
    ncol = len(cabeceras)
    def bloque(titulo: str, filas: list[tuple]) -> str:
        out = [f'        <tr><td colspan="{ncol}" style="background:rgba(0,0,0,.04)">'
               f'<strong>{titulo}</strong></td></tr>']
        destacada = ' class="v"'
        for celdas in filas:
            tds = "".join(
                "<td" + (destacada if i == 1 else "") + f">{c}</td>"
                for i, c in enumerate(celdas)
            )
            out.append(f"        <tr>{tds}</tr>")
        return "\n".join(out)
    head = "".join(f"<th>{c}</th>" for c in cabeceras)
    return (
        '    <table class="dt">\n'
        f"      <thead><tr>{head}</tr></thead>\n"
        "      <tbody>\n"
        + bloque(etq_alto, filas_alto) + "\n"
        + bloque(etq_bajo, filas_bajo) + "\n"
        "      </tbody>\n"
        "    </table>"
    )


def reemplaza_seccion(texto: str, id_h2: str, nuevo: str) -> tuple[str, bool]:
    """Sustituye desde <h2 id="X"> hasta justo antes del siguiente <h2."""
    m = re.search(rf'[ \t]*<h2 id="{id_h2}">.*?(?=<h2)', texto, re.S)
    if not m:
        return texto, False
    return texto[: m.start()] + nuevo + texto[m.end():], True


# --------------------------------------------------------------------------- #
def bloque_ibi(ms: list[dict]) -> str:
    orden = sorted(ms, key=lambda m: -m["oficial_tipo_urbana"])
    ejercicio = orden[0].get("oficial_ejercicio", "2025")
    def filas(sub: list[dict]) -> list[tuple]:
        return [
            (enlace(m), pct(m["oficial_tipo_urbana"]),
             euros(REF_VC * m["oficial_tipo_urbana"] / 100))
            for m in sub
        ]
    tipos = [m["oficial_tipo_urbana"] for m in ms]
    return f"""    <h2 id="municipios">Tipos de IBI por municipio: los extremos</h2>
    <p>Estos son los tipos de gravamen urbanos que el <strong>Ministerio de Hacienda</strong> publica para el ejercicio {ejercicio}, el último disponible. La cuota aplica cada tipo a un mismo valor catastral de {euros(REF_VC)} para que la comparación sea homogénea.</p>
{tabla_extremos(filas(orden[:10]), filas(orden[-10:]), ["Municipio", "Tipo urbano", f"Cuota con VC de {euros(REF_VC)}"], "Los 10 tipos más altos", "Los 10 tipos más bajos")}
    <p>La mediana de los {len(ms)} municipios de la guía es del <strong>{pct2(statistics.median(tipos))}</strong>. <a href="../municipios/" style="color:var(--accent);font-weight:600">Tabla ordenable con los {len(ms)} municipios, su año de valoración catastral, ICIO, IVTM y plusvalía →</a></p>
    <p>Recuerda que un tipo alto no implica un recibo alto: la cuota depende del <a href="../valor-catastral/">valor catastral de tu inmueble</a>. <a href="../analisis/valores-catastrales-antiguos/">Por qué la fecha de la última valoración pesa más que el tipo →</a></p>

"""


def bloque_plusvalia(ms: list[dict], imps: dict) -> str:
    datos = []
    for m in ms:
        imp = imps.get(m.get("oficial_codigo_ine") or "")
        c = (imp or {}).get("conceptos", {})
        def val(cod):
            b = (c.get(cod) or {}).get("valor")
            if b in (None, "", "-"):
                return None
            try:
                return float(str(b).replace(".", "").replace(",", "."))
            except ValueError:
                return None
        coefs = [val(f"C{n}") for n in range(51, 72)]
        validos_c = [x for x in coefs if x is not None]
        # Series muy por debajo del maximo legal son el porcentaje anual del
        # sistema anterior al RDL 26/2021: no las tratamos como coeficientes.
        if not validos_c or not (0.10 <= max(validos_c) <= 0.45):
            continue
        tipos = [val(f"C{n}") for n in range(72, 93)]
        validos_t = [x for x in tipos if x is not None]
        if validos_t:
            datos.append((max(validos_t), m))
    datos.sort(key=lambda par: -par[0])
    ejercicio = ms[0].get("oficial_ejercicio", "2025")
    al_maximo = sum(1 for t, _ in datos if abs(t - 30) < 1e-9)
    def filas(sub):
        return [(enlace(m), pct(t), "Sí" if abs(t - 30) < 1e-9 else "No")
                for t, m in sub]
    return f"""    <h2 id="municipios">El tipo de la plusvalía en los municipios de la guía</h2>
    <p>El tipo de gravamen del IIVTNU lo fija cada ayuntamiento y no puede pasar del <strong>30%</strong>. Estos son los que publica el Ministerio de Hacienda para el ejercicio {ejercicio}: <strong>{al_maximo} de {len(datos)}</strong> municipios aplican el máximo legal.</p>
{tabla_extremos(filas(datos[:10]), filas(datos[-10:]), ["Municipio", "Tipo de gravamen", "¿En el máximo legal?"], "Los 10 tipos más altos", "Los 10 tipos más bajos")}
    <p>En la ficha de cada municipio publicamos sus <strong>21 coeficientes</strong> y su tipo por período de tenencia, con un ejemplo de cálculo. <a href="../municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio →</a> · <a href="../analisis/coeficientes-plusvalia/">Quién aplica el coeficiente máximo →</a></p>
    <p>La base del método objetivo es el <a href="../valor-catastral/">valor catastral del suelo</a>, no el valor total del inmueble: en la Sede del Catastro figuran por separado.</p>

"""


def bloque_bonificaciones(ms: list[dict]) -> str:
    return f"""    <h2 id="municipios">Las bonificaciones en tu municipio</h2>
    <p>Aquí no podemos decirte qué porcentaje aplica tu ayuntamiento, y preferimos decirlo antes que rellenarlo: <strong>no existe una fuente estatal que publique las bonificaciones municipales del IBI</strong>. El Ministerio de Hacienda publica los tipos de gravamen, no los beneficios fiscales de cada ordenanza.</p>
    <p>Lo que sí publicamos en la ficha de cada uno de los {len(ms)} municipios es el <strong>límite legal</strong> de cada bonificación, quién gestiona la recaudación y el enlace donde presentar la solicitud. El porcentaje concreto está en la ordenanza fiscal, que es la única fuente con valor jurídico.</p>
    <p><a href="../municipios/" style="color:var(--accent);font-weight:600">Buscar mi municipio entre los {len(ms)} →</a> · <a href="../comunidades/">Ver por comunidad autónoma →</a></p>
    <p>Las bonificaciones del <a href="../impuesto-circulacion/">impuesto de circulación</a> se regulan aparte, en el artículo 95.6 del TRLRHL, y pueden llegar al 100% en vehículos de 25 años o más. Y si lo que quieres es bajar la base del IBI y no la cuota, el terreno es otro: el <a href="../valor-catastral/">valor catastral</a>.</p>

"""


LEY7 = "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5809"


def bloque_basuras(ms: list[dict]) -> str:
    """Sustituye la tabla de importes por municipio.

    Los importes que se publicaban no tenian fuente y se han retirado del sitio
    (scripts/retirar_datos_sin_fuente.py). Esta seccion explica por que no existe
    el dato agregado, citando el articulo 11 de la Ley 7/2022, y da el camino para
    que el lector localice su propia tarifa.
    """
    return f"""    <h2 id="municipios">Cuánto se paga en tu municipio: por qué aquí no hay una tabla</h2>
    <p>Es la pregunta que más nos llega y la única de todo el sitio que no podemos responder con una cifra. En el resto de tributos municipales —<a href="../ibi-2026/">IBI</a>, <a href="../plusvalia/">plusvalía</a>, <a href="../impuesto-circulacion/">impuesto de circulación</a>, ICIO— publicamos el dato de cada uno de los {len(ms)} municipios porque existe una fuente estatal que lo recoge. Con la tasa de residuos no existe, y merece la pena explicar por qué: dice bastante sobre cómo está organizada la información fiscal municipal en España.</p>

    <h3>No hay ningún registro estatal de tasas de residuos</h3>
    <p>La <a href="{LEY7}" target="_blank" rel="nofollow noopener">Ley 7/2022</a> obliga a aprobar la tasa, pero en su artículo 11.5 solo exige a las entidades locales comunicarla —junto con los cálculos con los que la han construido— <strong>a las autoridades competentes de su comunidad autónoma</strong>. No al Estado. No hay, por tanto, una base de datos nacional equivalente a la que sí existe para los impuestos locales.</p>
    <p>Nuestra fuente habitual, la consulta de información impositiva municipal del Ministerio de Hacienda, cubre exactamente eso: <strong>impuestos</strong> (IBI, IAE, IVTM, ICIO e IIVTNU). Las tasas quedan fuera de su ámbito, porque no son impuestos: son la contraprestación de un servicio.</p>
    <p>Eso deja una única vía para cada municipio: su ordenanza fiscal. Lo intentamos y estos fueron los obstáculos, uno por uno: las ordenanzas se publican casi siempre como <strong>PDF</strong> colgado de la web municipal o del boletín provincial, no como texto; varias <strong>sedes electrónicas devolvían errores de servidor</strong> en la propia página de la tasa; algunos <strong>boletines autonómicos</strong> presentaban problemas de certificado que impiden una descarga fiable; y las búsquedas devuelven <strong>noticias de prensa</strong>, que no sirven como fuente: no dicen a qué epígrafe corresponde la cifra, si incluye impuestos indirectos o si sigue vigente.</p>
    <div class="hb">
      <strong>📌 Por qué no publicamos una cifra «orientativa»</strong>
      Hasta julio de 2026 sí lo hacíamos, con un aviso de que no estaba contrastada. La retiramos porque un número con una advertencia sigue siendo un número que alguien copia, cita y usa para decidir. Y con las tarifas cambiando en masa desde 2025 precisamente por esta ley, un importe heredado tiene todas las papeletas de estar mal. <a href="../metodologia/#no-publicamos">Nuestra política sobre los datos que no podemos verificar</a>.
    </div>

    <h3>Cómo encontrar la tarifa de tu municipio en tres pasos</h3>
    <ol>
      <li><strong>Busca la ordenanza fiscal de la tasa de residuos</strong> en la web de tu ayuntamiento, normalmente en el apartado de «ordenanzas fiscales» o «normativa». El nombre exacto varía: «tasa por la prestación del servicio de recogida de basuras», «tasa de gestión de residuos», «prestación patrimonial de carácter público no tributario por el servicio de residuos».</li>
      <li><strong>Ve al cuadro de tarifas y localiza el epígrafe de viviendas.</strong> Ahí verás si tu municipio cobra un importe único o lo reparte por superficie, por valor catastral, por zona, por número de personas empadronadas o por generación real de residuos.</li>
      <li><strong>Comprueba las reducciones.</strong> Si no encuentras la ordenanza, el importe exacto que te han girado figura en el recibo, en el concepto de residuos, que puede venir en el mismo documento que el IBI o por separado.</li>
    </ol>
    <p>Si tu municipio pertenece a una <strong>mancomunidad o consorcio de residuos</strong>, es posible que la tasa la apruebe y la cobre esa entidad y no el ayuntamiento: en ese caso la ordenanza está publicada a su nombre.</p>

    <h3>Si tienes la ordenanza, mándanosla</h3>
    <p>Es la vía por la que este hueco se puede ir cerrando municipio a municipio: si nos envías el enlace a la ordenanza o al anuncio del boletín provincial, publicamos la tarifa citando la fuente y con su fecha. <a href="../contacto/" style="color:var(--accent);font-weight:600">Aportar la ordenanza de mi municipio →</a></p>
    <p>Mientras tanto, lo que sí puedes comparar entre municipios con datos oficiales está en el <a href="../municipios/" style="color:var(--accent);font-weight:600">comparador de los {len(ms)} municipios</a>: tipos de IBI, año de los valores catastrales, ICIO, impuesto de circulación y plusvalía.</p>

"""


BLOQUE_SUBIDA = f"""    <h2 id="subida">Por qué ha subido la tasa de basuras: qué obliga exactamente la ley</h2>
    <p>El artículo 11.3 de la <a href="{LEY7}" target="_blank" rel="nofollow noopener">Ley 7/2022, de residuos y suelos contaminados para una economía circular</a>, obliga a las entidades locales a establecer una tasa —o, en su caso, una prestación patrimonial de carácter público no tributaria— con tres condiciones: <strong>específica, diferenciada y no deficitaria</strong>. Debe además permitir implantar sistemas de pago por generación y reflejar el coste real, directo o indirecto, del servicio.</p>
    <p>Cada uno de esos adjetivos tiene consecuencias concretas en el recibo:</p>
    <ul>
      <li><strong>Específica y diferenciada:</strong> la tasa de residuos no puede ir escondida dentro de otro tributo ni cobrarse junto al agua como un concepto indistinguible. De ahí que en muchos municipios haya aparecido un recibo nuevo donde antes no había ninguno.</li>
      <li><strong>No deficitaria:</strong> los ingresos tienen que cubrir el coste del servicio. Muchos ayuntamientos venían financiando la recogida con sus ingresos generales, así que el ajuste ha sido una subida de golpe, no un incremento gradual.</li>
      <li><strong>Que refleje el coste real:</strong> la ley enumera qué debe computarse —recogida, transporte y tratamiento, vigilancia de esas operaciones, mantenimiento y vigilancia posterior al cierre de los vertederos, campañas de concienciación— y también qué debe restarse: los ingresos de la responsabilidad ampliada del productor y los de la venta de materiales y energía.</li>
      <li><strong>Pago por generación:</strong> es la dirección a la que apunta la norma. Por eso las ordenanzas nuevas reparten por superficie, empadronados, zona o aportación real en lugar de cobrar una cuota única.</li>
    </ul>
    <p>El plazo era de <strong>tres años desde la entrada en vigor de la ley</strong>. La ley se publicó en el BOE el 9 de abril de 2022 y entró en vigor al día siguiente, así que el plazo venció el <strong>10 de abril de 2025</strong>: de ahí la oleada de ordenanzas nuevas en 2025 y 2026.</p>
    <div class="hb">
      <strong>📌 El umbral de 5.000 habitantes que circula en la prensa</strong>
      Se repite mucho que la tasa solo obliga a los municipios de más de 5.000 habitantes. En la Ley 7/2022 ese umbral aparece en otros sitios: en el artículo 12.5.b), para la obligación de aprobar programas de gestión de residuos, y en el 25.2.b), que fijó la recogida separada de biorresiduos antes del 30 de junio de 2022 para los municipios de más de cinco mil habitantes y antes del 31 de diciembre de 2023 para el resto. El artículo 11.3, el de la tasa, <strong>no distingue por tamaño de municipio</strong>.
    </div>
    <p>A la obligación legal se suma un factor de coste: esa misma recogida separada de biorresiduos exige contenedor propio, ruta propia y planta de tratamiento, y encarece el servicio que la tasa tiene que cubrir. La ley admite expresamente el <strong>compostaje doméstico o comunitario</strong> como forma de recogida separada, lo que explica que muchas ordenanzas lo bonifiquen.</p>

"""


TABLA_BONIFICACIONES = f"""    <h2 id="tipos">Tipos de bonificaciones en el IBI</h2>
    <p>El <a href="{TRLRHL}" target="_blank" rel="nofollow noopener">texto refundido de la Ley Reguladora de las Haciendas Locales</a> distingue entre bonificaciones <strong>obligatorias</strong> —que el ayuntamiento debe aplicar aunque su ordenanza no las mencione— y <strong>potestativas</strong> —que existen solo si la ordenanza las regula, y con el porcentaje que decida el pleno hasta el tope legal—.</p>
    <table class="dt">
      <thead><tr><th>Bonificación</th><th>Tipo</th><th>Tope legal</th><th>Base</th></tr></thead>
      <tbody>
        <tr><td>Vivienda de protección oficial y equiparables</td><td>Obligatoria</td><td class="v">50% durante los 3 ejercicios siguientes a la calificación definitiva</td><td>Art. 73.2</td></tr>
        <tr><td>Empresas de urbanización, construcción y promoción (obra nueva y rehabilitación)</td><td>Obligatoria</td><td class="v">50%–90%</td><td>Art. 73.1</td></tr>
        <tr><td>Cooperativas agrarias y de explotación comunitaria de la tierra</td><td>Obligatoria</td><td class="v">95%</td><td>Art. 73.3</td></tr>
        <tr><td>Familia numerosa</td><td>Potestativa</td><td class="v">Hasta 90%</td><td>Art. 74.4</td></tr>
        <tr><td>Aprovechamiento térmico o eléctrico de energía solar o del ambiente</td><td>Potestativa</td><td class="v">Hasta 50%</td><td>Art. 74.5</td></tr>
        <tr><td>Punto de recarga de vehículo eléctrico</td><td>Potestativa</td><td class="v">Hasta 50%</td><td>Art. 74.7</td></tr>
        <tr><td>Vivienda de alquiler con renta limitada por una norma jurídica</td><td>Potestativa</td><td class="v">Hasta 95%</td><td>Art. 74.6</td></tr>
        <tr><td>Actividades económicas declaradas de especial interés o utilidad municipal</td><td>Potestativa</td><td class="v">Hasta 95%</td><td>Art. 74.2 quáter</td></tr>
        <tr><td>Organismos públicos de investigación y enseñanza universitaria</td><td>Potestativa</td><td class="v">Hasta 95%</td><td>Art. 74.2 bis</td></tr>
        <tr><td>Bienes inmuebles de características especiales (BICE)</td><td>Potestativa</td><td class="v">Hasta 90%</td><td>Art. 74.3</td></tr>
        <tr><td>Domiciliación, pago anticipado o fraccionado</td><td>Potestativa</td><td class="v">Hasta 5%</td><td>Art. 9.1</td></tr>
      </tbody>
    </table>
    <p style="font-size:.85rem;color:var(--mid)">Todos los artículos remiten al texto consolidado del TRLRHL en el BOE. Los apartados 74.6 y 74.7 se añadieron después de la redacción original de la ley, y el 74.5 fue modificado por el Real Decreto-ley 7/2026, en vigor desde el 22 de marzo de 2026.</p>

"""

RENOVABLES = """    <h2 id="renovables">Bonificación IBI por placas solares y energías renovables</h2>
    <p>El artículo 74.5 del TRLRHL permite a las ordenanzas bonificar <strong>hasta el 50%</strong> de la cuota de los inmuebles con sistemas de aprovechamiento <strong>térmico o eléctrico de la energía del sol o del ambiente</strong>. La ley pone una condición y deja el resto a la ordenanza:</p>
    <ul>
      <li><strong>Condición legal:</strong> las instalaciones deben disponer de la <strong>homologación</strong> correspondiente de la Administración competente. Sin ella no cabe la bonificación.</li>
      <li><strong>Porcentaje y duración:</strong> los fija la ordenanza de tu municipio. La ley no establece un número de años, así que las horquillas que se leen por ahí («3 a 5 años») son lo habitual en la práctica, no una regla.</li>
      <li><strong>Comunidades energéticas:</strong> desde el Real Decreto-ley 7/2026 la ordenanza puede fijar porcentajes distintos cuando se ceden espacios para instalaciones cuyo uso o propiedad esté asociado a una comunidad energética.</li>
      <li><strong>Documentación habitual:</strong> certificado del instalador autorizado, boletín eléctrico y memoria técnica.</li>
    </ul>
    <div class="hb gold">
      <strong>⚡ Y desde 2021, también los puntos de recarga</strong>
      El artículo 74.7 permite bonificar hasta el 50% de la cuota de los inmuebles con puntos de recarga para vehículos eléctricos, con la misma exigencia de homologación. Es una bonificación mucho menos conocida que la de las placas y se pide igual: por escrito y ante quien gestione tu recaudación.
    </div>

"""

OTRAS = """    <h2 id="otras">Otras bonificaciones potestativas</h2>
    <h3>Domiciliación bancaria</h3>
    <p>Muchas ordenanzas descuentan un pequeño porcentaje (hasta el 5%, al amparo del artículo 9.1 del TRLRHL) por domiciliar el recibo con antelación. Es la más sencilla de todas: basta comunicar el IBAN a quien gestione la recaudación.</p>
    <h3>Vivienda de alquiler con renta limitada</h3>
    <p>El artículo 74.6 permite bonificar <strong>hasta el 95%</strong> la cuota de los inmuebles de uso residencial destinados a <strong>alquiler de vivienda con renta limitada por una norma jurídica</strong>. Es la vía por la que algunos ayuntamientos incentivan el alquiler asequible, y suele exigir acreditar el contrato y el régimen de limitación de renta.</p>
    <h3>Actividades de especial interés municipal</h3>
    <p>El artículo 74.2 quáter permite bonificar <strong>hasta el 95%</strong> los inmuebles en los que se desarrollen actividades económicas declaradas de <strong>especial interés o utilidad municipal</strong> por razones sociales, culturales, histórico-artísticas o de fomento del empleo. La declaración la acuerda el Pleno del ayuntamiento, previa solicitud, por mayoría simple.</p>
    <h3>Bienes inmuebles de características especiales (BICE)</h3>
    <p>El artículo 74.3 permite bonificar <strong>hasta el 90%</strong> cada grupo de bienes inmuebles de características especiales: presas, autopistas, centrales de energía, aeropuertos y puertos. Conviene no confundirlos con los <em>bienes de interés cultural</em>, que son otra figura y siguen otra vía.</p>

"""

COMO_SOLICITAR = f"""    <h2 id="como-solicitar">Cómo y cuándo solicitar las bonificaciones del IBI</h2>
    <ul>
      <li><strong>Nunca se aplican de oficio.</strong> Hay que pedirlas por escrito, incluso las obligatorias.</li>
      <li><strong>El plazo lo fija cada ordenanza.</strong> No hay una fecha estatal: en muchos municipios está en el primer trimestre y en otros vence al abrirse el período de pago. Es el primer dato que conviene mirar.</li>
      <li><strong>Dónde:</strong> en el ayuntamiento o en el organismo provincial que gestione su recaudación. En la ficha de cada municipio indicamos cuál es y enlazamos su sede.</li>
      <li><strong>Qué llevar:</strong> formulario de solicitud más la documentación que acredite el supuesto (título de familia numerosa, homologación de la instalación, contrato de alquiler…).</li>
      <li><strong>Vigencia:</strong> algunas exigen renovación anual y otras se mantienen durante el período que fije la ordenanza. Pregúntalo al solicitarla.</li>
    </ul>
    <div class="hb red">
      <strong>⚠️ Fuera de plazo, no se aplica hasta el ejercicio siguiente</strong>
      El IBI se devenga el 1 de enero, así que una solicitud tardía normalmente surte efecto en el recibo del año que viene, no en el que ya tienes encima de la mesa. Con una cuota de 600 € y una bonificación del 50%, cada año de retraso son 300 € perdidos.
    </div>

"""


SIGUIENTE_PASO = """    <h2 id="siguiente-paso">Ya tienes la cuota: qué mirar ahora</h2>
    <p>La calculadora aplica el tipo oficial de tu municipio al valor catastral que introduzcas. Si el resultado no cuadra con tu recibo, casi siempre es por una de estas cuatro razones, y cada una tiene su propia página:</p>
    <ul>
      <li><strong>La base no es el valor catastral entero.</strong> Tras una revisión catastral se aplica una reducción que dura nueve años, así que se tributa sobre la base liquidable. <a href="../valor-catastral/">Cómo se pasa del valor catastral a la base liquidable →</a></li>
      <li><strong>Tienes una bonificación reconocida</strong> que se resta de la cuota íntegra. <a href="../bonificaciones/">Qué bonificaciones existen y cuál es su tope legal →</a></li>
      <li><strong>El recibo incluye otros conceptos</strong>, como la tasa de basuras, que se giran en el mismo documento. <a href="../tasa-basuras/">Cuánto se paga de basuras y quién la paga →</a></li>
      <li><strong>El tipo ha cambiado este ejercicio.</strong> Publicamos el último que el Ministerio de Hacienda tiene registrado; si el pleno lo modificó después, estará antes en la ordenanza. <a href="../ibi-2026/">Cómo funciona el IBI y cuándo se paga →</a></li>
    </ul>
    <p>Y si lo que quieres es comparar: <a href="../municipios/" style="color:var(--accent);font-weight:600">tabla con los tipos, el año de valoración catastral, el ICIO, el IVTM y la plusvalía de 134 municipios →</a></p>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ms = municipios()
    imps = impuestos()
    hechos: Counter[str] = Counter()
    textos = {g: (ROOT / g / "index.html").read_text(encoding="utf-8") for g in GUIAS}

    # ── 1. tablas por municipio ──
    for guia, nuevo in (
        ("ibi-2026", bloque_ibi(ms)),
        ("plusvalia", bloque_plusvalia(ms, imps)),
        ("bonificaciones", bloque_bonificaciones(ms)),
        ("tasa-basuras", bloque_basuras(ms)),
    ):
        textos[guia], ok = reemplaza_seccion(textos[guia], "municipios", nuevo)
        if ok:
            hechos[f"{guia}: tabla por municipio regenerada"] += 1

    # ── 2. tablas legales falsas ──
    t, n = re.subn(
        r'[ \t]*<table class="dt">\s*<thead><tr><th>Momento del pago</th>.*?</table>\s*',
        f'    <p>Si no pagas dentro del período voluntario, la deuda entra en vía '
        f'ejecutiva y el recargo depende del momento en que reacciones, no de los '
        f'meses transcurridos: lo regula el artículo 28 de la '
        f'<a href="{LGT}" target="_blank" rel="nofollow noopener">Ley General '
        f'Tributaria</a>. <a href="#recargos">Ver los tres tramos de recargo →</a></p>\n\n',
        textos["ibi-2026"], count=1, flags=re.S,
    )
    if n:
        hechos["ibi-2026: tabla de recargos por meses eliminada"] += 1
        textos["ibi-2026"] = t

    t, n = re.subn(
        r'[ \t]*<h3>Coeficientes máximos 2026 \(método objetivo\)</h3>\s*'
        r'<table class="dt">.*?</table>\s*',
        '    <p>El coeficiente que se aplica depende de los años transcurridos y lo '
        'aprueba cada ayuntamiento sin superar el tope estatal. '
        '<a href="#coeficientes">Tabla completa de los 21 tramos con su tope legal →</a></p>\n\n',
        textos["plusvalia"], count=1, flags=re.S,
    )
    if n:
        hechos["plusvalia: tabla de coeficientes falsa eliminada"] += 1
        textos["plusvalia"] = t

    # ── 3. bonificaciones al dia con el TRLRHL vigente ──
    for id_h2, nuevo, clave in (
        ("tipos", TABLA_BONIFICACIONES, "tabla de topes legales reescrita"),
        ("renovables", RENOVABLES, "renovables y punto de recarga actualizados"),
        ("otras", OTRAS, "otras bonificaciones corregidas (BICE, 74.6, 74.2 quáter)"),
        ("como-solicitar", COMO_SOLICITAR, "plazo sin inventar el 31 de marzo"),
    ):
        textos["bonificaciones"], ok = reemplaza_seccion(
            textos["bonificaciones"], id_h2, nuevo)
        if ok:
            hechos[f"bonificaciones: {clave}"] += 1

    t = textos["bonificaciones"]
    t2 = t.replace(
        '<tr><td>General (3–4 hijos)</td><td class="v">25%–50%</td>'
        '<td>No fijado legalmente</td></tr>',
        '<tr><td>General (3 o 4 hijos)</td><td class="v">25%–50% en la mayoría de '
        'ordenanzas</td><td>Hasta 90% (art. 74.4)</td></tr>',
    ).replace(
        '<tr><td>Especial (5 o más hijos)</td><td class="v">50%–90%</td>'
        '<td>No fijado legalmente</td></tr>',
        '<tr><td>Especial (5 o más hijos)</td><td class="v">50%–90% en la mayoría de '
        'ordenanzas</td><td>Hasta 90% (art. 74.4)</td></tr>',
    ).replace(
        "④ Solicitar antes del plazo (generalmente 31 de marzo)",
        "④ Solicitarlo en el plazo que fije la ordenanza de tu municipio",
    )
    if t2 != t:
        hechos["bonificaciones: máximo legal de familia numerosa corregido"] += 1
        textos["bonificaciones"] = t2
    # la descripción también prometía el 31 de marzo como norma
    t = textos["bonificaciones"].replace(
        "cómo solicitarlas antes del 31 de marzo.",
        "cómo y cuándo solicitarlas.",
    )
    if t != textos["bonificaciones"]:
        hechos["bonificaciones: descripción sin el plazo inventado"] += 1
        textos["bonificaciones"] = t

    # ── 4. higiene ──
    # La seccion #subida se queda corta y con afirmaciones sin fuente: se sustituye
    # por el contenido del art. 11 de la Ley 7/2022, verificado en el BOE.
    textos["tasa-basuras"], ok = reemplaza_seccion(
        textos["tasa-basuras"], "subida", BLOQUE_SUBIDA)
    if ok:
        hechos["tasa-basuras: sección de la subida con el art. 11 de la Ley 7/2022"] += 1

    # Los rangos de importe salian de los datos que hemos retirado por no tener
    # fuente: se sustituyen por lo que si es verificable.
    for viejo in (
        "Para una vivienda habitual de tamaño estándar, el rango habitual en los "
        "municipios de nuestra guía es de <strong>82 € a 145 € al año</strong>.",
        "Para una vivienda habitual de tamaño estándar, el rango en los municipios de "
        "nuestra guía va de <strong>78 € a 155 € al año</strong>, con una mediana de "
        "105 €.",
    ):
        t = textos["tasa-basuras"].replace(
            viejo,
            "No hay una respuesta única ni una fuente estatal que publique la tarifa "
            "de cada municipio: la fija la ordenanza fiscal de tu ayuntamiento y "
            "depende del tamaño del inmueble, del uso y, cada vez más, de la "
            "generación real de residuos. "
            '<a href="#municipios">Cómo localizar la tarifa de tu municipio →</a>',
        )
        if t != textos["tasa-basuras"]:
            hechos["tasa-basuras: rango sin fuente sustituido"] += 1
            textos["tasa-basuras"] = t

    t = textos["tasa-basuras"].replace(
        "Cada ayuntamiento fija su importe anual en la ordenanza fiscal "
        "correspondiente, con enormes diferencias entre municipios: desde menos de "
        "80 € hasta más de 200 € anuales para una vivienda habitual.",
        "Cada ayuntamiento fija su importe en la ordenanza fiscal correspondiente, y "
        "las diferencias entre municipios son grandes porque la ley no fija cuantías: "
        "fija los principios con los que hay que calcularlas.",
    )
    if t != textos["tasa-basuras"]:
        hechos["tasa-basuras: horquilla sin fuente («de 80 a 200 €») retirada"] += 1
        textos["tasa-basuras"] = t

    # El <title>, la meta y el JSON-LD de /tasa-basuras/ prometian «importes por
    # municipio», que es justo lo que no podemos publicar.
    for viejo, nuevo, clave in (
        ('content="Cuánto cuesta la tasa de residuos en 2026, por qué ha subido con la '
         'Ley 7/2022, quién la paga en un alquiler y cómo reclamar un recibo '
         'incorrecto. Importes por municipio y plazos de pago."',
         'content="Qué obliga la Ley 7/2022 sobre la tasa de residuos, por qué ha '
         'subido, quién la paga en un alquiler, cómo reclamar un recibo incorrecto y '
         'cómo localizar la tarifa de tu municipio."',
         "meta description sin la promesa de importes"),
        ('"headline":"Tasa de Basuras 2026: quién paga, importe por municipio y cómo '
         'reclamar"',
         '"headline":"Tasa de basuras 2026: qué obliga la Ley 7/2022, quién paga y cómo '
         'reclamar"',
         "titular del JSON-LD"),
        ('"description":"Tasa de basuras 2026: quién paga en alquiler, por qué ha '
         'subido y cómo reclamar. Guía con importes de 134 municipios de España '
         'actualizada."',
         '"description":"Tasa de basuras 2026: qué exige la Ley 7/2022, quién paga en '
         'alquiler, por qué ha subido, cómo reclamar y dónde localizar la tarifa de tu '
         'municipio."',
         "descripción del JSON-LD"),
    ):
        # sin limite: la misma descripcion se repite en <meta name> y en og:description
        if viejo in textos["tasa-basuras"]:
            textos["tasa-basuras"] = textos["tasa-basuras"].replace(viejo, nuevo)
            hechos[f"tasa-basuras: {clave}"] += 1

    # dateModified escrito a mano y ya caducado en las cuatro guias
    for guia in GUIAS:
        t, n = re.subn(r'"dateModified":"\d{4}-\d{2}-\d{2}"',
                       f'"dateModified":"{date.today().isoformat()}"', textos[guia])
        if n and t != textos[guia]:
            hechos[f"{guia}: dateModified del JSON-LD al día"] += 1
            textos[guia] = t

    t = textos["plusvalia"].replace(
        '<h2 id="calculadora-plusvalia">Calculadora de plusvalía municipal 2026</h2>',
        '<h2 id="calculadora-plusvalia">Calcula tu plusvalía municipal</h2>',
    )
    if t != textos["plusvalia"]:
        hechos["plusvalia: los dos h2 casi iguales de la calculadora"] += 1
        textos["plusvalia"] = t

    # ── 5. dos respuestas de la FAQ que no se sostienen ──
    # Estan duplicadas en el HTML y en el JSON-LD: hay que sustituirlas en las dos.
    faq_fixes = [
        (
            "bonificaciones",
            "Combinando familia numerosa (50%) y placas solares (20%), podrías reducir "
            "tu recibo de IBI hasta un 70%, lo que en un recibo de 600 € supone pagar "
            "solo 180 € al año.",
            "Depende de tu ordenanza y de si las bonificaciones son compatibles entre "
            "sí. Los topes legales son altos —hasta el 90% en familia numerosa y hasta "
            "el 50% en energía solar— pero cada pleno fija el porcentaje real y muchas "
            "ordenanzas limitan la acumulación. Con una cuota de 600 € y una "
            "bonificación efectiva del 50%, el ahorro es de 300 € al año.",
        ),
        (
            "bonificaciones",
            "Combinando familia numerosa (50%) y placas solares (20%), podrías reducir "
            "tu recibo hasta un 70%.",
            "Depende de tu ordenanza y de si las bonificaciones son compatibles entre "
            "sí: los topes legales son altos, pero cada pleno fija el porcentaje real "
            "y muchas ordenanzas limitan la acumulación.",
        ),
        (
            "ibi-2026",
            "Depende del municipio. La mayoría tienen el período voluntario entre "
            "septiembre y noviembre. Consulta la tabla superior o busca tu municipio "
            "para ver las fechas exactas.",
            "Depende del municipio: la fecha la fija cada ordenanza y no hay un plazo "
            "estatal. La mayoría lo sitúan entre septiembre y noviembre. En la ficha de "
            "tu municipio indicamos el período que recogemos y quién publica el "
            "calendario oficial.",
        ),
        (
            "ibi-2026",
            "Depende del municipio: la fecha la fija cada ordenanza y no hay un plazo "
            "estatal. La mayoría lo sitúan entre septiembre y noviembre. En la ficha de "
            "tu municipio indicamos el período que recogemos y quién publica el "
            "calendario oficial.",
            "La fija cada ordenanza y se aprueba cada ejercicio, así que no publicamos "
            "fechas por municipio. Cuando la ordenanza no señala otro plazo se aplica "
            "el del artículo 62.3 de la Ley General Tributaria, del 1 de septiembre al "
            "20 de noviembre, y quien lo modifique no puede dejarlo en menos de dos "
            "meses. En la ficha de tu municipio enlazamos al organismo que publica el "
            "calendario del año.",
        ),
        (
            "tasa-basuras",
            "Habitualmente en el primer trimestre del año, aunque varía por municipio. "
            "Algunos ayuntamientos la incluyen en el padrón municipal junto con otras "
            "tasas.",
            "Lo fija la ordenanza de cada ayuntamiento y no hay un plazo estatal, así "
            "que no publicamos fechas por municipio. Algunos la giran en el mismo "
            "recibo que el IBI y otros por separado. Cuando la ordenanza no señala "
            "plazo se aplica el del artículo 62.3 de la Ley General Tributaria, del 1 "
            "de septiembre al 20 de noviembre.",
        ),
        (
            "tasa-basuras",
            "Habitualmente en el primer trimestre del año, aunque varía por municipio.",
            "Lo fija la ordenanza de cada ayuntamiento; no hay un plazo estatal y no "
            "publicamos fechas por municipio.",
        ),
    ]
    for guia, viejo, nuevo in faq_fixes:
        n = textos[guia].count(viejo)
        if n:
            textos[guia] = textos[guia].replace(viejo, nuevo)
            hechos[f"{guia}: respuesta de la FAQ corregida ({n} apariciones)"] += 1

    # los rótulos del índice deben decir lo mismo que el h2 al que llevan
    for guia, viejo, nuevo in (
        ("ibi-2026", '<a href="#municipios">IBI por municipio 2026</a>',
         '<a href="#municipios">Tipos de IBI por municipio</a>'),
        ("plusvalia", '<a href="#municipios">Calculadora por municipio</a>',
         '<a href="#municipios">El tipo en cada municipio</a>'),
        ("plusvalia", '<a href="#calculadora-plusvalia">Calculadora interactiva</a>',
         '<a href="#calculadora-plusvalia">Calcula tu plusvalía</a>'),
        ("bonificaciones", '<a href="#municipios">Bonificaciones por municipio</a>',
         '<a href="#municipios">Las bonificaciones en tu municipio</a>'),
        ("tasa-basuras", '<a href="#municipios">Tasa de basura por municipio</a>',
         '<a href="#municipios">Tasa de basuras por municipio</a>'),
    ):
        if viejo in textos[guia]:
            textos[guia] = textos[guia].replace(viejo, nuevo, 1)
            hechos[f"{guia}: rótulo del índice alineado con su h2"] += 1

    for guia in GUIAS:
        t, n = re.subn(r"Actualizado: [^·<]*·", f"Actualizado: {HOY_ES} ·",
                       textos[guia], count=1)
        if n and t != textos[guia]:
            hechos[f"{guia}: fecha de actualización al día"] += 1
            textos[guia] = t

    # bloque de salida en la calculadora, que no enlazaba a ninguna parte
    calc = ROOT / "calculadora-ibi" / "index.html"
    if calc.exists():
        t = calc.read_text(encoding="utf-8")
        if 'id="siguiente-paso"' not in t:
            m = re.search(r'([ \t]*)<h2[^>]*>Preguntas frecuentes', t)
            if m:
                t = t[: m.start()] + SIGUIENTE_PASO + t[m.start():]
                if not args.dry_run:
                    calc.write_text(t, encoding="utf-8")
                hechos["calculadora: bloque de siguientes pasos con enlaces"] += 1

    for guia in GUIAS:
        destino = ROOT / guia / "index.html"
        if textos[guia] != destino.read_text(encoding="utf-8") and not args.dry_run:
            destino.write_text(textos[guia], encoding="utf-8")

    for k in sorted(hechos):
        print(f"  {k}")
    if not hechos:
        print("  (nada que cambiar)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
