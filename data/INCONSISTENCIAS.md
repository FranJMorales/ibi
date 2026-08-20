# Inconsistencias detectadas en los datos municipales

Generado automáticamente por `scripts/extract_municipal_data.py`. Municipios analizados: **134**. Municipios con al menos un conflicto: **130**. Conflictos totales: **920**.

Cada conflicto es un caso en el que el sitio publicaba dos valores distintos para el mismo dato, o citaba una fuente que no es comprobable. Hay que resolverlos consultando la ordenanza fiscal del ayuntamiento y anotando el enlace directo en `data/municipios.json` (`fuente_url`, `fuente_titulo`, `fecha_verificacion`, `verificado: true`).

## Barbastro (Huesca)

Valor publicado: IBI urbano **0.59%**, basuras **90 €/año**.

- boletín citado en la web «BOA nº 246, 20/12/2025» vs «BOP Huesca nº 245, 22/12/2025» en factcheck.json
- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Binéfar (Huesca)

Valor publicado: IBI urbano **0.59%**, basuras **92 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Fraga (Huesca)

Valor publicado: IBI urbano **0.60%**, basuras **95 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Huesca (Huesca)

Valor publicado: IBI urbano **0.60%**, basuras **102 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Jaca (Huesca)

Valor publicado: IBI urbano **0.57%**, basuras **98 €/año**.

- boletín citado en la web «BOA nº 247, 21/12/2025» vs «BOP Huesca nº 240, 18/12/2025» en factcheck.json
- municipal_factcheck.json registra IBI 0.52% frente al 0.57% publicado

## Monzón (Huesca)

Valor publicado: IBI urbano **0.58%**, basuras **88 €/año**.

- boletín citado en la web «BOA nº 246, 20/12/2025» vs «BOP Huesca nº 242, 20/12/2025» en factcheck.json
- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Sabiñánigo (Huesca)

Valor publicado: IBI urbano **0.58%**, basuras **96 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Alcañiz (Teruel)

Valor publicado: IBI urbano **0.60%**, basuras **98 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Teruel (Teruel)

Valor publicado: IBI urbano **0.58%**, basuras **95 €/año**.

- boletín citado en la web «BOA nº 248, 22/12/2025» vs «BOP Teruel nº 248, 28/12/2025» en factcheck.json
- municipal_factcheck.json registra IBI 0.6% frente al 0.58% publicado

## Calatayud (Zaragoza)

Valor publicado: IBI urbano **0.60%**, basuras **92 €/año**.

- boletín citado en la web «BOA nº 248, 22/12/2025» vs «BOP Zaragoza nº 290, 19/12/2025» en factcheck.json
- la ficha de Ejea de los Caballeros lo cita con basuras 95.0 € (su propia ficha dice 92.0 €)
- la ficha de Tarazona lo cita con basuras 95.0 € (su propia ficha dice 92.0 €)
- la ficha de Utebo lo cita con basuras 95.0 € (su propia ficha dice 92.0 €)
- la ficha de Zaragoza lo cita con basuras 95.0 € (su propia ficha dice 92.0 €)

## Ejea de los Caballeros (Zaragoza)

Valor publicado: IBI urbano **0.59%**, basuras **88 €/año**.

- boletín citado en la web «BOA nº 248, 22/12/2025» vs «BOP Zaragoza nº 288, 17/12/2025» en factcheck.json
- la ficha de Calatayud lo cita con basuras 92.0 € (su propia ficha dice 88.0 €)
- la ficha de Tarazona lo cita con basuras 92.0 € (su propia ficha dice 88.0 €)
- la ficha de Utebo lo cita con basuras 92.0 € (su propia ficha dice 88.0 €)
- la ficha de Zaragoza lo cita con basuras 92.0 € (su propia ficha dice 88.0 €)

## Tarazona (Zaragoza)

Valor publicado: IBI urbano **0.60%**, basuras **90 €/año**.

- boletín citado en la web «BOA nº 247, 21/12/2025» vs «BOP Zaragoza nº 291, 20/12/2025» en factcheck.json
- municipal_factcheck.json registra IBI 0.62% frente al 0.6% publicado

## Utebo (Zaragoza)

Valor publicado: IBI urbano **0.58%**, basuras **95 €/año**.

- boletín citado en la web «BOA nº 247, 21/12/2025» vs «BOP Zaragoza nº 287, 16/12/2025» en factcheck.json
- la ficha de Calatayud lo cita con basuras 90.0 € (su propia ficha dice 95.0 €)
- la ficha de Ejea de los Caballeros lo cita con basuras 90.0 € (su propia ficha dice 95.0 €)
- la ficha de Tarazona lo cita con basuras 90.0 € (su propia ficha dice 95.0 €)
- la ficha de Zaragoza lo cita con basuras 90.0 € (su propia ficha dice 95.0 €)

## Zaragoza (Zaragoza)

Valor publicado: IBI urbano **0.62%**, basuras **118 €/año**.

- cita «BOA nº 246, 20/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Avilés (Asturias)

Valor publicado: IBI urbano **0.62%**, basuras **138 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.64%
- el gráfico de la ficha de Grado lo dibuja con 0.64%
- el gráfico de la ficha de Lena lo dibuja con 0.64%
- el gráfico de la ficha de Llanes lo dibuja con 0.64%
- el gráfico de la ficha de Navia lo dibuja con 0.64%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.64%
- la ficha de Cangas de Onís lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Cangas de Onís lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Castrillón lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Castrillón lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Gijón lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Gijón lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Grado lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Grado lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Langreo lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Langreo lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Lena lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Lena lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Llanes lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Llanes lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Mieres lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Mieres lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Navia lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Navia lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Oviedo lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Oviedo lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Siero lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Siero lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Villaviciosa lo cita con basuras 110.0 € (su propia ficha dice 138.0 €)

## Cangas de Onís (Asturias)

Valor publicado: IBI urbano **0.60%**, basuras **102 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Castrillón (Asturias)

Valor publicado: IBI urbano **0.59%**, basuras **128 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.62%
- el gráfico de la ficha de Grado lo dibuja con 0.62%
- el gráfico de la ficha de Lena lo dibuja con 0.62%
- el gráfico de la ficha de Llanes lo dibuja con 0.62%
- el gráfico de la ficha de Navia lo dibuja con 0.62%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.62%
- la ficha de Avilés lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Avilés lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Cangas de Onís lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Gijón lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Gijón lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Grado lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Grado lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Langreo lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Langreo lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Lena lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Lena lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Llanes lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Llanes lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Mieres lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Mieres lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Navia lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Navia lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Oviedo lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Oviedo lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Siero lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Siero lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.62% (su propia ficha dice 0.59%)
- la ficha de Villaviciosa lo cita con basuras 98.0 € (su propia ficha dice 128.0 €)
- municipal_factcheck.json registra IBI 0.55% frente al 0.59% publicado

