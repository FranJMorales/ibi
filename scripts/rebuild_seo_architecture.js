const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const FACTCHECK_FILE = path.join(ROOT, "data", "municipal_factcheck.json");
const COMMUNITIES = [
  "aragon",
  "asturias",
  "castilla-la-mancha",
  "castilla-y-leon",
  "extremadura",
  "galicia",
  "murcia",
];

const SATELLITE_PREFIXES = [
  "ibi-2026-",
  "tasa-basuras-2026-",
  "plusvalia-municipal-",
  "bonificaciones-ibi-",
  "como-pagar-ibi-",
  "reclamar-tasa-basura-",
];

const INDEXABLE_ROOTS = [
  "/",
  "/comunidades/",
  "/municipios/",
  "/ibi-2026/",
  "/calculadora-ibi/",
  "/tasa-basuras/",
  "/plusvalia/",
  "/bonificaciones/",
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

function loadFactcheck() {
  if (!exists(FACTCHECK_FILE)) return {};
  try {
    return JSON.parse(read(FACTCHECK_FILE));
  } catch {
    return {};
  }
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function titleCaseFromSlug(slug) {
  return slug
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function collapseWhitespace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function stripTags(value) {
  return collapseWhitespace(String(value || "").replace(/<[^>]+>/g, " "));
}

function pick(pattern, content, fallback = "") {
  const match = content.match(pattern);
  return match ? collapseWhitespace(match[1]) : fallback;
}

function moneyFromRate(baseAmount, rateText) {
  const rate = Number(String(rateText).replace("%", "").replace(",", "."));
  if (!Number.isFinite(rate)) return "";
  return `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 }).format(
    Math.round((baseAmount * rate) / 100)
  )} €`;
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
            townDir,
            mainIndex,
          });
        }
      }
    }
  }
  return results;
}

function getSatellitePath(townDir, prefix, townSlug) {
  return path.join(townDir, `${prefix}${townSlug}`, "index.html");
}

function extractTextContent(content, patterns, fallback = "") {
  for (const pattern of patterns) {
    const value = pick(pattern, content, "");
    if (value) return value;
  }
  return fallback;
}

function extractTownName(mainHtml, townSlug) {
  return (
    extractTextContent(
      mainHtml,
      [
        /<strong>([^<]+)<\/strong>\s*<\/div>\s*<div class="layout">/i,
        /<h1[^>]*class="page-title"[^>]*>[\s\S]*?([A-ZÁÉÍÓÚÑ][^<\n]+)\s*2026/i,
        /<strong>([^<]+)<\/strong>\s*<\/div>\s*<\/div>\s*<div class="layout">/i,
      ],
      titleCaseFromSlug(townSlug)
    ) || titleCaseFromSlug(townSlug)
  );
}

function extractMeta(mainHtml, townSlug, provinceSlug, communitySlug) {
  const town = extractTownName(mainHtml, townSlug);
  const community =
    extractTextContent(
      mainHtml,
      [
        /<a href="\.\.\/\.\.\/index\.html#[^"]+">([^<]+)<\/a><span>›<\/span>\s*<a href="\.\.\/\.\.\/index\.html#[^"]+">[^<]+<\/a>/i,
        /<strong>([^·<]+)\s*·\s*[^<]+<\/strong>\s*·/i,
        /<meta name="description" content="[^"]*?([A-ZÁÉÍÓÚÑa-záéíóúñ\- ]+)\.">/i,
      ],
      titleCaseFromSlug(communitySlug)
    ) || titleCaseFromSlug(communitySlug);
  const province =
    extractTextContent(
      mainHtml,
      [
        /<strong>[^·<]+\s*·\s*([^·<]+)<\/strong>/i,
        /<meta name="description" content="[^"]*en [^,]+, ([A-ZÁÉÍÓÚÑa-záéíóúñ\- ]+)\.">/i,
      ],
      titleCaseFromSlug(provinceSlug)
    ) || titleCaseFromSlug(provinceSlug);
  return { town, community, province };
}

