#!/usr/bin/env python3
"""Mejoras basadas en los datos de Search Console (ultimos 3 meses).

1. Titles y descriptions de las guias nacionales. Acumulan miles de impresiones con
   un CTR del 0,4%-0,9%: el problema no es el contenido, es que el titulo no responde
   a lo que la gente escribe («cuándo se paga el ibi 2026» suma cientos de
   impresiones y el titulo no lo mencionaba).
2. Se corrige la afirmacion obsoleta de «26 municipios» (son 134).
3. Se publica en /plusvalia/ la tabla oficial de coeficientes maximos del IIVTNU,
   extraida del texto consolidado del TRLRHL en el BOE.
4. Tomelloso: su ficha acumula 8.812 impresiones con un CTR del 0,18% porque quien
   busca quiere el tipo de gravamen y los coeficientes de la ordenanza. Se anade una
   seccion que explica los limites legales, el ejemplo de calculo y donde esta el
   texto oficial, sin inventar los valores concretos del municipio.

Uso:  python3 scripts/improve_national_guides.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COEFS = ROOT / "data" / "coeficientes_plusvalia.json"

# pagina -> (title, description). Redactados a partir de las consultas reales.
METADATOS = {
    "ibi-2026": (
        "IBI 2026: cuándo se paga, cómo se calcula y cuánto sube",
        "Cuándo se paga el IBI en 2026, a qué año corresponde el recibo, cómo se "
        "calcula desde el valor catastral, cómo fraccionarlo y qué recargos hay si te "
        "pasas de plazo. Con los tipos oficiales de 134 municipios.",
    ),
    "plusvalia": (
        "Plusvalía municipal 2026: coeficientes, cálculo y plazos",
        "Coeficientes máximos vigentes del IIVTNU, los dos métodos de cálculo desde la "
        "sentencia del Constitucional, plazos en venta, herencia y donación, y cuándo "
        "no se paga por vender con pérdidas. Con ejemplos numéricos.",
    ),
    "tasa-basuras": (
        "Tasa de basuras 2026: cuánto se paga y quién la paga",
        "Cuánto cuesta la tasa de residuos en 2026, por qué ha subido con la Ley "
        "7/2022, quién la paga en un alquiler y cómo reclamar un recibo incorrecto. "
        "Importes por municipio y plazos de pago.",
    ),
    "bonificaciones": (
        "Bonificaciones del IBI 2026: hasta 90% y cómo pedirlas",
        "Familia numerosa hasta el 90%, placas solares hasta el 50%, VPO el 50% y "
        "domiciliación hasta el 5%. Qué bonificaciones son obligatorias, cuáles "
        "dependen de tu ordenanza y cómo solicitarlas antes del 31 de marzo.",
    ),
    "calculadora-ibi": (
        "Calculadora de IBI 2026: calcula tu recibo en un minuto",
        "Calcula el IBI de tu vivienda con el valor catastral de tu recibo o de tu "
        "referencia catastral. Aplica el tipo oficial de tu municipio y las "
        "bonificaciones. 134 municipios con datos del Ministerio de Hacienda.",
    ),
}


def sustituye_metadatos(dry: bool) -> int:
    cambios = 0
    for pagina, (title, description) in METADATOS.items():
        path = ROOT / pagina / "index.html"
        if not path.exists():
            print(f"  [aviso] no existe {pagina}")
            continue
        texto = path.read_text(encoding="utf-8")
        original = texto
        texto = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", texto, count=1)
        texto = re.sub(
            r'(<meta name="description" content=")[^"]*(")',
            lambda mo: mo.group(1) + description + mo.group(2),
            texto,
            count=1,
        )
        # og:title y og:description, si existen
        texto = re.sub(
            r'(<meta property="og:title" content=")[^"]*(")',
            lambda mo: mo.group(1) + title + mo.group(2),
            texto,
            count=1,
        )
        texto = re.sub(
            r'(<meta property="og:description" content=")[^"]*(")',
            lambda mo: mo.group(1) + description + mo.group(2),
            texto,
            count=1,
        )
        # dato obsoleto
        texto = texto.replace("26 municipios", "134 municipios")
        if texto != original:
            if not dry:
                path.write_text(texto, encoding="utf-8")
            cambios += 1
            print(f"  {pagina}: título y descripción actualizados ({len(title)} caracteres)")
    return cambios


def tabla_coeficientes() -> str:
    datos = json.loads(COEFS.read_text(encoding="utf-8"))
    filas = "\n            ".join(
        f"<tr><td>{tramo}</td><td class=\"v\">{coef}</td></tr>" for tramo, coef in datos["coeficientes"]
    )
    return f"""    <h2 id="coeficientes">Coeficientes de la plusvalía municipal vigentes</h2>
    <p>Si eliges el <strong>método objetivo</strong>, la base imponible sale de multiplicar el <em>valor catastral del suelo</em> por el coeficiente que corresponda a los años que has tenido el inmueble. Estos son los <strong>coeficientes máximos</strong> que fija el {datos['articulo']}: tu ayuntamiento puede aprobar los suyos, pero <strong>no puede superarlos</strong>.</p>
    <table class="dt">
      <thead><tr><th>Período de generación</th><th>Coeficiente máximo</th></tr></thead>
      <tbody>
            {filas}
      </tbody>
    </table>
    <p><strong>Ejemplo con los máximos legales.</strong> Vendes una vivienda que compraste hace 7 años. El valor catastral del suelo en la fecha de la venta es de 30.000 €. La base imponible por el método objetivo sería 30.000 € × 0,20 = <strong>6.000 €</strong>. Si tu ayuntamiento aplica el tipo máximo del 30% que permite el artículo 108 del mismo texto legal, la cuota sería 6.000 € × 30% = <strong>1.800 €</strong>. Con un tipo del 20%, serían 1.200 €.</p>
    <div class="note"><strong>⚖️ Compara siempre con el método real.</strong> Si la diferencia entre el precio de compra y el de venta, en la parte proporcional del suelo, es menor que esa base objetiva, puedes tributar por la real y pagarás menos. El ayuntamiento no hace el cálculo por ti: tienes que aportar las dos escrituras y pedirlo.</div>
    <p style="font-size:.85rem;color:var(--mid)">Fuente: <a href="{datos['fuente']}" target="_blank" rel="nofollow noopener">texto consolidado del TRLRHL en el BOE</a>, {datos['articulo']}. {datos['nota']} Los coeficientes se actualizan por norma estatal, normalmente en la Ley de Presupuestos.</p>

