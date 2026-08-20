#!/usr/bin/env python3
"""Audita el enlazado interno del sitio: grafo, profundidad y huerfanas.

Distingue lo que de verdad cuenta para el SEO:

  * enlaces de PLANTILLA (cabecera y pie): estan en todas las paginas, asi que no
    diferencian nada. Una pagina enlazada solo desde el menu no esta «enlazada».
  * enlaces de CONTENIDO (cuerpo del articulo y barra lateral): son los que
    transmiten contexto y relevancia, porque llevan texto de ancla propio.

Metricas por pagina: entrantes de contenido, dominios de ancla distintos,
salientes, y profundidad de clic desde la portada siguiendo solo enlaces de
contenido (que es el escenario pesimista) y siguiendo todos.

Uso:  python3 scripts/audit_interlinking.py [--nuevas impuesto-circulacion,valor-catastral]
"""
from __future__ import annotations

import argparse
import html
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.parse import unquote, urljoin

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tasasmunicipales.info"
PLANTILLA_RE = re.compile(r"<header\b.*?</header>|<footer\b.*?</footer>", re.S | re.I)
A_RE = re.compile(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)


def paginas() -> list[str]:
    """URLs indexables, tal y como las declara el sitemap."""
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return [u.replace(SITE, "").strip("/") or ""
            for u in re.findall(r"<loc>([^<]+)</loc>", sm)]


def normaliza(origen: str, href: str) -> str | None:
    """Convierte un href relativo en la ruta del sitio, o None si es externo."""
    href = href.split("#")[0].split("?")[0]
    if not href or href.startswith(("http", "mailto:", "tel:", "javascript:")):
        if href.startswith(SITE):
            href = href[len(SITE):]
        else:
            return None
    base = f"/{origen}/" if origen else "/"
    destino = urljoin(base, unquote(href))
    if not destino.endswith("/"):
        if destino.endswith(".html"):
            destino = destino.rsplit("/", 1)[0] + "/"
        else:
            return None
    return destino.strip("/")


def analiza() -> tuple[dict, dict, dict]:
    indexables = set(paginas())
    contenido: dict[str, list[tuple[str, str]]] = defaultdict(list)
    plantilla: dict[str, set[str]] = defaultdict(set)
    for ruta in sorted(indexables):
        archivo = ROOT / ruta / "index.html" if ruta else ROOT / "index.html"
        if not archivo.exists():
            continue
        bruto = archivo.read_text(encoding="utf-8")
        bruto = re.sub(r"(?s)<script.*?</script>", " ", bruto)
        for m in PLANTILLA_RE.finditer(bruto):
            for href, _ in A_RE.findall(m.group(0)):
                destino = normaliza(ruta, href)
                if destino is not None and destino in indexables:
                    plantilla[ruta].add(destino)
        cuerpo = PLANTILLA_RE.sub(" ", bruto)
        for href, texto in A_RE.findall(cuerpo):
            destino = normaliza(ruta, href)
            if destino is None or destino not in indexables or destino == ruta:
                continue
            ancla = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", texto))).strip()
            contenido[ruta].append((destino, ancla))
    return indexables, contenido, plantilla


