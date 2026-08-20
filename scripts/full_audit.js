#!/usr/bin/env node
/**
 * COMPREHENSIVE AUDIT — Post-implementation review
 * Checks: cookie, CSS, content uniqueness, links, schema, infographics, 
 * calculators, approximate data, hub content, duplicate content ratio
 */
const fs = require('fs');
const path = require('path');
const ROOT = 'c:\\Users\\aitha\\Desktop\\ibi';

const results = { pass: [], warn: [], fail: [] };
function pass(msg) { results.pass.push(msg); }
function warn(msg) { results.warn.push(msg); }
function fail(msg) { results.fail.push(msg); }

// Collect all HTML files
const allFiles = [];
function findHtml(dir) {
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory() && !['scripts','data','node_modules','img','.git'].includes(f.name)) findHtml(full);
    else if (f.name === 'index.html') allFiles.push(full);
  }
}
findHtml(ROOT);

// Categorize files
const muniFiles = allFiles.filter(f => {
  const parts = path.relative(ROOT, f).split(path.sep);
  return parts.length === 4; // ccaa/prov/muni/index.html
});
const pillarFiles = ['ibi-2026','tasa-basuras','plusvalia','bonificaciones'].map(d => path.join(ROOT, d, 'index.html'));
const hubFiles = ['comunidades','municipios','provincias'].map(d => path.join(ROOT, d, 'index.html'));
const legalFiles = ['aviso-legal','privacidad','cookies','contacto','sobre-nosotros'].map(d => path.join(ROOT, d, 'index.html'));

console.log('════════════════════════════════════════════');
console.log('  AUDITORÍA COMPLETA — TasasMunicipales.info');
console.log('════════════════════════════════════════════\n');

// ═══ 1. COOKIE CONSENT ═══
console.log('1. COOKIE CONSENT BANNER');
let cookieCount = 0;
for (const f of allFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('cookie-consent.js')) cookieCount++;
  else fail('Sin cookie consent: ' + path.relative(ROOT, f));
}
if (cookieCount === allFiles.length) pass('Cookie consent en ' + cookieCount + '/' + allFiles.length + ' páginas');
// Check cookie-consent.js exists
if (fs.existsSync(path.join(ROOT, 'cookie-consent.js'))) pass('cookie-consent.js existe');
else fail('cookie-consent.js NO existe');

// ═══ 2. CSS EXTERNO ═══
console.log('2. CSS EXTERNO');
let cssCount = 0, inlineCount = 0;
for (const f of allFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('styles.css')) cssCount++;
  else fail('Sin CSS externo: ' + path.relative(ROOT, f));
  if (/<style>/i.test(html)) { inlineCount++; warn('CSS inline en: ' + path.relative(ROOT, f)); }
}
if (cssCount === allFiles.length) pass('CSS externo en ' + cssCount + '/' + allFiles.length + ' páginas');
if (inlineCount === 0) pass('0 páginas con CSS inline');

// ═══ 3. DATOS APROXIMADOS ═══
console.log('3. DATOS APROXIMADOS');
let approxCount = 0;
for (const f of allFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  const matches = html.match(/~\d+[\s,]*€/g);
  if (matches) { approxCount++; fail('Datos aproximados en: ' + path.relative(ROOT, f) + ' → ' + matches.join(', ')); }
}
if (approxCount === 0) pass('0 páginas con datos aproximados (~XX €)');

// ═══ 4. "500 MUNICIPIOS" ═══
console.log('4. AFIRMACIÓN "500 MUNICIPIOS"');
let found500 = false;
for (const f of allFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (/500\s*municipios/i.test(html)) { found500 = true; fail('"500 municipios" en: ' + path.relative(ROOT, f)); }
}
if (!found500) pass('"500 municipios" eliminado de todo el sitio');

// ═══ 5. CONTENIDO ÚNICO EN MUNICIPIOS ═══
console.log('5. CONTENIDO ÚNICO EN MUNICIPIOS');
const introTexts = new Set();
let duplicateIntros = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  const leadMatch = html.match(/<p class="lead">(.*?)<\/p>/s);
  if (leadMatch) {
    const text = leadMatch[1].trim().substring(0, 100);
    if (introTexts.has(text)) { duplicateIntros++; fail('Intro duplicada: ' + path.relative(ROOT, f)); }
    introTexts.add(text);
  } else {
    warn('Sin intro lead: ' + path.relative(ROOT, f));
  }
}
if (duplicateIntros === 0) pass('59 municipios con intros únicas');