## Gijón (Asturias)

Valor publicado: IBI urbano **0.61%**, basuras **148 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.65%
- el gráfico de la ficha de Grado lo dibuja con 0.65%
- el gráfico de la ficha de Lena lo dibuja con 0.65%
- el gráfico de la ficha de Llanes lo dibuja con 0.65%
- el gráfico de la ficha de Navia lo dibuja con 0.65%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.65%
- la ficha de Avilés lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Avilés lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Cangas de Onís lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Castrillón lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Castrillón lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Grado lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Grado lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Langreo lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Langreo lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Lena lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Lena lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Llanes lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Llanes lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Mieres lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Mieres lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Navia lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Navia lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Oviedo lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Oviedo lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Siero lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Siero lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.65% (su propia ficha dice 0.61%)
- la ficha de Villaviciosa lo cita con basuras 118.0 € (su propia ficha dice 148.0 €)
- municipal_factcheck.json registra IBI 0.66% frente al 0.61% publicado

## Grado (Asturias)

Valor publicado: IBI urbano **0.61%**, basuras **100 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Langreo (Asturias)

Valor publicado: IBI urbano **0.64%**, basuras **125 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.66%
- el gráfico de la ficha de Grado lo dibuja con 0.66%
- el gráfico de la ficha de Lena lo dibuja con 0.66%
- el gráfico de la ficha de Llanes lo dibuja con 0.66%
- el gráfico de la ficha de Navia lo dibuja con 0.66%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.66%
- la ficha de Avilés lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Avilés lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Cangas de Onís lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Castrillón lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Castrillón lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Gijón lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Gijón lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Grado lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Grado lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Lena lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Lena lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Llanes lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Llanes lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Mieres lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Mieres lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Navia lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Navia lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Oviedo lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Oviedo lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Siero lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Siero lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.66% (su propia ficha dice 0.64%)
- la ficha de Villaviciosa lo cita con basuras 106.0 € (su propia ficha dice 125.0 €)
- municipal_factcheck.json registra IBI 0.58% frente al 0.64% publicado

## Lena (Asturias)

Valor publicado: IBI urbano **0.62%**, basuras **98 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Llanes (Asturias)

Valor publicado: IBI urbano **0.63%**, basuras **115 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Mieres (Asturias)

Valor publicado: IBI urbano **0.63%**, basuras **120 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.64%
- el gráfico de la ficha de Grado lo dibuja con 0.64%
- el gráfico de la ficha de Lena lo dibuja con 0.64%
- el gráfico de la ficha de Llanes lo dibuja con 0.64%
- el gráfico de la ficha de Navia lo dibuja con 0.64%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.64%
- la ficha de Avilés lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Avilés lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Cangas de Onís lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Castrillón lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Castrillón lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Gijón lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Gijón lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Grado lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Grado lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Langreo lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Langreo lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Lena lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Lena lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Llanes lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Llanes lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Navia lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Navia lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Oviedo lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Oviedo lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Siero lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Siero lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.64% (su propia ficha dice 0.63%)
- la ficha de Villaviciosa lo cita con basuras 105.0 € (su propia ficha dice 120.0 €)
- municipal_factcheck.json registra IBI 0.57% frente al 0.63% publicado

## Navia (Asturias)

Valor publicado: IBI urbano **0.62%**, basuras **100 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Oviedo (Asturias)

Valor publicado: IBI urbano **0.59%**, basuras **155 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.67%
- el gráfico de la ficha de Grado lo dibuja con 0.67%
- el gráfico de la ficha de Lena lo dibuja con 0.67%
- el gráfico de la ficha de Llanes lo dibuja con 0.67%
- el gráfico de la ficha de Navia lo dibuja con 0.67%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.67%
- la ficha de Avilés lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Avilés lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Cangas de Onís lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Castrillón lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Castrillón lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Gijón lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Gijón lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Grado lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Grado lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Langreo lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Langreo lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Lena lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Lena lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Llanes lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Llanes lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Mieres lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Mieres lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Navia lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Navia lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Siero lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Siero lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.67% (su propia ficha dice 0.59%)
- la ficha de Villaviciosa lo cita con basuras 124.0 € (su propia ficha dice 155.0 €)
- municipal_factcheck.json registra IBI 0.63% frente al 0.59% publicado

## Siero (Asturias)

Valor publicado: IBI urbano **0.58%**, basuras **130 €/año**.

- el gráfico de la ficha de Cangas de Onís lo dibuja con 0.63%
- el gráfico de la ficha de Grado lo dibuja con 0.63%
- el gráfico de la ficha de Lena lo dibuja con 0.63%
- el gráfico de la ficha de Llanes lo dibuja con 0.63%
- el gráfico de la ficha de Navia lo dibuja con 0.63%
- el gráfico de la ficha de Villaviciosa lo dibuja con 0.63%
- la ficha de Avilés lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Avilés lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Cangas de Onís lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Cangas de Onís lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Castrillón lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Castrillón lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Gijón lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Gijón lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Grado lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Grado lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Langreo lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Langreo lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Lena lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Lena lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Llanes lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Llanes lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Mieres lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Mieres lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Navia lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Navia lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Oviedo lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Oviedo lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- la ficha de Villaviciosa lo cita con IBI 0.63% (su propia ficha dice 0.58%)
- la ficha de Villaviciosa lo cita con basuras 108.0 € (su propia ficha dice 130.0 €)
- municipal_factcheck.json registra IBI 0.56% frente al 0.58% publicado

## Villaviciosa (Asturias)

Valor publicado: IBI urbano **0.61%**, basuras **102 €/año**.

- cita «BOPA nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Camargo (Cantabria)

Valor publicado: IBI urbano **0.62%**, basuras **115 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Castro-Urdiales (Cantabria)

Valor publicado: IBI urbano **0.63%**, basuras **128 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## El Astillero (Cantabria)

Valor publicado: IBI urbano **0.64%**, basuras **112 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Laredo (Cantabria)

Valor publicado: IBI urbano **0.62%**, basuras **120 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Los Corrales de Buelna (Cantabria)

Valor publicado: IBI urbano **0.60%**, basuras **100 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Piélagos (Cantabria)

Valor publicado: IBI urbano **0.60%**, basuras **108 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Santa Cruz de Bezana (Cantabria)

Valor publicado: IBI urbano **0.61%**, basuras **110 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Santander (Cantabria)

Valor publicado: IBI urbano **0.64%**, basuras **135 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Santoña (Cantabria)

Valor publicado: IBI urbano **0.63%**, basuras **115 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Torrelavega (Cantabria)

Valor publicado: IBI urbano **0.65%**, basuras **118 €/año**.

- cita «BOC nº 246, 22/12/2025» como fuente, igual que otros 9 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Albacete (Albacete)

