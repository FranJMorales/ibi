#!/usr/bin/env python3
"""Convierte el buscador de la portada en un autocompletado real.

Hasta ahora el buscador de la portada era decorativo: un <input> y un boton sin
una sola linea de codigo detras. Quien escribia «Ourense» y pulsaba la lupa no
iba a ninguna parte.

Este script:
  1. Genera `buscador-municipios.js` con el indice de los 134 municipios
     (nombre, provincia, comunidad y URL) y la logica del autocompletado.
  2. Sustituye el marcado de la portada por un combobox accesible dentro de un
     <form> que, sin JavaScript, lleva al comparador: el buscador nunca deja al
     usuario en un callejon sin salida.
  3. Anade a styles.css los estilos del panel de sugerencias.

El indice pesa unos pocos kB y el script se carga con `defer`, asi que no bloquea
el renderizado de la portada.

Uso:  python3 scripts/build_buscador.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"
JS = ROOT / "buscador-municipios.js"
CSS = ROOT / "styles.css"
HOME = ROOT / "index.html"
ARTICULOS = ("a", "o", "el", "la", "as", "os", "los", "las")


def normaliza(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", limpio.lower()).strip()


def claves(nombre: str, provincia: str) -> tuple[list[str], list[str]]:
    """Devuelve (claves de nombre, claves secundarias).

    La distinción importa para ordenar: quien escribe «Pontevedra» busca el
    municipio de Pontevedra, no los otros diez de esa provincia. Si todas las
    claves pesaran igual, Vigo saldría primero por tener más población.
    """
    base = normaliza(nombre)
    nombres = {base}
    palabras = base.split()
    # «A Coruña» también se busca como «coruña»; «O Porriño», como «porriño».
    if len(palabras) > 1 and palabras[0] in ARTICULOS:
        nombres.add(" ".join(palabras[1:]))
    otras = {normaliza(provincia)}
    # y por cualquier palabra significativa del nombre («santa cruz de bezana»)
    for w in palabras:
        if len(w) > 3 and w not in ARTICULOS and w not in nombres:
            otras.add(w)
    otras -= nombres
    return sorted(x for x in nombres if x), sorted(x for x in otras if x)


def indice() -> list[dict]:
    municipios = json.loads(DATA.read_text(encoding="utf-8"))["municipios"]
    out = []
    for m in sorted(municipios, key=lambda x: -(x.get("poblacion_oficial") or 0)):
        nombre = m["nombre"]
        provincia = m.get("provincia") or ""
        nombres, otras = claves(nombre, provincia)
        out.append({
            "n": nombre,
            "p": provincia,
            "u": f"{m['ccaa']}/{m['provincia_slug']}/{m['slug']}/",
            "k": nombres,
            "o": otras,
        })
    return out


LOGICA = """
/* Autocompletado del buscador de municipios.
   Sin dependencias, sin peticiones: el indice va en este mismo archivo.
   Patron combobox de WAI-ARIA: funciona con raton, teclado y lector de pantalla. */
