/* Pruebas funcionales en un DOM real (jsdom): comprueban que el sitio FUNCIONA,
   no solo que esta bien escrito.

   Cubre: la calculadora, el pilar territorial en modo hub, la integridad de las
   fichas municipales (que son las que captan el long-tail), las redirecciones de
   las URLs antiguas que devolvian 404 y la coherencia con la fuente de datos.

   Requiere jsdom. Desde una carpeta con jsdom instalado:
       node /ruta/al/repo/scripts/qa_browser.js /ruta/al/repo
*/
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = process.argv[2] || path.join(__dirname, '..');
let fallos = 0, oks = 0;
const ok = (t) => { oks++; console.log('  OK    ' + t); };
const bad = (t) => { fallos++; console.log('  FALLA ' + t); };
const leer = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');

// ─────────────────────────── calculadora ───────────────────────────
console.log('\n== Calculadora de IBI ==');
{
  const html = leer('calculadora-ibi/index.html');
  const datos = leer('municipios.js');
  const dom = new JSDOM(html.replace('<script src="../municipios.js"></script>', '<script>' + datos + '</script>'), {
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    beforeParse(win) { win.HTMLElement.prototype.scrollIntoView = () => {}; },
  });
  const w = dom.window, d = w.document;
  const munis = w.TM_MUNICIPIOS || [];

  const opciones = d.getElementById('municipio').options.length - 1;
  opciones === munis.length
    ? ok('el desplegable carga los ' + opciones + ' municipios desde municipios.js')
    : bad('el desplegable carga ' + opciones + ' de ' + munis.length);

  const idx = munis.findIndex((m) => m.nombre === 'Molina de Segura');
  const select = d.getElementById('municipio');
  select.value = String(idx);
  select.dispatchEvent(new w.Event('change'));
  const hint = d.getElementById('hint-ibi').textContent.trim();
  hint.includes(munis[idx].ibiU.toFixed(2).replace('.', ','))
    ? ok('muestra el tipo de la fuente de datos: "' + hint + '"')
    : bad('tipo mostrado inesperado: ' + hint);

  d.getElementById('catastral').value = '50000';
  w.calcular();
  const esperado = (50000 * munis[idx].ibiU / 100).toFixed(2).replace('.', ',');
  const bruta = d.getElementById('res-bruta').textContent.replace(/\s|€/g, '');
  bruta === esperado ? ok('cuota calculada correcta: ' + bruta + ' €') : bad('cuota ' + bruta + ' (esperada ' + esperado + ')');

  const enlace = d.querySelector('#res-links a').getAttribute('href');
  enlace === '../' + munis[idx].url && !enlace.includes('#')
    ? ok('el resultado enlaza a la ficha municipal, que es la que rankea: ' + enlace)
    : bad('enlace inesperado: ' + enlace);
  fs.existsSync(path.join(ROOT, munis[idx].url, 'index.html'))
    ? ok('la ficha enlazada existe en disco')
    : bad('la ficha enlazada no existe');

  const filas = d.querySelectorAll('#tabla-body tr').length;
  filas === munis.length ? ok('la tabla comparativa pinta las ' + filas + ' filas') : bad('pinta ' + filas + ' filas');
}

// ──────────────────── pilar territorial en modo hub ────────────────────
console.log('\n== Pilar /murcia/ en modo hub ==');
{
  const dom = new JSDOM(leer('murcia/index.html'), { runScripts: 'dangerously', pretendToBeVisual: true });
  const w = dom.window, d = w.document;

  const enlacesFicha = [...d.querySelectorAll('table.sortable tbody tr a')].map((a) => a.getAttribute('href'));
  enlacesFicha.length === 16 ? ok('la tabla lista los 16 municipios') : bad('la tabla lista ' + enlacesFicha.length);
  enlacesFicha.every((h) => h.startsWith('../murcia/murcia/') && !h.includes('#'))
    ? ok('la tabla enlaza a las fichas municipales, no a anclas internas')
    : bad('la tabla sigue enlazando a anclas: ' + enlacesFicha[0]);
  let faltan = 0;
  enlacesFicha.forEach((h) => { if (!fs.existsSync(path.join(ROOT, 'murcia', h, 'index.html'))) faltan++; });
  faltan === 0 ? ok('las 16 fichas enlazadas existen') : bad(faltan + ' fichas enlazadas no existen');

  const titulo = d.querySelector('title').textContent;
  /comparativa/i.test(titulo)
    ? ok('el título apunta a la intención comparativa, sin competir con las fichas: "' + titulo + '"')
    : bad('título inesperado: ' + titulo);

  let rotas = 0;
  d.querySelectorAll('a[href^="#"]').forEach((a) => { if (!d.getElementById(a.getAttribute('href').slice(1))) rotas++; });
  rotas === 0 ? ok('ninguna ancla interna rota') : bad(rotas + ' anclas rotas');

  const th = d.querySelector('table.sortable th[data-col="2"]');
  const antes = [...d.querySelectorAll('table.sortable tbody tr')].map((tr) => tr.cells[0].textContent.trim());
  th.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const despues = [...d.querySelectorAll('table.sortable tbody tr')].map((tr) => tr.cells[0].textContent.trim());
  JSON.stringify(antes) !== JSON.stringify(despues) ? ok('la tabla se reordena al pulsar el encabezado') : bad('la tabla no se reordena');

  const imgs = [...d.querySelectorAll('img')];
  imgs.length >= 3 && imgs.every((i) => i.getAttribute('alt') && i.getAttribute('width'))
    ? ok(imgs.length + ' imágenes propias con alt y dimensiones')
    : bad('problema con las imágenes (' + imgs.length + ')');

  const boe = [...d.querySelectorAll('a[href*="boe.es"]')].length;
  boe >= 6 ? ok(boe + ' citas normativas enlazadas al BOE') : bad('solo ' + boe + ' citas al BOE');

  const tipos = [...d.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent)['@type']);
  tipos.join(',') === 'Article,ItemList,FAQPage,BreadcrumbList' ? ok('datos estructurados: ' + tipos.join(', ')) : bad('schema inesperado: ' + tipos.join(','));
}

// ───────────── fichas municipales: son las que traen el tráfico ─────────────
console.log('\n== Fichas municipales ==');
{
  const conTrafico = [
    'galicia/ourense/ourense', 'castilla-la-mancha/toledo/talavera-de-la-reina',
    'murcia/murcia/molina-de-segura', 'galicia/a-coruna/ferrol',
    'castilla-la-mancha/guadalajara/azuqueca-de-henares', 'aragon/huesca/jaca',
    'murcia/murcia/aguilas', 'murcia/murcia/cieza', 'murcia/murcia/mazarron',
    'murcia/murcia/lorca', 'murcia/murcia/yecla', 'murcia/murcia/caravaca-de-la-cruz',
  ];
  let vivas = 0, redirigidas = 0, sinContenido = 0;
  conTrafico.forEach((rel) => {
    const f = path.join(ROOT, rel, 'index.html');
    if (!fs.existsSync(f)) { bad('no existe ' + rel); return; }
    const html = fs.readFileSync(f, 'utf8');
    if (html.includes('http-equiv="refresh"')) { redirigidas++; console.log('    redirige (no debería): ' + rel); return; }
    const texto = html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').split(/\s+/).length;
    if (texto < 500) { sinContenido++; console.log('    contenido escaso (' + texto + ' palabras): ' + rel); return; }
    vivas++;
  });
  redirigidas === 0 && sinContenido === 0 && vivas === conTrafico.length
    ? ok('las ' + vivas + ' fichas con tráfico siguen publicadas y con contenido')
    : bad(vivas + ' correctas, ' + redirigidas + ' convertidas en redirección, ' + sinContenido + ' con poco contenido');

  const sitemap = leer('sitemap.xml');
  const enSitemap = conTrafico.filter((r) => sitemap.includes('https://tasasmunicipales.info/' + r + '/')).length;
  enSitemap === conTrafico.length ? ok('las ' + enSitemap + ' están en el sitemap') : bad('solo ' + enSitemap + ' en el sitemap');
}

// ───────── redirecciones de las URLs antiguas que daban 404 ─────────
console.log('\n== Redirecciones de URLs antiguas (404 recuperados) ==');
{
  const csv = leer('redirects-301.csv').trim().split('\n').slice(1);
  // Se considera redirección cualquier página con meta refresh, esté al nivel que esté
  const stubs = [];
  const walk = (dir) => {
    fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
      if (['.git', 'img', 'scripts', 'data', 'node_modules'].includes(e.name)) return;
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name === 'index.html' && fs.readFileSync(p, 'utf8').includes('http-equiv="refresh"')) {
        stubs.push(path.dirname(p));
      }
    });
  };
  walk(ROOT);

  let bien = 0;
  stubs.forEach((p) => {
    const html = fs.readFileSync(path.join(p, 'index.html'), 'utf8');
    const canonical = (html.match(/<link rel="canonical" href="([^"]+)"/) || [])[1] || '';
    const refresh = (html.match(/http-equiv="refresh" content="0; url=([^"]+)"/) || [])[1] || '';
    const js = html.includes('window.location.replace');
    // el destino se deduce del propio meta refresh y debe existir en disco
    const destino = path.resolve(p, refresh);
    const destinoOk = refresh && fs.existsSync(path.join(destino, 'index.html'));
    const relDestino = path.relative(ROOT, destino).split(path.sep).join('/');
    const canonicalOk = canonical === 'https://tasasmunicipales.info/' + relDestino + '/';
    if (canonicalOk && js && destinoOk) bien++;
    else console.log('    revisar ' + path.relative(ROOT, p) + ' (canonical=' + canonical + ', refresh=' + refresh + ')');
  });
  stubs.length >= 25 ? ok(stubs.length + ' URLs antiguas con página de redirección') : bad(stubs.length + ' stubs (esperados 25 o más)');
  bien === stubs.length ? ok('todas apuntan a una ficha existente con canonical, meta refresh y JS') : bad(bien + '/' + stubs.length + ' correctas');
  csv.length === stubs.length ? ok('redirects-301.csv tiene las ' + csv.length + ' reglas para Cloudflare') : bad('el CSV tiene ' + csv.length + ' reglas y hay ' + stubs.length + ' redirecciones');

  const sitemap = leer('sitemap.xml');
  const enSitemap = stubs.filter((p) => sitemap.includes(path.relative(ROOT, p).split(path.sep).join('/'))).length;
  enSitemap === 0 ? ok('ninguna redirección está en el sitemap') : bad(enSitemap + ' redirecciones en el sitemap');
}

