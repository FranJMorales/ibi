#!/usr/bin/env python3
"""Elimina de las fichas municipales el texto boilerplate que se repetia literalmente
en decenas o cientos de paginas, y lo sustituye por enlaces a la guia canonica
correspondiente (/ibi-2026/, /plusvalia/, /tasa-basuras/, /bonificaciones/).

Motivo: Google AdSense rechazaba el sitio por "contenido de poco valor". La causa
principal medida sobre el propio repositorio era que 134 fichas municipales
compartian entre el 40% y el 68% de su texto literal (parrafos identicos en
134/134, 75/134 y 59/134 paginas). La informacion generica se consolida ahora en
una unica pagina pilar (mejor para SEO: una sola URL canonica por intencion de
busqueda) y cada ficha conserva solo lo que es propio de su municipio.

No se inventa ni se anade ningun dato nuevo: solo se elimina duplicado y se
enlaza a la guia que ya explica ese punto.

Uso:  python3 scripts/dedupe_municipal_boilerplate.py [--dry-run]
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = 'style="color:var(--accent);font-weight:600"'


def municipality(html: str) -> str:
    m = re.search(r'<div class="bc">.*?<strong>([^<]+)</strong>', html, re.S)
    return m.group(1).strip() if m else ""


def sede_url(html: str) -> str:
    m = re.search(
        r'<strong>Sede electrónica del Ayuntamiento:</strong>\s*<a href="([^"]+)"', html
    )
    if m:
        return m.group(1)
    m = re.search(r'href="(https://[a-z0-9\-]+\.sedelectronica\.es[^"]*)"', html)
    return m.group(1) if m else ""


def ccaa_slug(path: Path) -> str:
    return path.relative_to(ROOT).parts[0]


def build_rules(html: str, muni: str, sede: str, ccaa: str, prefix: str):
    """Devuelve la lista (nombre, patron, reemplazo) de sustituciones."""
    sede_link = (
        f'<a href="{sede}" target="_blank" rel="nofollow noopener">sede electrónica'
        f' de {muni}</a>'
        if sede
        else "sede electrónica municipal"
    )

    rules = []

    # 1. Nota "¿Cómo se calcula?" — 134/134 paginas con el mismo texto generico.
    rules.append((
        "nota-formula",
        re.compile(
            r'<div class="note"><strong>💡 ¿Cómo se calcula\?</strong> '
            r'<em>Cuota = Valor catastral × ([\d.,]+)%</em>\. El valor catastral '
            r'aparece en tu recibo del IBI o en la <a href="https://www\.sedecatastro\.gob\.es"'
            r'[^>]*>sede del Catastro</a>\. Las bonificaciones se restan después\.</div>'
        ),
        lambda m: (
            f'<div class="note"><strong>💡 Fórmula aplicable en {muni}:</strong> '
            f'<em>Cuota íntegra = Valor catastral × {m.group(1)}%</em>, menos las '
            f'bonificaciones reconocidas. '
            f'<a href="{prefix}calculadora-ibi/" {A}>Calcular con bonificaciones →</a></div>'
        ),
    ))

    # 2. Tutorial del Catastro identico en 59 paginas -> guia canonica en /ibi-2026/#catastro
    rules.append((
        "tutorial-catastro",
        re.compile(
            r'<h3>¿Cómo consultar tu valor catastral en la Sede del Catastro\?</h3>\s*'
            r'<p>Para conocer tu valor catastral exacto.*?</p>'
        ),
        lambda m: (
            f'<p><a href="{prefix}ibi-2026/#catastro" {A}>→ Cómo consultar tu valor '
            f'catastral en la Sede del Catastro, paso a paso</a></p>'
        ),
    ))

    # 3. Frase generica sobre el valor catastral repetida en 75 paginas.
    rules.append((
        "frase-cuota-depende",
        re.compile(
            r'\s*La cuota depende del valor catastral del inmueble, que puedes consultar '
            r'en tu recibo anterior o en la <a href="https://www\.sedecatastro\.gob\.es"'
            r'[^>]*>Sede del Catastro</a>\.'
        ),
        lambda m: "",
    ))

    # 4. Parrafo generico de basuras (locales + biorresiduos) repetido en 75 paginas.
    rules.append((
        "basuras-generico",
        re.compile(
            r'\s*Los locales comerciales y naves industriales pagan tarifas diferenciadas '
            r'según superficie y actividad\. El servicio de recogida incluye desde '
            r'2024/2025 contenedor específico de fracción orgánica \(biorresiduos\) en '
            r'aplicación de la Ley 7/2022\.'
        ),
        lambda m: (
            f' <a href="{prefix}tasa-basuras/" {A}>Ver tarifas por uso y superficie →</a>'
        ),
    ))

    # 5. Parrafo generico "la tasa se ha incrementado..." repetido en 59 paginas.
    #    Se elimina la parte generica y se conserva la frase propia del municipio.
    rules.append((
        "basuras-ley7-2022",
        re.compile(
            r'<p>La tasa de basuras se ha incrementado en la mayoría de municipios '
            r'españoles en 2025–2026 por la <strong>Ley 7/2022 de Residuos y Suelos '
            r'Contaminados</strong>, que obliga a los ayuntamientos a cubrir el coste '
            r'íntegro del servicio con las tasas cobradas\.\s*'
        ),
        lambda m: (
            f'<p>La <a href="{prefix}tasa-basuras/" {A}>Ley 7/2022 de Residuos</a> obliga '
            f'a que la tasa cubra el coste íntegro del servicio. '
        ),
    ))

    # 5b. Parrafo generico de "¿Cuándo NO se paga plusvalía?", identico en 59 paginas.
    rules.append((
        "plusvalia-perdidas",
        re.compile(
            r'<p>Si el precio de transmisión es inferior al de adquisición \(venta con '
            r'pérdidas\), no existe incremento de valor y no se devenga el impuesto\. '
            r'Debes aportar ambas escrituras \(compra y venta\) al Ayuntamiento para '
            r'acreditar la ausencia de plusvalía\. Desde la sentencia del Tribunal '
            r'Constitucional de 2021 \(STC 182/2021\) y el Real Decreto-ley 26/2021, '
            r'puedes optar por el método de cálculo \(real vs\. objetivo\) que resulte '
            r'más favorable\.</p>'
        ),
        lambda m: (
            f'<p>Si vendes con pérdidas no se devenga el impuesto: se acredita aportando '
            f'ambas escrituras al Ayuntamiento de {muni}. '
            f'<a href="{prefix}plusvalia/" {A}>Supuestos de no sujeción y exenciones →</a></p>'
        ),
    ))

    # 6. Parrafo del sujeto pasivo en alquiler, identico en 59 paginas.
    rules.append((
        "alquiler-sujeto-pasivo",
        re.compile(
            r'\s*<p>En caso de alquiler, el sujeto pasivo es legalmente el propietario '
            r'del inmueble, aunque el contrato de arrendamiento puede trasladar el pago '
            r'al inquilino si se pacta expresamente por escrito en una cláusula '
            r'específica\.</p>'
        ),
        lambda m: "",
    ))

    # 7. Bloque de plazos de plusvalia, identico en 134 paginas.
    rules.append((
        "plazos-plusvalia",
        re.compile(
            r'<h3>Plazos legales para declarar(?: la plusvalía)?</h3>\s*<ul>\s*'
            r'<li><strong>Compraventa:</strong>.*?</ul>',
            re.S,
        ),
        lambda m: (
            f'<p><strong>Plazos de declaración:</strong> 30 días hábiles en compraventa '
            f'y donación; 6 meses en herencia, prorrogables a 12 a solicitud ante el '
            f'Ayuntamiento de {muni}. '
            f'<a href="{prefix}plusvalia/" {A}>Modelos, cálculo y ejemplos →</a></p>'
        ),
    ))

    # 8. Nota de plusvalia: se conserva el enlace a la sede y se corta el texto repetido.
    rules.append((
        "nota-plusvalia",
        re.compile(
            r'<div class="note"><strong>⚖️ Elige el método más favorable[^<]*</strong> '
            r'Consulta la <a href="([^"]+)"[^>]*>sede electrónica del Ayuntamiento</a> '
            r'para conocer los coeficientes municipales vigentes y simular ambos métodos '
            r'antes de presentar la autoliquidación\.</div>'
        ),
        lambda m: (
            f'<div class="note"><strong>⚖️ Compara los dos métodos antes de '
            f'autoliquidar.</strong> Coeficientes vigentes en la '
            f'<a href="{m.group(1)}" target="_blank" rel="nofollow noopener">sede '
            f'electrónica de {muni}</a> · '
            f'<a href="{prefix}plusvalia/" {A}>calculadora →</a></div>'
        ),
    ))

    # 9. Filas de bonificaciones de alcance general (identicas en las 134 fichas y no
    #    verificadas contra la ordenanza local): se retiran de la tabla municipal y se
    #    remiten a la guia estatal.
    for name, pattern in (
        ("fila-sepa", r'\s*<tr><td>Domiciliación SEPA</td>.*?</tr>'),
        ("fila-vpo", r'\s*<tr><td>VPO \(nueva construcción\)</td>.*?</tr>'),
        ("fila-rehab", r'\s*<tr><td>Obras de rehabilitación energética</td>.*?</tr>'),
    ):
        rules.append((name, re.compile(pattern, re.S), lambda m: ""))

    # 10. Nota de plazo de solicitud, identica en 134 paginas.
    rules.append((
        "nota-bonificaciones",
        re.compile(
            r'<div class="note"><strong>📅 Plazo de solicitud:</strong> antes del 31 de '
            r'marzo del ejercicio fiscal, salvo que la ordenanza establezca otra fecha\. '
            r'Las bonificaciones no se aplican de oficio: debes solicitarlas activamente '
            r'en la <a href="([^"]+)"[^>]*>sede electrónica</a> o en las oficinas de '
            r'recaudación[^<]*\.</div>'
        ),
        lambda m: (
            f'<div class="note"><strong>📅 Solicitud:</strong> a instancia del interesado, '
            f'antes del 31 de marzo, en la <a href="{m.group(1)}" target="_blank" '
            f'rel="nofollow noopener">sede electrónica de {muni}</a>. '
            f'<a href="{prefix}bonificaciones/" {A}>Requisitos, documentación y '
            f'bonificaciones de alcance estatal (VPO, rehabilitación, SEPA) →</a></div>'
        ),
    ))

    # 11. Introduccion de la comparativa, identica en 134 paginas.
    rules.append((
        "intro-comparativa",
        re.compile(
            r'<p>El siguiente gráfico compara el tipo de IBI urbano de [^<]*? con el '
            r'(?:de otros|del resto de) municipios de ([^<]*?) incluidos en nuestra guía\. Un tipo más alto '
            r'no siempre implica cuotas más altas: depende del valor catastral de cada '
            r'inmueble\.(?: Consulta la guía comparativa completa en la '
            r'<a href="[^"]*">página de la comunidad autónoma</a>\.)?</p>'
        ),
        lambda m: (
            f'<p>Tipo de IBI urbano de {muni} frente al resto de municipios de '
            f'{m.group(1)} recogidos en la guía '
            f'(<a href="{prefix}{ccaa}/" {A}>tabla comparativa completa →</a>).</p>'
        ),
    ))

    # 12. Enlace de relleno a la Agencia Tributaria (identico en 75 fichas, sin relacion
    #     con la tributacion local).
    rules.append((
        "fuente-aeat",
        re.compile(
            r'\s*<li><strong>Agencia Tributaria:</strong>.*?</li>',
            re.S,
        ),
        lambda m: "",
    ))

    # 13. Aviso final, identico en 134 paginas: se compacta conservando la fuente.
    rules.append((
        "nota-aviso",
        re.compile(
            r'<div class="note"><strong>⚠️ Aviso:</strong> Los datos de esta guía se basan '
            r'en la ordenanza fiscal publicada en el ([^.]+?)\. Confirma siempre los '
            r'importes y plazos vigentes en la <a href="[^"]+"[^>]*>sede electrónica del '
            r'Ayuntamiento de [^<]*</a> antes de pagar, reclamar o solicitar una '
            r'bonificación\.</div>'
        ),
        lambda m: (
            f'<div class="note"><strong>⚠️ Verifica antes de pagar:</strong> datos '
            f'tomados de {m.group(1)}. Confirma importes y plazos en la {sede_link}.</div>'
        ),
    ))

    return rules


def process(path: Path, stats: Counter, dry_run: bool) -> bool:
    html = path.read_text(encoding="utf-8")
    muni = municipality(html)
    if not muni:
        print(f"  [aviso] no se detecta municipio: {path.relative_to(ROOT)}")
        return False

    prefix = "../" * (len(path.relative_to(ROOT).parts) - 1)
    rules = build_rules(html, muni, sede_url(html), ccaa_slug(path), prefix)

    original = html
    for name, pattern, repl in rules:
        html, n = pattern.subn(repl, html)
        if n:
            stats[name] += n

    if html == original:
        return False
    if not dry_run:
        path.write_text(html, encoding="utf-8")
    return True


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    pages = sorted(p for p in ROOT.glob("*/*/*/index.html") if ".git" not in p.parts)
    stats: Counter = Counter()
    changed = sum(1 for p in pages if process(p, stats, dry_run))

    print(f"Fichas municipales procesadas: {len(pages)} · modificadas: {changed}")
    for name, n in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