(function () {
  'use strict';
  var datos = window.TM_BUSCADOR || [];
  var input = document.getElementById('tm-buscador');
  var panel = document.getElementById('tm-sugerencias');
  if (!input || !panel) return;

  var MAX = 8;
  var activo = -1;
  var visibles = [];

  function normaliza(texto) {
    return texto
      .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
      .toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').trim();
  }

  /* Ordena por lo cerca que esta la coincidencia del principio de la palabra:
     quien escribe «our» espera Ourense antes que un municipio que solo lo
     contiene por dentro. */
  function puntua(item, q) {
    var mejor = -1;
    function revisa(claves, bono) {
      for (var i = 0; i < claves.length; i++) {
        var pos = claves[i].indexOf(q);
        if (pos === -1) continue;
        var puntos = (pos === 0 ? 100 : 40 - Math.min(pos, 20)) + bono;
        if (puntos > mejor) mejor = puntos;
      }
    }
    revisa(item.k, 60);          /* coincide con el nombre del municipio */
    revisa(item.o || [], 0);     /* coincide con la provincia o una palabra suelta */
    return mejor;
  }

  function buscar(texto) {
    var q = normaliza(texto);
    if (q.length < 2) return [];
    var res = [];
    for (var i = 0; i < datos.length; i++) {
      var p = puntua(datos[i], q);
      if (p >= 0) res.push({ item: datos[i], p: p, i: i });
    }
    res.sort(function (a, b) { return b.p - a.p || a.i - b.i; });
    return res.slice(0, MAX).map(function (r) { return r.item; });
  }

  function resalta(nombre, q) {
    var pos = normaliza(nombre).indexOf(q);
    if (pos === -1) return escapa(nombre);
    return escapa(nombre.slice(0, pos)) + '<strong>'
      + escapa(nombre.slice(pos, pos + q.length)) + '</strong>'
      + escapa(nombre.slice(pos + q.length));
  }

  function escapa(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function cerrar() {
    panel.hidden = true;
    panel.innerHTML = '';
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    activo = -1;
    visibles = [];
  }

  function marcar(i) {
    var opciones = panel.querySelectorAll('[role="option"]');
    for (var j = 0; j < opciones.length; j++) {
      var sel = j === i;
      opciones[j].setAttribute('aria-selected', sel ? 'true' : 'false');
      opciones[j].classList.toggle('on', sel);
      if (sel) {
        input.setAttribute('aria-activedescendant', opciones[j].id);
        if (opciones[j].scrollIntoView) {
          opciones[j].scrollIntoView({ block: 'nearest' });
        }
      }
    }
    if (i < 0) input.removeAttribute('aria-activedescendant');
    activo = i;
  }

  function pintar(texto) {
    var q = normaliza(texto);
    visibles = buscar(texto);
    if (q.length < 2) { cerrar(); return; }
    var html = '';
    if (visibles.length) {
      for (var i = 0; i < visibles.length; i++) {
        var m = visibles[i];
        html += '<li role="option" id="tm-sug-' + i + '" aria-selected="false"'
          + ' data-url="' + m.u + '">'
          + '<a href="' + m.u + '" tabindex="-1">'
          + '<span class="sug-n">' + resalta(m.n, q) + '</span>'
          + '<span class="sug-p">' + escapa(m.p) + '</span></a></li>';
      }
    } else {
      html = '<li class="sug-vacio" role="option" aria-selected="false"'
        + ' id="tm-sug-vacio" data-url="municipios/">'
        + '<a href="municipios/" tabindex="-1">No tenemos ficha de ese municipio '
        + 'todavía · <strong>ver los ' + datos.length + ' disponibles</strong></a></li>';
    }
    panel.innerHTML = html;
    panel.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    marcar(-1);
  }

  function ir(i) {
    var opciones = panel.querySelectorAll('[role="option"]');
    var destino = null;
    if (i >= 0 && opciones[i]) destino = opciones[i].getAttribute('data-url');
    else if (visibles.length) destino = visibles[0].u;
    else if (opciones.length) destino = opciones[0].getAttribute('data-url');
    if (destino) { window.location.href = destino; return true; }
    return false;
  }

  input.addEventListener('input', function () { pintar(input.value); });
  input.addEventListener('focus', function () {
    if (input.value) pintar(input.value);
  });

  input.addEventListener('keydown', function (e) {
    var total = panel.querySelectorAll('[role="option"]').length;
    if (e.key === 'ArrowDown' && total) {
      e.preventDefault(); marcar((activo + 1) % total);
    } else if (e.key === 'ArrowUp' && total) {
      e.preventDefault(); marcar(activo <= 0 ? total - 1 : activo - 1);
    } else if (e.key === 'Enter') {
      if (!panel.hidden && ir(activo)) e.preventDefault();
    } else if (e.key === 'Escape') {
      cerrar();
    }
  });

  panel.addEventListener('mousedown', function (e) {
    var li = e.target.closest ? e.target.closest('[role="option"]') : null;
    if (li) { e.preventDefault(); window.location.href = li.getAttribute('data-url'); }
  });

  document.addEventListener('click', function (e) {
    if (!panel.contains(e.target) && e.target !== input) cerrar();
  });

  /* El formulario solo actua como red de seguridad: si hay una coincidencia
     clara vamos a su ficha, y si no, al comparador, que es lo que pide el
     action del <form>. */
  var form = input.form;
  if (form) {
    form.addEventListener('submit', function (e) {
      if (visibles.length) { e.preventDefault(); ir(activo); }
    });
  }
})();
"""

MARCADO = """      <!-- buscador:inicio -->
      <div class="search-wrap">
        <form class="search-box" role="search" action="municipios/" method="get">
          <input type="search" id="tm-buscador" name="q"
                 placeholder="Busca tu municipio… ej: Ourense, Vigo, Toledo…"
                 aria-label="Buscar municipio" autocomplete="off"
                 role="combobox" aria-expanded="false" aria-controls="tm-sugerencias"
                 aria-autocomplete="list" aria-describedby="tm-buscador-ayuda">
          <button type="submit" aria-label="Buscar municipio">🔍</button>
        </form>
        <ul id="tm-sugerencias" class="search-sug" role="listbox"
            aria-label="Municipios sugeridos" hidden></ul>
        <p id="tm-buscador-ayuda" class="search-help">Escribe dos letras y te
          sugerimos los municipios disponibles. También puedes buscar por
          provincia.</p>
      </div>
      <!-- buscador:fin -->"""

ESTILOS = """
/* ── BUSCADOR CON AUTOCOMPLETADO (portada) ── */
.search-wrap { position: relative; max-width: 520px; margin: 0 auto; }
.search-wrap .search-box { max-width: none; margin: 0; }
.search-help {
  margin-top: 10px; font-size: 0.76rem; color: rgba(255,255,255,0.6);
  text-align: center;
}
.search-sug {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 80;
  list-style: none; margin: 0; padding: 6px; text-align: left;
  background: #fff; border-radius: 6px;
  box-shadow: 0 12px 34px rgba(0,0,0,0.28);
  max-height: 340px; overflow-y: auto;
}
.search-sug li { border-radius: 4px; }
.search-sug a {
  display: flex; justify-content: space-between; align-items: baseline; gap: 12px;
  padding: 9px 12px; color: var(--ink); font-size: 0.9rem;
}
.search-sug li.on, .search-sug li:hover { background: var(--accent); }
.search-sug li.on a, .search-sug li:hover a { color: #fff; }
.search-sug .sug-n strong { color: var(--accent); font-weight: 700; }
.search-sug li.on .sug-n strong, .search-sug li:hover .sug-n strong { color: #fff; }
.search-sug .sug-p { font-size: 0.75rem; color: var(--mid); white-space: nowrap; }
.search-sug li.on .sug-p, .search-sug li:hover .sug-p { color: rgba(255,255,255,0.85); }
.search-sug .sug-vacio a { font-size: 0.84rem; color: var(--mid); }
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = indice()
    js = ("/* Índice de búsqueda de municipios.\n"
          "   GENERADO AUTOMÁTICAMENTE por scripts/build_buscador.py desde\n"
          "   data/municipios.json. No editar a mano. */\n"
          "window.TM_BUSCADOR = "
          + json.dumps(items, ensure_ascii=False, separators=(",", ":"))
          + ";\n" + LOGICA)
    if not args.dry_run:
        JS.write_text(js, encoding="utf-8")
    print(f"  buscador-municipios.js  ({len(items)} municipios, "
          f"{len(js.encode()) // 1024} kB)")

    texto = HOME.read_text(encoding="utf-8")
    original = texto
    nuevo, n = re.subn(
        r'[ \t]*<!-- buscador:inicio -->.*?<!-- buscador:fin -->'
        r'|[ \t]*<div class="search-box"[^>]*>.*?</div>',
        MARCADO,
        texto,
        count=1,
        flags=re.S,
    )
    if n:
        texto = nuevo
    if "buscador-municipios.js" not in texto:
        texto = texto.replace(
            "</body>",
            '<script src="buscador-municipios.js" defer></script>\n</body>', 1)
    if texto != original and not args.dry_run:
        HOME.write_text(texto, encoding="utf-8")
    print(f"  portada: {'marcado actualizado' if n else 'marcado ya presente'}")

    css = CSS.read_text(encoding="utf-8")
    if ".search-sug" not in css and not args.dry_run:
        CSS.write_text(css.rstrip() + "\n" + ESTILOS, encoding="utf-8")
        print("  styles.css: estilos del panel de sugerencias añadidos")
    else:
        print("  styles.css: ya tenía los estilos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