Valor publicado: IBI urbano **0.60%**, basuras **110 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Almansa (Albacete)

Valor publicado: IBI urbano **0.63%**, basuras **92 €/año**.

- boletín citado en la web «DOCM nº 251, 21/12/2025» vs «BOP Albacete nº 150, 20/12/2025» en factcheck.json
- cita «DOCM nº 251, 21/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Albacete lo cita con basuras 105.0 € (su propia ficha dice 92.0 €)
- la ficha de Hellín lo cita con basuras 105.0 € (su propia ficha dice 92.0 €)
- municipal_factcheck.json registra IBI 0.65% frente al 0.63% publicado

## Hellín (Albacete)

Valor publicado: IBI urbano **0.64%**, basuras **95 €/año**.

- boletín citado en la web «DOCM nº 251, 21/12/2025» vs «BOP Albacete nº 148, 18/12/2025» en factcheck.json
- cita «DOCM nº 251, 21/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Albacete lo cita con basuras 108.0 € (su propia ficha dice 95.0 €)
- la ficha de Almansa lo cita con basuras 108.0 € (su propia ficha dice 95.0 €)
- municipal_factcheck.json registra IBI 0.63% frente al 0.64% publicado

## Alcázar de San Juan (Ciudad Real)

Valor publicado: IBI urbano **0.64%**, basuras **105 €/año**.

- boletín citado en la web «DOCM nº 250, 20/12/2025» vs «BOP Ciudad Real nº 242, 19/12/2025» en factcheck.json
- cita «DOCM nº 250, 20/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ciudad Real (Ciudad Real)

Valor publicado: IBI urbano **0.62%**, basuras **112 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Daimiel (Ciudad Real)

Valor publicado: IBI urbano **0.62%**, basuras **98 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Manzanares (Ciudad Real)

Valor publicado: IBI urbano **0.62%**, basuras **100 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Puertollano (Ciudad Real)

Valor publicado: IBI urbano **0.67%**, basuras **118 €/año**.

- boletín citado en la web «DOCM nº 251, 21/12/2025» vs «BOP Ciudad Real nº 244, 21/12/2025» en factcheck.json
- cita «DOCM nº 251, 21/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Alcázar de San Juan lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Ciudad Real lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Daimiel lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Manzanares lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Tomelloso lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Valdepeñas lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)
- la ficha de Villarrobledo lo cita con basuras 115.0 € (su propia ficha dice 118.0 €)

## Tomelloso (Ciudad Real)

Valor publicado: IBI urbano **0.65%**, basuras **110 €/año**.

- boletín citado en la web «DOCM nº 251, 21/12/2025» vs «BOP Ciudad Real nº 243, 20/12/2025» en factcheck.json
- cita «DOCM nº 251, 21/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Alcázar de San Juan lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Ciudad Real lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Daimiel lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Manzanares lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Puertollano lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Valdepeñas lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)
- la ficha de Villarrobledo lo cita con basuras 108.0 € (su propia ficha dice 110.0 €)

## Valdepeñas (Ciudad Real)

Valor publicado: IBI urbano **0.63%**, basuras **102 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Villarrobledo (Ciudad Real)

Valor publicado: IBI urbano **0.63%**, basuras **100 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Cuenca (Cuenca)

Valor publicado: IBI urbano **0.66%**, basuras **120 €/año**.

- boletín citado en la web «DOCM nº 252, 22/12/2025» vs «BOP Cuenca nº 147, 22/12/2025» en factcheck.json
- la ficha de Tarancón lo cita con basuras 115.0 € (su propia ficha dice 120.0 €)
- municipal_factcheck.json registra IBI 0.61% frente al 0.66% publicado

## Tarancón (Cuenca)

Valor publicado: IBI urbano **0.62%**, basuras **98 €/año**.

- boletín citado en la web «DOCM nº 250, 20/12/2025» vs «BOP Cuenca nº 146, 21/12/2025» en factcheck.json
- cita «DOCM nº 250, 20/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Cuenca lo cita con basuras 102.0 € (su propia ficha dice 98.0 €)

## Azuqueca de Henares (Guadalajara)

Valor publicado: IBI urbano **0.61%**, basuras **112 €/año**.

- boletín citado en la web «DOCM nº 252, 22/12/2025» vs «BOP Guadalajara nº 155, 23/12/2025» en factcheck.json
- la ficha de Cabanillas del Campo lo cita con basuras 108.0 € (su propia ficha dice 112.0 €)
- la ficha de Guadalajara lo cita con basuras 108.0 € (su propia ficha dice 112.0 €)

## Cabanillas del Campo (Guadalajara)

Valor publicado: IBI urbano **0.60%**, basuras **108 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Guadalajara (Guadalajara)

Valor publicado: IBI urbano **0.63%**, basuras **115 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Illescas (Toledo)

Valor publicado: IBI urbano **0.60%**, basuras **108 €/año**.

- boletín citado en la web «DOCM nº 250, 20/12/2025» vs «BOP Toledo nº 244, 21/12/2025» en factcheck.json
- cita «DOCM nº 250, 20/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Seseña lo cita con basuras 120.0 € (su propia ficha dice 108.0 €)
- la ficha de Talavera de la Reina lo cita con basuras 120.0 € (su propia ficha dice 108.0 €)
- la ficha de Toledo lo cita con basuras 120.0 € (su propia ficha dice 108.0 €)

## Seseña (Toledo)

Valor publicado: IBI urbano **0.58%**, basuras **105 €/año**.

- boletín citado en la web «DOCM nº 250, 20/12/2025» vs «BOP Toledo nº 245, 22/12/2025» en factcheck.json
- cita «DOCM nº 250, 20/12/2025» como fuente, igual que otros 3 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Illescas lo cita con basuras 100.0 € (su propia ficha dice 105.0 €)
- la ficha de Talavera de la Reina lo cita con basuras 100.0 € (su propia ficha dice 105.0 €)
- la ficha de Toledo lo cita con basuras 100.0 € (su propia ficha dice 105.0 €)

## Talavera de la Reina (Toledo)

Valor publicado: IBI urbano **0.68%**, basuras **142 €/año**.

- boletín citado en la web «DOCM nº 252, 22/12/2025» vs «BOP Toledo nº 243, 20/12/2025» en factcheck.json
- la ficha de Illescas lo cita con basuras 145.0 € (su propia ficha dice 142.0 €)
- la ficha de Seseña lo cita con basuras 145.0 € (su propia ficha dice 142.0 €)
- la ficha de Toledo lo cita con basuras 145.0 € (su propia ficha dice 142.0 €)

## Toledo (Toledo)

Valor publicado: IBI urbano **0.60%**, basuras **118 €/año**.

- cita «DOCM nº 244, 19/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ávila (Ávila)

