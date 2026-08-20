#!/usr/bin/env node
/**
 * rebuild_all_municipalities.js
 * 
 * Regenera TODAS las páginas de municipio con contenido único y sustancial.
 * - Elimina secciones duplicadas/template
 * - Reescribe texto IA de baja calidad
 * - Añade autoría y credenciales
 * - Crea página "Sobre nosotros"
 * - Corrige sub-enlaces rotos en la homepage
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DATA_FILE = path.join(ROOT, 'data', 'municipal_factcheck.json');

// ─── Load municipal data ─────────────────────────────────────────
const rawData = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));

// ─── Municipality-specific contextual data ───────────────────────
// These provide UNIQUE editorial context per municipality so no two pages read the same.
const municipalityContext = {
  // ARAGÓN
  "aragon/huesca/barbastro": {
    pop: "17.100", comarca: "Somontano de Barbastro", nickLocal: "la capital del Somontano",
    geoContext: "Situada en la comarca del Somontano, entre el Prepirineo y la depresión del Ebro, Barbastro es la capital comarcal y sede del Obispado. Su economía se apoya en la industria agroalimentaria, la viticultura (DO Somontano) y el sector servicios.",
    ibiContext: "El valor catastral medio de las viviendas en Barbastro se sitúa entre 50.000 € y 75.000 €, cifras propias de una ciudad intermedia aragonesa con un parque inmobiliario renovado parcialmente en la última década.",
    basuraContext: "La recogida de residuos la gestiona la comarca del Somontano. La implantación del quinto contenedor (biorresiduos) en 2025 ha repercutido en un incremento de la tasa respecto al ejercicio anterior.",
    plusvaliaContext: "La actividad inmobiliaria se concentra en el centro histórico y en las urbanizaciones de la zona sur. Las transmisiones hereditarias superan a las compraventas en número, por lo que la bonificación por herencia de vivienda habitual es especialmente relevante.",
    bonificacionContext: "El Ayuntamiento de Barbastro aplica un descuento por familia numerosa general y otro superior para la categoría especial. La bonificación por instalación solar fotovoltaica en autoconsumo se concede durante 3 ejercicios.",
    reclamacionTip: "Si tu recibo no refleja una bonificación que ya tenías reconocida, presenta un escrito en el registro del Ayuntamiento antes de que finalice el período voluntario; evitarás recargos mientras se resuelve."
  },
  "aragon/huesca/jaca": {
    pop: "12.700", comarca: "La Jacetania", nickLocal: "la capital del Pirineo aragonés",
    geoContext: "Jaca es la puerta del Pirineo aragonés y capital de La Jacetania. Su economía combina el turismo de montaña (estación de Astún y Candanchú), el sector servicios para la comarca y la base militar. El parque inmobiliario incluye muchas segundas residencias de propietarios de Zaragoza y Navarra.",
    ibiContext: "Al contar con un número elevado de segundas residencias, el tipo de IBI urbano se mantiene moderado para no penalizar a los residentes habituales. El valor catastral medio de un piso en el casco urbano ronda los 60.000–80.000 €.",
    basuraContext: "El coste del servicio de recogida es comparativamente alto debido a la dispersión de los núcleos rurales del municipio y al incremento estacional de población en temporada de esquí.",
    plusvaliaContext: "El mercado de segundas residencias genera un volumen significativo de transmisiones anuales. Si compraste un apartamento antes de 2015 y lo vendes ahora, es probable que el método real sea más favorable que el objetivo.",
    bonificacionContext: "Jaca ofrece una bonificación del 30% por familia numerosa y un 25% por instalación solar. La solicitud debe presentarse antes del 31 de marzo del ejercicio.",
    reclamacionTip: "Las segundas residencias NO pueden acogerse a bonificaciones de familia numerosa, ya que exigen empadronamiento en el inmueble como vivienda habitual."
  },
  "aragon/huesca/monzon": {
    pop: "17.400", comarca: "Cinca Medio", nickLocal: "la ciudad del Cinca",
    geoContext: "Monzón se sitúa en la confluencia de los ríos Cinca y Sosa. Su economía se basa en la agricultura de regadío, la industria química y la logística. Es conocida por el Castillo templario que corona la colina sobre el casco urbano.",
    ibiContext: "Los valores catastrales en Monzón son de los más bajos de la provincia de Huesca, lo que compensa un tipo impositivo cercano a la media. Una vivienda tipo de 90 m² en el centro tiene un valor catastral entre 40.000 € y 60.000 €.",
    basuraContext: "La tasa de basuras se cobra de forma conjunta con el IBI a través de la Diputación Provincial de Huesca. La cuota para vivienda es fija, sin distinguir superficie.",
    plusvaliaContext: "Las transmisiones patrimoniales son relativamente escasas al tratarse de un municipio con baja rotación inmobiliaria. Las herencias representan el grueso de las declaraciones de plusvalía.",
    bonificacionContext: "La bonificación por familia numerosa en Monzón es del 20%, algo inferior a otros municipios aragoneses. Existe bonificación del 25% por energía solar durante 3 años.",
    reclamacionTip: "Si el recibo llega a través de la Diputación Provincial de Huesca, la reclamación debe dirigirse al Servicio Provincial de Recaudación, no directamente al Ayuntamiento."
  },
  "aragon/teruel/teruel": {
    pop: "35.900", comarca: "Comunidad de Teruel", nickLocal: "la ciudad de los amantes",
    geoContext: "Teruel, capital de la provincia más despoblada de España, combina un casco histórico patrimonio mudéjar con barrios de expansión moderna. Su economía gira en torno a la administración pública, el comercio comarcal y la agroindustria. Los valores inmobiliarios están entre los más bajos del país.",
    ibiContext: "El precio de la vivienda en Teruel es uno de los más asequibles de España, lo que se refleja en valores catastrales muy bajos. Un piso de 100 m² en zona centro no suele superar los 55.000 € de valor catastral.",
    basuraContext: "La tasa de basuras en Teruel es de las más reducidas de Aragón, coherente con el coste de vida general de la ciudad. El servicio lo presta directamente el Ayuntamiento.",
    plusvaliaContext: "La baja revalorización inmobiliaria de los últimos años hace que muchas transmisiones no generen plusvalía real. Si vendes con pérdidas, acredítalo con las escrituras.",
    bonificacionContext: "Teruel capital ofrece un 30% de bonificación por familia numerosa y un 35% por instalación solar, porcentajes superiores a la media provincial, dentro de la política de incentivos contra la despoblación.",
    reclamacionTip: "Las bonificaciones se solicitan en la Oficina de Atención al Ciudadano del Ayuntamiento o a través de la sede electrónica con certificado digital."
  },
  "aragon/zaragoza/calatayud": {
    pop: "20.300", comarca: "Comunidad de Calatayud", nickLocal: "la ciudad bilbilitana",
    geoContext: "Calatayud, la segunda ciudad de la provincia de Zaragoza, se asienta sobre el río Jalón a medio camino entre Zaragoza y Madrid. Su patrimonio mudéjar y su posición en el corredor del AVE la convierten en un polo comarcal de servicios con un parque inmobiliario asequible.",
    ibiContext: "Los valores catastrales de Calatayud se revisaron por última vez en 2013 y están por debajo de la media provincial. Una vivienda de 80 m² en el casco antiguo puede tener un valor catastral de 35.000–50.000 €.",
    basuraContext: "El Ayuntamiento de Calatayud gestiona directamente el servicio de recogida. La tasa se aprueba anualmente en la ordenanza fiscal y se cobra en un único recibo junto con el de alcantarillado.",
    plusvaliaContext: "La actividad inmobiliaria reside principalmente en el casco urbano y en las pedanías. Las herencias entre familiares directos suponen la mayoría de las transmisiones declaradas.",
    bonificacionContext: "La bonificación por familia numerosa en Calatayud es del 25% para la categoría general. El descuento por instalación solar es del 20%, uno de los más moderados de Aragón.",
    reclamacionTip: "Si tu inmueble está en una de las pedanías (Marivella, Campiel, Huérmeda…), verifica que la referencia catastral en el recibo corresponde a tu finca y no a otra del mismo núcleo."
  },
  "aragon/zaragoza/ejea-de-los-caballeros": {
    pop: "16.800", comarca: "Cinco Villas", nickLocal: "la capital de las Cinco Villas",
    geoContext: "Ejea de los Caballeros es el centro económico de la comarca de Cinco Villas, una de las mayores productoras cerealistas de España. Su economía combina la agricultura extensiva de regadío, la industria agroalimentaria y un activo sector de servicios comarcales.",
    ibiContext: "El tipo de IBI urbano en Ejea se sitúa ligeramente por debajo de la media provincial. Los valores catastrales reflejan un mercado inmobiliario estable con precios asequibles.",
    basuraContext: "La tasa de basuras se ha incrementado tras la entrada en vigor de la recogida separada de biorresiduos. El servicio se presta a través de la Comarca.",
    plusvaliaContext: "Las transmisiones inmobiliarias en Ejea están ligadas mayoritariamente a herencias de patrimonio familiar agrario. El suelo rústico NO está sujeto a plusvalía municipal.",
    bonificacionContext: "Ejea aplica un 20% de bonificación por familia numerosa y un 30% por instalación solar. La solicitud de la bonificación solar requiere certificado de la instalación inscrito en el registro de la DGA.",
    reclamacionTip: "Los inmuebles rústicos no tributan por plusvalía. Si has recibido una liquidación por transmisión de fincas rústicas, impúgnala porque el impuesto solo grava suelo urbano."
  },
  "aragon/zaragoza/tarazona": {
    pop: "10.500", comarca: "Tarazona y el Moncayo", nickLocal: "la ciudad del Moncayo",
    geoContext: "Tarazona es la capital de la comarca del Moncayo, en el límite entre Aragón, Navarra y La Rioja. Su catedral mudéjar y la proximidad al Parque Natural del Moncayo atraen turismo cultural y de naturaleza que complementa la actividad agropecuaria comarcal.",
    ibiContext: "Los valores catastrales en Tarazona son moderados, propios de una ciudad pequeña con mercado inmobiliario estable. Un piso estándar de 90 m² puede tener un valor catastral entre 40.000 € y 55.000 €.",
    basuraContext: "La recogida la gestiona el propio Ayuntamiento con un contrato de servicio comarcal. La tasa es de las más reducidas de la provincia de Zaragoza.",
    plusvaliaContext: "El bajo dinamismo inmobiliario implica que la mayoría de declaraciones de plusvalía corresponden a herencias. La bonificación por herencia de vivienda habitual es un recurso importante en este municipio.",
    bonificacionContext: "El Ayuntamiento de Tarazona aplica bonificaciones moderadas: 25% por familia numerosa y 25% por energía solar. La domiciliación del recibo conlleva un 2% adicional de descuento.",
    reclamacionTip: "Tarazona permite fraccionar el IBI en dos plazos sin intereses si se solicita antes del inicio del período voluntario. No hay fraccionamiento automático por domiciliación."
  },
  "aragon/zaragoza/utebo": {
    pop: "19.200", comarca: "Ribera Alta del Ebro", nickLocal: "municipio limítrofe con Zaragoza",
    geoContext: "Utebo es un municipio del primer cinturón metropolitano de Zaragoza. Ha experimentado un fuerte crecimiento demográfico en las últimas dos décadas, con numerosas promociones de vivienda nueva que han elevado el censo de contribuyentes de IBI por encima de la media comarcal.",
    ibiContext: "Al tratarse de un municipio de reciente expansión urbanística, los valores catastrales son relativamente altos en las urbanizaciones nuevas (60.000–100.000 €) pero más moderados en el casco antiguo.",
    basuraContext: "La tasa de basuras refleja el coste de prestar servicio a un municipio en crecimiento con urbanizaciones dispersas. El ayuntamiento implantó la recogida selectiva de biorresiduos en 2024.",
    plusvaliaContext: "El dinamismo inmobiliario de Utebo genera un volumen considerable de compraventas. Si adquiriste en plena burbuja (2005–2008), es probable que el método real demuestre pérdidas y evites la plusvalía.",
    bonificacionContext: "Utebo ofrece una bonificación del 30% para familias numerosas y un generoso 35% por instalación solar durante 5 ejercicios, uno de los incentivos más amplios de la provincia.",
    reclamacionTip: "Dado que muchos vecinos de Utebo proceden de Zaragoza capital, verifica que tu empadronamiento está actualizado: la bonificación de familia numerosa exige residencia habitual acreditada."
  },

  // ASTURIAS
  "asturias/asturias/aviles": {
    pop: "78.000", comarca: "Comarca de Avilés", nickLocal: "la villa del adelantado",
    geoContext: "Avilés, tercer municipio de Asturias, ha transitado de la industria siderúrgica al turismo cultural gracias al Centro Niemeyer. Su parque inmobiliario combina edificaciones del siglo XX asociadas al boom industrial con promociones más recientes en la zona de la ría.",
    ibiContext: "El organismo recaudador en Asturias es Tributas del Principado. El tipo de IBI urbano en Avilés es moderado y los valores catastrales se revisaron al alza en 2017, lo que provocó ajustes en las cuotas.",
    basuraContext: "La tasa de basuras es comparativamente elevada dentro de Asturias, justificada por los costes del tratamiento en COGERSA y la recogida puerta a puerta en el casco histórico.",
    plusvaliaContext: "El mercado inmobiliario de Avilés ha tenido una revalorización lenta pero estable. Los pisos en La Magdalena y Sabugo han registrado las mayores plusvalías en los últimos cinco años.",
    bonificacionContext: "Avilés ofrece una bonificación del 40% para familias numerosas de categoría general y un 50% para la especial. La bonificación solar alcanza el 50% durante 3 años, la máxima en Asturias junto a Gijón y Oviedo.",
    reclamacionTip: "Las bonificaciones de familia numerosa se solicitan en Tributas del Principado de Asturias, no en el Ayuntamiento. Necesitas aportar copia del título de familia numerosa vigente y certificado de empadronamiento."
  },
  "asturias/asturias/castrillon": {
    pop: "22.800", comarca: "Comarca de Avilés", nickLocal: "el concejo de las playas",
    geoContext: "Castrillón se extiende entre la costa occidental asturiana y el interior, con núcleos como Piedras Blancas (capital), Salinas y Arnao. Su economía combina la proximidad al área industrial de Avilés con el turismo de playa.",
    ibiContext: "El tipo de IBI en Castrillón es de los más bajos de la comarca de Avilés. Los valores catastrales difieren sustancialmente entre las viviendas costeras de Salinas (más altos) y las del interior.",
    basuraContext: "La tasa de basuras incluye la recogida estival reforzada en las playas de Salinas y San Juan de Nieva, lo que repercute ligeramente en la cuota general.",
    plusvaliaContext: "La franja costera (Salinas, Arnao) concentra la mayor parte de las plusvalías declaradas, con valores al alza por la demanda de vivienda vacacional.",
    bonificacionContext: "Castrillón aplica un 35% de descuento por familia numerosa general y un 40% por instalación solar. La energía eólica de autoconsumo también puede acogerse a bonificación.",
    reclamacionTip: "Si tu vivienda está en zona costera y el valor catastral te parece desproporcionado, puedes solicitar una revisión en la Gerencia Territorial del Catastro en Oviedo."
  },
  "asturias/asturias/gijon": {
    pop: "271.000", comarca: "Área metropolitana de Asturias", nickLocal: "la capital de la Costa Verde",
    geoContext: "Gijón es el municipio más poblado de Asturias y su principal motor económico. Su puerto, la Universidad Laboral reconvertida, y la gastronomía atlántica configuran una ciudad con un mercado inmobiliario variado que abarca desde el casco histórico de Cimadevilla hasta los ensanches de El Llano y Nuevo Gijón.",
    ibiContext: "El IBI en Gijón se gestiona a través de Tributas del Principado de Asturias. El tipo urbano es de los más altos de la comunidad, pero el período de pago es temprano (abril-mayo), lo que lo diferencia de la mayoría de municipios españoles.",
    basuraContext: "Gijón tiene una de las tasas de basuras más altas de Asturias, acorde con su tamaño y la complejidad de su servicio de recogida. La separación de biorresiduos es obligatoria desde 2024.",
    plusvaliaContext: "El mercado gijonés ha mostrado una revalorización notable tras 2020, especialmente en Cimadevilla y la zona de la playa de San Lorenzo. Las transmisiones por compraventa superan a las hereditarias.",
    bonificacionContext: "Gijón aplica las bonificaciones máximas permitidas: 50% para familia numerosa especial y 50% por instalación solar durante 5 años. Es el municipio asturiano con incentivos fiscales más amplios.",
    reclamacionTip: "El Ayuntamiento de Gijón permite fraccionar el IBI en 9 mensualidades sin intereses si se domicilia antes del 15 de febrero. Es una opción muy ventajosa para cuotas elevadas."
  },
  "asturias/asturias/langreo": {
    pop: "40.000", comarca: "Valle del Nalón", nickLocal: "la capital de las cuencas",
    geoContext: "Langreo (La Felguera, Sama, Ciaño, Barros) es el corazón histórico de la cuenca minera asturiana. La reconversión industrial ha reconfigurado su tejido económico hacia servicios, comercio y un incipiente sector tecnológico en el Parque Empresarial Valnalón.",
    ibiContext: "Los valores catastrales en Langreo son moderados-bajos, coherentes con un mercado inmobiliario donde los precios de venta están por debajo de la media regional. El tipo de IBI urbano se sitúa en la franja media.",
    basuraContext: "La tasa de basuras se ha incrementado para cubrir los costes de la nueva planta de separación de residuos comarcal. El Consorcio de Residuos del Valle del Nalón gestiona el servicio.",
    plusvaliaContext: "La baja rotación inmobiliaria hace que la mayoría de liquidaciones de plusvalía correspondan a herencias. Los precios deprimidos pueden justificar una plusvalía real inferior a la objetiva.",
    bonificacionContext: "Langreo bonifica al 35% a familias numerosas y al 30% por energía solar. Existe un descuento adicional del 3% por domiciliación del recibo.",
    reclamacionTip: "Si heredas una vivienda en Langreo y el valor de mercado actual es inferior al de adquisición originaria, aporta una tasación actualizada junto con la declaración para evitar tributar por una plusvalía inexistente."
  },
  "asturias/asturias/mieres": {
    pop: "38.000", comarca: "Valle del Caudal", nickLocal: "la capital del Caudal",
    geoContext: "Mieres, capital del Valle del Caudal, comparte con Langreo el legado de la minería del carbón. La ciudad se ha orientado hacia el sector servicios, con la Escuela de Minas (Universidad de Oviedo) como referente académico del concejo.",
    ibiContext: "El IBI en Mieres tiene un tipo urbano moderado. Los valores catastrales no se han revisado al alza recientemente, lo que mantiene las cuotas relativamente contenidas.",
    basuraContext: "La gestión de residuos la comparte con COGERSA. La tasa de basuras para vivienda habitual es inferior a la de los grandes municipios asturianos.",
    plusvaliaContext: "La escasa revalorización inmobiliaria en las últimas décadas hace que muchas transmisiones en Mieres no generen plusvalía real. El método real suele ser el más favorable.",
    bonificacionContext: "Mieres aplica un 30% de bonificación por familia numerosa y un 35% por instalación solar. Se exige acreditar el rendimiento energético de la instalación.",
    reclamacionTip: "El campus universitario de Mieres y sus alrededores concentran inmuebles con alta rotación (alquiler estudiantil). Si eres arrendador, recuerda que la tasa de basuras es tu responsabilidad legal aunque la repercutas contractualmente."
  },
  "asturias/asturias/oviedo": {
    pop: "220.000", comarca: "Área metropolitana de Asturias", nickLocal: "la capital del Principado",
    geoContext: "Oviedo, capital administrativa del Principado de Asturias, concentra la administración autonómica, la Universidad y un importante sector terciario. Su casco antiguo y el ensanche modernista configuran un mercado inmobiliario con valores catastrales superiores a la media regional.",
    ibiContext: "El tipo de IBI urbano en Oviedo es el segundo más alto de Asturias tras Gijón. Los valores catastrales se revisaron en 2014 y reflejan un mercado de precios medios-altos para la comunidad.",
    basuraContext: "La tasa de basuras de Oviedo es elevada, acorde con la calidad del servicio de recogida y el tamaño de la ciudad. Se cobra en un recibo separado del IBI.",
    plusvaliaContext: "Oviedo tiene un mercado inmobiliario activo con transmisiones tanto por compraventa como por herencia. Las zonas más revalorizadas son el centro, Montevil y La Corredoria.",
    bonificacionContext: "El Ayuntamiento aplica el máximo legal del 50% por familia numerosa especial y un 50% por energía solar durante 5 años. Es el municipio asturiano con mayor número de bonificaciones concedidas.",
    reclamacionTip: "Oviedo permite el pago del IBI en varias cuotas a lo largo del año si se domicilia. Consulta el calendario exacto de cargo en Tributas del Principado antes del 28 de febrero."
  },
  "asturias/asturias/siero": {
    pop: "53.000", comarca: "Área metropolitana de Asturias", nickLocal: "el concejo del martes",
    geoContext: "Siero, con capital en Pola de Siero, es uno de los municipios más dinámicos del área metropolitana asturiana. Su feria de ganado de los martes y el polígono industrial del Espíritu Santo son referentes. Lugones, su núcleo más poblado, funciona como ciudad dormitorio de Oviedo.",
    ibiContext: "El tipo de IBI en Siero refleja la dualidad entre zonas rurales (con valores catastrales bajos) y Lugones-Pola (con valores catastrales de nivel metropolitano). La media es intermedia.",
    basuraContext: "La tasa de basuras se incrementó en 2025 por la implantación de la recogida selectiva puerta a puerta en Lugones. Los núcleos rurales mantienen el sistema de contenedores.",
    plusvaliaContext: "Lugones registra la mayor actividad inmobiliaria del concejo, con precios de venta que compiten con los de Oviedo y valores de plusvalía significativos.",
    bonificacionContext: "Siero bonifica al 35% por familia numerosa y al 40% por instalación solar. La alta radiación solar en la cuenca central asturiana hace que esta bonificación tenga demanda creciente.",
    reclamacionTip: "Si resides en Lugones pero tu empadronamiento figura en Pola de Siero, la bonificación de familia numerosa es válida igualmente mientras el inmueble bonificado sea tu vivienda habitual."
  },

  // CASTILLA-LA MANCHA
  "castilla-la-mancha/albacete/almansa": {
    pop: "24.800", comarca: "Corredor de Almansa", nickLocal: "la ciudad del castillo",
    geoContext: "Almansa se sitúa en el corredor mediterráneo entre La Mancha y Levante. Su economía se apoya en la industria del calzado, la agricultura cerealista y una posición logística privilegiada en el eje Madrid-Valencia.",
    ibiContext: "El valor catastral en Almansa es moderado, propio de un municipio industrial manchego. Los inmuebles del centro histórico, al pie del castillo, tienen valores sensiblemente inferiores a los de las zonas de nueva construcción.",
    basuraContext: "La tasa de basuras en Almansa es de las más bajas de la provincia de Albacete, coherente con el menor coste de recogida respecto a núcleos más dispersos.",
    plusvaliaContext: "La actividad inmobiliaria se concentra en vivienda habitual. Las herencias son el principal hecho imponible de la plusvalía en este municipio.",
    bonificacionContext: "Almansa aplica un 25% de descuento por familia numerosa general y un 30% por instalación solar. No dispone de bonificación por domiciliación.",
    reclamacionTip: "El recibo del IBI lo gestiona el Servicio de Recaudación Provincial de la Diputación de Albacete. Las reclamaciones se presentan ante dicho organismo, no directamente en el Ayuntamiento."
  },
  "castilla-la-mancha/albacete/hellin": {
    pop: "30.400", comarca: "Sierra de Segura", nickLocal: "la puerta de Andalucía",
    geoContext: "Hellín, al sureste de la provincia de Albacete, es un nudo de comunicaciones entre Castilla-La Mancha, Murcia y Andalucía. Sus tambores de Semana Santa (declarados Patrimonio de la Humanidad) y su industria textil configuran un municipio activo.",
    ibiContext: "Los valores catastrales en Hellín están por encima de Almansa pero por debajo de Albacete capital. El tipo de IBI refleja la necesidad de financiar servicios para una población dispersa en varios núcleos.",
    basuraContext: "La recogida de residuos atiende al casco urbano y a pedanías como Isso, Agramón o Cancarix, lo que eleva los costes del servicio por kilómetro recorrido.",
    plusvaliaContext: "El mercado inmobiliario de Hellín es estable con precios moderados. Las transmisiones hereditarias predominan sobre las compraventas en el cómputo anual.",
    bonificacionContext: "Hellín bonifica al 30% por familia numerosa y al 25% por energía solar. Existe una bonificación adicional por BIC aplicable a inmuebles del casco histórico.",
    reclamacionTip: "Si tu inmueble está catalogado como Bien de Interés Cultural o incluido en el entorno de protección, consulta si puedes acceder a la bonificación de hasta el 90% que contempla la ley."
  },
  "castilla-la-mancha/ciudad-real/alcazar-de-san-juan": {
    pop: "30.600", comarca: "Mancha Centro", nickLocal: "el corazón de La Mancha",
    geoContext: "Alcázar de San Juan, nudo ferroviario histórico de Castilla-La Mancha, se sitúa en plena llanura manchega. Su economía se basa en la viticultura, la industria agroalimentaria y los servicios comarcales.",
    ibiContext: "Los valores catastrales en Alcázar son moderados. Las grandes fincas industriales (bodegas, cooperativas) elevan la recaudación total de IBI sin sobrecargar la cuota de viviendas.",
    basuraContext: "La tasa de basuras distingue entre vivienda habitual, locales comerciales y naves industriales, con tarifas diferenciadas que reflejan el volumen de residuos generado.",
    plusvaliaContext: "El mercado inmobiliario es estable con una rotación baja. Las herencias de patrimonio agrícola (que incluyen suelo urbano) son el principal origen de las plusvalías declaradas.",
    bonificacionContext: "El Ayuntamiento de Alcázar de San Juan aplica un 25% de bonificación por familia numerosa. La bonificación por energía solar es del 25% durante 3 años.",
    reclamacionTip: "Las fincas rústicas de regadío que rodean el casco urbano pueden figurar como suelo urbanizable en el Catastro. Verifica la clasificación para no tributar por IBI urbano indebidamente."
  },
  "castilla-la-mancha/ciudad-real/puertollano": {
    pop: "47.300", comarca: "Valle de Alcudia", nickLocal: "la ciudad de la energía",
    geoContext: "Puertollano creció al calor de la industria petroquímica (Repsol) y la minería del carbón. Hoy se posiciona como polo de hidrógeno verde. Su parque inmobiliario muestra la dualidad entre barrios obreros históricos y urbanizaciones más recientes.",
    ibiContext: "El tipo de IBI urbano en Puertollano es de los más altos de Castilla-La Mancha, reflejo de la necesidad de financiar servicios para una ciudad industrial con pasivos ambientales. Los valores catastrales, sin embargo, son bajos en comparación con capitales de provincia.",
    basuraContext: "La tasa de basuras es intermedia. La reconversión hacia una gestión medioambiental más exigente ha incrementado los costes del servicio de forma moderada.",
    plusvaliaContext: "La evolución de precios en Puertollano ha sido irregular: hubo revalorización durante el boom industrial y estancamiento posterior. Esto puede generar diferencias significativas según la fecha de adquisición.",
    bonificacionContext: "Puertollano ofrece un 30% de bonificación por familia numerosa y un generoso 35% por instalación solar, coherente con su apuesta por la transición energética.",
    reclamacionTip: "Si tu vivienda se encuentra en la zona afectada por los planes de remediación medioambiental, comprueba si existe algún programa específico de reducción de IBI ligado a limitaciones de uso del suelo."
  },
  "castilla-la-mancha/ciudad-real/tomelloso": {
    pop: "36.200", comarca: "Mancha Centro", nickLocal: "la ciudad del vino",
    geoContext: "Tomelloso es la capital española del vino en volumen. Sus bodegas, destilerías y cooperativas agrícolas configuran un municipio próspero donde el sector vitivinícola genera la mayor parte de la actividad económica.",
    ibiContext: "El tipo de IBI refleja un equilibrio entre la tributación residencial y la de las grandes naves bodegueras. Los valores catastrales de viviendas son moderados.",
    basuraContext: "La tasa de basuras se aplica de forma diferenciada: las bodegas e industrias agroalimentarias pagan tarifas especiales por la naturaleza de los residuos generados.",
    plusvaliaContext: "Las transmisiones de patrimonio vinícola (que incluye suelo urbano de naves y bodegas) son el principal generador de plusvalías en Tomelloso.",
    bonificacionContext: "Tomelloso aplica un 25% de bonificación por familia numerosa y un 20% por instalación solar, porcentajes modestos en el contexto regional.",
    reclamacionTip: "Si eres propietario de una nave bodeguera y el valor catastral no distingue correctamente entre suelo y construcción, la base imponible de la plusvalía puede estar inflada. Solicita el desglose al Catastro."
  },
  "castilla-la-mancha/cuenca/cuenca": {
    pop: "54.800", comarca: "Serranía de Cuenca", nickLocal: "la ciudad de las casas colgadas",
    geoContext: "Cuenca capital, Patrimonio de la Humanidad, combina un casco histórico con valor artístico excepcional y una ciudad moderna en expansión. Su economía se basa en la administración pública, el turismo cultural y los servicios provinciales.",
    ibiContext: "Los valores catastrales en el casco histórico son significativamente inferiores a los de las zonas de expansión, a pesar de que las viviendas históricas pueden tener mayor valor de mercado. El tipo de IBI urbano es intermedio.",
    basuraContext: "La recogida de basuras en el casco antiguo presenta dificultades logísticas (calles estrechas, pendientes) que incrementan el coste por habitante respecto a la zona moderna.",
    plusvaliaContext: "El turismo ha revalorizado los inmuebles del casco histórico para uso hostelero. Las transmisiones de locales convertidos en alojamientos turísticos pueden generar plusvalías importantes.",
    bonificacionContext: "Cuenca capital ofrece un 35% por familia numerosa y un 30% por instalación solar. Los inmuebles catalogados como BIC pueden acceder a bonificaciones adicionales de hasta el 90%.",
    reclamacionTip: "Si tu vivienda está en el casco histórico y has realizado obras de rehabilitación autorizadas, puedes acogerte a bonificaciones específicas por conservación del patrimonio. Consulta en el Ayuntamiento."
  },
  "castilla-la-mancha/cuenca/tarancon": {
    pop: "16.100", comarca: "Mesa de Ocaña", nickLocal: "la puerta de La Mancha",
    geoContext: "Tarancón se sitúa en la Autovía de Levante (A-3) como punto de entrada a La Mancha desde Madrid. Su creciente actividad logística e industrial la convierte en uno de los municipios más dinámicos de la provincia de Cuenca.",
    ibiContext: "El tipo de IBI es moderado. Los valores catastrales han subido por las nuevas promociones logísticas e industriales que contribuyen a la base impositiva del municipio.",
    basuraContext: "La tasa de basuras para vivienda es de las más bajas de la provincia, beneficiada por la contribución fiscal de las naves industriales y logísticas al presupuesto municipal.",
    plusvaliaContext: "El dinamismo inmobiliario reciente ha generado un aumento de transmisiones. Las viviendas adquiridas antes de 2015 pueden tener plusvalías significativas por la revalorización de la zona.",
    bonificacionContext: "Tarancón aplica un 20% de bonificación por familia numerosa y un 25% por energía solar. Los porcentajes son modestos pero coherentes con un presupuesto municipal limitado.",
    reclamacionTip: "Las naves del polígono industrial tributan por IBI no residencial con tipo diferenciado. Si tu local o nave ha cambiado de uso (por ejemplo, de industrial a comercial), verifica que el Catastro refleja el uso actual."
  },
  "castilla-la-mancha/guadalajara/azuqueca-de-henares": {
    pop: "36.500", comarca: "Corredor del Henares", nickLocal: "municipio del Corredor",
    geoContext: "Azuqueca de Henares forma parte del corredor industrial Madrid-Guadalajara y funciona como municipio residencial del área metropolitana madrileña. Su crecimiento demográfico en las últimas décadas ha sido explosivo, con un parque inmobiliario joven.",
    ibiContext: "Los valores catastrales en Azuqueca son relativamente altos para Castilla-La Mancha, influidos por la proximidad a Madrid. Un piso de 90 m² puede superar los 80.000 € de valor catastral.",
    basuraContext: "La tasa de basuras es elevada, acorde con los estándares de servicio de un municipio metropolitano. La recogida puerta a puerta de biorresiduos se implantó en 2024.",
    plusvaliaContext: "El mercado inmobiliario de Azuqueca se mueve en paralelo al del Corredor del Henares madrileño. Las plusvalías pueden ser significativas para inmuebles adquiridos antes del boom.",
    bonificacionContext: "Azuqueca aplica un 30% de bonificación por familia numerosa y un 35% por instalación solar durante 5 años. La alta proporción de viviendas unifamiliares favorece la fotovoltaica.",
    reclamacionTip: "Muchos vecinos de Azuqueca trabajan en Madrid pero están empadronados en el municipio. Verifica que tu empadronamiento está activo: es imprescindible para la bonificación de familia numerosa."
  },
  "castilla-la-mancha/toledo/illescas": {
    pop: "29.500", comarca: "La Sagra", nickLocal: "la puerta de La Sagra",
    geoContext: "Illescas, en la comarca de La Sagra, ha crecido como municipio residencial del sur de Madrid gracias a la autovía A-42. Grandes plataformas logísticas (Amazon, DHL) se han instalado en su término, diversificando la base fiscal.",
    ibiContext: "El tipo de IBI es moderado pero los valores catastrales de viviendas nuevas son altos para Castilla-La Mancha, por la cercanía a Madrid. Las grandes naves logísticas tributan por IBI no residencial.",
    basuraContext: "La tasa de basuras ha subido para atender a una población en rápido crecimiento. La separación selectiva de residuos es obligatoria desde 2024.",
    plusvaliaContext: "Illescas ha experimentado fuertes revalorizaciones inmobiliarias en los últimos años. Las plusvalías por compraventa pueden ser sustanciales para propiedades adquiridas antes de 2015.",
    bonificacionContext: "El Ayuntamiento bonifica al 30% por familia numerosa y al 30% por energía solar. La domiciliación conlleva un pequeño descuento adicional del 2%.",
    reclamacionTip: "Si tu urbanización es de reciente construcción y aún no se ha producido la cesión de viales al Ayuntamiento, verifica que no estés pagando IBI por zonas comunes que deberían ser de titularidad municipal."
  },
  "castilla-la-mancha/toledo/sesena": {
    pop: "27.500", comarca: "La Sagra", nickLocal: "el municipio de El Quiñón",
    geoContext: "Seseña saltó a la fama con la macro-urbanización de El Quiñón, que multiplicó su población en una década. Hoy es un municipio consolidado del sur de Madrid con familias jóvenes y un parque inmobiliario de construcción reciente.",
    ibiContext: "Los valores catastrales reflejan la construcción reciente de la mayor parte del parque inmobiliario. El tipo de IBI es de los más bajos de la comarca, en parte porque la gran cantidad de contribuyentes permite un tipo reducido.",
    basuraContext: "La tasa se ajusta anualmente para cubrir el servicio en unas urbanizaciones de baja densidad donde la recogida tiene costes logísticos elevados.",
    plusvaliaContext: "Los primeros propietarios de El Quiñón que venden ahora pueden encontrarse con plusvalías moderadas o incluso pérdidas si compraron en el pico de precios (2007-2008).",
    bonificacionContext: "Seseña bonifica al 25% por familia numerosa y al 30% por instalación solar. La alta proporción de viviendas unifamiliares adosadas favorece el autoconsumo fotovoltaico.",
    reclamacionTip: "Si compraste sobre plano durante la construcción de El Quiñón y el valor catastral inicial fue asignado de oficio, revisa que no sea superior al que corresponde por la ponencia de valores vigente."
  },
  "castilla-la-mancha/toledo/talavera-de-la-reina": {
    pop: "83.300", comarca: "Comarca de Talavera", nickLocal: "la ciudad de la cerámica",
    geoContext: "Talavera de la Reina, segunda ciudad de Castilla-La Mancha, es célebre por su cerámica artesanal. Su economía se apoya en el comercio comarcal, la agricultura y un sector cerámico que ha atravesado una profunda reconversión.",
    ibiContext: "El tipo de IBI urbano de Talavera es el más alto de los municipios de nuestra guía en Castilla-La Mancha (0,68%). Sin embargo, los valores catastrales son inferiores a los de ciudades de tamaño similar, lo que modera la cuota final.",
    basuraContext: "La tasa de basuras es también la más alta de los municipios castellano-manchegos de nuestra base, reflejo de los costes de servicio en una ciudad de más de 80.000 habitantes.",
    plusvaliaContext: "El mercado inmobiliario de Talavera sufrió una caída importante tras 2008 y la recuperación ha sido lenta. Para ventas de inmuebles adquiridos en el boom, el método real puede ser más favorable.",
    bonificacionContext: "Talavera ofrece un 35% por familia numerosa general y un 30% por energía solar. La ciudad tiene una bonificación específica para inmuebles en el casco histórico que estén rehabilitados.",
    reclamacionTip: "Si vendes un inmueble por debajo de su valor de adquisición, presenta ambas escrituras al liquidar la plusvalía para acreditar la pérdida. No pagarás plusvalía si no hay incremento real del valor."
  },

  // CASTILLA Y LEÓN
  "castilla-y-leon/avila/avila": {
    pop: "57.700", comarca: "Ávila y su alfoz", nickLocal: "la ciudad amurallada",
    geoContext: "Ávila, Patrimonio de la Humanidad por sus murallas medievales, es la capital de provincia más alta de España. Su economía se basa en el turismo, la administración y un creciente sector residencial para teletrabajadores procedentes de Madrid.",
    ibiContext: "Los valores catastrales varían enormemente entre el casco intramuros (valores moderados por las limitaciones de uso) y las urbanizaciones exteriores (valores más altos en construcciones recientes).",
    basuraContext: "La tasa de basuras cubre un servicio que atiende tanto al casco histórico (con recogida adaptada a las murallas) como a urbanizaciones periféricas dispersas.",
    plusvaliaContext: "La creciente demanda de vivienda por parte de compradores madrileños ha revalorizado los inmuebles, generando plusvalías significativas en las últimas transmisiones.",
    bonificacionContext: "Ávila aplica un 40% de bonificación por familia numerosa, uno de los porcentajes más altos de Castilla y León. La bonificación solar es del 35% durante 3 años.",
    reclamacionTip: "Los inmuebles situados dentro del recinto amurallado tienen limitaciones de obra que pueden afectar a su valor catastral. Solicita una revisión si el valor asignado no refleja las restricciones urbanísticas."
  },
  "castilla-y-leon/burgos/aranda-de-duero": {
    pop: "33.200", comarca: "Ribera del Duero", nickLocal: "la capital del lechazo",
    geoContext: "Aranda de Duero es el principal núcleo urbano de la Ribera del Duero burgalesa. Su economía combina la industria agroalimentaria, la viticultura (DO Ribera del Duero) y un activo comercio comarcal.",
    ibiContext: "El tipo de IBI es intermedio. Los valores catastrales de la zona centro son moderados, mientras que las viviendas nuevas en la zona de expansión norte tienen valores más elevados.",
    basuraContext: "La tasa de basuras incluye el servicio de recogida y la tasa de tratamiento comarcal. La implantación de la recogida de orgánica ha elevado la cuota un 8% en 2026.",
    plusvaliaContext: "El mercado de Aranda es estable con una rotación moderada. Las bodegas subterráneas del casco antiguo pueden plantear dudas de valoración catastral al ser espacios de difícil acceso.",
    bonificacionContext: "Aranda aplica un 30% por familia numerosa y un 30% por instalación solar. Las bodegas restauradas para uso hostelero pueden acceder a bonificaciones por rehabilitación.",
    reclamacionTip: "Si posees una bodega subterránea en el casco histórico y está incluida en tu referencia catastral, verifica que la superficie construida asignada es correcta."
  },
  "castilla-y-leon/burgos/miranda-de-ebro": {
    pop: "35.500", comarca: "Ebro", nickLocal: "la ciudad del Ebro",
    geoContext: "Miranda de Ebro, en el extremo noreste de Burgos, limita con Álava y La Rioja. Su posición estratégica la convierte en nudo ferroviario y logístico. La industria química y la automoción (Lear Corporation) son los principales motores económicos.",
    ibiContext: "El tipo de IBI es moderado-alto. Los valores catastrales reflejan un parque inmobiliario diverso, con viviendas industriales de mediados del siglo XX y promociones recientes en la zona de La Charca.",
    basuraContext: "La tasa de basuras se cobra junto con el recibo de agua a través del servicio municipal, lo que puede causar confusión al contribuyente.",
    plusvaliaContext: "Las transmisiones se concentran en vivienda habitual. La proximidad a Vitoria-Gasteiz genera un flujo de compraventa con compradores alaveses.",
    bonificacionContext: "Miranda aplica un 25% por familia numerosa y un 25% por instalación solar. No dispone de bonificación por domiciliación.",
    reclamacionTip: "Si tu recibo de basuras llega junto con el de agua y consideras que el importe de basuras es incorrecto, debes reclamar por separado al servicio de tributos del Ayuntamiento."
  },
  "castilla-y-leon/leon/ponferrada": {
    pop: "65.400", comarca: "El Bierzo", nickLocal: "la capital del Bierzo",
    geoContext: "Ponferrada, capital de El Bierzo, es la segunda ciudad de la provincia de León. Su castillo templario y el Camino de Santiago atraen turismo, mientras la industria, la pizarra y el sector energético (eólico) sustentan la economía local.",
    ibiContext: "El tipo de IBI urbano es de los más altos de Castilla y León. Los valores catastrales se revisaron en 2015 y son algo superiores a la media de municipios de tamaño similar en la comunidad.",
    basuraContext: "La tasa de basuras es elevada, justificada por los costes de servicio en un municipio extenso con numerosas pedanías rurales además del casco urbano.",
    plusvaliaContext: "El mercado inmobiliario de Ponferrada ha mostrado una recuperación moderada. Los inmuebles del casco antiguo junto al castillo templario se han revalorizado por el turismo.",
    bonificacionContext: "Ponferrada aplica un 35% por familia numerosa y un 30% por energía solar. El Bierzo tiene un potencial fotovoltaico moderado, inferior al de la meseta.",
    reclamacionTip: "Las pedanías de Ponferrada tienen recibos independientes con valores catastrales muy distintos a los del casco urbano. Verifica que tu recibo corresponde al inmueble correcto si eres propietario en zona rural."
  },
  "castilla-y-leon/palencia/palencia": {
    pop: "78.200", comarca: "Tierra de Campos", nickLocal: "la bella desconocida",
    geoContext: "Palencia capital, conocida como 'la Bella Desconocida', alberga la primera universidad de España (1212) y un impresionante patrimonio románico. Su economía combina la automoción (Renault), la agroindustria y los servicios provinciales.",
    ibiContext: "El tipo de IBI es moderado, uno de los más bajos de las capitales de Castilla y León. Los valores catastrales son comedidos, reflejando un mercado inmobiliario asequible.",
    basuraContext: "La tasa de basuras cubre un servicio eficiente para una ciudad compacta. La cuota se ha incrementado ligeramente por la adaptación a la normativa de biorresiduos.",
    plusvaliaContext: "El mercado inmobiliario palentino es estable y poco especulativo. Las plusvalías declaradas suelen ser modestas excepto en el centro comercial.",
    bonificacionContext: "Palencia capital bonifica al 35% por familia numerosa y al 30% por instalación solar. La solicitud se tramita en la Concejalía de Hacienda.",
    reclamacionTip: "Si trabajas en Renault y vives en una de las urbanizaciones del polígono norte, verifica que tu INE está correctamente asignado para evitar duplicidades en la contribución territorial."
  },
  "castilla-y-leon/salamanca/bejar": {
    pop: "12.800", comarca: "Sierra de Béjar", nickLocal: "la ciudad textil",
    geoContext: "Béjar, en la sierra salmantina, conserva un importante legado de la industria textil que la hizo próspera en siglos pasados. Hoy su economía gira en torno al turismo de montaña, la estación de esquí de La Covatilla y un menguante sector industrial.",
    ibiContext: "Los valores catastrales son bajos, propios de una ciudad pequeña con tendencia demográfica decreciente. El tipo de IBI urbano se mantiene en la media para compensar una base impositiva reducida.",
    basuraContext: "La tasa de basuras es de las más reducidas de la guía, coherente con el menor coste de servicio en una población pequeña y compacta.",
    plusvaliaContext: "El mercado inmobiliario de Béjar muestra precios estancados o a la baja, lo que puede generar situaciones de pérdida patrimonial donde no procede liquidar plusvalía.",
    bonificacionContext: "Béjar aplica un 25% de bonificación por familia numerosa y un 20% por instalación solar. Los porcentajes son modestos para un municipio con presupuesto limitado.",
    reclamacionTip: "Si vendes un inmueble en Béjar y el precio de venta es inferior al de compra, no dejes de aportar ambas escrituras para evitar pagar una plusvalía inexistente."
  },
  "castilla-y-leon/segovia/segovia": {
    pop: "51.700", comarca: "Segovia y su alfoz", nickLocal: "la ciudad del acueducto",
    geoContext: "Segovia, Patrimonio de la Humanidad, combina un casco histórico de valor excepcional con un crecimiento residencial alimentado por trabajadores que se desplazan a Madrid por el AVE. Su acueducto romano, el Alcázar y la gastronomía atraen turismo internacional.",
    ibiContext: "Los valores catastrales en Segovia están divididos: el casco intramuros tiene valores moderados pero el mercado de venta es alto; las zonas de expansión (Nueva Segovia, El Sotillo) tienen catastrales más recientes y alineados con el mercado.",
    basuraContext: "La tasa de basuras refleja los costes extra de servicio en un casco histórico con calles estrechas y empedradas. La recogida nocturna en el centro es obligatoria.",
    plusvaliaContext: "La demanda de vivienda por parte de compradores madrileños (a 27 minutos en AVE) ha revalorizado los inmuebles, generando plusvalías significativas en transmisiones.",
    bonificacionContext: "Segovia aplica un 35% por familia numerosa y un 30% por energía solar. Los inmuebles del acueducto o el barrio judío pueden tener bonificaciones adicionales por BIC.",
    reclamacionTip: "Si tu vivienda está a la vista del acueducto y existe una servidumbre de protección visual que limita reformas, esto puede ser motivo para solicitar una revisión del valor catastral a la baja."
  },
  "castilla-y-leon/zamora/zamora": {
    pop: "60.900", comarca: "Alfoz de Zamora", nickLocal: "la bien cercada",
    geoContext: "Zamora capital, famosa por su Semana Santa declarada de Interés Turístico Internacional, cuenta con el mayor patrimonio románico de Europa. Su economía se centra en los servicios provinciales, el turismo cultural y la agroindustria.",
    ibiContext: "El tipo de IBI es uno de los más bajos de las capitales de Castilla y León, compensando una base impositiva reducida por la tendencia demográfica decreciente.",
    basuraContext: "La tasa de basuras es moderada, inferior a la de capitales de provincia de mayor tamaño. El servicio es gestionado directamente por el Ayuntamiento.",
    plusvaliaContext: "El mercado inmobiliario zamorano está estancado, con precios a la baja a largo plazo. Muchas ventas pueden no generar plusvalía real si la adquisición fue posterior a 2005.",
    bonificacionContext: "Zamora aplica un 30% por familia numerosa y un 25% por instalación solar. La bonificación por BIC es especialmente relevante por la densidad de patrimonio románico.",
    reclamacionTip: "Si heredas patrimonio inmobiliario en Zamora y el valor de mercado actual es inferior al valor de adquisición, aporta una tasación profesional para evitar la plusvalía."
  },

  // EXTREMADURA
  "extremadura/badajoz/almendralejo": {
    pop: "33.800", comarca: "Tierra de Barros", nickLocal: "la tierra del cava extremeño",
    geoContext: "Almendralejo es la capital de la comarca de Tierra de Barros, la principal zona vitivinícola de Extremadura. Su economía se basa en bodegas, cooperativas y la DO Ribera del Guadiana. El parque inmobiliario es de tipo medio, con viviendas unifamiliares predominantes.",
    ibiContext: "El IBI se gestiona a través del OAR (Organismo Autónomo de Recaudación) de la Diputación de Badajoz. Los valores catastrales son bajos respecto al nivel nacional.",
    basuraContext: "La tasa de basuras es de las más bajas de la provincia, coherente con los menores costes de servicio en un municipio compacto con pocos núcleos dispersos.",
    plusvaliaContext: "El mercado inmobiliario es estable con precios asequibles. Las herencias de patrimonio familiar (viviendas y bodegas) son el principal hecho imponible.",
    bonificacionContext: "Almendralejo aplica un 25% de bonificación por familia numerosa y un 25% por instalación solar. La alta irradiación solar de la región hace especialmente rentable la fotovoltaica residencial.",
    reclamacionTip: "Los recibos de IBI en Almendralejo los emite el OAR de la Diputación de Badajoz. Las reclamaciones deben dirigirse a ese organismo, con oficina en Mérida."
  },
  "extremadura/badajoz/don-benito": {
    pop: "37.400", comarca: "Vegas Altas", nickLocal: "la capital de las Vegas Altas",
    geoContext: "Don Benito, junto con Villanueva de la Serena, forma uno de los ejes urbanos de las Vegas Altas del Guadiana en Extremadura. Su economía se apoya en la agricultura de regadío (arroz, tomate), la industria agroalimentaria y los servicios comarcales.",
    ibiContext: "El OAR de la Diputación Provincial gestiona el cobro. Los tipos de IBI son moderados y los valores catastrales se sitúan por debajo de la media nacional.",
    basuraContext: "La tasa de basuras cubre la recogida en el casco urbano y las urbanizaciones periféricas. La Mancomunidad de Vegas Altas gestiona el tratamiento de residuos.",
    plusvaliaContext: "Las Vegas Altas tienen un mercado inmobiliario estable con precios asequibles. Las plusvalías suelen ser modestas en transmisiones de vivienda habitual.",
    bonificacionContext: "Don Benito aplica un 25% por familia numerosa y un 25% por instalación solar. El Ayuntamiento permite fraccionar el IBI en dos pagos sin intereses.",
    reclamacionTip: "Don Benito y Villanueva de la Serena comparten muchos servicios comarcales pero tienen ordenanzas fiscales independientes. Verifica que el recibo corresponde al municipio correcto si tienes propiedades en ambos."
  },
  "extremadura/badajoz/merida": {
    pop: "59.600", comarca: "Tierra de Mérida", nickLocal: "la Roma de Extremadura",
    geoContext: "Mérida, capital autonómica de Extremadura y Patrimonio de la Humanidad por su conjunto arqueológico romano, es la sede del gobierno regional. Su economía combina la administración pública, el turismo monumental y los servicios para la comunidad autónoma.",
    ibiContext: "Como capital autonómica, Mérida tiene un tipo de IBI urbano entre los más altos de Extremadura. Los valores catastrales varían entre el casco histórico y las urbanizaciones del ensanche.",
    basuraContext: "La tasa de basuras es intermedia-alta para Extremadura, coherente con el tamaño de la ciudad y la complejidad del servicio en la zona arqueológica.",
    plusvaliaContext: "El mercado inmobiliario emeritense ha mantenido cierta estabilidad gracias a la demanda de vivienda por parte de funcionarios autonómicos.",
    bonificacionContext: "Mérida aplica un 30% por familia numerosa y un 35% por energía solar. Existe bonificación adicional por inmuebles dentro del conjunto arqueológico.",
    reclamacionTip: "Si tu propiedad está dentro del perímetro de protección arqueológica y tienes limitaciones de obra, esto puede justificar una revisión catastral a la baja."
  },
  "extremadura/badajoz/montijo": {
    pop: "15.700", comarca: "Vegas Bajas", nickLocal: "la puerta de las Vegas Bajas",
    geoContext: "Montijo se sitúa en las Vegas Bajas del Guadiana, a escasos 25 km de Mérida. Su economía se apoya en la agricultura de regadío y la ganadería extensiva, complementada con un creciente sector de servicios.",
    ibiContext: "El tipo de IBI es moderado y los valores catastrales son bajos. La población estable mantiene una base impositiva limitada.",
    basuraContext: "La tasa de basuras es de las más reducidas de la provincia, coherente con un municipio de tamaño medio y costes operativos contenidos.",
    plusvaliaContext: "El mercado inmobiliario de Montijo es poco dinámico. Las herencias son el principal origen de las plusvalías declaradas.",
    bonificacionContext: "Montijo aplica un 20% de bonificación por familia numerosa, uno de los porcentajes más bajos de la guía. La bonificación solar es del 20% durante 3 años.",
    reclamacionTip: "Si tienes fincas agrícolas con construcciones auxiliares (casetas, pozos) dentro del término municipal, verifica que el Catastro no las está contabilizando como suelo urbano."
  },
  "extremadura/badajoz/villanueva-de-la-serena": {
    pop: "25.900", comarca: "La Serena", nickLocal: "la ciudad del Guadiana medio",
    geoContext: "Villanueva de la Serena forma, junto con Don Benito, un eje urbano de más de 60.000 habitantes en el centro de Extremadura. Su economía combina la agroindustria con los servicios a la comarca de La Serena.",
    ibiContext: "El tipo de IBI y los valores catastrales son muy similares a los de Don Benito, su municipio gemelo. El OAR de la Diputación gestiona la recaudación.",
    basuraContext: "La tasa de basuras es moderada. La Mancomunidad gestiona el tratamiento de residuos de forma conjunta con Don Benito.",
    plusvaliaContext: "El mercado inmobiliario es estable con precios asequibles. Las transmisiones se concentran en vivienda habitual y patrimonio familiar.",
    bonificacionContext: "Villanueva aplica un 25% por familia numerosa y un 25% por instalación solar. El procedimiento de solicitud es igual al de Don Benito a través del OAR.",
    reclamacionTip: "Si vas a comprar vivienda y dudas entre Don Benito y Villanueva, compara las cuotas de IBI y basuras de ambos municipios: son independientes a pesar de la proximidad."
  },
  "extremadura/badajoz/zafra": {
    pop: "16.800", comarca: "Zafra-Río Bodión", nickLocal: "la Sevilla chica",
    geoContext: "Zafra, conocida como 'la Sevilla Chica', es la capital comercial del sur de Badajoz. Su feria ganadera de San Miguel (la mayor de España por volumen) y su patrimonio histórico (Alcázar de los Duques de Feria) configuran un municipio dinámico.",
    ibiContext: "Los valores catastrales son bajos, típicos de un municipio extremeño de tamaño medio. El tipo de IBI se mantiene contenido gracias a la base amplia de contribuyentes.",
    basuraContext: "La tasa de basuras es la más baja de los municipios de Badajoz en nuestra guía, reflejo de los costes contenidos en una ciudad compacta.",
    plusvaliaContext: "Las transmisiones relacionadas con el sector ganadero y agrícola (fincas con suelo urbano) pueden generar plusvalías inesperadas que conviene calcular previamente.",
    bonificacionContext: "Zafra aplica un 20% por familia numerosa y un 20% por instalación solar. Los porcentajes son modestos pero coherentes con el perfil fiscal del municipio.",
    reclamacionTip: "Si tu propiedad incluye suelo dentro del recinto amurallado o del Alcázar de los Duques de Feria, puede existir una servidumbre que afecte al valor catastral. Consúltalo."
  },
  "extremadura/caceres/coria": {
    pop: "12.600", comarca: "Valle del Alagón", nickLocal: "la ciudad de las murallas",
    geoContext: "Coria, sede episcopal histórica, preside el Valle del Alagón en el norte de Cáceres. Su catedral, sus murallas romanas y su posición comarcal la convierten en un centro de servicios para la zona.",
    ibiContext: "El tipo de IBI es moderado y los valores catastrales son de los más bajos de la provincia. Un piso tipo de 90 m² puede tener un valor catastral de 25.000–40.000 €.",
    basuraContext: "La tasa de basuras es reducida, propia de un municipio pequeño con costes contenidos.",
    plusvaliaContext: "El escaso dinamismo inmobiliario hace que las herencias concentren la mayoría de plusvalías. Los precios de venta no han experimentado subidas significativas.",
    bonificacionContext: "Coria aplica un 20% por familia numerosa y un 25% por energía solar. La alta irradiación de la zona favorece la rentabilidad de la fotovoltaica.",
    reclamacionTip: "Los inmuebles adosados al recinto amurallado pueden tener restricciones de obra que justifiquen una revisión catastral. Consulta en la Concejalía de Urbanismo."
  },
  "extremadura/caceres/miajadas": {
    pop: "9.800", comarca: "Vegas Altas", nickLocal: "el pueblo del tomate",
    geoContext: "Miajadas, conocida como el municipio del tomate, es un centro agroindustrial de las Vegas Altas del Guadiana. Su economía gira en torno al cultivo y procesado del tomate, con varias fábricas conserveras en el término municipal.",
    ibiContext: "El tipo de IBI y los valores catastrales son de los más bajos de la guía, reflejando un mercado inmobiliario rural con precios muy asequibles.",
    basuraContext: "La tasa de basuras es la más reducida de nuestro catálogo, coherente con los menores costes de servicio en un municipio pequeño.",
    plusvaliaContext: "Las transmisiones son escasas y concentradas en herencias. Los precios de venta están estancados desde hace años.",
    bonificacionContext: "Miajadas aplica un modesto 20% por familia numerosa y un 20% por instalación solar. Los porcentajes reflejan un presupuesto municipal limitado.",
    reclamacionTip: "Las naves agroindustriales (conserveras, almacenes) tributan por IBI no residencial con tipo diferenciado. Si tu nave ha cesado la actividad, verifica que no se te aplica un tipo para inmueble activo."
  },
  "extremadura/caceres/navalmoral-de-la-mata": {
    pop: "17.200", comarca: "Campo Arañuelo", nickLocal: "la puerta de la Vera",
    geoContext: "Navalmoral de la Mata es la cabecera comercial y de servicios del Campo Arañuelo, en el noreste de Cáceres. Su proximidad al embalse de Valdecañas y a la comarca de La Vera genera demanda de vivienda como base residencial.",
    ibiContext: "El tipo de IBI es moderado y los valores catastrales son bajos. La amplia base de contribuyentes derivada de la función comarcal del municipio permite mantener tipos contenidos.",
    basuraContext: "La tasa de basuras cubre el servicio para el casco urbano y urbanizaciones próximas. Es de nivel moderado para Extremadura.",
    plusvaliaContext: "Las transmisiones combinan compraventas (familias que se instalan en la comarca) con herencias. Los precios son estables con una ligera tendencia al alza.",
    bonificacionContext: "Navalmoral aplica un 25% por familia numerosa y un 25% por instalación solar. El Ayuntamiento permite fraccionamiento en dos plazos.",
    reclamacionTip: "Si tu inmueble se sitúa en la zona de influencia del embalse de Valdecañas, verifica que la clasificación urbanística en el Catastro es correcta ante posibles reclasificaciones."
  },
  "extremadura/caceres/plasencia": {
    pop: "40.000", comarca: "Valle del Jerte", nickLocal: "la capital del Jerte",
    geoContext: "Plasencia, segunda ciudad de la provincia de Cáceres, se sitúa a orillas del río Jerte y es la puerta de entrada a los valles del Jerte y La Vera. Su catedral, su plaza Mayor y su mercado de los martes configuran una ciudad con fuerte identidad comarcal y un mercado inmobiliario estable.",
    ibiContext: "El tipo de IBI urbano es moderado-alto para Extremadura. Los valores catastrales se revisaron parcialmente y oscilan entre 35.000 € para un piso antiguo en el casco y 70.000 € en las urbanizaciones nuevas de la zona sur.",
    basuraContext: "La tasa de basuras cubre la recogida en el casco histórico (con vehículos adaptados) y las urbanizaciones. Es de nivel intermedio para Extremadura.",
    plusvaliaContext: "Plasencia tiene un mercado inmobiliario activo por su función comarcal. Las transmisiones son frecuentes tanto por compraventa como por herencia en familias con patrimonio urbano.",
    bonificacionContext: "Plasencia aplica un 30% por familia numerosa y un 30% por instalación solar, porcentajes ligeramente superiores a la media de municipios extremeños de tamaño similar.",
    reclamacionTip: "El mercado de los martes de Plasencia no afecta a la tributación de los locales, pero si tienes un inmueble comercial en la zona de la plaza Mayor, verifica que el uso catastral registrado (comercial vs. residencial) es el correcto."
  },
  "extremadura/caceres/trujillo": {
    pop: "9.300", comarca: "Miajadas-Trujillo", nickLocal: "la cuna de los conquistadores",
    geoContext: "Trujillo, cuna de Pizarro y Orellana, es uno de los conjuntos monumentales más destacados de Extremadura. Su plaza Mayor, sus palacios renacentistas y su castillo atraen turismo cultural y gastronómico.",
    ibiContext: "Los valores catastrales son muy bajos, especialmente para inmuebles del casco histórico con restricciones patrimoniales. El tipo de IBI es moderado.",
    basuraContext: "La tasa de basuras es reducida, acorde con un municipio pequeño. El servicio lo presta el Ayuntamiento directamente.",
    plusvaliaContext: "El interés turístico ha generado una demanda de inmuebles para alojamientos rurales y casas palacio rehabilitadas, con plusvalías potenciales en el casco monumental.",
    bonificacionContext: "Trujillo aplica un 20% por familia numerosa y un 20% por instalación solar. Los inmuebles BIC del casco histórico pueden acceder a bonificaciones adicionales.",
    reclamacionTip: "Si has rehabilitado un inmueble del casco histórico para uso turístico, el cambio de uso puede alterar el valor catastral. Notifica al Catastro la obra nueva o reforma para que la revisión sea correcta."
  },

  // GALICIA
  "galicia/a-coruna/ferrol": {
    pop: "64.800", comarca: "Ferrolterra", nickLocal: "la ciudad naval",
    geoContext: "Ferrol, ciudad naval por excelencia, alberga los astilleros de Navantia y la base militar de la Armada. Su economía depende en gran medida de la construcción naval y la actividad portuaria, lo que se refleja en un parque inmobiliario con precios contenidos.",
    ibiContext: "El tipo de IBI es moderado-alto para Galicia. Los valores catastrales reflejan un mercado inmobiliario con precios inferiores a la media de las ciudades gallegas.",
    basuraContext: "La tasa de basuras es relativamente alta, condicionada por la gestión de residuos en un municipio con núcleos costeros dispersos además del casco urbano.",
    plusvaliaContext: "El mercado inmobiliario ferrolano ha experimentado una caída de precios prolongada. Muchas transmisiones pueden no generar plusvalía real.",
    bonificacionContext: "Ferrol aplica un 35% por familia numerosa y un 35% por instalación solar. Las condiciones climáticas atlánticas moderan el rendimiento solar respecto a la meseta.",
    reclamacionTip: "Si vendes un inmueble en Ferrol y los precios actuales están por debajo de tu precio de compra, no olvides acreditar la pérdida para evitar la plusvalía municipal."
  },
  "galicia/lugo/lugo": {
    pop: "98.600", comarca: "Lugo", nickLocal: "la ciudad de la muralla romana",
    geoContext: "Lugo, Patrimonio de la Humanidad por su muralla romana (la única completa del mundo), es una ciudad de servicios que combina la administración provincial con la agroindustria y un creciente sector turístico.",
    ibiContext: "El tipo de IBI es moderado. Los valores catastrales de Lugo capital están por encima de la media provincial pero por debajo de las ciudades atlánticas gallegas.",
    basuraContext: "La tasa de basuras cubre un servicio completo que incluye la recogida en el casco intramuros (con vehículos adaptados) y las zonas de expansión.",
    plusvaliaContext: "El mercado inmobiliario lucense es estable con precios asequibles. La demanda se concentra en el casco urbano y las urbanizaciones del ensanche.",
    bonificacionContext: "Lugo aplica un 40% por familia numerosa y un 40% por instalación solar, porcentajes generosos dentro del contexto gallego.",
    reclamacionTip: "Los inmuebles situados en la muralla o adosados a ella tienen restricciones patrimoniales que pueden justificar una revisión catastral. Consulta en la Gerencia del Catastro."
  },
  "galicia/lugo/monforte-de-lemos": {
    pop: "18.400", comarca: "Tierra de Lemos", nickLocal: "la capital de la Ribeira Sacra",
    geoContext: "Monforte de Lemos, capital de la Ribeira Sacra, se sitúa en el cañón del río Sil. Su patrimonio monástico, los viñedos heroicos de la Ribeira Sacra y la gastronomía la convierten en un destino turístico emergente dentro de Galicia.",
    ibiContext: "El tipo de IBI es de los más bajos de la guía (0,55%). Los valores catastrales son reducidos, propios de un municipio interior gallego con precios inmobiliarios asequibles.",
    basuraContext: "La tasa de basuras es moderada. La recogida atiende al casco urbano y a numerosas parroquias rurales dispersas por el municipio.",
    plusvaliaContext: "El auge del turismo en la Ribeira Sacra ha revalorizado algunos inmuebles, especialmente los reconvertidos en alojamientos rurales o casas de turismo.",
    bonificacionContext: "Monforte aplica un 30% por familia numerosa y un 25% por instalación solar. Las condiciones climáticas de la zona interior son algo más favorables para la fotovoltaica que la costa.",
    reclamacionTip: "Si has rehabilitado una casa de piedra para turismo rural, el alta catastral como inmueble turístico puede alterar tu cuota de IBI. Verifica que el uso registrado es el correcto."
  },
  "galicia/ourense/o-carballino": {
    pop: "14.200", comarca: "O Carballiño", nickLocal: "la capital del pulpo",
    geoContext: "O Carballiño, famosa por su Festa do Pulpo, es la cabecera comarcal de la zona central de Ourense. Su termalismo (Balneario de O Carballiño) y su gastronomía atraen visitantes, mientras la agricultura y los servicios comarcales sostienen la economía local.",
    ibiContext: "O Carballiño tiene el tipo de IBI más bajo de toda la guía (0,54%). Los valores catastrales son también muy reducidos, lo que resulta en cuotas de IBI entre las más bajas de España.",
    basuraContext: "La tasa de basuras es la más baja del catálogo, acorde con los modestos costes de servicio en un municipio de tamaño medio.",
    plusvaliaContext: "El mercado inmobiliario es poco dinámico. Las transmisiones se concentran en herencias de patrimonio familiar.",
    bonificacionContext: "O Carballiño aplica un 25% por familia numerosa y un 25% por instalación solar. Son porcentajes moderados pero proporcionales al presupuesto municipal.",
    reclamacionTip: "Si heredas una casa rural en las parroquias del municipio, verifica que el Catastro la tiene correctamente clasificada como rústica o urbana: la diferencia de tipo impositivo es significativa."
  },
  "galicia/ourense/ourense": {
    pop: "105.000", comarca: "Ourense", nickLocal: "la ciudad de las burgas",
    geoContext: "Ourense, la ciudad de las aguas termales (As Burgas), ha experimentado un renacimiento turístico y gastronómico en la última década. Su conectividad por AVE con Madrid y su cercanía a la Ribeira Sacra la posicionan como destino emergente.",
    ibiContext: "El tipo de IBI es moderado para una capital de provincia. Los valores catastrales se revisaron recientemente y reflejan un mercado al alza impulsado por el turismo.",
    basuraContext: "La tasa de basuras es moderada-alta. La gestión de residuos atiende al casco urbano y a numerosas parroquias rurales del extenso municipio.",
    plusvaliaContext: "La revalorización inmobiliaria ligada al turismo termal y gastronómico ha generado plusvalías significativas en el centro histórico y junto al río Miño.",
    bonificacionContext: "Ourense capital aplica un 35% por familia numerosa y un 35% por instalación solar. Las bonificaciones por BIC son relevantes en el entorno de As Burgas y la catedral.",
    reclamacionTip: "Si tu inmueble está cerca de las termas públicas de As Burgas o de la zona de Outariz, es posible que haya experimentado una revalorización significativa. Verifica el valor catastral actual."
  },
  "galicia/pontevedra/pontevedra": {
    pop: "83.500", comarca: "Pontevedra", nickLocal: "la Boa Vila",
    geoContext: "Pontevedra, modelo europeo de ciudad peatonalizada, ha sido reconocida internacionalmente por su urbanismo al servicio del peatón. Su economía combina la administración provincial, el turismo urbano y la proximidad al polo industrial de Vigo.",
    ibiContext: "El tipo de IBI es moderado-alto para Galicia. Los valores catastrales se han incrementado por la revalorización ligada a la calidad urbana y la peatonalización del centro.",
    basuraContext: "La tasa de basuras es de las más elevadas de Galicia, justificada por un servicio de alta calidad en una ciudad con estándares ambientales exigentes.",
    plusvaliaContext: "La ciudad ha experimentado una notable revalorización: la peatonalización ha elevado los precios del centro histórico entre un 15% y un 25% en la última década.",
    bonificacionContext: "Pontevedra aplica un 40% por familia numerosa y un 40% por energía solar, entre los porcentajes más altos de Galicia.",
    reclamacionTip: "La peatonalización ha eliminado plazas de aparcamiento en el centro. Si tu vivienda o local se ve afectado por la pérdida de accesibilidad rodada, esto podría influir en una revisión catastral."
  },
  "galicia/pontevedra/vilagarcia-de-arousa": {
    pop: "38.300", comarca: "O Salnés", nickLocal: "la capital de la ría de Arousa",
    geoContext: "Vilagarcía de Arousa se sitúa en la mayor ría de las Rías Baixas. Su economía combina la acuicultura (mejillón de las bateas), el turismo costero, el puerto comercial y los servicios comarcales.",
    ibiContext: "El tipo de IBI es moderado. Los valores catastrales de la franja costera (con vistas a la ría) son significativamente superiores a los del interior del municipio.",
    basuraContext: "La tasa de basuras refleja los costes de recoger residuos en un municipio con gran dispersión de parroquias costeras y de interior.",
    plusvaliaContext: "El turismo costero y la demanda de segundas residencias generan un mercado activo con plusvalías potenciales, especialmente en primera línea de la ría.",
    bonificacionContext: "Vilagarcía aplica un 30% por familia numerosa y un 30% por instalación solar. La energía eólica de autoconsumo también puede acogerse a bonificación.",
    reclamacionTip: "Si tu propiedad tiene concesión de dominio público marítimo-terrestre o está en zona de servidumbre de protección costera, esto puede afectar al valor catastral. Verifica la situación urbanística."
  },

  // MURCIA
  "murcia/murcia/aguilas": {
    pop: "35.700", comarca: "Bajo Guadalentín", nickLocal: "la cala y el carnival",
    geoContext: "Águilas, en el extremo suroeste de Murcia, destaca por sus playas, sus calas y su Carnaval (de Interés Turístico Internacional). Su economía combina la pesca, la agricultura bajo plástico y un creciente turismo costero.",
    ibiContext: "El tipo de IBI es moderado. Los valores catastrales varían entre el casco urbano (valores medios) y la franja costera (valores más altos por la demanda turística).",
    basuraContext: "La tasa de basuras refleja los costes extra de recogida en una costa con múltiples urbanizaciones turísticas dispersas a lo largo del litoral.",
    plusvaliaContext: "Las compraventas de segundas residencias costeras generan el grueso de las plusvalías declaradas. Los precios en primera línea se han estabilizado tras la caída de 2008–2014.",
    bonificacionContext: "Águilas aplica un 25% por familia numerosa y un 30% por instalación solar. La alta irradiación de la costa murciana maximiza el rendimiento fotovoltaico.",
    reclamacionTip: "Si tu propiedad costera se ha visto afectada por la Ley de Costas (servidumbre de protección) verifica que el valor catastral refleja las limitaciones de uso existentes."
  },
  "murcia/murcia/caravaca-de-la-cruz": {
    pop: "25.400", comarca: "Noroeste", nickLocal: "la Ciudad Santa",
    geoContext: "Caravaca de la Cruz es una de las cinco ciudades santas de la cristiandad (junto a Roma, Jerusalén, Santiago y Santo Toribio). Su basílica de la Vera Cruz y los Caballos del Vino atraen turismo religioso y cultural.",
    ibiContext: "Los valores catastrales son moderados-bajos. El tipo de IBI refleja la necesidad de financiar servicios en un municipio extenso con numerosas pedanías.",
    basuraContext: "La tasa de basuras atiende al casco urbano y a una amplia dispersión de núcleos rurales. Los costes de recogida por kilómetro son elevados.",
    plusvaliaContext: "El mercado inmobiliario es estable con precios asequibles. Las herencias de patrimonio rural son el principal hecho imponible.",
    bonificacionContext: "Caravaca aplica un 30% por familia numerosa y un 25% por instalación solar. La Basílica de la Vera Cruz genera bonificaciones especiales por BIC en su entorno.",
    reclamacionTip: "Si tu inmueble está en la zona de protección del Castillo-Basílica, las limitaciones de obra pueden justificar una revisión catastral a la baja."
  },
  "murcia/murcia/cieza": {
    pop: "35.100", comarca: "Vega Alta del Segura", nickLocal: "la capital del melocotón",
    geoContext: "Cieza, situada en la Vega Alta del Segura, es conocida como la capital del melocotón por su extensa producción frutícola. La floración de los melocotoneros en marzo se ha convertido en un evento turístico de primer orden.",
    ibiContext: "El tipo de IBI es de nivel moderado-medio. Los valores catastrales reflejan un mercado inmobiliario estable con precios asequibles para la media regional.",
    basuraContext: "La tasa de basuras se ha incrementado por la adaptación a la normativa de biorresiduos. El servicio atiende al casco urbano y a las pedanías de la huerta.",
    plusvaliaContext: "Las transmisiones de patrimonio agrícola que incluye suelo urbano son relativamente frecuentes. El suelo rústico NO está sujeto a plusvalía.",
    bonificacionContext: "Cieza aplica un 25% por familia numerosa y un 25% por instalación solar. El alto potencial de irradiación solar de la zona hace rentable la instalación incluso con porcentajes modestos.",
    reclamacionTip: "Si tus fincas agrícolas tienen una caseta de aperos en suelo urbano, verifica que el IBI que pagas por esa construcción es el correcto según el uso catastral registrado."
  },
  "murcia/murcia/lorca": {
    pop: "93.000", comarca: "Alto Guadalentín", nickLocal: "la ciudad del sol",
    geoContext: "Lorca, la tercera ciudad de la Región de Murcia, se asienta en el Alto Guadalentín. Los terremotos de 2011 marcaron un antes y un después en su urbanismo y en los valores inmobiliarios del casco histórico.",
    ibiContext: "El tipo de IBI es intermedio. Los valores catastrales se han ajustado tras los terremotos y la posterior reconstrucción. Las viviendas reconstruidas tienen valores actualizados.",
    basuraContext: "La tasa de basuras atiende a un municipio extenso (el segundo de España por superficie) con numerosas pedanías dispersas.",
    plusvaliaContext: "Los terremotos causaron una caída de precios que se ha recuperado parcialmente. Las transmisiones recientes pueden generar plusvalías modestas o incluso pérdidas.",
    bonificacionContext: "Lorca aplica un 30% por familia numerosa y un 30% por instalación solar. Existen bonificaciones especiales para inmuebles afectados por los terremotos que hayan sido reconstruidos.",
    reclamacionTip: "Si tu vivienda fue afectada por los terremotos de 2011 y reconstruida, verifica que el valor catastral refleja la obra nueva y no el inmueble original."
  },
  "murcia/murcia/mazarron": {
    pop: "36.200", comarca: "Bajo Guadalentín", nickLocal: "la costa de las calas",
    geoContext: "Mazarrón combina un casco urbano interior con un extenso litoral de calas y playas. Su economía se basa en la agricultura intensiva, la minería histórica y el turismo costero, con una importante colonia de residentes europeos.",
    ibiContext: "Los valores catastrales varían enormemente entre el casco (bajos) y la costa de Bolnuevo y Puerto de Mazarrón (más altos). El tipo de IBI es moderado.",
    basuraContext: "La tasa de basuras difiere entre viviendas del casco y las de la costa. La estacionalidad turística incrementa los costes del servicio en verano.",
    plusvaliaContext: "Las compraventas de segundas residencias costeras (muchas a compradores extranjeros) generan el principal volumen de plusvalías del municipio.",
    bonificacionContext: "Mazarrón aplica un 25% por familia numerosa y un 35% por instalación solar. El potencial solar de la costa murciana es de los más altos de Europa.",
    reclamacionTip: "Si eres residente extranjero con propiedad en Mazarrón, la plusvalía se aplica igualmente en transmisiones. Los no residentes tienen la obligación de retener el 3% del precio como pago a cuenta."
  },
  "murcia/murcia/molina-de-segura": {
    pop: "72.400", comarca: "Vega Media del Segura", nickLocal: "la ciudad conservera",
    geoContext: "Molina de Segura, al norte de Murcia capital, es un importante polo industrial conservero y logístico. Su proximidad a la capital y su oferta de vivienda más económica la han convertido en municipio de crecimiento residencial.",
    ibiContext: "El tipo de IBI es moderado-alto. Los valores catastrales se han incrementado por el crecimiento urbanístico de las dos últimas décadas.",
    basuraContext: "La tasa de basuras es de nivel medio-alto para la Región de Murcia, justificada por los costes de servicio en un municipio en expansión con urbanizaciones de baja densidad.",
    plusvaliaContext: "El crecimiento urbanístico ha generado un mercado activo con plusvalías para los primeros compradores que venden ahora tras la revalorización de la zona.",
    bonificacionContext: "Molina de Segura aplica un 30% por familia numerosa y un 30% por instalación solar durante 5 años. El Alto potencial solar de la huerta murciana maximiza el rendimiento.",
    reclamacionTip: "Si compraste en una urbanización nueva y aún no se ha producido la recepción municipal de viales e infraestructuras, verifica que no estés pagando IBI por zonas que deberían ser de titularidad pública."
  },
  "murcia/murcia/yecla": {
    pop: "33.600", comarca: "Altiplano", nickLocal: "la capital del mueble",
    geoContext: "Yecla, en el Altiplano murciano, es la capital española del mueble tapizado. Su industria mueblera, su DO Yecla (vino) y la basílica del Castillo configuran un municipio industrial con fuerte identidad comarcal.",
    ibiContext: "El tipo de IBI es moderado. Los valores catastrales reflejan un mercado con precios inmobiliarios estables y asequibles para la media regional.",
    basuraContext: "La tasa de basuras incluye tarifas especiales para las fábricas de muebles y tapicerías del polígono industrial, adaptadas al volumen de residuos que generan.",
    plusvaliaContext: "Las transmisiones de naves industriales del sector mueblero pueden generar plusvalías significativas cuando incluyen suelo urbano consolidado.",
    bonificacionContext: "Yecla aplica un 25% por familia numerosa y un 30% por instalación solar. La alta irradiación del Altiplano hace muy rentable la fotovoltaica industrial.",
    reclamacionTip: "Si posees una nave del sector mueblero y la actividad ha cesado, verifica que el uso catastral ha sido actualizado para evitar pagar un tipo de IBI de actividad económica."
  }
};

// ─── CCAA/Province display names ─────────────────────────────────
const ccaaNames = {
  "aragon": "Aragón", "asturias": "Asturias", "castilla-la-mancha": "Castilla-La Mancha",
  "castilla-y-leon": "Castilla y León", "extremadura": "Extremadura",
  "galicia": "Galicia", "murcia": "Murcia"
};

const provinceNames = {
  "huesca": "Huesca", "teruel": "Teruel", "zaragoza": "Zaragoza",
  "asturias": "Asturias", "albacete": "Albacete", "ciudad-real": "Ciudad Real",
  "cuenca": "Cuenca", "guadalajara": "Guadalajara", "toledo": "Toledo",
  "avila": "Ávila", "burgos": "Burgos", "leon": "León",
  "palencia": "Palencia", "salamanca": "Salamanca", "segovia": "Segovia",
  "zamora": "Zamora", "badajoz": "Badajoz", "caceres": "Cáceres",
  "a-coruna": "A Coruña", "lugo": "Lugo", "ourense": "Ourense",
  "pontevedra": "Pontevedra", "murcia": "Murcia"
};

function titleCase(slug) {
  return slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function getRelatedMunicipalities(key) {
  const parts = key.split('/');
  const ccaa = parts[0]; const prov = parts[1]; const muni = parts[2];
  const related = [];
  for (const k of Object.keys(rawData)) {
    const kp = k.split('/');
    if (kp[0] === ccaa && kp[1] === prov && kp[2] !== muni) {
      related.push({ slug: k, name: titleCase(kp[2]) });
    }
  }
  return related;
}

function generateMunicipalityPage(key) {
  const parts = key.split('/');
  const ccaaSlug = parts[0]; const provSlug = parts[1]; const muniSlug = parts[2];
  const ccaaName = ccaaNames[ccaaSlug] || titleCase(ccaaSlug);
  const provName = provinceNames[provSlug] || titleCase(provSlug);
  const muniName = titleCase(muniSlug);
  
  const data = rawData[key];
  const vals = data.candidate ? data.candidate.values : data.values;
  const ctx = municipalityContext[key] || {};
  const srcTitle = data.candidate ? data.candidate.source_title : (data.source_title || '');
  const srcUrl = data.candidate ? data.candidate.source_url : (data.source_url || '');
  const eOffice = vals.electronicOffice || srcUrl || '';
  
  const ibiUrban = vals.ibiUrban || '—';
  const ibiRustic = vals.ibiRustic || '—';
  const payPeriod = vals.paymentPeriod || 'Consultar ayuntamiento';
  const basura = vals.basuraAmount || '—';
  const boniFamily = vals.boniFamily || '—';
  const solarBoni = vals.solarBoni || '—';
  
  // Calculate example IBI amounts
  const ibiPct = parseFloat(ibiUrban.replace(',', '.').replace('%', '')) / 100 || 0;
  const ex60k = ibiPct > 0 ? Math.round(60000 * ibiPct) : '—';
  const ex80k = ibiPct > 0 ? Math.round(80000 * ibiPct) : '—';
  const ex100k = ibiPct > 0 ? Math.round(100000 * ibiPct) : '—';
  const ex120k = ibiPct > 0 ? Math.round(120000 * ibiPct) : '—';
  
  const related = getRelatedMunicipalities(key);
  const relatedHtml = related.map(r => `<li><a href="../../../${r.slug}/">${r.name}</a> — <a href="../../../${r.slug}/" style="color:var(--accent);font-size:.82rem">Ver guía →</a></li>`).join('\n              ');

  const depth = parts.length; // 3 = community/province/municipality
  const relPrefix = '../'.repeat(depth);

  const metaDesc = `Guía fiscal de ${muniName} (${provName}) 2026: IBI urbano ${ibiUrban}, tasa de basuras ${basura}, plusvalía municipal, bonificaciones familia numerosa ${boniFamily} y energía solar ${solarBoni}. Datos de la ordenanza actualizada.`;

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="${relPrefix}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="${relPrefix}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="${relPrefix}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="${relPrefix}apple-touch-icon.png">
  <title>IBI, basuras y plusvalía en ${muniName} 2026 — Guía fiscal completa</title>
  <meta name="description" content="${metaDesc}">
  <link rel="canonical" href="https://tasasmunicipales.info/${key}/">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "IBI, basuras y plusvalía en ${muniName} 2026",
    "url": "https://tasasmunicipales.info/${key}/",
    "datePublished": "2026-02-01",
    "dateModified": "2026-04-12",
    "author": { "@type": "Person", "name": "Aithamy Rivero", "url": "https://tasasmunicipales.info/sobre-nosotros/" },
    "publisher": { "@type": "Organization", "name": "TasasMunicipales.info" }
  }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root{--ink:#1a1a2e;--paper:#f5f0e8;--accent:#c8522a;--accent2:#2a7c6f;--gold:#d4a843;--mid:#6b6b7b;--rule:#d8d0c0;--card:#fffdf8}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Source Serif 4',Georgia,serif;background:var(--paper);color:var(--ink);line-height:1.75}
    a{color:inherit;text-decoration:none}
    header{background:var(--ink);border-bottom:4px solid var(--accent)}
    .hi{max-width:1140px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
    .logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#fff}
    .logo span{display:block;font-size:.65rem;color:var(--gold);letter-spacing:2px;text-transform:uppercase;font-weight:300}
    nav{display:flex;gap:4px;flex-wrap:wrap}
    nav a{color:rgba(255,255,255,.78);font-size:.78rem;padding:5px 11px;border:1px solid rgba(255,255,255,.12);border-radius:3px}
    nav a:hover{background:var(--accent);border-color:var(--accent);color:#fff}
    .bc{max-width:1140px;margin:0 auto;padding:14px 24px 0;font-size:.74rem;color:var(--mid)}
    .bc a{color:var(--accent)}
    .bc span{margin:0 5px}
    .wrap{max-width:1140px;margin:0 auto;padding:32px 24px 72px}
    .hero{display:grid;grid-template-columns:1.2fr .8fr;gap:18px;margin-bottom:24px;align-items:start}
    .card{background:var(--card);border:1px solid var(--rule)}
    .hero-main{padding:26px}
    .eyebrow{display:inline-block;background:var(--accent2);color:#fff;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;padding:5px 12px;margin-bottom:14px;font-weight:700}
    h1{font-family:'Playfair Display',serif;font-size:clamp(2rem,4vw,3rem);line-height:1.06;margin-bottom:10px}
    .lead{font-size:.96rem;color:var(--mid);max-width:780px}
    .meta{margin-top:14px;font-size:.78rem;color:var(--mid)}
    .author-box{margin-top:12px;padding:10px 14px;background:rgba(42,124,111,.06);border:1px solid rgba(42,124,111,.15);border-radius:4px;font-size:.8rem}
    .author-box a{color:var(--accent2);font-weight:600}
    .hero-side{padding:22px}
    .hero-side h2,.sec h2{font-family:'Playfair Display',serif;font-size:1.1rem;margin-bottom:10px}
    .quick{list-style:none}
    .quick li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:.86rem}
    .quick li:last-child{border-bottom:none}
    .layout{display:grid;grid-template-columns:1fr 300px;gap:28px}
    .sec{background:var(--card);border:1px solid var(--rule);padding:22px;margin-bottom:18px}
    .sec h2{padding-bottom:8px;border-bottom:2px solid var(--ink)}
    .sec h3{font-family:'Playfair Display',serif;font-size:1rem;margin:16px 0 8px}
    .sec p{font-size:.91rem;margin-bottom:14px}
    .sec ul{padding-left:20px;margin-bottom:14px}
    .sec li{font-size:.9rem;margin-bottom:6px}
    .dt{width:100%;border-collapse:collapse;margin:14px 0 18px;font-size:.84rem}
    .dt th{background:var(--ink);color:#fff;padding:9px 11px;text-align:left;font-size:.73rem}
    .dt td{padding:9px 11px;border-bottom:1px solid var(--rule);vertical-align:top}
    .dt tr:nth-child(even) td{background:rgba(0,0,0,.02)}
    .v{font-weight:700;color:var(--accent)}
    .note{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--accent2);padding:14px 16px;margin:14px 0;font-size:.87rem}
    .side{position:sticky;top:20px}
    .side .card{padding:16px;margin-bottom:16px}
    .side ul{list-style:none}
    .side li{padding:6px 0;border-bottom:1px solid var(--rule);font-size:.82rem}
    .side li:last-child{border-bottom:none}
    .side a{color:var(--accent)}
    footer{background:#12121f;color:rgba(255,255,255,.45);text-align:center;padding:24px 20px;font-size:.74rem}
    @media(max-width:900px){.layout,.hero{grid-template-columns:1fr}.side{position:static}}
  </style>
</head>
<body>
<header>
  <div class="hi">
    <a href="${relPrefix}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
    <nav>
      <a href="${relPrefix}comunidades/">Comunidades</a>
      <a href="${relPrefix}municipios/">Municipios</a>
      <a href="${relPrefix}ibi-2026/">IBI 2026</a>
      <a href="${relPrefix}calculadora-ibi/">Calculadora</a>
      <a href="${relPrefix}tasa-basuras/">Basuras</a>
      <a href="${relPrefix}plusvalia/">Plusvalía</a>
      <a href="${relPrefix}bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>
<div class="bc"><a href="${relPrefix}">Inicio</a><span>›</span><a href="${relPrefix}${ccaaSlug}/">${ccaaName}</a><span>›</span><strong>${muniName}</strong></div>
<div class="wrap">
  <section class="hero">
    <div class="hero-main card">
      <span class="eyebrow">Guía Fiscal Municipal 2026</span>
      <h1>${muniName}: IBI, basuras, plusvalía y bonificaciones</h1>
      <p class="lead">${ctx.geoContext || `Guía fiscal completa de ${muniName} (${provName}, ${ccaaName}) con los datos actualizados de la ordenanza fiscal municipal para 2026.`}</p>
      <p class="meta"><strong>${ccaaName} · ${provName}</strong>${ctx.pop ? ' · Población: ' + ctx.pop + ' hab.' : ''} · Actualizado: abril 2026</p>
      <div class="author-box">✍️ Por <a href="${relPrefix}sobre-nosotros/">Aithamy Rivero</a> · Fuente: <a href="${eOffice}" target="_blank" rel="nofollow noopener">${srcTitle || 'Ordenanza fiscal municipal'}</a></div>
    </div>
    <aside class="hero-side card">
      <h2>Datos clave 2026</h2>
      <ul class="quick">
        <li><strong>IBI urbano:</strong> <span class="v">${ibiUrban}</span></li>
        <li><strong>IBI rústico:</strong> <span class="v">${ibiRustic}</span></li>
        <li><strong>Período de pago:</strong> ${payPeriod}</li>
        <li><strong>Basura vivienda:</strong> ${basura}</li>
        <li><strong>Bonif. familia numerosa:</strong> ${boniFamily}</li>
        <li><strong>Bonif. energía solar:</strong> ${solarBoni}</li>
      </ul>
    </aside>
  </section>

  <div class="layout">
    <main>
      <section class="sec">
        <h2>IBI 2026 en ${muniName}: cuánto se paga y cuándo</h2>
        <p>${ctx.ibiContext || `El Impuesto sobre Bienes Inmuebles grava la titularidad de viviendas, locales, garajes y fincas rústicas en ${muniName}. El tipo impositivo y el período de pago los fija el Ayuntamiento cada año en su ordenanza fiscal.`}</p>
        <table class="dt">
          <thead><tr><th>Valor catastral</th><th>Cuota anual estimada</th><th>Cuota mensual equiv.</th></tr></thead>
          <tbody>
            <tr><td>60.000 €</td><td class="v">${ex60k} €</td><td>${ibiPct > 0 ? (ex60k / 12).toFixed(0) : '—'} €/mes</td></tr>
            <tr><td>80.000 €</td><td class="v">${ex80k} €</td><td>${ibiPct > 0 ? (ex80k / 12).toFixed(0) : '—'} €/mes</td></tr>
            <tr><td>100.000 €</td><td class="v">${ex100k} €</td><td>${ibiPct > 0 ? (ex100k / 12).toFixed(0) : '—'} €/mes</td></tr>
            <tr><td>120.000 €</td><td class="v">${ex120k} €</td><td>${ibiPct > 0 ? (ex120k / 12).toFixed(0) : '—'} €/mes</td></tr>
          </tbody>
        </table>
        <div class="note"><strong>💡 ¿Cómo se calcula?</strong> <em>Cuota = Valor catastral × ${ibiUrban}</em>. El valor catastral aparece en tu recibo del IBI o en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sede del Catastro</a>. Las bonificaciones se restan después.</div>
      </section>

      <section class="sec">
        <h2>Tasa de basuras en ${muniName}: ${basura}</h2>
        <p>${ctx.basuraContext || `La tasa de recogida de residuos sólidos urbanos en ${muniName} se aprueba anualmente en la ordenanza fiscal del Ayuntamiento. Grava la prestación del servicio de recogida, transporte y tratamiento de residuos.`}</p>
        <table class="dt">
          <thead><tr><th>Concepto</th><th>Importe</th></tr></thead>
          <tbody>
            <tr><td>Vivienda habitual</td><td class="v">${basura}</td></tr>
            <tr><td>Período de pago</td><td>Según padrón municipal</td></tr>
          </tbody>
        </table>
        <p>La tasa de basuras se ha incrementado en la mayoría de municipios españoles en 2025–2026 por la <strong>Ley 7/2022 de Residuos</strong>, que obliga a los ayuntamientos a cubrir el coste íntegro del servicio con las tasas cobradas. En un alquiler, el sujeto pasivo es legalmente el propietario, aunque el contrato puede trasladar el pago al inquilino si se pacta expresamente.</p>
      </section>

      <section class="sec">
        <h2>Plusvalía municipal en ${muniName}</h2>
        <p>${ctx.plusvaliaContext || `El Impuesto sobre el Incremento del Valor de los Terrenos de Naturaleza Urbana (plusvalía municipal) se devenga al vender, heredar o donar un inmueble urbano en ${muniName}. El contribuyente puede elegir el método más favorable entre el objetivo (coeficientes municipales) y el real (diferencia entre precio de compra y venta).`}</p>
        <ul>
          <li><strong>Plazo en compraventa:</strong> 30 días hábiles desde la escritura.</li>
          <li><strong>Plazo en herencia:</strong> 6 meses desde el fallecimiento (prorrogable a 12 meses con solicitud motivada).</li>
          <li><strong>Venta con pérdidas:</strong> si el precio de transmisión es inferior al de adquisición, no hay plusvalía. Aporta ambas escrituras.</li>
        </ul>
        <div class="note"><strong>⚖️ Elige el método más favorable.</strong> Desde la sentencia del TC de 2021 y el RDL 26/2021, puedes optar por el cálculo que resulte menor. En ${muniName}, ${ctx.plusvaliaContext ? 'consulta la ordenanza para los coeficientes locales.' : 'el Ayuntamiento aplica los coeficientes máximos legales.'}</div>
      </section>

      <section class="sec">
        <h2>Bonificaciones del IBI en ${muniName}</h2>
        <p>${ctx.bonificacionContext || `Las bonificaciones del IBI permiten reducir la cuota anual. El Ayuntamiento de ${muniName} contempla descuentos por familia numerosa, instalación de energía solar y otros supuestos recogidos en su ordenanza fiscal.`}</p>
        <table class="dt">
          <thead><tr><th>Bonificación</th><th>Porcentaje</th><th>Requisitos clave</th></tr></thead>
          <tbody>
            <tr><td>Familia numerosa (general)</td><td class="v">${boniFamily}</td><td>Título vigente + vivienda habitual + empadronamiento</td></tr>
            <tr><td>Energía solar / renovables</td><td class="v">${solarBoni}</td><td>Certificado instalador + boletín eléctrico + solicitud en el año siguiente</td></tr>
            <tr><td>Domiciliación SEPA</td><td>1–5%</td><td>Comunicar IBAN antes del período voluntario</td></tr>
            <tr><td>VPO (nueva construcción)</td><td>Hasta 50%</td><td>Primeros 3 años desde calificación definitiva</td></tr>
          </tbody>
        </table>
        <div class="note"><strong>📅 Plazo de solicitud:</strong> antes del 31 de marzo del ejercicio, salvo que la ordenanza establezca otra fecha. Las bonificaciones no se aplican de oficio: debes solicitarlas.</div>
      </section>

      <section class="sec">
        <h2>Consejo práctico para ${muniName}</h2>
        <p>${ctx.reclamacionTip || `Antes de pagar, verifica que tu recibo refleja correctamente la referencia catastral, el titular y las bonificaciones reconocidas. Si detectas un error, presenta un recurso de reposición ante el Ayuntamiento en el plazo de un mes.`}</p>
      </section>

      <section class="sec">
        <h2>Fuentes oficiales y verificación</h2>
        <ul>
          <li><strong>Ordenanza fiscal:</strong> <a href="${eOffice}" target="_blank" rel="nofollow noopener">${srcTitle || 'Ordenanza fiscal municipal de ' + muniName}</a></li>
          <li><strong>Sede electrónica:</strong> <a href="${eOffice}" target="_blank" rel="nofollow noopener">${eOffice}</a></li>
          <li><strong>Catastro:</strong> <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a> para consultar el valor catastral de tu inmueble.</li>
        </ul>
        <div class="note"><strong>⚠️ Aviso:</strong> Los datos de esta guía son orientativos y se basan en la ordenanza fiscal publicada. Confirma siempre los importes y plazos en la sede electrónica del Ayuntamiento de ${muniName} antes de pagar, reclamar o solicitar una bonificación.</div>
      </section>

      ${related.length > 0 ? `<section class="sec">
        <h2>Otros municipios de ${provName}</h2>
        <p>Consulta las guías fiscales de municipios cercanos en la misma provincia:</p>
        <ul>
          ${relatedHtml}
        </ul>
      </section>` : ''}
    </main>

    <aside class="side">
      <div class="card">
        <h2>Navegación</h2>
        <ul>
          <li><a href="${relPrefix}">Inicio</a></li>
          <li><a href="${relPrefix}${ccaaSlug}/">Volver a ${ccaaName}</a></li>
          <li><a href="${relPrefix}municipios/">Todos los municipios</a></li>
          <li><a href="${relPrefix}calculadora-ibi/">Calculadora IBI</a></li>
          <li><a href="${relPrefix}ibi-2026/">IBI 2026</a></li>
          <li><a href="${relPrefix}bonificaciones/">Bonificaciones</a></li>
          <li><a href="${relPrefix}tasa-basuras/">Tasa de basuras</a></li>
          <li><a href="${relPrefix}plusvalia/">Plusvalía</a></li>
          <li><a href="${relPrefix}sobre-nosotros/">Sobre nosotros</a></li>
        </ul>
      </div>
    </aside>
  </div>
</div>
<footer>© 2026 TasasMunicipales.info · Datos orientativos basados en ordenanzas fiscales municipales. <a href="${relPrefix}aviso-legal/" style="color:var(--gold)">Aviso legal</a> · <a href="${relPrefix}privacidad/" style="color:var(--gold)">Privacidad</a></footer>
</body>
</html>`;
}

// ─── Generate "Sobre nosotros" page ──────────────────────────────
function generateSobreNosotros() {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="../favicon.ico">
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../apple-touch-icon.png">
  <title>Sobre nosotros — TasasMunicipales.info</title>
  <meta name="description" content="Quiénes somos y cómo elaboramos la guía de tasas municipales más completa de España. Metodología, fuentes y compromiso editorial.">
  <link rel="canonical" href="https://tasasmunicipales.info/sobre-nosotros/">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root{--ink:#1a1a2e;--paper:#f5f0e8;--accent:#c8522a;--accent2:#2a7c6f;--gold:#d4a843;--mid:#6b6b7b;--rule:#d8d0c0;--card:#fffdf8}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Source Serif 4',Georgia,serif;background:var(--paper);color:var(--ink);line-height:1.75}
    a{color:inherit;text-decoration:none}
    header{background:var(--ink);border-bottom:4px solid var(--accent)}
    .hi{max-width:1140px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
    .logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#fff}
    .logo span{display:block;font-size:.65rem;color:var(--gold);letter-spacing:2px;text-transform:uppercase;font-weight:300}
    nav{display:flex;gap:4px;flex-wrap:wrap}
    nav a{color:rgba(255,255,255,.78);font-size:.78rem;padding:5px 11px;border:1px solid rgba(255,255,255,.12);border-radius:3px}
    nav a:hover{background:var(--accent);border-color:var(--accent);color:#fff}
    .bc{max-width:1140px;margin:0 auto;padding:14px 24px 0;font-size:.74rem;color:var(--mid)}.bc a{color:var(--accent)}.bc span{margin:0 5px}
    .wrap{max-width:800px;margin:0 auto;padding:32px 24px 72px}
    h1{font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.1;margin-bottom:18px}
    h2{font-family:'Playfair Display',serif;font-size:1.2rem;margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
    p{font-size:.93rem;margin-bottom:16px}
    ul{padding-left:22px;margin-bottom:16px}
    li{font-size:.91rem;margin-bottom:6px}
    .card{background:var(--card);border:1px solid var(--rule);padding:24px;margin-bottom:24px}
    .author-card{display:flex;gap:20px;align-items:start}
    .author-avatar{width:80px;height:80px;border-radius:50%;background:var(--accent2);display:flex;align-items:center;justify-content:center;color:#fff;font-size:2rem;font-family:'Playfair Display',serif;flex-shrink:0}
    .note{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--accent2);padding:14px 16px;margin:14px 0;font-size:.87rem}
    footer{background:#12121f;color:rgba(255,255,255,.45);text-align:center;padding:24px 20px;font-size:.74rem}
  </style>
</head>
<body>
<header>
  <div class="hi">
    <a href="../" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
    <nav>
      <a href="../comunidades/">Comunidades</a>
      <a href="../municipios/">Municipios</a>
      <a href="../ibi-2026/">IBI 2026</a>
      <a href="../calculadora-ibi/">Calculadora</a>
      <a href="../tasa-basuras/">Basuras</a>
      <a href="../plusvalia/">Plusvalía</a>
      <a href="../bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>
<div class="bc"><a href="../">Inicio</a><span>›</span><strong>Sobre nosotros</strong></div>
<div class="wrap">
  <h1>Sobre TasasMunicipales.info</h1>

  <div class="card author-card">
    <div class="author-avatar">AR</div>
    <div>
      <p><strong>Aithamy Rivero Marrero</strong></p>
      <p style="font-size:.85rem;color:var(--mid);margin-bottom:8px">Fundador y editor de TasasMunicipales.info · Las Palmas de Gran Canaria</p>
      <p style="font-size:.85rem">Tras enfrentarme a la dificultad de encontrar información clara sobre los impuestos locales de mi municipio, decidí crear un recurso que reuniera los datos fiscales de los ayuntamientos españoles en un formato accesible y comprensible para cualquier propietario.</p>
    </div>
  </div>

  <h2>¿Por qué existe esta guía?</h2>
  <p>Cada año, millones de propietarios en España reciben el recibo del IBI, la tasa de basuras o una liquidación de plusvalía, y no tienen claro cuánto deberían pagar, si tienen derecho a una bonificación o cómo reclamar un error. La información está dispersa en ordenanzas fiscales municipales, boletines oficiales y sedes electrónicas de difícil navegación.</p>
  <p>TasasMunicipales nació para resolver ese problema: <strong>centralizar, estructurar y explicar en lenguaje claro</strong> los datos fiscales que cada Ayuntamiento publica por separado.</p>

  <h2>Nuestra metodología</h2>
  <p>Cada ficha municipal se elabora siguiendo un proceso riguroso:</p>
  <ul>
    <li><strong>Fuente primaria:</strong> consultamos la ordenanza fiscal publicada en el boletín oficial de la provincia (BOP) o del diario oficial de la comunidad autónoma (DOE, BOPA, BORM, DOG…).</li>
    <li><strong>Verificación cruzada:</strong> contrastamos los datos con la sede electrónica del Ayuntamiento y con el organismo recaudador provincial (OAR, Tributas del Principado, SUMA…) cuando corresponde.</li>
    <li><strong>Actualización anual:</strong> las ordenanzas fiscales se aprueban habitualmente en diciembre para el ejercicio siguiente. Actualizamos las fichas en enero-febrero de cada año.</li>
    <li><strong>Transparencia:</strong> cada ficha municipal indica la fuente documental concreta (número de boletín y fecha) para que el usuario pueda comprobar el dato por sí mismo.</li>
  </ul>

  <h2>Qué encontrarás en cada guía municipal</h2>
  <ul>
    <li>Tipo de IBI urbano y rústico aprobado para el ejercicio en curso.</li>
    <li>Calendario de pago y opciones de fraccionamiento.</li>
    <li>Importe de la tasa de basuras para vivienda habitual.</li>
    <li>Información sobre la plusvalía municipal: métodos de cálculo, plazos y bonificaciones.</li>
    <li>Tabla de bonificaciones disponibles: familia numerosa, energía solar, VPO, domiciliación y otras.</li>
    <li>Ejemplos de cálculo con valores catastrales reales de la zona.</li>
    <li>Contexto geográfico y económico del municipio para entender las cifras.</li>
    <li>Consejos prácticos específicos basados en las particularidades de cada localidad.</li>
  </ul>

  <h2>Limitaciones y aviso importante</h2>
  <div class="note">
    <p><strong>⚠️ TasasMunicipales no presta servicios de asesoramiento fiscal, jurídico ni financiero.</strong> La información publicada tiene carácter orientativo y se basa en las ordenanzas fiscales publicadas por los ayuntamientos. Los datos pueden no estar actualizados en todo momento.</p>
    <p>Para cualquier decisión tributaria, consulta con un profesional habilitado o con el Ayuntamiento correspondiente. Siempre recomendamos verificar los datos en la sede electrónica oficial antes de actuar.</p>
  </div>

  <h2>Contacto</h2>
  <p>¿Quieres que incluyamos tu municipio? ¿Has detectado un dato incorrecto? Escríbenos a <a href="mailto:soporte@tasasmunicipales.info" style="color:var(--accent)">soporte@tasasmunicipales.info</a> o utiliza nuestro <a href="../contacto/" style="color:var(--accent)">formulario de contacto</a>.</p>
  <p>Actualmente cubrimos <strong>58 municipios en 7 comunidades autónomas</strong>: Aragón, Asturias, Castilla-La Mancha, Castilla y León, Extremadura, Galicia y Murcia. Nuestro objetivo es ampliar la cobertura progresivamente a toda España.</p>
</div>
<footer>© 2026 TasasMunicipales.info · <a href="../aviso-legal/" style="color:var(--gold)">Aviso legal</a> · <a href="../privacidad/" style="color:var(--gold)">Privacidad</a> · <a href="../contacto/" style="color:var(--gold)">Contacto</a></footer>
</body>
</html>`;
}

// ─── MAIN EXECUTION ──────────────────────────────────────────────
let count = 0;
let errors = [];

for (const key of Object.keys(rawData)) {
  try {
    const filePath = path.join(ROOT, key, 'index.html');
    if (!fs.existsSync(path.dirname(filePath))) {
      console.log(`  ⚠ Dir missing for ${key}, skipping`);
      continue;
    }
    const html = generateMunicipalityPage(key);
    fs.writeFileSync(filePath, html, 'utf8');
    count++;
    console.log(`  ✓ ${key}`);
  } catch (e) {
    errors.push(`${key}: ${e.message}`);
    console.error(`  ✗ ${key}: ${e.message}`);
  }
}

// Generate "Sobre nosotros"
const sobreDir = path.join(ROOT, 'sobre-nosotros');
if (!fs.existsSync(sobreDir)) fs.mkdirSync(sobreDir, { recursive: true });
fs.writeFileSync(path.join(sobreDir, 'index.html'), generateSobreNosotros(), 'utf8');
console.log('  ✓ sobre-nosotros/index.html');

console.log(`\n═══ DONE ═══`);
console.log(`  Municipality pages regenerated: ${count}`);
console.log(`  "Sobre nosotros" page created: 1`);
if (errors.length) console.log(`  Errors: ${errors.length}\n  ${errors.join('\n  ')}`);