def profundidad(inicio: str, aristas: dict[str, set[str]], universo: set[str]) -> dict[str, int]:
    dist = {inicio: 0}
    cola = deque([inicio])
    while cola:
        actual = cola.popleft()
        for vecino in aristas.get(actual, ()):
            if vecino in universo and vecino not in dist:
                dist[vecino] = dist[actual] + 1
                cola.append(vecino)
    return dist


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nuevas", default="impuesto-circulacion,valor-catastral")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()
    nuevas = [s for s in args.nuevas.split(",") if s]

    problemas: list[str] = []
    indexables, contenido, plantilla = analiza()
    entrantes: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for origen, enlaces in contenido.items():
        for destino, ancla in enlaces:
            entrantes[destino].append((origen, ancla))

    solo_contenido = {o: {d for d, _ in e} for o, e in contenido.items()}
    todos = {o: solo_contenido.get(o, set()) | plantilla.get(o, set())
             for o in indexables}

    d_cont = profundidad("", solo_contenido, indexables)
    d_todo = profundidad("", todos, indexables)

    print(f"Páginas indexables: {len(indexables)}")
    print(f"Enlaces de contenido: {sum(len(v) for v in contenido.values())}")
    print(f"Enlaces de plantilla (cabecera y pie): "
          f"{sum(len(v) for v in plantilla.values())}")
    print()

    # ── huérfanas y casi huérfanas ──
    huerfanas = sorted(p for p in indexables
                       if p and not entrantes.get(p))
    if huerfanas:
        problemas.append(f"{len(huerfanas)} páginas sin ningún enlace de contenido "
                         f"entrante: {', '.join('/' + h + '/' for h in huerfanas[:5])}")
    print(f"Sin ningún enlace de contenido entrante: {len(huerfanas)}")
    for p in huerfanas[: args.top]:
        print(f"    /{p}/")
    pocas = sorted((len(entrantes.get(p, [])), p) for p in indexables
                   if p and 0 < len(entrantes.get(p, [])) <= 2)
    print(f"Con solo 1 o 2 enlaces de contenido entrantes: {len(pocas)}")
    for n, p in pocas[: args.top]:
        print(f"    /{p}/  ({n})")
    print()

    # ── profundidad de clic ──
    inalcanzables = sorted(p for p in indexables if p not in d_todo)
    if inalcanzables:
        problemas.append(f"{len(inalcanzables)} páginas inalcanzables desde la portada")
    print(f"Inalcanzables desde la portada (con plantilla): {len(inalcanzables)}")
    for p in inalcanzables[: args.top]:
        print(f"    /{p}/")
    reparto = Counter(d_todo.get(p, -1) for p in indexables)
    print("Profundidad de clic (siguiendo también el menú):")
    for k in sorted(reparto):
        etq = "inalcanzable" if k < 0 else f"{k} clic(s)"
        print(f"    {etq:14} {reparto[k]}")
    reparto_c = Counter(d_cont.get(p, -1) for p in indexables)
    print("Profundidad solo con enlaces de contenido:")
    for k in sorted(reparto_c):
        etq = "inalcanzable" if k < 0 else f"{k} clic(s)"
        print(f"    {etq:14} {reparto_c[k]}")
    print()

    # ── páginas más y menos enlazadas ──
    ranking = sorted(((len(entrantes.get(p, [])), p) for p in indexables), reverse=True)
    print("Más enlazadas desde contenido:")
    for n, p in ranking[: args.top]:
        anclas = len({a.lower() for _, a in entrantes.get(p, []) if a})
        print(f"    {n:5d} entrantes · {anclas:3d} anclas distintas · /{p}/")
    print()

    # ── las páginas nuevas, en detalle ──
    for p in nuevas:
        e = entrantes.get(p, [])
        if not e and p not in indexables:
            print(f"[aviso] /{p}/ no está en el sitemap")
            continue
        origenes = Counter(o for o, _ in e)
        anclas = Counter(a for _, a in e if a)
        salientes = solo_contenido.get(p, set())
        print(f"── /{p}/ ──")
        print(f"  entrantes de contenido: {len(e)} desde {len(origenes)} páginas")
        print(f"  profundidad de clic: {d_todo.get(p, '—')} con menú, "
              f"{d_cont.get(p, '—')} solo con contenido")
        print(f"  salientes de contenido: {len(salientes)}")
        print(f"  anclas distintas: {len(anclas)}")
        for a, n in anclas.most_common(6):
            print(f"      {n:4d} × «{a[:80]}»")
        tipos = Counter(
            "portada" if not o else
            "ficha municipal" if o.count("/") == 2 else
            "pilar de comunidad" if o.count("/") == 0 and o in {
                "aragon", "asturias", "cantabria", "castilla-la-mancha",
                "castilla-y-leon", "extremadura", "galicia", "la-rioja", "murcia"}
            else "análisis" if o.startswith("analisis") else "otra guía o página"
            for o in origenes
        )
        for t, n in tipos.most_common():
            print(f"      desde {t}: {n}")
        print()
        if len(e) < 20:
            problemas.append(f"/{p}/ solo recibe {len(e)} enlaces de contenido")
        if len(anclas) < 3:
            problemas.append(f"/{p}/ recibe {len(anclas)} anclas distintas: "
                             f"conviene variar el texto del enlace")

    # ── reciprocidad entre las guías nacionales ──
    guias = ["ibi-2026", "plusvalia", "bonificaciones", "tasa-basuras",
             "impuesto-circulacion", "valor-catastral", "calculadora-ibi",
             "municipios", "comunidades", "analisis", "metodologia"]
    print("Matriz de enlaces de contenido entre las páginas principales")
    print("    (fila enlaza a columna; · = no enlaza)")
    corto = [g[:6] for g in guias]
    print("            " + " ".join(f"{c:>6}" for c in corto))
    for g in guias:
        fila = []
        for h in guias:
            if g == h:
                fila.append("     —")
            else:
                n = sum(1 for d, _ in contenido.get(g, []) if d == h)
                fila.append(f"{n:>6}" if n else "     ·")
        print(f"    {g[:10]:<10}" + " ".join(fila))

    # una pagina principal que no reparte enlaces es un callejon sin salida
    for g in guias:
        if g in indexables and not solo_contenido.get(g):
            problemas.append(f"/{g}/ no tiene ningún enlace de contenido saliente "
                             f"(callejón sin salida)")

    print()
    if problemas:
        print(f"INCIDENCIAS ({len(problemas)}):")
        for x in problemas:
            print(f"  - {x}")
        return 1
    print("Sin incidencias de enlazado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