Valor publicado: IBI urbano **0.60%**, basuras **115 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.63%
- el gráfico de la ficha de León lo dibuja con 0.63%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.63%
- el gráfico de la ficha de Salamanca lo dibuja con 0.63%
- el gráfico de la ficha de Soria lo dibuja con 0.63%
- el gráfico de la ficha de Valladolid lo dibuja con 0.63%

## Aranda de Duero (Burgos)

Valor publicado: IBI urbano **0.62%**, basuras **108 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.64%
- el gráfico de la ficha de León lo dibuja con 0.64%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.64%
- el gráfico de la ficha de Salamanca lo dibuja con 0.64%
- el gráfico de la ficha de Soria lo dibuja con 0.64%
- el gráfico de la ficha de Valladolid lo dibuja con 0.64%
- la ficha de Burgos lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Burgos lo cita con basuras 110.0 € (su propia ficha dice 108.0 €)
- la ficha de Miranda de Ebro lo cita con IBI 0.64% (su propia ficha dice 0.62%)
- la ficha de Miranda de Ebro lo cita con basuras 110.0 € (su propia ficha dice 108.0 €)
- municipal_factcheck.json registra IBI 0.63% frente al 0.62% publicado

## Burgos (Burgos)

Valor publicado: IBI urbano **0.60%**, basuras **118 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Miranda de Ebro (Burgos)

Valor publicado: IBI urbano **0.64%**, basuras **112 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.65%
- el gráfico de la ficha de León lo dibuja con 0.65%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.65%
- el gráfico de la ficha de Salamanca lo dibuja con 0.65%
- el gráfico de la ficha de Soria lo dibuja con 0.65%
- el gráfico de la ficha de Valladolid lo dibuja con 0.65%
- la ficha de Aranda de Duero lo cita con IBI 0.65% (su propia ficha dice 0.64%)
- la ficha de Aranda de Duero lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Burgos lo cita con IBI 0.65% (su propia ficha dice 0.64%)
- la ficha de Burgos lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- municipal_factcheck.json registra IBI 0.65% frente al 0.64% publicado

## León (León)

Valor publicado: IBI urbano **0.62%**, basuras **120 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ponferrada (León)

Valor publicado: IBI urbano **0.62%**, basuras **118 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.67%
- el gráfico de la ficha de León lo dibuja con 0.67%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.67%
- el gráfico de la ficha de Salamanca lo dibuja con 0.67%
- el gráfico de la ficha de Soria lo dibuja con 0.67%
- el gráfico de la ficha de Valladolid lo dibuja con 0.67%
- la ficha de León lo cita con IBI 0.67% (su propia ficha dice 0.62%)
- la ficha de León lo cita con basuras 135.0 € (su propia ficha dice 118.0 €)
- municipal_factcheck.json registra IBI 0.67% frente al 0.62% publicado

## Palencia (Palencia)

Valor publicado: IBI urbano **0.60%**, basuras **110 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.63%
- el gráfico de la ficha de León lo dibuja con 0.63%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.63%
- el gráfico de la ficha de Salamanca lo dibuja con 0.63%
- el gráfico de la ficha de Soria lo dibuja con 0.63%
- el gráfico de la ficha de Valladolid lo dibuja con 0.63%
- municipal_factcheck.json registra IBI 0.59% frente al 0.6% publicado

## Béjar (Salamanca)

Valor publicado: IBI urbano **0.65%**, basuras **95 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.64%
- el gráfico de la ficha de León lo dibuja con 0.64%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.64%
- el gráfico de la ficha de Salamanca lo dibuja con 0.64%
- el gráfico de la ficha de Soria lo dibuja con 0.64%
- el gráfico de la ficha de Valladolid lo dibuja con 0.64%
- la ficha de Salamanca lo cita con IBI 0.64% (su propia ficha dice 0.65%)
- la ficha de Salamanca lo cita con basuras 92.0 € (su propia ficha dice 95.0 €)
- municipal_factcheck.json registra IBI 0.64% frente al 0.65% publicado

## Salamanca (Salamanca)

Valor publicado: IBI urbano **0.61%**, basuras **115 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Soria (Soria)

Valor publicado: IBI urbano **0.60%**, basuras **108 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Medina del Campo (Valladolid)

Valor publicado: IBI urbano **0.62%**, basuras **100 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Valladolid (Valladolid)

Valor publicado: IBI urbano **0.61%**, basuras **120 €/año**.

- cita «BOCYL nº 245, 19/12/2025» como fuente, igual que otros 5 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Zamora (Zamora)

Valor publicado: IBI urbano **0.61%**, basuras **108 €/año**.

- el gráfico de la ficha de Burgos lo dibuja con 0.64%
- el gráfico de la ficha de León lo dibuja con 0.64%
- el gráfico de la ficha de Medina del Campo lo dibuja con 0.64%
- el gráfico de la ficha de Salamanca lo dibuja con 0.64%
- el gráfico de la ficha de Soria lo dibuja con 0.64%
- el gráfico de la ficha de Valladolid lo dibuja con 0.64%
- municipal_factcheck.json registra IBI 0.58% frente al 0.61% publicado

## Almendralejo (Badajoz)

Valor publicado: IBI urbano **0.64%**, basuras **98 €/año**.

- la ficha de Badajoz lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Don Benito lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Montijo lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Mérida lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Olivenza lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Villanueva de la Serena lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)
- la ficha de Zafra lo cita con basuras 110.0 € (su propia ficha dice 98.0 €)

## Badajoz (Badajoz)

Valor publicado: IBI urbano **0.60%**, basuras **115 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Don Benito (Badajoz)

Valor publicado: IBI urbano **0.63%**, basuras **92 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Almendralejo lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Badajoz lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Montijo lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Mérida lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Olivenza lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Villanueva de la Serena lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)
- la ficha de Zafra lo cita con basuras 108.0 € (su propia ficha dice 92.0 €)

## Jerez de los Caballeros (Badajoz)

Valor publicado: IBI urbano **0.61%**, basuras **92 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Montijo (Badajoz)

Valor publicado: IBI urbano **0.62%**, basuras **84 €/año**.

- la ficha de Almendralejo lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Badajoz lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Don Benito lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Mérida lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Olivenza lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Villanueva de la Serena lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)
- la ficha de Zafra lo cita con basuras 95.0 € (su propia ficha dice 84.0 €)

## Mérida (Badajoz)

Valor publicado: IBI urbano **0.66%**, basuras **125 €/año**.

- la ficha de Almendralejo lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Badajoz lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Don Benito lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Montijo lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Olivenza lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Villanueva de la Serena lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)
- la ficha de Zafra lo cita con basuras 130.0 € (su propia ficha dice 125.0 €)

## Olivenza (Badajoz)

Valor publicado: IBI urbano **0.62%**, basuras **98 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Villanueva de la Serena (Badajoz)

