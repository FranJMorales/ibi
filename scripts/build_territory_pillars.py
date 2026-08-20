#!/usr/bin/env python3
"""Genera los ARTICULOS PILAR TERRITORIALES que sustituyen a las fichas municipales.

Arquitectura resultante:

    /                        home
    /ibi-2026/ ...           8 guias pilar nacionales (tema)
    /comunidades/            hub de segundo nivel
    /{ccaa}/                 pilar de comunidad autonoma
    /{ccaa}/{provincia}/     pilar de provincia, SOLO si la provincia alcanza el
                             umbral PROVINCE_PILLAR_THRESHOLD de municipios cubiertos

Cada pilar contiene: introduccion con datos agregados propios del territorio,
tabla maestra comparativa de todos sus municipios, grafico comparativo, indice de
saltos, una seccion con ancla por municipio (solo con el texto que es unico de ese
municipio) y una FAQ construida a partir de los datos reales del territorio.

Las URLs de municipio absorbidas se convierten en paginas de redireccion hacia
/{territorio}/#{slug} (GitHub Pages no soporta 301, ver --redirects) y salen del
sitemap.

Uso:
    python3 scripts/build_territory_pillars.py --list
    python3 scripts/build_territory_pillars.py --only murcia [--dry-run]
    python3 scripts/build_territory_pillars.py --all
"""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"
TODAY = date.today().isoformat()

# Una provincia obtiene pilar propio a partir de este numero de municipios cubiertos.
# Por debajo, sus municipios se integran en el pilar de la comunidad autonoma:
# una URL solo debe existir si tiene masa critica de datos propios.
PROVINCE_PILLAR_THRESHOLD = 6

CCAA_NAMES = {
    "aragon": "Aragón",
    "asturias": "Asturias",
    "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha",
    "castilla-y-leon": "Castilla y León",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "la-rioja": "La Rioja",
    "murcia": "Murcia",
}

# Comunidades uniprovinciales: el pilar de comunidad ES el de provincia.
UNIPROVINCIAL = {"asturias", "cantabria", "la-rioja", "murcia"}


# ─────────────────────────────── utilidades ────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def euros(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + " €"


def pct(value: float) -> str:
    """Tipo tal y como lo publica Hacienda, sin ceros de relleno.

    Las fichas y el comparador muestran 0,984%; el pilar mostraba 0,98%. Misma
    cifra con dos formatos distintos parece un error de datos.
    """
    return f"{round(value, 4):g}".replace(".", ",") + "%"


def pct2(value: float) -> str:
    """Para medias y medianas, donde cuatro decimales solo hacen ruido."""
    return f"{value:.2f}".replace(".", ",") + "%"


# ─────────────────────────── extraccion de datos ───────────────────────────

QUICK_LABELS = {
    "IBI urbano": "ibi_urbano",
    "IBI rústico": "ibi_rustico",
    "Valores catastrales": "ano_valores",
    "Bonif. familia numerosa": "boni_familia",
    "Bonif. energía solar": "boni_solar",
}


def parse_municipality(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    name = re.search(r'<div class="bc">.*?<strong>([^<]+)</strong>', raw, re.S)
    if not name:
        return None

    data: dict = {
        "path": path,
        "ccaa": path.relative_to(ROOT).parts[0],
        "provincia_slug": path.relative_to(ROOT).parts[1],
        "slug": path.relative_to(ROOT).parts[2],
        "nombre": name.group(1).strip(),
        "url_antigua": "/" + "/".join(path.relative_to(ROOT).parts[:-1]) + "/",
    }

    lead = re.search(r'<p class="lead">(.*?)</p>', raw, re.S)
    data["lead"] = re.sub(r"\s+", " ", lead.group(1)).strip() if lead else ""

    pobl = re.search(r"Población: ([\d.]+) hab\.", raw)
    data["poblacion"] = int(pobl.group(1).replace(".", "")) if pobl else None

    quick = re.search(r'<ul class="quick">(.*?)</ul>', raw, re.S)
    for label, key in QUICK_LABELS.items():
        data[key] = ""
    if quick:
        for item in re.findall(r"<li>(.*?)</li>", quick.group(1), re.S):
            label = re.search(r"<strong>([^:]+):</strong>", item)
            if not label:
                continue
            key = QUICK_LABELS.get(label.group(1).strip())
            if key:
                data[key] = strip_tags(re.sub(r"<strong>.*?</strong>", "", item, flags=re.S))

    data["tipo_urbano"] = _to_float(data["ibi_urbano"])
    data["tipo_rustico"] = _to_float(data["ibi_rustico"])
    # El importe de basuras y el periodo de pago ya no se publican: no tenian
    # fuente (ver scripts/retirar_datos_sin_fuente.py).
    data["basuras"] = ""
    data["basuras_eur"] = None
    data["periodo"] = ""
    ano = re.search(r"\b(19|20)\d{2}\b", data.get("ano_valores") or "")
    data["oficial_ano_valores_catastrales"] = ano.group(0) if ano else ""

    sede = re.search(
        r"<strong>Sede electrónica del Ayuntamiento:</strong>\s*<a href=\"([^\"]+)\"", raw
    )
    data["sede"] = sede.group(1) if sede else ""

    consejo = re.search(r"<h2>Consejo práctico[^<]*</h2>\s*<p>(.*?)</p>", raw, re.S)
    data["consejo"] = re.sub(r"\s+", " ", consejo.group(1)).strip() if consejo else ""

    provincia = re.search(r'<p class="meta"><strong>([^·<]+)·\s*([^<]+)</strong>', raw)
    data["provincia"] = provincia.group(2).strip() if provincia else ""

    # Parrafos candidatos: se filtran despues quedandose solo con los que son
    # unicos en todo el sitio (los repetidos ya viven en las guias pilar).
    main = re.search(r"<main>(.*?)</main>", raw, re.S)
    body = main.group(1) if main else raw
    body = re.sub(r'(?s)<section class="sec">\s*<h2>Otros municipios.*?</section>', "", body)
    body = re.sub(r'(?s)<div class="chart-container">.*?</div>\s*</div>', "", body)
    paragraphs = []
    for frag in re.findall(r"<p>(.*?)</p>", body, re.S):
        text = re.sub(r"\s+", " ", frag).strip()
        plain = strip_tags(text)
        if len(plain) < 160 or plain.startswith("→"):
            continue
        paragraphs.append(text)
    data["parrafos"] = paragraphs
    return data


def _to_float(value: str) -> float | None:
    m = re.search(r"([\d]+[.,]?[\d]*)", value or "")
    return float(m.group(1).replace(",", ".")) if m else None


# ────────────────────── agrupacion en pilares territoriales ─────────────────

def assign_territories(municipalities: list[dict],
                       solo_comunidades: bool = False) -> dict[str, dict]:
    """Reparte los municipios en pilares territoriales.

    Con `solo_comunidades` no se crean pilares de provincia: cada comunidad
    autonoma tiene un unico articulo con TODOS sus municipios. Es la opcion que
    usamos en produccion, porque un pilar de provincia repetiria la misma tabla y
    las mismas secciones que el de su comunidad para un subconjunto de municipios,
    y eso son dos URLs compitiendo con contenido casi identico.
    """
    by_province: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for m in municipalities:
        by_province[(m["ccaa"], m["provincia_slug"])].append(m)

    territories: dict[str, dict] = {}
    for (ccaa, prov), items in by_province.items():
        own_pillar = (not solo_comunidades and ccaa not in UNIPROVINCIAL
                      and len(items) >= PROVINCE_PILLAR_THRESHOLD)
        if own_pillar:
            key = f"{ccaa}/{prov}"
            territories.setdefault(key, {
                "key": key,
                "nivel": "provincia",
                "ccaa": ccaa,
                "nombre": items[0]["provincia"] or prov.replace("-", " ").title(),
                "municipios": [],
            })["municipios"].extend(items)
        else:
            key = ccaa
            territories.setdefault(key, {
                "key": key,
                "nivel": "comunidad",
                "ccaa": ccaa,
                "nombre": CCAA_NAMES.get(ccaa, ccaa),
                "municipios": [],
            })["municipios"].extend(items)

    for t in territories.values():
        t["municipios"].sort(key=lambda m: -(m["poblacion"] or 0))
    return territories


# ──────────────────────────── plantilla comun ──────────────────────────────

# Menu principal agrupado por intencion, no por tipo de contenido.
#   Mi municipio  -> el 76,6% de los clics llega buscando un municipio concreto
#   Impuestos     -> aqui caben las guias nuevas sin volver a tocar 162 cabeceras
#   Comparativas  -> /analisis/, con un rotulo que dice que hay dentro
#   Metodologia   -> sube del pie al header: es la pagina que sostiene la confianza
#   Calcular      -> la unica herramienta interactiva, como boton y no como enlace
#
# Los desplegables son <details>/<summary> nativos: funcionan con teclado y en
# tactil, y no anaden una sola linea de JavaScript.
NAV_GRUPOS = [
    ("municipio", "Mi municipio", [
        ("municipios/", "Buscar entre los 134 municipios"),
        ("comunidades/", "Por comunidad autónoma"),
    ]),
    ("impuestos", "Impuestos", [
        ("ibi-2026/", "IBI"),
        ("tasa-basuras/", "Tasa de basuras"),
        ("plusvalia/", "Plusvalía municipal"),
        ("bonificaciones/", "Bonificaciones del IBI"),
        ("impuesto-circulacion/", "Impuesto de circulación"),
        ("valor-catastral/", "Valor catastral"),
    ]),
]
NAV_SUELTOS = [("analisis/", "Comparativas"), ("metodologia/", "Metodología")]
NAV_CTA = ("calculadora-ibi/", "Calcular mi IBI")


def nav_block(prefix: str, activo: str = "") -> str:
    """Cabecera comun. `activo` es la ruta de la pagina actual, p. ej. "ibi-2026/"."""
    partes = ['    <nav class="mainnav" aria-label="Navegación principal">']
    for gid, titulo, enlaces in NAV_GRUPOS:
        dentro = any(activo == destino for destino, _ in enlaces)
        abierto = ' class="nav-group on"' if dentro else ' class="nav-group"'
        partes.append(f'      <details{abierto}>')
        partes.append(f'        <summary>{titulo}</summary>')
        partes.append('        <div class="nav-menu">')
        for destino, etiqueta in enlaces:
            marca = ' class="on" aria-current="page"' if activo == destino else ""
            partes.append(f'          <a href="{prefix}{destino}"{marca}>{etiqueta}</a>')
        partes.append("        </div>")
        partes.append("      </details>")
    for destino, etiqueta in NAV_SUELTOS:
        marca = ' class="on" aria-current="page"' if activo == destino else ""
        partes.append(f'      <a href="{prefix}{destino}"{marca}>{etiqueta}</a>')
    destino, etiqueta = NAV_CTA
    marca = ' aria-current="page"' if activo == destino else ""
    partes.append(f'      <a href="{prefix}{destino}" class="nav-cta"{marca}>{etiqueta}</a>')
    partes.append("    </nav>")
    return "\n".join(partes)


def head_block(title: str, description: str, canonical: str, prefix: str) -> str:
    # La entrada activa se deduce del canonical, para que los generadores no
    # dependan de que despues se pase rebuild_header.py a marcarla.
    activo = canonical.replace(f"{SITE}/", "")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{prefix}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{prefix}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{prefix}apple-touch-icon.png">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <!-- Google Consent Mode v2: estado por defecto denegado hasta que el usuario acepte (RGPD) -->
  <script id="tm-consent-default">
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    (function () {{
      var m = document.cookie.match('(^|;)\\\\s*tm_cookie_consent\\\\s*=\\\\s*([^;]+)');
      var state = (m ? m.pop() : '') === 'accepted' ? 'granted' : 'denied';
      gtag('consent', 'default', {{
        ad_storage: state,
        ad_user_data: state,
        ad_personalization: state,
        analytics_storage: state,
        wait_for_update: 500
      }});
    }})();
  </script>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4975903304841229" crossorigin="anonymous"></script>
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="{prefix}styles.css">
</head>
<body>
<header>
  <div class="hi">
    <a href="{prefix}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
{nav_block(prefix, activo)}
  </div>
</header>
"""


def footer_block(prefix: str) -> str:
    link = 'style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;"'
    col = 'style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;"'
    return f"""<footer>
  <div class="ft-grid" style="max-width:1100px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px;padding:40px 24px 24px;">
    <div>
      <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:900;color:#fff;margin-bottom:6px;">TasasMunicipales</div>
      <div style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:10px;">Guía de Impuestos Locales · España 2026</div>
      <p style="font-size:.78rem;line-height:1.7;color:rgba(255,255,255,.45);margin:0;">Guía de IBI, tasa de basuras, plusvalía y bonificaciones municipio a municipio, con enlace a la sede electrónica de cada ayuntamiento.</p>
    </div>
    <div>
      <div {col}>Navegación</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{prefix}" {link}>Inicio</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}comunidades/" {link}>Comunidades</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}municipios/" {link}>Municipios</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}calculadora-ibi/" {link}>Calculadora IBI</a></li>
      </ul>
    </div>
    <div>
      <div {col}>Impuestos</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{prefix}ibi-2026/" {link}>IBI 2026</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}tasa-basuras/" {link}>Tasa de Basuras</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}plusvalia/" {link}>Plusvalía Municipal</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}bonificaciones/" {link}>Bonificaciones</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}impuesto-circulacion/" {link}>Impuesto de Circulación</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}valor-catastral/" {link}>Valor Catastral</a></li>
      </ul>
    </div>
    <div>
      <div {col}>Legal</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{prefix}aviso-legal/" rel="nofollow" {link}>Aviso Legal</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}privacidad/" rel="nofollow" {link}>Privacidad</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}cookies/" rel="nofollow" {link}>Cookies</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}contacto/" {link}>Contacto</a></li>
        <li style="margin-bottom:8px;"><a href="{prefix}sobre-nosotros/" {link}>Sobre nosotros</a></li>
      </ul>
    </div>
  </div>
  <div style="max-width:1100px;margin:0 auto;padding:16px 24px 28px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:.72rem;color:rgba(255,255,255,.4);">
    <span>© 2026 TasasMunicipales.info · La información no constituye asesoramiento fiscal.</span>
    <span>Datos del Ministerio de Hacienda, el INE y el BOE. La ordenanza de tu ayuntamiento es la que manda.</span>
  </div>