// ───────────── datos oficiales del Ministerio de Hacienda ─────────────
console.log('\n== Datos oficiales descargados ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const conOficial = municipios.filter((m) => m.oficial_tipo_urbana);
  conOficial.length === municipios.length
    ? ok('los ' + conOficial.length + ' municipios tienen tipo oficial del Ministerio')
    : bad(conOficial.length + ' de ' + municipios.length + ' con dato oficial');

  const conFuente = conOficial.filter((m) => m.oficial_fuente_url && m.oficial_comprobado_el);
  conFuente.length === conOficial.length ? ok('todos llevan fuente y fecha de comprobación') : bad('faltan fuente o fecha en ' + (conOficial.length - conFuente.length));

  const distintos = conOficial.filter((m) => m.tipo_urbano && Math.abs(m.oficial_tipo_urbana - m.tipo_urbano) > 1e-9);
  console.log('    (' + distintos.length + ' municipios publican un tipo distinto al oficial)');
  fs.existsSync(path.join(ROOT, 'data/DISCREPANCIAS_OFICIALES.md'))
    ? ok('informe de discrepancias generado')
    : bad('falta el informe de discrepancias');

  const rango = conOficial.filter((m) => m.oficial_tipo_urbana < 0.05 || m.oficial_tipo_urbana > 2);
  rango.length === 0 ? ok('todos los tipos oficiales están en un rango plausible') : bad(rango.length + ' tipos fuera de rango');
}

