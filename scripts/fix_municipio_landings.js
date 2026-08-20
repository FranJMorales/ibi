const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const files = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.isFile() && entry.name === "index.html") {
      const html = fs.readFileSync(full, "utf8");
      if (html.includes("legacy-municipio-fix.css")) files.push(full);
    }
  }
}

[
  "aragon",
  "castilla-la-mancha",
  "castilla-y-leon",
  "extremadura",
  "galicia",
  "murcia",
].forEach((dir) => {
  const full = path.join(ROOT, dir);
  if (fs.existsSync(full)) walk(full);
});

const fixCss = `<style>:root{--card:var(--card-bg)}.hi{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}.logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#fff;text-decoration:none;display:flex;flex-direction:column;gap:2px}.logo span{font-family:'Source Serif 4',Georgia,serif;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.62)}.bc{max-width:1100px;margin:0 auto;padding:14px 24px 0;font-size:.75rem;color:var(--mid)}.bc a{color:var(--accent);text-decoration:none}.bc span{margin:0 5px}.wrap{max-width:1100px;margin:0 auto;padding:24px 24px 60px}</style>`;

let touched = 0;
for (const file of files) {
  let html = fs.readFileSync(file, "utf8");
  html = html.replace(/\s*<link rel="stylesheet" href="\/extremadura\/legacy-municipio-fix\.css">\s*/i, "\n");
  if (!html.includes(":root{--card:var(--card-bg)}.hi{")) {
    html = html.replace(/(<style>)/, `${fixCss}\n  $1`);
  }
  fs.writeFileSync(file, html, "utf8");
  touched++;
}

console.log(`fixed_municipio_landings=${touched}`);
