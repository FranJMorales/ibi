const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const COMMUNITIES = [
  "aragon",
  "castilla-la-mancha",
  "castilla-y-leon",
  "extremadura",
  "galicia",
  "murcia",
];

const ARTICLE_TYPES = [
  "ibi-2026",
  "tasa-basuras-2026",
  "plusvalia-municipal",
  "bonificaciones-ibi",
  "como-pagar-ibi",
  "reclamar-tasa-basura",
];

const NATIVE_AD_BLOCK = `
    <div class="tm-native-ad" aria-label="Publicidad">
      <div class="tm-native-ad-label">Publicidad</div>
      <script async="async" data-cfasync="false" src="https://pl28952826.profitablecpmratenetwork.com/668e307b638c1713b6b2ebc83aab889c/invoke.js"></script>
      <div id="container-668e307b638c1713b6b2ebc83aab889c"></div>
    </div>
`;

const BASE_CSS = `
    :root{--ink:#1a1a2e;--paper:#f5f0e8;--accent:#c8522a;--accent2:#2a7c6f;--gold:#d4a843;--mid:#6b6b7b;--rule:#d8d0c0;--card-bg:#fffdf8;--card:var(--card-bg)}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Source Serif 4',Georgia,serif;background:var(--paper);color:var(--ink);line-height:1.75}
    header{background:var(--ink);border-bottom:4px solid var(--accent);padding:14px 24px}
    .hi{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
    .logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#fff;text-decoration:none;display:flex;flex-direction:column;gap:2px}
    .logo span{font-family:'Source Serif 4',Georgia,serif;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.62)}
    nav a{color:rgba(255,255,255,.75);text-decoration:none;font-size:.8rem;margin-left:12px}
    .bc{max-width:1100px;margin:0 auto;padding:14px 24px 0;font-size:.75rem;color:var(--mid)}
    .bc a{color:var(--accent);text-decoration:none}.bc span{margin:0 5px}
    .wrap{max-width:1100px;margin:0 auto;padding:24px 24px 60px}
    .art-layout{display:grid;grid-template-columns:1fr 280px;gap:44px;align-items:start}
    .tag{display:inline-block;color:#fff;font-size:.66rem;letter-spacing:2px;text-transform:uppercase;padding:4px 12px;margin-bottom:14px}
    .t-r{background:var(--accent)}.t-g{background:var(--accent2)}.t-o{background:#b65a2a}.t-d{background:var(--ink)}
    h1{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,3vw,2.2rem);font-weight:900;line-height:1.15;margin-bottom:8px}
    .art-meta{font-size:.74rem;color:var(--mid);margin-bottom:26px}
    .toc-box{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--ink);padding:14px 18px;margin-bottom:28px}
    .toc-box h2{font-size:.76rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;color:var(--mid);border:0;padding:0}
    .toc-box ol{padding-left:18px}.toc-box li{font-size:.83rem;margin-bottom:4px}.toc-box a{color:var(--accent);text-decoration:none}
    main h2{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;margin:28px 0 10px;padding-top:6px;border-top:1px solid var(--rule)}
    main h3{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;margin:16px 0 6px}
    main p{margin-bottom:14px;font-size:.9rem} main ul{padding-left:20px;margin-bottom:14px}
    main ul li{font-size:.9rem;margin-bottom:6px} main a{color:var(--accent)}
    .intro-box,.highlight-box,.method-card,.step,.boni-card{background:var(--card);border:1px solid var(--rule);padding:14px 18px;margin:16px 0}
    .intro-box,.highlight-box{border-left:4px solid var(--accent2)}
    .intro-box{margin:0 0 24px;font-size:.9rem;line-height:1.7}
    .highlight-box strong{display:block;margin-bottom:5px}
    .method-card{display:flex;gap:16px;align-items:flex-start}
    .method-icon{font-size:1.8rem;flex-shrink:0}
    .step{border-left:4px solid var(--accent);display:flex;gap:14px;align-items:flex-start}
    .step-num{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:900;color:var(--accent);flex-shrink:0;line-height:1}
    .boni-card{border-left:4px solid var(--accent2)} .boni-pct{font-size:1.4rem;font-weight:900;color:var(--accent);float:right}
    .boni-plazo{font-size:.76rem;background:var(--paper);border:1px solid var(--rule);display:inline-block;padding:2px 8px;color:var(--mid);margin-bottom:8px}
    .faq-item{border:1px solid var(--rule);margin-bottom:10px;overflow:hidden}
    .faq-q{background:var(--card);padding:12px 16px;font-weight:700;font-size:.88rem}.faq-a{padding:12px 16px;font-size:.84rem;color:var(--mid);border-top:1px solid var(--rule)}
    .data-table{width:100%;border-collapse:collapse;margin:14px 0 22px;font-size:.83rem}
    .data-table th{background:var(--ink);color:#fff;padding:8px 11px;text-align:left;font-size:.73rem;letter-spacing:.5px}
    .data-table td{padding:8px 11px;border-bottom:1px solid var(--rule)} .data-table tr:nth-child(even) td{background:rgba(0,0,0,.025)}
    .tm-native-ad{margin:22px 0 30px;padding:14px 16px 16px;background:var(--card);border:1px solid var(--rule);border-radius:6px;box-shadow:0 8px 20px rgba(26,26,46,.04)}
    .tm-native-ad-label{font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mid);margin-bottom:10px;font-weight:700}
    .tm-native-ad > div[id^="container-"]{min-height:90px}
    .val{font-weight:700;color:var(--accent)} .sidebar{position:sticky;top:20px}
    .s-block{background:var(--card);border:1px solid var(--rule);margin-bottom:16px;overflow:hidden}.s-head{background:var(--ink);color:#fff;padding:10px 14px;font-family:'Playfair Display',serif;font-size:.88rem;font-weight:700}
    .s-body{padding:12px 14px}.s-list{list-style:none;padding:0}.s-list li{padding:5px 0;border-bottom:1px solid var(--rule);font-size:.8rem}.s-list li:last-child{border-bottom:none}
    .s-list a{color:var(--ink);text-decoration:none}.s-btn{display:block;background:var(--accent);color:#fff;text-align:center;padding:10px;text-decoration:none;font-weight:600;font-size:.8rem;margin-top:8px}
    .info-grid{list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.83rem;padding-left:0}.info-grid li{margin-bottom:0}
    footer{background:#12121f;color:rgba(255,255,255,.45);text-align:center;padding:24px;font-size:.75rem}
    @media (max-width:768px){.art-layout{grid-template-columns:1fr}.info-grid{grid-template-columns:1fr}.method-card,.step{flex-direction:column;gap:8px}}
`;

