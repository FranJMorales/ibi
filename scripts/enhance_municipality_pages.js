const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const FACTCHECK_FILE = path.join(ROOT, "data", "municipal_factcheck.json");
const TODAY = "2026-03-27";
const COMMUNITIES = [
  "aragon",
  "asturias",
  "castilla-la-mancha",
  "castilla-y-leon",
  "extremadura",
  "galicia",
  "murcia",
];

function read(file) {
  return fs.readFileSync(file, "utf8");
}

function write(file, content) {
  fs.writeFileSync(file, content, "utf8");
}

function exists(file) {
  return fs.existsSync(file);
}

function walkMunicipalities() {
  const results = [];
  for (const communitySlug of COMMUNITIES) {
    const communityDir = path.join(ROOT, communitySlug);
    if (!exists(communityDir)) continue;
    for (const provinceEntry of fs.readdirSync(communityDir, { withFileTypes: true })) {
      if (!provinceEntry.isDirectory()) continue;
      const provinceDir = path.join(communityDir, provinceEntry.name);
      for (const townEntry of fs.readdirSync(provinceDir, { withFileTypes: true })) {
        if (!townEntry.isDirectory()) continue;
        const townDir = path.join(provinceDir, townEntry.name);
        const mainIndex = path.join(townDir, "index.html");
        if (exists(mainIndex)) {
          results.push({
            communitySlug,
            provinceSlug: provinceEntry.name,
            townSlug: townEntry.name,
            slug: `${communitySlug}/${provinceEntry.name}/${townEntry.name}`,
            mainIndex,
          });
        }
      }
    }
  }
  return results;
}

