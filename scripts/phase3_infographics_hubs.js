#!/usr/bin/env node
/**
 * Phase 3: Add infographics to pillar pages + enhance hub pages
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

function addInfographic(file, searchStr, imgPath, caption) {
  let html = fs.readFileSync(file, 'utf-8');
  if (html.includes(imgPath)) { console.log(`  - ${path.basename(path.dirname(file))}: infographic already present`); return; }
  const infHTML = `\n    <figure class="infographic"><img src="${imgPath}" alt="${caption}" width="800" height="500" loading="lazy"><figcaption>${caption}</figcaption></figure>\n`;
  const idx = html.indexOf(searchStr);
  if (idx > 0) {
    html = html.slice(0, idx) + infHTML + html.slice(idx);
    fs.writeFileSync(file, html, 'utf-8');
    console.log(`  ✓ ${path.basename(path.dirname(file))}: infographic added`);
  } else {
    console.log(`  ✗ ${path.basename(path.dirname(file))}: marker not found`);
  }
}

// 1. IBI page
addInfographic(
  path.join(ROOT, 'ibi-2026', 'index.html'),
  '<h2 id="como-se-calcula"',
  '../img/infografia-calculo-ibi.png',
  'Infografía: Cómo se calcula el IBI en España (Valor Catastral × Tipo Impositivo - Bonificaciones = Cuota Final)'
);

// 2. Plusvalía page
addInfographic(
  path.join(ROOT, 'plusvalia', 'index.html'),
  '<h2 id="dos-metodos"',
  '../img/infografia-plusvalia.png',
  'Infografía: Dos métodos de cálculo de la plusvalía municipal (Objetivo vs. Real)'
);

// 3. Basuras page
addInfographic(
  path.join(ROOT, 'tasa-basuras', 'index.html'),
  '<h2',
  '../img/infografia-tasa-basuras.png',
  'Infografía: Por qué sube la tasa de basuras en 2026 (Ley 7/2022 de Residuos)'
);

// 4. Enhance hub pages with substantial content
const hubPages = [
  {
    file: path.join(ROOT, 'comunidades', 'index.html'),
    marker: '</h1>',
    content: `
    <p class="lead">Consulta la guía fiscal completa de cada comunidad autónoma. Cada municipio tiene sus propias ordenanzas fiscales que determinan el tipo de IBI, la tasa de basuras y las bonificaciones disponibles.</p>
    <div class="hb">
      <strong>📊 ¿Sabías que el IBI varía hasta un 0,10% entre comunidades?</strong>
      El tipo de IBI urbano oscila entre el 0,57% de Jaca (Aragón) y el 0,68% de Talavera de la Reina (Castilla-La Mancha) y Lorca (Murcia) en los municipios de nuestra guía. La tasa de basuras también presenta diferencias significativas: desde 78 €/año en Trujillo hasta 155 €/año en Oviedo. Estas diferencias reflejan tanto las necesidades de financiación de cada ayuntamiento como el nivel de servicios que prestan.
    </div>
    <p>En España, los impuestos locales están regulados por el <strong>Real Decreto Legislativo 2/2004</strong> (Texto Refundido de la Ley Reguladora de las Haciendas Locales), pero cada ayuntamiento fija sus propios tipos dentro de los márgenes legales. Esto significa que dos viviendas idénticas en municipios diferentes pueden tener cuotas de IBI muy distintas.</p>
    <p>Nuestra guía cubre actualmente <strong>59 municipios en 7 comunidades autónomas</strong>: Aragón, Asturias, Castilla y León, Castilla-La Mancha, Extremadura, Galicia y Murcia. Cada guía municipal incluye datos exactos de la ordenanza fiscal vigente, calculadoras, bonificaciones disponibles y consejos prácticos.</p>`
  },
  {
    file: path.join(ROOT, 'municipios', 'index.html'),
    marker: '</h1>',
    content: `
    <p class="lead">Directorio completo de los 59 municipios incluidos en nuestra guía fiscal 2026. Cada página incluye el tipo de IBI, la tasa de basuras, las bonificaciones disponibles, la plusvalía municipal y un consejo práctico específico para ese municipio.</p>
    <div class="hb">
      <strong>🔍 ¿Cómo usar esta guía?</strong>
      Busca tu municipio en la lista inferior. Cada guía incluye: tipo de IBI urbano y rústico con cuotas estimadas para diferentes valores catastrales, tasa de basuras exacta, bonificaciones del IBI (familia numerosa, energía solar, VPO, domiciliación), información sobre la plusvalía municipal, y un gráfico comparativo con otros municipios de la misma comunidad autónoma.
    </div>
    <p>Los datos provienen de las <strong>ordenanzas fiscales publicadas en los boletines oficiales</strong> correspondientes (BOE, DOCM, DOE, BOPA, DOG, BORM, BOA) entre diciembre de 2025 y enero de 2026. Verificamos cada dato con la fuente original y actualizamos la información cuando se producen modificaciones a lo largo del ejercicio.</p>
    <p>Si tu municipio no aparece en la lista, puedes consultar tu valor catastral directamente en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener" style="color:var(--accent)">Sede del Catastro</a> y utilizar nuestra <a href="../calculadora-ibi/" style="color:var(--accent)">calculadora de IBI</a> para estimar tu cuota.</p>`
  }
];

for (const hub of hubPages) {
  if (!fs.existsSync(hub.file)) { console.log(`  ✗ ${hub.file} not found`); continue; }
  let html = fs.readFileSync(hub.file, 'utf-8');
  if (html.includes('¿Sabías que') || html.includes('¿Cómo usar esta guía')) {
    console.log(`  - ${path.basename(path.dirname(hub.file))}: already enhanced`);
    continue;
  }
  const idx = html.indexOf(hub.marker);
  if (idx > 0) {
    const insertPos = idx + hub.marker.length;
    html = html.slice(0, insertPos) + hub.content + html.slice(insertPos);
    fs.writeFileSync(hub.file, html, 'utf-8');
    console.log(`  ✓ ${path.basename(path.dirname(hub.file))}: enhanced with content`);
  }
}

// 5. Enhance provincias hub
const provFile = path.join(ROOT, 'provincias', 'index.html');
if (fs.existsSync(provFile)) {
  let html = fs.readFileSync(provFile, 'utf-8');
  if (!html.includes('fiscalidad local varía')) {
    const marker = '</h1>';
    const idx = html.indexOf(marker);
    if (idx > 0) {
      const content = `
    <p class="lead">Explora los municipios organizados por provincia. La fiscalidad local varía significativamente dentro de cada provincia: municipios capitales suelen tener tipos de IBI más altos pero también más bonificaciones disponibles.</p>
    <p>En cada provincia, los ayuntamientos fijan sus tipos impositivos de forma independiente, dentro de los márgenes establecidos por la Ley Reguladora de las Haciendas Locales. Esto explica por qué dos municipios vecinos pueden tener cuotas de IBI o basuras muy diferentes. Nuestra guía te ayuda a comparar y entender estas diferencias.</p>`;
      html = html.slice(0, idx + marker.length) + content + html.slice(idx + marker.length);
      fs.writeFileSync(provFile, html, 'utf-8');
      console.log(`  ✓ provincias: enhanced`);
    }
  }
}

console.log('\nDone! Phase 3 complete.');
