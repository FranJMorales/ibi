const fs = require('fs');
const path = 'c:\\Users\\aitha\\Desktop\\ibi\\plusvalia\\index.html';
let html = fs.readFileSync(path, 'utf-8');

// The file is duplicated from line 184 onwards - the entire page appears twice
// Keep only lines 1-183 (the correct version), then add footer + closing tags

const lines = html.split('\n');
console.log('Total lines before:', lines.length);

// Find where the second <!DOCTYPE starts
let cutLine = -1;
for (let i = 100; i < lines.length; i++) {
  if (lines[i].trim() === '<!DOCTYPE html>') {
    cutLine = i;
    break;
  }
}
console.log('Second <!DOCTYPE at line:', cutLine + 1);

// Keep lines 0 to cutLine-1, then add schema scripts + footer + closing
const goodPart = lines.slice(0, cutLine).join('\n');

// Extract the footer from the duplicate (it's the same)
const footerStart = html.lastIndexOf('<footer>');
const footerEnd = html.lastIndexOf('</footer>') + '</footer>'.length;
const footer = html.substring(footerStart, footerEnd);

// Build the final file
const finalHtml = goodPart + '\n' +
  '<script type="application/ld+json">\n' +
  '{"@context":"https://schema.org","@type":"Article","headline":"Plusvalía Municipal 2026: calculadora, cuánto se paga y cómo evitarla","description":"Plusvalía municipal 2026: dos métodos de cálculo, coeficientes actualizados, plazos en herencias y ventas.","datePublished":"2026-01-15","dateModified":"2026-04-22","author":{"@type":"Organization","name":"TasasMunicipales.info","url":"https://tasasmunicipales.info"},"publisher":{"@type":"Organization","name":"TasasMunicipales.info","url":"https://tasasmunicipales.info"},"mainEntityOfPage":{"@type":"WebPage","@id":"https://tasasmunicipales.info/plusvalia/"},"inLanguage":"es"}\n' +
  '</script>\n' +
  '<script type="application/ld+json">\n' +
  '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"¿Cómo se calcula la plusvalía municipal en 2026?","acceptedAnswer":{"@type":"Answer","text":"Con el método objetivo o el método real. Elige el más favorable."}},{"@type":"Question","name":"¿Qué pasa si vendo con pérdidas?","acceptedAnswer":{"@type":"Answer","text":"No se paga plusvalía. Aporta ambas escrituras."}},{"@type":"Question","name":"¿Cuándo hay que pagar en una herencia?","acceptedAnswer":{"@type":"Answer","text":"6 meses desde el fallecimiento, prorrogables a 12."}}]}\n' +
  '</script>\n' +
  '<script type="application/ld+json">\n' +
  '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Inicio","item":"https://tasasmunicipales.info/"},{"@type":"ListItem","position":2,"name":"Plusvalía Municipal 2026","item":"https://tasasmunicipales.info/plusvalia/"}]}\n' +
  '</script>\n' +
  footer + '\n' +
  '<script src="../cookie-consent.js" defer></script>\n' +
  '</body>\n' +
  '</html>\n';

fs.writeFileSync(path, finalHtml, 'utf-8');

// Verify
const final = fs.readFileSync(path, 'utf-8');
const doctypeCount = (final.match(/<!DOCTYPE/gi) || []).length;
const mainCount = (final.match(/<\/main>/g) || []).length;
const asideCount = (final.match(/<aside>/g) || []).length;
const bodyCount = (final.match(/<\/body>/g) || []).length;
const finalLines = final.split('\n').length;

console.log('\nAfter fix:');
console.log('  Total lines:', finalLines);
console.log('  <!DOCTYPE> count:', doctypeCount, doctypeCount === 1 ? '✅' : '❌');
console.log('  </main> count:', mainCount, mainCount === 1 ? '✅' : '❌');
console.log('  <aside> count:', asideCount, asideCount === 1 ? '✅' : '❌');
console.log('  </body> count:', bodyCount, bodyCount === 1 ? '✅' : '❌');

// Check layout order
const mc = final.indexOf('</main>');
const ao = final.indexOf('<aside>');
const ac = final.indexOf('</article>');
console.log('  Layout order OK:', ac < mc && mc < ao ? '✅' : '❌');