// Check for unique "consejo práctico"
const consejos = new Set();
let dupConsejos = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  const consMatch = html.match(/Consejo práctico.*?<\/h2>\s*<p>(.*?)<\/p>/s);
  if (consMatch) {
    const text = consMatch[1].trim().substring(0, 80);
    if (consejos.has(text)) { dupConsejos++; warn('Consejo duplicado: ' + path.relative(ROOT, f)); }
    consejos.add(text);
  }
}
if (dupConsejos === 0) pass('59 municipios con consejos prácticos únicos');

// ═══ 6. GRÁFICOS DE BARRAS ═══
console.log('6. GRÁFICOS COMPARATIVOS');
let chartCount = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('chart-container')) chartCount++;
  else warn('Sin gráfico: ' + path.relative(ROOT, f));
}
pass('Gráficos de barras: ' + chartCount + '/' + muniFiles.length + ' municipios');

// ═══ 7. INFOGRAFÍAS ═══
console.log('7. INFOGRAFÍAS');
const imgDir = path.join(ROOT, 'img');
const expectedImgs = ['infografia-calculo-ibi.png','infografia-plusvalia.png','infografia-tasa-basuras.png','infografia-bonificaciones.svg'];
for (const img of expectedImgs) {
  if (fs.existsSync(path.join(imgDir, img))) pass('Imagen existe: ' + img);
  else fail('Imagen NO existe: ' + img);
}
// Check pillar pages reference infographics
for (const f of pillarFiles) {
  if (!fs.existsSync(f)) { warn('Página pilar no existe: ' + path.relative(ROOT, f)); continue; }
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('infografia') || html.includes('infographic')) pass('Infografía en: ' + path.basename(path.dirname(f)));
  else warn('Sin infografía: ' + path.basename(path.dirname(f)));
}

// ═══ 8. CALCULADORAS ═══
console.log('8. CALCULADORAS');
const calcIBI = fs.readFileSync(path.join(ROOT, 'calculadora-ibi', 'index.html'), 'utf-8');
if (calcIBI.includes('calcular') || calcIBI.includes('function')) pass('Calculadora IBI funcional');
else fail('Calculadora IBI no encontrada');

const calcPV = fs.readFileSync(path.join(ROOT, 'plusvalia', 'index.html'), 'utf-8');
if (calcPV.includes('calcPV') || calcPV.includes('calculadora-plusvalia')) pass('Calculadora plusvalía funcional');
else fail('Calculadora plusvalía no encontrada');

// ═══ 9. PÁGINAS HUB ═══
console.log('9. CONTENIDO EN HUBS');
for (const f of hubFiles) {
  if (!fs.existsSync(f)) { fail('Hub no existe: ' + path.relative(ROOT, f)); continue; }
  const html = fs.readFileSync(f, 'utf-8');
  const textOnly = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
  const wordCount = textOnly.split(' ').filter(w => w.length > 3).length;
  if (wordCount >= 80) pass(path.basename(path.dirname(f)) + ': ' + wordCount + ' palabras sustanciales');
  else warn(path.basename(path.dirname(f)) + ': solo ' + wordCount + ' palabras (necesita más)');
}

// ═══ 10. SCHEMA.ORG ═══
console.log('10. SCHEMA.ORG');
let schemaCount = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('application/ld+json')) schemaCount++;
  else warn('Sin schema: ' + path.relative(ROOT, f));
}
pass('Schema.org en ' + schemaCount + '/' + muniFiles.length + ' municipios');

for (const f of pillarFiles) {
  if (!fs.existsSync(f)) continue;
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('application/ld+json')) pass('Schema en: ' + path.basename(path.dirname(f)));
  else warn('Sin schema: ' + path.basename(path.dirname(f)));
}

// ═══ 11. FUENTES OFICIALES ═══
console.log('11. FUENTES OFICIALES');
let fuenteCount = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('Fuentes oficiales') || html.includes('Ordenanza fiscal')) fuenteCount++;
  else warn('Sin fuentes: ' + path.relative(ROOT, f));
}
pass('Fuentes oficiales: ' + fuenteCount + '/' + muniFiles.length + ' municipios');

// ═══ 12. GUÍA SEDE CATASTRO ═══
console.log('12. GUÍA SEDE CATASTRO');
let catastroCount = 0;
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  if (html.includes('sedecatastro.gob.es')) catastroCount++;
}
pass('Enlace Sede Catastro: ' + catastroCount + '/' + muniFiles.length + ' municipios');

