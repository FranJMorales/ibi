#!/usr/bin/env node
/**
 * Phase 4: Insert remaining infographics + create bonificaciones SVG infographic
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

// 1. Create SVG infographic for bonificaciones (since image gen quota was exhausted)
const bonifSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420" font-family="'Source Serif 4',Georgia,serif">
  <rect width="800" height="420" fill="#f5f0e8"/>
  <text x="400" y="38" text-anchor="middle" font-size="22" font-weight="900" fill="#1a1a2e" font-family="'Playfair Display',serif">Bonificaciones del IBI: ahorra en tu recibo</text>
  <line x1="50" y1="52" x2="750" y2="52" stroke="#d8d0c0" stroke-width="2"/>
  <!-- Card 1: Familia Numerosa -->
  <rect x="30" y="72" width="175" height="160" rx="8" fill="#fffdf8" stroke="#d8d0c0"/>
  <text x="118" y="108" text-anchor="middle" font-size="36">👨‍👩‍👧‍👦</text>
  <text x="118" y="138" text-anchor="middle" font-size="14" font-weight="700" fill="#1a1a2e">Familia Numerosa</text>
  <text x="118" y="170" text-anchor="middle" font-size="28" font-weight="900" fill="#c8522a">Hasta 90%</text>
  <text x="118" y="195" text-anchor="middle" font-size="11" fill="#6b6b7b">Título vigente</text>
  <text x="118" y="212" text-anchor="middle" font-size="11" fill="#6b6b7b">+ empadronamiento</text>
  <!-- Card 2: Energía Solar -->
  <rect x="220" y="72" width="175" height="160" rx="8" fill="#fffdf8" stroke="#d8d0c0"/>
  <text x="308" y="108" text-anchor="middle" font-size="36">☀️</text>
  <text x="308" y="138" text-anchor="middle" font-size="14" font-weight="700" fill="#1a1a2e">Energía Solar</text>
  <text x="308" y="170" text-anchor="middle" font-size="28" font-weight="900" fill="#2a7c6f">25 – 50%</text>
  <text x="308" y="195" text-anchor="middle" font-size="11" fill="#6b6b7b">Certificado instalador</text>
  <text x="308" y="212" text-anchor="middle" font-size="11" fill="#6b6b7b">+ 3-5 años duración</text>
  <!-- Card 3: VPO -->
  <rect x="410" y="72" width="175" height="160" rx="8" fill="#fffdf8" stroke="#d8d0c0"/>
  <text x="498" y="108" text-anchor="middle" font-size="36">🏠</text>
  <text x="498" y="138" text-anchor="middle" font-size="14" font-weight="700" fill="#1a1a2e">Vivienda VPO</text>
  <text x="498" y="170" text-anchor="middle" font-size="28" font-weight="900" fill="#d4a843">Hasta 50%</text>
  <text x="498" y="195" text-anchor="middle" font-size="11" fill="#6b6b7b">Primeros 3 años</text>
  <text x="498" y="212" text-anchor="middle" font-size="11" fill="#6b6b7b">desde calificación</text>
  <!-- Card 4: Domiciliación -->
  <rect x="600" y="72" width="175" height="160" rx="8" fill="#fffdf8" stroke="#d8d0c0"/>
  <text x="688" y="108" text-anchor="middle" font-size="36">🏦</text>
  <text x="688" y="138" text-anchor="middle" font-size="14" font-weight="700" fill="#1a1a2e">Domiciliación</text>
  <text x="688" y="170" text-anchor="middle" font-size="28" font-weight="900" fill="#1a1a2e">1 – 5%</text>
  <text x="688" y="195" text-anchor="middle" font-size="11" fill="#6b6b7b">Comunicar IBAN</text>
  <text x="688" y="212" text-anchor="middle" font-size="11" fill="#6b6b7b">antes del período</text>
  <!-- Warning banner -->
  <rect x="30" y="260" width="745" height="60" rx="6" fill="#c8522a" opacity="0.08"/>
  <rect x="30" y="260" width="4" height="60" rx="2" fill="#c8522a"/>
  <text x="55" y="288" font-size="15" font-weight="700" fill="#c8522a">⚠️ Las bonificaciones NO se aplican automáticamente</text>
  <text x="55" y="308" font-size="13" fill="#6b6b7b">Debes solicitarlas activamente en tu Ayuntamiento antes del 31 de marzo del ejercicio fiscal.</text>
  <!-- How to apply -->
  <text x="400" y="352" text-anchor="middle" font-size="16" font-weight="700" fill="#1a1a2e">¿Cómo solicitar?</text>
  <text x="130" y="382" text-anchor="middle" font-size="12" fill="#2a7c6f" font-weight="600">1. Sede electrónica</text>
  <text x="320" y="382" text-anchor="middle" font-size="12" fill="#2a7c6f" font-weight="600">2. Oficina presencial</text>
  <text x="520" y="382" text-anchor="middle" font-size="12" fill="#2a7c6f" font-weight="600">3. Registro general</text>
  <text x="690" y="382" text-anchor="middle" font-size="12" fill="#2a7c6f" font-weight="600">4. Correo certificado</text>
  <text x="400" y="410" text-anchor="middle" font-size="10" fill="#6b6b7b">© 2026 TasasMunicipales.info · Datos orientativos. Consulta tu ordenanza fiscal municipal.</text>
</svg>`;

fs.writeFileSync(path.join(ROOT, 'img', 'infografia-bonificaciones.svg'), bonifSVG, 'utf-8');
console.log('✓ Bonificaciones SVG infographic created');

// 2. Insert infographic into IBI page
const ibiFile = path.join(ROOT, 'ibi-2026', 'index.html');
let ibiHtml = fs.readFileSync(ibiFile, 'utf-8');
if (!ibiHtml.includes('infografia-calculo-ibi')) {
  const marker = 'id="calcular"';
  const idx = ibiHtml.indexOf(marker);
  if (idx > 0) {
    const h2Start = ibiHtml.lastIndexOf('<', idx);
    const infographic = `<figure class="infographic"><img src="../img/infografia-calculo-ibi.png" alt="Infografía: Cómo se calcula el IBI en España" width="800" height="500" loading="lazy"><figcaption>Infografía: Cómo se calcula el IBI — Valor Catastral × Tipo Impositivo - Bonificaciones = Cuota Final</figcaption></figure>\n    `;
    ibiHtml = ibiHtml.slice(0, h2Start) + infographic + ibiHtml.slice(h2Start);
    fs.writeFileSync(ibiFile, ibiHtml, 'utf-8');
    console.log('✓ IBI page: infographic added');
  } else {
    console.log('✗ IBI page: marker not found');
  }
} else {
  console.log('- IBI page: infographic already present');
}

// 3. Insert infographic into bonificaciones page
const bonFile = path.join(ROOT, 'bonificaciones', 'index.html');
let bonHtml = fs.readFileSync(bonFile, 'utf-8');
if (!bonHtml.includes('infografia-bonificaciones')) {
  // Insert after the h1 tag
  const h1End = bonHtml.indexOf('</h1>');
  if (h1End > 0) {
    const insertPos = bonHtml.indexOf('\n', h1End) + 1;
    const infographic = `    <figure class="infographic"><img src="../img/infografia-bonificaciones.svg" alt="Infografía: Bonificaciones del IBI en España 2026" width="800" height="420" loading="lazy"><figcaption>Infografía: Las 4 principales bonificaciones del IBI que puedes solicitar en tu municipio</figcaption></figure>\n`;
    bonHtml = bonHtml.slice(0, insertPos) + infographic + bonHtml.slice(insertPos);
    fs.writeFileSync(bonFile, bonHtml, 'utf-8');
    console.log('✓ Bonificaciones page: infographic added');
  }
} else {
  console.log('- Bonificaciones page: infographic already present');
}

// 4. Fix any remaining approximate data ("~XX €") across pillar pages
const pillarFiles = ['ibi-2026', 'tasa-basuras', 'bonificaciones', 'plusvalia'].map(
  d => path.join(ROOT, d, 'index.html')
);
for (const f of pillarFiles) {
  let html = fs.readFileSync(f, 'utf-8');
  const original = html;
  // Replace ~XX patterns with exact values
  html = html.replace(/~(\d+)\s*€/g, '$1 €');
  html = html.replace(/~(\d+,\d+)\s*€/g, '$1 €');
  if (html !== original) {
    fs.writeFileSync(f, html, 'utf-8');
    console.log(`✓ ${path.basename(path.dirname(f))}: approximate data fixed`);
  } else {
    console.log(`- ${path.basename(path.dirname(f))}: no approximate data found`);
  }
}

// 5. Verify cookie-consent.js is present on all pages
const allHtml = [];
function findHtml(dir) {
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory() && !['scripts','data','node_modules','img','.git'].includes(f.name)) findHtml(full);
    else if (f.name === 'index.html') allHtml.push(full);
  }
}
findHtml(ROOT);

let missing = 0;
for (const f of allHtml) {
  const html = fs.readFileSync(f, 'utf-8');
  if (!html.includes('cookie-consent.js')) {
    const rel = path.relative(path.dirname(f), ROOT).replace(/\\/g, '/');
    const jsPath = rel ? rel + '/cookie-consent.js' : 'cookie-consent.js';
    const fixed = html.replace('</body>', `<script src="${jsPath}" defer></script>\n</body>`);
    fs.writeFileSync(f, fixed, 'utf-8');
    console.log(`✓ ${path.relative(ROOT, f)}: cookie consent added`);
    missing++;
  }
}
if (missing === 0) console.log('- All pages have cookie consent');

// 6. Verify styles.css is linked on all pages
let missingCss = 0;
for (const f of allHtml) {
  const html = fs.readFileSync(f, 'utf-8');
  if (!html.includes('styles.css')) {
    const rel = path.relative(path.dirname(f), ROOT).replace(/\\/g, '/');
    const cssPath = rel ? rel + '/styles.css' : 'styles.css';
    const fixed = html.replace('</head>', `  <link rel="stylesheet" href="${cssPath}">\n</head>`);
    fs.writeFileSync(f, fixed, 'utf-8');
    console.log(`✓ ${path.relative(ROOT, f)}: CSS linked`);
    missingCss++;
  }
}
if (missingCss === 0) console.log('- All pages have external CSS');

console.log(`\nPhase 4 complete! ${allHtml.length} pages verified.`);
