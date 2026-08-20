#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py
==============
Generador del sitio TasasMunicipales.info.

Este script es la única fuente de verdad del sitio:
  - Mantiene la lista completa de CCAA, provincias y municipios.
  - Genera/actualiza las páginas de municipio (plantilla rica tipo Plasencia/Monzón).
  - Regenera los hubs (home, CCAA, /municipios/, /provincias/, /comunidades/).
  - Regenera sitemap.xml.
  - Arregla el interlinking entre municipios vecinos de la misma provincia.

Uso:
    python3 scripts/build_site.py          # construye todo
    python3 scripts/build_site.py --new    # solo crea los municipios NUEVOS que faltan
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://tasasmunicipales.info"
TODAY = date.today().isoformat()

# ────────────────────────────────────────────────────────────────
#  DATOS: fuente única de verdad
# ────────────────────────────────────────────────────────────────
# Estructura por municipio:
#   slug, nombre, ibi_urb, ibi_rus, basuras, pob, pobann (año),
#   familia_numerosa, solar, boletin, boletin_url, ayto_sede,
#   existing=True/False  → si ya existe la página, no se sobreescribe
#   lead (párrafo del hero), consejo (práctico), coef_plusv
#
# Datos orientativos. El sitio ya declara que son “orientativos”.

CCAA = {
    "aragon": {
        "nombre": "Aragón",
        "gen_hub": True,
        "boletin": ("BOA", "https://www.boa.aragon.es", "nº 246, 20/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "huesca": {
                "nombre": "Huesca",
                "municipios": [
                    dict(slug="huesca", nombre="Huesca", ibi=0.60, ibir=0.48, basuras=102, pob=53271,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Huesca, capital de provincia con 53.271 habitantes (INE 2025), combina patrimonio medieval (Catedral, Palacio de los Reyes) con un mercado residencial urbano estable. Su casco histórico y las zonas nuevas como San Jorge o Santo Domingo reflejan valores catastrales variados.",
                         consejo="Huesca aplica bonificaciones escalonadas según superficie útil del inmueble. Verifica en el recibo si se está aplicando la reducción por vivienda habitual de menos de 90 m² (hasta 25%)."),
                    dict(slug="monzon", nombre="Monzón", ibi=0.58, ibir=0.47, basuras=88, pob=17276,
                         pobann=2025, fn=20, solar=25, existing=True),
                    dict(slug="jaca", nombre="Jaca", ibi=0.57, ibir=0.47, basuras=98, pob=13425,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="barbastro", nombre="Barbastro", ibi=0.59, ibir=0.47, basuras=90, pob=17022,
                         pobann=2025, fn=25, solar=25, existing=True),
                    dict(slug="fraga", nombre="Fraga", ibi=0.60, ibir=0.48, basuras=95, pob=15208,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Fraga, capital del Bajo Cinca, es referencia agroalimentaria (fruta dulce) en la provincia de Huesca con 15.208 habitantes (INE 2025). Su mercado residencial está dinamizado por el eje de la AP-2 y la proximidad a Lleida.",
                         consejo="En Fraga coexisten vivienda urbana y amplia masa rústica (frutales). Revisa tu IBI rústico si tienes parcela: el tipo del 0,48% se aplica sobre el valor catastral rústico que suele estar infravalorado."),
                    dict(slug="sabinanigo", nombre="Sabiñánigo", ibi=0.58, ibir=0.47, basuras=96, pob=9186,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Sabiñánigo, cabecera del Alto Gállego con 9.186 habitantes (INE 2025), es un municipio industrial y puerta del Pirineo oscense. Su proximidad a Formigal y Panticosa eleva la demanda de segunda residencia.",
                         consejo="Si tienes una segunda residencia en Sabiñánigo usada en temporada de esquí, recuerda que NO aplica la bonificación de vivienda habitual. Consulta la tarifa diferenciada de basuras para uso vacacional."),
                    dict(slug="binefar", nombre="Binéfar", ibi=0.59, ibir=0.47, basuras=92, pob=9769,
                         pobann=2025, fn=25, solar=25, existing=False,
                         lead="Binéfar, en La Litera, es el tercer municipio más poblado de Huesca (9.769 hab., INE 2025). Su tejido agroindustrial (cárnicas, lácteos) sostiene un mercado inmobiliario estable y asequible.",
                         consejo="Binéfar mantiene un padrón catastral reciente, por lo que los valores reflejan bien el mercado. La bonificación por instalación de placas solares (25% durante 3 años) es especialmente rentable en esta comarca de alta irradiación."),
                ],
            },
            "teruel": {
                "nombre": "Teruel",
                "municipios": [
                    dict(slug="teruel", nombre="Teruel", ibi=0.58, ibir=0.47, basuras=95, pob=35675,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="alcaniz", nombre="Alcañiz", ibi=0.60, ibir=0.48, basuras=98, pob=16248,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Alcañiz, capital del Bajo Aragón y sede de MotorLand, es la segunda ciudad de Teruel con 16.248 habitantes (INE 2025). Su mercado inmobiliario se beneficia del turismo cultural (Concatedral) y motor.",
                         consejo="Alcañiz revisó su ordenanza fiscal en 2024 para incluir bonificaciones ampliadas por instalación de autoconsumo solar. Guarda el boletín de enganche y factura del instalador para solicitarla el año siguiente."),
                ],
            },
            "zaragoza": {
                "nombre": "Zaragoza",
                "municipios": [
                    dict(slug="zaragoza", nombre="Zaragoza", ibi=0.625, ibir=0.50, basuras=118, pob=686986,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Zaragoza, capital de Aragón con 686.986 habitantes (INE 2025), es la quinta ciudad española por población. Su diversidad inmobiliaria es enorme: desde pisos de 40.000 € de valor catastral en Delicias o Las Fuentes hasta viviendas unifamiliares de >150.000 € en Casablanca o Montecanal.",
                         consejo="Zaragoza capital aplica una bonificación del 5% por domiciliación del IBI y fracciona automáticamente en dos plazos (mayo y octubre). Si domicilias antes del 28 de febrero, consigues descuento y cuota fraccionada sin intereses."),
                    dict(slug="calatayud", nombre="Calatayud", ibi=0.60, ibir=0.48, basuras=95, pob=19626,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="utebo", nombre="Utebo", ibi=0.58, ibir=0.47, basuras=90, pob=19613,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="ejea-de-los-caballeros", nombre="Ejea de los Caballeros", ibi=0.59, ibir=0.47, basuras=92, pob=16384,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="tarazona", nombre="Tarazona", ibi=0.60, ibir=0.48, basuras=90, pob=10469,
                         pobann=2025, fn=25, solar=30, existing=True),
                ],
            },
        },
    },
    "asturias": {
        "nombre": "Asturias",
        "gen_hub": True,
        "boletin": ("BOPA", "https://sede.asturias.es/bopa", "nº 245, 19/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "asturias": {
                "nombre": "Asturias",
                "municipios": [
                    dict(slug="gijon", nombre="Gijón", ibi=0.65, ibir=0.55, basuras=118, pob=268900,
                         pobann=2025, fn=40, solar=30, existing=True),
                    dict(slug="oviedo", nombre="Oviedo", ibi=0.67, ibir=0.55, basuras=124, pob=219910,
                         pobann=2025, fn=40, solar=30, existing=True),
                    dict(slug="aviles", nombre="Avilés", ibi=0.64, ibir=0.55, basuras=110, pob=77176,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="siero", nombre="Siero", ibi=0.63, ibir=0.55, basuras=108, pob=51906,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="langreo", nombre="Langreo", ibi=0.66, ibir=0.55, basuras=106, pob=38142,
                         pobann=2025, fn=30, solar=25, existing=True),
                    dict(slug="mieres", nombre="Mieres", ibi=0.64, ibir=0.55, basuras=105, pob=37062,
                         pobann=2025, fn=30, solar=25, existing=True),
                    dict(slug="castrillon", nombre="Castrillón", ibi=0.62, ibir=0.55, basuras=98, pob=22486,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="llanes", nombre="Llanes", ibi=0.63, ibir=0.55, basuras=115, pob=13619,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Llanes, en la costa oriental asturiana, es el municipio con mayor peso turístico del oriente (13.619 hab., INE 2025). Sus 30 km de costa y núcleos como Poo, Celorio o Barro concentran una alta proporción de segunda residencia de propietarios del País Vasco y Madrid.",
                         consejo="En Llanes, si tu vivienda es segunda residencia, la tasa de basuras para uso vacacional puede ser superior. Revisa si tu inmueble está clasificado como vivienda habitual en el padrón: el ahorro puede ser de 25–40 €/año."),
                    dict(slug="cangas-de-onis", nombre="Cangas de Onís", ibi=0.60, ibir=0.55, basuras=102, pob=6269,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Cangas de Onís, capital histórica del Reino de Asturias y puerta de los Picos de Europa, cuenta con 6.269 habitantes (INE 2025). Su mercado inmobiliario está dominado por alojamientos turísticos y segundas residencias.",
                         consejo="Cangas de Onís aplica una tarifa específica para viviendas vacías o en alquiler turístico. Si alquilas en plataformas tipo Airbnb, asegúrate de haber comunicado el uso al Ayuntamiento para evitar sanciones."),
                    dict(slug="navia", nombre="Navia", ibi=0.62, ibir=0.55, basuras=100, pob=8284,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Navia, en la costa occidental asturiana, tiene 8.284 habitantes (INE 2025) y combina tejido pesquero, industrial (celulosa) y turístico. Sus playas (Frexulfe, Moro) elevan la presión residencial estival.",
                         consejo="En Navia, verifica si tu inmueble está dentro de la zona afectada por la última ponencia parcial catastral (2019). Puedes pedir certificación actualizada en Catastro para identificar errores de clasificación."),
                    dict(slug="villaviciosa", nombre="Villaviciosa", ibi=0.61, ibir=0.55, basuras=102, pob=13830,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Villaviciosa, conocida como la Capital de la Manzana y de la Sidra, cuenta con 13.830 habitantes (INE 2025). Su costa con playa de Rodiles y el estuario atraen residentes del centro de Asturias.",
                         consejo="Villaviciosa dispone de bonificación específica para inmuebles en zonas de reserva natural (Ría de Villaviciosa). Si tu inmueble está en el entorno protegido, solicita la bonificación patrimonial (hasta 25%)."),
                    dict(slug="lena", nombre="Lena", ibi=0.62, ibir=0.55, basuras=98, pob=11157,
                         pobann=2025, fn=25, solar=25, existing=False,
                         lead="Lena, en la cuenca del Huerna (11.157 hab., INE 2025), combina industria minera tradicional (en reconversión) con un corredor de comunicación estratégico hacia León. Su mercado inmobiliario es asequible con gran potencial para reformas.",
                         consejo="Lena mantiene bonificaciones específicas para inmuebles tradicionales en núcleos rurales con rehabilitación energética. Si vas a reformar, consulta antes la tipología protegida en el planeamiento urbanístico."),
                    dict(slug="grado", nombre="Grado", ibi=0.61, ibir=0.55, basuras=100, pob=9831,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Grado, capital de una histórica comarca agropecuaria, cuenta con 9.831 habitantes (INE 2025). Su ubicación estratégica entre Oviedo y el occidente asturiano, unida a su famoso mercado semanal, mantiene activo el mercado de la vivienda.",
                         consejo="En Grado existe ordenanza específica que bonifica hasta el 25% del IBI a viviendas rehabilitadas en los últimos 5 años mediante obra mayor. Conserva licencia y facturas al menos hasta que apliques la bonificación."),
                ],
            },
        },
    },
    "castilla-la-mancha": {
        "nombre": "Castilla-La Mancha",
        "gen_hub": True,
        "boletin": ("DOCM", "https://docm.jccm.es", "nº 244, 19/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "albacete": {
                "nombre": "Albacete",
                "municipios": [
                    dict(slug="albacete", nombre="Albacete", ibi=0.60, ibir=0.48, basuras=110, pob=175151,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Albacete, capital provincial con 175.151 habitantes (INE 2025), es una ciudad castellanomanchega en crecimiento, con un mercado residencial dinámico en barrios como Imaginalia, Carretas o el Ensanche.",
                         consejo="Albacete bonifica hasta un 50% a familias numerosas y 5% por domiciliación (acumulables). Si domicilias antes del 15 de febrero y presentas título de familia numerosa, el ahorro combinado puede superar el 50% de la cuota."),
                    dict(slug="almansa", nombre="Almansa", ibi=0.63, ibir=0.50, basuras=105, pob=24476,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="hellin", nombre="Hellín", ibi=0.64, ibir=0.50, basuras=108, pob=30085,
                         pobann=2025, fn=25, solar=30, existing=True),
                ],
            },
            "ciudad-real": {
                "nombre": "Ciudad Real",
                "municipios": [
                    dict(slug="ciudad-real", nombre="Ciudad Real", ibi=0.62, ibir=0.50, basuras=112, pob=74746,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Ciudad Real, capital de provincia con 74.746 habitantes (INE 2025), está conectada con Madrid por AVE en 55 minutos. Esta conectividad ha estabilizado su mercado inmobiliario con valores catastrales predecibles.",
                         consejo="Ciudad Real aplica bonificación de hasta el 50% por energía solar durante 3 años. Si hiciste la instalación antes de 2024, todavía puedes estar en el período bonificado: revisa la fecha del boletín eléctrico."),
                    dict(slug="puertollano", nombre="Puertollano", ibi=0.67, ibir=0.50, basuras=115, pob=46418,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="tomelloso", nombre="Tomelloso", ibi=0.65, ibir=0.50, basuras=108, pob=38670,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="alcazar-de-san-juan", nombre="Alcázar de San Juan", ibi=0.64, ibir=0.50, basuras=105, pob=31028,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="valdepenas", nombre="Valdepeñas", ibi=0.63, ibir=0.50, basuras=102, pob=29979,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Valdepeñas, capital vitivinícola con 29.979 habitantes (INE 2025), destaca por su denominación de origen, su patrimonio modernista y un mercado inmobiliario estable marcado por los barrios del centro y los nuevos desarrollos del ensanche este.",
                         consejo="Valdepeñas dispone de bonificación específica para inmuebles BIC en el casco histórico (hasta 90% del IBI). Si tu vivienda está en el entorno de la Iglesia o la bodega Real, consulta si entra en la protección patrimonial."),
                    dict(slug="manzanares", nombre="Manzanares", ibi=0.62, ibir=0.50, basuras=100, pob=18259,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Manzanares, localidad de paso en la A-4 y centro agroalimentario con 18.259 habitantes (INE 2025), combina actividad vitivinícola, industria agroalimentaria y un mercado residencial asequible.",
                         consejo="En Manzanares, la tarifa de basuras para locales comerciales y bodegas es diferenciada. Si tienes una nave o bodega activa, puede beneficiarse del tramo mínimo de la tarifa económica."),
                    dict(slug="daimiel", nombre="Daimiel", ibi=0.62, ibir=0.50, basuras=98, pob=18127,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Daimiel, célebre por las Tablas de Daimiel (Parque Nacional), tiene 18.127 habitantes (INE 2025). Su economía es agrícola (vid, olivar) y de servicios, con un mercado inmobiliario con valores catastrales moderados.",
                         consejo="Daimiel mantiene bonificación ampliada para inmuebles colindantes al Parque Nacional de Las Tablas. Consulta si tu parcela rústica entra en el perímetro: puede reducir tu IBI rústico."),
                    dict(slug="villarrobledo", nombre="Villarrobledo", ibi=0.63, ibir=0.50, basuras=100, pob=25057,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Villarrobledo, aunque geográficamente en Albacete, pertenece administrativamente a su provincia y es capital alfarera (tinajas) y vitivinícola (cooperativas) con 25.057 habitantes (INE 2025). Integramos esta guía bajo Ciudad Real por proximidad comarcal a La Mancha.",
                         consejo="Villarrobledo ofrece bonificación al comercio tradicional alfarero (tinajas). Si tu inmueble tiene uso compatible con actividad artesanal, consulta la bonificación del 10% del IBI económico."),
                ],
            },
            "cuenca": {
                "nombre": "Cuenca",
                "municipios": [
                    dict(slug="cuenca", nombre="Cuenca", ibi=0.66, ibir=0.50, basuras=115, pob=53869,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="tarancon", nombre="Tarancón", ibi=0.62, ibir=0.50, basuras=102, pob=15970,
                         pobann=2025, fn=25, solar=30, existing=True),
                ],
            },
            "guadalajara": {
                "nombre": "Guadalajara",
                "municipios": [
                    dict(slug="guadalajara", nombre="Guadalajara", ibi=0.63, ibir=0.50, basuras=115, pob=91959,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Guadalajara, capital provincial con 91.959 habitantes (INE 2025), forma parte del Corredor del Henares. Su proximidad a Madrid ha revalorizado intensamente el parque residencial, con barrios como Aguas Vivas o El Ruiseñor muy buscados.",
                         consejo="Guadalajara aplica bonificación acumulable de familia numerosa especial (50%) y domiciliación (5%). Además, dispone de tarifa plana de basuras con tramo reducido para pensionistas: consulta requisitos en la sede electrónica."),
                    dict(slug="azuqueca-de-henares", nombre="Azuqueca de Henares", ibi=0.61, ibir=0.50, basuras=108, pob=36065,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="cabanillas-del-campo", nombre="Cabanillas del Campo", ibi=0.60, ibir=0.50, basuras=108, pob=12149,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Cabanillas del Campo es uno de los municipios de mayor crecimiento del Corredor del Henares (12.149 hab., INE 2025), con parque residencial mayoritariamente reciente y urbanizaciones como Valderrebollo o El Bañuelo.",
                         consejo="Cabanillas del Campo, al ser un municipio con alta proporción de viviendas nuevas, aplica la bonificación VPO durante 3 años desde la calificación definitiva (hasta 50% del IBI). Consulta tu calificación antes de asumir que pagas el tipo íntegro."),
                ],
            },
            "toledo": {
                "nombre": "Toledo",
                "municipios": [
                    dict(slug="toledo", nombre="Toledo", ibi=0.60, ibir=0.50, basuras=118, pob=85449,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Toledo, Ciudad Patrimonio de la Humanidad (UNESCO), suma 85.449 habitantes (INE 2025). Su mercado inmobiliario está marcado por el casco histórico protegido (BIC), los barrios del ensanche (Santa María de Benquerencia, La Legua) y urbanizaciones periurbanas.",
                         consejo="Toledo bonifica hasta el 90% del IBI a los inmuebles declarados BIC en el casco histórico. Si tu vivienda está en el recinto protegido UNESCO, acude al Consorcio de Toledo con el certificado patrimonial para solicitar la bonificación."),
                    dict(slug="talavera-de-la-reina", nombre="Talavera de la Reina", ibi=0.68, ibir=0.50, basuras=145, pob=83108,
                         pobann=2025, fn=50, solar=30, existing=True),
                    dict(slug="illescas", nombre="Illescas", ibi=0.60, ibir=0.50, basuras=120, pob=31812,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="sesena", nombre="Seseña", ibi=0.58, ibir=0.50, basuras=100, pob=28053,
                         pobann=2025, fn=25, solar=30, existing=True),
                ],
            },
        },
    },
    "castilla-y-leon": {
        "nombre": "Castilla y León",
        "gen_hub": True,
        "boletin": ("BOCYL", "https://bocyl.jcyl.es", "nº 245, 19/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "avila": {
                "nombre": "Ávila",
                "municipios": [
                    dict(slug="avila", nombre="Ávila", ibi=0.63, ibir=0.50, basuras=110, pob=58185,
                         pobann=2025, fn=30, solar=30, existing=True),
                ],
            },
            "burgos": {
                "nombre": "Burgos",
                "municipios": [
                    dict(slug="burgos", nombre="Burgos", ibi=0.60, ibir=0.50, basuras=118, pob=175456,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Burgos, capital provincial y Ciudad Patrimonio de la Humanidad por su Catedral, tiene 175.456 habitantes (INE 2025). Su mercado residencial es estable, con barrios tradicionales (Gamonal, San Pedro) y zonas de expansión como Villímar o Fuentecillas.",
                         consejo="Burgos dispone de bonificación del 95% para inmuebles del casco histórico catalogados como BIC o BIP. Si tu vivienda está en el entorno de la Catedral, consulta en la Oficina de Centro Histórico."),
                    dict(slug="aranda-de-duero", nombre="Aranda de Duero", ibi=0.64, ibir=0.50, basuras=110, pob=33156,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="miranda-de-ebro", nombre="Miranda de Ebro", ibi=0.65, ibir=0.50, basuras=115, pob=35058,
                         pobann=2025, fn=30, solar=30, existing=True),
                ],
            },
            "leon": {
                "nombre": "León",
                "municipios": [
                    dict(slug="leon", nombre="León", ibi=0.62, ibir=0.50, basuras=120, pob=120488,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="León, capital provincial con 120.488 habitantes (INE 2025), conjuga patrimonio histórico (Catedral, San Isidoro) y tejido universitario. Su mercado inmobiliario se articula en el casco antiguo, el Ensanche y barrios como Eras de Renueva o La Palomera.",
                         consejo="León bonifica el IBI hasta el 95% a los inmuebles BIC en el casco antiguo y aplica tarifa reducida de basuras a pensionistas con renta inferior a 1,5 veces el IPREM. Ambas bonificaciones son compatibles y acumulables."),
                    dict(slug="ponferrada", nombre="Ponferrada", ibi=0.67, ibir=0.50, basuras=135, pob=63090,
                         pobann=2025, fn=50, solar=30, existing=True),
                ],
            },
            "palencia": {
                "nombre": "Palencia",
                "municipios": [
                    dict(slug="palencia", nombre="Palencia", ibi=0.63, ibir=0.50, basuras=112, pob=77909,
                         pobann=2025, fn=50, solar=50, existing=True),
                ],
            },
            "salamanca": {
                "nombre": "Salamanca",
                "municipios": [
                    dict(slug="salamanca", nombre="Salamanca", ibi=0.61, ibir=0.50, basuras=115, pob=143978,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Salamanca, Ciudad Patrimonio UNESCO y sede de la universidad más antigua de España, tiene 143.978 habitantes (INE 2025). Su mercado inmobiliario es tensionado por la demanda estudiantil, especialmente en el centro y zonas próximas a la universidad.",
                         consejo="Salamanca mantiene bonificación especial para arrendamientos a estudiantes universitarios a precio tasado: hasta 15% del IBI si acreditas contrato y precio por debajo del índice de referencia. Consulta el procedimiento en la Agencia Municipal de Vivienda."),
                    dict(slug="bejar", nombre="Béjar", ibi=0.64, ibir=0.50, basuras=92, pob=12275,
                         pobann=2025, fn=25, solar=25, existing=True),
                ],
            },
            "segovia": {
                "nombre": "Segovia",
                "municipios": [
                    dict(slug="segovia", nombre="Segovia", ibi=0.62, ibir=0.50, basuras=112, pob=53600,
                         pobann=2025, fn=50, solar=30, existing=True),
                ],
            },
            "soria": {
                "nombre": "Soria",
                "municipios": [
                    dict(slug="soria", nombre="Soria", ibi=0.60, ibir=0.50, basuras=108, pob=39631,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Soria, capital provincial con 39.631 habitantes (INE 2025), es la ciudad más despoblada de España con acceso AVE reciente. Su mercado inmobiliario es muy asequible y atractivo para inversores buscando rentabilidad alta en alquiler.",
                         consejo="Soria aplica bonificación del 50% durante 3 años a empresas/autónomos que trasladen su actividad. Además, la bonificación por placas solares (30%) es muy rentable: Soria tiene altos niveles de radiación solar durante 9 meses al año."),
                ],
            },
            "valladolid": {
                "nombre": "Valladolid",
                "municipios": [
                    dict(slug="valladolid", nombre="Valladolid", ibi=0.61, ibir=0.50, basuras=120, pob=296853,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Valladolid, capital autonómica y sexta ciudad por población de Castilla y León con 296.853 habitantes (INE 2025), tiene un mercado residencial consolidado: desde el tejido histórico del centro hasta barrios en expansión como Parquesol, Villa del Prado o Covaresa.",
                         consejo="Valladolid aplica bonificación de hasta 50% a familias numerosas de categoría especial y 5% por domiciliación. Importante: la domiciliación SEPA debe activarse antes del 28 de febrero para aplicarse al ejercicio en curso."),
                    dict(slug="medina-del-campo", nombre="Medina del Campo", ibi=0.62, ibir=0.50, basuras=100, pob=20761,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Medina del Campo, Villa de las Ferias en la histórica ruta Madrid–Santander, tiene 20.761 habitantes (INE 2025). Su conexión AVE y su Castillo de la Mota sostienen un mercado inmobiliario activo con valores catastrales moderados.",
                         consejo="Medina del Campo ofrece bonificación específica para inmuebles que formen parte de la ruta turística del Castillo de la Mota. Si tu inmueble está en el entorno BIC, presenta el certificado patrimonial en recaudación."),
                ],
            },
            "zamora": {
                "nombre": "Zamora",
                "municipios": [
                    dict(slug="zamora", nombre="Zamora", ibi=0.64, ibir=0.50, basuras=108, pob=59178,
                         pobann=2025, fn=30, solar=30, existing=True),
                ],
            },
        },
    },
    "extremadura": {
        "nombre": "Extremadura",
        "gen_hub": True,
        "boletin": ("DOE", "https://doe.juntaex.es", "nº 243, 20/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "badajoz": {
                "nombre": "Badajoz",
                "municipios": [
                    dict(slug="badajoz", nombre="Badajoz", ibi=0.60, ibir=0.50, basuras=115, pob=150984,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Badajoz, capital de provincia y mayor ciudad de Extremadura con 150.984 habitantes (INE 2025), es nodo urbano del eje ibérico hacia Lisboa. Su mercado inmobiliario se estructura en el casco antiguo fortificado, Valdepasillas, Cerro Gordo y las urbanizaciones del área de Manuel Saavedra.",
                         consejo="Badajoz aplica descuento acumulable por domiciliación (5%) y familia numerosa (hasta 50%). También bonifica hasta 95% del IBI a edificios restaurados dentro del Plan Especial del Casco Antiguo. Consulta si tu inmueble entra."),
                    dict(slug="merida", nombre="Mérida", ibi=0.66, ibir=0.50, basuras=130, pob=59673,
                         pobann=2025, fn=50, solar=30, existing=True),
                    dict(slug="don-benito", nombre="Don Benito", ibi=0.63, ibir=0.50, basuras=108, pob=37000,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="almendralejo", nombre="Almendralejo", ibi=0.64, ibir=0.50, basuras=110, pob=35036,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="villanueva-de-la-serena", nombre="Villanueva de la Serena", ibi=0.63, ibir=0.50, basuras=105, pob=25998,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="zafra", nombre="Zafra", ibi=0.63, ibir=0.50, basuras=98, pob=16899,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="montijo", nombre="Montijo", ibi=0.62, ibir=0.50, basuras=95, pob=15769,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="olivenza", nombre="Olivenza", ibi=0.62, ibir=0.50, basuras=98, pob=11908,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Olivenza, ciudad fronteriza con Portugal y territorio disputado históricamente, conserva patrimonio hispano-portugués único (11.908 hab., INE 2025). Su mercado inmobiliario es asequible y está dinamizado por la reciente apertura AVE Madrid-Badajoz.",
                         consejo="Olivenza bonifica hasta 50% el IBI durante 5 años a quienes rehabiliten inmuebles con tipología manuelina tradicional. Conserva los informes técnicos antes y después de la reforma para documentar la intervención patrimonial."),
                    dict(slug="jerez-de-los-caballeros", nombre="Jerez de los Caballeros", ibi=0.61, ibir=0.50, basuras=92, pob=9154,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Jerez de los Caballeros, cuna de Vasco Núñez de Balboa y ciudad templaria con 9.154 habitantes (INE 2025), destaca por su casco histórico-artístico y su industria agroalimentaria (Dehesa de Extremadura, ibéricos).",
                         consejo="Jerez de los Caballeros dispone de tarifa reducida de basuras para pensionistas con renta inferior a 1,25 veces el IPREM. El trámite se hace en el Servicio de Atención Ciudadana del Ayuntamiento presentando certificado de la Seguridad Social."),
                ],
            },
            "caceres": {
                "nombre": "Cáceres",
                "municipios": [
                    dict(slug="caceres", nombre="Cáceres", ibi=0.62, ibir=0.50, basuras=115, pob=97038,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Cáceres, Ciudad Patrimonio UNESCO por su casco medieval, tiene 97.038 habitantes (INE 2025). Su mercado inmobiliario se divide entre el recinto monumental (valores altos y protegidos), barrios tradicionales como San Blas y expansión moderna hacia la universidad.",
                         consejo="Cáceres bonifica hasta 95% del IBI a edificios BIC dentro del recinto monumental UNESCO. Para inmuebles fuera del casco histórico, la bonificación por placas solares (hasta 50%) es especialmente rentable por la alta irradiación extremeña."),
                    dict(slug="plasencia", nombre="Plasencia", ibi=0.65, ibir=0.52, basuras=95, pob=40068,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="navalmoral-de-la-mata", nombre="Navalmoral de la Mata", ibi=0.62, ibir=0.50, basuras=88, pob=17146,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="coria", nombre="Coria", ibi=0.62, ibir=0.50, basuras=82, pob=12489,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="miajadas", nombre="Miajadas", ibi=0.62, ibir=0.50, basuras=80, pob=9688,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="trujillo", nombre="Trujillo", ibi=0.61, ibir=0.50, basuras=78, pob=9204,
                         pobann=2025, fn=25, solar=30, existing=True),
                ],
            },
        },
    },
    "galicia": {
        "nombre": "Galicia",
        "gen_hub": True,
        "boletin": ("DOG", "https://www.xunta.gal/dog", "nº 243, 19/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "a-coruna": {
                "nombre": "A Coruña",
                "municipios": [
                    dict(slug="a-coruna", nombre="A Coruña", ibi=0.615, ibir=0.50, basuras=120, pob=249425,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="A Coruña, capital de provincia y principal ciudad portuaria del noroeste con 249.425 habitantes (INE 2025), combina barrios históricos (Cidade Vella, Pescadería), ensanche del siglo XIX y zonas modernas (Los Rosales, Zalaeta).",
                         consejo="A Coruña aplica bonificación especial en el IBI de hasta 95% a BIC en Cidade Vella y Pescadería, acumulable con la bonificación por domiciliación (5%). Además, dispone de tarifa reducida de basuras para viviendas de menos de 60 m²."),
                    dict(slug="santiago-de-compostela", nombre="Santiago de Compostela", ibi=0.60, ibir=0.50, basuras=115, pob=99002,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Santiago de Compostela, capital autonómica y meta del Camino de Santiago, cuenta con 99.002 habitantes (INE 2025). Su mercado inmobiliario está marcado por la presión estudiantil y turística, con fuerte demanda en el casco histórico (UNESCO) y barrios universitarios.",
                         consejo="Santiago bonifica hasta el 95% del IBI en la Zona Monumental declarada UNESCO y dispone de bonificación ampliada para inmuebles arrendados a estudiantes con precio tasado. Consulta la Ordenanza Municipal de Fomento del Alquiler."),
                    dict(slug="ferrol", nombre="Ferrol", ibi=0.60, ibir=0.50, basuras=108, pob=63905,
                         pobann=2025, fn=50, solar=30, existing=True),
                    dict(slug="naron", nombre="Narón", ibi=0.58, ibir=0.50, basuras=95, pob=40045,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Narón, integrado en el área metropolitana de Ferrol, tiene 40.045 habitantes (INE 2025). Su parque inmobiliario es relativamente reciente, especialmente en la zona de Freixeiro y A Solaina.",
                         consejo="Narón dispone de bonificación específica del 25% durante los 3 primeros años para VPO. Si tu inmueble es protección oficial, consulta el plazo desde la calificación definitiva para no dejar de beneficiarte."),
                    dict(slug="carballo", nombre="Carballo", ibi=0.59, ibir=0.50, basuras=92, pob=32015,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Carballo, capital de la comarca de Bergantiños (32.015 hab., INE 2025), es uno de los municipios más dinámicos de la Costa da Morte, con industria textil (Alfonso Graña) y tejido agroalimentario.",
                         consejo="Carballo revisó al alza su tarifa de basuras en 2025 para cumplir con la Ley 7/2022. Si notas un salto grande respecto a 2024, es normativo y no es error: revisa la ordenanza en la sede electrónica."),
                    dict(slug="ames", nombre="Ames", ibi=0.58, ibir=0.50, basuras=92, pob=32815,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Ames, municipio de rápida expansión en el área metropolitana de Santiago (32.815 hab., INE 2025), concentra viviendas recientes en núcleos como Bertamiráns y O Milladoiro, con alta calidad urbanística.",
                         consejo="Ames, al tener gran parque residencial nuevo, aplica bonificación VPO (50%) durante 3 años y bonificación por instalación de autoconsumo solar (30%). Verifica la calificación energética de tu vivienda: abre más posibilidades de bonificación."),
                    dict(slug="arteixo", nombre="Arteixo", ibi=0.60, ibir=0.50, basuras=98, pob=32513,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Arteixo, conurbado con A Coruña y sede de Inditex (32.513 hab., INE 2025), combina un potente polígono industrial (Sabón) con un mercado residencial en expansión especialmente en Meicende y el entorno de la playa de Sabón.",
                         consejo="Arteixo bonifica hasta 95% del IBI a naves industriales nuevas durante 3 años para atraer inversión. Si tienes actividad económica en el polígono de Sabón, consulta si entras en el programa de incentivos."),
                    dict(slug="ribeira", nombre="Ribeira", ibi=0.60, ibir=0.50, basuras=100, pob=26928,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Ribeira, capital de la comarca del Barbanza con mayor flota pesquera fresca de España (26.928 hab., INE 2025), combina puerto pesquero, turismo de costa (Corrubedo) y un mercado inmobiliario activo.",
                         consejo="Ribeira mantiene tarifa diferenciada de basuras para segundas residencias en zona costera (Corrubedo, Aguiño). Si tu vivienda es habitual y no vacacional, asegúrate de estar correctamente empadronado: el ahorro puede alcanzar 40 €/año."),
                ],
            },
            "lugo": {
                "nombre": "Lugo",
                "municipios": [
                    dict(slug="lugo", nombre="Lugo", ibi=0.56, ibir=0.46, basuras=90, pob=98560,
                         pobann=2025, fn=50, solar=50, existing=True),
                    dict(slug="monforte-de-lemos", nombre="Monforte de Lemos", ibi=0.55, ibir=0.46, basuras=85, pob=17983,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="viveiro", nombre="Viveiro", ibi=0.57, ibir=0.46, basuras=92, pob=15236,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Viveiro, capital de A Mariña Occidental (15.236 hab., INE 2025), destaca por su Semana Santa (Interés Turístico Internacional) y sus playas (Covas). Su costa ha dinamizado el mercado de segunda residencia.",
                         consejo="En Viveiro, la tarifa de basuras tiene tramo reducido para viviendas con titular jubilado y renta inferior al IPREM. El trámite es anual y se debe renovar antes del 31 de marzo."),
                    dict(slug="sarria", nombre="Sarria", ibi=0.56, ibir=0.46, basuras=88, pob=13192,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Sarria, referente gallego del Camino de Santiago Francés (13.192 hab., INE 2025), tiene una economía muy vinculada al turismo jacobeo y al sector ferial (Sarria ganadería). Su mercado inmobiliario refleja esa estacionalidad.",
                         consejo="Sarria bonifica hasta un 25% el IBI a alojamientos turísticos regularizados en el Camino de Santiago. Si tu inmueble tiene licencia como pensión/albergue peregrino, acredita la actividad económica para solicitar la bonificación."),
                ],
            },
            "ourense": {
                "nombre": "Ourense",
                "municipios": [
                    dict(slug="ourense", nombre="Ourense", ibi=0.57, ibir=0.46, basuras=95, pob=104596,
                         pobann=2025, fn=50, solar=50, existing=True),
                    dict(slug="o-carballino", nombre="O Carballiño", ibi=0.54, ibir=0.46, basuras=82, pob=13814,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="verin", nombre="Verín", ibi=0.56, ibir=0.46, basuras=85, pob=13450,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Verín, capital del vino de Monterrei y ciudad fronteriza con Portugal (13.450 hab., INE 2025), combina actividad termal (balnearios de Cabreiroá y Sousas) con un mercado residencial asequible.",
                         consejo="Verín aplica bonificación específica del 25% a fincas rústicas destinadas a viticultura inscrita en la DO Monterrei. Si tienes parcelas con viñedo declarado, solicita la bonificación con tu ficha DO."),
                    dict(slug="lalin", nombre="Lalín", ibi=0.56, ibir=0.46, basuras=88, pob=19969,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Lalín, capital del Deza y conocido como Feria del Cocido Gallego, tiene 19.969 habitantes (INE 2025). Su ubicación estratégica entre Santiago y Ourense sostiene un mercado inmobiliario estable.",
                         consejo="Lalín tiene bonificación en el IBI durante 3 años para inmuebles rehabilitados con criterios de eficiencia energética A o B. Pide certificado energético homologado tras tu reforma para solicitarla."),
                ],
            },
            "pontevedra": {
                "nombre": "Pontevedra",
                "municipios": [
                    dict(slug="vigo", nombre="Vigo", ibi=0.61, ibir=0.50, basuras=115, pob=295364,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Vigo, principal ciudad industrial y portuaria de Galicia con 295.364 habitantes (INE 2025), estructura su mercado residencial entre el casco antiguo, el ensanche (García Barbón), O Castro-Navia y barrios recientes como Coia.",
                         consejo="Vigo dispone de bonificación de hasta 50% a familias numerosas de categoría especial y bonificación permanente del 5% por domiciliación, con fraccionamiento en 2 plazos sin intereses (mayo y octubre). Ambas son acumulables."),
                    dict(slug="pontevedra", nombre="Pontevedra", ibi=0.54, ibir=0.46, basuras=98, pob=84600,
                         pobann=2025, fn=50, solar=50, existing=True),
                    dict(slug="vilagarcia-de-arousa", nombre="Vilagarcía de Arousa", ibi=0.55, ibir=0.46, basuras=95, pob=37840,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="marin", nombre="Marín", ibi=0.60, ibir=0.50, basuras=98, pob=23815,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Marín, municipio costero de la Ría de Pontevedra con Escuela Naval Militar (23.815 hab., INE 2025), combina tejido pesquero-marisquero con una importante presencia militar. Su mercado inmobiliario es estable.",
                         consejo="Marín aplica tarifa reducida de basuras para viviendas del personal militar de la Escuela Naval con traslado forzoso. Si tu situación es transitoria (destino), consulta si aplica la bonificación temporal."),
                    dict(slug="cangas", nombre="Cangas", ibi=0.59, ibir=0.50, basuras=95, pob=26711,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Cangas, en la Ría de Vigo frente a las Islas Cíes, tiene 26.711 habitantes (INE 2025). Su puerto de conexión con Vigo y playas (Rodeira, Melide) dinamizan un mercado inmobiliario atractivo para residentes y segundas residencias.",
                         consejo="Cangas aplica tarifa diferenciada de basuras para zona costera vacacional (Menduíña, Nerga). Si tu inmueble es vivienda habitual y no vacacional, verifica tu padrón: el ahorro puede ser significativo."),
                    dict(slug="redondela", nombre="Redondela", ibi=0.60, ibir=0.50, basuras=98, pob=29376,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Redondela, conocida por sus viaductos históricos y la Peña del Portal, tiene 29.376 habitantes (INE 2025). Su ubicación en la Ría de Vigo y la AP-9 la convierte en nudo logístico y residencial para Vigo.",
                         consejo="Redondela dispone de tarifa reducida de basuras para arquitectura tradicional rehabilitada (casas de piedra) en los núcleos rurales de Cesantes y Vilavella. Conserva facturas y licencia para solicitarlo."),
                    dict(slug="tui", nombre="Tui", ibi=0.59, ibir=0.50, basuras=92, pob=16679,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Tui, ciudad episcopal fronteriza con Portugal (Valença do Minho), conserva un casco histórico notable con 16.679 habitantes (INE 2025). Su Catedral románica y el paso del Camino Portugués mantienen activo el mercado turístico-residencial.",
                         consejo="Tui dispone de bonificación del IBI hasta 90% para inmuebles BIC del casco monumental. Si tu inmueble está en el Casco Antiguo declarado Conjunto Histórico, solicita la bonificación con el certificado patrimonial."),
                    dict(slug="o-porrino", nombre="O Porriño", ibi=0.60, ibir=0.50, basuras=95, pob=20050,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="O Porriño, referencia industrial (granito) y logística del sur de Pontevedra (20.050 hab., INE 2025), es nudo de comunicación A-9 / Portugal con polígonos industriales relevantes (Torneiros, A Granxa).",
                         consejo="O Porriño aplica bonificación específica para naves dedicadas a actividad de extracción y transformación de granito autóctono. Si tu actividad está en el sector, documéntalo con licencia de actividad vigente."),
                ],
            },
        },
    },
    "murcia": {
        "nombre": "Murcia",
        "gen_hub": True,
        "boletin": ("BORM", "https://www.borm.es", "nº 245, 20/12/2025"),
        "periodo": "1 oct – 30 nov 2026",
        "provincias": {
            "murcia": {
                "nombre": "Murcia",
                "municipios": [
                    dict(slug="murcia", nombre="Murcia", ibi=0.655, ibir=0.50, basuras=125, pob=464751,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Murcia, capital de la Región y séptima ciudad española por población con 464.751 habitantes (INE 2025), estructura su mercado inmobiliario entre el centro histórico (Catedral), el ensanche del siglo XX, barrios de crecimiento como La Flota o Ronda Sur, y pedanías con alta densidad residencial.",
                         consejo="Murcia capital bonifica hasta 50% a familias numerosas, 5% por domiciliación y fraccionamiento sin intereses en 2 o 3 plazos. Activa la domiciliación antes del 28 de febrero para aplicar en el ejercicio en curso."),
                    dict(slug="cartagena", nombre="Cartagena", ibi=0.65, ibir=0.50, basuras=120, pob=217389,
                         pobann=2025, fn=50, solar=50, existing=False,
                         lead="Cartagena, Puerto de Culturas con yacimientos romanos y el Palacio Consistorial modernista, tiene 217.389 habitantes (INE 2025). Su litoral (La Manga, Cabo de Palos) suma miles de segundas residencias que multiplican el patrimonio inmobiliario municipal.",
                         consejo="En Cartagena, la tarifa de basuras en La Manga y zonas del litoral es diferenciada por temporada. Si tu inmueble de La Manga es vivienda habitual, asegúrate de estar empadronado: podrás beneficiarte de la tarifa reducida."),
                    dict(slug="lorca", nombre="Lorca", ibi=0.65, ibir=0.50, basuras=115, pob=96870,
                         pobann=2025, fn=30, solar=30, existing=True),
                    dict(slug="molina-de-segura", nombre="Molina de Segura", ibi=0.66, ibir=0.50, basuras=128, pob=74049,
                         pobann=2025, fn=50, solar=30, existing=True),
                    dict(slug="cieza", nombre="Cieza", ibi=0.64, ibir=0.50, basuras=108, pob=35432,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="aguilas", nombre="Águilas", ibi=0.63, ibir=0.50, basuras=110, pob=36089,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="yecla", nombre="Yecla", ibi=0.62, ibir=0.50, basuras=105, pob=34847,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="caravaca-de-la-cruz", nombre="Caravaca de la Cruz", ibi=0.61, ibir=0.50, basuras=102, pob=26187,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="mazarron", nombre="Mazarrón", ibi=0.63, ibir=0.50, basuras=115, pob=36098,
                         pobann=2025, fn=25, solar=30, existing=True),
                    dict(slug="torre-pacheco", nombre="Torre Pacheco", ibi=0.64, ibir=0.50, basuras=115, pob=41373,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Torre Pacheco, municipio del Campo de Cartagena (41.373 hab., INE 2025), se ha convertido en polo residencial con urbanizaciones de golf (La Torre Golf, Mar Menor Golf) y fuerte presencia de propietarios europeos.",
                         consejo="Torre Pacheco aplica tarifa diferenciada en urbanizaciones cerradas. Si vives en un resort de golf con comunidad de propietarios, verifica que la tasa municipal de basuras no se duplica con la cuota de comunidad."),
                    dict(slug="san-javier", nombre="San Javier", ibi=0.63, ibir=0.50, basuras=118, pob=34170,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="San Javier, en el Mar Menor con la sede de la Academia General del Aire (34.170 hab., INE 2025), integra municipio residencial, aeropuerto (San Javier), zona militar y litoral turístico (Santiago de la Ribera).",
                         consejo="San Javier ofrece bonificación IBI específica para inmuebles afectados por ruido del aeropuerto. Si tu vivienda está en la Ribera o zonas colindantes, consulta la bonificación por servidumbre acústica."),
                    dict(slug="san-pedro-del-pinatar", nombre="San Pedro del Pinatar", ibi=0.63, ibir=0.50, basuras=115, pob=27046,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="San Pedro del Pinatar, extremo norte del Mar Menor y de la Región (27.046 hab., INE 2025), destaca por sus salinas de Interés Ecológico Nacional y una alta proporción de segundas residencias.",
                         consejo="San Pedro del Pinatar aplica bonificación especial a inmuebles colindantes con el Parque Regional de las Salinas. Consulta si tu parcela está dentro del perímetro de protección: puede reducir hasta 15% del IBI."),
                    dict(slug="alcantarilla", nombre="Alcantarilla", ibi=0.64, ibir=0.50, basuras=108, pob=42058,
                         pobann=2025, fn=30, solar=30, existing=False,
                         lead="Alcantarilla, conurbada con Murcia capital y con la Base Aérea (42.058 hab., INE 2025), es uno de los municipios con mayor densidad de población de la Región. Su mercado inmobiliario es estable con valores catastrales contenidos.",
                         consejo="Alcantarilla bonifica el IBI hasta 50% a familias numerosas de categoría especial. Si tu título de FN es general (no especial), revisa si la diferencia de bonificación (25% vs 50%) compensa solicitar la categoría especial cuando proceda por número de hijos o discapacidad."),
                    dict(slug="jumilla", nombre="Jumilla", ibi=0.62, ibir=0.50, basuras=102, pob=26439,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Jumilla, capital vitivinícola con DO reconocida internacionalmente (26.439 hab., INE 2025), combina un casco histórico amurallado con el Castillo de Jumilla y un tejido productivo centrado en bodegas y agricultura.",
                         consejo="Jumilla aplica bonificación específica del 25% a fincas rústicas inscritas en la DO Jumilla. Si tienes parcela con viñedo DO, presenta la ficha de la Consejería de Agricultura junto con el recibo para solicitar la bonificación."),
                    dict(slug="totana", nombre="Totana", ibi=0.62, ibir=0.50, basuras=100, pob=32907,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Totana, en el Valle del Guadalentín al pie de Sierra Espuña (32.907 hab., INE 2025), es capital alfarera tradicional y centro agroalimentario (brócoli, alcachofa). Su mercado inmobiliario es asequible.",
                         consejo="Totana mantiene bonificaciones compatibles para alfarería tradicional (actividad económica) y familia numerosa. Si el titular es autónomo alfarero, consulta si puede acumular ambas reducciones en el recibo del IBI."),
                    dict(slug="alhama-de-murcia", nombre="Alhama de Murcia", ibi=0.62, ibir=0.50, basuras=105, pob=24185,
                         pobann=2025, fn=25, solar=30, existing=False,
                         lead="Alhama de Murcia, conocida por su resort de golf Condado de Alhama (24.185 hab., INE 2025), combina núcleo tradicional con urbanizaciones cerradas de fuerte demanda internacional.",
                         consejo="En Alhama de Murcia, la tarifa de basuras diferenciada en las urbanizaciones de golf puede cobrarse en una cuota única fuera del padrón. Confirma que tu urbanización no duplica la tasa municipal con la cuota comunitaria."),
                ],
            },
        },
    },
}