</footer>
<script src="{prefix}cookie-consent.js" defer></script>
</body>
</html>
"""


# ─────────────────────────── bloques del pilar ─────────────────────────────

REFERENCE_VC = 50000


def _anos_valores(municipios: list[dict]) -> list[tuple[int, dict]]:
    out = []
    for m in municipios:
        ano = m.get("oficial_ano_valores_catastrales")
        if ano and str(ano).isdigit():
            out.append((int(ano), m))
    out.sort(key=lambda par: par[0])
    return out


def stats(municipios: list[dict]) -> dict:
    tipos = [(m["tipo_urbano"], m) for m in municipios if m["tipo_urbano"]]
    tipos.sort(key=lambda pair: pair[0])
    poblacion = sum(m["poblacion"] or 0 for m in municipios)
    anos = _anos_valores(municipios)
    return {
        "n": len(municipios),
        "poblacion": poblacion,
        "min_tipo": tipos[0] if tipos else None,
        "max_tipo": tipos[-1] if tipos else None,
        "media_tipo": sum(t for t, _ in tipos) / len(tipos) if tipos else None,
        # Los valores catastrales sustituyen a la tasa de basuras como segundo eje
        # del resumen: es dato verificado en el Ministerio de Hacienda y explica
        # mejor que el tipo por que dos recibos vecinos no se parecen.
        "anos_valores": anos,
        "ano_antiguo": anos[0] if anos else None,
        "ano_reciente": anos[-1] if anos else None,
    }


def intro_block(t: dict, s: dict, prefix: str) -> str:
    nombre = t["nombre"]
    min_t, min_m = s["min_tipo"]
    max_t, max_m = s["max_tipo"]
    delta = (max_t - min_t) / 100 * REFERENCE_VC

    poblacion_txt = f"{s['poblacion']:,}".replace(",", ".")

    # Segundo párrafo: antigüedad de los valores catastrales, dato verificado en
    # Hacienda que antes ocupaba la tasa de basuras (retirada por falta de fuente).
    if s["ano_antiguo"] and s["ano_reciente"] and len(s["anos_valores"]) >= 3:
        ano_min, m_min = s["ano_antiguo"]
        ano_max, m_max = s["ano_reciente"]
        viejos = [par for par in s["anos_valores"] if par[0] < 2010]
        frase_viejos = (
            f" En {len(viejos)} de los {len(s['anos_valores'])} municipios con dato "
            f"la última valoración es anterior a 2010, así que la base del recibo "
            f"arrastra el mercado inmobiliario de entonces."
            if viejos else
            " Todos los municipios con dato tienen valoraciones de 2010 o posteriores."
        )
        valores_frase = (
            f'    <p>El tipo no lo explica todo: sobre él se aplica el <a href="'
            f'{prefix}valor-catastral/">valor catastral</a>, y en {nombre} las '
            f'valoraciones vigentes van de <strong>{ano_min} en {m_min["nombre"]}</strong> '
            f'a <strong>{ano_max} en {m_max["nombre"]}</strong>.{frase_viejos} '
            f'El año de los valores de cada municipio está en la tabla, tal y como lo '
            f'publica el Ministerio de Hacienda.</p>\n'
        )
    else:
        valores_frase = ""

    return f"""  <p class="lead">Esta guía reúne el <strong>IBI, la plusvalía municipal, el impuesto de circulación y las bonificaciones</strong> de los <strong>{s['n']} municipios de {nombre}</strong> que cubrimos, con el detalle de cada uno y una tabla para compararlos de un vistazo. Población cubierta: {poblacion_txt} habitantes.</p>

  <div class="ed">
    <h2 class="sec" id="resumen">Lo que cuesta el IBI en {nombre} en 2026</h2>
    <p>El tipo de IBI urbano en {nombre} se mueve entre el <strong>{pct(min_t)} de {min_m['nombre']}</strong> y el <strong>{pct(max_t)} de {max_m['nombre']}</strong>, con una media de <strong>{pct2(s['media_tipo'])}</strong> en los {s['n']} municipios analizados. Esa horquilla parece pequeña, pero sobre un valor catastral de {euros(REFERENCE_VC)} supone una diferencia de <strong>{euros(delta)} al año</strong> según dónde esté el inmueble: {euros(REFERENCE_VC * min_t / 100)} en {min_m['nombre']} frente a {euros(REFERENCE_VC * max_t / 100)} en {max_m['nombre']}.</p>
{valores_frase}    <p>Aquí no publicamos el importe de la <a href="{prefix}tasa-basuras/">tasa de residuos</a> ni las fechas de cobro de cada municipio: no existe fuente estatal que los recoja y preferimos el hueco a un dato sin respaldo. Lo que sí fija la ley es el plazo por defecto del IBI, del 1 de septiembre al 20 de noviembre cuando la ordenanza no señala otro (art. 62.3 de la Ley General Tributaria). La mecánica general del impuesto está en las guías de <a href="{prefix}ibi-2026/">IBI 2026</a>, <a href="{prefix}bonificaciones/">bonificaciones</a> y <a href="{prefix}plusvalia/">plusvalía</a>; aquí van los datos de {nombre}.</p>
  </div>
