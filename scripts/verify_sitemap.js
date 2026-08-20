const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const sitemap = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');

// Extract all URLs from the sitemap
const urls = [];
const regex = /<loc>(.*?)<\/loc>/g;
let m;
while ((m = regex.exec(sitemap)) !== null) {
  urls.push(m[1]);
}

console.log(`Total URLs in sitemap: ${urls.length}`);
console.log('');

let missing = 0;
let ok = 0;

for (const url of urls) {
  // Convert URL to local path
  const rel = url.replace('https://tasasmunicipales.info/', '');
  const localPath = rel === '' ? 'index.html' : path.join(rel, 'index.html');
  const fullPath = path.join(ROOT, localPath);
  
  if (fs.existsSync(fullPath)) {
    ok++;
  } else {
    console.log(`  ✗ 404: ${url}`);
    console.log(`    → Missing: ${fullPath}`);
    missing++;
  }
}

console.log('');
console.log(`OK: ${ok} | Missing: ${missing}`);

// Also check for www in URLs
const wwwUrls = urls.filter(u => u.includes('www.tasasmunicipales'));
if (wwwUrls.length > 0) {
  console.log(`\n⚠️ URLs with www: ${wwwUrls.length}`);
  wwwUrls.forEach(u => console.log(`  ${u}`));
} else {
  console.log('✅ No www URLs found (correct!)');
}