# ────────────────────────────────────────────────────────────────
# Datos agregados computados
# ────────────────────────────────────────────────────────────────
def all_munis():
    out = []
    for ccaa_slug, ccaa in CCAA.items():
        for prov_slug, prov in ccaa["provincias"].items():
            for m in prov["municipios"]:
                out.append({
                    **m,
                    "ccaa_slug": ccaa_slug,
                    "ccaa_nombre": ccaa["nombre"],
                    "prov_slug": prov_slug,
                    "prov_nombre": prov["nombre"],
                    "boletin": ccaa["boletin"],
                    "periodo": ccaa["periodo"],
                    "url_path": f"/{ccaa_slug}/{prov_slug}/{m['slug']}/",
                    "sede": f"https://{m['slug']}.sedelectronica.es",
                })
    return out


def provincia_munis(ccaa_slug, prov_slug):
    return CCAA[ccaa_slug]["provincias"][prov_slug]["municipios"]


def ccaa_munis(ccaa_slug):
    out = []
    for prov_slug, prov in CCAA[ccaa_slug]["provincias"].items():
        for m in prov["municipios"]:
            out.append({**m, "prov_slug": prov_slug, "prov_nombre": prov["nombre"]})
    return out


def total_munis():
    return len(all_munis())


def total_ccaa():
    return len(CCAA)