function titleFromSlug(slug) {
  return slug
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function buildRelatedMunicipalities(municipalities) {
  const byProvince = new Map();
  for (const municipality of municipalities) {
    const key = `${municipality.communitySlug}/${municipality.provinceSlug}`;
    if (!byProvince.has(key)) byProvince.set(key, []);
    byProvince.get(key).push(municipality);
  }

  const related = new Map();
  for (const municipality of municipalities) {
    const key = `${municipality.communitySlug}/${municipality.provinceSlug}`;
    const siblings = (byProvince.get(key) || [])
      .filter((item) => item.slug !== municipality.slug)
      .sort((a, b) => titleFromSlug(a.townSlug).localeCompare(titleFromSlug(b.townSlug), "es"));
    related.set(municipality.slug, siblings.slice(0, 6));
  }

  return related;
}

function loadFactcheck() {
  return JSON.parse(read(FACTCHECK_FILE));
}

function saveFactcheck(data) {
  write(FACTCHECK_FILE, `${JSON.stringify(data, null, 2)}\n`);
}

function patchRegionalFactcheck(registry) {
  const asturiasSource = {
    status: "partial",
    source_title: "Tributos del Principado de Asturias · Guía del IBI",
    source_url:
      "https://sede.tributasenasturias.es/sites/sede/default/es_ES/Que-quieres-hacer/IBI/Guia-del-impuesto",
    source_date: TODAY,
    notes:
      "Contraste parcial con fuente oficial general del organismo recaudador. Los tipos, bonificaciones e importes concretos siguen pendientes de ordenanza municipal.",
  };
  const badajozSource = {
    status: "partial",
    source_title: "OAR Diputación de Badajoz · Impuestos, tasas y otros ingresos",
    source_url: "https://oar.dip-badajoz.es/paginas/impuestos-tasas-y-otros",
    source_date: TODAY,
    notes:
      "Contraste parcial con fuente oficial general del organismo recaudador. Los tipos, bonificaciones e importes concretos siguen pendientes de ordenanza municipal.",
  };

  for (const [slug, item] of Object.entries(registry)) {
    if (slug.startsWith("asturias/asturias/")) Object.assign(item, asturiasSource);
    if (slug.startsWith("extremadura/badajoz/")) Object.assign(item, badajozSource);
  }
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildVerificationBlock(entry) {
  if (entry.status === "verified") {
    return `<div class="note"><strong>Estado de verificación editorial:</strong> municipio contrastado con fuente oficial documentada${entry.source_date ? ` (${esc(entry.source_date)})` : ""}. ${entry.notes ? esc(entry.notes) : ""}</div>`;
  }
  if (entry.status === "partial") {
    return `<div class="note"><strong>Estado de verificación editorial:</strong> contraste parcial con fuente oficial general${entry.source_date ? ` (${esc(entry.source_date)})` : ""}. ${entry.notes ? esc(entry.notes) : ""}</div>`;
  }
  return `<div class="note"><strong>Estado de verificación editorial:</strong> revisión editorial realizada, pero el municipio sigue pendiente de contraste oficial completo. Antes de pagar, reclamar o solicitar una bonificación, confirma el dato en la ordenanza fiscal vigente y en el calendario fiscal del ayuntamiento.</div>`;
}

function applyTextFixes(html) {
  const replacements = [
    ["GuÃ­a", "Guía"],
    ["guÃ­a", "guía"],
    ["InformaciÃ³n", "Información"],
    ["informaciÃ³n", "información"],
    ["plusvalÃ­a", "plusvalía"],
    ["electrÃ³nica", "electrónica"],
    ["revisiÃ³n", "revisión"],
    ["verificaciÃ³n", "verificación"],
    ["bonificaciÃ³n", "bonificación"],
    ["bonificaciones e importes concretos siguen pendientes de ordenanza municipal.", "bonificaciones e importes concretos siguen pendientes de ordenanza municipal."],
    ["Ãšltima", "Última"],
    ["rÃºstico", "rústico"],
    ["PerÃ­odo", "Período"],
    ["perÃ­odo", "período"],
    ["mÃ¡s", "más"],
    ["cÃ³mo", "cómo"],
    ["prÃ¡ctica", "práctica"],
    ["CÃ³mo", "Cómo"],
    ["domiciliaciÃ³n", "domiciliación"],
    ["QuÃ©", "Qué"],
    ["telemÃ¡tico", "telemático"],
    ["recaudaciÃ³n", "recaudación"],
    ["InstalaciÃ³n", "Instalación"],
    ["DocumentaciÃ³n", "Documentación"],
    ["lÃ­mites", "límites"],
    ["vacÃ­a", "vacía"],
    ["aquÃ­", "aquí"],
    ["pÃ©rdidas", "pérdidas"],
    ["mÃ©todo", "método"],
    ["aÃ±ade", "añade"],
    ["pÃ¡gina", "página"],
    ["pÃ¡gina", "página"],
    ["pÃ¡ginas", "páginas"],
    ["Â·", "·"],
    ["â€º", "›"],
    ["â‚¬", "€"],
    ["Â©", "©"],
    ["nÂº", "nº"],
    ["Ã±", "ñ"],
    ["Ã¡", "á"],
    ["Ã©", "é"],
    ["Ã­", "í"],
    ["Ã³", "ó"],
    ["Ãº", "ú"],
    ["Ã", "Á"],
    ["Ã‰", "É"],
    ["Ã", "Í"],
    ["Ã“", "Ó"],
    ["Ãš", "Ú"],
    ["Ã‘", "Ñ"],
  ];

  let next = html;
  for (const [from, to] of replacements) {
    next = next.split(from).join(to);
  }
  return next;
}

function updateMunicipalityPage(file, registryEntry, municipality, relatedMap) {
  let html = applyTextFixes(read(file));
  const relativeParts = path.relative(ROOT, file).split(path.sep);
  const communitySlug = relativeParts[0];
  const candidate = registryEntry.candidate || {};
  const candidateValues = candidate.values || {};
  const sourceUrl = registryEntry.source_url || candidate.source_url || candidateValues.electronicOffice || "";
  const sourceTitle = registryEntry.source_title || candidate.source_title || "Fuente oficial municipal";
  const lastReviewed = registryEntry.source_date || candidate.extracted_at || TODAY;
  const electronicOffice = sourceUrl || candidateValues.electronicOffice || "";

  html = html.replace(
    /\.hero\{display:grid;grid-template-columns:1\.2fr \.8fr;gap:18px;margin-bottom:24px\}/,
    `.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:18px;margin-bottom:24px;align-items:start}`
  );

  if (!/\.summary-note\{/.test(html)) {
    html = html.replace(
      /\.hero-side h2,\.sec h2\{font-family:'Playfair Display',serif;font-size:1\.1rem;margin-bottom:10px\}/,
      `.hero-side h2,.sec h2{font-family:'Playfair Display',serif;font-size:1.1rem;margin-bottom:10px}
    .summary-note{font-size:.82rem;color:var(--mid);margin-bottom:10px}`
    );
  }

  if (!/<meta name="robots" content="index, follow, max-image-preview:large">/i.test(html)) {
    html = html.replace(
      /(<meta name="google-adsense-account" content="[^"]+">)/i,
      `$1\n  <meta name="robots" content="index, follow, max-image-preview:large">`
    );
  }

  html = html.replace(
    /"url": "([^"]+)"(?:,\s*"dateModified": "([^"]+)")?\s*\n\s*}/,
    `"url": "$1",\n    "dateModified": "${esc(lastReviewed)}"\n  }`
  );

  html = html.replace(/<p class="meta"><strong>(.*?)<\/strong>([\s\S]*?)<\/p>/, (_, strong, rest) => {
    const cleanedRest = rest
      .replace(/· Última revisión editorial: [^·<]+/g, "")
      .replace(/· Referencia editorial: [\s\S]*$/g, "")
      .trim();
    return `<p class="meta"><strong>${strong}</strong>${cleanedRest ? ` ${cleanedRest}` : ""} · Última revisión editorial: ${esc(lastReviewed)} · Referencia editorial: ${esc(sourceTitle)}</p>`;
  });

  html = html.replace(
    /<div class="note"><strong>Estado de verificación editorial:[\s\S]*?<\/div>/,
    buildVerificationBlock(registryEntry)
  );

  if (sourceUrl && !/Fuente oficial principal:/i.test(html)) {
    html = html.replace(
      /<li><strong>Calendario fiscal municipal:<\/strong>[^<]+<\/li>/,
      (match) =>
        `${match}\n          <li><strong>Fuente oficial principal:</strong> <a href="${esc(sourceUrl)}" target="_blank" rel="nofollow noopener">${esc(sourceTitle)}</a></li>`
    );
  }

  if (electronicOffice) {
    html = html.replace(
      /<li><strong>Sede electrónica:<\/strong> comprobar en la web municipal o recaudación provincial<\/li>/,
      `<li><strong>Sede electrónica:</strong> <a href="${esc(electronicOffice)}" target="_blank" rel="nofollow noopener">${esc(electronicOffice)}</a></li>`
    );
  }

  const ibiUrban = candidateValues.ibiUrban || "0,60%";
  const ibiRustic = candidateValues.ibiRustic || "0,55%";
  const paymentPeriod = candidateValues.paymentPeriod || "Consulta el calendario fiscal municipal";
  const basuraAmount = candidateValues.basuraAmount || "Consultar padrón municipal";
  const boniFamily = candidateValues.boniFamily || "Según ordenanza";
  const solarBoni = candidateValues.solarBoni || "Consultar ordenanza";

  html = html.replace(/<li><strong>IBI urbano:<\/strong> <span class="v">[^<]+<\/span><\/li>/, `<li><strong>IBI urbano:</strong> <span class="v">${esc(ibiUrban)}</span></li>`);
  html = html.replace(/<li><strong>IBI rústico:<\/strong> <span class="v">[^<]+<\/span><\/li>/, `<li><strong>IBI rústico:</strong> <span class="v">${esc(ibiRustic)}</span></li>`);
  html = html.replace(/<li><strong>Período de pago:<\/strong> [^<]+<\/li>/, `<li><strong>Período de pago:</strong> ${esc(paymentPeriod)}</li>`);
  html = html.replace(/<li><strong>Basura vivienda:<\/strong> [^<]+<\/li>/, `<li><strong>Basura vivienda:</strong> ${esc(basuraAmount)}</li>`);
  html = html.replace(/<li><strong>Familia numerosa:<\/strong> [^<]+<\/li>/, `<li><strong>Familia numerosa:</strong> ${esc(boniFamily)}</li>`);

  html = html.replace(/<tr><td>Tipo IBI urbano<\/td><td class="v">[^<]+<\/td><\/tr>/, `<tr><td>Tipo IBI urbano</td><td class="v">${esc(ibiUrban)}</td></tr>`);
  html = html.replace(/<tr><td>Tipo IBI rústico<\/td><td class="v">[^<]+<\/td><\/tr>/, `<tr><td>Tipo IBI rústico</td><td class="v">${esc(ibiRustic)}</td></tr>`);
  html = html.replace(/<tr><td>Calendario de pago<\/td><td>[^<]+<\/td><\/tr>/, `<tr><td>Calendario de pago</td><td>${esc(paymentPeriod)}</td></tr>`);

  html = html.replace(/<tr><td>Familia numerosa<\/td><td class="v">[^<]+<\/td>/, `<tr><td>Familia numerosa</td><td class="v">${esc(boniFamily)}</td>`);
  html = html.replace(/<tr><td>Instalación solar<\/td><td class="v">[^<]+<\/td>/, `<tr><td>Instalación solar</td><td class="v">${esc(solarBoni)}</td>`);


  html = html.replace(
    /<div class="card">\s*<h2>Navegación útil<\/h2>[\s\S]*?<\/div>\s*<div class="card">\s*<h2>Qué cambió en esta URL<\/h2>/,
    `<div class="card">
        <h2>Navegación útil</h2>
        <ul>
          <li><a href="../../../">Inicio</a></li>
          <li><a href="../../../${esc(communitySlug)}/">Volver a la comunidad</a></li>
          <li><a href="../../../municipios/">Ver todos los municipios</a></li>
          <li><a href="../../../ibi-2026/">Guía general del IBI</a></li>
          <li><a href="../../../bonificaciones/">Guía general de bonificaciones</a></li>
          <li><a href="../../../tasa-basuras/">Guía general de tasa de basura</a></li>
          <li><a href="../../../plusvalia/">Guía general de plusvalía</a></li>
        </ul>
      </div>`
  );

  html = html.replace(
    /<div class="card">\s*<h2>Qué cambió en esta URL<\/h2>[\s\S]*?<\/div>\s*<\/aside>/,
    `</aside>`
  );

  html = html.replace(
    /\s*<ul>\s*<li>Una sola página indexable por municipio<\/li>[\s\S]*?<\/div>\s*<\/aside>/,
    `</aside>`
  );

  html = html.replace(
    /<p class="lead">[\s\S]*?<\/p>/,
    `<p class="lead">Consulta aquí el IBI, la tasa de basura, la plusvalía y las bonificaciones municipales, con enlaces oficiales para comprobar cada trámite antes de pagar, domiciliar o presentar una solicitud.</p>`
  );

  html = html.replace(
    /<h2>Resumen rápido<\/h2>/,
    `<h2>Resumen rápido</h2>
      <p style="font-size:.82rem;color:var(--mid);margin-bottom:10px">Datos prácticos para una primera consulta. Confirma siempre el detalle final en la ordenanza y en la sede oficial.</p>`
  );

  html = html.replace(
    /<p>La parte útil para SEO y para el usuario no es repetir una ficha vacía, sino concentrar aquí qué bonificaciones suele consultar la gente y qué documentos debe verificar antes de presentar la solicitud\.<\/p>/,
    ``
  );

  html = html.replace(
    /<p>Para evitar problemas de calidad y contenido thin, esta guía no añade afirmaciones promocionales ni comparativas no verificadas\. Si necesitas confirmar un dato antes de actuar, revisa estas fuentes:<\/p>/,
    `<p>Si necesitas confirmar un dato antes de actuar, revisa estas fuentes:</p>`
  );

  if (!/Pasos recomendados antes de actuar/.test(html)) {
    html = html.replace(
      /<\/main>/,
      `      <section class="sec">
        <h2>Pasos recomendados antes de actuar</h2>
        <ul>
          <li>Revisa la ordenanza vigente y el calendario fiscal del ejercicio.</li>
          <li>Confirma si el recibo se gestiona en el ayuntamiento o en un organismo recaudador.</li>
          <li>Comprueba titular, referencia catastral, plazos y si existe bonificación reconocida.</li>
          <li>Conserva el justificante de pago o la resolución de bonificación si haces un trámite.</li>
        </ul>
      </section>
    </main>`
    );
  }

  html = html
    .replace(/(?:\s*<p(?: class="summary-note"| style="font-size:\.82rem;color:var\(--mid\);margin-bottom:10px")[^>]*>Datos pr[^<]*<\/p>)+/g, "")
    .replace(/<h2>Resumen r[^<]*<\/h2>/, `<h2>Resumen rÃ¡pido</h2>
      <p class="summary-note">Datos prÃ¡cticos para una primera consulta. Confirma siempre el detalle final en la ordenanza y en la sede oficial.</p>`)
    .replace(/(<a href="\.\.\/\.\.\/\.\.\/ibi-2026\/">)[^<]+(<\/a>)/g, `$1IBI 2026 por municipio$2`)
    .replace(/(<a href="\.\.\/\.\.\/\.\.\/bonificaciones\/">)[^<]+(<\/a>)/g, `$1Bonificaciones del IBI$2`)
    .replace(/(<a href="\.\.\/\.\.\/\.\.\/tasa-basuras\/">)[^<]+(<\/a>)/g, `$1Tasa de basura por municipio$2`)
    .replace(/(<a href="\.\.\/\.\.\/\.\.\/plusvalia\/">)[^<]+(<\/a>)/g, `$1PlusvalÃ­a municipal$2`);

  const relatedItems = (relatedMap.get(municipality.slug) || [])
    .map(
      (item) =>
        `<li><a href="../../../${esc(item.communitySlug)}/${esc(item.provinceSlug)}/${esc(item.townSlug)}/">${esc(
          titleFromSlug(item.townSlug)
        )}</a></li>`
    )
    .join("");

  if (relatedItems) {
    if (/<h2>Municipios relacionados<\/h2>/.test(html)) {
      html = html.replace(
        /<section class="sec">\s*<h2>Municipios relacionados<\/h2>[\s\S]*?<\/section>/,
        `      <section class="sec">
        <h2>Municipios relacionados</h2>
        <p>Si también necesitas consultar otro ayuntamiento de la misma provincia, aquí tienes accesos directos a guías municipales cercanas.</p>
        <ul>${relatedItems}</ul>
      </section>`
      );
    } else {
      html = html.replace(
        /<\/main>/,
        `      <section class="sec">
        <h2>Municipios relacionados</h2>
        <p>Si también necesitas consultar otro ayuntamiento de la misma provincia, aquí tienes accesos directos a guías municipales cercanas.</p>
        <ul>${relatedItems}</ul>
      </section>
    </main>`
      );
    }
  }

  write(file, applyTextFixes(html));
}

function main() {
  const registry = loadFactcheck();
  const municipalities = walkMunicipalities();
  const relatedMap = buildRelatedMunicipalities(municipalities);
  patchRegionalFactcheck(registry);
  saveFactcheck(registry);

  for (const municipality of municipalities) {
    updateMunicipalityPage(municipality.mainIndex, registry[municipality.slug] || {}, municipality, relatedMap);
  }

  console.log("enhanced_municipality_pages=1");
}

main();