Valor publicado: IBI urbano **0.63%**, basuras **90 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas
- la ficha de Almendralejo lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Badajoz lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Don Benito lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Montijo lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Mérida lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Olivenza lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)
- la ficha de Zafra lo cita con basuras 105.0 € (su propia ficha dice 90.0 €)

## Zafra (Badajoz)

Valor publicado: IBI urbano **0.63%**, basuras **85 €/año**.

- la ficha de Almendralejo lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Badajoz lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Don Benito lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Jerez de los Caballeros lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Montijo lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Mérida lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Olivenza lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- la ficha de Villanueva de la Serena lo cita con basuras 98.0 € (su propia ficha dice 85.0 €)
- municipal_factcheck.json registra IBI 0.61% frente al 0.63% publicado

## Cáceres (Cáceres)

Valor publicado: IBI urbano **0.62%**, basuras **115 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Miajadas (Cáceres)

Valor publicado: IBI urbano **0.62%**, basuras **80 €/año**.

- municipal_factcheck.json registra IBI 0.6% frente al 0.62% publicado

## Plasencia (Cáceres)

Valor publicado: IBI urbano **0.65%**, basuras **95 €/año**.

- cita «DOE nº 243, 20/12/2025» como fuente, igual que otros 6 municipios: un único número de boletín no puede contener todas esas ordenanzas

## A Coruña (A Coruña)

Valor publicado: IBI urbano **0.61%**, basuras **120 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ames (A Coruña)

Valor publicado: IBI urbano **0.58%**, basuras **92 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Arteixo (A Coruña)

Valor publicado: IBI urbano **0.60%**, basuras **98 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Carballo (A Coruña)

Valor publicado: IBI urbano **0.59%**, basuras **92 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ferrol (A Coruña)

Valor publicado: IBI urbano **0.63%**, basuras **132 €/año**.

- boletín citado en la web «DOG nº 245, 22/12/2025» vs «BOP A Coruña nº 242, 20/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.6%
- el gráfico de la ficha de Ames lo dibuja con 0.6%
- el gráfico de la ficha de Arteixo lo dibuja con 0.6%
- el gráfico de la ficha de Cangas lo dibuja con 0.6%
- el gráfico de la ficha de Carballo lo dibuja con 0.6%
- el gráfico de la ficha de Lalín lo dibuja con 0.6%
- el gráfico de la ficha de Marín lo dibuja con 0.6%
- el gráfico de la ficha de Narón lo dibuja con 0.6%
- el gráfico de la ficha de O Porriño lo dibuja con 0.6%
- el gráfico de la ficha de Redondela lo dibuja con 0.6%
- el gráfico de la ficha de Ribeira lo dibuja con 0.6%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.6%
- el gráfico de la ficha de Sarria lo dibuja con 0.6%
- el gráfico de la ficha de Tui lo dibuja con 0.6%
- el gráfico de la ficha de Verín lo dibuja con 0.6%
- el gráfico de la ficha de Vigo lo dibuja con 0.6%
- el gráfico de la ficha de Viveiro lo dibuja con 0.6%
- la ficha de A Coruña lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de A Coruña lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Ames lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Ames lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Arteixo lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Arteixo lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Carballo lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Carballo lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Narón lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Narón lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Ribeira lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Ribeira lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- la ficha de Santiago de Compostela lo cita con IBI 0.6% (su propia ficha dice 0.63%)
- la ficha de Santiago de Compostela lo cita con basuras 108.0 € (su propia ficha dice 132.0 €)
- municipal_factcheck.json registra IBI 0.64% frente al 0.63% publicado

## Narón (A Coruña)

Valor publicado: IBI urbano **0.58%**, basuras **95 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Ribeira (A Coruña)

Valor publicado: IBI urbano **0.60%**, basuras **100 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Santiago de Compostela (A Coruña)

Valor publicado: IBI urbano **0.60%**, basuras **115 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Lugo (Lugo)

Valor publicado: IBI urbano **0.62%**, basuras **125 €/año**.

- boletín citado en la web «DOG nº 244, 21/12/2025» vs «BOP Lugo nº 290, 19/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.56%
- el gráfico de la ficha de Ames lo dibuja con 0.56%
- el gráfico de la ficha de Arteixo lo dibuja con 0.56%
- el gráfico de la ficha de Cangas lo dibuja con 0.56%
- el gráfico de la ficha de Carballo lo dibuja con 0.56%
- el gráfico de la ficha de Lalín lo dibuja con 0.56%
- el gráfico de la ficha de Marín lo dibuja con 0.56%
- el gráfico de la ficha de Narón lo dibuja con 0.56%
- el gráfico de la ficha de O Porriño lo dibuja con 0.56%
- el gráfico de la ficha de Redondela lo dibuja con 0.56%
- el gráfico de la ficha de Ribeira lo dibuja con 0.56%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.56%
- el gráfico de la ficha de Sarria lo dibuja con 0.56%
- el gráfico de la ficha de Tui lo dibuja con 0.56%
- el gráfico de la ficha de Verín lo dibuja con 0.56%
- el gráfico de la ficha de Vigo lo dibuja con 0.56%
- el gráfico de la ficha de Viveiro lo dibuja con 0.56%
- la ficha de Monforte de Lemos lo cita con IBI 0.56% (su propia ficha dice 0.62%)
- la ficha de Monforte de Lemos lo cita con basuras 90.0 € (su propia ficha dice 125.0 €)
- la ficha de Sarria lo cita con IBI 0.56% (su propia ficha dice 0.62%)
- la ficha de Sarria lo cita con basuras 90.0 € (su propia ficha dice 125.0 €)
- la ficha de Viveiro lo cita con IBI 0.56% (su propia ficha dice 0.62%)
- la ficha de Viveiro lo cita con basuras 90.0 € (su propia ficha dice 125.0 €)
- municipal_factcheck.json registra IBI 0.58% frente al 0.62% publicado

## Monforte de Lemos (Lugo)

Valor publicado: IBI urbano **0.64%**, basuras **108 €/año**.