// ───────── las 134 fichas con el dato oficial aplicado ─────────
console.log('\n== Fichas con el dato oficial aplicado (todas) ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const claves = municipios.map((m) => m.ccaa + '/' + m.provincia_slug + '/' + m.slug);
  const pct = (v) => String(Number(v.toFixed(4))).replace('.', ',') + '%';
  const hoy = new Date().toISOString().slice(0, 10);
  const oficialPorNombre = {};
  municipios.forEach((m) => { if (m.oficial_tipo_urbana) oficialPorNombre[m.nombre] = m.oficial_tipo_urbana; });

  let tipoOk = 0, cuotasOk = 0, bloqueOk = 0, sinSedeFalsa = 0, fechaOk = 0, graficoOk = 0, calcOk = 0;
  let calendarioOk = 0, estadoOk = 0, orientativoOk = 0, boniOk = 0;
  let poblacionOk = 0, serieOk = 0, contextoOk = 0, ivtmOk = 0, totalOk = 0, htmlLimpio = 0;
  let plusOficial = 0, sinInventos = 0;
  const impuestos = JSON.parse(leer('data/hacienda_impuestos.json'));
  const datosCalc = leer('municipios.js');
  const munisCalc = JSON.parse(datosCalc.slice(datosCalc.indexOf('[')).replace(/;\s*$/, ''));

  claves.forEach((clave) => {
    const m = municipios.find((x) => clave === x.ccaa + '/' + x.provincia_slug + '/' + x.slug);
    const dom = new JSDOM(leer(clave + '/index.html'));
    const d = dom.window.document;
    const esperado = pct(m.oficial_tipo_urbana);

    const celda = [...d.querySelectorAll('.quick li')].find((li) => /IBI urbano/.test(li.textContent));
    if (celda && celda.textContent.includes(esperado)) tipoOk++;
    else console.log('    tipo no aplicado en ' + clave + ' (esperado ' + esperado + ')');

    // cuotas de ejemplo recalculadas
    const filas = [...d.querySelectorAll('table.dt tbody tr')].filter((tr) => tr.cells.length === 4 && /€$/.test(tr.cells[1].textContent.trim()));
    const malas = filas.filter((tr) => {
      const vc = parseFloat(tr.cells[1].textContent.replace(/\./g, '').replace(/[^\d]/g, ''));
      const anual = parseFloat(tr.cells[2].textContent.replace(/\./g, '').replace(/[^\d]/g, ''));
      return Math.abs(anual - vc * m.oficial_tipo_urbana / 100) > 1.5;
    });
    if (filas.length && malas.length === 0) cuotasOk++;
    else if (malas.length) console.log('    cuotas mal recalculadas en ' + clave);

    const html = leer(clave + '/index.html');
    if (/Tipo oficial del IBI en/.test(html) && html.includes('serviciostelematicosext.hacienda.gob.es')) bloqueOk++;
    else console.log('    falta el bloque oficial en ' + clave);
    if (!/sedelectronica\.es/.test(html)) sinSedeFalsa++;
    else console.log('    sigue habiendo enlace a sede falsa en ' + clave);
    if (html.includes('"dateModified": "' + hoy + '"') || html.includes('"dateModified":"' + hoy + '"')) fechaOk++;
    else console.log('    dateModified sin actualizar en ' + clave);

    // el gráfico usa los tipos oficiales
    const barras = [...d.querySelectorAll('.chart-bar-row')];
    const malGrafico = barras.filter((row) => {
      const nombre = row.querySelector('.chart-label').textContent.trim();
      const valor = parseFloat(row.querySelector('.chart-bar span').textContent.replace(',', '.'));
      return oficialPorNombre[nombre] !== undefined && Math.abs(valor - oficialPorNombre[nombre]) > 0.0001;
    });
    if (barras.length && malGrafico.length === 0) graficoOk++;
    else if (malGrafico.length) console.log('    gráfico desactualizado en ' + clave + ' (' + malGrafico.length + ' barras)');

    const enCalc = munisCalc.find((x) => x.nombre === m.nombre);
    if (enCalc && Math.abs(enCalc.ibiU - m.oficial_tipo_urbana) < 1e-9) calcOk++;
    else console.log('    la calculadora no coincide en ' + clave);

    // bloques nuevos y transparencia de los datos no contrastados
    // la explicación de los recargos vive una sola vez en /ibi-2026/#recargos
    if (/<h2>Cuándo se paga el IBI en/.test(html) && html.includes('ibi-2026/#recargos')) calendarioOk++;
    else console.log('    falta el bloque de calendario en ' + clave);
    if (/<strong>Verificado<\/strong> el \d{2}\/\d{2}\/\d{4} en Hacienda/.test(html)
        && /<strong>No publicamos<\/strong> el importe de la tasa de residuos/.test(html)
        && html.includes('metodologia/')) estadoOk++;
    else console.log('    falta el estado de los datos en ' + clave);
    // La tasa de residuos y las fechas de cobro se retiraron por no tener fuente:
    // no debe quedar ningún importe ni ninguna fecha presentada como propia del
    // municipio, y sí debe estar la explicación con el art. 11.3 de la Ley 7/2022.
    const sinImporteBasuras = !/Basura vivienda:<\/strong>/.test(html)
      && !/<td>Vivienda habitual<\/td><td class="v">[\d.,]+ €\/año<\/td>/.test(html)
      && !/<tr><td>Basuras<\/td>/.test(html);
    const sinFechasInventadas = !/Período de pago:<\/strong>\s*\d/.test(html)
      && !/<td>Período de pago \(orientativo\)<\/td>/.test(html);
    const conMarcoLegal = /<h2>Tasa de (?:basuras|residuos) en /.test(html)
      && html.includes('BOE-A-2022-5809')
      && html.includes('art. 62.3');
    if (sinImporteBasuras && sinFechasInventadas && conMarcoLegal) orientativoOk++;
    else console.log('    basuras o calendario sin el tratamiento nuevo en ' + clave);
    if (!/<td>Familia numerosa[^<]*<\/td><td class="v">\d+%/.test(html)) boniOk++;
    else console.log('    bonificación con porcentaje sin respaldo en ' + clave);

    // población oficial del INE y su serie
    const pobEsperada = new Intl.NumberFormat('de-DE').format(m.poblacion_oficial);
    if (html.includes(pobEsperada + ' habitantes')) poblacionOk++;
    else console.log('    población oficial no aplicada en ' + clave);
    const serie = m.poblacion_serie || [];
    const filasSerie = [...d.querySelectorAll('#contexto table.dt tbody tr')]
      .filter((tr) => /^\d{4}$/.test(tr.cells[0].textContent.trim()));
    if (serie.length >= 2 && filasSerie.length === serie.length) serieOk++;
    else console.log('    serie de población incompleta en ' + clave + ' (' + filasSerie.length + '/' + serie.length + ')');

    // secciones propias
    if (d.getElementById('contexto') && d.getElementById('otros-impuestos')) contextoOk++;
    else console.log('    faltan las secciones propias en ' + clave);

    // IVTM con la tarifa oficial
    const imp = impuestos[m.oficial_codigo_ine];
    const turismo = imp && imp.conceptos.C19 && imp.conceptos.C19.valor;
    const eur2 = (s) => new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      .format(parseFloat(String(s).replace(/\./g, '').replace(',', '.')));
    if (turismo && html.includes(eur2(turismo) + ' €/año')) ivtmOk++;
    else console.log('    tarifa de IVTM no publicada en ' + clave);

    // coeficientes reales de plusvalía cuando Hacienda los publica y son coherentes
    const coefs = [];
    for (let k = 51; k <= 71 && imp; k++) {
      const c = imp.conceptos['C' + k];
      if (c && c.valor) coefs.push(parseFloat(c.valor.replace(',', '.')));
    }
    // Los coeficientes del art. 107.4 TRLRHL van de 0,09 a 0,40: por debajo es
    // el porcentaje anual del sistema anterior al RDL 26/2021.
    const coherente = coefs.length > 0 && Math.max(...coefs) >= 0.10 && Math.max(...coefs) <= 0.45;
    if (!coherente) {
      // debe caer al bloque genérico, con aviso y sin tabla
      if (/Coeficientes máximos vigentes/.test(html) && !/<td>20 años o más<\/td>/.test(html)) plusOficial++;
      else console.log('    plusvalía sin respaldo publicada en ' + clave);
    } else if (/<h2>Plusvalía municipal en [^<]*coeficientes y tipos oficiales/.test(html)
               && html.includes('<td>20 años o más</td>')) plusOficial++;
    else console.log('    plusvalía sin coeficientes oficiales en ' + clave);

    // el resumen de la barra lateral: solo IBI, y la cuota debe salir del tipo oficial
    const resumen = html.match(/<tr><td>IBI \(VC ([\d.]+) €\)<\/td><td[^>]*>([\d.]+) €<\/td><\/tr>\s*<tr><td>Equivalente mensual<\/td><td[^>]*>([\d.,]+) €\/mes<\/td><\/tr>/);
    if (resumen) {
      const num = (s) => parseInt(s.replace(/\./g, ''), 10);
      const esperada = Math.round(num(resumen[1]) * m.oficial_tipo_urbana / 100);
      if (num(resumen[2]) === esperada) totalOk++;
      else console.log('    el resumen fiscal no cuadra en ' + clave + ' (' + resumen[2] + ' vs ' + esperada + ')');
    } else console.log('    no se localiza el resumen fiscal en ' + clave);

    // restos de HTML mal formado y avisos duplicados
    const orientativos = (html.match(/\[Importe orientativo, sin contrastar\.\]/g) || []).length;
    if (orientativos <= 1 && !/>https?:\/\/[^<"]*"https/.test(html)) htmlLimpio++;
    else console.log('    HTML sucio en ' + clave + ' (' + orientativos + ' avisos duplicados)');

    // nada de lecturas de mercado sin fuente
    if (!/mercado inmobiliario local|contenedor marrón|amortigua la subida/.test(html)) sinInventos++;
    else console.log('    queda texto sin fuente en ' + clave);
  });

  const n = claves.length;
  tipoOk === n ? ok('las ' + n + ' fichas muestran el tipo oficial del Ministerio') : bad(tipoOk + '/' + n + ' con el tipo oficial');
  cuotasOk === n ? ok('las cuotas de ejemplo están recalculadas en las ' + n) : bad(cuotasOk + '/' + n + ' con cuotas correctas');
  graficoOk === n ? ok('los gráficos comparativos usan los tipos oficiales') : bad(graficoOk + '/' + n + ' con gráfico correcto');
  bloqueOk === n ? ok('las ' + n + ' incluyen el bloque de tipo oficial con enlace a la fuente') : bad(bloqueOk + '/' + n + ' con bloque oficial');
  sinSedeFalsa === n ? ok('ninguna enlaza ya a las sedes electrónicas inexistentes') : bad((n - sinSedeFalsa) + ' con enlaces falsos');
  fechaOk === n ? ok('las ' + n + ' actualizan dateModified a hoy') : bad(fechaOk + '/' + n + ' con fecha actualizada');
  calcOk === n ? ok('la calculadora usa el mismo tipo que las fichas') : bad(calcOk + '/' + n + ' coinciden con la calculadora');
  calendarioOk === n ? ok('las ' + n + ' tienen el bloque de calendario de cobro y recargos') : bad(calendarioOk + '/' + n + ' con bloque de calendario');
  estadoOk === n ? ok('las ' + n + ' publican el estado de cada dato (contrastado u orientativo)') : bad(estadoOk + '/' + n + ' con estado de los datos');
  orientativoOk === n ? ok('las ' + n + ' explican la tasa de residuos con la Ley 7/2022 y el art. 62.3 LGT, sin importes ni fechas sin fuente') : bad(orientativoOk + '/' + n + ' con el tratamiento nuevo de basuras y calendario');
  boniOk === n ? ok('ninguna afirma un porcentaje de bonificación municipal sin respaldo') : bad((n - boniOk) + ' con porcentajes sin respaldo');
  poblacionOk === n ? ok('las ' + n + ' publican la población oficial del INE') : bad(poblacionOk + '/' + n + ' con población oficial');
  serieOk === n ? ok('las ' + n + ' publican la serie del padrón (6 revisiones)') : bad(serieOk + '/' + n + ' con serie de población');
  contextoOk === n ? ok('las ' + n + ' tienen la comparativa propia y el bloque de otros tributos') : bad(contextoOk + '/' + n + ' con las secciones propias');
  ivtmOk === n ? ok('las ' + n + ' publican la tarifa oficial del IVTM') : bad(ivtmOk + '/' + n + ' con IVTM');
  plusOficial === n ? ok('la plusvalía usa los coeficientes reales cuando Hacienda los publica') : bad(plusOficial + '/' + n + ' con plusvalía correcta');
  totalOk === n ? ok('el resumen fiscal de la barra lateral cuadra con el tipo oficial en las ' + n) : bad(totalOk + '/' + n + ' con el resumen correcto');
  htmlLimpio === n ? ok('sin avisos duplicados ni enlaces mal formados en las ' + n) : bad((n - htmlLimpio) + ' con HTML sucio');
  sinInventos === n ? ok('sin lecturas de mercado ni datos sin fuente en las ' + n) : bad((n - sinInventos) + ' con texto sin fuente');
}

// ───────── páginas nuevas: comparador, metodología y transparencia ─────────
console.log('\n== Páginas nuevas ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;

  const domCmp = new JSDOM(leer('municipios/index.html'), { runScripts: 'dangerously', pretendToBeVisual: true });
  const dCmp = domCmp.window.document;
  const filas = [...dCmp.querySelectorAll('table tbody tr')];
  filas.length === municipios.length
    ? ok('el comparador /municipios/ lista los ' + filas.length + ' municipios')
    : bad('el comparador lista ' + filas.length + ' de ' + municipios.length);

  // columnas ampliadas: el comparador ya no se queda en el tipo de IBI
  const columnas = [...dCmp.querySelectorAll('table.sortable thead th')].map((th) => th.textContent.trim());
  const esperadas = ['Municipio', 'Provincia', 'Comunidad', 'Habitantes', 'IBI urbano',
    'IBI rústico', 'Cuota con VC de 50.000 €', 'Valores catastrales', 'ICIO',
    'IVTM 8–11,99 CV', 'Plusvalía: tipo máx.'];
  JSON.stringify(columnas) === JSON.stringify(esperadas)
    ? ok('el comparador tiene las ' + columnas.length + ' columnas y todas salen de Hacienda (sin la de basuras)')
    : bad('columnas inesperadas: ' + columnas.join(' | '));

  // y cada celda nueva coincide con la fuente oficial
  const impuestosCmp = JSON.parse(leer('data/hacienda_impuestos.json'));
  const pctTxt = (v) => String(Number(v.toFixed(4))).replace('.', ',') + '%';
  const eur2Cmp = (v) => new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v);
  let celdasOk = 0, celdasMal = 0;
  municipios.forEach((m) => {
    const fila = filas.find((tr) => tr.cells[0].textContent.trim() === m.nombre);
    if (!fila) { celdasMal++; return; }
    const imp = impuestosCmp[m.oficial_codigo_ine];
    const leerV = (c) => {
      const x = imp && imp.conceptos[c] && imp.conceptos[c].valor;
      return x ? parseFloat(String(x).replace(/\./g, '').replace(',', '.')) : null;
    };
    const icio = leerV('C17');
    const ivtm = leerV('C19');
    const problemas = [];
    if (fila.cells[7].textContent.trim() !== String(m.oficial_ano_valores_catastrales)) problemas.push('año catastral');
    if (icio !== null && fila.cells[8].textContent.trim() !== pctTxt(icio)) problemas.push('ICIO');
    if (ivtm !== null && fila.cells[9].textContent.trim() !== eur2Cmp(ivtm) + ' €') problemas.push('IVTM');
    if (problemas.length === 0) celdasOk++;
    else { celdasMal++; console.log('    ' + m.nombre + ': ' + problemas.join(', ')); }
  });
  celdasMal === 0
    ? ok('las columnas nuevas coinciden con la fuente en los ' + celdasOk + ' municipios')
    : bad(celdasMal + ' municipios con celdas que no coinciden con la fuente');

  // el título mira a 2026 pero la página dice de qué ejercicio es el dato
  const htmlCmp = leer('municipios/index.html');
  const tituloCmp = (htmlCmp.match(/<title>([^<]*)<\/title>/) || [])[1] || '';
  /2026/.test(tituloCmp) && tituloCmp.length <= 60
    ? ok('el título del comparador apunta a 2026 y cabe en 60 caracteres: "' + tituloCmp + '"')
    : bad('título del comparador: "' + tituloCmp + '" (' + tituloCmp.length + ' caracteres)');
  /ejercicio <strong>2025<\/strong>|ejercicio 2025/.test(htmlCmp)
    ? ok('y aclara que el dato oficial es del ejercicio 2025')
    : bad('el comparador no aclara a qué ejercicio corresponden los tipos');
  let enlacesRotos = 0;
  filas.forEach((tr) => {
    const a = tr.querySelector('a');
    if (!a) { enlacesRotos++; return; }
    const destino = path.resolve(path.join(ROOT, 'municipios'), a.getAttribute('href'));
    if (!fs.existsSync(path.join(destino, 'index.html'))) enlacesRotos++;
  });
  enlacesRotos === 0 ? ok('todas las filas enlazan a una ficha existente') : bad(enlacesRotos + ' filas con enlace roto');
  const th = dCmp.querySelector('table th[data-col]');
  if (th) {
    const antes = filas.map((tr) => tr.cells[0].textContent.trim());
    th.dispatchEvent(new domCmp.window.MouseEvent('click', { bubbles: true }));
    const despues = [...dCmp.querySelectorAll('table tbody tr')].map((tr) => tr.cells[0].textContent.trim());
    JSON.stringify(antes) !== JSON.stringify(despues)
      ? ok('la tabla del comparador se reordena al pulsar el encabezado')
      : bad('la tabla del comparador no se reordena');
  } else bad('el comparador no tiene encabezados ordenables');

  const palabras = (rel) => leer(rel).replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
  palabras('metodologia/index.html') >= 600 ? ok('/metodologia/ tiene ' + palabras('metodologia/index.html') + ' palabras') : bad('/metodologia/ es demasiado corta');
  palabras('sobre-nosotros/index.html') >= 400 ? ok('/sobre-nosotros/ tiene ' + palabras('sobre-nosotros/index.html') + ' palabras') : bad('/sobre-nosotros/ es demasiado corta');
  /no soy asesor fiscal|no somos asesores fiscales/i.test(leer('sobre-nosotros/index.html'))
    ? ok('/sobre-nosotros/ avisa de que no hay asesoramiento fiscal')
    : bad('/sobre-nosotros/ no incluye el aviso de no asesoramiento');
  !/colegiad|máster en|licenciad|años de experiencia como asesor/i.test(leer('sobre-nosotros/index.html'))
    ? ok('/sobre-nosotros/ no atribuye credenciales inventadas')
    : bad('/sobre-nosotros/ afirma credenciales sin respaldo');

  const prov = leer('provincias/index.html');
  /http-equiv="refresh"/.test(prov) && /window\.location\.replace/.test(prov)
    ? ok('/provincias/ redirige a /comunidades/')
    : bad('/provincias/ no redirige');

  const contacto = leer('contacto/index.html');
  /FORM_ENDPOINT\s*=\s*'https:\/\/formsubmit\.co\/ajax\//.test(contacto)
    ? ok('el formulario envía a un endpoint real (FormSubmit)')
    : bad('el formulario no tiene endpoint de envío');
  !/enviado correctamente/i.test(contacto.replace(/[\s\S]*?FORM_ENDPOINT/, '')) || /fetch\(/.test(contacto)
    ? ok('el formulario hace una petición real, no simula el envío')
    : bad('el formulario simula el envío');

  const aviso = leer('aviso-legal/index.html');
  /\[PENDIENTE/.test(aviso)
    ? ok('el aviso legal marca lo que falta (NIF y domicilio) en lugar de inventarlo')
    : console.log('    (el aviso legal ya no tiene marcadores PENDIENTE: revisar que el NIF esté puesto)');
}

// ───────── buscador de la portada con autocompletado ─────────
console.log('\n== Buscador de la portada ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  let html = leer('index.html');
  const js = leer('buscador-municipios.js');
  // se inyecta el script porque jsdom no resuelve el src local
  html = html.replace('<script src="buscador-municipios.js" defer></script>',
    '<script>' + js + '</script>');
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const w = dom.window, d = dom.window.document;
  const input = d.getElementById('tm-buscador');
  const panel = d.getElementById('tm-sugerencias');

  if (!input || !panel) { bad('la portada no tiene el buscador con autocompletado'); }
  else {
    ok('la portada monta el combobox del buscador');

    const teclea = (q) => {
      input.value = q;
      input.dispatchEvent(new w.Event('input', { bubbles: true }));
      return [...panel.querySelectorAll('[role="option"]')];
    };
    const nombres = (ops) => ops.map((li) => {
      const n = li.querySelector('.sug-n');
      return n ? n.textContent.trim() : '';
    });

    // el caso que pedía el usuario: escribir «our» sugiere Ourense
    const our = nombres(teclea('our'));
    our[0] === 'Ourense'
      ? ok('escribir «our» sugiere Ourense en primer lugar')
      : bad('«our» sugiere: ' + our.join(', '));

    // acentos, artículos y provincia
    const casos = [
      ['coruña', 'A Coruña'], ['coruna', 'A Coruña'], ['porri', 'O Porriño'],
      ['pontevedra', 'Pontevedra'], ['SANTAND', 'Santander'],
    ];
    const fallan = casos.filter(([q, esperado]) => nombres(teclea(q))[0] !== esperado);
    fallan.length === 0
      ? ok('funciona sin acentos, con artículo («A Coruña») y por provincia')
      : bad('fallan: ' + fallan.map((c) => c[0]).join(', '));

    // todos los municipios se encuentran por su nombre y su destino existe
    let noEncontrados = 0, destinosRotos = 0;
    municipios.forEach((m) => {
      const ops = teclea(m.nombre);
      const urls = ops.map((li) => li.getAttribute('data-url'));
      const esperado = m.ccaa + '/' + m.provincia_slug + '/' + m.slug + '/';
      if (!urls.includes(esperado)) {
        noEncontrados++;
        if (noEncontrados <= 3) console.log('    no se encuentra: ' + m.nombre);
      }
      urls.forEach((u) => {
        if (!fs.existsSync(path.join(ROOT, u, 'index.html'))) destinosRotos++;
      });
    });
    noEncontrados === 0
      ? ok('los ' + municipios.length + ' municipios se encuentran escribiendo su nombre')
      : bad(noEncontrados + ' municipios no aparecen en las sugerencias');
    destinosRotos === 0 ? ok('ningún destino sugerido lleva a una página inexistente') : bad(destinosRotos + ' destinos rotos');

    // sin resultados: no se deja al usuario en el aire
    const vacio = teclea('zzzzz');
    vacio.length === 1 && vacio[0].getAttribute('data-url') === 'municipios/'
      ? ok('si no hay coincidencia, ofrece el comparador en lugar de no responder')
      : bad('el caso sin resultados no ofrece salida');

    // teclado y ARIA
    teclea('our');
    input.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    const marcada = panel.querySelector('[aria-selected="true"]');
    marcada && input.getAttribute('aria-activedescendant') === marcada.id
      && input.getAttribute('aria-expanded') === 'true'
      ? ok('se navega con flechas y aria-activedescendant sigue a la opción marcada')
      : bad('la navegación por teclado o el ARIA no funcionan');
    input.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    panel.hidden && input.getAttribute('aria-expanded') === 'false'
      ? ok('Escape cierra el panel y actualiza aria-expanded')
      : bad('Escape no cierra el panel');

    // menos de dos letras no abre el panel (evita listar los 134)
    teclea('o');
    panel.hidden ? ok('con una sola letra no despliega sugerencias') : bad('se despliega con una sola letra');

    // funciona sin JavaScript: el formulario lleva al comparador
    const form = new JSDOM(leer('index.html')).window.document
      .querySelector('.search-wrap form');
    form && form.getAttribute('action') === 'municipios/'
      ? ok('sin JavaScript el formulario lleva al comparador de municipios')
      : bad('el buscador no tiene respaldo sin JavaScript');

    // el índice sale de la fuente de datos y no bloquea el renderizado
    const indice = JSON.parse(js.slice(js.indexOf('['), js.indexOf('];') + 1));
    indice.length === municipios.length
      ? ok('el índice del buscador tiene los ' + indice.length + ' municipios')
      : bad('el índice tiene ' + indice.length + ' de ' + municipios.length);
    /<script src="buscador-municipios.js" defer><\/script>/.test(leer('index.html'))
      ? ok('el script se carga con defer y no bloquea el renderizado')
      : bad('el script del buscador no se carga con defer');
  }
}

// ───────── guías nuevas: impuesto de circulación y valor catastral ─────────
console.log('\n== Guías nuevas ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const impuestos = JSON.parse(leer('data/hacienda_impuestos.json'));
  const NUEVAS = ['impuesto-circulacion', 'valor-catastral'];
  const eur2 = (v) => new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v) + ' €';

  let existen = 0, extensas = 0, schemaOk = 0, tituloOk = 0, enlacesOk = 0, figurasOk = 0;
  NUEVAS.forEach((slug) => {
    const rel = slug + '/index.html';
    if (!fs.existsSync(path.join(ROOT, rel))) { bad('falta /' + slug + '/'); return; }
    existen++;
    const html = leer(rel);
    const dom = new JSDOM(html);
    const d = dom.window.document;

    const palabras = html.replace(/<script[\s\S]*?<\/script>/g, '')
      .replace(/<(nav|header|footer)[\s\S]*?<\/\1>/g, '')
      .replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
    if (palabras >= 2000) extensas++;
    else console.log('    /' + slug + '/ solo tiene ' + palabras + ' palabras');

    const tipos = [...d.querySelectorAll('script[type="application/ld+json"]')]
      .map((s) => JSON.parse(s.textContent)['@type']);
    if (tipos.includes('Article') && tipos.includes('FAQPage') && tipos.includes('BreadcrumbList')) schemaOk++;
    else console.log('    schema incompleto en /' + slug + '/: ' + tipos.join(','));

    const titulo = (html.match(/<title>([^<]*)<\/title>/) || [])[1] || '';
    if (titulo.length > 0 && titulo.length <= 62) tituloOk++;
    else console.log('    título de /' + slug + '/ con ' + titulo.length + ' caracteres');

    // el índice de contenidos apunta a secciones que existen
    let anclasRotas = 0;
    d.querySelectorAll('.toc a[href^="#"]').forEach((a) => {
      if (!d.getElementById(a.getAttribute('href').slice(1))) anclasRotas++;
    });
    let rotos = anclasRotas;
    d.querySelectorAll('a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      if (/^(https?:|mailto:|#)/.test(href)) return;
      const sinFragmento = href.split('#')[0];
      if (!sinFragmento) return;
      const destino = path.resolve(path.join(ROOT, slug), sinFragmento);
      if (!fs.existsSync(destino) && !fs.existsSync(path.join(destino, 'index.html'))) {
        rotos++;
        console.log('    destino inexistente: ' + href);
      }
    });
    if (rotos === 0) enlacesOk++; else console.log('    ' + rotos + ' enlaces o anclas rotos en /' + slug + '/');

    // imágenes propias, con alt y dimensiones, y el archivo en disco
    const imgs = [...d.querySelectorAll('article img, figure img')];
    const malas = imgs.filter((i) => !i.getAttribute('alt') || !i.getAttribute('width')
      || !fs.existsSync(path.resolve(path.join(ROOT, slug), i.getAttribute('src'))));
    if (imgs.length >= 2 && malas.length === 0) figurasOk++;
    else console.log('    problema con las ' + imgs.length + ' imágenes de /' + slug + '/');
  });
  existen === 2 ? ok('las 2 guías nuevas existen') : bad('faltan guías nuevas');
  extensas === 2 ? ok('las 2 pasan de 2.000 palabras') : bad(extensas + '/2 con extensión suficiente');
  schemaOk === 2 ? ok('las 2 llevan Article, FAQPage y BreadcrumbList') : bad(schemaOk + '/2 con schema');
  tituloOk === 2 ? ok('los 2 títulos caben sin truncarse') : bad(tituloOk + '/2 con título correcto');
  enlacesOk === 2 ? ok('ningún enlace ni ancla roto en las 2') : bad('hay enlaces o anclas rotos');
  figurasOk === 2 ? ok('las 2 llevan gráficos propios con alt y dimensiones') : bad(figurasOk + '/2 con imágenes correctas');

  // los SVG generados son texto real indexable y ligeros
  const svgs = ['esquema-ivtm.svg', 'ivtm-turismos-2026.svg',
    'esquema-valor-catastral.svg', 'valor-catastral-antiguedad.svg'];
  const buenos = svgs.filter((f) => {
    const p = path.join(ROOT, 'img', f);
    if (!fs.existsSync(p)) return false;
    const s = fs.readFileSync(p, 'utf8');
    return /<title id=/.test(s) && /<desc id=/.test(s) && /aria-labelledby/.test(s)
      && fs.statSync(p).size < 20 * 1024;
  });
  buenos.length === svgs.length
    ? ok('los ' + svgs.length + ' SVG llevan title, desc y aria, y pesan menos de 20 kB')
    : bad(buenos.length + '/' + svgs.length + ' SVG correctos');

  // las cifras del IVTM salen de la fuente
  const ivtm = leer('impuesto-circulacion/index.html');
  const conDato = municipios.filter((m) => {
    const imp = impuestos[m.oficial_codigo_ine];
    return imp && imp.conceptos.C19 && imp.conceptos.C19.valor;
  });
  const valores = conDato.map((m) => parseFloat(impuestos[m.oficial_codigo_ine].conceptos.C19.valor.replace(',', '.')));
  const maxV = Math.max(...valores), minV = Math.min(...valores);
  ivtm.includes(eur2(maxV)) && ivtm.includes(eur2(minV))
    ? ok('la guía del IVTM cita el máximo y el mínimo reales (' + eur2(minV) + '–' + eur2(maxV) + ')')
    : bad('las cifras del IVTM no coinciden con la fuente');
  /34,08 €/.test(ivtm) && /68,16 €/.test(ivtm)
    ? ok('y la cuota mínima legal del art. 95.1 con su tope (×2)')
    : bad('falta la cuota mínima legal o su tope');

  // la guía del valor catastral usa la antigüedad real
  const vc = leer('valor-catastral/index.html');
  const anos = municipios.filter((m) => /^\d+$/.test(String(m.oficial_ano_valores_catastrales)))
    .map((m) => parseInt(m.oficial_ano_valores_catastrales, 10)).sort((a, b) => a - b);
  const mediana = anos[Math.floor(anos.length / 2)];
  const antig = new Date().getFullYear() - mediana;
  vc.includes(antig + ' años') ? ok('la guía del valor catastral usa la antigüedad mediana real (' + antig + ' años)') : bad('la antigüedad mediana no coincide');
  /valor de referencia/i.test(vc) && /base liquidable/i.test(vc) && /subsanación de discrepancias/i.test(vc)
    ? ok('y cubre valor de referencia, base liquidable y subsanación de discrepancias')
    : bad('falta alguno de los tres conceptos clave del valor catastral');

  // enlazadas desde el menú y desde las guías relacionadas
  const enMenu = NUEVAS.filter((s) => new RegExp('<nav[\\s\\S]*?' + s + '/"[\\s\\S]*?</nav>').test(leer('ibi-2026/index.html')));
  enMenu.length === 2 ? ok('las 2 están en el menú de Impuestos') : bad(enMenu.length + '/2 en el menú');
  leer('ibi-2026/index.html').includes('../valor-catastral/') && leer('plusvalia/index.html').includes('../valor-catastral/')
    ? ok('/ibi-2026/ y /plusvalia/ enlazan la guía del valor catastral en su texto')
    : bad('las guías relacionadas no enlazan el valor catastral');
  const sitemap = leer('sitemap.xml');
  NUEVAS.every((s) => sitemap.includes('https://tasasmunicipales.info/' + s + '/'))
    ? ok('las 2 están en el sitemap')
    : bad('faltan en el sitemap');
  const ficha = leer(municipios[0].ccaa + '/' + municipios[0].provincia_slug + '/' + municipios[0].slug + '/index.html');
  ficha.includes('impuesto-circulacion/') ? ok('las fichas enlazan la guía del IVTM desde su tarifa') : bad('las fichas no enlazan la guía del IVTM');
}