function read(file) { return fs.readFileSync(file, "utf8"); }
function write(file, text) { fs.writeFileSync(file, text, "utf8"); }
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function slugToName(slug) { return slug.split("-").map(p => p ? p[0].toUpperCase() + p.slice(1) : p).join(" "); }
function pick(re, text, fallback = "") { const m = text.match(re); return m ? m[1].trim() : fallback; }
function money(n) { return new Intl.NumberFormat("es-ES").format(Math.round(n)); }

function articleLabel(type, town) {
  return {
    "ibi-2026": `IBI 2026 · ${town}`,
    "tasa-basuras-2026": `Basuras 2026 · ${town}`,
    "plusvalia-municipal": `Plusvalía · ${town}`,
    "bonificaciones-ibi": `Bonificaciones · ${town}`,
    "como-pagar-ibi": `Pago IBI · ${town}`,
    "reclamar-tasa-basura": `Reclamaciones · ${town}`,
  }[type];
}

function pageTitle(type, d) {
  return {
    "ibi-2026": `IBI 2026 en ${d.town}: tipo ${d.ibiUrbano}, cuándo se paga y cómo fraccionar`,
    "tasa-basuras-2026": `Tasa de basura ${d.town} 2026: importe, quién la paga y cómo reclamar`,
    "plusvalia-municipal": `Plusvalía municipal ${d.town}: calcular, pagar y plazos`,
    "bonificaciones-ibi": `Bonificaciones IBI ${d.town} 2026: familia numerosa, solar y domiciliación`,
    "como-pagar-ibi": `Cómo pagar el IBI en ${d.town} 2026: online, banco y fraccionamiento`,
    "reclamar-tasa-basura": `Cómo reclamar la tasa de basura en ${d.town}: recurso, errores y exenciones`,
  }[type];
}

function desc(type, d) {
  return {
    "ibi-2026": `IBI ${d.town} 2026: tipo ${d.ibiUrbano}. Fechas de cobro, cálculo del recibo, fraccionamiento y bonificaciones disponibles en ${d.province}.`,
    "tasa-basuras-2026": `Tasa de basura en ${d.town} 2026: importe orientativo ${d.basura}, quién debe pagarla, plazos y cómo recurrir un recibo incorrecto.`,
    "plusvalia-municipal": `Guía de plusvalía municipal en ${d.town}: cálculo, plazos, exenciones y qué método conviene al vender o heredar.`,
    "bonificaciones-ibi": `Bonificaciones del IBI en ${d.town}: familia numerosa, placas solares, vivienda protegida y descuentos por domiciliación.`,
    "como-pagar-ibi": `Cómo pagar el IBI en ${d.town}: banca colaboradora, pago online, domiciliación y fraccionamiento sin intereses.`,
    "reclamar-tasa-basura": `Cómo reclamar la tasa de basura en ${d.town}: errores en el recibo, recurso de reposición, exenciones y documentación.`,
  }[type];
}

function foot(up = "../../../../") {
  return `<footer><div style="max-width:1100px;margin:0 auto;padding:16px 24px 8px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:.72rem;color:rgba(255,255,255,.4);"><span>© 2026 TasasMunicipales.info · La información no constituye asesoramiento fiscal.</span><span>Datos orientativos. Consulta siempre tu ayuntamiento.</span></div></footer>`;
}

