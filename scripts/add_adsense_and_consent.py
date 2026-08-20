#!/usr/bin/env python3
"""Inserta el loader de Google AdSense y el bloque de Consent Mode v2 en el <head>
de todas las paginas del sitio.

- Idempotente: si la pagina ya tiene el loader, no la toca.
- El bloque de consentimiento se inyecta ANTES del loader de AdSense, porque
  Consent Mode v2 exige que el estado por defecto ('denied') se declare antes de
  que cargue cualquier etiqueta publicitaria.
- El estado por defecto se calcula leyendo la cookie 'tm_cookie_consent' que
  gestiona /cookie-consent.js, de modo que un visitante que ya acepto no vuelve
  a arrancar en 'denied'.

Uso:  python3 scripts/add_adsense_and_consent.py [--dry-run]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB_ID = "ca-pub-4975903304841229"
LOADER_MARK = "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"
CONSENT_MARK = "tm-consent-default"

SNIPPET = r"""  <!-- Google Consent Mode v2: estado por defecto denegado hasta que el usuario acepte (RGPD) -->
  <script id="tm-consent-default">
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    (function () {
      var m = document.cookie.match('(^|;)\\s*tm_cookie_consent\\s*=\\s*([^;]+)');
      var state = (m ? m.pop() : '') === 'accepted' ? 'granted' : 'denied';
      gtag('consent', 'default', {
        ad_storage: state,
        ad_user_data: state,
        ad_personalization: state,
        analytics_storage: state,
        wait_for_update: 500
      });
    })();
  </script>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=__PUB__" crossorigin="anonymous"></script>
""".replace("__PUB__", PUB_ID)

META_RE = re.compile(r'([ \t]*<meta name="google-adsense-account"[^>]*>\n)')


def process(path: Path, dry_run: bool = False) -> str:
    html = path.read_text(encoding="utf-8")

    if LOADER_MARK in html and CONSENT_MARK in html:
        return "skip"

    # Limpia inserciones parciales de ejecuciones anteriores.
    if CONSENT_MARK in html:
        html = re.sub(
            r'[ \t]*<!-- Google Consent Mode v2[^\n]*\n(?:.*?</script>\n)',
            "",
            html,
            count=1,
            flags=re.S,
        )

    m = META_RE.search(html)
    if m:
        new_html = html[: m.end()] + SNIPPET + html[m.end():]
    elif "</head>" in html:
        new_html = html.replace("</head>", SNIPPET + "</head>", 1)
    else:
        return "no-head"

    if not dry_run:
        path.write_text(new_html, encoding="utf-8")
    return "patched"


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    counts: dict[str, int] = {}
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        result = process(path, dry_run)
        counts[result] = counts.get(result, 0) + 1
        if result == "no-head":
            print(f"  [aviso] sin <head>: {path.relative_to(ROOT)}")
    print("AdSense + Consent Mode v2:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
