const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
let filesFixed = 0;

// Find all index.html files
function findHtml(dir, results = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules' && e.name !== 'scripts' && e.name !== 'data') {
      findHtml(full, results);
    } else if (e.name === 'index.html') {
      results.push(full);
    }
  }
  return results;
}

const allFiles = findHtml(ROOT);
// Also add root index.html
allFiles.push(path.join(ROOT, 'index.html'));

console.log(`Found ${allFiles.length} HTML files\n`);

for (const fp of allFiles) {
  let html = fs.readFileSync(fp, 'utf8');
  let changed = false;
  const rel = path.relative(ROOT, fp);

  // Fix 1: Update "52 municipios en 6 comunidades" → "59 municipios en 7 comunidades"
  if (html.includes('52 municipios') || html.includes('6 comunidades autónomas')) {
    html = html.replace(/52 municipios/g, '59 municipios');
    html = html.replace(/6 comunidades autónomas/g, '7 comunidades autónomas');
    html = html.replace(/6 comunidades autonomas/g, '7 comunidades autonomas');
    changed = true;
  }

  // Fix 2: Remove "próximamente" from comunidades highlight box
  if (rel.includes('comunidades') && html.includes('lo añadimos próximamente')) {
    html = html.replace(
      'lo añadimos próximamente',
      'lo incluiremos en la próxima actualización'
    );
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(fp, html, 'utf8');
    filesFixed++;
    console.log(`  ✓ ${rel}`);
  }
}

// Fix 3: Fix calculadora broken links in result section
const calcPath = path.join(ROOT, 'calculadora-ibi', 'index.html');
if (fs.existsSync(calcPath)) {
  let calc = fs.readFileSync(calcPath, 'utf8');
  
  // Remove broken sub-page links from the result, keep only the valid municipality link
  const oldLinks = `    <a href="\${m.slug}/bonificaciones-ibi-\${m.slug.split('/').pop()}/" class="res-link-btn">Solicitar bonificaciones</a>
    <a href="\${m.slug}/como-pagar-ibi-\${m.slug.split('/').pop()}/" class="res-link-btn">Cómo pagar el IBI</a>`;
  
  const newLinks = `    <a href="../bonificaciones/" class="res-link-btn">Guía de bonificaciones</a>
    <a href="../ibi-2026/" class="res-link-btn">Guía IBI 2026</a>`;
  
  if (calc.includes('bonificaciones-ibi-${m.slug')) {
    calc = calc.replace(
      /\s*<a href="\$\{m\.slug\}\/bonificaciones-ibi-\$\{m\.slug\.split.*?<\/a>\s*<a href="\$\{m\.slug\}\/como-pagar-ibi-\$\{m\.slug\.split.*?<\/a>/,
      `\n    <a href="../bonificaciones/" class="res-link-btn">Guía de bonificaciones</a>\n    <a href="../ibi-2026/" class="res-link-btn">Guía IBI 2026</a>`
    );
    fs.writeFileSync(calcPath, calc, 'utf8');
    console.log(`  ✓ calculadora-ibi/index.html (broken result links fixed)`);
    filesFixed++;
  }
}

console.log(`\n═══ DONE ═══`);
console.log(`Files fixed: ${filesFixed}`);