- boletín citado en la web «DOG nº 243, 20/12/2025» vs «BOP Lugo nº 289, 18/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.55%
- el gráfico de la ficha de Ames lo dibuja con 0.55%
- el gráfico de la ficha de Arteixo lo dibuja con 0.55%
- el gráfico de la ficha de Cangas lo dibuja con 0.55%
- el gráfico de la ficha de Carballo lo dibuja con 0.55%
- el gráfico de la ficha de Lalín lo dibuja con 0.55%
- el gráfico de la ficha de Marín lo dibuja con 0.55%
- el gráfico de la ficha de Narón lo dibuja con 0.55%
- el gráfico de la ficha de O Porriño lo dibuja con 0.55%
- el gráfico de la ficha de Redondela lo dibuja con 0.55%
- el gráfico de la ficha de Ribeira lo dibuja con 0.55%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.55%
- el gráfico de la ficha de Sarria lo dibuja con 0.55%
- el gráfico de la ficha de Tui lo dibuja con 0.55%
- el gráfico de la ficha de Verín lo dibuja con 0.55%
- el gráfico de la ficha de Vigo lo dibuja con 0.55%
- el gráfico de la ficha de Viveiro lo dibuja con 0.55%
- la ficha de Lugo lo cita con IBI 0.55% (su propia ficha dice 0.64%)
- la ficha de Lugo lo cita con basuras 85.0 € (su propia ficha dice 108.0 €)
- la ficha de Sarria lo cita con IBI 0.55% (su propia ficha dice 0.64%)
- la ficha de Sarria lo cita con basuras 85.0 € (su propia ficha dice 108.0 €)
- la ficha de Viveiro lo cita con IBI 0.55% (su propia ficha dice 0.64%)
- la ficha de Viveiro lo cita con basuras 85.0 € (su propia ficha dice 108.0 €)
- municipal_factcheck.json registra IBI 0.55% frente al 0.64% publicado

## Sarria (Lugo)

Valor publicado: IBI urbano **0.56%**, basuras **88 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Viveiro (Lugo)

Valor publicado: IBI urbano **0.57%**, basuras **92 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Lalín (Ourense)

Valor publicado: IBI urbano **0.56%**, basuras **88 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## O Carballiño (Ourense)

Valor publicado: IBI urbano **0.63%**, basuras **95 €/año**.

- boletín citado en la web «DOG nº 243, 20/12/2025» vs «BOP Ourense nº 288, 17/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.54%
- el gráfico de la ficha de Ames lo dibuja con 0.54%
- el gráfico de la ficha de Arteixo lo dibuja con 0.54%
- el gráfico de la ficha de Cangas lo dibuja con 0.54%
- el gráfico de la ficha de Carballo lo dibuja con 0.54%
- el gráfico de la ficha de Lalín lo dibuja con 0.54%
- el gráfico de la ficha de Marín lo dibuja con 0.54%
- el gráfico de la ficha de Narón lo dibuja con 0.54%
- el gráfico de la ficha de O Porriño lo dibuja con 0.54%
- el gráfico de la ficha de Redondela lo dibuja con 0.54%
- el gráfico de la ficha de Ribeira lo dibuja con 0.54%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.54%
- el gráfico de la ficha de Sarria lo dibuja con 0.54%
- el gráfico de la ficha de Tui lo dibuja con 0.54%
- el gráfico de la ficha de Verín lo dibuja con 0.54%
- el gráfico de la ficha de Vigo lo dibuja con 0.54%
- el gráfico de la ficha de Viveiro lo dibuja con 0.54%
- la ficha de Lalín lo cita con IBI 0.54% (su propia ficha dice 0.63%)
- la ficha de Lalín lo cita con basuras 82.0 € (su propia ficha dice 95.0 €)
- la ficha de Ourense lo cita con IBI 0.54% (su propia ficha dice 0.63%)
- la ficha de Ourense lo cita con basuras 82.0 € (su propia ficha dice 95.0 €)
- la ficha de Verín lo cita con IBI 0.54% (su propia ficha dice 0.63%)
- la ficha de Verín lo cita con basuras 82.0 € (su propia ficha dice 95.0 €)
- municipal_factcheck.json registra IBI 0.54% frente al 0.63% publicado

## Ourense (Ourense)

Valor publicado: IBI urbano **0.62%**, basuras **128 €/año**.

- boletín citado en la web «DOG nº 244, 21/12/2025» vs «BOP Ourense nº 290, 19/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.57%
- el gráfico de la ficha de Ames lo dibuja con 0.57%
- el gráfico de la ficha de Arteixo lo dibuja con 0.57%
- el gráfico de la ficha de Cangas lo dibuja con 0.57%
- el gráfico de la ficha de Carballo lo dibuja con 0.57%
- el gráfico de la ficha de Lalín lo dibuja con 0.57%
- el gráfico de la ficha de Marín lo dibuja con 0.57%
- el gráfico de la ficha de Narón lo dibuja con 0.57%
- el gráfico de la ficha de O Porriño lo dibuja con 0.57%
- el gráfico de la ficha de Redondela lo dibuja con 0.57%
- el gráfico de la ficha de Ribeira lo dibuja con 0.57%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.57%
- el gráfico de la ficha de Sarria lo dibuja con 0.57%
- el gráfico de la ficha de Tui lo dibuja con 0.57%
- el gráfico de la ficha de Verín lo dibuja con 0.57%
- el gráfico de la ficha de Vigo lo dibuja con 0.57%
- el gráfico de la ficha de Viveiro lo dibuja con 0.57%
- la ficha de Lalín lo cita con IBI 0.57% (su propia ficha dice 0.62%)
- la ficha de Lalín lo cita con basuras 95.0 € (su propia ficha dice 128.0 €)
- la ficha de O Carballiño lo cita con IBI 0.57% (su propia ficha dice 0.62%)
- la ficha de O Carballiño lo cita con basuras 95.0 € (su propia ficha dice 128.0 €)
- la ficha de Verín lo cita con IBI 0.57% (su propia ficha dice 0.62%)
- la ficha de Verín lo cita con basuras 95.0 € (su propia ficha dice 128.0 €)
- municipal_factcheck.json registra IBI 0.6% frente al 0.62% publicado

## Verín (Ourense)

Valor publicado: IBI urbano **0.56%**, basuras **85 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Cangas (Pontevedra)

Valor publicado: IBI urbano **0.59%**, basuras **95 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Marín (Pontevedra)

Valor publicado: IBI urbano **0.60%**, basuras **98 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## O Porriño (Pontevedra)

Valor publicado: IBI urbano **0.60%**, basuras **95 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Pontevedra (Pontevedra)

Valor publicado: IBI urbano **0.60%**, basuras **135 €/año**.

- boletín citado en la web «DOG nº 245, 22/12/2025» vs «BOP Pontevedra nº 242, 20/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.54%
- el gráfico de la ficha de Ames lo dibuja con 0.54%
- el gráfico de la ficha de Arteixo lo dibuja con 0.54%
- el gráfico de la ficha de Cangas lo dibuja con 0.54%
- el gráfico de la ficha de Carballo lo dibuja con 0.54%
- el gráfico de la ficha de Lalín lo dibuja con 0.54%
- el gráfico de la ficha de Marín lo dibuja con 0.54%
- el gráfico de la ficha de Narón lo dibuja con 0.54%
- el gráfico de la ficha de O Porriño lo dibuja con 0.54%
- el gráfico de la ficha de Redondela lo dibuja con 0.54%
- el gráfico de la ficha de Ribeira lo dibuja con 0.54%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.54%
- el gráfico de la ficha de Sarria lo dibuja con 0.54%
- el gráfico de la ficha de Tui lo dibuja con 0.54%
- el gráfico de la ficha de Verín lo dibuja con 0.54%
- el gráfico de la ficha de Vigo lo dibuja con 0.54%
- el gráfico de la ficha de Viveiro lo dibuja con 0.54%
- la ficha de Cangas lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Cangas lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de Marín lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Marín lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de O Porriño lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de O Porriño lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de Redondela lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Redondela lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de Tui lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Tui lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de Vigo lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Vigo lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- la ficha de Vilagarcía de Arousa lo cita con IBI 0.54% (su propia ficha dice 0.6%)
- la ficha de Vilagarcía de Arousa lo cita con basuras 98.0 € (su propia ficha dice 135.0 €)
- municipal_factcheck.json registra IBI 0.62% frente al 0.6% publicado