"""


def toc_block(municipios: list[dict], prefix: str = "", modo: str = "hub") -> str:
    chips = "".join(
        f'<a href="{ficha_url(m, prefix, modo)}" class="ct">{html.escape(m["nombre"])}</a>'
        for m in municipios
    )
    titulo = (
        "Ficha fiscal de cada municipio" if modo == "hub" else "Ir directamente a tu municipio"
    )
    return f"""  <h2 class="sec" id="indice">{titulo}</h2>
  <div class="ct-grid">
    {chips}
  </div>
"""


def ficha_url(m: dict, prefix: str, modo: str) -> str:
    """Destino del nombre del municipio en la tabla.

    En modo 'hub' la ficha municipal sigue existiendo y es la que capta el
    long-tail («ibi molina de segura 2026»), asi que el pilar enlaza a ella.
    En modo 'absorbe' la ficha desaparece y el destino es el ancla interna.
    """
    if modo == "hub":
        return f"{prefix}{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/"
    return f"#{m['slug']}"


def table_block(t: dict, municipios: list[dict], prefix: str, modo: str = "hub") -> str:
    rows = []
    for m in municipios:
        cuota = REFERENCE_VC * m["tipo_urbano"] / 100 if m["tipo_urbano"] else None
        ano = m.get("oficial_ano_valores_catastrales") or ""
        bice = m.get("oficial_tipo_bice")
        hab = f"{m['poblacion']:,}".replace(",", ".") if m["poblacion"] else "—"
        rows.append(
            "<tr>"
            f'<td data-sort="{html.escape(m["nombre"])}"><a href="{ficha_url(m, prefix, modo)}"><strong>{html.escape(m["nombre"])}</strong></a></td>'
            f'<td data-sort="{m["poblacion"] or 0}">{hab}</td>'
            f'<td data-sort="{m["tipo_urbano"] or 0}" class="v">{pct(m["tipo_urbano"]) if m["tipo_urbano"] else "—"}</td>'
            f'<td data-sort="{m["tipo_rustico"] or 0}">{pct(m["tipo_rustico"]) if m["tipo_rustico"] else "—"}</td>'
            f'<td data-sort="{cuota or 0}">{euros(cuota) if cuota else "—"}</td>'
            f'<td data-sort="{ano or 0}">{html.escape(str(ano)) or "—"}</td>'
            f'<td data-sort="{bice or 0}">{pct(bice) if bice else "—"}</td>'
            "</tr>"
        )
    body = "\n            ".join(rows)
    return f"""  <h2 class="sec" id="tabla">Tabla comparativa: el IBI en los {len(municipios)} municipios de {t['nombre']}</h2>
  <p>Ordenable por cualquier columna. Todas las cifras salen de la consulta de información impositiva del Ministerio de Hacienda. «Cuota IBI» aplica el tipo de cada municipio a un valor catastral común de {euros(REFERENCE_VC)}; con el de tu recibo, usa la <a href="{prefix}calculadora-ibi/">calculadora</a>. «Valores catastrales» es el año de la última valoración vigente, que determina la base sobre la que se aplica el tipo.</p>
  <div class="table-scroll">
    <table class="dt sortable">
      <thead>
        <tr>
          <th data-col="0">Municipio</th>
          <th data-col="1">Habitantes</th>
          <th data-col="2">IBI urbano</th>
          <th data-col="3">IBI rústico</th>
          <th data-col="4">Cuota IBI (VC {euros(REFERENCE_VC)})</th>
          <th data-col="5">Valores catastrales</th>
          <th data-col="6">Tipo BICE</th>
        </tr>
      </thead>
      <tbody>
            {body}
      </tbody>
    </table>
  </div>
"""


def chart_block(t: dict, municipios: list[dict]) -> str:
    tipos = [m for m in municipios if m["tipo_urbano"]]
    if not tipos:
        return ""
    top = max(m["tipo_urbano"] for m in tipos)
    rows = []
    for m in sorted(tipos, key=lambda x: x["tipo_urbano"]):
        width = 55 + 45 * m["tipo_urbano"] / top
        rows.append(
            '  <div class="chart-bar-row">\n'
            f'    <span class="chart-label">{html.escape(m["nombre"])}</span>\n'
            '    <div class="chart-bar-wrap">\n'
            f'      <div class="chart-bar" style="width:{width:.0f}%;"><span>{pct(m["tipo_urbano"])}</span></div>\n'
            "    </div>\n  </div>"
        )
    bars = "\n".join(rows)
    return f"""  <h2 class="sec" id="grafico">Comparativa visual del tipo de IBI urbano</h2>
  <div class="chart-container">
{bars}
  </div>
  <p style="font-size:0.82rem;color:var(--mid);margin-top:6px">Tipo de gravamen del IBI urbano de cada municipio según la consulta de información impositiva del Ministerio de Hacienda. Un tipo más alto no implica siempre una cuota mayor: depende del valor catastral de cada inmueble.</p>
