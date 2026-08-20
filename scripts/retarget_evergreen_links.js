const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const files = [
  "ibi-2026/index.html",
  "bonificaciones/index.html",
  "tasa-basuras/index.html",
  "plusvalia/index.html",
];

const patterns = [
  /\/ibi-2026-[^/"']+\//g,
  /\/bonificaciones-ibi-[^/"']+\//g,
  /\/tasa-basuras-2026-[^/"']+\//g,
  /\/plusvalia-municipal-[^/"']+\//g,
];

let updated = 0;

for (const rel of files) {
  const file = path.join(ROOT, rel);
  let html = fs.readFileSync(file, "utf8");
  const before = html;
  for (const pattern of patterns) {
    html = html.replace(pattern, "/");
  }
  if (html !== before) {
    fs.writeFileSync(file, html, "utf8");
    updated += 1;
  }
}

console.log(`retargeted_evergreens=${updated}`);