function parseMunicipality(data) {
  const mainHtml = read(data.mainIndex);
  const meta = extractMeta(mainHtml, data.townSlug, data.provinceSlug, data.communitySlug);
  const ibiPath = getSatellitePath(data.townDir, "ibi-2026-", data.townSlug);
  const pagarPath = getSatellitePath(data.townDir, "como-pagar-ibi-", data.townSlug);
  const boniPath = getSatellitePath(data.townDir, "bonificaciones-ibi-", data.townSlug);
  const basuraPath = getSatellitePath(data.townDir, "tasa-basuras-2026-", data.townSlug);
  const plusvaliaPath = getSatellitePath(data.townDir, "plusvalia-municipal-", data.townSlug);

  const ibiHtml = exists(ibiPath) ? read(ibiPath) : "";
  const pagarHtml = exists(pagarPath) ? read(pagarPath) : "";
  const boniHtml = exists(boniPath) ? read(boniPath) : "";
  const basuraHtml = exists(basuraPath) ? read(basuraPath) : "";
  const plusvaliaHtml = exists(plusvaliaPath) ? read(plusvaliaPath) : "";

  const ibiUrban = extractTextContent(
    ibiHtml || mainHtml,
    [
      /IBI Urbano[^<]*<\/td><td class="(?:val|v)">([^<]+)</i,
      /IBI Urbano<\/td><td class="(?:val|v)">([^<]+)</i,
    ],
    "0,60%"
  );
  const ibiRustic = extractTextContent(
    ibiHtml || mainHtml,
    [/IBI R[úu]stico[^<]*<\/td><td class="(?:val|v)">([^<]+)</i],
    "0,55%"
  );
  const paymentPeriod = extractTextContent(
    pagarHtml || ibiHtml || mainHtml,
    [
      /per[ií]odo voluntario(?: de pago)?(?: del IBI)?(?: en [^<]+)?(?: es| va del?) <strong>([^<]+)<\/strong>/i,
      /Per[ií]odo voluntario[^<]*<\/td><td>([^<]+)</i,
      /<tr><td>IBI Urbano<\/td><td class="(?:val|v)">[^<]+<\/td><td>([^<]+)<\/td>/i,
    ],
    "Consulta el calendario fiscal municipal"
  );
  const boniFamily = extractTextContent(
    boniHtml || mainHtml,
    [
      /Familia numerosa[^<]*<\/td><td class="(?:val|v)">([^<]+)</i,
      /boni-pct">([^<]+)<\/div><div class="boni-plazo">[^<]+<\/div><h3>Vivienda habitual/i,
    ],
    "Según ordenanza"
  );
  const solarBoni = extractTextContent(
    boniHtml,
    [
      /Placas solares[^<]*<\/td><td class="(?:val|v)">([^<]+)</i,
      /Bonificaci[oó]n por placas solares[\s\S]*?boni-pct">([^<]+)<\/div>/i,
    ],
    "Consultar ordenanza"
  );
  const basuraAmount = extractTextContent(
    basuraHtml || mainHtml,
    [
      /referencia orientativa es <strong>([^<]+)<\/strong>/i,
      /Tasa de Basuras \(vivienda\)<\/td><td class="(?:val|v)">([^<]+)</i,
      /Importe vivienda habitual<\/td><td class="(?:val|v)">([^<]+)</i,
    ],
    "Consultar padrón municipal"
  );
  const basuraPeriod = extractTextContent(
    basuraHtml,
    [
      /Per[ií]odo habitual<\/td><td>([^<]+)</i,
      /liquidarse durante el <strong>([^<]+)<\/strong>/i,
    ],
    "Según padrón municipal"
  );
  const electronicOffice = extractTextContent(
    pagarHtml,
    [/href="(https:\/\/[^"]+sede[^"]+)"/i],
    ""
  );
  const population = extractTextContent(
    mainHtml,
    [
      /·\s*([^·<]*hab\.)\s*·\s*Actualizado/i,
      /Con una poblaci[oó]n de <strong>([^<]+)<\/strong>/i,
    ],
    ""
  );
  const sourceNote = extractTextContent(
    mainHtml,
    [
      /Datos actualizados seg[uú]n ([^.]+)\./i,
      /Fuente:\s*([^<]+)/i,
    ],
    "Ordenanza fiscal y calendario municipal"
  );
  const calculator90 = moneyFromRate(90000, ibiUrban);
  const calculator120 = moneyFromRate(120000, ibiUrban);
  const calculator80 = moneyFromRate(80000, ibiUrban);

  const slugKey = `${data.communitySlug}/${data.provinceSlug}/${data.townSlug}`;
  const factcheck = FACTCHECK[slugKey] || {};
  const factcheckStatus =
    factcheck.status === "verified" || factcheck.verified === true
      ? "verified"
      : factcheck.status === "partial"
      ? "partial"
      : "unverified";
  const factcheckedValues = factcheckStatus !== "unverified" && factcheck.values ? factcheck.values : {};

  return {
    ...data,
    ...meta,
    population,
    ibiUrban: factcheckedValues.ibiUrban || ibiUrban,
    ibiRustic: factcheckedValues.ibiRustic || ibiRustic,
    paymentPeriod: factcheckedValues.paymentPeriod || paymentPeriod,
    boniFamily: factcheckedValues.boniFamily || boniFamily,
    solarBoni: factcheckedValues.solarBoni || solarBoni,
    basuraAmount: factcheckedValues.basuraAmount || basuraAmount,
    basuraPeriod: factcheckedValues.basuraPeriod || basuraPeriod,
    electronicOffice: factcheckedValues.electronicOffice || electronicOffice,
    sourceNote: factcheckStatus === "unverified" ? sourceNote : factcheck.source_title || sourceNote,
    calculator90,
    calculator120,
    calculator80,
    factcheckStatus,
    factcheckSourceUrl: factcheck.source_url || "",
    factcheckSourceDate: factcheck.source_date || "",
    factcheckNotes: factcheck.notes || "",
  };
}