function sidebar(d, active) {
  const items = [
    ["ibi-2026", "🏠", "Ficha municipal", `../`],
    ["tasa-basuras-2026", "🗑️", "Tasa de basuras", `../`],
    ["plusvalia-municipal", "📈", "Plusvalía municipal", `../`],
    ["bonificaciones-ibi", "🎁", "Bonificaciones IBI", `../`],
    ["como-pagar-ibi", "💳", "Cómo pagar el IBI", `../`],
    ["reclamar-tasa-basura", "⚖️", "Reclamar tasa basura", `../`],
  ];
  const lis = items.map(([k, icon, label, href]) => `<li>${icon} <a href="${href}">${k === active ? `<strong>${label}</strong>` : label}</a></li>`).join("");
  return `<aside class="sidebar"><div class="s-block"><div class="s-head">📋 ${esc(d.town)}: todas las tasas</div><div class="s-body"><ul class="s-list">${lis}</ul><a href="../" class="s-btn">← Volver a ${esc(d.town)}</a></div></div><div class="s-block"><div class="s-head">📂 Comunidad: ${esc(d.community)}</div><div class="s-body"><ul class="s-list"><li><a href="../../../../${d.slugCommunity}/">← Municipios de ${esc(d.community)}</a></li></ul></div></div></aside>`;
}

function moreInfo(d) {
  return `<h2>Más información sobre ${esc(d.town)}</h2><ul class="info-grid"><li>🏠 <a href="../">Guía municipal de ${esc(d.town)}</a></li><li>🗑️ <a href="../#tasa-basuras">Tasa de basuras ${esc(d.town)}</a></li><li>📈 <a href="../#plusvalia">Plusvalía municipal ${esc(d.town)}</a></li><li>🎁 <a href="../#bonificaciones">Bonificaciones IBI ${esc(d.town)}</a></li></ul>`;
}

function injectArticleAd(body) {
  if (body.includes('class="tm-native-ad"')) return body;
  if (body.includes('class="intro-box"')) {
    return body.replace(/(<div class="intro-box">[\s\S]*?<\/div>)/, `$1${NATIVE_AD_BLOCK}`);
  }
  if (body.includes('class="toc-box"')) {
    return body.replace(/(<div class="toc-box">[\s\S]*?<\/div>)/, `$1${NATIVE_AD_BLOCK}`);
  }
  return `${NATIVE_AD_BLOCK}${body}`;
}

function loadData(dir) {
  const landing = read(path.join(dir, "index.html"));
  const rel = path.relative(ROOT, dir).split(path.sep);
  const slugCommunity = rel[0];
  const slugProvince = rel[1];
  const slugTown = rel[2];
  const town = pick(/<strong>([^<]+)<\/strong><\/div>[\s\S]*?<div class="wrap">/, landing) || slugToName(slugTown);
  const loc = pick(/<p[^>]*>([^<]+hab\.)<\/p>/, landing, "");
  const [community = slugToName(slugCommunity), province = slugToName(slugProvince), population = ""] = loc.split("·").map(x => x.trim());
  const ibiUrbano = pick(/<tr><td>IBI Urbano<\/td><td class="val">([^<]+)/, landing, "0,60%");
  const ibiRustico = pick(/<tr><td>IBI R[^<]*<\/td><td class="val">([^<]+)/, landing, "0,55%");
  const basura = pick(/<tr><td>Tasa de Basuras \(vivienda\)<\/td><td class="val">([^<]+)/, landing, "~100 €/año");
  const plusvalia = pick(/<tr><td>Plusval[ií]a Municipal<\/td><td class="val">([^<]+)/, landing, "Calculadora disponible");
  const boni = pick(/<tr><td>Bonificaci[^<]+<\/td><td class="val">([^<]+)/, landing, "Hasta 25%");
  const periodo = pick(/<tr><td>IBI Urbano<\/td><td class="val">[^<]+<\/td><td>([^<]+)/, landing, "1 oct – 30 nov 2026");
  const cuota90 = pick(/cuota bruta asciende a <strong>([^<]+)/, landing, "");
  const cuota90Num = Number((cuota90.match(/[\d\.]+/) || ["0"])[0].replace(/\./g, ""));
  return { slugCommunity, slugProvince, slugTown, town, community, province, population, ibiUrbano, ibiRustico, basura, plusvalia, boni, periodo, cuota90, cuota90Num };
}