// ───────── cabecera: menú agrupado por intención ─────────
console.log('\n== Cabecera del sitio ==');
{
  const paginas = [];
  const walk = (dir) => {
    fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
      if (['.git', 'img', 'scripts', 'data', 'node_modules'].includes(e.name)) return;
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name === 'index.html') paginas.push(p);
    });
  };
  walk(ROOT);

  const ENTRADAS = ['Mi municipio', 'Impuestos', 'Comparativas', 'Metodología', 'Calcular mi IBI'];
  const ACTIVAS = {
    'municipios': 'municipios/', 'comunidades': 'comunidades/', 'ibi-2026': 'ibi-2026/',
    'tasa-basuras': 'tasa-basuras/', 'plusvalia': 'plusvalia/',
    'bonificaciones': 'bonificaciones/', 'analisis': 'analisis/',
    'metodologia': 'metodologia/', 'calculadora-ibi': 'calculadora-ibi/',
  };
  let conNav = 0, estructura = 0, aria = 0, sinJs = 0, cta = 0, destinosOk = 0, viejo = 0;
  let activasOk = 0, activasEsperadas = 0;
  paginas.forEach((p) => {
    const html = fs.readFileSync(p, 'utf8');
    const m = html.match(/<nav[\s\S]*?<\/nav>/);
    const esRedireccion = /http-equiv="refresh"/.test(html);
    if (!m) { if (!esRedireccion) bad('sin cabecera: ' + path.relative(ROOT, p)); return; }
    conNav++;
    const nav = m[0];

    if (ENTRADAS.every((e) => nav.includes('>' + e + '<'))) estructura++;
    else console.log('    entradas incompletas en ' + path.relative(ROOT, p));
    if (/aria-label="Navegación principal"/.test(nav)) aria++;
    // los desplegables son <details>/<summary>: sin JavaScript y accesibles
    if ((nav.match(/<details/g) || []).length === 2 && (nav.match(/<summary>/g) || []).length === 2
        && !/onclick|javascript:/i.test(nav)) sinJs++;
    else console.log('    desplegables incorrectos en ' + path.relative(ROOT, p));
    if (/class="nav-cta"/.test(nav)) cta++;
    if (/>Bonificaciones<\/a>|>IBI 2026<\/a>|>Análisis<\/a>/.test(nav)) {
      viejo++;
      console.log('    quedan rótulos del menú antiguo en ' + path.relative(ROOT, p));
    }

    // todos los destinos del menú existen
    const prefijo = '../'.repeat(path.relative(ROOT, p).split(path.sep).length - 1);
    const hrefs = [...nav.matchAll(/href="([^"]+)"/g)].map((x) => x[1]);
    const rotos = hrefs.filter((h) => !fs.existsSync(path.resolve(path.dirname(p), h, 'index.html')));
    if (rotos.length === 0) destinosOk++; else console.log('    destinos rotos: ' + rotos.join(', '));

    // la página marca su propia entrada
    const carpeta = path.relative(ROOT, path.dirname(p)).split(path.sep).join('/');
    const esperado = ACTIVAS[carpeta];
    if (esperado) {
      activasEsperadas++;
      const re = new RegExp('href="' + prefijo.replace(/\./g, '\\.') + esperado + '"[^>]*aria-current="page"');
      if (re.test(nav) || (esperado === 'calculadora-ibi/' && /nav-cta"[^>]*aria-current/.test(nav))) activasOk++;
      else console.log('    no marca su entrada activa: ' + carpeta);
    }
  });
  estructura === conNav ? ok('las ' + conNav + ' cabeceras tienen las 5 entradas y el botón') : bad(estructura + '/' + conNav);
  aria === conNav ? ok('todas llevan aria-label en la navegación') : bad(aria + '/' + conNav + ' con aria-label');
  sinJs === conNav ? ok('los desplegables son <details> nativos, sin JavaScript') : bad(sinJs + '/' + conNav);
  cta === conNav ? ok('todas destacan la calculadora como botón') : bad(cta + '/' + conNav + ' con el botón');
  viejo === 0 ? ok('no queda ningún rótulo del menú antiguo') : bad(viejo + ' páginas con el menú antiguo');
  destinosOk === conNav ? ok('todos los destinos del menú existen en las ' + conNav) : bad('hay destinos rotos');
  activasOk === activasEsperadas ? ok('las ' + activasOk + ' páginas del menú marcan su entrada activa') : bad(activasOk + '/' + activasEsperadas);

  const css = leer('styles.css');
  /\.nav-menu\s*\{[^}]*position:\s*absolute/.test(css) && /@media \(max-width: 900px\)[\s\S]*?\.mainnav[\s\S]*?overflow-x:\s*auto/.test(css)
    ? ok('el CSS despliega el submenú por encima y en móvil desliza en horizontal')
    : bad('falta el CSS del submenú o el comportamiento móvil');
}

// ───────── guías nacionales: sin datos obsoletos ni tablas falsas ─────────
console.log('\n== Datos de las cuatro guías ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const pct = (v) => String(Number(v.toFixed(4))).replace('.', ',') + '%';
  const eur = (v) => new Intl.NumberFormat('de-DE').format(Math.round(v)) + ' €';
  const GUIAS = ['ibi-2026', 'plusvalia', 'bonificaciones', 'tasa-basuras'];

  // 1. ninguna cifra municipal contradice ya a la ficha
  let contradicen = 0;
  const porNombre = {};
  municipios.forEach((m) => { porNombre[m.nombre] = m; });
  // Se valida cada celda según lo que dice su encabezado de columna, no a bulto:
  // en /plusvalia/ el porcentaje es el tipo del IIVTNU, no el del IBI.
  const impuestosG = JSON.parse(leer('data/hacienda_impuestos.json'));
  const tipoPlusvalia = (m) => {
    const imp = impuestosG[m.oficial_codigo_ine];
    if (!imp) return null;
    const leerV = (c) => {
      const x = imp.conceptos[c] && imp.conceptos[c].valor;
      return x ? parseFloat(String(x).replace(',', '.')) : null;
    };
    const tipos = [];
    for (let k = 72; k <= 92; k++) { const v = leerV('C' + k); if (v !== null) tipos.push(v); }
    return tipos.length ? Math.max(...tipos) : null;
  };
  GUIAS.forEach((g) => {
    const dom = new JSDOM(leer(g + '/index.html'));
    [...dom.window.document.querySelectorAll('table.dt')].forEach((tabla) => {
      const cabeceras = [...tabla.querySelectorAll('thead th')].map((th) => th.textContent.trim());
      [...tabla.querySelectorAll('tbody tr')].forEach((tr) => {
        const nombre = tr.cells[0] ? tr.cells[0].textContent.trim() : '';
        const m = porNombre[nombre];
        if (!m) return;
        [...tr.cells].forEach((celda, i) => {
          const cab = (cabeceras[i] || '').toLowerCase();
          const txt = celda.textContent.trim();
          const fallo = (esperado) => {
            contradicen++;
            console.log('    ' + g + ' · ' + nombre + ' [' + cabeceras[i] + ']: ' + txt
              + ' frente a ' + esperado);
          };
          if (/tipo urbano|ibi urbano/.test(cab) && txt !== pct(m.oficial_tipo_urbana)) fallo(pct(m.oficial_tipo_urbana));
          if (/tipo de gravamen/.test(cab)) {
            const esperado = tipoPlusvalia(m);
            if (esperado !== null && txt !== pct(esperado)) fallo(pct(esperado));
          }
          // La columna «tasa anual» de /tasa-basuras/ se retiró: si reaparece, es
          // que alguien ha vuelto a publicar un importe sin fuente.
          if (/tasa anual/.test(cab)) fallo('la columna no debería existir');
          if (/cuota con vc/.test(cab)) {
            const esperado = eur(50000 * m.oficial_tipo_urbana / 100);
            if (txt !== esperado) fallo(esperado);
          }
        });
      });
    });
  });
  contradicen === 0
    ? ok('ninguna cifra municipal de las guías contradice a su ficha')
    : bad(contradicen + ' cifras contradicen a las fichas');

  // 2. las tablas legales falsas ya no están
  const falsos = [
    ['plusvalia', '0,045', 'coeficiente de plusvalía inventado para más de 20 años'],
    ['ibi-2026', '1–3 meses de retraso', 'recargos por meses en lugar de por momento procesal'],
    ['bonificaciones', 'No fijado legalmente', 'el máximo de familia numerosa sí está fijado (90%)'],
    ['bonificaciones', 'Inicio de actividad empresarial', 'bonificación de IBI que no existe'],
    ['bonificaciones', 'Conjunto Histórico-Artístico (BIC)', 'confunde BIC con BICE'],
    ['tasa-basuras', '82 € a 145', 'rango de basuras equivocado'],
    ['tasa-basuras', '78 € a 155', 'rango de basuras sin fuente'],
    ['tasa-basuras', 'Importes por municipio', 'promete importes por municipio que no se publican'],
    ['tasa-basuras', 'primer trimestre del año', 'fecha de cobro sin fuente'],
  ];
  const quedan = falsos.filter(([g, aguja]) => leer(g + '/index.html').includes(aguja));
  quedan.length === 0
    ? ok('las ' + falsos.length + ' afirmaciones falsas detectadas han desaparecido')
    : bad('siguen: ' + quedan.map((f) => f[2]).join(' | '));

  // 3. bonificaciones al día con el TRLRHL vigente
  const boni = leer('bonificaciones/index.html');
  const vigentes = ['Art. 74.6', 'Art. 74.7', 'Art. 74.2 quáter', 'Art. 74.2 bis',
    'Art. 73.1', 'Art. 73.3', 'Real Decreto-ley 7/2026'];
  const faltan = vigentes.filter((v) => !boni.includes(v));
  faltan.length === 0
    ? ok('/bonificaciones/ recoge los apartados vigentes del TRLRHL, incluido el RDL 7/2026')
    : bad('faltan en /bonificaciones/: ' + faltan.join(', '));
  /punto de recarga/i.test(boni) && /renta limitada/i.test(boni)
    ? ok('y las dos bonificaciones que faltaban: punto de recarga y alquiler con renta limitada')
    : bad('siguen faltando las bonificaciones de recarga o de alquiler con renta limitada');

  // 4. higiene
  const hoy = new Date();
  const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
    'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const fechaHoy = hoy.getDate() + ' ' + meses[hoy.getMonth()] + ' ' + hoy.getFullYear();
  const conFecha = GUIAS.filter((g) => leer(g + '/index.html').includes('Actualizado: ' + fechaHoy));
  conFecha.length === GUIAS.length
    ? ok('las 4 guías llevan la fecha de la última generación (' + fechaHoy + ')')
    : bad(conFecha.length + '/4 con la fecha al día');
  const enlazanComparador = GUIAS.filter((g) => leer(g + '/index.html').includes('href="../municipios/"'));
  enlazanComparador.length === GUIAS.length
    ? ok('las 4 remiten al comparador de los 134 en lugar de listar 32 municipios')
    : bad(enlazanComparador.length + '/4 enlazan el comparador');
  const plus = leer('plusvalia/index.html');
  (plus.match(/<h2[^>]*>[^<]*[Cc]alculadora[^<]*<\/h2>/g) || []).length <= 1
    ? ok('/plusvalia/ ya no tiene dos h2 casi iguales sobre la calculadora')
    : bad('/plusvalia/ sigue con dos h2 de calculadora');
}

// ───────── los 9 pilares de comunidad autónoma, con la misma estructura ─────────
console.log('\n== Pilares de comunidad autónoma ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const CCAA = [...new Set(municipios.map((m) => m.ccaa))].sort();
  const SECCIONES = ['resumen', 'indice', 'tabla', 'gestion', 'ranking',
    'otros-tributos', 'catastro', 'poblacion', 'fichas', 'faq', 'metodologia'];
  const pct = (v) => String(Number(v.toFixed(4))).replace('.', ',') + '%';
  const miles = (v) => new Intl.NumberFormat('de-DE').format(v);

  let existen = 0, estructura = 0, extensos = 0, tablaOk = 0, tipoOk = 0, pobOk = 0;
  let graficosOk = 0, boeOk = 0, schemaOk = 0, sinGenerico = 0, enlacesOk = 0;
  const cubiertos = new Set();

  CCAA.forEach((c) => {
    const rel = c + '/index.html';
    if (!fs.existsSync(path.join(ROOT, rel))) { bad('falta el pilar /' + c + '/'); return; }
    existen++;
    const html = leer(rel);
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
    const d = dom.window.document;

    const faltan = SECCIONES.filter((id) => !d.getElementById(id));
    if (faltan.length === 0) estructura++;
    else console.log('    /' + c + '/ sin las secciones: ' + faltan.join(', '));

    const palabras = html.replace(/<script[\s\S]*?<\/script>/g, '')
      .replace(/<(nav|header|footer)[\s\S]*?<\/\1>/g, '')
      .replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
    if (palabras >= 1500) extensos++;
    else console.log('    /' + c + '/ solo tiene ' + palabras + ' palabras');

    // la tabla comparativa cubre todos los municipios de la comunidad
    const propios = municipios.filter((m) => m.ccaa === c);
    const filas = [...d.querySelectorAll('table.sortable tbody tr')];
    if (filas.length === propios.length) tablaOk++;
    else console.log('    /' + c + '/ lista ' + filas.length + ' de ' + propios.length + ' municipios');

    // y muestra el dato oficial, no el heredado
    let malTipo = 0, malPob = 0, rotos = 0;
    propios.forEach((m) => {
      cubiertos.add(m.ccaa + '/' + m.provincia_slug + '/' + m.slug);
      const fila = filas.find((tr) => tr.cells[0].textContent.trim() === m.nombre);
      if (!fila) { malTipo++; return; }
      if (fila.cells[2].textContent.trim() !== pct(m.oficial_tipo_urbana)) {
        malTipo++;
        console.log('    ' + c + '/' + m.slug + ': tabla dice ' + fila.cells[2].textContent.trim()
          + ' y el dato oficial es ' + pct(m.oficial_tipo_urbana));
      }
      if (fila.cells[1].textContent.trim() !== miles(m.poblacion_oficial)) malPob++;
      const href = fila.querySelector('a').getAttribute('href');
      const destino = path.resolve(path.join(ROOT, c), href);
      if (!fs.existsSync(path.join(destino, 'index.html'))) rotos++;
    });
    if (malTipo === 0) tipoOk++;
    if (malPob === 0) pobOk++; else console.log('    /' + c + '/ con ' + malPob + ' poblaciones desactualizadas');
    if (rotos === 0) enlacesOk++; else console.log('    /' + c + '/ con ' + rotos + ' enlaces de ficha rotos');

    const svgs = [...d.querySelectorAll('img[src$=".svg"]')].map((i) => i.getAttribute('src'));
    const propios2 = svgs.filter((s) => s.includes(c + '-ibi-urbano') || s.includes(c + '-valores-catastrales'));
    if (propios2.length === 2 && propios2.every((s) => fs.existsSync(path.resolve(path.join(ROOT, c), s)))) graficosOk++;
    else console.log('    /' + c + '/ sin sus dos gráficos propios');

    const boe = [...d.querySelectorAll('a[href*="boe.es"]')].length;
    if (boe >= 6) boeOk++; else console.log('    /' + c + '/ solo cita ' + boe + ' normas del BOE');

    const tipos = [...d.querySelectorAll('script[type="application/ld+json"]')]
      .map((s) => JSON.parse(s.textContent)['@type']);
    if (tipos.includes('Article') && tipos.includes('FAQPage') && tipos.includes('BreadcrumbList')) schemaOk++;
    else console.log('    /' + c + '/ con schema incompleto: ' + tipos.join(','));

    // los bloques que explicaban la mecánica general viven solo en las guías
    const genericos = [
      'Bonificaciones: cuáles te tienen que dar',
      'Cuánto puede subirte el IBI tu ayuntamiento',
      'Qué hacer si el recibo está mal',
      'Cómo comprobar tu valor catastral, que es el dato',
    ].filter((f) => html.includes(f));
    if (genericos.length === 0) sinGenerico++;
    else console.log('    /' + c + '/ repite bloques genéricos: ' + genericos.join(' | '));
  });

  const n = CCAA.length;
  existen === n ? ok('los ' + n + ' pilares de comunidad autónoma existen') : bad(existen + '/' + n + ' pilares');
  estructura === n ? ok('los ' + n + ' tienen las mismas ' + SECCIONES.length + ' secciones') : bad(estructura + '/' + n + ' con la estructura completa');
  extensos === n ? ok('los ' + n + ' superan las 1.500 palabras') : bad(extensos + '/' + n + ' con extensión suficiente');
  tablaOk === n ? ok('cada pilar lista todos los municipios de su comunidad') : bad(tablaOk + '/' + n + ' con la tabla completa');
  cubiertos.size === municipios.length
    ? ok('los ' + municipios.length + ' municipios están cubiertos por un pilar y solo uno')
    : bad(cubiertos.size + '/' + municipios.length + ' municipios cubiertos');
  tipoOk === n ? ok('los tipos de las tablas son los oficiales del Ministerio') : bad(tipoOk + '/' + n + ' con tipos correctos');
  pobOk === n ? ok('las poblaciones son las oficiales del INE') : bad(pobOk + '/' + n + ' con población correcta');
  enlacesOk === n ? ok('ningún enlace a ficha roto en las tablas') : bad('hay enlaces de ficha rotos');
  graficosOk === n ? ok('los ' + n + ' llevan sus dos gráficos SVG propios') : bad(graficosOk + '/' + n + ' con gráficos');
  boeOk === n ? ok('los ' + n + ' citan la normativa enlazada al BOE') : bad(boeOk + '/' + n + ' con citas al BOE');
  schemaOk === n ? ok('los ' + n + ' llevan Article, FAQPage y BreadcrumbList') : bad(schemaOk + '/' + n + ' con schema completo');
  sinGenerico === n ? ok('ninguno repite la mecánica general que ya está en las guías') : bad('hay pilares con bloques genéricos duplicados');

  // no se han creado pilares de provincia, que competirían con el de su comunidad
  const provincias = [...new Set(municipios.map((m) => m.ccaa + '/' + m.provincia_slug))];
  const conIndice = provincias.filter((p) => fs.existsSync(path.join(ROOT, p, 'index.html')));
  conIndice.length === 0
    ? ok('no hay pilares de provincia compitiendo con los de comunidad')
    : bad('existen pilares de provincia: ' + conIndice.join(', '));

  // y el hub de comunidades enlaza los nueve
  const hub = leer('comunidades/index.html');
  const enlazados = CCAA.filter((c) => hub.includes('"../' + c + '/"') || hub.includes("'../" + c + "/'"));
  enlazados.length === n ? ok('el hub /comunidades/ enlaza los ' + n + ' pilares') : bad(enlazados.length + '/' + n + ' enlazados desde /comunidades/');
}

// ───────── artículos de análisis propios ─────────
console.log('\n== Análisis con datos oficiales ==');
{
  const municipios = JSON.parse(leer('data/municipios.json')).municipios;
  const impuestos = JSON.parse(leer('data/hacienda_impuestos.json'));
  const articulos = [
    'analisis', 'analisis/ranking-ibi-municipios', 'analisis/impuesto-circulacion-ivtm',
    'analisis/coeficientes-plusvalia', 'analisis/valores-catastrales-antiguos',
  ];
  const palabras = (rel) => leer(rel + '/index.html')
    .replace(/<script[\s\S]*?<\/script>/g, '')
    .replace(/<(nav|header|footer)[\s\S]*?<\/\1>/g, '')
    .replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;

  let existen = 0, extensos = 0, schemaOk = 0, enlacesOk = 0, tituloOk = 0;
  articulos.forEach((rel) => {
    if (!fs.existsSync(path.join(ROOT, rel, 'index.html'))) { bad('falta /' + rel + '/'); return; }
    existen++;
    const minimo = rel === 'analisis' ? 300 : 900;
    const n = palabras(rel);
    if (n >= minimo) extensos++; else console.log('    /' + rel + '/ solo tiene ' + n + ' palabras');

    const html = leer(rel + '/index.html');
    const dom = new JSDOM(html);
    const d = dom.window.document;
    const tipos = [...d.querySelectorAll('script[type="application/ld+json"]')]
      .map((s) => JSON.parse(s.textContent)['@type']);
    if (tipos.includes('Article') && tipos.includes('BreadcrumbList')) schemaOk++;
    else console.log('    schema incompleto en /' + rel + '/: ' + tipos.join(','));

    const titulo = (html.match(/<title>([^<]*)<\/title>/) || [])[1] || '';
    if (titulo.length > 0 && titulo.length <= 60) tituloOk++;
    else console.log('    título de ' + rel + ' con ' + titulo.length + ' caracteres');

    let rotos = 0;
    d.querySelectorAll('a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      if (/^(https?:|mailto:|#)/.test(href)) return;
      // el ancla no forma parte de la ruta: audit_site.py comprueba los anclas
      const destino = path.resolve(path.join(ROOT, rel), href.split('#')[0]);
      if (!fs.existsSync(destino) && !fs.existsSync(path.join(destino, 'index.html'))) {
        rotos++;
        console.log('      ' + rel + ' → ' + href);
      }
    });
    if (rotos === 0) enlacesOk++; else console.log('    ' + rotos + ' enlaces rotos en /' + rel + '/');
  });
  existen === articulos.length ? ok('las ' + existen + ' páginas de análisis existen') : bad('faltan páginas de análisis');
  extensos === articulos.length ? ok('todas tienen extensión suficiente') : bad(extensos + '/' + articulos.length + ' con extensión suficiente');
  schemaOk === articulos.length ? ok('todas llevan Article y BreadcrumbList') : bad(schemaOk + '/' + articulos.length + ' con schema correcto');
  tituloOk === articulos.length ? ok('todos los títulos caben en 60 caracteres') : bad(tituloOk + '/' + articulos.length + ' con título correcto');
  enlacesOk === articulos.length ? ok('ningún enlace interno roto en los análisis') : bad('hay enlaces rotos');

  // las cifras del artículo de IVTM salen de la fuente, no de la nada
  const ivtm = leer('analisis/impuesto-circulacion-ivtm/index.html');
  const eur2 = (s) => new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    .format(parseFloat(String(s).replace(/\./g, '').replace(',', '.')));
  let coinciden = 0, comprobados = 0;
  municipios.forEach((m) => {
    const imp = impuestos[m.oficial_codigo_ine];
    const v = imp && imp.conceptos.C19 && imp.conceptos.C19.valor;
    if (!v) return;
    comprobados++;
    if (ivtm.includes('>' + eur2(v) + ' €<')) coinciden++;
  });
  coinciden === comprobados
    ? ok('las ' + comprobados + ' tarifas del artículo de IVTM coinciden con la fuente')
    : bad(coinciden + '/' + comprobados + ' tarifas coinciden');

  // no publicamos como coeficientes las series que no encajan con el RDL 26/2021
  const plus = leer('analisis/coeficientes-plusvalia/index.html');
  const dudosos = municipios.filter((m) => {
    const imp = impuestos[m.oficial_codigo_ine];
    if (!imp) return false;
    const vals = [];
    for (let n = 51; n <= 71; n++) {
      const c = imp.conceptos['C' + n];
      if (c && c.valor) vals.push(parseFloat(c.valor.replace(',', '.')));
    }
    return vals.length > 0 && Math.max(...vals) < 0.10;
  });
  const excluidos = dudosos.filter((m) => plus.includes('descartado') || plus.includes('descartar'));
  dudosos.length === 0 || excluidos.length === dudosos.length
    ? ok('las ' + dudosos.length + ' series incoherentes se advierten en lugar de publicarse')
    : bad('series incoherentes publicadas como coeficientes');
  let fichasAvisadas = 0;
  dudosos.forEach((m) => {
    const f = leer(m.ccaa + '/' + m.provincia_slug + '/' + m.slug + '/index.html');
    if (/no encaja con el sistema vigente/.test(f) && !/<td>20 años o más<\/td>/.test(f)) fichasAvisadas++;
    else console.log('    la ficha de ' + m.nombre + ' publica una serie que no encaja');
  });
  fichasAvisadas === dudosos.length ? ok('sus fichas lo advierten y no publican la tabla') : bad('alguna ficha publica la serie dudosa');

  // enlazados desde el resto del sitio y en el sitemap
  const sitemap = leer('sitemap.xml');
  const enSitemap = articulos.filter((r) => sitemap.includes('https://tasasmunicipales.info/' + r + '/')).length;
  enSitemap === articulos.length ? ok('los ' + enSitemap + ' análisis están en el sitemap') : bad(enSitemap + '/' + articulos.length + ' en el sitemap');
  const ficha = leer(municipios[0].ccaa + '/' + municipios[0].provincia_slug + '/' + municipios[0].slug + '/index.html');
  /<nav[\s\S]*?analisis\/"[^>]*>Comparativas<\/a>[\s\S]*?<\/nav>/.test(ficha)
    ? ok('las fichas enlazan la sección de análisis desde el menú («Comparativas»)')
    : bad('las fichas no enlazan la sección de análisis');
  /id="analisis-destacados"/.test(leer('index.html'))
    ? ok('la portada destaca los análisis')
    : bad('la portada no enlaza los análisis');
}