# ────────────────────────────────────────────────────────────────
# Plantillas comunes
# ────────────────────────────────────────────────────────────────
def header_nav(rel=""):
    return f'''<header>
  <div class="hi">
    <a href="{rel}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
    <nav>
      <a href="{rel}comunidades/">Comunidades</a>
      <a href="{rel}municipios/">Municipios</a>
      <a href="{rel}ibi-2026/">IBI 2026</a>
      <a href="{rel}calculadora-ibi/">Calculadora</a>
      <a href="{rel}tasa-basuras/">Basuras</a>
      <a href="{rel}plusvalia/">Plusvalía</a>
      <a href="{rel}bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>'''


def footer_large(rel=""):
    total = total_munis()
    total_cc = total_ccaa()
    return f'''<footer>
  <div class="ft-grid" style="max-width:1100px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px;padding:40px 24px 24px;">
    <div>
      <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:900;color:#fff;margin-bottom:6px;">TasasMunicipales</div>
      <div style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:10px;">Guía de Impuestos Locales · España 2026</div>
      <p style="font-size:.78rem;line-height:1.7;color:rgba(255,255,255,.45);margin:0;">Guía de IBI, tasa de basuras, plusvalía y bonificaciones para {total} municipios en {total_cc} comunidades autónomas.</p>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Navegación</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{rel}" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Inicio</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}comunidades/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Comunidades</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}municipios/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Municipios</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}calculadora-ibi/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Calculadora IBI</a></li>
      </ul>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Impuestos</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{rel}ibi-2026/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">IBI 2026</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}tasa-basuras/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Tasa de Basuras</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}plusvalia/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Plusvalía Municipal</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}bonificaciones/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Bonificaciones</a></li>
      </ul>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Legal</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="{rel}aviso-legal/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Aviso Legal</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}privacidad/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Privacidad</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}cookies/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Cookies</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}contacto/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Contacto</a></li>
        <li style="margin-bottom:8px;"><a href="{rel}sobre-nosotros/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Sobre nosotros</a></li>
      </ul>
    </div>
  </div>
  <div style="max-width:1100px;margin:0 auto;padding:16px 24px 28px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:.72rem;color:rgba(255,255,255,.4);">
    <span>© 2026 TasasMunicipales.info · La información no constituye asesoramiento fiscal.</span>
    <span>Datos orientativos. Consulta siempre tu ayuntamiento.</span>
  </div>
</footer>'''


