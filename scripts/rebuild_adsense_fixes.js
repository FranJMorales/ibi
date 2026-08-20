#!/usr/bin/env node
/**
 * REBUILD SCRIPT — AdSense Fixes
 * Phase 1: Cookie banner + CSS externalization + "500 municipios" fix
 * Processes ALL HTML files in the project
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

function findAllHtml(dir) {
  let results = [];
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory() && f.name !== 'scripts' && f.name !== 'data' && f.name !== 'node_modules') {
      results = results.concat(findAllHtml(full));
    } else if (f.name === 'index.html') {
      results.push(full);
    }
  }
  return results;
}

function getRelativeCssPath(htmlPath) {
  const rel = path.relative(path.dirname(htmlPath), ROOT).replace(/\\/g, '/');
  return rel ? rel + '/styles.css' : 'styles.css';
}

function getRelativeJsPath(htmlPath) {
  const rel = path.relative(path.dirname(htmlPath), ROOT).replace(/\\/g, '/');
  return rel ? rel + '/cookie-consent.js' : 'cookie-consent.js';
}

function processFile(filePath) {
  let html = fs.readFileSync(filePath, 'utf-8');
  const relCss = getRelativeCssPath(filePath);
  const relJs = getRelativeJsPath(filePath);

  // 1. Remove inline <style>...</style> blocks
  html = html.replace(/<style>[\s\S]*?<\/style>/gi, '');

  // 2. Add external CSS link if not already present
  if (!html.includes('styles.css')) {
    html = html.replace('</head>', `  <link rel="stylesheet" href="${relCss}">\n</head>`);
  }

  // 3. Add cookie consent script before </body>
  if (!html.includes('cookie-consent.js')) {
    html = html.replace('</body>', `<script src="${relJs}" defer></script>\n</body>`);
  }

  // 4. Fix "500 municipios" → "59 municipios"
  html = html.replace(/más de 500 municipios/gi, '59 municipios');
  html = html.replace(/500 municipios/gi, '59 municipios');

  // 5. Remove legacy CSS fix references
  html = html.replace(/<link[^>]*legacy-article-fix\.css[^>]*>/gi, '');
  html = html.replace(/<link[^>]*legacy-municipio-fix\.css[^>]*>/gi, '');

  fs.writeFileSync(filePath, html, 'utf-8');
  return true;
}

// Run
const files = findAllHtml(ROOT);
console.log(`Found ${files.length} HTML files to process...`);
let count = 0;
for (const f of files) {
  try {
    processFile(f);
    count++;
    const rel = path.relative(ROOT, f);
    console.log(`  ✓ ${rel}`);
  } catch (e) {
    console.error(`  ✗ ${path.relative(ROOT, f)}: ${e.message}`);
  }
}
console.log(`\nDone! Processed ${count}/${files.length} files.`);