"""


def inserta_coeficientes(dry: bool) -> bool:
    path = ROOT / "plusvalia" / "index.html"
    texto = path.read_text(encoding="utf-8")
    if 'id="coeficientes"' in texto:
        print("  /plusvalia/: la tabla de coeficientes ya estaba")
        return False
    marca = re.search(r'[ \t]*<h2(?: class="sec")? id="plazos">', texto)
    ancla = marca.start() if marca else -1
    if ancla == -1:
        print("  [aviso] no encuentro dónde insertar la tabla en /plusvalia/")
        return False
    texto = texto[:ancla] + tabla_coeficientes() + texto[ancla:]
    # enlace en el índice de la página, si existe
    if not dry:
        path.write_text(texto, encoding="utf-8")
    print(f"  /plusvalia/: tabla oficial de coeficientes insertada "
          f"({len(json.loads(COEFS.read_text(encoding='utf-8'))['coeficientes'])} tramos)")
    return True


def seccion_tomelloso() -> str:
    datos = json.loads(COEFS.read_text(encoding="utf-8"))
    return """      <section class="sec">
        <h2>Coeficientes y tipo de gravamen de la plusvalía en Tomelloso: dónde está el dato exacto</h2>
        <p>Es la duda que más nos llega sobre este municipio, así que vamos al grano: los valores concretos que aplica Tomelloso están en su <strong>ordenanza fiscal del IIVTNU</strong>, cuyo texto íntegro se publica en el <strong>Boletín Oficial de la Provincia de Ciudad Real</strong>. Nosotros no reproducimos aquí unos coeficientes que no hayamos podido contrastar, pero sí podemos decirte los límites que la ley impone a cualquier ayuntamiento y cómo se hace el cálculo.</p>
        <h3>Los dos topes legales que no puede superar ninguna ordenanza</h3>
        <ul>
          <li><strong>Tipo de gravamen: 30% como máximo</strong> (artículo 108 del texto refundido de la Ley Reguladora de las Haciendas Locales). Cuando encuentras la frase «el tipo de gravamen del impuesto será del 30%» en una ordenanza, significa que ese ayuntamiento aplica el techo legal.</li>
          <li><strong>Coeficientes por años de tenencia</strong>: el artículo 107.4 fija un máximo para cada tramo, desde 0,15 para menos de un año hasta 0,40 a partir de veinte años. Los tienes todos, con la fuente, en nuestra <a href="../../../plusvalia/#coeficientes" style="color:var(--accent);font-weight:600">tabla de coeficientes vigentes</a>.</li>
        </ul>
        <h3>Cómo calcular tu plusvalía en Tomelloso paso a paso</h3>
        <ol>
          <li>Localiza el <strong>valor catastral del suelo</strong> en tu recibo del IBI o en la Sede del Catastro. Ojo: es el valor del suelo, no el valor catastral total.</li>
          <li>Multiplícalo por el coeficiente de los años completos que has tenido el inmueble.</li>
          <li>Aplica a ese resultado el tipo de gravamen de la ordenanza.</li>
          <li>Calcula también el <strong>método real</strong>: diferencia entre precio de venta y de compra, multiplicada por el porcentaje que el suelo representa sobre el valor catastral total. Se tributa por la base menor de las dos.</li>
        </ol>
        <p><strong>Ejemplo aplicando los topes legales</strong> (si Tomelloso aprueba valores menores, pagarás menos): vivienda comprada hace 7 años, valor catastral del suelo 25.000 €. Base objetiva: 25.000 € × 0,20 = 5.000 €. Con el tipo máximo del 30%, la cuota serían <strong>1.500 €</strong>.</p>
        <div class="note"><strong>📄 Dónde conseguir el texto oficial.</strong> Pide la ordenanza fiscal del IIVTNU en el <a href="https://www.tomelloso.es" target="_blank" rel="nofollow noopener">Ayuntamiento de Tomelloso</a> o búscala en el Boletín Oficial de la Provincia de Ciudad Real, que publica el texto íntegro cuando se aprueba o se modifica. Es el único documento con valor jurídico, y prevalece sobre cualquier resumen, incluido el nuestro.</div>
        <p>Recuerda los <strong>plazos</strong>: 30 días hábiles desde la escritura en compraventas y donaciones, y 6 meses desde el fallecimiento en herencias, prorrogables a un año si lo solicitas dentro de los seis primeros meses. Presentar fuera de plazo añade recargos aunque la cuota sea cero.</p>
      </section>