function layout(type, d, body) {
  const up = "../../../../";
  const rootHref = `${up}`;
  const canonical = `https://tasasmunicipales.info/${d.slugCommunity}/${d.slugProvince}/${d.slugTown}/${type}-${d.slugTown}/`;
  return `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><link rel="icon" type="image/x-icon" href="${up}favicon.ico"><link rel="icon" type="image/svg+xml" href="${up}favicon.svg"><link rel="icon" type="image/png" sizes="32x32" href="${up}favicon-32x32.png"><link rel="apple-touch-icon" sizes="180x180" href="${up}apple-touch-icon.png"><title>${esc(pageTitle(type, d))}</title><meta name="description" content="${esc(desc(type, d))}"><link rel="canonical" href="${canonical}"><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet"><style>${BASE_CSS}</style></head><body><header><div class="hi"><a href="${rootHref}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a><nav><a href="${up}comunidades/">Comunidades</a><a href="${up}municipios/">Municipios</a><a href="${up}ibi-2026/">IBI 2026</a><a href="${up}calculadora-ibi/">Calculadora</a><a href="${up}tasa-basuras/">Basuras</a><a href="${up}plusvalia/">Plusvalía</a><a href="${up}bonificaciones/">Bonificaciones</a></nav></div></header><div class="bc"><a href="${up}">Inicio</a><span>›</span><a href="${up}${d.slugCommunity}/">${esc(d.community)}</a><span>›</span><a href="../">${esc(d.town)}</a><span>›</span><strong>${esc(pageTitle(type, d).replace(` en ${d.town}`, "").replace(`${d.town}: `, ""))}</strong></div><div class="wrap"><div class="art-layout"><main><span class="tag ${type === "ibi-2026" ? "t-r" : type === "tasa-basuras-2026" || type === "reclamar-tasa-basura" ? "t-d" : type === "bonificaciones-ibi" ? "t-g" : "t-o"}">${esc(articleLabel(type, d.town))}</span><h1>${esc(pageTitle(type, d))}</h1><p class="art-meta">Actualizado: 1 febrero 2026 · Fuente: Ordenanza fiscal Ayuntamiento de ${esc(d.town)} 2026</p>${injectArticleAd(body)}</main>${sidebar(d, type)}</div></div>${foot(up)}</body></html>`;
}

function ibiBody(d) {
  const cuota = d.cuota90Num || Math.round(90000 * parseFloat(d.ibiUrbano.replace(",", ".")) / 100);
  const ex80 = Math.round(80000 * parseFloat(d.ibiUrbano.replace(",", ".")) / 100);
  return `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#tipo">Tipo impositivo del IBI en ${esc(d.town)} 2026</a></li><li><a href="#cuando">Cuándo se paga el IBI en ${esc(d.town)}</a></li><li><a href="#calcular">Cómo calcular tu IBI en ${esc(d.town)}</a></li><li><a href="#fraccionar">Cómo fraccionar el pago</a></li><li><a href="#bonificaciones">Bonificaciones disponibles</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><p>El <strong>IBI (Impuesto sobre Bienes Inmuebles)</strong> es el tributo local de referencia para cualquier propietario de vivienda, local o nave. En ${esc(d.town)} (${esc(d.province)}, ${esc(d.community)}), el Ayuntamiento fija cada año el tipo impositivo y el calendario de cobro en sus ordenanzas fiscales.</p><h2 id="tipo">Tipo impositivo del IBI en ${esc(d.town)} 2026</h2><table class="data-table"><thead><tr><th>Clase de inmueble</th><th>Tipo 2026</th></tr></thead><tbody><tr><td>IBI Urbano (viviendas, locales...)</td><td class="val">${esc(d.ibiUrbano)}</td></tr><tr><td>IBI Rústico (fincas agrícolas)</td><td class="val">${esc(d.ibiRustico)}</td></tr><tr><td>Inmuebles de características especiales</td><td class="val">1,30%</td></tr></tbody></table><div class="highlight-box"><strong>📌 ¿Es alto el IBI de ${esc(d.town)}?</strong> El tipo del ${esc(d.ibiUrbano)} se sitúa en una franja media-alta dentro de ${esc(d.province)}. Comparado con otros municipios similares, es un nivel fiscal moderado con margen de reducción mediante bonificaciones.</div><h2 id="cuando">Cuándo se paga el IBI en ${esc(d.town)}</h2><p>El período voluntario de pago del IBI en ${esc(d.town)} es <strong>${esc(d.periodo)}</strong>. Pasada esa fecha sin pagar, la deuda entra en vía ejecutiva con recargos e intereses de demora.</p><p>Si tienes el IBI domiciliado, el cargo se realiza automáticamente durante el período voluntario. Conviene revisar la cuenta asociada antes de la campaña de cobro.</p><h2 id="calcular">Cómo calcular tu IBI en ${esc(d.town)}</h2><p>La fórmula es: <strong>valor catastral × tipo impositivo = cuota íntegra</strong>. Ejemplo con un valor catastral de 90.000 €:</p><p style="background:var(--card);border:1px solid var(--rule);padding:10px 14px;font-size:.86rem;font-family:monospace;margin-bottom:14px;">90.000 € × ${esc(d.ibiUrbano)} = <strong>${money(cuota)} € / año</strong></p><p>Puedes consultar tu valor catastral en el recibo del año anterior o en la Sede Electrónica del Catastro: <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a>.</p><table class="data-table"><thead><tr><th>Valor catastral</th><th>Cuota bruta IBI (${esc(d.ibiUrbano)})</th></tr></thead><tbody><tr><td>50.000 €</td><td class="val">${money(Math.round(50000 * parseFloat(d.ibiUrbano.replace(",", ".")) / 100))} €</td></tr><tr><td>80.000 €</td><td class="val">${money(ex80)} €</td></tr><tr><td>90.000 €</td><td class="val">${money(cuota)} €</td></tr><tr><td>120.000 €</td><td class="val">${money(Math.round(120000 * parseFloat(d.ibiUrbano.replace(",", ".")) / 100))} €</td></tr></tbody></table><h2 id="fraccionar">Cómo fraccionar el pago del IBI en ${esc(d.town)}</h2><p>La mayoría de ayuntamientos, incluido ${esc(d.town)}, permiten fraccionar el IBI en dos plazos <strong>sin intereses</strong> si se solicita antes del inicio del período voluntario. La petición suele tramitarse en sede electrónica o en las oficinas de recaudación.</p><div class="highlight-box"><strong>💡 Consejo: domicilia el IBI</strong> La domiciliación bancaria evita olvidos y puede facilitar el fraccionamiento del recibo. Si además el Ayuntamiento aplica bonificación por domiciliación, la reducción se refleja en el siguiente padrón.</div><h2 id="bonificaciones">Bonificaciones disponibles en ${esc(d.town)}</h2><p>La ordenanza fiscal contempla descuentos para determinados supuestos. En ${esc(d.town)} destacan la <strong>bonificación para familia numerosa</strong> (${esc(d.boni)}), las ayudas por <strong>instalación de energías renovables</strong> y, según el caso, descuentos por <strong>domiciliación bancaria</strong> o vivienda protegida.</p><table class="data-table"><thead><tr><th>Bonificación</th><th>Descuento</th><th>Plazo</th></tr></thead><tbody><tr><td>Familia numerosa</td><td class="val">${esc(d.boni)}</td><td>Antes del 31 de marzo</td></tr><tr><td>Placas solares / energías renovables</td><td class="val">20%-30%</td><td>Tras la instalación</td></tr><tr><td>Domiciliación bancaria</td><td class="val">1%-5%</td><td>Antes del período voluntario</td></tr></tbody></table><h2 id="faq">Preguntas frecuentes sobre el IBI en ${esc(d.town)}</h2><div class="faq-item"><div class="faq-q">¿Cuánto se paga de IBI en ${esc(d.town)} en 2026?</div><div class="faq-a">Con un valor catastral de 90.000 €, la cuota bruta ronda los ${money(cuota)} € al año antes de aplicar bonificaciones.</div></div><div class="faq-item"><div class="faq-q">¿Cuándo se paga el IBI en ${esc(d.town)}?</div><div class="faq-a">El período voluntario de cobro es ${esc(d.periodo)}.</div></div><div class="faq-item"><div class="faq-q">¿Puedo fraccionar el IBI en ${esc(d.town)}?</div><div class="faq-a">Sí, normalmente en dos plazos sin intereses si lo solicitas antes de que arranque la campaña de cobro.</div></div>${moreInfo(d)}`;
}