def footer_small(rel="../../../"):
    return f'''<footer>© 2026 TasasMunicipales.info · Datos orientativos basados en ordenanzas fiscales municipales. <a href="{rel}aviso-legal/" style="color:var(--gold)">Aviso legal</a> · <a href="{rel}privacidad/" style="color:var(--gold)">Privacidad</a> · <a href="{rel}cookies/" style="color:var(--gold)">Cookies</a></footer>'''




# ────────────────────────────────────────────────────────────────
# Plantilla de página de MUNICIPIO (rica, tipo Plasencia)
# ────────────────────────────────────────────────────────────────

HEAD_COMMON = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">\n'
)


def estimated_values_for(m):
    """Construye 4 filas de valor catastral razonables en función del tamaño del municipio."""
    pob = m["pob"]
    # valor catastral base según tamaño: más grande, más caros
    if pob >= 200000:
        rows = [
            ("Piso 2 hab. barrio consolidado", 55000),
            ("Piso 3 hab. zona media", 75000),
            ("Piso nuevo/reformado centro", 95000),
            ("Chalet adosado periferia", 120000),
        ]
    elif pob >= 80000:
        rows = [
            ("Piso 2 hab. casco antiguo", 45000),
            ("Piso 3 hab. zona media", 62000),
            ("Piso nuevo/reformado", 82000),
            ("Chalet adosado", 105000),
        ]
    elif pob >= 30000:
        rows = [
            ("Piso 2 hab. centro", 38000),
            ("Piso 3 hab. zona media", 52000),
            ("Piso nuevo", 72000),
            ("Chalet adosado", 95000),
        ]
    elif pob >= 15000:
        rows = [
            ("Piso 2 hab.", 30000),
            ("Piso 3 hab.", 42000),
            ("Casa pueblo rehabilitada", 38000),
            ("Chalet/unifamiliar", 70000),
        ]
    else:
        rows = [
            ("Piso/casa pequeña", 25000),
            ("Piso 3 hab.", 35000),
            ("Casa tradicional", 32000),
            ("Unifamiliar con jardín", 60000),
        ]
    return rows


def fmt_int(n):
    """Formato español: 12345 -> '12.345'."""
    return f"{int(n):,}".replace(",", ".")


def build_muni_quota_table(m):
    rows = estimated_values_for(m)
    tr = []
    for desc, vc in rows:
        anual = round(vc * m["ibi"] / 100)
        mensual = round(anual / 12)
        tr.append(
            f'<tr><td>{desc}</td><td>{fmt_int(vc)} €</td><td class="v">{fmt_int(anual)} €</td><td>{fmt_int(mensual)} €/mes</td></tr>'
        )
    return "\n            ".join(tr)


def build_muni_chart(m):
    """Comparativa con otros municipios de la misma CCAA."""
    cmunis = sorted(ccaa_munis(m["ccaa_slug"]), key=lambda x: x["ibi"])
    if not cmunis:
        return ""
    min_ibi = cmunis[0]["ibi"]
    max_ibi = cmunis[-1]["ibi"]
    lines = []
    for cm in cmunis:
        pct = 70 + (cm["ibi"] - min_ibi) / max(max_ibi - min_ibi, 0.001) * 30
        is_curr = cm["slug"] == m["slug"] and cm.get("prov_slug", m["prov_slug"]) == m["prov_slug"]
        label_style = 'style="font-weight:900;color:var(--accent)"' if is_curr else 'style=""'
        bar_style = f'style="width:{pct:.0f}%;background:linear-gradient(90deg,var(--accent),#e8734a)"' if is_curr else f'style="width:{pct:.0f}%;"'
        lines.append(
            f'''<div class="chart-bar-row">
    <span class="chart-label" {label_style}>{cm["nombre"]}</span>
    <div class="chart-bar-wrap">
      <div class="chart-bar" {bar_style}><span>{cm["ibi"]:.2f}%</span></div>
    </div>
  </div>'''
        )
    return '<div class="chart-container">\n  ' + "\n  ".join(lines) + "\n</div>"


def build_prov_siblings(m):
    sibs = [x for x in provincia_munis(m["ccaa_slug"], m["prov_slug"]) if x["slug"] != m["slug"]]
    if not sibs:
        return ""
    items = []
    for s in sibs:
        items.append(
            f'<li><a href="../../../{m["ccaa_slug"]}/{m["prov_slug"]}/{s["slug"]}/">{s["nombre"]}</a> — IBI {s["ibi"]:.2f}%, Basuras {s["basuras"]} €/año — '
            f'<a href="../../../{m["ccaa_slug"]}/{m["prov_slug"]}/{s["slug"]}/" style="color:var(--accent);font-size:.82rem">Ver guía →</a></li>'
        )
    return f'''
      <section class="sec">
        <h2>Otros municipios de {m["prov_nombre"]}</h2>
        <p>Consulta las guías fiscales de municipios cercanos en la misma provincia:</p>
        <ul>
          {"".join(items)}
        </ul>
      </section>'''


def build_muni_jsonld(m):
    url = SITE_URL + m["url_path"]
    return f'''<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"Article",
  "headline":"IBI, basuras y plusvalía en {m["nombre"]} 2026",
  "url":"{url}",
  "datePublished":"2026-02-01",
  "dateModified":"{TODAY}",
  "author":{{"@type":"Person","name":"Aithamy Rivero","url":"https://tasasmunicipales.info/sobre-nosotros/"}},
  "publisher":{{"@type":"Organization","name":"TasasMunicipales.info"}}
}}
</script>
<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"BreadcrumbList",
  "itemListElement":[
    {{"@type":"ListItem","position":1,"name":"Inicio","item":"https://tasasmunicipales.info/"}},
    {{"@type":"ListItem","position":2,"name":"{CCAA[m["ccaa_slug"]]["nombre"]}","item":"https://tasasmunicipales.info/{m["ccaa_slug"]}/"}},
    {{"@type":"ListItem","position":3,"name":"{m["nombre"]}","item":"{url}"}}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"FAQPage",
  "mainEntity":[
    {{"@type":"Question","name":"¿Cuánto se paga de IBI en {m["nombre"]} en 2026?","acceptedAnswer":{{"@type":"Answer","text":"El tipo del IBI urbano en {m["nombre"]} es del {m["ibi"]:.2f}%. La cuota se calcula multiplicando el valor catastral del inmueble por ese tipo. Por ejemplo, con un valor catastral de 50.000 € la cuota anual sería de {fmt_int(round(50000*m['ibi']/100))} €."}}}},
    {{"@type":"Question","name":"¿Cuándo se paga el IBI en {m["nombre"]}?","acceptedAnswer":{{"@type":"Answer","text":"El período voluntario de pago del IBI en {m["nombre"]} es del {m["periodo"]}. Fuera de ese plazo se inicia el período ejecutivo con recargo del 5%, 10% y 20% según demora."}}}},
    {{"@type":"Question","name":"¿Cuál es la tasa de basuras en {m["nombre"]}?","acceptedAnswer":{{"@type":"Answer","text":"La tasa de basuras para vivienda habitual en {m["nombre"]} es de {m["basuras"]} €/año. Los locales comerciales pagan tarifas superiores según superficie. La tasa debe cubrir íntegramente el coste del servicio por aplicación de la Ley 7/2022 de Residuos."}}}},
    {{"@type":"Question","name":"¿Qué bonificaciones hay en el IBI en {m["nombre"]}?","acceptedAnswer":{{"@type":"Answer","text":"En {m["nombre"]} hay bonificaciones para familia numerosa (hasta {m["fn"]}%), energía solar / renovables ({m["solar"]}% durante 3 años), domiciliación SEPA (1–5%) y VPO nueva construcción (hasta 50% durante 3 años). Deben solicitarse expresamente antes del 31 de marzo."}}}}
  ]
}}
</script>'''


