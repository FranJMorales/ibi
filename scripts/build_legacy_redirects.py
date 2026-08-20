#!/usr/bin/env python3
"""Recupera las URLs antiguas que devuelven 404 y siguen posicionadas en Google.

Search Console (ultimos 3 meses) muestra que el sitio tuvo subpaginas por
municipio del tipo /{ccaa}/{provincia}/{municipio}/{tema}-{municipio}/ que se
eliminaron en algun rebuild anterior. Siguen indexadas, siguen recibiendo clics y
hoy devuelven 404: cada visita que llega ahi se pierde.

Este script crea una pagina de redireccion para cada una hacia la ficha del
municipio correspondiente (canonical + meta refresh + JS + enlace visible) y las
anade a redirects-301.csv para poder convertirlas en 301 reales con Cloudflare.

Los datos de Search Console de cada URL quedan documentados aqui para poder
priorizar: hay URLs en posicion 3-5 con CTR superior al 12%.

Uso:  python3 scripts/build_legacy_redirects.py [--dry-run]
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"

# ruta antigua (404), clics, impresiones, posicion media — datos de Search Console
LEGACY: list[tuple[str, int, int, float]] = [
    ("castilla-la-mancha/guadalajara/azuqueca-de-henares/ibi-2026-azuqueca-de-henares", 8, 132, 4.67),
    ("galicia/a-coruna/ferrol/plusvalia-municipal-ferrol", 4, 31, 3.52),
    ("extremadura/badajoz/almendralejo/ibi-2026-almendralejo", 2, 62, 5.13),
    ("aragon/teruel/teruel/plusvalia-municipal-teruel", 2, 14, 4.29),
    ("galicia/ourense/o-carballino/ibi-2026-o-carballino", 1, 47, 5.04),
    ("castilla-la-mancha/cuenca/tarancon/ibi-2026-tarancon", 1, 5, 5.60),
    ("galicia/pontevedra/pontevedra/como-pagar-ibi-pontevedra", 1, 16, 6.75),
    ("galicia/a-coruna/ferrol/tasa-basuras-2026-ferrol", 1, 5, 2.80),
    ("extremadura/badajoz/don-benito/ibi-2026-don-benito", 1, 2, 1.00),
    ("galicia/a-coruna/ferrol/reclamar-tasa-basura-ferrol", 1, 1, 9.00),
    ("extremadura/caceres/navalmoral-de-la-mata/ibi-2026-navalmoral-de-la-mata", 0, 55, 6.00),
    ("galicia/pontevedra/pontevedra/ibi-2026-pontevedra", 0, 14, 4.71),
    ("castilla-la-mancha/ciudad-real/alcazar-de-san-juan/tasa-basuras-2026-alcazar-de-san-juan", 0, 7, 5.57),
    ("castilla-la-mancha/cuenca/cuenca/plusvalia-municipal-cuenca", 0, 7, 7.86),
    ("extremadura/badajoz/don-benito/tasa-basuras-2026-don-benito", 0, 6, 7.00),
    ("extremadura/caceres/navalmoral-de-la-mata/como-pagar-ibi-navalmoral-de-la-mata", 0, 5, 7.80),
    ("extremadura/caceres/plasencia/bonificaciones-ibi-plasencia", 0, 4, 3.50),
    ("castilla-la-mancha/ciudad-real/tomelloso/reclamar-tasa-basura-tomelloso", 0, 4, 6.50),
    ("castilla-la-mancha/albacete/hellin/plusvalia-municipal-hellin", 0, 3, 4.67),
    ("extremadura/badajoz/zafra/ibi-2026-zafra", 0, 2, 3.50),
    ("extremadura/badajoz/villanueva-de-la-serena/plusvalia-municipal-villanueva-de-la-serena", 0, 2, 6.00),
    ("extremadura/badajoz/montijo/ibi-2026-montijo", 0, 2, 7.00),
    ("aragon/huesca/barbastro/bonificaciones-ibi-barbastro", 0, 1, 2.00),
    ("asturias/asturias/castrillon/plusvalia-municipal-castrillon", 0, 1, 6.00),
    ("murcia/murcia/cieza/bonificaciones-ibi-cieza", 0, 1, 6.00),
]

TEMAS = {
    "ibi-2026": "el IBI",
    "plusvalia-municipal": "la plusvalía municipal",
    "tasa-basuras-2026": "la tasa de basuras",
    "como-pagar-ibi": "el pago del IBI",
    "bonificaciones-ibi": "las bonificaciones del IBI",
    "reclamar-tasa-basura": "las reclamaciones de la tasa de basuras",
}


def municipio_nombre(ficha: Path) -> str:
    if not ficha.exists():
        return ""
    match = re.search(r'<div class="bc">.*?<strong>([^<]+)</strong>', ficha.read_text(encoding="utf-8"), re.S)
    return match.group(1).strip() if match else ""


def tema_de(slug_final: str, municipio_slug: str) -> str:
    tema = slug_final[: -(len(municipio_slug) + 1)] if slug_final.endswith("-" + municipio_slug) else slug_final
    return TEMAS.get(tema, "los impuestos municipales")


def stub(nombre: str, tema: str, destino_abs: str, destino_rel: str, prefix: str) -> str:
    nombre_html = html.escape(nombre)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nombre_html}: IBI, basuras y plusvalía 2026 — TasasMunicipales</title>
  <link rel="canonical" href="{destino_abs}">
  <meta http-equiv="refresh" content="0; url={destino_rel}">
  <link rel="stylesheet" href="{prefix}styles.css">
  <script>window.location.replace("{destino_rel}");</script>
</head>
<body>
<div class="wrap" style="padding:60px 24px;text-align:center">
  <h1>Esta información se ha unificado</h1>
  <p class="lead">Todo lo relativo a {tema} en {nombre_html} está ahora en una sola página, junto con el resto de sus datos fiscales.</p>
  <p><a href="{destino_rel}" style="color:var(--accent);font-weight:600">Ir a la ficha fiscal de {nombre_html} →</a></p>
</div>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    creadas = saltadas = 0
    reglas: list[tuple[str, str]] = []
    clics = impresiones = 0

    for ruta, c, i, pos in sorted(LEGACY, key=lambda x: -x[1]):
        partes = ruta.split("/")
        municipio_slug = partes[2]
        ficha_dir = ROOT / "/".join(partes[:3])
        ficha = ficha_dir / "index.html"
        if not ficha.exists():
            print(f"  [aviso] no existe la ficha destino de {ruta}")
            saltadas += 1
            continue

        nombre = municipio_nombre(ficha) or municipio_slug.replace("-", " ").title()
        tema = tema_de(partes[3], municipio_slug)
        destino_abs = f"{SITE}/{'/'.join(partes[:3])}/"
        destino_rel = "../"
        prefix = "../" * len(partes)

        salida = ROOT / ruta / "index.html"
        if not args.dry_run:
            salida.parent.mkdir(parents=True, exist_ok=True)
            salida.write_text(stub(nombre, tema, destino_abs, destino_rel, prefix), encoding="utf-8")
        creadas += 1
        clics += c
        impresiones += i
        reglas.append((f"/{ruta}/", destino_abs))
        print(f"  {c:3} clics {i:5} impr  pos {pos:5.2f}  /{ruta}/  ->  /{'/'.join(partes[:3])}/")

    if not args.dry_run and reglas:
        csv_path = ROOT / "redirects-301.csv"
        lineas = ["source_url,target_url,status_code"]
        if csv_path.exists():
            existentes = [
                l for l in csv_path.read_text(encoding="utf-8").splitlines()[1:]
                if l.strip() and not any(l.startswith(SITE + src) for src, _ in reglas)
            ]
            lineas += existentes
        lineas += [f"{SITE}{src},{dst},301" for src, dst in reglas]
        csv_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(
        f"\nredirecciones creadas: {creadas} (saltadas: {saltadas}) · "
        f"tráfico recuperado en los últimos 3 meses: {clics} clics y {impresiones} impresiones"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
