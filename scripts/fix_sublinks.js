const fs = require('fs');

// Fix homepage - remove all broken sub-links
const homepage = fs.readFileSync('index.html', 'utf8');
const fixed = homepage.replace(/<div class="sub-links">[\s\S]*?<\/div>/g, '');
fs.writeFileSync('index.html', fixed, 'utf8');
console.log('Homepage: sub-links removed');

// Fix community pages
const ccaaPages = ['aragon', 'asturias', 'castilla-la-mancha', 'castilla-y-leon', 'extremadura', 'galicia', 'murcia'];
for (const ccaa of ccaaPages) {
  const fp = `${ccaa}/index.html`;
  if (fs.existsSync(fp)) {
    let html = fs.readFileSync(fp, 'utf8');
    html = html.replace(/<div class="sub-links">[\s\S]*?<\/div>/g, '');
    fs.writeFileSync(fp, html, 'utf8');
    console.log(`${ccaa}: sub-links removed`);
  }
}

// Fix municipios page
if (fs.existsSync('municipios/index.html')) {
  let html = fs.readFileSync('municipios/index.html', 'utf8');
  html = html.replace(/<div class="sub-links">[\s\S]*?<\/div>/g, '');
  fs.writeFileSync('municipios/index.html', html, 'utf8');
  console.log('municipios: sub-links removed');
}

// Fix comunidades page
if (fs.existsSync('comunidades/index.html')) {
  let html = fs.readFileSync('comunidades/index.html', 'utf8');
  html = html.replace(/<div class="sub-links">[\s\S]*?<\/div>/g, '');
  fs.writeFileSync('comunidades/index.html', html, 'utf8');
  console.log('comunidades: sub-links removed');
}

// Fix provincias page
if (fs.existsSync('provincias/index.html')) {
  let html = fs.readFileSync('provincias/index.html', 'utf8');
  html = html.replace(/<div class="sub-links">[\s\S]*?<\/div>/g, '');
  fs.writeFileSync('provincias/index.html', html, 'utf8');
  console.log('provincias: sub-links removed');
}

// Add "Sobre nosotros" link to the footer of ALL pages
const allHtmlFiles = [];
function findHtml(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = dir + '/' + e.name;
    if (e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules' && e.name !== 'scripts') {
      findHtml(full);
    } else if (e.name === 'index.html') {
      allHtmlFiles.push(full);
    }
  }
}
findHtml('.');

console.log(`\nTotal HTML files found: ${allHtmlFiles.length}`);
console.log('Done!');