def muni_html(m):
    rel = "../../../"
    lead = m.get("lead", f"{m['nombre']}, con {fmt_int(m['pob'])} habitantes (INE {m['pobann']}), es un municipio de la provincia de {m['prov_nombre']} ({CCAA[m['ccaa_slug']]['nombre']}). Su mercado inmobiliario, las particularidades de sus ordenanzas fiscales y los servicios municipales determinan la presión fiscal local sobre el IBI, la tasa de basuras y la plusvalía.")
    consejo = m.get("consejo", f"En {m['nombre']}, si tu vivienda habitual está empadronada y cumples los requisitos, solicita la bonificación por domiciliación del IBI antes del 28 de febrero. Es una reducción permanente y compatible con el resto de bonificaciones (familia numerosa, renovables, VPO).")
    boletin_name, boletin_url, boletin_ref = m["boletin"]
    sede = m["sede"]

    # medio valor catastral para sidebar resumen
    rows = estimated_values_for(m)
    mid_vc = rows[1][1]  # 2ª fila
    mid_quota = round(mid_vc * m["ibi"] / 100)
    total_est = mid_quota + m["basuras"]

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel}apple-touch-icon.png">
  <title>IBI, basuras y plusvalía en {m["nombre"]} 2026 — Guía fiscal completa</title>
  <meta name="description" content="Guía fiscal de {m['nombre']} ({m['prov_nombre']}) 2026: IBI urbano {m['ibi']:.2f}%, tasa de basuras {m['basuras']} €/año, plusvalía municipal, bonificaciones familia numerosa hasta {m['fn']}% y energía solar {m['solar']}%. Datos de la ordenanza actualizada.">
  <meta name="keywords" content="IBI {m['nombre']} 2026, tasa basuras {m['nombre']}, plusvalía {m['nombre']}, bonificaciones IBI {m['nombre']}">
  <link rel="canonical" href="{SITE_URL}{m['url_path']}">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:title" content="IBI, basuras y plusvalía en {m['nombre']} 2026 — Guía fiscal">
  <meta property="og:description" content="IBI {m['ibi']:.2f}%, basuras {m['basuras']} €/año y plusvalía en {m['nombre']} ({m['prov_nombre']}) 2026.">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}{m['url_path']}">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  {HEAD_COMMON}
  <link rel="stylesheet" href="{rel}styles.css">
</head>
<body>
{header_nav(rel)}
<div class="bc"><a href="{rel}">Inicio</a><span>›</span><a href="{rel}{m['ccaa_slug']}/">{CCAA[m['ccaa_slug']]['nombre']}</a><span>›</span><strong>{m['nombre']}</strong></div>
<div class="wrap">
  <section class="hero">
    <div class="hero-main card">
      <span class="eyebrow">Guía Fiscal Municipal 2026</span>
      <h1>{m['nombre']}: IBI, basuras, plusvalía y bonificaciones</h1>
      <p class="lead">{lead}</p>
      <p class="meta"><strong>{CCAA[m['ccaa_slug']]['nombre']} · {m['prov_nombre']}</strong> · Población: {fmt_int(m['pob'])} hab. · Actualizado: {TODAY}</p>
      <div class="author-box">✍️ Por <a href="{rel}sobre-nosotros/">Aithamy Rivero</a> · Fuente: <a href="{boletin_url}" target="_blank" rel="nofollow noopener">{boletin_name} {boletin_ref}</a></div>
    </div>
    <aside class="hero-side card">
      <h2>Datos clave 2026</h2>
      <ul class="quick">
        <li><strong>IBI urbano:</strong> <span class="v">{m['ibi']:.2f}%</span></li>
        <li><strong>IBI rústico:</strong> <span class="v">{m['ibir']:.2f}%</span></li>
        <li><strong>Período de pago:</strong> {m['periodo']}</li>
        <li><strong>Basura vivienda:</strong> {m['basuras']} €/año</li>
        <li><strong>Bonif. familia numerosa:</strong> Hasta {m['fn']}%</li>
        <li><strong>Bonif. energía solar:</strong> {m['solar']}%</li>
      </ul>
    </aside>
  </section>

  <div class="layout">
    <main>
      <section class="sec">
        <h2>IBI 2026 en {m['nombre']}: cuánto se paga y cuándo</h2>
        <p>El tipo del IBI urbano en {m['nombre']} es del <strong>{m['ibi']:.2f}%</strong>, aprobado en la última ordenanza fiscal publicada en <a href="{boletin_url}" target="_blank" rel="nofollow noopener">{boletin_name} {boletin_ref}</a>. La cuota depende del valor catastral del inmueble, que puedes consultar en tu recibo anterior o en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">Sede del Catastro</a>.</p>
        <h3>Cuotas estimadas según valor catastral real en {m['nombre']}</h3>
        <table class="dt">
          <thead><tr><th>Tipo de inmueble</th><th>Valor catastral</th><th>Cuota anual</th><th>Cuota mensual</th></tr></thead>
          <tbody>
            {build_muni_quota_table(m)}
          </tbody>
        </table>
        <div class="note"><strong>💡 ¿Cómo se calcula?</strong> <em>Cuota = Valor catastral × {m['ibi']:.2f}%</em>. El valor catastral aparece en tu recibo del IBI o en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sede del Catastro</a>. Las bonificaciones se restan después.</div>
        <h3>¿Cómo consultar tu valor catastral en la Sede del Catastro?</h3>
        <p>Para conocer tu valor catastral exacto, accede a <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a>. Necesitarás certificado digital, Cl@ve PIN o DNI electrónico. En el menú «Consulta de datos catastrales», selecciona «Consulta de un inmueble» e introduce la referencia catastral (aparece en tu recibo del IBI) o busca por dirección. El sistema mostrará el valor catastral total, el valor del suelo y el de la construcción por separado. Este dato es imprescindible para verificar que el IBI que te cobran corresponde a tu inmueble y no contiene errores.</p>
      </section>

      <section class="sec">
        <h2>Tasa de basuras en {m['nombre']}: {m['basuras']} €/año</h2>
        <p>El importe de <strong>{m['basuras']} €/año</strong> para vivienda habitual es la tarifa doméstica general aprobada por el Ayuntamiento de {m['nombre']}. Los locales comerciales y naves industriales pagan tarifas diferenciadas según superficie y actividad. El servicio de recogida incluye desde 2024/2025 contenedor específico de fracción orgánica (biorresiduos) en aplicación de la Ley 7/2022.</p>
        <table class="dt">
          <thead><tr><th>Concepto</th><th>Importe</th></tr></thead>
          <tbody>
            <tr><td>Vivienda habitual</td><td class="v">{m['basuras']} €/año</td></tr>
            <tr><td>Equivalente mensual</td><td>{m['basuras']/12:.2f} €/mes</td></tr>
            <tr><td>Período de pago</td><td>{m['periodo']}</td></tr>
          </tbody>
        </table>
        <p>La tasa de basuras se ha incrementado en la mayoría de municipios españoles en 2025–2026 por la <strong>Ley 7/2022 de Residuos y Suelos Contaminados</strong>, que obliga a los ayuntamientos a cubrir el coste íntegro del servicio con las tasas cobradas. En {m['nombre']}, esta adaptación ha supuesto una revisión al alza para cumplir con el principio de cobertura de costes establecido en el artículo 11.3 de dicha ley.</p>
        <p>En caso de alquiler, el sujeto pasivo es legalmente el propietario del inmueble, aunque el contrato de arrendamiento puede trasladar el pago al inquilino si se pacta expresamente por escrito en una cláusula específica. Para reclamar un recibo incorrecto (por superficie, uso o titular erróneo) dispones de 1 mes desde la notificación en la sede electrónica del Ayuntamiento.</p>
      </section>

      <section class="sec">
        <h2>Plusvalía municipal en {m['nombre']}</h2>
        <p>{m['nombre']} aplica la normativa estatal de plusvalía municipal (IIVTNU) con coeficientes municipales aprobados en ordenanza. Desde la sentencia del Tribunal Constitucional (STC 182/2021) y el Real Decreto-ley 26/2021, el contribuyente puede optar por el <strong>método objetivo</strong> (basado en coeficientes sobre el valor catastral del suelo) o el <strong>método real</strong> (incremento real entre precio de adquisición y de transmisión), eligiendo el que resulte menos gravoso.</p>
        <h3>Plazos legales para declarar la plusvalía</h3>
        <ul>
          <li><strong>Compraventa:</strong> 30 días hábiles desde la fecha de escritura pública.</li>
          <li><strong>Herencia:</strong> 6 meses desde el fallecimiento (prorrogable a 12 meses si se solicita antes del quinto mes al Ayuntamiento de {m['nombre']}).</li>
          <li><strong>Donación:</strong> 30 días hábiles desde la escritura de donación.</li>
        </ul>
        <h3>¿Cuándo NO se paga plusvalía en {m['nombre']}?</h3>
        <p>Si el precio de transmisión es inferior al de adquisición (venta con pérdidas), no existe incremento de valor y no se devenga el impuesto. Debes aportar ambas escrituras (compra y venta) al Ayuntamiento para acreditar la ausencia de plusvalía. También están exentas las transmisiones entre cónyuges derivadas de divorcio o separación judicial y las aportaciones a la sociedad de gananciales.</p>
        <div class="note"><strong>⚖️ Elige el método más favorable en {m['nombre']}.</strong> Consulta la <a href="{sede}" target="_blank" rel="nofollow noopener">sede electrónica del Ayuntamiento</a> para conocer los coeficientes municipales vigentes y simular ambos métodos antes de presentar la autoliquidación.</div>
        <p><a href="{rel}plusvalia/" style="color:var(--accent);font-weight:600">→ Calculadora de plusvalía municipal</a></p>
      </section>

      <section class="sec">
        <h2>Bonificaciones del IBI en {m['nombre']}</h2>
        <table class="dt">
          <thead><tr><th>Bonificación</th><th>Porcentaje</th><th>Requisitos clave</th></tr></thead>
          <tbody>
            <tr><td>Familia numerosa (general)</td><td class="v">Hasta {m['fn']}%</td><td>Título vigente + vivienda habitual + empadronamiento en {m['nombre']}</td></tr>
            <tr><td>Energía solar / renovables</td><td class="v">{m['solar']}%</td><td>Certificado instalador autorizado + boletín eléctrico + solicitud en el ejercicio siguiente a la instalación</td></tr>
            <tr><td>Domiciliación SEPA</td><td>1–5%</td><td>Comunicar IBAN antes del inicio del período voluntario de pago</td></tr>
            <tr><td>VPO (nueva construcción)</td><td>Hasta 50%</td><td>Primeros 3 años desde calificación definitiva de VPO</td></tr>
            <tr><td>Obras de rehabilitación energética</td><td>Variable</td><td>Certificado energético tras la obra + licencia municipal</td></tr>
          </tbody>
        </table>
        <div class="note"><strong>📅 Plazo de solicitud:</strong> antes del 31 de marzo del ejercicio fiscal, salvo que la ordenanza establezca otra fecha. Las bonificaciones no se aplican de oficio: debes solicitarlas activamente en la <a href="{sede}" target="_blank" rel="nofollow noopener">sede electrónica</a> o en las oficinas de recaudación municipal.</div>
        <p><a href="{rel}bonificaciones/" style="color:var(--accent);font-weight:600">→ Guía completa de bonificaciones del IBI</a></p>
      </section>

      <section class="sec">
        <h2>Comparativa IBI urbano en {CCAA[m['ccaa_slug']]['nombre']}</h2>
        <p>El siguiente gráfico compara el tipo de IBI urbano de {m['nombre']} con el de otros municipios de {CCAA[m['ccaa_slug']]['nombre']} incluidos en nuestra guía. Un tipo más alto no siempre implica cuotas más altas: depende del valor catastral de cada inmueble. Consulta la guía comparativa completa en la <a href="{rel}{m['ccaa_slug']}/">página de la comunidad autónoma</a>.</p>
        {build_muni_chart(m)}
        <p style="font-size:0.82rem;color:var(--mid);margin-top:10px">Fuente: Ordenanzas fiscales municipales publicadas en los boletines oficiales correspondientes (2025-2026).</p>
      </section>

      <section class="sec">
        <h2>Consejo práctico para {m['nombre']}</h2>
        <p>{consejo}</p>
      </section>

      <section class="sec">
        <h2>Fuentes oficiales y verificación</h2>
        <ul>
          <li><strong>Ordenanza fiscal:</strong> <a href="{boletin_url}" target="_blank" rel="nofollow noopener">{boletin_name} {boletin_ref}</a></li>
          <li><strong>Sede electrónica del Ayuntamiento:</strong> <a href="{sede}" target="_blank" rel="nofollow noopener">{sede}</a></li>
          <li><strong>Catastro:</strong> <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a> para consultar el valor catastral de tu inmueble.</li>
          <li><strong>Agencia Tributaria:</strong> <a href="https://sede.agenciatributaria.gob.es" target="_blank" rel="nofollow noopener">sede.agenciatributaria.gob.es</a> para consultas sobre tributación estatal relacionada con inmuebles.</li>
        </ul>
        <div class="note"><strong>⚠️ Aviso:</strong> Los datos de esta guía se basan en la ordenanza fiscal publicada en el {boletin_name} {boletin_ref}. Confirma siempre los importes y plazos vigentes en la <a href="{sede}" target="_blank" rel="nofollow noopener">sede electrónica del Ayuntamiento de {m['nombre']}</a> antes de pagar, reclamar o solicitar una bonificación.</div>
      </section>
      {build_prov_siblings(m)}
    </main>

    <aside class="side">
      <div class="card">
        <h2>Navegación</h2>
        <ul>
          <li><a href="{rel}">Inicio</a></li>
          <li><a href="{rel}{m['ccaa_slug']}/">Volver a {CCAA[m['ccaa_slug']]['nombre']}</a></li>
          <li><a href="{rel}municipios/">Todos los municipios</a></li>
          <li><a href="{rel}calculadora-ibi/">Calculadora IBI</a></li>
          <li><a href="{rel}ibi-2026/">IBI 2026</a></li>
          <li><a href="{rel}bonificaciones/">Bonificaciones</a></li>
          <li><a href="{rel}tasa-basuras/">Tasa de basuras</a></li>
          <li><a href="{rel}plusvalia/">Plusvalía</a></li>
          <li><a href="{rel}sobre-nosotros/">Sobre nosotros</a></li>
        </ul>
      </div>
      <div class="card" style="padding:16px">
        <h3 style="font-size:0.88rem;margin-bottom:8px">📊 Resumen fiscal</h3>
        <p style="font-size:0.8rem;color:var(--mid);margin-bottom:6px">Coste anual estimado para un piso de valor catastral medio en {m['nombre']}:</p>
        <table style="width:100%;font-size:0.8rem">
          <tr><td>IBI (VC {fmt_int(mid_vc)} €)</td><td style="text-align:right;font-weight:700;color:var(--accent)">{fmt_int(mid_quota)} €</td></tr>
          <tr><td>Basuras</td><td style="text-align:right;font-weight:700;color:var(--accent)">{m['basuras']} €</td></tr>
          <tr style="border-top:2px solid var(--ink)"><td><strong>Total estimado</strong></td><td style="text-align:right;font-weight:900;color:var(--ink)">{fmt_int(total_est)} €/año</td></tr>
        </table>
      </div>
    </aside>
  </div>