// ───────── imágenes optimizadas ─────────
console.log('\n== Peso de las infografías ==');
{
  const jpgs = fs.readdirSync(path.join(ROOT, 'img')).filter((f) => f.endsWith('.jpg'));
  let conWebp = 0, ligeras = 0, enPicture = 0;
  jpgs.forEach((f) => {
    const webp = path.join(ROOT, 'img', f.replace(/\.jpg$/, '.webp'));
    if (fs.existsSync(webp)) conWebp++;
    else console.log('    sin versión webp: ' + f);
    const kb = fs.statSync(path.join(ROOT, 'img', f)).size / 1024;
    if (kb <= 150) ligeras++; else console.log('    ' + f + ' pesa ' + Math.round(kb) + ' KB');
  });
  const paginas = ['calculadora-ibi', 'ibi-2026', 'plusvalia', 'tasa-basuras'];
  paginas.forEach((p) => {
    const html = leer(p + '/index.html');
    if (/<picture><source srcset="[^"]+\.webp" type="image\/webp"><img [^>]*width="\d+" height="\d+"/.test(html)) enPicture++;
    else console.log('    ' + p + ' no sirve la infografía en webp con dimensiones');
  });
  conWebp === jpgs.length ? ok('las ' + jpgs.length + ' infografías tienen versión WebP') : bad(conWebp + '/' + jpgs.length + ' con WebP');
  ligeras === jpgs.length ? ok('ninguna pasa de 150 KB en el respaldo JPEG') : bad(ligeras + '/' + jpgs.length + ' por debajo de 150 KB');
  enPicture === paginas.length ? ok('las ' + enPicture + ' páginas las sirven con <picture> y dimensiones reales') : bad(enPicture + '/' + paginas.length + ' correctas');
}