"""


def municipality_section(m: dict, prefix: str, _unused=None) -> str:
    """Seccion de datos puros: cero parrafos genericos, cero afirmaciones sin fuente.

    Solo contiene: contexto propio del municipio (una frase), la tabla de datos de su
    ordenanza, el estado de verificacion de esos datos y los enlaces oficiales
    comprobados donde el lector puede contrastarlos.
    """
    nombre = html.escape(m["nombre"])
    cuota = REFERENCE_VC * m["tipo_urbano"] / 100 if m["tipo_urbano"] else None

    meta = []
    if m["poblacion"]:
        meta.append(f"{m['poblacion']:,}".replace(",", ".") + " habitantes")
    if m.get("recaudacion"):
        meta.append(html.escape(m["recaudacion"]))

    filas = []
    if m["tipo_urbano"]:
        extra = f" <span style=\"color:var(--mid)\">({euros(cuota)}/año con un valor catastral de {euros(REFERENCE_VC)})</span>" if cuota else ""
        filas.append(f'<tr><td>Tipo de IBI urbano</td><td class="v">{pct(m["tipo_urbano"])}{extra}</td></tr>')
    if m["tipo_rustico"]:
        filas.append(f'<tr><td>Tipo de IBI rústico</td><td>{pct(m["tipo_rustico"])}</td></tr>')
    if m.get("oficial_ano_valores_catastrales"):
        filas.append(
            f'<tr><td>Año de los valores catastrales</td>'
            f'<td>{html.escape(str(m["oficial_ano_valores_catastrales"]))}</td></tr>'
        )
    if m.get("oficial_tipo_bice"):
        filas.append(
            f'<tr><td>Tipo de BICE</td><td>{pct(m["oficial_tipo_bice"])} '
            f'<span style="color:var(--mid)">(presas, autopistas, centrales, '
            f'aeropuertos)</span></td></tr>'
        )
    if m["boni_familia"]:
        filas.append(f'<tr><td>Bonificación por familia numerosa</td><td>{html.escape(m["boni_familia"])}</td></tr>')
    if m["boni_solar"]:
        filas.append(f'<tr><td>Bonificación por energía solar</td><td>{html.escape(m["boni_solar"])}</td></tr>')

    if m.get("oficial_fuente_url"):
        fecha = m.get("oficial_comprobado_el") or ""
        ejercicio = m.get("oficial_ejercicio") or ""
        estado = (
            f'<a href="{m["oficial_fuente_url"]}" target="_blank" rel="nofollow noopener">'
            f'Ministerio de Hacienda</a>, ejercicio {ejercicio}'
            + (f", comprobado el {fecha}" if fecha else "")
            + ". El pleno puede haber cambiado el tipo para 2026."
        )
    else:
        estado = (
            "Sin dato en la consulta del Ministerio de Hacienda. <strong>Confírmalo en "
            "la ordenanza fiscal</strong> antes de pagar o reclamar."
        )
    filas.append(f'<tr><td>Estado del dato</td><td style="font-size:.82rem">{estado}</td></tr>')

    enlaces = []
    if m.get("web_oficial"):
        etiqueta = html.escape(m.get("web_oficial_nombre") or f"Ayuntamiento de {m['nombre']}")
        enlaces.append(
            f'<a href="{m["web_oficial"]}" target="_blank" rel="nofollow noopener">{etiqueta}</a>'
        )
    # Antes se enlazaba el calendario de la Agencia Tributaria de Murcia en las
    # nueve comunidades. Ahora cada municipio enlaza al organismo que le recauda.
    rec = load_recaudadores().get(m.get("provincia_slug") or "") or {}
    if rec.get("url") and rec.get("nombre"):
        enlaces.append(
            f'<a href="{rec["url"]}" target="_blank" rel="nofollow noopener">'
            f'calendario de cobro ({html.escape(rec["nombre"])})</a>'
        )
    enlaces.append(
        '<a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">tu valor catastral</a>'
    )
    enlaces.append(f'<a href="{prefix}calculadora-ibi/">calcular tu cuota</a>')

    partes = [
        '  <section class="sec">',
        f'    <h2 id="{m["slug"]}">{nombre}: IBI, plusvalía y bonificaciones 2026</h2>',
    ]
    if meta:
        partes.append(f'    <p class="muni-meta">{" · ".join(meta)}</p>')
    if m["lead"]:
        partes.append(f"    <p>{m['lead']}</p>")
    partes.append(
        '    <table class="dt"><tbody>\n      ' + "\n      ".join(filas) + "\n    </tbody></table>"
    )
    partes.append(f'    <p style="font-size:.85rem">Comprobar en: {" · ".join(enlaces)} · <a href="#tabla">volver a la tabla</a></p>')
    partes.append("  </section>")
    return "\n".join(partes)


def faq_block(t: dict, s: dict, prefix: str) -> tuple[str, list[tuple[str, str]]]:
    """FAQ construida con los datos del territorio.

    Las respuestas genericas (que bonificaciones existen, donde esta la ordenanza)
    se han sustituido por preguntas que solo se pueden responder con los datos de
    esta comunidad: quien recauda y cuanto cuesta el IVTM. La mecanica general se
    enlaza a las guias nacionales en lugar de repetirse en nueve paginas.
    """
    nombre = t["nombre"]
    municipios = t["municipios"]
    min_t, min_m = s["min_tipo"]
    max_t, max_m = s["max_tipo"]

    qa = [
        (
            f"¿Qué municipio de {nombre} tiene el IBI más alto en 2026?",
            f"De los {s['n']} municipios analizados, el tipo urbano más alto es el de "
            f"{max_m['nombre']} ({pct(max_t)}) y el más bajo el de {min_m['nombre']} "
            f"({pct(min_t)}). Sobre un valor catastral de {euros(REFERENCE_VC)} son "
            f"{euros(REFERENCE_VC * max_t / 100)} frente a "
            f"{euros(REFERENCE_VC * min_t / 100)} al año.",
        ),
        (
            f"¿Cuál es el tipo medio de IBI en {nombre}?",
            f"La media de los {s['n']} municipios de {nombre} que recoge esta guía es "
            f"del {pct2(s['media_tipo'])}, con una mediana del "
            f"{pct2(_mediana([m['tipo_urbano'] for m in municipios if m.get('tipo_urbano')]))}. "
            f"La ley permite moverse entre el 0,40% y el 1,10% en urbana.",
        ),
        (
            f"¿Cuándo se paga el IBI en {nombre}?",
            f"No hay una fecha única: la fija cada ordenanza y se aprueba cada "
            f"ejercicio, por eso no publicamos fechas concretas. Cuando la ordenanza no "
            f"señala otro plazo se aplica el del artículo 62.3 de la Ley General "
            f"Tributaria, del 1 de septiembre al 20 de noviembre, y quien lo modifique "
            f"no puede dejarlo en menos de dos meses. El calendario del año lo publica "
            f"el organismo que recauda, enlazado en la ficha de cada municipio.",
        ),
        (
            f"¿Cuánto se paga de basuras en {nombre}?",
            f"No lo publicamos porque no podemos verificarlo: la tarifa está en la "
            f"ordenanza fiscal de cada ayuntamiento y ninguna administración estatal las "
            f"reúne. La Ley 7/2022 obliga desde el 10 de abril de 2025 a cobrar una tasa "
            f"de residuos específica, diferenciada y no deficitaria (art. 11.3), y solo "
            f"exige comunicarla a la comunidad autónoma (art. 11.5). En la guía de la "
            f"tasa de residuos explicamos dónde localizar la tuya.",
        ),
    ]

    # Quien recauda: dato propio del territorio.
    recaudadores = load_recaudadores()
    organismos = []
    for m in municipios:
        rec = recaudadores.get(m["provincia_slug"])
        if rec and rec.get("nombre") and rec["nombre"] not in organismos:
            organismos.append(rec["nombre"])
    if organismos:
        lista = (organismos[0] if len(organismos) == 1
                 else ", ".join(organismos[:-1]) + " y " + organismos[-1])
        qa.append((
            f"¿Quién cobra el IBI en {nombre}?",
            f"En {nombre} la recaudación de buena parte de los ayuntamientos corre a "
            f"cargo de: {lista}. El resto la lleva su propio ayuntamiento. Cada ficha "
            f"indica cuál corresponde y enlaza dónde consultar el calendario.",
        ))

    # IVTM: dato propio del territorio.
    imps = load_impuestos()
    tarifas = []
    for m in municipios:
        v = _valor(imps.get(m.get("oficial_codigo_ine") or ""), "C19")
        if v is not None:
            tarifas.append((v, m))
    if len(tarifas) >= 3:
        tarifas.sort(key=lambda par: par[0])
        qa.append((
            f"¿Dónde cuesta más el impuesto de circulación en {nombre}?",
            f"Por un turismo de 8 a 11,99 caballos fiscales, el más caro de "
            f"{nombre} es {tarifas[-1][1]['nombre']} con {_num(tarifas[-1][0])} € al "
            f"año y el más barato {tarifas[0][1]['nombre']} con "
            f"{_num(tarifas[0][0])} €. La cuota mínima que fija la ley es de 34,08 €.",
        ))

    items = "\n".join(
        f'    <h3>{html.escape(q)}</h3>\n    <p>{html.escape(a)}</p>' for q, a in qa
    )
    block = f"""  <section class="sec">
    <h2 id="faq">Preguntas frecuentes sobre el IBI y las tasas en {nombre}</h2>
{items}
  </section>
"""
    return block, qa


def legal_sources() -> list[dict]:
    path = ROOT / "data" / "fuentes_legales.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["fuentes"]


def methodology_block(t: dict, s: dict, prefix: str, municipios: list[dict]) -> str:
    """Estado de verificacion de ESTE territorio.

    La politica completa (que fuente respalda cada dato, como corregimos, que no
    hacemos) vive una sola vez en /metodologia/. Antes se repetia entera en cada
    pilar: 350 palabras identicas en nueve paginas.
    """
    enlaces_ok = sum(1 for m in municipios if m.get("web_http_status") == 200)
    con_enlace = sum(1 for m in municipios if m.get("web_oficial"))
    verificados = sum(1 for m in municipios if m.get("oficial_tipo_urbana"))
    comprobadas = next(
        (m.get("web_comprobada_el") for m in municipios if m.get("web_comprobada_el")),
        TODAY,
    )
    # La lista de normas si se mantiene: son citas, y sin ellas el pilar afirmaria
    # limites legales sin enlazar de donde salen.
    fila_webs = (
        f'        <tr><td>Webs oficiales de los ayuntamientos</td><td><strong>'
        f'{enlaces_ok} de {con_enlace}</strong> respondían el {comprobadas}</td></tr>\n'
        if con_enlace else ""
    )
    fuentes_html = "\n      ".join(
        f'<li><a href="{f["url"]}" target="_blank" rel="nofollow noopener">'
        f'{html.escape(f["titulo"])}</a></li>'
        for f in legal_sources()
    )
    return f"""  <section class="sec">
    <h2 id="metodologia">Qué está verificado en esta página</h2>
    <table class="dt">
      <thead><tr><th>Dato</th><th>Estado en {t['nombre']}</th></tr></thead>
      <tbody>
        <tr><td>Tipos de IBI, rústica, BICE y año de los valores catastrales</td><td><strong>{verificados} de {s['n']}</strong> contrastados con el Ministerio de Hacienda</td></tr>
{fila_webs}        <tr><td>Tasa de residuos y fechas de cobro</td><td><strong>No se publican:</strong> las fija cada ordenanza, no hay registro estatal y no hemos podido acceder a una fuente primaria</td></tr>
      </tbody>
    </table>
    <p>Si un dato no coincide con lo que dice tu ayuntamiento, manda la ordenanza publicada en el boletín oficial. <a href="{prefix}metodologia/">Qué fuente respalda cada dato y cómo corregimos →</a> · <a href="{prefix}contacto/">Avisar de un error</a></p>
    <h3>Normativa citada en esta página</h3>
    <ul>
      {fuentes_html}
    </ul>
  </section>
