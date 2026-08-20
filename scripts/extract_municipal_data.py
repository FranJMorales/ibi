#!/usr/bin/env python3
"""Extrae los datos municipales de las fichas HTML a una FUENTE UNICA DE VERDAD
(data/municipios.json) y audita las contradicciones internas del sitio.

Por que existe este script:
las fichas municipales publicaban el mismo dato en cuatro sitios distintos (la
lista «Datos clave», la meta description, el grafico comparativo y la lista «Otros
municipios» de las demas fichas de la provincia) y esos cuatro sitios NO siempre
coincidian. Con los pilares territoriales cada dato se publica una sola vez, pero
antes hay que dejar constancia de que valor se toma y donde habia conflicto.

Salidas:
    data/municipios.json    datos canonicos por municipio + conflictos detectados
    data/INCONSISTENCIAS.md informe legible para resolver la verificacion

Uso:  python3 scripts/extract_municipal_data.py
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "data" / "municipios.json"
OUT_REPORT = ROOT / "data" / "INCONSISTENCIAS.md"

QUICK_LABELS = {
    "IBI urbano": "ibi_urbano",
    "IBI rústico": "ibi_rustico",
    "Período de pago": "periodo",
    "Basura vivienda": "basuras",
    "Bonif. familia numerosa": "boni_familia",
    "Bonif. energía solar": "boni_solar",
}


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def to_float(value: str | None) -> float | None:
    m = re.search(r"([\d]+[.,]?[\d]*)", value or "")
    return float(m.group(1).replace(",", ".")) if m else None


# Parrafos que NO se llevan al pilar territorial:
#  - los que repiten un dato que ya esta en la lista «Datos clave» de la seccion
#    (el tipo de IBI y el importe de basuras), porque duplicarlo dentro de la misma
#    seccion no aporta nada;
#  - los que apoyan el dato en una cita de boletin oficial que no es comprobable
#    (enlace a la portada del boletin, no al texto de la ordenanza). Hasta que la
#    fuente este verificada con enlace directo, no se publica la cita.
REDUNDANT_PATTERNS = (
    re.compile(r"^El tipo del IBI (urbano|rústico) en "),
    re.compile(r"^El importe de <strong>[\d.,]+ €"),
    re.compile(r"^[\d.,]+ €/año"),
    re.compile(r"href=\"https://www\.(borm|bocyl|boa|bopa|boc|bor|dog|doe|docm)\b"),
)


def is_redundant(paragraph: str) -> bool:
    return any(p.search(paragraph) for p in REDUNDANT_PATTERNS)


def parse(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    name = re.search(r'<div class="bc">.*?<strong>([^<]+)</strong>', raw, re.S)
    if not name:
        return None
    parts = path.relative_to(ROOT).parts

    rec: dict = {
        "slug": parts[2],
        "nombre": name.group(1).strip(),
        "ccaa": parts[0],
        "provincia_slug": parts[1],
        "url_antigua": "/" + "/".join(parts[:-1]) + "/",
    }

    lead = re.search(r'<p class="lead">(.*?)</p>', raw, re.S)
    rec["lead"] = re.sub(r"\s+", " ", lead.group(1)).strip() if lead else ""

    pobl = re.search(r"Población: ([\d.]+) hab\.", raw)
    rec["poblacion"] = int(pobl.group(1).replace(".", "")) if pobl else None

    prov = re.search(r'<p class="meta"><strong>([^·<]+)·\s*([^<]+)</strong>', raw)
    rec["provincia"] = prov.group(2).strip() if prov else ""

    for key in QUICK_LABELS.values():
        rec[key] = ""
    quick = re.search(r'<ul class="quick">(.*?)</ul>', raw, re.S)
    if quick:
        for item in re.findall(r"<li>(.*?)</li>", quick.group(1), re.S):
            label = re.search(r"<strong>([^:]+):</strong>", item)
            if label and label.group(1).strip() in QUICK_LABELS:
                rec[QUICK_LABELS[label.group(1).strip()]] = strip_tags(
                    re.sub(r"<strong>.*?</strong>", "", item, flags=re.S)
                )

    rec["tipo_urbano"] = to_float(rec["ibi_urbano"])
    rec["tipo_rustico"] = to_float(rec["ibi_rustico"])
    rec["basuras_eur"] = to_float(rec["basuras"])

    sede = re.search(
        r"<strong>Sede electrónica del Ayuntamiento:</strong>\s*<a href=\"([^\"]+)\"", raw
    )
    rec["sede"] = sede.group(1) if sede else ""

    boletin = re.search(r"<strong>Ordenanza fiscal:</strong>\s*<a[^>]*>([^<]+)</a>", raw)
    rec["boletin_citado"] = boletin.group(1).strip() if boletin else ""

    consejo = re.search(r"<h2>Consejo práctico[^<]*</h2>\s*<p>(.*?)</p>", raw, re.S)
    rec["consejo"] = re.sub(r"\s+", " ", consejo.group(1)).strip() if consejo else ""

    desc = re.search(r'name="description" content="([^"]+)"', raw)
    rec["_meta_description"] = desc.group(1) if desc else ""

    main = re.search(r"<main>(.*?)</main>", raw, re.S)
    body = main.group(1) if main else raw
    body = re.sub(r'(?s)<section class="sec">\s*<h2>Otros municipios.*?</section>', "", body)
    body = re.sub(r'(?s)<div class="chart-container">.*?</div>\s*</div>', "", body)
    parrafos = []
    for frag in re.findall(r"<p>(.*?)</p>", body, re.S):
        text = re.sub(r"\s+", " ", frag).strip()
        if len(strip_tags(text)) < 160 or strip_tags(text).startswith("→"):
            continue
        if is_redundant(text):
            continue
        parrafos.append(text)
    rec["parrafos"] = parrafos

    # Como cita ESTA ficha a los demas municipios (para el cruce de conflictos).
    rec["_citas"] = {}
    for m in re.finditer(r'/([a-z0-9\-]+)/">([^<]+)</a> — IBI ([\d.]+)%, Basuras ([\d.]+) €/año', raw):
        rec["_citas"][m.group(1)] = {"tipo": float(m.group(3)), "basuras": float(m.group(4))}
    rec["_chart"] = {}
    for m in re.finditer(
        r'<span class="chart-label"[^>]*>([^<]+)</span>.*?<span>([\d.]+)%</span>', raw, re.S
    ):
        rec["_chart"][m.group(1).strip()] = float(m.group(2))
    return rec


def audit(records: list[dict]) -> dict[str, list[str]]:
    by_slug = {r["slug"]: r for r in records}
    by_name = {r["nombre"]: r for r in records}
    conflicts: dict[str, list[str]] = defaultdict(list)

    for r in records:
        # 1. meta description vs datos clave
        desc = r["_meta_description"]
        m = re.search(r"IBI urbano ([\d.]+)%", desc)
        if m and r["tipo_urbano"] and abs(float(m.group(1)) - r["tipo_urbano"]) > 1e-9:
            conflicts[r["slug"]].append(
                f"meta description dice IBI {m.group(1)}% y «Datos clave» dice {r['tipo_urbano']}%"
            )
        m = re.search(r"tasa de basuras ([\d.]+) €", desc)
        if m and r["basuras_eur"] and abs(float(m.group(1)) - r["basuras_eur"]) > 1e-9:
            conflicts[r["slug"]].append(
                f"meta description dice basuras {m.group(1)} € y «Datos clave» dice {r['basuras_eur']} €"
            )

        # 2. como lo citan las demas fichas de su provincia
        for other in records:
            if other["slug"] == r["slug"]:
                continue
            cita = other["_citas"].get(r["slug"])
            if cita and r["tipo_urbano"] and abs(cita["tipo"] - r["tipo_urbano"]) > 1e-9:
                conflicts[r["slug"]].append(
                    f"la ficha de {other['nombre']} lo cita con IBI {cita['tipo']}% "
                    f"(su propia ficha dice {r['tipo_urbano']}%)"
                )
            if cita and r["basuras_eur"] and abs(cita["basuras"] - r["basuras_eur"]) > 1e-9:
                conflicts[r["slug"]].append(
                    f"la ficha de {other['nombre']} lo cita con basuras {cita['basuras']} € "
                    f"(su propia ficha dice {r['basuras_eur']} €)"
                )
            chart = other["_chart"].get(r["nombre"])
            if chart and r["tipo_urbano"] and abs(chart - r["tipo_urbano"]) > 1e-9:
                conflicts[r["slug"]].append(
                    f"el gráfico de la ficha de {other['nombre']} lo dibuja con {chart}%"
                )

    # 3. factcheck.json
    fc_path = ROOT / "data" / "municipal_factcheck.json"
    if fc_path.exists():
        fc = json.loads(fc_path.read_text(encoding="utf-8"))
        for key, entry in fc.items():
            slug = key.split("/")[-1]
            r = by_slug.get(slug)
            if not r:
                continue
            cand = (entry.get("candidate") or {}).get("values") or {}
            val = to_float(cand.get("ibiUrban"))
            if val and r["tipo_urbano"] and abs(val - r["tipo_urbano"]) > 1e-9:
                conflicts[slug].append(
                    f"municipal_factcheck.json registra IBI {val}% frente al {r['tipo_urbano']}% publicado"
                )
            src = (entry.get("candidate") or {}).get("source_title") or ""
            if src and r["boletin_citado"] and src.split(" nº")[0] != r["boletin_citado"].split(" nº")[0]:
                conflicts[slug].append(
                    f"boletín citado en la web «{r['boletin_citado']}» vs «{src}» en factcheck.json"
                )

    # 4. boletines compartidos por demasiados municipios (cita no verificable)
    shared: dict[str, list[str]] = defaultdict(list)
    for r in records:
        if r["boletin_citado"]:
            shared[r["boletin_citado"]].append(r["nombre"])
    for boletin, names in shared.items():
        if len(names) > 3:
            for r in records:
                if r["boletin_citado"] == boletin:
                    conflicts[r["slug"]].append(
                        f"cita «{boletin}» como fuente, igual que otros {len(names) - 1} municipios: "
                        "un único número de boletín no puede contener todas esas ordenanzas"
                    )
    return {k: sorted(set(v)) for k, v in conflicts.items()}


def main() -> int:
    records = [r for r in (parse(p) for p in sorted(ROOT.glob("*/*/*/index.html"))) if r]
    conflicts = audit(records)

    for r in records:
        r["conflictos"] = conflicts.get(r["slug"], [])
        r["verificado"] = False
        r["fuente_url"] = ""
        r["fuente_titulo"] = ""
        r["fecha_verificacion"] = ""
        for tmp in ("_meta_description", "_citas", "_chart"):
            r.pop(tmp, None)

    OUT_JSON.write_text(
        json.dumps({"municipios": records}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    con_conflictos = [r for r in records if r["conflictos"]]
    total = sum(len(r["conflictos"]) for r in records)

    lines = [
        "# Inconsistencias detectadas en los datos municipales",
        "",
        f"Generado automáticamente por `scripts/extract_municipal_data.py`. "
        f"Municipios analizados: **{len(records)}**. "
        f"Municipios con al menos un conflicto: **{len(con_conflictos)}**. "
        f"Conflictos totales: **{total}**.",
        "",
        "Cada conflicto es un caso en el que el sitio publicaba dos valores distintos para "
        "el mismo dato, o citaba una fuente que no es comprobable. Hay que resolverlos "
        "consultando la ordenanza fiscal del ayuntamiento y anotando el enlace directo en "
        "`data/municipios.json` (`fuente_url`, `fuente_titulo`, `fecha_verificacion`, "
        "`verificado: true`).",
        "",
    ]
    for r in sorted(con_conflictos, key=lambda x: (x["ccaa"], x["provincia_slug"], x["nombre"])):
        lines.append(f"## {r['nombre']} ({r['provincia']})")
        lines.append("")
        lines.append(f"Valor publicado: IBI urbano **{r['ibi_urbano']}**, basuras **{r['basuras']}**.")
        lines.append("")
        for c in r["conflictos"]:
            lines.append(f"- {c}")
        lines.append("")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"data/municipios.json  → {len(records)} municipios")
    print(f"data/INCONSISTENCIAS.md → {len(con_conflictos)} municipios con conflicto, {total} conflictos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
