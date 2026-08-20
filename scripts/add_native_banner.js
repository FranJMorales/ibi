const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const AD_MARKER = "container-668e307b638c1713b6b2ebc83aab889c";
const SKIP_SEGMENTS = new Set(["aviso-legal", "cookies", "privacidad", "contacto"]);

const AD_CSS = `
    .tm-native-ad{margin:24px 0 30px;padding:14px 16px 16px;background:var(--card,var(--card-bg,#fffdf8));border:1px solid var(--rule,#d8d0c0);border-radius:6px;box-shadow:0 8px 20px rgba(26,26,46,.04)}
    .tm-native-ad-label{font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mid,#6b6b7b);margin-bottom:10px;font-weight:700}
    .tm-native-ad > div[id^="container-"]{min-height:90px}
`;

const AD_BLOCK = `
<div class="tm-native-ad" aria-label="Publicidad">
  <div class="tm-native-ad-label">Publicidad</div>
  <script async="async" data-cfasync="false" src="https://pl28952826.profitablecpmratenetwork.com/668e307b638c1713b6b2ebc83aab889c/invoke.js"></script>
  <div id="container-668e307b638c1713b6b2ebc83aab889c"></div>
</div>
`;

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "scripts" || entry.name.startsWith(".")) continue;
      walk(full, out);
    } else if (entry.isFile() && entry.name === "index.html") {
      out.push(full);
    }
  }
  return out;
}

function shouldSkip(file) {
  const rel = path.relative(ROOT, file).split(path.sep);
  return rel.some((segment) => SKIP_SEGMENTS.has(segment));
}

function injectCss(html) {
  if (html.includes(".tm-native-ad")) return html;
  const lastStyle = html.lastIndexOf("</style>");
  if (lastStyle === -1) return html;
  return `${html.slice(0, lastStyle)}${AD_CSS}\n${html.slice(lastStyle)}`;
}

function insertAfter(html, pattern) {
  const match = html.match(pattern);
  if (!match) return null;
  const index = match.index + match[0].length;
  return `${html.slice(0, index)}\n\n${AD_BLOCK}\n${html.slice(index)}`;
}

function injectAd(html, file) {
  if (html.includes(AD_MARKER)) return html;

  const rel = path.relative(ROOT, file).replace(/\\/g, "/");
  if (rel === "index.html") {
    return (
      insertAfter(html, /<\/section>\s*<div class="section">/) ||
      insertAfter(html, /<\/section>\s*<div class="ruled bg-alt">/) ||
      insertAfter(html, /<\/section>\s*<!--[\s\S]*?-->\s*<section class="section">/) ||
      html
    );
  }

  if (html.includes('<div class="intro-box">')) {
    return insertAfter(html, /<div class="intro-box">[\s\S]*?<\/div>/) || html;
  }

  if (html.includes('<div class="toc-box">')) {
    return insertAfter(html, /<div class="toc-box">[\s\S]*?<\/div>/) || html;
  }

  if (html.includes('<div class="toc">')) {
    return insertAfter(html, /<div class="toc">[\s\S]*?<\/div>/) || html;
  }

  if (html.includes('class="art-meta"')) {
    return insertAfter(html, /<p class="art-meta">[\s\S]*?<\/p>/) || html;
  }

  if (html.includes('<p class="lead">')) {
    return insertAfter(html, /<p class="lead">[\s\S]*?<\/p>/) || html;
  }

  if (html.includes('<div class="calc-hero">')) {
    return insertAfter(html, /<div class="calc-hero">[\s\S]*?<\/div>/) || html;
  }

  return html;
}

let updated = 0;
for (const file of walk(ROOT)) {
  if (shouldSkip(file)) continue;
  const original = fs.readFileSync(file, "utf8");
  let html = injectCss(original);
  html = injectAd(html, file);
  if (html !== original) {
    fs.writeFileSync(file, html, "utf8");
    updated++;
  }
}

console.log(`native_banner_updated=${updated}`);
