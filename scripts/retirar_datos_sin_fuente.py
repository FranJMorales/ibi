#!/usr/bin/env python3
"""Retira de data/municipios.json los dos datos que no tienen fuente: el importe
de la tasa de basuras y el periodo de pago.

Por que se retira la tasa de basuras
------------------------------------
El campo `basuras_eur` estaba en 134 de 134 municipios (rango 78-155 EUR,
mediana 105 EUR) sin ninguna fuente asociada: no habia URL, ni boletin, ni
fecha de comprobacion, a diferencia de los tipos de IBI (Ministerio de
Hacienda), la poblacion (INE) o los coeficientes de plusvalia. Se publicaba
con la etiqueta «orientativo», que aparecia hasta cinco veces en la misma
ficha.

Intentos de verificacion, todos fallidos (julio de 2026):

  1. Ordenanzas municipales: se publican como PDF (por ejemplo
     mirandadeebro.es/documentacion/fiscales-ordenanza-recogida-de-basuras/).
     La herramienta de descarga solo admite text/html, text/* y
     application/json, asi que el PDF no se puede leer.
  2. Sedes electronicas: sede.santander.es/content/tasa-gestion-residuos-0
     responde HTTP 500.
  3. Boletines oficiales autonomicos: sede.asturias.es (BOPA) falla en la
     verificacion del certificado TLS ("unable to get local issuer
     certificate").
  4. Buscador web: solo devuelve prensa (RTVE, 20minutos, idealista,
     diariosur). No es fuente primaria y no da la cifra por municipio.

Y no existe fuente estatal agregada: el art. 11.5 de la Ley 7/2022 obliga a
comunicar la tasa y sus calculos «a las autoridades competentes de las
comunidades autonomas», no al Estado. La consulta de informacion impositiva
del Ministerio de Hacienda cubre impuestos locales (IBI, IAE, IVTM, ICIO,
IIVTNU), no tasas.

Conclusion: publicar la cifra es publicar un dato inventado. Se retira y en su
lugar cada ficha explica el marco legal verificado (art. 11.3 y 11.4 de la Ley
7/2022) y como localizar la tarifa propia. El valor anterior queda registrado
en `basuras_retirado_eur` para no perder el rastro de lo que se publico.

Uso:  python3 scripts/retirar_basuras.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "municipios.json"

MOTIVO = (
    "no publicado: sin fuente primaria accesible (ordenanzas en PDF, sedes "
    "caidas, sin registro estatal; art. 11.5 Ley 7/2022 obliga a comunicar la "
    "tasa a la comunidad autonoma, no al Estado)"
)
# El periodo de pago tiene el mismo problema y una consecuencia peor: una fecha
# equivocada puede costarle al lector el recargo del art. 28 LGT. Solo 3 valores
# distintos para 134 municipios (117 identicos) delataban que no salian de las
# ordenanzas. Se sustituye por el plazo por defecto del art. 62.3 LGT, que si es
# verificable, y por el enlace al organismo que publica el calendario.
MOTIVO_PERIODO = (
    "no publicado: las fechas de cobro las aprueba cada ayuntamiento u organismo "
    "provincial cada ejercicio y no hay fuente estatal que las recoja; se publica "
    "el plazo por defecto del art. 62.3 LGT"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    n = 0
    for m in payload["municipios"]:
        limpio = (
            m.get("basuras_eur") is None
            and m.get("basuras_estado") == MOTIVO
            and not m.get("periodo")
            and m.get("periodo_estado") == MOTIVO_PERIODO
        )
        if limpio:
            continue
        if m.get("basuras_eur") is not None:
            m["basuras_retirado_eur"] = m["basuras_eur"]
        m["basuras_eur"] = None
        m["basuras"] = ""
        m["basuras_estado"] = MOTIVO
        if m.get("periodo"):
            m["periodo_retirado"] = m["periodo"]
        m["periodo"] = ""
        m["periodo_estado"] = MOTIVO_PERIODO
        n += 1

    print(f"municipios con datos sin fuente retirados: {n}")
    if not args.dry_run and n:
        DATA.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"escrito {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
