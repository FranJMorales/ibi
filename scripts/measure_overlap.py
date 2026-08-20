#!/usr/bin/env python3
"""Mide el solapamiento textual entre las fichas municipales.

Uso:
    python3 scripts/measure_overlap.py [--top 20] [--git-ref main]

Calcula:
  * Porcentaje medio de shingles (5-gramas) de cada ficha que aparecen en
    al menos otra ficha -> "solapamiento".
  * Frases (sentencias) repetidas en varias fichas, ordenadas por apariciones.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from collections import Counter
from typing import NamedTuple
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHINGLE = 5


def municipal_pages() -> list[Path]:
    data = json.loads((ROOT / "data" / "municipios.json").read_text(encoding="utf-8"))
    rows = data["municipios"] if isinstance(data, dict) else data
    paths = []
    for row in rows:
        ca = row.get("ccaa")
        prov = row.get("provincia_slug")
        mun = row.get("slug")
        if not (ca and prov and mun):
            continue
        slug = f"/{ca}/{prov}/{mun}/"
        p = ROOT / slug.strip("/") / "index.html"
        if p.exists():
            paths.append(p)
    return paths


TAG_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
STRIP_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def visible_text(raw: str) -> str:
    raw = TAG_RE.sub(" ", raw)
    raw = STRIP_RE.sub(" ", raw)
    raw = html.unescape(raw)
    return WS_RE.sub(" ", raw).strip()


def normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^0-9a-záéíóúüñç%.,;:/()\-\s]", " ", text)
    return WS_RE.sub(" ", text).strip()


def tokens(text: str) -> list[str]:
    return normalise(text).split()


def shingles(words: list[str], n: int = SHINGLE) -> set[str]:
    return {" ".join(words[i : i + n]) for i in range(max(0, len(words) - n + 1))}


SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def sentences(text: str) -> list[str]:
    out = []
    for chunk in SENT_SPLIT.split(text):
        chunk = normalise(chunk).strip()
        if len(chunk.split()) >= 8:
            out.append(chunk)
    return out


MAIN_RE = re.compile(r"<main>(.*?)</main>", re.S)


def main_text(raw: str) -> str:
    m = MAIN_RE.search(raw)
    return visible_text(m.group(1) if m else raw)


class Metricas(NamedTuple):
    solapamiento: float
    plantilla: float
    par_maximo: float
    frases: list
    apariciones: int


def analyse(pages: dict[str, str]) -> "Metricas":
    docs = {name: tokens(text) for name, text in pages.items()}
    counts: Counter[str] = Counter()
    doc_shingles = {}
    for name, words in docs.items():
        sh = shingles(words)
        doc_shingles[name] = sh
        counts.update(sh)

    ratios = []
    boiler = []
    total = len(doc_shingles)
    umbral = max(2, int(total * 0.8))
    for name, sh in doc_shingles.items():
        if not sh:
            continue
        shared = sum(1 for s in sh if counts[s] > 1)
        ratios.append(shared / len(sh))
        boiler.append(sum(1 for s in sh if counts[s] >= umbral) / len(sh))
    overlap = 100 * sum(ratios) / len(ratios) if ratios else 0.0
    boilerplate = 100 * sum(boiler) / len(boiler) if boiler else 0.0

    sent_counts: Counter[str] = Counter()
    for name, text in pages.items():
        for s in set(sentences(text)):
            sent_counts[s] += 1
    repeated = [(c, s) for s, c in sent_counts.items() if c >= 20]
    repeated.sort(reverse=True)
    total_appearances = sum(c for c, _ in repeated)

    # Similitud máxima con otra ficha (lo que mira un detector de duplicados).
    nombres = list(doc_shingles)
    maximos = []
    for i, a in enumerate(nombres):
        sa = doc_shingles[a]
        if not sa:
            continue
        mejor = 0.0
        for j, b in enumerate(nombres):
            if i == j:
                continue
            sb = doc_shingles[b]
            if not sb:
                continue
            inter = len(sa & sb)
            if not inter:
                continue
            jac = inter / len(sa | sb)
            if jac > mejor:
                mejor = jac
        maximos.append(mejor)
    par_max = 100 * sum(maximos) / len(maximos) if maximos else 0.0

    return Metricas(overlap, boilerplate, par_max, repeated, total_appearances)


def load_from_git(ref: str, rel_paths: list[str]) -> dict[str, str]:
    pages = {}
    for rel in rel_paths:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue
        pages[rel] = main_text(raw)
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--git-ref", default=None, help="comparar contra una rama/commit")
    args = ap.parse_args()

    paths = municipal_pages()
    rel_paths = [str(p.relative_to(ROOT)) for p in paths]
    raws = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in rel_paths}
    pages = {rel: main_text(raw) for rel, raw in raws.items()}
    full = {rel: visible_text(raw) for rel, raw in raws.items()}

    m = analyse(pages)
    overlap, repeated, appearances = m.solapamiento, m.frases, m.apariciones
    mf = analyse(full)
    avg_words = sum(len(t.split()) for t in pages.values()) / len(pages)
    print(f"Fichas analizadas: {len(pages)}")
    print(f"Palabras medias del contenido principal: {avg_words:.0f}")
    print(f"Texto que aparece en otra ficha (shingles de {SHINGLE}): {overlap:.1f}%")
    print(f"Texto de plantilla (en >=80% de las fichas): {m.plantilla:.1f}%")
    print(f"Similitud máxima con otra ficha (Jaccard): {m.par_maximo:.1f}%")
    print(f"Página completa, texto repetido: {mf.solapamiento:.1f}%  "
          f"plantilla: {mf.plantilla:.1f}%")
    print(f"Frases repetidas (>=20 fichas): {len(repeated)} distintas, {appearances} apariciones")
    print()
    for count, sent in repeated[: args.top]:
        preview = sent[:110] + ("..." if len(sent) > 110 else "")
        print(f"  {count:4d}  {preview}")

    if args.git_ref:
        base_pages = load_from_git(args.git_ref, rel_paths)
        if base_pages:
            b = analyse(base_pages)
            b_words = sum(len(t.split()) for t in base_pages.values()) / len(base_pages)
            print()
            print(f"[{args.git_ref}] fichas: {len(base_pages)}  palabras: {b_words:.0f}")
            print(f"[{args.git_ref}] repetido: {b.solapamiento:.1f}%   "
                  f"plantilla: {b.plantilla:.1f}%   "
                  f"similitud máxima: {b.par_maximo:.1f}%   "
                  f"frases repetidas: {len(b.frases)} ({b.apariciones} apariciones)")
            print(f"Delta repetido: {overlap - b.solapamiento:+.1f}  "
                  f"plantilla: {m.plantilla - b.plantilla:+.1f}  "
                  f"similitud máxima: {m.par_maximo - b.par_maximo:+.1f}  "
                  f"frases: {appearances - b.apariciones:+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