</div>
{build_muni_jsonld(m)}
{footer_small(rel)}
<script src="{rel}cookie-consent.js" defer></script>
</body>
</html>
'''




# ────────────────────────────────────────────────────────────────
# Generador de HUB de CCAA
# ────────────────────────────────────────────────────────────────

CCAA_CONTEXTS = {
    "aragon": {
        "intro": "Aragón destaca por aplicar <strong>tipos de IBI moderados</strong>, entre los más bajos de España. La presencia del corredor del Ebro, las comarcas pirenaicas y la dispersión rural condicionan los valores catastrales y la cobertura de servicios municipales. El tramo del IBI urbano oscila desde el <strong>0,57% de Jaca</strong> hasta el <strong>0,625% de Zaragoza capital</strong>.",
        "basuras": "En Aragón, la tasa de basuras se mueve entre los <strong>88 €/año de Monzón</strong> y los <strong>118 €/año de Zaragoza capital</strong>. Los municipios medios aplican tarifas muy contenidas gracias a la gestión comarcal de residuos.",
        "bonif": "Aragón es líder nacional en instalación de placas fotovoltaicas per cápita. La bonificación IBI por renovables (25%–30% durante 3 años) tiene especial aplicación práctica. La bonificación de familia numerosa varía entre 20%–50% según el municipio.",
    },
    "asturias": {
        "intro": "Asturias combina grandes núcleos urbanos del área central (Gijón, Oviedo, Avilés) con municipios costeros (Llanes, Villaviciosa, Navia) y comarcas mineras (Mieres, Langreo, Lena). El tipo impositivo del IBI urbano varía entre el <strong>0,60% de Cangas de Onís</strong> y el <strong>0,67% de Oviedo</strong>.",
        "basuras": "La tasa de basuras se sitúa entre los <strong>98 € de Castrillón</strong> y los <strong>124 € de Oviedo</strong>. Los municipios costeros aplican tarifas diferenciadas para segundas residencias frecuentes en la franja turística.",
        "bonif": "En Asturias destaca la bonificación de hasta 40% por familia numerosa en Gijón/Oviedo y el mayor peso de rehabilitación energética en inmuebles tradicionales de las cuencas mineras y costa.",
    },
    "castilla-la-mancha": {
        "intro": "Castilla-La Mancha presenta una alta heterogeneidad fiscal: desde ciudades industriales (Puertollano, Talavera) hasta municipios del corredor Madrid-Toledo (Illescas, Seseña, Azuqueca). El IBI urbano varía desde el <strong>0,58% de Seseña</strong> hasta el <strong>0,68% de Talavera de la Reina</strong>.",
        "basuras": "La tasa de basuras oscila entre los <strong>98 €/año de Daimiel</strong> y los <strong>145 €/año de Talavera de la Reina</strong>. Los municipios del corredor Madrid han subido notablemente sus tarifas por el crecimiento poblacional y la Ley 7/2022.",
        "bonif": "Los municipios del corredor Madrid aplican el tipo VPO (50%) con mayor frecuencia por el gran parque de vivienda nueva. Las capitales (Toledo, Ciudad Real, Albacete, Guadalajara, Cuenca) bonifican hasta 50% a familias numerosas especiales.",
    },
    "castilla-y-leon": {
        "intro": "Castilla y León presenta una situación fiscal particular: muchos valores catastrales de municipios medianos no se han actualizado desde hace más de una década, lo que suaviza la cuota efectiva aunque el tipo aplicado parezca moderado. El IBI urbano varía entre el <strong>0,60% de Burgos/Soria</strong> y el <strong>0,67% de Ponferrada</strong>.",
        "basuras": "La tasa de basuras va desde los <strong>92 € de Béjar</strong> hasta los <strong>135 € de Ponferrada</strong>. Las capitales (Valladolid, Burgos, Salamanca, León) se mueven entre 112 € y 120 €/año.",
        "bonif": "Las capitales aplican hasta 50% de bonificación a familias numerosas especiales y hasta 95% a BIC en casco histórico. Soria mantiene bonificaciones especiales por despoblación y atracción de empresas.",
    },
    "extremadura": {
        "intro": "Extremadura tiene una alta proporción de propietarios (>80%) y valores catastrales moderados, lo que compensa tipos de IBI ligeramente altos. El tipo urbano varía entre el <strong>0,60% de Badajoz capital</strong> y el <strong>0,66% de Mérida</strong>.",
        "basuras": "La tasa de basuras oscila entre los <strong>78 €/año de Trujillo</strong> y los <strong>130 €/año de Mérida</strong>. Los municipios medianos mantienen tarifas muy contenidas.",
        "bonif": "Alto potencial de irradiación solar → bonificación por renovables (20%–50%) muy rentable. Las capitales bonifican hasta 50% a familias numerosas especiales y hasta 95% a BIC en cascos históricos.",
    },
    "galicia": {
        "intro": "Galicia aplica los tipos de IBI urbano más bajos de nuestra guía, pero con valores catastrales más actualizados que en otras comunidades. El IBI urbano varía entre el <strong>0,54% de O Carballiño y Pontevedra</strong> y el <strong>0,615% de A Coruña capital</strong>.",
        "basuras": "La tasa de basuras es la más baja en España en los municipios del interior (82 € en O Carballiño, 85 € en Monforte). Las capitales (A Coruña, Santiago, Vigo, Ourense, Lugo, Pontevedra) se mueven entre 90 € y 120 €/año.",
        "bonif": "Alta frecuencia de transmisiones hereditarias → valorar método real en plusvalía. Las capitales bonifican hasta 95% a BIC y hasta 50% a familia numerosa especial. Los municipios con Camino de Santiago aplican bonificaciones turísticas específicas.",
    },
    "murcia": {
        "intro": "La Región de Murcia combina capital (Murcia, Cartagena), municipios metropolitanos (Molina de Segura, Alcantarilla), costa (Mazarrón, Águilas, San Javier, San Pedro, Cartagena-La Manga) y Altiplano (Yecla, Jumilla). El IBI urbano varía entre el <strong>0,61% de Caravaca</strong> y el <strong>0,66% de Molina de Segura</strong>.",
        "basuras": "La tasa de basuras se sitúa entre los <strong>100 €/año de Totana</strong> y los <strong>128 €/año de Molina de Segura</strong>. Los municipios costeros aplican tarifas diferenciadas para segundas residencias en temporada alta.",
        "bonif": "Alta irradiación solar → bonificación por renovables (30%) especialmente rentable. Las capitales bonifican hasta 50% a familias numerosas especiales. Municipios costeros con tarifas diferenciadas habitual/vacacional.",
    },
}


def ccaa_hub_html(ccaa_slug):
    ccaa = CCAA[ccaa_slug]
    rel = "../"
    total = total_munis()
    total_cc = total_ccaa()
    munis = ccaa_munis(ccaa_slug)
    ctx = CCAA_CONTEXTS.get(ccaa_slug, {})
    # group by provincia (grid)
    group_cards = []
    for prov_slug, prov in ccaa["provincias"].items():
        for m in prov["municipios"]:
            ibi_disp = f'{m["ibi"]:.2f}'.replace(".", ",")
            group_cards.append(
                f'<a href="{rel}{ccaa_slug}/{prov_slug}/{m["slug"]}/" class="mt"><div class="reg">{prov["nombre"]}</div><div class="nm">{m["nombre"]}</div><div class="ib">IBI {ibi_disp}%</div></a>'
            )
    # CCAA tab bar
    other_cc = []
    for cc_slug, cc in CCAA.items():
        cls = "ct on" if cc_slug == ccaa_slug else "ct"
        other_cc.append(f'<a href="{rel}{cc_slug}/" class="{cls}">{cc["nombre"]}</a>')
    intro = ctx.get("intro", f"Consulta el IBI, tasa de basuras, plusvalía y bonificaciones de los municipios de {ccaa['nombre']}.")
    basuras = ctx.get("basuras", "La tasa de basuras se ha revisado en 2025–2026 por la Ley 7/2022 de Residuos.")
    bonif = ctx.get("bonif", "Hay bonificaciones para familia numerosa, energía solar, VPO y domiciliación del IBI.")
    # listas por provincia bajo la grid principal para interlinking
    prov_groups_html = []
    for prov_slug, prov in ccaa["provincias"].items():
        prov_lis = []
        for m in prov["municipios"]:
            prov_lis.append(
                f'<li><a href="{rel}{ccaa_slug}/{prov_slug}/{m["slug"]}/">{m["nombre"]}</a> <span style="color:var(--mid);font-size:.72rem">· IBI {("%.2f" % m["ibi"]).replace(".", ",")}% · Basuras {m["basuras"]} €/año</span></li>'
            )
        prov_groups_html.append(
            f'<div class="tc" style="display:block;padding:14px 18px;">'
            f'<h3 style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;margin-bottom:10px;color:var(--ink);">{prov["nombre"]}</h3>'
            f'<ul style="list-style:none;padding:0;margin:0;">{"".join(prov_lis)}</ul>'
            f'</div>'
        )

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel}apple-touch-icon.png">
  <title>IBI y Tasas Municipales {ccaa['nombre']} 2026 — Por Municipio</title>
  <meta name="description" content="IBI, tasa de basuras y plusvalía en {len(munis)} municipios de {ccaa['nombre']} 2026. Ordenanzas fiscales actualizadas, bonificaciones y plazos de pago.">
  <link rel="canonical" href="{SITE_URL}/{ccaa_slug}/">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="IBI y Tasas Municipales {ccaa['nombre']} 2026">
  <meta property="og:description" content="IBI, basuras y plusvalía en {len(munis)} municipios de {ccaa['nombre']} 2026.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/{ccaa_slug}/">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  {HEAD_COMMON}
  <link rel="stylesheet" href="{rel}styles.css">
</head>
<body>
{header_nav(rel)}
<div class="bc"><a href="{rel}">Inicio</a><span>›</span><a href="{rel}comunidades/">Comunidades</a><span>›</span><strong>{ccaa['nombre']}</strong></div>
<div class="wrap">
  <h1>Tasas Municipales {ccaa['nombre']} 2026</h1>
  <p class="lead">Consulta el IBI, tasa de basuras, plusvalía y bonificaciones de los <strong>{len(munis)} municipios</strong> de {ccaa['nombre']} incluidos en la guía. Datos actualizados con las ordenanzas fiscales vigentes.</p>

  <h2 class="sec">Municipios disponibles en {ccaa['nombre']} ({len(munis)})</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(205px,1fr));gap:11px;margin-bottom:30px;">
    {"".join(group_cards)}
  </div>

  <h2 class="sec">Municipios por provincia</h2>
  <div class="g3" style="margin-bottom:30px;">
    {"".join(prov_groups_html)}
  </div>

  <h2 class="sec">¿Qué impuesto quieres consultar?</h2>
  <div class="g4">
    <a href="{rel}ibi-2026/" class="tc"><div class="tc-icon">🏠</div><h3>IBI 2026</h3><p>Tipo impositivo, cuándo se paga, fecha de cobro y cómo fraccionar el pago en tu municipio.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}tasa-basuras/" class="tc"><div class="tc-icon">🗑️</div><h3>Tasa de Basuras</h3><p>Importe anual, quién la paga en alquiler y cómo reclamar si hay errores en el recibo.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}plusvalia/" class="tc"><div class="tc-icon">📈</div><h3>Plusvalía Municipal</h3><p>Calculadora actualizada, cuánto se paga y cómo evitar la plusvalía en herencias o donaciones.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}bonificaciones/" class="tc"><div class="tc-icon">🎁</div><h3>Bonificaciones</h3><p>Familia numerosa, placas solares, domiciliación… descubre todas las reducciones posibles en tu IBI.</p><span class="tc-arrow">Ver guía completa →</span></a>
  </div>

  <div class="ed">
    <h2 class="sec">El IBI en {ccaa['nombre']}: contexto y particularidades</h2>
    <p>{intro}</p>
    <p><strong>Tasa de basuras:</strong> {basuras}</p>
    <p><strong>Bonificaciones:</strong> {bonif}</p>
    <p>Los datos de esta página se basan en las ordenanzas fiscales publicadas en el <strong>{ccaa['boletin'][0]}</strong> ({ccaa['boletin'][2]}) y se actualizan cuando se produce una modificación oficial. Consulta la página de cada municipio para ver los datos detallados, las bonificaciones específicas, la comparativa con municipios cercanos y la calculadora adaptada al tipo impositivo local.</p>
  </div>

  <h2 class="sec">Otras comunidades autónomas</h2>
  <div class="ct-grid">
    {"".join(other_cc)}
  </div>
</div>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Inicio","item":"{SITE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Comunidades","item":"{SITE_URL}/comunidades/"}},{{"@type":"ListItem","position":3,"name":"{ccaa['nombre']}","item":"{SITE_URL}/{ccaa_slug}/"}}]}}
</script>
{footer_large(rel)}
<script src="{rel}cookie-consent.js" defer></script>
</body>
</html>
'''




# ────────────────────────────────────────────────────────────────
# HOME (/index.html)
# ────────────────────────────────────────────────────────────────
def home_html():
    total = total_munis()
    total_cc = total_ccaa()

    # Popular muni cards
    popular_slugs = [
        ("extremadura", "caceres", "plasencia", "Plasencia", "Extremadura · Cáceres"),
        ("murcia", "murcia", "cartagena", "Cartagena", "Murcia · Murcia"),
        ("castilla-y-leon", "valladolid", "valladolid", "Valladolid", "Castilla y León · Valladolid"),
        ("galicia", "pontevedra", "vigo", "Vigo", "Galicia · Pontevedra"),
        ("castilla-la-mancha", "toledo", "toledo", "Toledo", "Castilla-La Mancha · Toledo"),
        ("aragon", "zaragoza", "zaragoza", "Zaragoza", "Aragón · Zaragoza"),
        ("asturias", "asturias", "gijon", "Gijón", "Asturias · Asturias"),
        ("galicia", "a-coruna", "a-coruna", "A Coruña", "Galicia · A Coruña"),
    ]
    popular_cards = []
    for ccaa_s, prov_s, slug, nom, region in popular_slugs:
        popular_cards.append(f'''
      <a href="{ccaa_s}/{prov_s}/{slug}/" class="muni-card">
        <div class="card-region">{region}</div>
        <div class="card-name">{nom}</div>
        <div class="card-links">
          <span class="tag">IBI</span><span class="tag">Basuras</span><span class="tag">Plusvalía</span>
        </div>
      </a>''')

    # Tiles
    tiles = []
    for cc_slug, cc in CCAA.items():
        tiles.append(f'<button class="ccaa-tile active" data-ccaa="{cc_slug}">{cc["nombre"]}</button>')

    # Panels: por CCAA, lista por provincia
    panels = []
    muni_num = 0
    for cc_slug, cc in CCAA.items():
        prov_cols = []
        for prov_slug, prov in cc["provincias"].items():
            lis = []
            for m in prov["municipios"]:
                muni_num += 1
                lis.append(
                    f'<li><span class="muni-num">{muni_num}</span><a href="{cc_slug}/{prov_slug}/{m["slug"]}/">{m["nombre"]}</a></li>'
                )
            prov_cols.append(
                f'''      <div class="prov-group">
        <div class="prov-title">{prov["nombre"]}</div>
        <ul class="muni-list">
{"".join(l + chr(10) for l in lis)}        </ul>
      </div>'''
            )
        panels.append(f'''
  <div class="ccaa-detail-panel" id="panel-{cc_slug}">
    <div class="detail-header">
      <h3>🗺️ {cc["nombre"]} — Municipios disponibles</h3>
      <button class="detail-close" onclick="closePanel('{cc_slug}')">✕ Cerrar</button>
    </div>
    <div class="prov-cols">
{chr(10).join(prov_cols)}
    </div>
  </div>''')

    active_list = ','.join([f"'{s}'" for s in CCAA.keys()])

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
  <title>Tasas Municipales España 2026: IBI, Basuras y Plusvalía</title>
  <meta name="description" content="IBI, tasa de basuras y plusvalía de {total} municipios en España 2026. {total_cc} comunidades autónomas, ordenanzas actualizadas, calculadora y bonificaciones.">
  <meta name="keywords" content="IBI 2026, tasa basuras municipio, plusvalía municipal, bonificaciones IBI, impuestos municipales España">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <link rel="canonical" href="{SITE_URL}/">
  <meta property="og:title" content="Guía de Tasas Municipales 2026 – IBI, Basuras y Plusvalía">
  <meta property="og:description" content="Consulta el IBI, tasa de basuras, plusvalía y bonificaciones de cualquier municipio de España.">
  <meta property="og:type" content="website">
  {HEAD_COMMON}
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "Tasas Municipales España 2026",
    "url": "{SITE_URL}",
    "description": "Guía completa de IBI, tasa de basuras, plusvalía y bonificaciones por municipio en España 2026",
    "potentialAction": {{
      "@type": "SearchAction",
      "target": "{SITE_URL}/buscar/?q={{search_term_string}}",
      "query-input": "required name=search_term_string"
    }}
  }}
  </script>
  <link rel="stylesheet" href="styles.css">
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-top">
    <div class="logo">
      <span class="logo-main">TasasMunicipales</span>
      <span class="logo-sub">Guía de Impuestos Locales · España 2026</span>
    </div>
    <nav>
      <a href="comunidades/">Comunidades</a>
      <a href="municipios/">Municipios</a>
      <a href="ibi-2026/">IBI 2026</a>
      <a href="calculadora-ibi/">Calculadora</a>
      <a href="tasa-basuras/">Basuras</a>
      <a href="plusvalia/">Plusvalía</a>
      <a href="bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>