"""


# ───────────────── secciones territoriales con datos oficiales ─────────────────
#
# El pilar de Murcia arrastraba ~1.500 palabras de explicaciones genericas
# (limites legales, bonificaciones del TRLRHL, Ley 7/2022, plusvalia tras la STC,
# recargos, como consultar el Catastro). Replicarlas en nueve comunidades daria
# nueve paginas casi identicas entre si y ademas duplicadas con las guias
# nacionales, que es justo lo que Google llama contenido de poco valor.
#
# En su lugar, cada pilar publica secciones construidas con los datos oficiales de
# SUS municipios: quien recauda, donde se paga mas, los otros tributos, la
# antiguedad catastral y la evolucion del padron. La mecanica general vive una sola
# vez en /ibi-2026/, /bonificaciones/, /tasa-basuras/ y /plusvalia/, y se enlaza.

HACIENDA_URL = ("https://serviciostelematicosext.hacienda.gob.es/SGFAL/ConsultaTipos/"
                "html/portadaconsultasm.aspx")
# Coeficientes maximos del art. 107.4 TRLRHL.
MAXIMOS_PLUSVALIA = [
    0.15, 0.15, 0.14, 0.14, 0.16, 0.18, 0.19, 0.20, 0.19, 0.15, 0.12,
    0.10, 0.09, 0.09, 0.09, 0.09, 0.10, 0.13, 0.17, 0.23, 0.40,
]


def _num(value: float, dec: int = 2) -> str:
    return f"{value:,.{dec}f}".replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def _mediana(valores: list[float]) -> float:
    orden = sorted(valores)
    n = len(orden)
    if n % 2:
        return orden[n // 2]
    return (orden[n // 2 - 1] + orden[n // 2]) / 2


def load_impuestos() -> dict:
    path = ROOT / "data" / "hacienda_impuestos.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_recaudadores() -> dict:
    path = ROOT / "data" / "recaudadores.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("provincias", {})


def _valor(imp: dict | None, codigo: str) -> float | None:
    if not imp:
        return None
    c = (imp.get("conceptos") or {}).get(codigo) or {}
    bruto = c.get("valor")
    if bruto in (None, "", "-"):
        return None
    try:
        return float(str(bruto).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def national_stats() -> dict:
    """Referencias nacionales sobre los 134 municipios, para contextualizar."""
    records = json.loads(DATA_FILE.read_text(encoding="utf-8"))["municipios"]
    tipos = [m["oficial_tipo_urbana"] for m in records if m.get("oficial_tipo_urbana")]
    anos = [int(m["oficial_ano_valores_catastrales"]) for m in records
            if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()]
    return {
        "n": len(tipos),
        "mediana_tipo": _mediana(tipos) if tipos else 0,
        "mediana_ano": _mediana(anos) if anos else 0,
    }


def ficha_link(m: dict, prefix: str) -> str:
    return (f'<a href="{prefix}{m["ccaa"]}/{m["provincia_slug"]}/{m["slug"]}/">'
            f'{html.escape(m["nombre"])}</a>')


def gestion_block(t: dict, municipios: list[dict], prefix: str) -> str:
    """Quien gestiona y cobra, provincia a provincia, con la fuente comprobada."""
    recaudadores = load_recaudadores()
    por_prov: dict[str, list[dict]] = defaultdict(list)
    for m in municipios:
        por_prov[m["provincia_slug"]].append(m)

    filas, sin_organismo = [], []
    for prov, items in sorted(por_prov.items(), key=lambda kv: -len(kv[1])):
        rec = recaudadores.get(prov)
        nombre_prov = items[0].get("provincia") or prov.replace("-", " ").title()
        if rec and rec.get("url"):
            organismo = (f'<a href="{rec["url"]}" target="_blank" rel="nofollow noopener">'
                         f'{html.escape(rec["nombre"])}</a>')
            estado = ("responde correctamente" if rec.get("http_status") == 200
                      else "pendiente de comprobar")
        else:
            organismo = "Cada ayuntamiento, por su cuenta"
            estado = "—"
            sin_organismo.append(nombre_prov)
        filas.append(
            f'        <tr><td>{html.escape(nombre_prov)}</td>'
            f'<td>{len(items)}</td><td>{organismo}</td><td>{estado}</td></tr>'
        )

    aviso = ""
    if sin_organismo:
        aviso = (f'    <p>En {", ".join(sin_organismo)} no hemos identificado un '
                 f'organismo provincial de recaudación para estos municipios: el '
                 f'calendario y la ventanilla de pago están en la web de cada '
                 f'ayuntamiento.</p>\n')

    return f"""  <section class="sec">
    <h2 id="gestion">Quién gestiona y cobra el IBI en {t['nombre']}</h2>
    <p>El recibo, el calendario y las solicitudes se tramitan <strong>donde esté la recaudación</strong>, que no siempre es el ayuntamiento:</p>
    <table class="dt">
      <thead><tr><th>Provincia</th><th>Municipios en la guía</th><th>Organismo de recaudación</th><th>Estado del enlace</th></tr></thead>
      <tbody>
{chr(10).join(filas)}
      </tbody>
    </table>
{aviso}    <p>De ahí que no haya una fecha única para toda {t['nombre']}: cada organismo publica su calendario.</p>
  </section>"""


def ranking_block(t: dict, municipios: list[dict], prefix: str, nac: dict,
                  s: dict) -> str:
    """Donde se paga mas y menos dentro del territorio, con la referencia nacional."""
    con_tipo = [m for m in municipios if m.get("oficial_tipo_urbana")]
    if len(con_tipo) < 3:
        return ""
    tipos = [m["oficial_tipo_urbana"] for m in con_tipo]
    mediana = _mediana(tipos)
    nac_med = nac["mediana_tipo"]
    # Exactamente los municipios que citan la entradilla y la FAQ: si aqui se
    # eligieran por separado, tres partes de la pagina nombrarian municipios
    # distintos cuando varios empatan en el extremo.
    alto = s["max_tipo"][1]
    bajo = s["min_tipo"][1]
    empatan_alto = [m for m in con_tipo
                    if abs(m["oficial_tipo_urbana"] - alto["oficial_tipo_urbana"]) < 1e-9]
    empatan_bajo = [m for m in con_tipo
                    if abs(m["oficial_tipo_urbana"] - bajo["oficial_tipo_urbana"]) < 1e-9]

    def extremo(m: dict, empatados: list[dict]) -> str:
        if len(empatados) > 1:
            return f"empatan {len(empatados)} municipios al {pct(m['oficial_tipo_urbana'])}"
        return f"está {ficha_link(m, prefix)} con el {pct(m['oficial_tipo_urbana'])}"
    diff = (mediana - nac_med) / 100 * REFERENCE_VC

    # Por debajo de una centesima de punto la diferencia no se ve al redondear:
    # decir «queda 0,007 puntos por encima de 0,61%» partiendo de 0,61% parece un error.
    if abs(mediana - nac_med) < 0.01:
        comparacion = (f"está en línea con la mediana de los {nac['n']} municipios que "
                       f"analizamos en toda España ({pct2(nac_med)})")
    elif mediana > nac_med:
        comparacion = (f"queda {_num(mediana - nac_med, 3)} puntos por encima de la "
                       f"mediana nacional de la guía ({pct2(nac_med)}): {euros(abs(diff))} "
                       f"más al año por un inmueble de {euros(REFERENCE_VC)}")
    else:
        comparacion = (f"queda {_num(nac_med - mediana, 3)} puntos por debajo de la "
                       f"mediana nacional de la guía ({pct2(nac_med)}): {euros(abs(diff))} "
                       f"menos al año por un inmueble de {euros(REFERENCE_VC)}")

    en_minimo = [m for m in con_tipo if abs(m["oficial_tipo_urbana"] - 0.40) < 1e-9]
    minimo_txt = ""
    if en_minimo:
        minimo_txt = (
            f" {len(en_minimo)} de ellos aplican exactamente el mínimo legal del 0,40% ("
            + ", ".join(ficha_link(m, prefix) for m in en_minimo) + ")."
        )

    subidas = [m for m in con_tipo if m.get("oficial_tipo_urbana_anterior")
               and m["oficial_tipo_urbana"] > m["oficial_tipo_urbana_anterior"]]
    bajadas = [m for m in con_tipo if m.get("oficial_tipo_urbana_anterior")
               and m["oficial_tipo_urbana"] < m["oficial_tipo_urbana_anterior"]]
    cambios = ""
    if subidas or bajadas:
        filas = "\n".join(
            f'        <tr><td>{ficha_link(m, prefix)}</td>'
            f'<td>{pct(m["oficial_tipo_urbana_anterior"])}</td>'
            f'<td class="v">{pct(m["oficial_tipo_urbana"])}</td>'
            f'<td>{"Sube" if m["oficial_tipo_urbana"] > m["oficial_tipo_urbana_anterior"] else "Baja"} '
            f'{_num(abs(m["oficial_tipo_urbana"] - m["oficial_tipo_urbana_anterior"]), 3)} puntos</td></tr>'
            for m in sorted(subidas + bajadas,
                            key=lambda x: -abs(x["oficial_tipo_urbana"]
                                               - x["oficial_tipo_urbana_anterior"]))
        )
        def cuenta(n: int, verbo_sing: str, verbo_plur: str) -> str:
            if n == 0:
                return f"ningún municipio {verbo_sing}"
            if n == 1:
                return f"un municipio {verbo_sing}"
            return f"{n} municipios {verbo_plur}"

        frase_cambios = (
            f"En {t['nombre']}, {cuenta(len(subidas), 'ha subido', 'han subido')} el "
            f"tipo y {cuenta(len(bajadas), 'lo ha bajado', 'lo han bajado')}; el resto "
            f"lo mantiene."
        )
        ej = con_tipo[0].get("oficial_ejercicio", "2025")
        ej_ant = con_tipo[0].get("oficial_ejercicio_anterior", "2024")
        cambios = f"""
    <h3>Quién ha movido el tipo entre {ej_ant} y {ej}</h3>
    <p>{frase_cambios}</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>{ej_ant}</th><th>{ej}</th><th>Variación</th></tr></thead>
      <tbody>
{filas}
      </tbody>
    </table>"""

    return f"""  <section class="sec">
    <h2 id="ranking">¿Dónde se paga más y menos IBI en {t['nombre']}?</h2>
    <p>La mediana del tipo urbano de los {len(con_tipo)} municipios de {t['nombre']} es del <strong>{pct2(mediana)}</strong>, y {comparacion}.{minimo_txt}</p>
    <p>En el extremo alto {extremo(alto, empatan_alto)}; en el bajo {extremo(bajo, empatan_bajo)}. Ojo: <strong>un tipo alto no significa un recibo alto</strong>, porque la cuota es valor catastral × tipo. <a href="{prefix}analisis/ranking-ibi-municipios/">Ranking nacional →</a></p>{cambios}
  </section>"""


def otros_tributos_block(t: dict, municipios: list[dict], prefix: str) -> str:
    """ICIO, IVTM y plusvalia reales de cada municipio del territorio."""
    imps = load_impuestos()
    filas, icios, ivtms, en_maximo, con_coef = [], [], [], [], []
    for m in sorted(municipios, key=lambda x: x["nombre"]):
        imp = imps.get(m.get("oficial_codigo_ine") or "")
        if not imp:
            continue
        icio = _valor(imp, "C17")
        ivtm = _valor(imp, "C19")
        coefs = [_valor(imp, f"C{n}") for n in range(51, 72)]
        tipos_p = [_valor(imp, f"C{n}") for n in range(72, 93)]
        validos_t = [x for x in tipos_p if x is not None]
        validos_c = [c for c in coefs if c is not None]
        # Series muy por debajo del maximo legal son el porcentaje anual del
        # sistema anterior al RDL 26/2021: no las tratamos como coeficientes.
        coherente = bool(validos_c) and 0.10 <= max(validos_c) <= 0.45
        if coherente:
            con_coef.append(m)
            if all(c is not None and abs(c - mx) < 1e-9
                   for c, mx in zip(coefs, MAXIMOS_PLUSVALIA)):
                en_maximo.append(m)
        if icio is not None:
            icios.append(icio)
        if ivtm is not None:
            ivtms.append(ivtm)
        filas.append(
            f'        <tr><td>{ficha_link(m, prefix)}</td>'
            f'<td class="v">{pct(icio) if icio is not None else "—"}</td>'
            f'<td>{_num(ivtm) + " €" if ivtm is not None else "—"}</td>'
            f'<td>{pct(max(validos_t)) if validos_t and coherente else "—"}</td>'
            f'<td>{"Sí" if m in en_maximo else ("No" if coherente else "—")}</td></tr>'
        )
    if not filas:
        return ""

    resumen = []
    if icios:
        resumen.append(f"el ICIO va del {pct(min(icios))} al {pct(max(icios))} "
                       f"(mediana {pct(_mediana(icios))})")
    if ivtms:
        resumen.append(f"un turismo de 8 a 11,99 CV paga entre {_num(min(ivtms))} € y "
                       f"{_num(max(ivtms))} € al año")
    if con_coef:
        resumen.append(f"{len(en_maximo)} de {len(con_coef)} aplican los coeficientes "
                       f"máximos de plusvalía del art. 107.4 TRLRHL")

    return f"""  <section class="sec">
    <h2 id="otros-tributos">ICIO, impuesto de circulación y plusvalía en {t['nombre']}</h2>
    <p>El IBI no es el único tributo que aprueba un ayuntamiento. En {t['nombre']}, {"; ".join(resumen)}.</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>ICIO (obras)</th><th>IVTM 8–11,99 CV</th><th>Plusvalía: tipo máximo</th><th>¿Coeficientes al tope legal?</th></tr></thead>
      <tbody>
{chr(10).join(filas)}
      </tbody>
    </table>
    <p style="font-size:.85rem;color:var(--mid)">Fuente: <a href="{HACIENDA_URL}" target="_blank" rel="nofollow noopener">Ministerio de Hacienda</a>. El guion marca lo que la consulta no publica. La tarifa completa del IVTM está en cada ficha.</p>
    <p><a href="{prefix}impuesto-circulacion/">Guía del impuesto de circulación →</a> · <a href="{prefix}analisis/impuesto-circulacion-ivtm/">Comparativa del IVTM →</a> · <a href="{prefix}analisis/coeficientes-plusvalia/">Quién aplica el coeficiente máximo de plusvalía →</a></p>
  </section>"""


def catastro_block(t: dict, municipios: list[dict], prefix: str, nac: dict) -> str:
    """Antiguedad de la ultima valoracion colectiva, que es la mitad de la cuota."""
    datos = [(int(m["oficial_ano_valores_catastrales"]), m) for m in municipios
             if str(m.get("oficial_ano_valores_catastrales") or "").isdigit()]
    if len(datos) < 3:
        return ""
    datos.sort(key=lambda par: par[0])
    ano_actual = date.today().year
    anos = [a for a, _ in datos]
    mediana = _mediana(anos)
    viejos = [m for a, m in datos if ano_actual - a >= 20]
    filas = "\n".join(
        f'        <tr><td>{ficha_link(m, prefix)}</td><td class="v">{a}</td>'
        f'<td>{ano_actual - a} años</td>'
        f'<td>{pct(m["oficial_tipo_urbana"]) if m.get("oficial_tipo_urbana") else "—"}</td></tr>'
        for a, m in datos
    )
    relacion = ("más antigua" if mediana < nac["mediana_ano"]
                else "más reciente" if mediana > nac["mediana_ano"] else "igual")
    return f"""  <section class="sec">
    <h2 id="catastro">Cuándo se revisaron los valores catastrales en {t['nombre']}</h2>
    <p>La cuota del IBI es <strong>valor catastral × tipo</strong>, así que la fecha de la última valoración colectiva pesa tanto como el porcentaje que vota el pleno. En {t['nombre']} la mediana está en <strong>{int(mediana)}</strong>, {relacion} que la del conjunto de la guía ({int(nac['mediana_ano'])}), y <strong>{len(viejos)} de {len(datos)}</strong> municipios arrastran valores de hace 20 años o más.</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>Año de la valoración</th><th>Antigüedad</th><th>Tipo urbano</th></tr></thead>
      <tbody>
{filas}
      </tbody>
    </table>
    <p><a href="{prefix}valor-catastral/">Qué es el valor catastral, cómo se consulta y cómo se corrige →</a> · <a href="{prefix}analisis/valores-catastrales-antiguos/">Qué implica una ponencia desfasada →</a></p>
  </section>"""


def poblacion_block(t: dict, municipios: list[dict], prefix: str) -> str:
    """Evolucion del padron: explica por donde va la tasa de residuos."""
    con_serie = [m for m in municipios if len(m.get("poblacion_serie") or []) >= 2]
    if len(con_serie) < 3:
        return ""
    filas, ganan, pierden = [], 0, 0
    total_ini = total_fin = 0
    for m in sorted(con_serie, key=lambda x: -(x["poblacion_serie"][-1][1])):
        (y0, p0), (y1, p1) = m["poblacion_serie"][0], m["poblacion_serie"][-1]
        delta = p1 - p0
        total_ini += p0
        total_fin += p1
        if delta > 0:
            ganan += 1
        elif delta < 0:
            pierden += 1
        filas.append(
            f'        <tr><td>{ficha_link(m, prefix)}</td>'
            f'<td>{_num(p0, 0)}</td><td class="v">{_num(p1, 0)}</td>'
            f'<td>{"+" if delta > 0 else ""}{_num(delta, 0)}</td>'
            f'<td>{"+" if delta > 0 else ""}{_num(delta / p0 * 100, 1)} %</td></tr>'
        )
    y0 = con_serie[0]["poblacion_serie"][0][0]
    y1 = con_serie[0]["poblacion_serie"][-1][0]
    conjunto = total_fin - total_ini
    signo = "ganado" if conjunto > 0 else "perdido"
    return f"""  <section class="sec">
    <h2 id="poblacion">Población de los municipios de {t['nombre']} ({y0}–{y1})</h2>
    <p>El padrón no cambia el IBI, pero sí explica la tasa de residuos: cuando el coste del servicio se reparte entre menos vecinos, la tarifa sube. En conjunto, los {len(con_serie)} municipios de {t['nombre']} que cubrimos han {signo} <strong>{_num(abs(conjunto), 0)} habitantes</strong> desde {y0} ({ganan} {"crece" if ganan == 1 else "crecen"}, {pierden} {"pierde" if pierden == 1 else "pierden"} población).</p>
    <table class="dt">
      <thead><tr><th>Municipio</th><th>{y0}</th><th>{y1}</th><th>Variación</th><th>%</th></tr></thead>
      <tbody>
{chr(10).join(filas)}
      </tbody>
    </table>
    <p style="font-size:.85rem;color:var(--mid)">Fuente: INE, padrón a 1 de enero.</p>
  </section>"""


# Solo se conservan los bloques editoriales que aportan algo que los datos no
# dicen. Los que explicaban la mecanica general del impuesto se han retirado:
# viven una sola vez en las guias nacionales y el pilar las enlaza.
BLOQUES_EDITORIALES_PERMITIDOS = {"quien-recauda", "contexto-territorial"}


def territorial_content(t: dict, prefix: str) -> str:
    """Bloques editoriales propios del territorio (data/territorios.json)."""
    path = ROOT / "data" / "territorios.json"
    if not path.exists():
        return ""
    contenido = json.loads(path.read_text(encoding="utf-8")).get(t["key"])
    if not contenido:
        return ""
    out = []
    for bloque in contenido["bloques"]:
        if bloque["id"] not in BLOQUES_EDITORIALES_PERMITIDOS:
            continue
        cuerpo = bloque["html"].replace("{P}", prefix)
        out.append(
            f'  <section class="sec">\n    <h2 id="{bloque["id"]}">{html.escape(bloque["h2"])}</h2>\n'
            f"    {cuerpo}\n  </section>"
        )
    return "\n\n".join(out)


def svg_size(path: Path) -> tuple[int, int]:
    head = path.read_text(encoding="utf-8")[:400]
    w = re.search(r'width="(\d+)"', head)
    h = re.search(r'height="(\d+)"', head)
    return (int(w.group(1)) if w else 900, int(h.group(1)) if h else 500)


def figure(src: str, alt: str, caption: str, width: int, height: int, lazy: bool = True) -> str:
    loading = ' loading="lazy" decoding="async"' if lazy else ""
    return (
        f'  <figure class="fig">\n'
        f'    <img src="{src}" alt="{html.escape(alt)}" width="{width}" height="{height}"{loading}>\n'
        f"    <figcaption>{caption}</figcaption>\n  </figure>"
    )


SORT_SCRIPT = """<script>
(function () {
  document.querySelectorAll('table.sortable').forEach(function (table) {
    var tbody = table.querySelector('tbody');
    table.querySelectorAll('th[data-col]').forEach(function (th) {
      th.style.cursor = 'pointer';
      th.title = 'Ordenar por esta columna';
      th.addEventListener('click', function () {
        var col = +th.dataset.col;
        var asc = th.dataset.dir !== 'asc';
        table.querySelectorAll('th[data-col]').forEach(function (o) { delete o.dataset.dir; });
        th.dataset.dir = asc ? 'asc' : 'desc';
        var rows = Array.prototype.slice.call(tbody.rows);
        rows.sort(function (a, b) {
          var x = a.cells[col].dataset.sort, y = b.cells[col].dataset.sort;
          var nx = parseFloat(x), ny = parseFloat(y);
          var cmp = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : String(x).localeCompare(String(y), 'es');
          return asc ? cmp : -cmp;
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });
  });
})();
</script>
"""


def schema_block(t: dict, municipios: list[dict], canonical: str, qa, prefix_url: str) -> str:
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"IBI, tasa de basuras y plusvalía en {t['nombre']} 2026",
        "url": canonical,
        "datePublished": "2026-02-01",
        "dateModified": TODAY,
        "author": {"@type": "Person", "name": "Aithamy Rivero", "url": f"{SITE}/sobre-nosotros/"},
        "publisher": {"@type": "Organization", "name": "TasasMunicipales.info"},
        "about": {"@type": "Thing", "name": f"Impuesto sobre Bienes Inmuebles en {t['nombre']}"},
    }
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Municipios de {t['nombre']} con datos de IBI y tasas 2026",
        "numberOfItems": len(municipios),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": m["nombre"],
                "url": f"{canonical}#{m['slug']}",
            }
            for i, m in enumerate(municipios)
        ],
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qa
        ],
    }
    crumbs = [
        {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Comunidades", "item": f"{SITE}/comunidades/"},
    ]
    if t["nivel"] == "provincia":
        crumbs.append({"@type": "ListItem", "position": 3, "name": CCAA_NAMES[t["ccaa"]],
                       "item": f"{SITE}/{t['ccaa']}/"})
        crumbs.append({"@type": "ListItem", "position": 4, "name": t["nombre"], "item": canonical})
    else:
        crumbs.append({"@type": "ListItem", "position": 3, "name": t["nombre"], "item": canonical})
    breadcrumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}

    out = []
    for obj in (article, itemlist, faq, breadcrumb):
        out.append('<script type="application/ld+json">\n'
                   + json.dumps(obj, ensure_ascii=False, indent=1)
                   + "\n</script>")
    return "\n".join(out) + "\n"


# ──────────────────────────── generacion del pilar ─────────────────────────

def build_pillar(t: dict, unique_map: dict[str, list[str]], modo: str = "hub") -> tuple[Path, str]:
    depth = len(t["key"].split("/"))
    prefix = "../" * depth
    canonical = f"{SITE}/{t['key']}/"
    municipios = t["municipios"]
    s = stats(municipios)
    nombre = t["nombre"]
    nac = national_stats()

    # En modo hub el titulo apunta a la intencion comparativa/regional, para no
    # competir con las fichas municipales por su propio long-tail.
    if modo == "hub":
        title = f"IBI en {nombre} 2026: comparativa de {s['n']} municipios"
    else:
        title = f"IBI y plusvalía en {nombre} 2026: los {s['n']} municipios"
    if len(title) > 65:
        title = f"IBI y tasas en {nombre} 2026: {s['n']} municipios comparados"
    min_t = s["min_tipo"][0]
    max_t = s["max_tipo"][0]
    description = (
        f"IBI, plusvalía municipal, impuesto de circulación y bonificaciones de los "
        f"{s['n']} municipios de {nombre} en 2026. Tipos del {pct(min_t)} al {pct(max_t)} "
        f"según el Ministerio de Hacienda, tabla comparativa y enlaces oficiales."
    )

    breadcrumb_html = f'<div class="bc"><a href="{prefix}">Inicio</a><span>›</span><a href="{prefix}comunidades/">Comunidades</a><span>›</span>'
    if t["nivel"] == "provincia":
        breadcrumb_html += f'<a href="{prefix}{t["ccaa"]}/">{CCAA_NAMES[t["ccaa"]]}</a><span>›</span>'
    breadcrumb_html += f"<strong>{nombre}</strong></div>"

    faq_html, qa = faq_block(t, s, prefix)
    if modo == "hub":
        # Las fichas municipales siguen publicadas: el pilar no repite sus datos,
        # los compara y enlaza. Asi no se canibaliza el long-tail municipal.
        enlaces_fichas = "\n".join(
            f'      <li><a href="{ficha_url(m, prefix, modo)}"><strong>{html.escape(m["nombre"])}</strong></a>'
            + (f" — IBI {pct(m['tipo_urbano'])}" if m.get("tipo_urbano") else "")
            + (f" · cuota {euros(REFERENCE_VC * m['tipo_urbano'] / 100)} con VC de "
               f"{euros(REFERENCE_VC)}" if m.get("tipo_urbano") else "")
            + (f" · valores de {html.escape(str(m['oficial_ano_valores_catastrales']))}"
               if m.get("oficial_ano_valores_catastrales") else "")
            + "</li>"
            for m in municipios
        )
        sections = f"""  <section class="sec">
    <h2 id="fichas">Ficha fiscal de los {s['n']} municipios de {nombre}</h2>
    <p>Cada ficha recoge el detalle de ese ayuntamiento: tipos aprobados, calendario de cobro, bonificaciones, plusvalía y enlaces oficiales donde comprobarlo.</p>
    <ul class="muni-list">
{enlaces_fichas}
    </ul>
  </section>"""
    else:
        sections = "\n\n".join(municipality_section(m, prefix) for m in municipios)

    otras = "".join(
        f'<a href="{prefix}{slug}/" class="ct{" on" if slug == t["ccaa"] else ""}">{name}</a>'
        for slug, name in sorted(CCAA_NAMES.items(), key=lambda kv: kv[1])
    )

    slug_img = t["key"].replace("/", "-")
    figuras = []
    tipos_svg = ROOT / "img" / f"{slug_img}-ibi-urbano-2026.svg"
    coste_svg = ROOT / "img" / f"{slug_img}-valores-catastrales.svg"
    esquema_svg = ROOT / "img" / "esquema-calculo-ibi.svg"
    if tipos_svg.exists():
        w, h = svg_size(tipos_svg)
        figuras.append(figure(
            f"{prefix}img/{tipos_svg.name}",
            f"Gráfico del tipo de IBI urbano de los {s['n']} municipios de {nombre} en 2026, "
            f"del {pct(s['min_tipo'][0])} al {pct(s['max_tipo'][0])}",
            f"Tipo de IBI urbano por municipio en {nombre}. Gráfico propio elaborado con los datos de esta página.",
            w, h, lazy=False,
        ))
    if coste_svg.exists():
        w, h = svg_size(coste_svg)
        figuras.append(figure(
            f"{prefix}img/{coste_svg.name}",
            f"Gráfico del año de los valores catastrales vigentes en los municipios de {nombre}",
            "Año de la última valoración catastral de cada municipio, tal y como lo publica "
            "el Ministerio de Hacienda: es la base sobre la que se aplica el tipo del IBI.",
            w, h,
        ))
    esquema_fig = ""
    if esquema_svg.exists():
        w, h = svg_size(esquema_svg)
        esquema_fig = figure(
            f"{prefix}img/{esquema_svg.name}",
            "Esquema del cálculo del IBI: valor catastral, base liquidable, tipo de gravamen, "
            "cuota íntegra y bonificaciones",
            "Del valor catastral al importe del recibo. Esquema propio según los artículos 65 a 74 del TRLRHL.",
            w, h,
        )

    body = f"""{breadcrumb_html}
<div class="wrap">
  <h1>IBI, tasa de basuras y plusvalía en {nombre} 2026</h1>
{intro_block(t, s, prefix)}
{toc_block(municipios, prefix, modo)}
{table_block(t, municipios, prefix, modo)}
{chr(10).join(figuras)}
{territorial_content(t, prefix)}

{gestion_block(t, municipios, prefix)}

{ranking_block(t, municipios, prefix, nac, s)}

{otros_tributos_block(t, municipios, prefix)}

{catastro_block(t, municipios, prefix, nac)}

{poblacion_block(t, municipios, prefix)}

{esquema_fig}

{sections}

{faq_html}
{methodology_block(t, s, prefix, municipios)}
  <h2 class="sec">Otras comunidades autónomas</h2>
  <div class="ct-grid">
    {otras}
  </div>
</div>
{SORT_SCRIPT}{schema_block(t, municipios, canonical, qa, prefix)}"""

    doc = head_block(title, description, canonical, prefix) + body + footer_block(prefix)
    return ROOT / t["key"] / "index.html", doc


# ──────────────────────── redirecciones de municipios ──────────────────────

def redirect_stub(m: dict, target_url: str, target_rel: str, prefix: str) -> str:
    nombre = html.escape(m["nombre"])
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>IBI y tasas en {nombre} 2026 — TasasMunicipales</title>
  <link rel="canonical" href="{target_url}">
  <meta http-equiv="refresh" content="0; url={target_rel}">
  <link rel="stylesheet" href="{prefix}styles.css">
  <script>window.location.replace("{target_rel}");</script>
</head>
<body>
<div class="wrap" style="padding:60px 24px;text-align:center">
  <h1>Esta página se ha unificado</h1>
  <p class="lead">La información fiscal de {nombre} vive ahora, ampliada y comparada con el resto de municipios, en la guía territorial.</p>
  <p><a href="{target_rel}" style="color:var(--accent);font-weight:600">Ir a los datos de {nombre} →</a></p>
</div>
</body>
</html>
"""


def rewrite_internal_links(ccaa: str, provincia: str, slugs: set[str], target_key: str) -> int:
    """Reescribe los enlaces internos a fichas absorbidas para que apunten al ancla."""
    pattern = re.compile(
        r'href="((?:\.\./)*)' + re.escape(f"{ccaa}/{provincia}") + r'/([a-z0-9\-]+)/"'
    )
    changed = 0
    for path in ROOT.rglob("*.html"):
        if ".git" in path.parts:
            continue
        rel_parts = path.relative_to(ROOT).parts
        if rel_parts[:3] == (ccaa, provincia, rel_parts[2] if len(rel_parts) > 2 else ""):
            if len(rel_parts) == 4 and rel_parts[2] in slugs:
                continue  # es un stub de redireccion
        html_text = path.read_text(encoding="utf-8")

        def repl(match: re.Match) -> str:
            up, slug = match.group(1), match.group(2)
            if slug not in slugs:
                return match.group(0)
            return f'href="{up}{target_key}/#{slug}"'

        new_text, n = pattern.subn(repl, html_text)
        if n:
            path.write_text(new_text, encoding="utf-8")
            changed += n
    return changed


def update_sitemap(removed_urls: list[str], pillar_url: str) -> int:
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    removed = 0
    for url in removed_urls:
        pattern = re.compile(
            r"\s*<url>\s*<loc>" + re.escape(SITE + url) + r"</loc>.*?</url>", re.S
        )
        xml, n = pattern.subn("", xml)
        removed += n
    xml = re.sub(
        r"(<loc>" + re.escape(pillar_url) + r"</loc>\s*<lastmod>)[\d-]+(</lastmod>)",
        r"\g<1>" + TODAY + r"\g<2>",
        xml,
    )
    path.write_text(xml, encoding="utf-8")
    return removed


def write_cloudflare_list(redirects: list[tuple[str, str]]) -> None:
    """Lista para Bulk Redirects de Cloudflare: GitHub Pages no emite 301."""
    lines = ["source_url,target_url,status_code"]
    lines += [f"{SITE}{src},{dst},301" for src, dst in redirects]
    (ROOT / "redirects-301.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─────────────────────────────────── main ──────────────────────────────────

DATA_FILE = ROOT / "data" / "municipios.json"


def collect() -> list[dict]:
    """Lee la fuente unica de verdad (data/municipios.json).

    Si no existe todavia, cae hacia atras leyendo las fichas HTML. Una vez las
    fichas son stubs de redireccion, el JSON es la unica fuente valida: por eso
    el generador debe poder reconstruir cualquier pilar sin depender del HTML.
    """
    if DATA_FILE.exists():
        records = json.loads(DATA_FILE.read_text(encoding="utf-8"))["municipios"]
        for r in records:
            r["path"] = ROOT / r["ccaa"] / r["provincia_slug"] / r["slug"] / "index.html"
            # Si hay dato oficial del Ministerio, manda sobre el que se publicaba
            # antes: asi el pilar, las fichas y la calculadora dicen lo mismo.
            if r.get("oficial_tipo_urbana"):
                r["tipo_urbano"] = r["oficial_tipo_urbana"]
                r["ibi_urbano"] = pct(r["oficial_tipo_urbana"])
            # Y la poblacion oficial del INE manda sobre la que se publicaba antes:
            # el pilar mostraba 464.751 habitantes en Murcia frente a los 479.405
            # que ya publicaban la ficha y el comparador.
            if r.get("poblacion_oficial"):
                r["poblacion"] = r["poblacion_oficial"]
            rustica = r.get("oficial_tipo_rustica")
            if rustica and 0.3 <= rustica <= 0.9:
                r["tipo_rustico"] = rustica
                r["ibi_rustico"] = pct(rustica)
        return records

    out = []
    for path in sorted(ROOT.glob("*/*/*/index.html")):
        if ".git" in path.parts:
            continue
        data = parse_municipality(path)
        if data:
            out.append(data)
    return out


def unique_paragraph_map(municipalities: list[dict], limit: int = 3) -> dict[str, list[str]]:
    """Conserva por municipio solo los parrafos que no aparecen en ninguna otra ficha."""
    freq: Counter = Counter()
    for m in municipalities:
        for para in m["parrafos"]:
            freq[strip_tags(para)] += 1
    out: dict[str, list[str]] = {}
    for m in municipalities:
        keep = [p for p in m["parrafos"] if freq[strip_tags(p)] == 1]
        out[str(m["path"])] = keep[:limit]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="clave de territorio, p. ej. murcia o galicia/a-coruna")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--solo-comunidades",
        action="store_true",
        dest="solo_comunidades",
        help="un unico pilar por comunidad autonoma con todos sus municipios, sin "
        "crear pilares de provincia que duplicarian su contenido",
    )
    ap.add_argument(
        "--modo",
        choices=("hub", "absorbe"),
        default="hub",
        help="hub: conserva las fichas municipales y las enlaza (recomendado, "
        "protege el long-tail municipal). absorbe: integra las fichas en el pilar "
        "y las convierte en redirecciones.",
    )
    args = ap.parse_args()

    municipalities = collect()
    territories = assign_territories(municipalities, args.solo_comunidades)

    if args.list:
        print(f"Umbral para pilar de provincia: {PROVINCE_PILLAR_THRESHOLD} municipios\n")
        print(f"{'territorio':38} {'nivel':11} municipios")
        for key, t in sorted(territories.items()):
            print(f"/{key + '/':37} {t['nivel']:11} {len(t['municipios'])}")
        print(f"\nTotal pilares territoriales: {len(territories)}"
              f" · municipios absorbidos: {sum(len(t['municipios']) for t in territories.values())}")
        return 0

    keys = list(territories) if args.all else ([args.only] if args.only else [])
    if not keys:
        ap.error("indica --only <territorio>, --all o --list")

    unique_map = unique_paragraph_map(municipalities)
    all_redirects: list[tuple[str, str]] = []

    for key in keys:
        t = territories.get(key)
        if not t:
            print(f"[error] territorio desconocido: {key}")
            continue

        out_path, doc = build_pillar(t, unique_map, args.modo)
        words = len(strip_tags(re.sub(r"(?s)<script.*?</script>", "", doc)).split())
        print(f"\n▸ /{key}/  ({t['nivel']}, {len(t['municipios'])} municipios, ~{words} palabras)")
        if not args.dry_run:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(doc, encoding="utf-8")
            print(f"  pilar escrito en {out_path.relative_to(ROOT)}")

        if args.modo == "hub":
            # Las fichas municipales se mantienen publicadas: nada que redirigir.
            print("  modo hub: las fichas municipales se conservan y el pilar las enlaza")
            continue

        by_prov: dict[str, list[dict]] = defaultdict(list)
        for m in t["municipios"]:
            by_prov[m["provincia_slug"]].append(m)

        removed = []
        for prov, items in by_prov.items():
            slugs = {m["slug"] for m in items}
            for m in items:
                depth = len(m["path"].relative_to(ROOT).parts) - 1
                prefix = "../" * depth
                target_url = f"{SITE}/{key}/#{m['slug']}"
                target_rel = f"{prefix}{key}/#{m['slug']}"
                if not args.dry_run:
                    m["path"].write_text(
                        redirect_stub(m, target_url, target_rel, prefix), encoding="utf-8"
                    )
                removed.append(m["url_antigua"])
                all_redirects.append((m["url_antigua"], target_url))
            if not args.dry_run:
                n = rewrite_internal_links(t["ccaa"], prov, slugs, key)
                print(f"  enlaces internos reescritos ({prov}): {n}")
        print(f"  stubs de redirección: {len(removed)}")

        if not args.dry_run:
            gone = update_sitemap(removed, f"{SITE}/{key}/")
            print(f"  URLs retiradas del sitemap: {gone}")

    if all_redirects and not args.dry_run:
        write_cloudflare_list(all_redirects)
        print(f"\nredirects-301.csv generado con {len(all_redirects)} reglas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