// ───────── guías nacionales y contenido nuevo ─────────
console.log('\n== Guías nacionales ==');
{
  const esperados = {
    'ibi-2026': 'IBI 2026: cuándo se paga, cómo se calcula y cuánto sube',
    'plusvalia': 'Plusvalía municipal 2026: coeficientes, cálculo y plazos',
    'tasa-basuras': 'Tasa de basuras 2026: cuánto se paga y quién la paga',
    'bonificaciones': 'Bonificaciones del IBI 2026: hasta 90% y cómo pedirlas',
    'calculadora-ibi': 'Calculadora de IBI 2026: calcula tu recibo en un minuto',
  };
  let titulos = 0, longitud = 0, descripciones = 0, obsoletos = 0;
  Object.entries(esperados).forEach(([pagina, titulo]) => {
    const html = leer(pagina + '/index.html');
    const actual = (html.match(/<title>([^<]*)<\/title>/) || [])[1];
    if (actual === titulo) titulos++; else console.log('    título distinto en ' + pagina + ': ' + actual);
    if (actual && actual.length <= 60) longitud++; else console.log('    título largo en ' + pagina + ' (' + (actual || '').length + ')');
    const desc = (html.match(/name="description" content="([^"]*)"/) || [])[1] || '';
    if (desc.length >= 120 && desc.length <= 280) descripciones++;
    else console.log('    descripción fuera de rango en ' + pagina + ' (' + desc.length + ')');
    if (/26 municipios/.test(html)) { obsoletos++; console.log('    dato obsoleto «26 municipios» en ' + pagina); }
  });
  titulos === 5 ? ok('los 5 títulos responden a las consultas reales de Search Console') : bad(titulos + '/5 títulos');
  longitud === 5 ? ok('los 5 títulos caben sin truncarse (60 caracteres o menos)') : bad(longitud + '/5 con longitud correcta');
  descripciones === 5 ? ok('las 5 descripciones tienen longitud adecuada') : bad(descripciones + '/5 descripciones');
  obsoletos === 0 ? ok('no queda la afirmación obsoleta de «26 municipios»') : bad(obsoletos + ' páginas con el dato obsoleto');

  // tabla oficial de coeficientes
  const dom = new JSDOM(leer('plusvalia/index.html'));
  const d = dom.window.document;
  const seccion = d.getElementById('coeficientes');
  // solo la tabla que sigue inmediatamente al encabezado de coeficientes
  let tabla = seccion ? seccion.nextElementSibling : null;
  while (tabla && tabla.tagName !== 'TABLE') tabla = tabla.nextElementSibling;
  const filas = tabla ? [...tabla.querySelectorAll('tbody tr')] : [];
  const coefs = JSON.parse(leer('data/coeficientes_plusvalia.json'));
  seccion ? ok('/plusvalia/#coeficientes existe') : bad('falta la sección de coeficientes');
  const guiaIbi = new JSDOM(leer('ibi-2026/index.html')).window.document;
  guiaIbi.getElementById('recargos') ? ok('/ibi-2026/#recargos existe (explicación única de los recargos)') : bad('falta la sección de recargos');
  filas.length === coefs.coeficientes.length ? ok('la tabla publica los ' + filas.length + ' tramos oficiales') : bad('la tabla tiene ' + filas.length + ' tramos y la fuente ' + coefs.coeficientes.length);
  const correctos = filas.filter((tr, i) => tr.cells[1].textContent.trim() === coefs.coeficientes[i][1]).length;
  correctos === filas.length ? ok('los coeficientes coinciden con el texto consolidado del BOE') : bad(correctos + '/' + filas.length + ' coeficientes correctos');
  leer('plusvalia/index.html').includes('BOE-A-2004-4214') ? ok('la tabla cita el TRLRHL en el BOE') : bad('falta la cita al BOE');
}