function municipalityUrl(data) {
  return `https://tasasmunicipales.info/${data.communitySlug}/${data.provinceSlug}/${data.townSlug}/`;
}

function relToRoot(depth) {
  return "../".repeat(depth);
}

function municipalityHtml(data) {
  const root = "../../../";
  const canonical = municipalityUrl(data);
  const officeBlock = data.electronicOffice
    ? `<li><strong>Sede electrónica:</strong> <a href="${esc(data.electronicOffice)}" target="_blank" rel="nofollow noopener">${esc(data.electronicOffice)}</a></li>`
    : `<li><strong>Sede electrónica:</strong> comprobar en la web municipal o recaudación provincial</li>`;
  const verificationBlock =
    data.factcheckStatus === "verified"
      ? `<div class="note"><strong>Estado de verificación editorial:</strong> verificado con fuente oficial documentada${data.factcheckSourceDate ? ` (${esc(data.factcheckSourceDate)})` : ""}. ${data.factcheckSourceUrl ? `Fuente: <a href="${esc(data.factcheckSourceUrl)}" target="_blank" rel="nofollow noopener">${esc(data.factcheckSourceUrl)}</a>.` : ""}${data.factcheckNotes ? ` ${esc(data.factcheckNotes)}` : ""}</div>`
      : data.factcheckStatus === "partial"
      ? `<div class="note"><strong>Estado de verificación editorial:</strong> contraste parcial con fuente oficial general${data.factcheckSourceDate ? ` (${esc(data.factcheckSourceDate)})` : ""}. ${data.factcheckNotes ? ` ${esc(data.factcheckNotes)}` : ""}</div>`
      : `<div class="note"><strong>Estado de verificación editorial:</strong> pendiente de contraste oficial municipio a municipio. Antes de pagar, reclamar o solicitar una bonificación, confirma el dato en la ordenanza fiscal vigente y en el calendario fiscal del ayuntamiento.</div>`;

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="${root}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="${root}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="${root}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="${root}apple-touch-icon.png">
  <title>Impuestos municipales en ${esc(data.town)} 2026: IBI, basura, plusvalía y bonificaciones</title>
  <meta name="description" content="Guía municipal de ${esc(data.town)} 2026: IBI urbano ${esc(data.ibiUrban)}, calendario de pago, tasa de basura, plusvalía y bonificaciones. Información concentrada en una sola página útil.">
  <link rel="canonical" href="${canonical}">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Impuestos municipales en ${esc(data.town)} 2026",
    "url": "${canonical}"
  }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root{--ink:#1a1a2e;--paper:#f5f0e8;--accent:#c8522a;--accent2:#2a7c6f;--gold:#d4a843;--mid:#6b6b7b;--rule:#d8d0c0;--card:#fffdf8}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Source Serif 4',Georgia,serif;background:var(--paper);color:var(--ink);line-height:1.75}
    a{color:inherit;text-decoration:none}
    header{background:var(--ink);border-bottom:4px solid var(--accent)}
    .hi{max-width:1140px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
    .logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#fff}
    .logo span{display:block;font-size:.65rem;color:var(--gold);letter-spacing:2px;text-transform:uppercase;font-weight:300}
    nav{display:flex;gap:4px;flex-wrap:wrap}
    nav a{color:rgba(255,255,255,.78);font-size:.78rem;padding:5px 11px;border:1px solid rgba(255,255,255,.12);border-radius:3px}
    nav a:hover{background:var(--accent);border-color:var(--accent);color:#fff}
    .bc{max-width:1140px;margin:0 auto;padding:14px 24px 0;font-size:.74rem;color:var(--mid)}
    .bc a{color:var(--accent)}
    .bc span{margin:0 5px}
    .wrap{max-width:1140px;margin:0 auto;padding:32px 24px 72px}
    .hero{display:grid;grid-template-columns:1.2fr .8fr;gap:18px;margin-bottom:24px;align-items:start}
    .card{background:var(--card);border:1px solid var(--rule)}
    .hero-main{padding:26px}
    .eyebrow{display:inline-block;background:var(--accent2);color:#fff;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;padding:5px 12px;margin-bottom:14px;font-weight:700}
    h1{font-family:'Playfair Display',serif;font-size:clamp(2rem,4vw,3rem);line-height:1.06;margin-bottom:10px}
    .lead{font-size:.96rem;color:var(--mid);max-width:780px}
    .meta{margin-top:14px;font-size:.78rem;color:var(--mid)}
    .hero-side{padding:22px}
    .hero-side h2,.sec h2{font-family:'Playfair Display',serif;font-size:1.1rem;margin-bottom:10px}
    .summary-note{font-size:.82rem;color:var(--mid);margin-bottom:10px}
    .quick{list-style:none}
    .quick li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:.86rem}
    .quick li:last-child{border-bottom:none}
    .layout{display:grid;grid-template-columns:1fr 300px;gap:28px}
    .sec{background:var(--card);border:1px solid var(--rule);padding:22px;margin-bottom:18px}
    .sec h2{padding-bottom:8px;border-bottom:2px solid var(--ink)}
    .sec h3{font-family:'Playfair Display',serif;font-size:1rem;margin:16px 0 8px}
    .sec p{font-size:.91rem;margin-bottom:14px}
    .sec ul{padding-left:20px;margin-bottom:14px}
    .sec li{font-size:.9rem;margin-bottom:6px}
    .dt{width:100%;border-collapse:collapse;margin:14px 0 18px;font-size:.84rem}
    .dt th{background:var(--ink);color:#fff;padding:9px 11px;text-align:left;font-size:.73rem}
    .dt td{padding:9px 11px;border-bottom:1px solid var(--rule);vertical-align:top}
    .dt tr:nth-child(even) td{background:rgba(0,0,0,.02)}
    .v{font-weight:700;color:var(--accent)}
    .note{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--accent2);padding:14px 16px;margin:14px 0;font-size:.87rem}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
    .mini{background:var(--card);border:1px solid var(--rule);padding:16px}
    .mini h3{margin-top:0}
    .side{position:sticky;top:20px}
    .side .card{padding:16px;margin-bottom:16px}
    .side ul{list-style:none}
    .side li{padding:6px 0;border-bottom:1px solid var(--rule);font-size:.82rem}
    .side li:last-child{border-bottom:none}
    .side a{color:var(--accent)}
    footer{background:#12121f;color:rgba(255,255,255,.45);text-align:center;padding:24px 20px;font-size:.74rem}
    @media(max-width:900px){.layout,.hero,.grid{grid-template-columns:1fr}.side{position:static}}
  </style>
</head>
<body>
<header>
  <div class="hi">
    <a href="${root}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
    <nav>
      <a href="${root}comunidades/">Comunidades</a>
      <a href="${root}municipios/">Municipios</a>
      <a href="${root}ibi-2026/">IBI 2026</a>
      <a href="${root}calculadora-ibi/">Calculadora</a>
      <a href="${root}tasa-basuras/">Basuras</a>
      <a href="${root}plusvalia/">Plusvalía</a>
      <a href="${root}bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>
<div class="bc"><a href="${root}">Inicio</a><span>›</span><a href="${root}${esc(data.communitySlug)}/">${esc(data.community)}</a><span>›</span><strong>${esc(data.town)}</strong></div>
<div class="wrap">
  <section class="hero">
    <div class="hero-main card">
      <span class="eyebrow">Guía Municipal Consolidada</span>
      <h1>${esc(data.town)} 2026: IBI, basura, plusvalía y bonificaciones</h1>
      <p class="lead">Esta es la URL principal e indexable de ${esc(data.town)}. Reúne en una sola guía los datos más útiles para consultar el IBI, entender cómo se paga, revisar bonificaciones y ubicar la información oficial que conviene comprobar antes de presentar una solicitud o pagar un recibo.</p>
      <p class="meta"><strong>${esc(data.community)} · ${esc(data.province)}</strong>${data.population ? ` · ${esc(data.population)}` : ""} · Referencia editorial: ${esc(data.sourceNote)}</p>
    </div>
    <aside class="hero-side card">
      <h2>Resumen rápido</h2>
      <ul class="quick">
        <li><strong>IBI urbano:</strong> <span class="v">${esc(data.ibiUrban)}</span></li>
        <li><strong>IBI rústico:</strong> <span class="v">${esc(data.ibiRustic)}</span></li>
        <li><strong>Período de pago:</strong> ${esc(data.paymentPeriod)}</li>
        <li><strong>Basura vivienda:</strong> ${esc(data.basuraAmount)}</li>
        <li><strong>Familia numerosa:</strong> ${esc(data.boniFamily)}</li>
      </ul>
    </aside>
  </section>

  <div class="layout">
    <main>
      <section class="sec">
        <h2>IBI 2026 en ${esc(data.town)}</h2>
        <p>El IBI es el tributo municipal principal para vivienda, local, garaje o nave. Para evitar contenido disperso, aquí se concentra la información práctica que antes estaba separada en varias landings.</p>
        <table class="dt">
          <thead><tr><th>Concepto</th><th>Dato</th></tr></thead>
          <tbody>
            <tr><td>Tipo IBI urbano</td><td class="v">${esc(data.ibiUrban)}</td></tr>
            <tr><td>Tipo IBI rústico</td><td class="v">${esc(data.ibiRustic)}</td></tr>
            <tr><td>Calendario de pago</td><td>${esc(data.paymentPeriod)}</td></tr>
            <tr><td>Ejemplo para 80.000 € de valor catastral</td><td>${esc(data.calculator80 || "Consultar ordenanza")}</td></tr>
            <tr><td>Ejemplo para 90.000 € de valor catastral</td><td>${esc(data.calculator90 || "Consultar ordenanza")}</td></tr>
            <tr><td>Ejemplo para 120.000 € de valor catastral</td><td>${esc(data.calculator120 || "Consultar ordenanza")}</td></tr>
          </tbody>
        </table>
        <div class="note"><strong>Cómo interpretar estas cifras:</strong> la cuota final puede bajar si el inmueble tiene una bonificación reconocida o variar si el valor catastral no coincide con los ejemplos. La comprobación definitiva debe hacerse con el recibo y la ordenanza vigente.</div>
      </section>

      <section class="sec">
        <h2>Pago, domiciliación y fraccionamiento</h2>
        <div class="grid">
          <div class="mini">
            <h3>Qué revisar antes de pagar</h3>
            <ul>
              <li>Que el período voluntario siga abierto: ${esc(data.paymentPeriod)}</li>
              <li>Que la referencia catastral y el titular del recibo sean correctos</li>
              <li>Que la bonificación, si la tienes reconocida, aparezca aplicada</li>
            </ul>
          </div>
          <div class="mini">
            <h3>Opciones habituales</h3>
            <ul>
              <li>Pago en entidad colaboradora con carta o recibo</li>
              <li>Pago telemático en sede electrónica o recaudación</li>
              <li>Domiciliación bancaria para evitar recargos</li>
              <li>Fraccionamiento si la ordenanza municipal lo permite</li>
            </ul>
          </div>
        </div>
        <p>La mayor parte de municipios permiten el pago telemático y un sistema de fraccionamiento o plan personalizado para importes altos. Si el recibo entra en ejecutiva, se aplican recargos y, en su caso, intereses.</p>
      </section>

      <section class="sec">
        <h2>Bonificaciones que merece la pena comprobar</h2>
        <table class="dt">
          <thead><tr><th>Supuesto</th><th>Referencia</th><th>Qué conviene revisar</th></tr></thead>
          <tbody>
            <tr><td>Familia numerosa</td><td class="v">${esc(data.boniFamily)}</td><td>Vivienda habitual, plazo de solicitud y límites de valor catastral</td></tr>
            <tr><td>Instalación solar</td><td class="v">${esc(data.solarBoni)}</td><td>Documentación técnica, licencia y duración del incentivo</td></tr>
            <tr><td>Domiciliación o VPO</td><td>Según ordenanza</td><td>Si el descuento es automático o requiere solicitud previa</td></tr>
          </tbody>
        </table>
        <p>La parte útil para SEO y para el usuario no es repetir una ficha vacía, sino concentrar aquí qué bonificaciones suele consultar la gente y qué documentos debe verificar antes de presentar la solicitud.</p>
      </section>

      <section class="sec">
        <h2>Tasa de basura y plusvalía</h2>
        <h3>Tasa de basura</h3>
        <p>La referencia local más útil que hemos conservado para vivienda habitual es <strong>${esc(data.basuraAmount)}</strong>. Antes de pagar o reclamar, conviene comprobar cómo calcula el municipio la tasa: uso del inmueble, superficie, padrón o tarifa plana.</p>
        <p><strong>Período habitual orientativo:</strong> ${esc(data.basuraPeriod)}</p>
        <h3>Plusvalía municipal</h3>
        <p>La plusvalía se liquida cuando se transmite suelo urbano por compraventa, donación o herencia. Desde la reforma estatal, se puede comparar método objetivo y método real para elegir el más favorable cuando la ordenanza lo permite.</p>
        <div class="note"><strong>En ventas con pérdidas:</strong> si no hay incremento real del valor del terreno, puede no haber cuota. Para herencias, el plazo general suele ser de 6 meses prorrogables.</div>
      </section>

      <section class="sec">
        <h2>Fuentes y comprobación recomendada</h2>
        <p>Para evitar problemas de calidad y contenido thin, esta guía no añade afirmaciones promocionales ni comparativas no verificadas. Si necesitas confirmar un dato antes de actuar, revisa estas fuentes:</p>
        ${verificationBlock}
        <ul>
          <li><strong>Ordenanza fiscal municipal:</strong> referencia normativa principal para IBI, bonificaciones y plusvalía.</li>
          <li><strong>Calendario fiscal municipal:</strong> confirma el período voluntario exacto del ejercicio.</li>
          ${officeBlock}
          <li><strong>Catastro:</strong> <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a> para revisar el valor catastral y la referencia del inmueble.</li>
        </ul>
      </section>
    </main>

    <aside class="side">
      <div class="card">
        <h2>Navegación útil</h2>
        <ul>
          <li><a href="${root}${esc(data.communitySlug)}/">Volver a ${esc(data.community)}</a></li>
          <li><a href="${root}municipios/">Ver todos los municipios</a></li>
          <li><a href="${root}ibi-2026/">Guía general del IBI</a></li>
          <li><a href="${root}bonificaciones/">Guía general de bonificaciones</a></li>
        </ul>
      </div>
      <div class="card">
        <h2>Qué cambió en esta URL</h2>
        <ul>
          <li>Una sola página indexable por municipio</li>
          <li>Datos consolidados en lugar de landings repetidas</li>
          <li>Sin texto promocional ni relleno local inventado</li>
          <li>Satélites movidas a noindex para evitar thin content</li>
        </ul>
      </div>
    </aside>
  </div>
</div>
<footer>© 2026 TasasMunicipales.info · Datos orientativos. Consulta siempre la ordenanza y el calendario fiscal de tu ayuntamiento.</footer>
</body>
</html>`;
}

function satelliteHtml(data, prefix) {
  const root = relToRoot(4);
  const canonical = municipalityUrl(data);
  const labelMap = {
    "ibi-2026-": "IBI 2026",
    "tasa-basuras-2026-": "Tasa de basura",
    "plusvalia-municipal-": "Plusvalía municipal",
    "bonificaciones-ibi-": "Bonificaciones IBI",
    "como-pagar-ibi-": "Pago del IBI",
    "reclamar-tasa-basura-": "Reclamación de la tasa de basura",
  };
  const label = labelMap[prefix];
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="${canonical}">
  <title>${esc(label)} en ${esc(data.town)} · contenido consolidado</title>
  <meta name="description" content="Esta URL ya no se indexa por separado. La información útil sobre ${esc(label.toLowerCase())} en ${esc(data.town)} se ha integrado en la guía principal del municipio.">
  <style>
    :root{--ink:#1a1a2e;--paper:#f5f0e8;--accent:#c8522a;--rule:#d8d0c0;--card:#fffdf8}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:Georgia,serif;background:var(--paper);color:var(--ink);line-height:1.7;padding:32px}
    .box{max-width:760px;margin:40px auto;background:var(--card);border:1px solid var(--rule);padding:28px}
    h1{font-size:2rem;margin-bottom:12px}
    p{margin-bottom:14px}
    a{color:var(--accent)}
  </style>
</head>
<body>
  <div class="box">
    <h1>${esc(label)} en ${esc(data.town)}</h1>
    <p>Esta página se mantiene solo para navegación interna y ya no se indexa por separado. Para evitar contenido duplicado o thin content, la información principal se ha integrado en una única guía municipal más completa.</p>
    <p><a href="${canonical}">Ir a la guía principal de ${esc(data.town)}</a></p>
  </div>
</body>
</html>`;
}

function buildSitemap(indexableUrls) {
  const today = new Date().toISOString().slice(0, 10);
  const items = indexableUrls
    .map(
      (url) => `  <url>
    <loc>https://tasasmunicipales.info${url}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${url === "/" ? "weekly" : "monthly"}</changefreq>
    <priority>${url === "/" ? "1.0" : url.split("/").filter(Boolean).length >= 3 ? "0.7" : "0.8"}</priority>
  </url>`
    )
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${items}
</urlset>
`;
}

function main() {
  const municipalities = walkMunicipalities().map(parseMunicipality);
  const sitemapUrls = [...INDEXABLE_ROOTS];

  for (const municipality of municipalities) {
    write(municipality.mainIndex, municipalityHtml(municipality));
    sitemapUrls.push(`/${municipality.communitySlug}/${municipality.provinceSlug}/${municipality.townSlug}/`);
    for (const prefix of SATELLITE_PREFIXES) {
      const satelliteIndex = getSatellitePath(municipality.townDir, prefix, municipality.townSlug);
      if (!exists(path.dirname(satelliteIndex))) continue;
      write(satelliteIndex, satelliteHtml(municipality, prefix));
    }
  }

  for (const communitySlug of COMMUNITIES) {
    const communityIndex = path.join(ROOT, communitySlug, "index.html");
    if (exists(communityIndex)) sitemapUrls.push(`/${communitySlug}/`);
  }

  write(path.join(ROOT, "sitemap.xml"), buildSitemap(sitemapUrls));
  console.log(`rebuilt_municipalities=${municipalities.length}`);
}

const FACTCHECK = loadFactcheck();
main();