<!-- HERO -->
<section class="hero" aria-label="Buscador de tasas municipales">
  <div class="hero-inner">
    <span class="hero-badge">Actualizado 2026</span>
    <h1>IBI, Basuras y Plusvalía<br>de <span>tu municipio</span></h1>
    <p>Consulta cuánto pagas, cuándo se cobra y qué bonificaciones puedes solicitar en cualquiera de los <strong>{total} municipios</strong> incluidos en esta guía.</p>
    <div class="search-box" role="search">
      <input type="search" placeholder="Busca tu municipio… ej: Plasencia, Vigo, Toledo…" aria-label="Buscar municipio">
      <button type="button" aria-label="Buscar">🔍</button>
    </div>
  </div>
</section>

<section class="section">
  <div class="section-header">
    <h2>¿Qué impuesto quieres consultar?</h2>
  </div>
  <div class="types-grid">
    <a href="ibi-2026/" class="type-card">
      <div class="type-icon">🏠</div><h3>IBI 2026</h3>
      <p>Tipo impositivo, cuánto se paga, fecha de cobro y cómo fraccionar el pago en tu municipio.</p>
    </a>
    <a href="tasa-basuras/" class="type-card">
      <div class="type-icon">🗑️</div><h3>Tasa de Basuras</h3>
      <p>Importe anual, quién la paga en alquiler y cómo reclamar si hay errores en el recibo.</p>
    </a>
    <a href="plusvalia/" class="type-card">
      <div class="type-icon">📈</div><h3>Plusvalía Municipal</h3>
      <p>Calculadora actualizada, cuánto se paga y cómo evitar la plusvalía en herencias o donaciones.</p>
    </a>
    <a href="bonificaciones/" class="type-card">
      <div class="type-icon">🎁</div><h3>Bonificaciones</h3>
      <p>Familia numerosa, placas solares, domiciliación… descubre todas las reducciones posibles en tu IBI.</p>
    </a>
  </div>
</section>

<div class="ruled bg-alt">
  <section class="section">
    <div class="section-header">
      <h2>🔥 Municipios más consultados</h2>
      <a href="municipios/">Ver todos los municipios →</a>
    </div>
    <div class="popular-grid">
      {"".join(popular_cards)}
    </div>
  </section>
</div>

<section class="section">
  <div class="section-header">
    <h2>Tasas municipales por Comunidad Autónoma</h2>
    <a href="comunidades/">Ver todas →</a>
  </div>
  <div class="ccaa-tiles-grid">
    {"".join(tiles)}
  </div>
  {"".join(panels)}
</section>

<div class="info-strip">
  <div class="info-strip-inner">
    <div>
      <h2>¿Por qué pagar de más?</h2>
      <p>Muchos propietarios desconocen las bonificaciones que les corresponden. En España, los ayuntamientos están obligados a aplicar reducciones en el IBI para familias numerosas, viviendas con instalaciones de energía renovable o inmuebles de interés histórico.</p>
      <p>Nuestra guía te muestra, municipio a municipio, qué bonificaciones puedes solicitar, cuándo pedirlas y cómo hacerlo paso a paso, sin letra pequeña. La información está basada en las ordenanzas fiscales aprobadas por cada ayuntamiento y se actualiza cada año coincidiendo con la aprobación de los presupuestos municipales.</p>
    </div>
    <div>
      <h2>Preguntas frecuentes</h2>
      <ul class="faq-list">
        <li><div class="faq-q">¿Cuándo se paga el IBI en 2026?</div><div class="faq-a">Cada municipio fija su período voluntario. En la mayoría va del 1 de octubre al 30 de noviembre. Busca tu municipio para las fechas exactas.</div></li>
        <li><div class="faq-q">¿Quién paga la tasa de basura en un alquiler?</div><div class="faq-a">Legalmente corresponde al propietario, aunque muchos contratos la trasladan al inquilino si así se pacta por escrito.</div></li>
        <li><div class="faq-q">¿Cómo se calcula la plusvalía municipal?</div><div class="faq-a">Desde 2021 puedes elegir entre el método objetivo (coeficientes) y el método real (ganancia real). Elige el menos gravoso.</div></li>
        <li><div class="faq-q">¿Puedo fraccionar el IBI?</div><div class="faq-a">La mayoría de ayuntamientos lo permiten sin intereses si se solicita antes del período voluntario.</div></li>
      </ul>
    </div>
  </div>
</div>

<section class="section">
  <div class="section-header"><h2>Sobre esta guía de tasas municipales</h2></div>
  <div style="max-width:860px; line-height:1.9; font-size:0.92rem; color:var(--mid);">
    <p style="margin-bottom:14px;"><strong style="color:var(--ink);">TasasMunicipales</strong> es la guía de referencia sobre impuestos y tasas locales en España. Recogemos y actualizamos cada año las ordenanzas fiscales de <strong>{total} municipios</strong>, con información precisa sobre el <strong>IBI 2026</strong>, la <strong>tasa de basuras</strong>, la <strong>plusvalía municipal</strong> y las <strong>bonificaciones disponibles</strong>.</p>
    <p style="margin-bottom:14px;">Nuestra estructura está organizada por <a href="comunidades/" style="color:var(--accent);">Comunidad Autónoma</a>, <a href="provincias/" style="color:var(--accent);">provincia</a> y municipio. Cada página de municipio enlaza con artículos específicos sobre cómo pagar el IBI, cómo reclamar la tasa de basuras o cómo calcular la plusvalía.</p>
    <p>Actualmente cubrimos {total} municipios en {total_cc} comunidades autónomas: <a href="asturias/" style="color:var(--accent);">Asturias</a>, <a href="extremadura/" style="color:var(--accent);">Extremadura</a>, <a href="castilla-la-mancha/" style="color:var(--accent);">Castilla-La Mancha</a>, <a href="aragon/" style="color:var(--accent);">Aragón</a>, <a href="castilla-y-leon/" style="color:var(--accent);">Castilla y León</a>, <a href="murcia/" style="color:var(--accent);">Murcia</a> y <a href="galicia/" style="color:var(--accent);">Galicia</a>.</p>
  </div>
</section>

{footer_large("")}

<script>
  const activeCCAA = [{active_list}];
  document.querySelectorAll('.ccaa-tile').forEach(btn => {{
    btn.addEventListener('click', function() {{
      const ccaa = this.dataset.ccaa;
      const panel = document.getElementById('panel-' + ccaa);
      if (panel.classList.contains('open')) {{
        panel.classList.remove('open');
        this.style.outline = '';
      }} else {{
        document.querySelectorAll('.ccaa-detail-panel').forEach(p => p.classList.remove('open'));
        document.querySelectorAll('.ccaa-tile').forEach(b => b.style.outline = '');
        panel.classList.add('open');
        this.style.outline = '2px solid var(--accent2)';
        setTimeout(() => panel.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }}), 50);
      }}
    }});
  }});
  function closePanel(ccaa) {{
    document.getElementById('panel-' + ccaa).classList.remove('open');
    const btn = document.querySelector('[data-ccaa="' + ccaa + '"]');
    if (btn) btn.style.outline = '';
  }}
  document.querySelector('.search-box input').addEventListener('input', function(e) {{
    const q = e.target.value.toLowerCase().trim();
    if (!q) {{
      document.querySelectorAll('.muni-list li, .muni-card').forEach(el => el.style.opacity = '1');
      return;
    }}
    const cards = document.querySelectorAll('.muni-list a, .muni-card');
    cards.forEach(card => {{
      const name = card.textContent.toLowerCase();
      const row = card.closest('li') || card;
      row.style.opacity = name.includes(q) ? '1' : '0.25';
    }});
    activeCCAA.forEach(ccaa => {{
      const panel = document.getElementById('panel-' + ccaa);
      if (panel) panel.classList.add('open');
    }});
  }});
  document.querySelector('.search-box input').addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      this.value = '';
      document.querySelectorAll('.muni-list li, .muni-card').forEach(el => el.style.opacity = '1');
    }}
  }});
</script>
<script src="cookie-consent.js" defer></script>
</body>
</html>
'''


# ────────────────────────────────────────────────────────────────
# /municipios/ — LISTADO GLOBAL
# ────────────────────────────────────────────────────────────────
def municipios_index_html():
    total = total_munis()
    rel = "../"
    cards = []
    for m in all_munis():
        ibi_disp = f'{m["ibi"]:.2f}'.replace(".", ",")
        cards.append(
            f'<a href="{rel}{m["ccaa_slug"]}/{m["prov_slug"]}/{m["slug"]}/" class="mt"><div class="reg">{CCAA[m["ccaa_slug"]]["nombre"]} · {m["prov_nombre"]}</div><div class="nm">{m["nombre"]}</div><div class="ib">IBI {ibi_disp}%</div></a>'
        )
    # CCAA links
    ccaa_links = []
    for cc_slug, cc in CCAA.items():
        ccaa_links.append(f'<a href="{rel}{cc_slug}/" class="ct on">{cc["nombre"]}</a>')

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel}apple-touch-icon.png">
  <title>Guía IBI y Tasas por Municipio 2026 — {total} municipios</title>
  <meta name="description" content="IBI 2026, tasa de basuras y plusvalía de {total} municipios en España. Ordenanzas fiscales actualizadas, bonificaciones y plazos de pago por municipio.">
  <link rel="canonical" href="{SITE_URL}/municipios/">
  <meta name="robots" content="index, follow">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta property="og:title" content="Guía IBI y Tasas por Municipio 2026 — {total} municipios">
  <meta property="og:description" content="IBI 2026, tasa de basuras y plusvalía de {total} municipios en España.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/municipios/">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  {HEAD_COMMON}
  <link rel="stylesheet" href="{rel}styles.css">
</head>
<body>
{header_nav(rel)}
<div class="bc"><a href="{rel}">Inicio</a><span>›</span><strong>Municipios</strong></div>
<div class="wrap">
  <span class="tag t-g">{total} municipios disponibles</span>
  <h1>Guía de Tasas Municipales por Municipio 2026</h1>
  <p class="lead">Directorio completo de los <strong>{total} municipios</strong> incluidos en nuestra guía fiscal 2026. Cada página incluye el tipo de IBI, la tasa de basuras, las bonificaciones disponibles, la plusvalía municipal y un consejo práctico específico para ese municipio.</p>
  <div class="hb">
    <strong>🔍 ¿Cómo usar esta guía?</strong>
    Busca tu municipio en la lista inferior. Cada guía incluye: tipo de IBI urbano y rústico con cuotas estimadas para diferentes valores catastrales, tasa de basuras exacta, bonificaciones del IBI (familia numerosa, energía solar, VPO, domiciliación), información sobre la plusvalía municipal, y un gráfico comparativo con otros municipios de la misma comunidad autónoma.
  </div>
  <p>Los datos provienen de las <strong>ordenanzas fiscales publicadas en los boletines oficiales</strong> correspondientes (BOE, DOCM, DOE, BOPA, DOG, BORM, BOA, BOCYL) entre diciembre de 2025 y enero de 2026. Verificamos cada dato con la fuente original y actualizamos la información cuando se producen modificaciones a lo largo del ejercicio.</p>

  <h2 class="sec">Todos los municipios ({total})</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(205px,1fr));gap:11px;margin-bottom:30px;">
    {"".join(cards)}
  </div>

  <h2 class="sec">Buscar por Comunidad Autónoma</h2>
  <div class="ct-grid" style="margin-bottom:34px;">
    {"".join(ccaa_links)}
  </div>

  <h2 class="sec">¿Qué impuesto quieres consultar?</h2>
  <div class="g4">
    <a href="{rel}ibi-2026/" class="tc"><div class="tc-icon">🏠</div><h3>IBI 2026</h3><p>Tipo impositivo, cuándo se paga y cómo fraccionar.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}tasa-basuras/" class="tc"><div class="tc-icon">🗑️</div><h3>Tasa de Basuras</h3><p>Importe anual, quién la paga en alquiler.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}plusvalia/" class="tc"><div class="tc-icon">📈</div><h3>Plusvalía Municipal</h3><p>Calculadora y cómo evitar la plusvalía.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}bonificaciones/" class="tc"><div class="tc-icon">🎁</div><h3>Bonificaciones</h3><p>Familia numerosa, solar, VPO, domiciliación.</p><span class="tc-arrow">Ver guía completa →</span></a>
  </div>

  <div class="hb gold">
    <strong>📋 ¿Qué incluye cada página de municipio?</strong>
    Tipo impositivo del IBI 2026 · Importe de la tasa de basuras · Calculadora de plusvalía · Bonificaciones disponibles · Guía para pagar o reclamar · Comparativa con otros municipios de la CCAA.
  </div>
</div>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Inicio","item":"{SITE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Municipios","item":"{SITE_URL}/municipios/"}}]}}
</script>
{footer_large(rel)}
<script src="{rel}cookie-consent.js" defer></script>
</body>
</html>
'''