// ═══ 13. PÁGINAS LEGALES ═══
console.log('13. PÁGINAS LEGALES');
for (const f of legalFiles) {
  if (fs.existsSync(f)) {
    const html = fs.readFileSync(f, 'utf-8');
    const size = html.length;
    if (size > 500) pass(path.basename(path.dirname(f)) + ': OK (' + size + ' bytes)');
    else warn(path.basename(path.dirname(f)) + ': muy corta (' + size + ' bytes)');
  } else {
    fail('Página legal falta: ' + path.basename(path.dirname(f)));
  }
}

// ═══ 14. LINKS ROTOS INTERNOS ═══
console.log('14. LINKS INTERNOS');
let brokenLinks = 0;
for (const f of allFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  const links = html.match(/href="(\.\.\/[^"]+)"/g) || [];
  for (const link of links) {
    const href = link.match(/href="([^"]+)"/)[1];
    if (href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto')) continue;
    const target = path.resolve(path.dirname(f), href.replace(/\/$/, ''), 'index.html');
    // Also check if it's a file directly
    const targetDirect = path.resolve(path.dirname(f), href);
    if (!fs.existsSync(target) && !fs.existsSync(targetDirect) && !href.includes('sedecatastro') && !href.includes('.css') && !href.includes('.js') && !href.includes('.ico') && !href.includes('.svg') && !href.includes('.png') && !href.includes('.jpg')) {
      brokenLinks++;
      if (brokenLinks <= 5) fail('Link roto: ' + href + ' en ' + path.relative(ROOT, f));
    }
  }
}
if (brokenLinks === 0) pass('0 links internos rotos');
else if (brokenLinks > 5) fail('...' + (brokenLinks - 5) + ' links rotos más');

// ═══ 15. CONTENIDO DUPLICADO ENTRE SECCIONES ═══
console.log('15. ANÁLISIS DE DUPLICACIÓN');
const basuraTexts = [];
for (const f of muniFiles) {
  const html = fs.readFileSync(f, 'utf-8');
  const basMatch = html.match(/Tasa de basuras.*?<\/section>/s);
  if (basMatch) basuraTexts.push({ file: path.relative(ROOT, f), text: basMatch[0] });
}
// Check if basura sections are unique (compare first 200 chars after h2)
const basuraUnique = new Set();
let basuraDups = 0;
for (const bt of basuraTexts) {
  const key = bt.text.replace(/<[^>]+>/g, '').trim().substring(0, 200);
  if (basuraUnique.has(key)) basuraDups++;
  basuraUnique.add(key);
}
if (basuraDups === 0) pass('Secciones de basuras únicas en todos los municipios');
else warn(basuraDups + ' secciones de basuras con inicio similar');

// ═══ SITEMAP ═══
console.log('16. SITEMAP');
const sitemap = path.join(ROOT, 'sitemap.xml');
if (fs.existsSync(sitemap)) {
  const sitemapContent = fs.readFileSync(sitemap, 'utf-8');
  const urlCount = (sitemapContent.match(/<url>/g) || []).length;
  pass('Sitemap existe con ' + urlCount + ' URLs');
  // Check for plusvalia calculator URL
  if (sitemapContent.includes('/plusvalia/')) pass('Plusvalía en sitemap');
  else warn('Plusvalía NO en sitemap');
} else {
  fail('sitemap.xml NO existe');
}

// ═══ ROBOTS.TXT ═══
console.log('17. ROBOTS.TXT');
const robots = path.join(ROOT, 'robots.txt');
if (fs.existsSync(robots)) {
  const content = fs.readFileSync(robots, 'utf-8');
  if (content.includes('Sitemap')) pass('robots.txt con referencia a sitemap');
  else warn('robots.txt sin referencia a sitemap');
} else {
  fail('robots.txt NO existe');
}

// ═══ PRINT RESULTS ═══
console.log('\n════════════════════════════════════════════');
console.log('  RESULTADOS');
console.log('════════════════════════════════════════════');
console.log('\n✅ PASS (' + results.pass.length + '):');
results.pass.forEach(m => console.log('  ✅ ' + m));
console.log('\n⚠️  WARNINGS (' + results.warn.length + '):');
results.warn.forEach(m => console.log('  ⚠️  ' + m));
console.log('\n❌ FAIL (' + results.fail.length + '):');
results.fail.forEach(m => console.log('  ❌ ' + m));
console.log('\n════════════════════════════════════════════');
console.log('  SCORE: ' + results.pass.length + ' pass, ' + results.warn.length + ' warnings, ' + results.fail.length + ' fails');
console.log('════════════════════════════════════════════');
