const fs = require('fs');
const css = fs.readFileSync('c:\\Users\\aitha\\Desktop\\ibi\\styles.css', 'utf-8');

console.log('=== CSS SELECTOR VERIFICATION ===\n');

// Check required selectors exist
const required = {
  'body > section.hero': 'Homepage hero (scoped)',
  '.wrap .hero': 'Municipality hero grid',
  'section.sec': 'Municipality sections',
  'h2.sec': 'Hub section headers',
  '.hero-inner': 'Homepage hero inner',
  '.search-box': 'Search box',
  '.type-card': 'Type cards',
  '.muni-card': 'Muni cards',
  '.ccaa-tile': 'CCAA tiles',
  '.ccaa-detail-panel': 'Detail panels',
  '.info-strip': 'Info strip',
  '.footer-inner': 'Footer grid',
  '.header-top': 'Header top',
  '.header-inner': 'Legal header',
  '.breadcrumb': 'Breadcrumb',
  '.page-wrap': 'Legal pages',
  '.ed-cols': 'Editorial columns',
  '.cookie-banner': 'Cookie banner',
  '.prov-cols': 'Province columns',
  '.muni-list': 'Municipality list',
  '.faq-list': 'FAQ list',
  '.logo-main': 'Logo main',
};

for (const [sel, desc] of Object.entries(required)) {
  const found = css.includes(sel);
  console.log((found ? '  ✅' : '  ❌') + ' ' + desc + ' (' + sel + ')');
}

// Check for CONFLICTING selectors that would affect municipality pages
console.log('\n=== CONFLICT CHECK ===\n');
const lines = css.split('\n');
let conflicts = 0;

lines.forEach((line, i) => {
  const trimmed = line.trim();
  // Bare section.hero without body > prefix
  if (/^section\.hero\s*[{h]/.test(trimmed) && !trimmed.startsWith('body')) {
    console.log('  ⚠️  Line ' + (i+1) + ': ' + trimmed.substring(0, 80));
    conflicts++;
  }
  // Bare .hero without .wrap prefix
  if (/^\.hero\s*{/.test(trimmed)) {
    console.log('  ⚠️  Line ' + (i+1) + ': ' + trimmed.substring(0, 80));
    conflicts++;
  }
});

if (conflicts === 0) console.log('  ✅ No conflicting hero selectors found');

console.log('\n=== DONE ===');