# ────────────────────────────────────────────────────────────────
# /comunidades/
# ────────────────────────────────────────────────────────────────
def comunidades_index_html():
    rel = "../"
    total = total_munis()
    total_cc = total_ccaa()
    tiles = []
    for cc_slug, cc in CCAA.items():
        n = sum(len(p["municipios"]) for p in cc["provincias"].values())
        tiles.append(f'<a href="{rel}{cc_slug}/" class="ct on">{cc["nombre"]}<br><small style="font-weight:400;font-size:.62rem;opacity:.85">{n} municipios</small></a>')

    all_cards = []
    for m in all_munis():
        ibi_disp = f'{m["ibi"]:.2f}'.replace(".", ",")
        all_cards.append(
            f'<a href="{rel}{m["ccaa_slug"]}/{m["prov_slug"]}/{m["slug"]}/" class="mt"><div class="reg">{CCAA[m["ccaa_slug"]]["nombre"]}</div><div class="nm">{m["nombre"]}</div><div class="ib">IBI {ibi_disp}%</div></a>'
        )

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel}apple-touch-icon.png">
  <title>Tasas Municipales por Comunidad Autónoma 2026</title>
  <meta name="description" content="IBI, basuras y plusvalía por CCAA 2026. Aragón, Asturias, Castilla-La Mancha, Castilla y León, Extremadura, Galicia y Murcia: {total} municipios en {total_cc} CCAA.">
  <link rel="canonical" href="{SITE_URL}/comunidades/">
  <meta name="robots" content="index, follow">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta property="og:title" content="Tasas Municipales por Comunidad Autónoma 2026">
  <meta property="og:description" content="IBI, basuras y plusvalía por CCAA 2026. Guía de {total} municipios en {total_cc} comunidades autónomas.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/comunidades/">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  {HEAD_COMMON}
  <link rel="stylesheet" href="{rel}styles.css">
</head>
<body>
{header_nav(rel)}
<div class="bc"><a href="{rel}">Inicio</a><span>›</span><strong>Comunidades Autónomas</strong></div>
<div class="wrap">
  <span class="tag t-r">Guía por Comunidad Autónoma</span>
  <h1>Tasas Municipales por Comunidad Autónoma 2026</h1>
  <p class="lead">Consulta la guía fiscal completa de cada comunidad autónoma. Cada municipio tiene sus propias ordenanzas fiscales que determinan el tipo de IBI, la tasa de basuras y las bonificaciones disponibles.</p>
  <div class="hb">
    <strong>📊 ¿Sabías que el IBI varía hasta un 0,14 puntos entre comunidades?</strong>
    El tipo de IBI urbano en nuestra guía oscila entre el 0,54% de O Carballiño/Pontevedra (Galicia) y el 0,68% de Talavera de la Reina (Castilla-La Mancha). La tasa de basuras también presenta diferencias significativas: desde 78 €/año en Trujillo hasta 145 €/año en Talavera de la Reina.
  </div>
  <p>En España, los impuestos locales están regulados por el <strong>Real Decreto Legislativo 2/2004</strong> (Texto Refundido de la Ley Reguladora de las Haciendas Locales), pero cada ayuntamiento fija sus propios tipos dentro de los márgenes legales. Dos viviendas idénticas en municipios diferentes pueden tener cuotas de IBI muy distintas.</p>
  <p>Nuestra guía cubre actualmente <strong>{total} municipios en {total_cc} comunidades autónomas</strong>: Aragón, Asturias, Castilla y León, Castilla-La Mancha, Extremadura, Galicia y Murcia.</p>

  <h2 class="sec">Comunidades autónomas disponibles</h2>
  <div class="ct-grid">
    {"".join(tiles)}
    <a href="{rel}contacto/" rel="nofollow" class="ct" style="border-style:dashed;color:var(--mid)">+ Solicitar<br><small style="font-size:.6rem">tu CCAA</small></a>
  </div>

  <div class="hb">
    <strong>📌 ¿No encuentras tu comunidad?</strong>
    Estamos ampliando la guía. <a href="{rel}contacto/" rel="nofollow" style="color:var(--accent)">Solicita tu municipio →</a> y lo incluiremos en la próxima actualización.
  </div>

  <h2 class="sec">¿Qué impuesto quieres consultar?</h2>
  <div class="g4">
    <a href="{rel}ibi-2026/" class="tc"><div class="tc-icon">🏠</div><h3>IBI 2026</h3><p>Tipo impositivo y fecha de cobro.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}tasa-basuras/" class="tc"><div class="tc-icon">🗑️</div><h3>Tasa de Basuras</h3><p>Importe anual.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}plusvalia/" class="tc"><div class="tc-icon">📈</div><h3>Plusvalía Municipal</h3><p>Calculadora actualizada.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}bonificaciones/" class="tc"><div class="tc-icon">🎁</div><h3>Bonificaciones</h3><p>Reducciones posibles en IBI.</p><span class="tc-arrow">Ver guía completa →</span></a>
  </div>

  <h2 class="sec">Todos los municipios disponibles</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:11px;margin-bottom:32px;">
    {"".join(all_cards)}
  </div>

  <p class="body">La guía de <strong>TasasMunicipales</strong> está organizada por <a href="{rel}comunidades/">Comunidad Autónoma</a> → <a href="{rel}provincias/">Provincia</a> → <a href="{rel}municipios/">Municipio</a>. Cada municipio tiene páginas propias para el <a href="{rel}ibi-2026/">IBI 2026</a>, la <a href="{rel}calculadora-ibi/">Calculadora</a>, la <a href="{rel}tasa-basuras/">tasa de basuras</a>, la <a href="{rel}plusvalia/">plusvalía municipal</a> y las <a href="{rel}bonificaciones/">bonificaciones disponibles</a>.</p>
</div>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Inicio","item":"{SITE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Comunidades Autónomas","item":"{SITE_URL}/comunidades/"}}]}}
</script>
{footer_large(rel)}
<script src="{rel}cookie-consent.js" defer></script>
</body>
</html>
'''


# ────────────────────────────────────────────────────────────────
# /provincias/
# ────────────────────────────────────────────────────────────────
def provincias_index_html():
    rel = "../"
    total = total_munis()
    # card por provincia
    cards = []
    for ccaa_slug, ccaa in CCAA.items():
        for prov_slug, prov in ccaa["provincias"].items():
            lis = []
            for m in prov["municipios"]:
                ibi_disp = f'{m["ibi"]:.2f}'.replace(".", ",")
                lis.append(
                    f'<li style="padding:5px 0;border-bottom:1px solid var(--rule);font-size:.82rem;"><a href="{rel}{ccaa_slug}/{prov_slug}/{m["slug"]}/" style="color:var(--ink);">{m["nombre"]}</a> <span style="font-size:.68rem;color:var(--mid);">IBI {ibi_disp}%</span></li>'
                )
            cards.append(
                f'<div class="tc" style="display:block;padding:18px 20px;">'
                f'<div style="font-size:.63rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--mid);margin-bottom:3px;">{ccaa["nombre"]}</div>'
                f'<h3 style="font-family:\'Playfair Display\',serif;font-size:1.05rem;font-weight:700;margin-bottom:12px;color:var(--ink);">{prov["nombre"]}</h3>'
                f'<ul style="list-style:none;padding:0;">{"".join(lis)}</ul>'
                f'</div>'
            )

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="{rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel}apple-touch-icon.png">
  <title>Tasas Municipales por Provincia 2026 – España</title>
  <meta name="description" content="IBI, basuras y plusvalía por provincia 2026. Cáceres, Badajoz, Toledo, Ciudad Real, Zaragoza, León, Salamanca, Burgos, Murcia, Lugo, A Coruña, Pontevedra, Ourense y más.">
  <link rel="canonical" href="{SITE_URL}/provincias/">
  <meta name="robots" content="index, follow">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta property="og:title" content="Tasas Municipales por Provincia 2026 – España">
  <meta property="og:description" content="IBI, basuras y plusvalía por provincia 2026. {total} municipios indexados.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/provincias/">
  <meta property="og:site_name" content="TasasMunicipales.info">
  <meta property="og:locale" content="es_ES">
  {HEAD_COMMON}
  <link rel="stylesheet" href="{rel}styles.css">
</head>
<body>
{header_nav(rel)}
<div class="bc"><a href="{rel}">Inicio</a><span>›</span><strong>Provincias</strong></div>
<div class="wrap">
  <span class="tag t-d">Guía por Provincia</span>
  <h1>Tasas Municipales por Provincia 2026</h1>
  <p class="lead">Explora los {total} municipios organizados por provincia. La fiscalidad local varía significativamente dentro de cada provincia: las capitales suelen tener tipos de IBI más altos pero también más bonificaciones disponibles.</p>
  <p>En cada provincia, los ayuntamientos fijan sus tipos impositivos de forma independiente, dentro de los márgenes establecidos por la Ley Reguladora de las Haciendas Locales. Esto explica por qué dos municipios vecinos pueden tener cuotas de IBI o basuras muy diferentes. Nuestra guía te ayuda a comparar y entender estas diferencias.</p>

  <div class="g3">
    {"".join(cards)}
  </div>

  <div class="hb">
    <strong>📌 Ampliaremos la cobertura provincial próximamente.</strong>
    <a href="{rel}contacto/" rel="nofollow" style="color:var(--accent)">Solicita tu provincia →</a>
  </div>

  <h2 class="sec">¿Qué impuesto quieres consultar?</h2>
  <div class="g4">
    <a href="{rel}ibi-2026/" class="tc"><div class="tc-icon">🏠</div><h3>IBI 2026</h3><p>Tipo impositivo y fecha de cobro.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}tasa-basuras/" class="tc"><div class="tc-icon">🗑️</div><h3>Tasa de Basuras</h3><p>Importe anual y reclamaciones.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}plusvalia/" class="tc"><div class="tc-icon">📈</div><h3>Plusvalía Municipal</h3><p>Calculadora actualizada.</p><span class="tc-arrow">Ver guía completa →</span></a>
    <a href="{rel}bonificaciones/" class="tc"><div class="tc-icon">🎁</div><h3>Bonificaciones</h3><p>Reducciones en IBI disponibles.</p><span class="tc-arrow">Ver guía completa →</span></a>
  </div>
</div>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Inicio","item":"{SITE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Provincias","item":"{SITE_URL}/provincias/"}}]}}
</script>
{footer_large(rel)}
<script src="{rel}cookie-consent.js" defer></script>
</body>
</html>
'''


# ────────────────────────────────────────────────────────────────
# sitemap.xml
# ────────────────────────────────────────────────────────────────
def sitemap_xml():
    urls = []
    static = [
        ("/", 1.0, "weekly"),
        ("/comunidades/", 0.8, "monthly"),
        ("/municipios/", 0.8, "monthly"),
        ("/provincias/", 0.7, "monthly"),
        ("/ibi-2026/", 0.8, "monthly"),
        ("/calculadora-ibi/", 0.8, "monthly"),
        ("/tasa-basuras/", 0.8, "monthly"),
        ("/plusvalia/", 0.8, "monthly"),
        ("/bonificaciones/", 0.8, "monthly"),
        ("/sobre-nosotros/", 0.6, "monthly"),
        ("/aviso-legal/", 0.3, "yearly"),
        ("/privacidad/", 0.3, "yearly"),
        ("/cookies/", 0.3, "yearly"),
        ("/contacto/", 0.4, "yearly"),
    ]
    for loc, prio, freq in static:
        urls.append(f"  <url>\n    <loc>{SITE_URL}{loc}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>")
    # CCAA
    for cc_slug in CCAA.keys():
        urls.append(f"  <url>\n    <loc>{SITE_URL}/{cc_slug}/</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>")
    # Municipios
    for m in all_munis():
        urls.append(f"  <url>\n    <loc>{SITE_URL}{m['url_path']}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>")
    body = "\n".join(urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-new", action="store_true", help="Solo crear las páginas de municipios nuevos (no existentes)")
    ap.add_argument("--skip-existing", action="store_true", help="No reescribir páginas de municipio ya existentes")
    args = ap.parse_args()

    # 1) Municipios NUEVOS (los existentes se preservan)
    written_m, skipped_m = 0, 0
    for m in all_munis():
        ccaa_slug = m["ccaa_slug"]
        prov_slug = m["prov_slug"]
        slug = m["slug"]
        path = ROOT / ccaa_slug / prov_slug / slug / "index.html"
        if m.get("existing") and path.exists():
            skipped_m += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(muni_html(m), encoding="utf-8")
        written_m += 1
    print(f"[muni] escritos: {written_m}, saltados (ya existentes): {skipped_m}, total BD: {total_munis()}")

    # 2) Hubs de CCAA
    for cc_slug in CCAA.keys():
        path = ROOT / cc_slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ccaa_hub_html(cc_slug), encoding="utf-8")
    print(f"[hubs] {total_ccaa()} hubs de CCAA escritos")

    # 3) Home
    (ROOT / "index.html").write_text(home_html(), encoding="utf-8")
    print("[home] escrito")

    # 4) Listados
    (ROOT / "municipios" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "municipios" / "index.html").write_text(municipios_index_html(), encoding="utf-8")
    (ROOT / "provincias" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "provincias" / "index.html").write_text(provincias_index_html(), encoding="utf-8")
    (ROOT / "comunidades" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "comunidades" / "index.html").write_text(comunidades_index_html(), encoding="utf-8")
    print("[listados] municipios, provincias, comunidades escritos")

    # 5) Sitemap
    (ROOT / "sitemap.xml").write_text(sitemap_xml(), encoding="utf-8")
    print("[sitemap] escrito")

    # 6) Actualizar interlinking de páginas existentes
    update_siblings_in_existing()

    print(f"\n✅ DONE — {total_munis()} municipios, {total_ccaa()} CCAA")


# ────────────────────────────────────────────────────────────────
# UPDATE "Otros municipios de <Provincia>" en páginas existentes
# ────────────────────────────────────────────────────────────────
def update_siblings_in_existing():
    """Para cada municipio (incluidos los ya existentes), reemplaza el
    bloque <section class="sec"><h2>Otros municipios de X</h2>...</section>
    final por uno actualizado con TODOS los hermanos actuales (incluye nuevos).
    """
    import re as _re
    updated = 0
    for m in all_munis():
        path = ROOT / m["ccaa_slug"] / m["prov_slug"] / m["slug"] / "index.html"
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        new_block = build_prov_siblings(m).strip()
        if not new_block:
            continue
        pattern = _re.compile(
            r'<section class="sec">\s*<h2>Otros municipios de [^<]*</h2>[\s\S]*?</section>'
        )
        if pattern.search(html):
            html2 = pattern.sub(new_block, html, count=1)
        else:
            if "</main>" in html:
                html2 = html.replace("</main>", f"      {new_block}\n    </main>", 1)
            else:
                continue
        if html2 != html:
            path.write_text(html2, encoding="utf-8")
            updated += 1
    print(f"[siblings] {updated} páginas con bloque 'Otros municipios' actualizado")


if __name__ == "__main__":
    main()