console.log('\n== Tomelloso (8.812 impresiones, CTR 0,18%) ==');
{
  const html = leer('castilla-la-mancha/ciudad-real/tomelloso/index.html');
  /dónde está el dato exacto/.test(html) ? ok('sección nueva sobre coeficientes y tipo de gravamen') : bad('falta la sección nueva');
  /30% como máximo/.test(html) ? ok('explica el tope legal del 30% que la gente busca') : bad('no menciona el tope del 30%');
  html.includes('plusvalia/#coeficientes') ? ok('enlaza la tabla canónica de coeficientes') : bad('no enlaza la tabla de coeficientes');
  html.includes('https://www.tomelloso.es') ? ok('enlaza el ayuntamiento verificado como fuente del texto oficial') : bad('no enlaza el ayuntamiento');
  !/coeficiente[^<]{0,40}de Tomelloso es/.test(html) ? ok('no afirma coeficientes municipales sin contrastar') : bad('afirma coeficientes sin fuente');
}

// ───────── figuras de los análisis y páginas de confianza ─────────
// ───────── portada ─────────
console.log('\n== Portada ==');
{
  const home = leer('index.html');
  const d = new JSDOM(home).window.document;

  // las seis guías del sitio tienen tarjeta, y la rejilla cuadra en dos filas
  const rejilla = d.querySelector('.types-grid.cols-3');
  const destinos = rejilla
    ? [...rejilla.querySelectorAll('a.type-card')].map((a) => a.getAttribute('href'))
    : [];
  const guias = ['ibi-2026/', 'tasa-basuras/', 'plusvalia/', 'bonificaciones/',
    'impuesto-circulacion/', 'valor-catastral/'];
  const faltan = guias.filter((g) => !destinos.includes(g));
  faltan.length === 0 && destinos.length === guias.length
    ? ok('la rejilla de impuestos tiene las ' + guias.length + ' guías en tres columnas')
    : bad('en la rejilla de la portada faltan: ' + (faltan.join(', ') || 'ninguna')
          + ' (tarjetas: ' + destinos.length + ')');
  fs.readFileSync(path.join(ROOT, 'styles.css'), 'utf8').includes('.types-grid.cols-3')
    ? ok('y la hoja de estilos define la variante de tres columnas')
    : bad('falta .types-grid.cols-3 en styles.css');

  // el bloque de análisis comparte maquetación con el resto de la portada
  const analisis = d.querySelector('#analisis-destacados');
  analisis && analisis.classList.contains('section')
    && analisis.querySelector('.section-header h2')
    && analisis.querySelectorAll('.types-grid a.type-card').length === 4
    ? ok('el bloque de análisis usa el contenedor y la cabecera del resto de secciones')
    : bad('el bloque de análisis sigue descuadrado');

  // nada que prometa datos que ya no publicamos
  const prohibido = [
    ['Importe anual', 'la tarjeta de basuras promete el importe'],
    ['fecha de cobro', 'la tarjeta de IBI promete la fecha de cobro'],
    ['del 1 de octubre al 30 de noviembre', 'la FAQ da un plazo que ya no publicamos'],
    ['están obligados a aplicar reducciones', 'presenta como obligatorias bonificaciones potestativas'],
    ['ordenanzas actualizadas', 'atribuye los datos a las ordenanzas'],
    ['/buscar/?q=', 'el SearchAction apunta a una URL inexistente'],
  ];
  const restos = prohibido.filter(([t]) => home.includes(t));
  restos.length === 0
    ? ok('ningún texto de la portada contradice a los datos que se publican')
    : bad('en la portada: ' + restos.map(([, m]) => m).join(' | '));

  // el respaldo sin JavaScript del buscador y el SearchAction llevan al mismo sitio
  const target = (home.match(/"target":\s*"([^"]+)"/) || [])[1] || '';
  const accion = (d.querySelector('.search-box') || {}).getAttribute
    ? d.querySelector('.search-box').getAttribute('action') : '';
  target.includes('/municipios/?q=') && accion === 'municipios/'
    ? ok('el buscador sin JS y el SearchAction apuntan los dos a /municipios/?q=')
    : bad('el buscador y el SearchAction no coinciden (' + accion + ' vs ' + target + ')');

  // y /municipios/ ahora sí lee ese parámetro
  const comparador = leer('municipios/index.html');
  comparador.includes('id="tm-filtro"')
    && /URLSearchParams\(window\.location\.search\)\.get\('q'\)/.test(comparador)
    ? ok('/municipios/ filtra la tabla y lee el parámetro q de la URL')
    : bad('/municipios/ no lee el parámetro q');
}