## Redondela (Pontevedra)

Valor publicado: IBI urbano **0.60%**, basuras **98 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Tui (Pontevedra)

Valor publicado: IBI urbano **0.59%**, basuras **92 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Vigo (Pontevedra)

Valor publicado: IBI urbano **0.61%**, basuras **115 €/año**.

- cita «DOG nº 243, 19/12/2025» como fuente, igual que otros 16 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Vilagarcía de Arousa (Pontevedra)

Valor publicado: IBI urbano **0.62%**, basuras **118 €/año**.

- boletín citado en la web «DOG nº 244, 21/12/2025» vs «BOP Pontevedra nº 241, 19/12/2025» en factcheck.json
- el gráfico de la ficha de A Coruña lo dibuja con 0.55%
- el gráfico de la ficha de Ames lo dibuja con 0.55%
- el gráfico de la ficha de Arteixo lo dibuja con 0.55%
- el gráfico de la ficha de Cangas lo dibuja con 0.55%
- el gráfico de la ficha de Carballo lo dibuja con 0.55%
- el gráfico de la ficha de Lalín lo dibuja con 0.55%
- el gráfico de la ficha de Marín lo dibuja con 0.55%
- el gráfico de la ficha de Narón lo dibuja con 0.55%
- el gráfico de la ficha de O Porriño lo dibuja con 0.55%
- el gráfico de la ficha de Redondela lo dibuja con 0.55%
- el gráfico de la ficha de Ribeira lo dibuja con 0.55%
- el gráfico de la ficha de Santiago de Compostela lo dibuja con 0.55%
- el gráfico de la ficha de Sarria lo dibuja con 0.55%
- el gráfico de la ficha de Tui lo dibuja con 0.55%
- el gráfico de la ficha de Verín lo dibuja con 0.55%
- el gráfico de la ficha de Vigo lo dibuja con 0.55%
- el gráfico de la ficha de Viveiro lo dibuja con 0.55%
- la ficha de Cangas lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Cangas lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de Marín lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Marín lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de O Porriño lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de O Porriño lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de Pontevedra lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Pontevedra lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de Redondela lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Redondela lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de Tui lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Tui lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- la ficha de Vigo lo cita con IBI 0.55% (su propia ficha dice 0.62%)
- la ficha de Vigo lo cita con basuras 95.0 € (su propia ficha dice 118.0 €)
- municipal_factcheck.json registra IBI 0.57% frente al 0.62% publicado

## Alfaro (La Rioja)

Valor publicado: IBI urbano **0.60%**, basuras **90 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Arnedo (La Rioja)

Valor publicado: IBI urbano **0.59%**, basuras **92 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Calahorra (La Rioja)

Valor publicado: IBI urbano **0.60%**, basuras **98 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Haro (La Rioja)

Valor publicado: IBI urbano **0.58%**, basuras **95 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Lardero (La Rioja)

Valor publicado: IBI urbano **0.57%**, basuras **88 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Logroño (La Rioja)

Valor publicado: IBI urbano **0.62%**, basuras **110 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Nájera (La Rioja)

Valor publicado: IBI urbano **0.58%**, basuras **90 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Santo Domingo de la Calzada (La Rioja)

Valor publicado: IBI urbano **0.56%**, basuras **92 €/año**.

- cita «BOR nº 244, 19/12/2025» como fuente, igual que otros 7 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Alcantarilla (Murcia)

Valor publicado: IBI urbano **0.64%**, basuras **108 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Alhama de Murcia (Murcia)

Valor publicado: IBI urbano **0.62%**, basuras **105 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Caravaca de la Cruz (Murcia)

Valor publicado: IBI urbano **0.64%**, basuras **95 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.61%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.61%
- el gráfico de la ficha de Cartagena lo dibuja con 0.61%
- el gráfico de la ficha de Jumilla lo dibuja con 0.61%
- el gráfico de la ficha de Murcia lo dibuja con 0.61%
- el gráfico de la ficha de San Javier lo dibuja con 0.61%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.61%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.61%
- el gráfico de la ficha de Totana lo dibuja con 0.61%
- la ficha de Alcantarilla lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Alcantarilla lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Alhama de Murcia lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Alhama de Murcia lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Cartagena lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Cartagena lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Cieza lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Cieza lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Jumilla lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Jumilla lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Lorca lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Lorca lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Mazarrón lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Mazarrón lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Molina de Segura lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Molina de Segura lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Murcia lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Murcia lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de San Javier lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de San Javier lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de San Pedro del Pinatar lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Torre Pacheco lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Torre Pacheco lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Totana lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Totana lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Yecla lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Yecla lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- la ficha de Águilas lo cita con IBI 0.61% (su propia ficha dice 0.64%)
- la ficha de Águilas lo cita con basuras 102.0 € (su propia ficha dice 95.0 €)
- municipal_factcheck.json registra IBI 0.61% frente al 0.64% publicado

## Cartagena (Murcia)

Valor publicado: IBI urbano **0.65%**, basuras **120 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Cieza (Murcia)

Valor publicado: IBI urbano **0.64%**, basuras **105 €/año**.

- la ficha de Alcantarilla lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Alhama de Murcia lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Caravaca de la Cruz lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Cartagena lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Jumilla lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Lorca lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Mazarrón lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Molina de Segura lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Murcia lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de San Javier lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de San Pedro del Pinatar lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Torre Pacheco lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Totana lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Yecla lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)
- la ficha de Águilas lo cita con basuras 108.0 € (su propia ficha dice 105.0 €)

## Jumilla (Murcia)

Valor publicado: IBI urbano **0.62%**, basuras **102 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Lorca (Murcia)