function simpleBody(type, d) {
  const bodies = {
    "tasa-basuras-2026": `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#importe">Importe orientativo en ${esc(d.town)}</a></li><li><a href="#quien">Quién paga la tasa de basura</a></li><li><a href="#cuando">Cuándo se cobra y cómo se paga</a></li><li><a href="#reclamar">Cómo reclamar un recibo incorrecto</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><div class="intro-box"><p>La <strong>tasa de basura en ${esc(d.town)}</strong> financia la recogida y tratamiento de residuos. Para una vivienda habitual, el importe orientativo en 2026 es de <strong>${esc(d.basura)}</strong>.</p><p>El recibo suele cargarse al propietario, aunque en contratos de alquiler puede repercutirse al inquilino si así se pacta expresamente.</p></div><h2 id="importe">Importe de la tasa de basura en ${esc(d.town)} 2026</h2><p>La cuantía depende del uso del inmueble, la superficie y la ordenanza municipal. En vivienda habitual, la referencia más habitual para ${esc(d.town)} es <strong>${esc(d.basura)}</strong>.</p><div class="highlight-box"><strong>📌 ¿Ha cambiado la tasa en 2026?</strong> La Ley 7/2022 de residuos ha llevado a muchos municipios a revisar sus tarifas. Conviene comprobar el padrón municipal si tu recibo llega con una variación relevante.</div><h2 id="quien">Quién paga la tasa de basura en ${esc(d.town)}</h2><p>Con carácter general, la tasa figura a nombre del <strong>propietario</strong>. En un alquiler, el casero puede repercutirla al inquilino si el contrato lo recoge claramente.</p><h2 id="cuando">Cuándo se cobra y cómo pagarla</h2><p>En ${esc(d.town)}, la tasa de basuras suele liquidarse durante el <strong>primer trimestre</strong>. El pago puede hacerse por domiciliación, banca colaboradora o sede electrónica, según el sistema de recaudación del municipio o la diputación.</p><table class="data-table"><thead><tr><th>Concepto</th><th>Dato orientativo</th></tr></thead><tbody><tr><td>Importe vivienda habitual</td><td class="val">${esc(d.basura)}</td></tr><tr><td>Sujeto pasivo</td><td>Propietario</td></tr><tr><td>Repercusión en alquiler</td><td>Posible por contrato</td></tr><tr><td>Período habitual</td><td>Primer trimestre</td></tr></tbody></table><h2 id="reclamar">Cómo reclamar la tasa de basura en ${esc(d.town)}</h2><p>Si el recibo tiene un error de titularidad, superficie, uso o duplicidad, puedes presentar un <strong>recurso de reposición</strong> en el plazo de un mes desde la notificación. Aporta copia del recibo, DNI y la documentación justificativa.</p><h2 id="faq">Preguntas frecuentes</h2><div class="faq-item"><div class="faq-q">¿Cuánto es la tasa de basura en ${esc(d.town)} 2026?</div><div class="faq-a">Para vivienda habitual, la referencia orientativa es ${esc(d.basura)}.</div></div><div class="faq-item"><div class="faq-q">¿Quién paga la tasa de basura en un alquiler?</div><div class="faq-a">Legalmente corresponde al propietario, salvo que se repercuta al inquilino por contrato.</div></div><div class="faq-item"><div class="faq-q">¿Cómo se reclama una tasa de basura incorrecta?</div><div class="faq-a">Presentando recurso de reposición dentro del mes siguiente a la notificación del recibo.</div></div>${moreInfo(d)}`,
    "plusvalia-municipal": `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#quees">Qué es la plusvalía municipal</a></li><li><a href="#calculo">Cómo se calcula en ${esc(d.town)}</a></li><li><a href="#plazos">Plazos para pagarla</a></li><li><a href="#exenciones">Exenciones y supuestos sin pago</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><div class="intro-box"><p>La <strong>plusvalía municipal</strong> grava el incremento de valor del suelo urbano cuando vendes, donas o heredas un inmueble. En ${esc(d.town)}, el impuesto se gestiona conforme al método <strong>objetivo o real</strong>, aplicando el más favorable para el contribuyente.</p></div><h2 id="quees">Qué es la plusvalía municipal en ${esc(d.town)}</h2><p>Se trata del Impuesto sobre el Incremento de Valor de los Terrenos de Naturaleza Urbana. Solo afecta al <strong>suelo urbano</strong>, no a la construcción.</p><h2 id="calculo">Cómo se calcula en ${esc(d.town)}</h2><p>Desde la reforma estatal, puedes tributar por el <strong>método objetivo</strong> o por la <strong>ganancia real</strong> si esta resulta inferior. El Ayuntamiento debe aplicar el sistema más favorable cuando acreditas los valores de adquisición y transmisión.</p><div class="highlight-box"><strong>📌 Consejo práctico</strong> Si has vendido con poca ganancia o incluso con pérdidas, conviene comparar ambos métodos y conservar escrituras, gastos e impuestos asociados.</div><table class="data-table"><thead><tr><th>Situación</th><th>Plazo habitual</th></tr></thead><tbody><tr><td>Compraventa / donación</td><td class="val">30 días hábiles</td></tr><tr><td>Herencia</td><td class="val">6 meses prorrogables</td></tr><tr><td>Pago telemático</td><td>Sede electrónica o recaudación</td></tr></tbody></table><h2 id="plazos">Plazos para pagar la plusvalía</h2><p>En transmisiones inter vivos, el plazo general es de <strong>30 días hábiles</strong>. En herencias, dispones de <strong>6 meses</strong> desde el fallecimiento, prorrogables por otros seis si lo solicitas a tiempo.</p><h2 id="exenciones">Exenciones y casos sin pago</h2><p>No se paga plusvalía si no existe incremento de valor acreditable. También pueden concurrir exenciones por transmisiones entre cónyuges derivadas de separación, daciones en pago o determinados supuestos protegidos por ley.</p><h2 id="faq">Preguntas frecuentes</h2><div class="faq-item"><div class="faq-q">¿Cuándo hay que pagar la plusvalía en ${esc(d.town)}?</div><div class="faq-a">En ventas y donaciones, dentro de los 30 días hábiles siguientes a la firma. En herencias, en 6 meses desde el fallecimiento.</div></div><div class="faq-item"><div class="faq-q">¿Se paga si he vendido con pérdidas?</div><div class="faq-a">No, si acreditas que no ha existido incremento de valor del terreno o el método real resulta nulo o inferior.</div></div><div class="faq-item"><div class="faq-q">¿Qué método conviene usar?</div><div class="faq-a">El que arroje menor cuota: objetivo o real. Conviene comparar ambos antes de presentar la autoliquidación.</div></div>${moreInfo(d)}`,
    "bonificaciones-ibi": `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#familia">Bonificación por familia numerosa</a></li><li><a href="#solar">Bonificación por placas solares</a></li><li><a href="#otras">Otras bonificaciones</a></li><li><a href="#solicitar">Cómo solicitarlas</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><div class="intro-box"><p>Las <strong>bonificaciones del IBI en ${esc(d.town)}</strong> pueden reducir de forma importante la cuota anual. Las más habituales afectan a <strong>familias numerosas</strong>, instalaciones de <strong>energía solar</strong>, vivienda protegida y domiciliación bancaria.</p></div><h2 id="familia">Bonificación IBI por familia numerosa</h2><div class="boni-card"><div class="boni-pct">${esc(d.boni)}</div><div class="boni-plazo">Solicitar antes del 31 de marzo</div><h3>Vivienda habitual</h3><p>La ayuda para familia numerosa se aplica sobre la vivienda habitual y suele condicionarse al valor catastral y a que el inmueble esté al corriente de pago.</p></div><h2 id="solar">Bonificación por placas solares en ${esc(d.town)}</h2><div class="boni-card"><div class="boni-pct">20%-30%</div><div class="boni-plazo">Tras la instalación</div><h3>Energías renovables</h3><p>La ordenanza local suele reconocer un descuento temporal por instalar sistemas de aprovechamiento térmico o eléctrico de energía solar debidamente legalizados.</p></div><h2 id="otras">Otras bonificaciones disponibles</h2><div class="boni-card"><div class="boni-pct">1%-5%</div><div class="boni-plazo">Antes del período voluntario</div><h3>Domiciliación y otros supuestos</h3><p>Algunos municipios aplican pequeñas reducciones por domiciliación bancaria, vivienda protegida o actividades de interés municipal.</p></div><table class="data-table"><thead><tr><th>Bonificación</th><th>Descuento</th><th>Requisito general</th></tr></thead><tbody><tr><td>Familia numerosa</td><td class="val">${esc(d.boni)}</td><td>Vivienda habitual y solicitud anual</td></tr><tr><td>Placas solares</td><td class="val">20%-30%</td><td>Instalación legalizada</td></tr><tr><td>Domiciliación</td><td class="val">1%-5%</td><td>Recibo domiciliado</td></tr></tbody></table><h2 id="solicitar">Cómo solicitar las bonificaciones</h2><p>La solicitud se presenta normalmente en sede electrónica o registro municipal junto con DNI, título de familia numerosa, certificado de empadronamiento o documentación técnica de la instalación solar.</p><h2 id="faq">Preguntas frecuentes</h2><div class="faq-item"><div class="faq-q">¿Qué bonificación tiene la familia numerosa en ${esc(d.town)}?</div><div class="faq-a">La referencia general es ${esc(d.boni)} sobre la vivienda habitual, aunque puede graduarse según categoría y valor catastral.</div></div><div class="faq-item"><div class="faq-q">¿Hay descuento por placas solares?</div><div class="faq-a">Sí, suele situarse entre el 20% y el 30% durante varios ejercicios si la instalación cumple los requisitos.</div></div><div class="faq-item"><div class="faq-q">¿Se puede pedir por internet?</div><div class="faq-a">Sí, en la mayoría de municipios la solicitud puede tramitarse por sede electrónica.</div></div>${moreInfo(d)}`,
    "como-pagar-ibi": `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#formas">Formas de pagar el IBI</a></li><li><a href="#fraccionar">Fraccionamiento</a></li><li><a href="#impago">Qué pasa si no pagas a tiempo</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><div class="intro-box"><p>El <strong>período voluntario de pago del IBI en ${esc(d.town)}</strong> es ${esc(d.periodo)}. Puedes abonarlo en entidad colaboradora, por internet o mediante domiciliación bancaria.</p></div><h2 id="formas">Formas de pagar el IBI en ${esc(d.town)}</h2><div class="method-card"><div class="method-icon">🏦</div><div><h3>Entidades bancarias colaboradoras</h3><p>Con el recibo municipal o la carta de pago, dentro del período voluntario.</p></div></div><div class="method-card"><div class="method-icon">💻</div><div><h3>Pago online</h3><p>Desde la sede electrónica municipal o el organismo provincial de recaudación, con certificado digital, DNIe o cl@ve.</p></div></div><div class="method-card"><div class="method-icon">🔁</div><div><h3>Domiciliación bancaria</h3><p>La opción más cómoda para evitar olvidos y acelerar el fraccionamiento si la ordenanza lo permite.</p></div></div><h2 id="fraccionar">Fraccionamiento del IBI en ${esc(d.town)}</h2><p>Si el importe es elevado, lo habitual es poder solicitar <strong>dos plazos sin intereses</strong> antes del inicio de la campaña de cobro. El pago se divide y se domicilia en la cuenta indicada.</p><div class="step"><div class="step-num">1</div><div><h3>Revisar el calendario</h3><p>Comprueba que la solicitud se presenta antes del inicio del período voluntario: ${esc(d.periodo)}.</p></div></div><div class="step"><div class="step-num">2</div><div><h3>Presentar la solicitud</h3><p>Hazlo por sede electrónica o en el registro de recaudación, indicando la cuenta bancaria.</p></div></div><div class="step"><div class="step-num">3</div><div><h3>Guardar el justificante</h3><p>Conserva el resguardo por si necesitas acreditar la petición antes del cargo.</p></div></div><h2 id="impago">Qué pasa si no pagas el IBI a tiempo</h2><ul><li><strong>Primer mes:</strong> recargo del 5%</li><li><strong>Hasta tres meses:</strong> recargo del 10%</li><li><strong>Más de tres meses:</strong> recargo del 20% más intereses</li></ul><h2 id="faq">Preguntas frecuentes</h2><div class="faq-item"><div class="faq-q">¿Puedo pagar el IBI de ${esc(d.town)} online?</div><div class="faq-a">Sí, normalmente desde la sede electrónica municipal o el portal de recaudación provincial.</div></div><div class="faq-item"><div class="faq-q">¿Cuándo vence el plazo de pago?</div><div class="faq-a">El período voluntario es ${esc(d.periodo)}.</div></div><div class="faq-item"><div class="faq-q">¿Se puede fraccionar?</div><div class="faq-a">Sí, habitualmente en dos plazos sin intereses si lo solicitas antes de la campaña de cobro.</div></div>${moreInfo(d)}`,
    "reclamar-tasa-basura": `<div class="toc-box"><h2>Contenido</h2><ol><li><a href="#motivos">Motivos habituales para reclamar</a></li><li><a href="#pasos">Cómo presentar el recurso</a></li><li><a href="#documentos">Documentación necesaria</a></li><li><a href="#faq">Preguntas frecuentes</a></li></ol></div><div class="intro-box"><p>Si el recibo de basura de ${esc(d.town)} contiene errores de titularidad, uso, superficie, duplicidad o falta de exención, puedes presentar un <strong>recurso de reposición</strong> o una solicitud de rectificación.</p></div><h2 id="motivos">Motivos habituales para reclamar la tasa de basura</h2><ul><li>El inmueble no genera residuos o no está en uso.</li><li>Existe <strong>duplicidad</strong> de recibos.</li><li>La superficie o el uso asignado son incorrectos.</li><li>La tasa se gira a un titular equivocado.</li><li>Corresponde una exención o bonificación no aplicada.</li></ul><h2 id="pasos">Cómo presentar el recurso en ${esc(d.town)}</h2><div class="step"><div class="step-num">1</div><div><h3>Revisar el recibo</h3><p>Comprueba referencia, titular, inmueble, base y fecha de notificación.</p></div></div><div class="step"><div class="step-num">2</div><div><h3>Preparar alegaciones</h3><p>Explica el error y solicita la anulación, rectificación o devolución del importe.</p></div></div><div class="step"><div class="step-num">3</div><div><h3>Presentar el recurso</h3><p>El plazo ordinario es de <strong>un mes</strong> desde la notificación, salvo que la ordenanza local diga otra cosa.</p></div></div><h2 id="documentos">Documentación recomendable</h2><table class="data-table"><thead><tr><th>Documento</th><th>Utilidad</th></tr></thead><tbody><tr><td>Recibo o liquidación</td><td>Identifica el acto recurrido</td></tr><tr><td>DNI o acreditación</td><td>Identifica al reclamante</td></tr><tr><td>Escritura / contrato / catastro</td><td>Prueba titularidad, superficie o uso</td></tr><tr><td>Justificantes adicionales</td><td>Respaldan exenciones o errores</td></tr></tbody></table><div class="highlight-box"><strong>📌 Recomendación</strong> Si el error afecta al catastro o al padrón municipal, conviene corregir ambas bases de datos para que el problema no vuelva a repetirse en ejercicios posteriores.</div><h2 id="faq">Preguntas frecuentes</h2><div class="faq-item"><div class="faq-q">¿Cuánto tiempo tengo para reclamar?</div><div class="faq-a">Con carácter general, un mes desde la notificación del recibo o liquidación.</div></div><div class="faq-item"><div class="faq-q">¿Puedo reclamar si el local está cerrado?</div><div class="faq-a">Sí, si la ordenanza prevé exención o reducción y puedes acreditarlo documentalmente.</div></div><div class="faq-item"><div class="faq-q">¿Hay que pagar antes de reclamar?</div><div class="faq-a">Depende del procedimiento y de si solicitas suspensión. Revisa la notificación o consulta con recaudación.</div></div>${moreInfo(d)}`
  };
  return bodies[type];
}

function shouldProcess(file) {
  const html = read(file);
  if (!/art-meta/.test(html) || !/faq-item/.test(html) || !/toc-box/.test(html)) return true;
  if (!/Fuente: Ordenanza fiscal Ayuntamiento/.test(html)) return true;
  return false;
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (entry.isFile() && entry.name === "index.html") out.push(full);
  }
  return out;
}

function processArticle(file) {
  const parts = path.relative(ROOT, file).split(path.sep);
  if (parts.length < 5) return false;
  const typeSlug = parts[3];
  const type = ARTICLE_TYPES.find(t => typeSlug.startsWith(t));
  if (!type || !shouldProcess(file)) return false;
  const dir = path.dirname(path.dirname(file));
  const d = loadData(dir);
  const html = layout(type, d, type === "ibi-2026" ? ibiBody(d) : simpleBody(type, d));
  write(file, html);
  return true;
}

let touched = 0;
for (const community of COMMUNITIES) {
  const base = path.join(ROOT, community);
  if (!fs.existsSync(base)) continue;
  for (const file of walk(base)) {
    if (processArticle(file)) touched++;
  }
}

console.log(`normalized_articles=${touched}`);