"""


def inserta_tomelloso(dry: bool) -> bool:
    path = ROOT / "castilla-la-mancha" / "ciudad-real" / "tomelloso" / "index.html"
    texto = path.read_text(encoding="utf-8")
    if "dónde está el dato exacto" in texto:
        print("  Tomelloso: la sección ya estaba")
        return False
    ancla = re.search(r'      <section class="sec">\s*<h2>Bonificaciones del IBI en Tomelloso', texto)
    if not ancla:
        print("  [aviso] no encuentro dónde insertar la sección en Tomelloso")
        return False
    texto = texto[: ancla.start()] + seccion_tomelloso() + texto[ancla.start():]
    if not dry:
        path.write_text(texto, encoding="utf-8")
    print("  Tomelloso: sección de coeficientes y tipo de gravamen insertada")
    return True


def enlaza_coeficientes_en_fichas(dry: bool) -> int:
    """Cada ficha enlaza la tabla canónica en lugar de repetirla."""
    n = 0
    for path in sorted(ROOT.glob("*/*/*/index.html")):
        texto = path.read_text(encoding="utf-8")
        if "plusvalia/#coeficientes" in texto or 'http-equiv="refresh"' in texto:
            continue
        nuevo, k = re.subn(
            r'(<a href="((?:\.\./)+)plusvalia/" style="color:var\(--accent\);font-weight:600">)calculadora →</a>',
            lambda mo: f'<a href="{mo.group(2)}plusvalia/#coeficientes" style="color:var(--accent);font-weight:600">'
            "coeficientes máximos vigentes →</a>",
            texto,
            count=1,
        )
        if k:
            if not dry:
                path.write_text(nuevo, encoding="utf-8")
            n += 1
    print(f"  fichas que enlazan la tabla canónica de coeficientes: {n}")
    return n


SECCION_RECARGOS = """    <h2 id="recargos">Qué recargo se aplica si pagas el IBI fuera de plazo</h2>
    <p>Pasado el período voluntario que fija tu ayuntamiento, la deuda entra en vía ejecutiva y el recargo depende de lo rápido que reacciones. Lo regula el artículo 28 de la <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2003-23186" target="_blank" rel="nofollow noopener">Ley General Tributaria</a>:</p>
    <table class="dt">
      <thead><tr><th>Momento en que pagas</th><th>Recargo</th><th>Intereses de demora</th></tr></thead>
      <tbody>
        <tr><td>Antes de que te notifiquen la providencia de apremio</td><td class="v">5%</td><td>No</td></tr>
        <tr><td>Después de la notificación, dentro del plazo que concede</td><td class="v">10%</td><td>No</td></tr>
        <tr><td>Fuera de ese plazo</td><td class="v">20%</td><td>Sí, se suman</td></tr>
      </tbody>
    </table>
    <p>Sobre un recibo de 300 €, la diferencia entre reaccionar en la primera semana o dejarlo correr es de 15 € frente a 60 € más intereses. Si no puedes pagarlo de golpe, pide el <strong>fraccionamiento antes de que acabe el período voluntario</strong>: una vez en apremio, el recargo ya está devengado.</p>
    <div class="note"><strong>💡 Domicilia el recibo.</strong> Además de evitar recargos por despiste, muchas ordenanzas premian la domiciliación con una bonificación de hasta el <strong>5%</strong> de la cuota, al amparo del artículo 9.1 del <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214" target="_blank" rel="nofollow noopener">TRLRHL</a>. Hay que comunicar el IBAN antes de que se abra el período de pago.</div>

"""


def inserta_recargos(dry: bool) -> bool:
    """Explicacion unica de los recargos, que las 134 fichas enlazan en lugar de repetir."""
    path = ROOT / "ibi-2026" / "index.html"
    texto = path.read_text(encoding="utf-8")
    if 'id="recargos"' in texto:
        print("  /ibi-2026/: la sección de recargos ya estaba")
        return False
    marca = re.search(r'[ \t]*<h2(?: class="sec")? id="fraccionar">', texto)
    if not marca:
        print("  [aviso] no encuentro dónde insertar los recargos en /ibi-2026/")
        return False
    texto = texto[: marca.start()] + SECCION_RECARGOS + texto[marca.start():]
    if not dry:
        path.write_text(texto, encoding="utf-8")
    print("  /ibi-2026/: sección de recargos por pago fuera de plazo insertada")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("Metadatos de las guías nacionales:")
    sustituye_metadatos(args.dry_run)
    print("\nTabla oficial de coeficientes:")
    inserta_coeficientes(args.dry_run)
    enlaza_coeficientes_en_fichas(args.dry_run)
    print("\nRecargos por pago fuera de plazo:")
    inserta_recargos(args.dry_run)
    print("\nTomelloso:")
    inserta_tomelloso(args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