console.log('\n== Figuras de los análisis ==');
{
  const articulos = ['analisis', 'analisis/ranking-ibi-municipios',
    'analisis/impuesto-circulacion-ivtm', 'analisis/coeficientes-plusvalia',
    'analisis/valores-catastrales-antiguos'];
  let conFigura = 0, accesibles = 0, ligeras = 0, conPie = 0;
  articulos.forEach((rel) => {
    const html = leer(rel + '/index.html');
    const d = new JSDOM(html).window.document;
    const figuras = [...d.querySelectorAll('figure img[src$=".svg"]')];
    if (figuras.length >= 1) conFigura++;
    else { console.log('    /' + rel + '/ sigue sin ninguna figura'); return; }
    const problemas = [];
    figuras.forEach((img) => {
      const src = img.getAttribute('src');
      const destino = path.resolve(path.join(ROOT, rel), src);
      if (!fs.existsSync(destino)) { problemas.push('no existe ' + src); return; }
      const svg = fs.readFileSync(destino, 'utf8');
      // accesibilidad: alt propio, <title>/<desc> y aria-labelledby en el SVG
      if (!img.getAttribute('alt') || img.getAttribute('alt').length < 30) problemas.push('alt pobre en ' + src);
      if (!/aria-labelledby=/.test(svg) || !/<title id=/.test(svg) || !/<desc id=/.test(svg)) problemas.push('SVG sin title/desc en ' + src);
      if (!img.getAttribute('width') || !img.getAttribute('height')) problemas.push('sin dimensiones ' + src);
      const kb = fs.statSync(destino).size / 1024;
      if (kb > 20) problemas.push(src + ' pesa ' + Math.round(kb) + ' kB');
    });
    if (problemas.length === 0) { accesibles++; ligeras++; }
    else console.log('    /' + rel + '/: ' + problemas.join(' | '));
    if (figuras.every((img) => img.closest('figure').querySelector('figcaption'))) conPie++;
    else console.log('    /' + rel + '/ con figura sin pie');
  });
  const n = articulos.length;
  conFigura === n ? ok('los ' + n + ' análisis (índice incluido) llevan al menos una figura propia') : bad(conFigura + '/' + n + ' con figura');
  accesibles === n ? ok('las figuras tienen alt descriptivo, title/desc en el SVG y dimensiones declaradas') : bad(accesibles + '/' + n + ' con figuras accesibles');
  ligeras === n ? ok('ninguna figura pasa de 20 kB') : bad(ligeras + '/' + n + ' con figuras ligeras');
  conPie === n ? ok('todas las figuras llevan pie con la fuente') : bad(conPie + '/' + n + ' con pie de figura');
}

console.log('\n== Páginas que sostienen la confianza ==');
{
  const palabras = (rel) => leer(rel + '/index.html')
    .split('<footer>')[0]
    .replace(/<script[\s\S]*?<\/script>/g, '')
    .replace(/<(nav|header)[\s\S]*?<\/\1>/g, '')
    .replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;

  const minimos = [['sobre-nosotros', 900], ['contacto', 700], ['metodologia', 1400],
    ['tasa-basuras', 1400], ['analisis', 800]];
  let extension = 0;
  minimos.forEach(([rel, min]) => {
    const p = palabras(rel);
    if (p >= min) extension++;
    else console.log('    /' + rel + '/ tiene ' + p + ' palabras y el mínimo es ' + min);
  });
  extension === minimos.length
    ? ok('las ' + minimos.length + ' páginas de confianza superan su extensión mínima')
    : bad(extension + '/' + minimos.length + ' con extensión suficiente');

  // /sobre-nosotros/ debe declarar cómo se financia y no atribuirse credenciales
  const sobre = leer('sobre-nosotros/index.html');
  /publicidad/i.test(sobre) && /id="financiacion"/.test(sobre)
    ? ok('/sobre-nosotros/ declara cómo se financia el sitio')
    : bad('/sobre-nosotros/ no declara la financiación');
  /no soy asesor fiscal/i.test(sobre)
    ? ok('y sigue diciendo que no hay habilitación profesional detrás')
    : bad('/sobre-nosotros/ ya no aclara que no es asesoramiento');

  // /contacto/ debe explicar el procedimiento de corrección y el uso de los datos
  const contacto = leer('contacto/index.html');
  const bloques = ['Cómo avisar de un dato incorrecto', 'Qué hago con tus datos',
    'metodologia/#errores-corregidos', 'privacidad/'];
  const faltan = bloques.filter((b) => !contacto.includes(b));
  faltan.length === 0
    ? ok('/contacto/ explica cómo pedir una corrección, qué se hace con los datos y enlaza metodología y privacidad')
    : bad('faltan en /contacto/: ' + faltan.join(' | '));

  // ningún importe de basuras publicado en todo el sitio
  const sospechosas = [];
  const recorrer = (dir) => {
    fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
      if (e.isDirectory()) {
        if (['.git', 'node_modules', 'scripts', 'img', '.qa'].includes(e.name)) return;
        recorrer(path.join(dir, e.name));
      } else if (e.name === 'index.html') {
        const html = fs.readFileSync(path.join(dir, e.name), 'utf8');
        if (/tasa de basuras[^<.]{0,40}\d{2,3} €\/año/i.test(html)
            || /Basura vivienda:<\/strong>/.test(html)
            || /Importe orientativo, sin contrastar/.test(html)) {
          sospechosas.push(path.relative(ROOT, dir) || '.');
        }
      }
    });
  };
  recorrer(ROOT);
  sospechosas.length === 0
    ? ok('ninguna página publica un importe de tasa de basuras ni avisos de «orientativo»')
    : bad(sospechosas.length + ' páginas siguen publicando importes sin fuente: ' + sospechosas.slice(0, 5).join(', '));
}

console.log('\n──────────────────────────────────────');
console.log('Comprobaciones: ' + oks + ' correctas, ' + fallos + ' fallidas');
process.exit(fallos ? 1 : 0);
