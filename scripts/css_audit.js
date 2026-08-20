const fs = require('fs');
const path = require('path');
const ROOT = 'c:\\Users\\aitha\\Desktop\\ibi';

// 1. Parse all CSS class selectors from styles.css
const css = fs.readFileSync(path.join(ROOT, 'styles.css'), 'utf-8');
const cssClasses = new Set();
const classRegex = /\.([a-zA-Z_-][a-zA-Z0-9_-]*)/g;
let m;
while ((m = classRegex.exec(css)) !== null) {
  cssClasses.add(m[1]);
}

// 2. Find all HTML files recursively
function findHtml(dir) {
  let results = [];
  const items = fs.readdirSync(dir);
  for (const item of items) {
    if (item === 'node_modules' || item === '.git' || item === 'scripts') continue;
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      results = results.concat(findHtml(full));
    } else if (item.endsWith('.html')) {
      results.push(full);
    }
  }
  return results;
}

const htmlFiles = findHtml(ROOT);
console.log(`Found ${htmlFiles.length} HTML files`);
console.log(`Found ${cssClasses.size} CSS classes in styles.css\n`);

// 3. For each HTML file, extract class="" values and check against CSS
const missingByPage = {};
const allMissing = {};
// Classes that are OK to be missing (dynamic/JS-generated or standard)
const ignore = new Set(['open', 'active', 'on', 'cookie-hidden', 'body', 'hidden']);

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf-8');
  const rel = path.relative(ROOT, file).replace(/\\/g, '/');
  
  // Extract all class="..." values
  const classAttrRegex = /class="([^"]+)"/g;
  const usedClasses = new Set();
  let cm;
  while ((cm = classAttrRegex.exec(html)) !== null) {
    const classes = cm[1].split(/\s+/);
    for (const cls of classes) {
      if (cls.trim()) usedClasses.add(cls.trim());
    }
  }
  
  // Check each used class
  const missing = [];
  for (const cls of usedClasses) {
    if (!cssClasses.has(cls) && !ignore.has(cls)) {
      missing.push(cls);
      allMissing[cls] = (allMissing[cls] || []);
      allMissing[cls].push(rel);
    }
  }
  
  if (missing.length > 0) {
    missingByPage[rel] = missing.sort();
  }
}

// 4. Report
const pageCount = Object.keys(missingByPage).length;
const classCount = Object.keys(allMissing).length;

if (classCount === 0) {
  console.log('✅ ALL CSS CLASSES ARE DEFINED — No missing classes found!\n');
} else {
  console.log(`⚠️  Found ${classCount} missing CSS classes across ${pageCount} pages:\n`);
  
  // Group by class, show how many pages use it
  const sorted = Object.entries(allMissing).sort((a, b) => b[1].length - a[1].length);
  for (const [cls, pages] of sorted) {
    const pageList = pages.length > 3 ? pages.slice(0, 3).join(', ') + ` +${pages.length - 3} more` : pages.join(', ');
    console.log(`  ❌ .${cls} — used in ${pages.length} page(s): ${pageList}`);
  }
}

// 5. Also check for structural issues
console.log('\n═══ STRUCTURAL CHECKS ═══\n');
let structIssues = 0;
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf-8');
  const rel = path.relative(ROOT, file).replace(/\\/g, '/');
  
  // Check </body> and </html>
  if (!html.includes('</body>')) { console.log(`  ❌ ${rel}: missing </body>`); structIssues++; }
  if (!html.includes('</html>')) { console.log(`  ❌ ${rel}: missing </html>`); structIssues++; }
  
  // Check stylesheet link
  if (!html.includes('styles.css')) { console.log(`  ❌ ${rel}: missing styles.css link`); structIssues++; }
  
  // Check for <style> inline blocks (bad for AdSense)
  const styleCount = (html.match(/<style[\s>]/g) || []).length;
  if (styleCount > 0) { console.log(`  ⚠️  ${rel}: has ${styleCount} inline <style> block(s)`); structIssues++; }
  
  // Check .al layout has both main and aside
  if (html.includes('class="al"')) {
    if (!html.includes('<main')) { console.log(`  ❌ ${rel}: has .al layout but no <main>`); structIssues++; }
    if (!html.includes('<aside')) { console.log(`  ❌ ${rel}: has .al layout but no <aside>`); structIssues++; }
    // Check main closes before aside opens
    const mainClose = html.indexOf('</main>');
    const asideOpen = html.indexOf('<aside');
    if (mainClose > asideOpen && asideOpen > 0) { 
      console.log(`  ❌ ${rel}: </main> comes after <aside> — sidebar will be below`); 
      structIssues++; 
    }
  }
}

if (structIssues === 0) {
  console.log('  ✅ All structural checks passed');
}

console.log('\n═══ DONE ═══');