Valor publicado: IBI urbano **0.68%**, basuras **135 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.65%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.65%
- el gráfico de la ficha de Cartagena lo dibuja con 0.65%
- el gráfico de la ficha de Jumilla lo dibuja con 0.65%
- el gráfico de la ficha de Murcia lo dibuja con 0.65%
- el gráfico de la ficha de San Javier lo dibuja con 0.65%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.65%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.65%
- el gráfico de la ficha de Totana lo dibuja con 0.65%
- la ficha de Alcantarilla lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Alcantarilla lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Alhama de Murcia lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Alhama de Murcia lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Caravaca de la Cruz lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Caravaca de la Cruz lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Cartagena lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Cartagena lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Cieza lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Cieza lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Jumilla lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Jumilla lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Mazarrón lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Mazarrón lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Molina de Segura lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Molina de Segura lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Murcia lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Murcia lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de San Javier lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de San Javier lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de San Pedro del Pinatar lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Torre Pacheco lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Torre Pacheco lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Totana lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Totana lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Yecla lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Yecla lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)
- la ficha de Águilas lo cita con IBI 0.65% (su propia ficha dice 0.68%)
- la ficha de Águilas lo cita con basuras 115.0 € (su propia ficha dice 135.0 €)

## Mazarrón (Murcia)

Valor publicado: IBI urbano **0.65%**, basuras **112 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.63%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.63%
- el gráfico de la ficha de Cartagena lo dibuja con 0.63%
- el gráfico de la ficha de Jumilla lo dibuja con 0.63%
- el gráfico de la ficha de Murcia lo dibuja con 0.63%
- el gráfico de la ficha de San Javier lo dibuja con 0.63%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.63%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.63%
- el gráfico de la ficha de Totana lo dibuja con 0.63%
- la ficha de Alcantarilla lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Alcantarilla lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Alhama de Murcia lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Alhama de Murcia lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Caravaca de la Cruz lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Caravaca de la Cruz lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Cartagena lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Cartagena lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Cieza lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Cieza lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Jumilla lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Jumilla lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Lorca lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Lorca lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Molina de Segura lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Molina de Segura lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Murcia lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Murcia lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de San Javier lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de San Javier lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de San Pedro del Pinatar lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Torre Pacheco lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Torre Pacheco lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Totana lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Totana lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Yecla lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Yecla lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- la ficha de Águilas lo cita con IBI 0.63% (su propia ficha dice 0.65%)
- la ficha de Águilas lo cita con basuras 115.0 € (su propia ficha dice 112.0 €)
- municipal_factcheck.json registra IBI 0.62% frente al 0.65% publicado

## Molina de Segura (Murcia)

Valor publicado: IBI urbano **0.65%**, basuras **128 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.66%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.66%
- el gráfico de la ficha de Cartagena lo dibuja con 0.66%
- el gráfico de la ficha de Jumilla lo dibuja con 0.66%
- el gráfico de la ficha de Murcia lo dibuja con 0.66%
- el gráfico de la ficha de San Javier lo dibuja con 0.66%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.66%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.66%
- el gráfico de la ficha de Totana lo dibuja con 0.66%
- la ficha de Alcantarilla lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Alhama de Murcia lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Caravaca de la Cruz lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Cartagena lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Cieza lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Jumilla lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Lorca lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Mazarrón lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Murcia lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de San Javier lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Torre Pacheco lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Totana lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Yecla lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- la ficha de Águilas lo cita con IBI 0.66% (su propia ficha dice 0.65%)
- municipal_factcheck.json registra IBI 0.66% frente al 0.65% publicado

## Murcia (Murcia)

Valor publicado: IBI urbano **0.66%**, basuras **125 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## San Javier (Murcia)

Valor publicado: IBI urbano **0.63%**, basuras **118 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## San Pedro del Pinatar (Murcia)

Valor publicado: IBI urbano **0.63%**, basuras **115 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Torre Pacheco (Murcia)

Valor publicado: IBI urbano **0.64%**, basuras **115 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Totana (Murcia)

Valor publicado: IBI urbano **0.62%**, basuras **100 €/año**.

- cita «BORM nº 245, 20/12/2025» como fuente, igual que otros 8 municipios: un único número de boletín no puede contener todas esas ordenanzas

## Yecla (Murcia)

Valor publicado: IBI urbano **0.63%**, basuras **98 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.62%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.62%
- el gráfico de la ficha de Cartagena lo dibuja con 0.62%
- el gráfico de la ficha de Jumilla lo dibuja con 0.62%
- el gráfico de la ficha de Murcia lo dibuja con 0.62%
- el gráfico de la ficha de San Javier lo dibuja con 0.62%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.62%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.62%
- el gráfico de la ficha de Totana lo dibuja con 0.62%
- la ficha de Alcantarilla lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Alcantarilla lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Alhama de Murcia lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Alhama de Murcia lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Caravaca de la Cruz lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Caravaca de la Cruz lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Cartagena lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Cartagena lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Cieza lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Cieza lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Jumilla lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Jumilla lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Lorca lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Lorca lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Mazarrón lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Mazarrón lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Molina de Segura lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Molina de Segura lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Murcia lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Murcia lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de San Javier lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de San Javier lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de San Pedro del Pinatar lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Torre Pacheco lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Torre Pacheco lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Totana lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Totana lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- la ficha de Águilas lo cita con IBI 0.62% (su propia ficha dice 0.63%)
- la ficha de Águilas lo cita con basuras 105.0 € (su propia ficha dice 98.0 €)
- municipal_factcheck.json registra IBI 0.6% frente al 0.63% publicado

## Águilas (Murcia)

Valor publicado: IBI urbano **0.66%**, basuras **118 €/año**.

- el gráfico de la ficha de Alcantarilla lo dibuja con 0.63%
- el gráfico de la ficha de Alhama de Murcia lo dibuja con 0.63%
- el gráfico de la ficha de Cartagena lo dibuja con 0.63%
- el gráfico de la ficha de Jumilla lo dibuja con 0.63%
- el gráfico de la ficha de Murcia lo dibuja con 0.63%
- el gráfico de la ficha de San Javier lo dibuja con 0.63%
- el gráfico de la ficha de San Pedro del Pinatar lo dibuja con 0.63%
- el gráfico de la ficha de Torre Pacheco lo dibuja con 0.63%
- el gráfico de la ficha de Totana lo dibuja con 0.63%
- la ficha de Alcantarilla lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Alcantarilla lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Alhama de Murcia lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Alhama de Murcia lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Caravaca de la Cruz lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Caravaca de la Cruz lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Cartagena lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Cartagena lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Cieza lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Cieza lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Jumilla lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Jumilla lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Lorca lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Lorca lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Mazarrón lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Mazarrón lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Molina de Segura lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Molina de Segura lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Murcia lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Murcia lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de San Javier lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de San Javier lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de San Pedro del Pinatar lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de San Pedro del Pinatar lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Torre Pacheco lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Torre Pacheco lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Totana lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Totana lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- la ficha de Yecla lo cita con IBI 0.63% (su propia ficha dice 0.66%)
- la ficha de Yecla lo cita con basuras 110.0 € (su propia ficha dice 118.0 €)
- municipal_factcheck.json registra IBI 0.63% frente al 0.66% publicado
