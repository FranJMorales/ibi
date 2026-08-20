#!/usr/bin/env node
/**
 * REBUILD MUNICIPALITIES — Generates enhanced HTML for all 59 municipalities
 * with unique editorial content, exact data, bar charts, and external CSS
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

// Load all data parts
const allMunis = [
  ...require('./muni_data_part1'),
  ...require('./muni_data_part2'),
  ...require('./muni_data_part3'),
  ...require('./muni_data_part4'),
  ...require('./muni_data_part5'),
  ...require('./muni_data_part6'),
  ...require('./muni_data_part7')
];

// Get siblings (other munis in same province)
function getSiblings(m) {
  const parts = m.slug.split('/');
  const provPath = parts[0] + '/' + parts[1];
  return allMunis.filter(x => x.slug !== m.slug && x.slug.startsWith(provPath));
}

// Get regional munis for comparison chart
function getRegionalMunis(m) {
  return allMunis.filter(x => x.ccaaSlug === m.ccaaSlug).sort((a,b) => a.ibiU - b.ibiU);
}

function getRelRoot(slug) {
  const depth = slug.split('/').length;
  return '../'.repeat(depth);
}

function generateBarChart(munis, currentSlug) {
  const maxIBI = Math.max(...munis.map(x => x.ibiU));
  let html = '<div class="chart-container">\n';
  for (const m of munis) {
    const pct = (m.ibiU / maxIBI * 100).toFixed(0);
    const isCurrent = m.slug === currentSlug;
    const style = isCurrent ? 'font-weight:900;color:var(--accent)' : '';
    html += `  <div class="chart-bar-row">
    <span class="chart-label" style="${style}">${m.nombre}</span>
    <div class="chart-bar-wrap">
      <div class="chart-bar" style="width:${pct}%;${isCurrent ? 'background:linear-gradient(90deg,var(--accent),#e8734a)' : ''}"><span>${m.ibiU.toFixed(2)}%</span></div>
    </div>
  </div>\n`;
  }
  html += '</div>';
  return html;
}

function generateMuniPage(m) {
  const rel = getRelRoot(m.slug);
  const siblings = getSiblings(m);
  const regional = getRegionalMunis(m);
  const today = new Date().toISOString().split('T')[0];

  // Calculate IBI examples from actual rate
  const examples = m.valoresCatastrales.map(v => ({
    desc: v.desc, vc: v.vc,
    cuota: Math.round(v.vc * m.ibiU / 100),
    mensual: Math.round(v.vc * m.ibiU / 100 / 12)
  }));

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/x-icon" href="${rel}favicon.ico">
  <link rel="icon" type="image/svg+xml" href="${rel}favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="${rel}favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="${rel}apple-touch-icon.png">
  <title>IBI, basuras y plusvalía en ${m.nombre} 2026 — Guía fiscal completa</title>
  <meta name="description" content="Guía fiscal de ${m.nombre} (${m.prov}) 2026: IBI urbano ${m.ibiU.toFixed(2)}%, tasa de basuras ${m.basura} €/año, plusvalía municipal, bonificaciones familia numerosa ${m.bonFN} y energía solar ${m.bonSolar}. Datos de la ordenanza actualizada.">
  <link rel="canonical" href="https://tasasmunicipales.info/${m.slug}/">
  <meta name="google-adsense-account" content="ca-pub-4975903304841229">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "IBI, basuras y plusvalía en ${m.nombre} 2026",
    "url": "https://tasasmunicipales.info/${m.slug}/",
    "datePublished": "2026-02-01",
    "dateModified": "${today}",
    "author": { "@type": "Person", "name": "Aithamy Rivero", "url": "https://tasasmunicipales.info/sobre-nosotros/" },
    "publisher": { "@type": "Organization", "name": "TasasMunicipales.info" }
  }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${rel}styles.css">
</head>
<body>
<header>
  <div class="hi">
    <a href="${rel}" class="logo">TasasMunicipales<span>Guía de Impuestos Locales · España 2026</span></a>
    <nav>
      <a href="${rel}comunidades/">Comunidades</a>
      <a href="${rel}municipios/">Municipios</a>
      <a href="${rel}ibi-2026/">IBI 2026</a>
      <a href="${rel}calculadora-ibi/">Calculadora</a>
      <a href="${rel}tasa-basuras/">Basuras</a>
      <a href="${rel}plusvalia/">Plusvalía</a>
      <a href="${rel}bonificaciones/">Bonificaciones</a>
    </nav>
  </div>
</header>
<div class="bc"><a href="${rel}">Inicio</a><span>›</span><a href="${rel}${m.ccaaSlug}/">${m.ccaa}</a><span>›</span><strong>${m.nombre}</strong></div>
<div class="wrap">
  <section class="hero">
    <div class="hero-main card">
      <span class="eyebrow">Guía Fiscal Municipal 2026</span>
      <h1>${m.nombre}: IBI, basuras, plusvalía y bonificaciones</h1>
      <p class="lead">${m.intro}</p>
      <p class="meta"><strong>${m.ccaa} · ${m.prov}</strong> · Población: ${m.poblacion} hab. · Actualizado: abril 2026</p>
      <div class="author-box">✍️ Por <a href="${rel}sobre-nosotros/">Aithamy Rivero</a> · Fuente: <a href="${m.fuenteUrl}" target="_blank" rel="nofollow noopener">${m.fuente}</a></div>
    </div>
    <aside class="hero-side card">
      <h2>Datos clave 2026</h2>
      <ul class="quick">
        <li><strong>IBI urbano:</strong> <span class="v">${m.ibiU.toFixed(2)}%</span></li>
        <li><strong>IBI rústico:</strong> <span class="v">${m.ibiR.toFixed(2)}%</span></li>
        <li><strong>Período de pago:</strong> ${m.periodo}</li>
        <li><strong>Basura vivienda:</strong> ${m.basura} €/año</li>
        <li><strong>Bonif. familia numerosa:</strong> ${m.bonFN}</li>
        <li><strong>Bonif. energía solar:</strong> ${m.bonSolar}</li>
      </ul>
    </aside>
  </section>

  <div class="layout">
    <main>
      <section class="sec">
        <h2>IBI 2026 en ${m.nombre}: cuánto se paga y cuándo</h2>
        <p>${m.contextoIBI}</p>
        <h3>Cuotas estimadas según valor catastral real</h3>
        <table class="dt">
          <thead><tr><th>Tipo de inmueble</th><th>Valor catastral</th><th>Cuota anual</th><th>Cuota mensual</th></tr></thead>
          <tbody>
${examples.map(e => `            <tr><td>${e.desc}</td><td>${e.vc.toLocaleString('es-ES')} €</td><td class="v">${e.cuota} €</td><td>${e.mensual} €/mes</td></tr>`).join('\n')}
          </tbody>
        </table>
        <div class="note"><strong>💡 ¿Cómo se calcula?</strong> <em>Cuota = Valor catastral × ${m.ibiU.toFixed(2)}%</em>. El valor catastral aparece en tu recibo del IBI o en la <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sede del Catastro</a>. Las bonificaciones se restan después.</div>
        <h3>¿Cómo consultar tu valor catastral en la Sede del Catastro?</h3>
        <p>Para conocer tu valor catastral exacto, accede a <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a>. Necesitarás certificado digital, Cl@ve PIN o DNI electrónico. En el menú «Consulta de datos catastrales», selecciona «Consulta de un inmueble» e introduce la referencia catastral (aparece en tu recibo del IBI) o busca por dirección. El sistema mostrará el valor catastral total, el valor del suelo y el de la construcción por separado.</p>
      </section>

      <section class="sec">
        <h2>Tasa de basuras en ${m.nombre}: ${m.basura} €/año</h2>
        <p>${m.contextoBasura}</p>
        <table class="dt">
          <thead><tr><th>Concepto</th><th>Importe</th></tr></thead>
          <tbody>
            <tr><td>Vivienda habitual</td><td class="v">${m.basura} €/año</td></tr>
            <tr><td>Equivalente mensual</td><td>${(m.basura/12).toFixed(2)} €/mes</td></tr>
            <tr><td>Período de pago</td><td>${m.periodo}</td></tr>
          </tbody>
        </table>
        <p>La tasa de basuras se ha incrementado en la mayoría de municipios españoles en 2025–2026 por la <strong>Ley 7/2022 de Residuos y Suelos Contaminados</strong>, que obliga a los ayuntamientos a cubrir el coste íntegro del servicio con las tasas cobradas. En ${m.nombre}, esta adaptación ha supuesto una revisión de la tarifa vigente para cumplir con el principio de cobertura de costes establecido en el artículo 11.3 de dicha ley.</p>
        <p>En caso de alquiler, el sujeto pasivo es legalmente el propietario del inmueble, aunque el contrato de arrendamiento puede trasladar el pago al inquilino si se pacta expresamente por escrito en una cláusula específica.</p>
      </section>

      <section class="sec">
        <h2>Plusvalía municipal en ${m.nombre}</h2>
        <p>${m.contextoPlusvalia}</p>
        <h3>Plazos legales para declarar</h3>
        <ul>
          <li><strong>Compraventa:</strong> 30 días hábiles desde la fecha de escritura pública.</li>
          <li><strong>Herencia:</strong> 6 meses desde el fallecimiento (prorrogable a 12 meses con solicitud motivada ante el Ayuntamiento de ${m.nombre}).</li>
          <li><strong>Donación:</strong> 30 días hábiles desde la escritura de donación.</li>
        </ul>
        <h3>¿Cuándo NO se paga plusvalía?</h3>
        <p>Si el precio de transmisión es inferior al de adquisición (venta con pérdidas), no existe incremento de valor y no se devenga el impuesto. Debes aportar ambas escrituras (compra y venta) al Ayuntamiento para acreditar la ausencia de plusvalía. Desde la sentencia del Tribunal Constitucional de 2021 (STC 182/2021) y el Real Decreto-ley 26/2021, puedes optar por el método de cálculo (real vs. objetivo) que resulte más favorable.</p>
        <div class="note"><strong>⚖️ Elige el método más favorable en ${m.nombre}.</strong> Consulta la <a href="${m.sedeUrl}" target="_blank" rel="nofollow noopener">sede electrónica del Ayuntamiento</a> para conocer los coeficientes municipales vigentes y simular ambos métodos antes de presentar la autoliquidación.</div>
        <p><a href="${rel}plusvalia/" style="color:var(--accent);font-weight:600">→ Calculadora de plusvalía municipal</a></p>
      </section>

      <section class="sec">
        <h2>Bonificaciones del IBI en ${m.nombre}</h2>
        <table class="dt">
          <thead><tr><th>Bonificación</th><th>Porcentaje</th><th>Requisitos clave</th></tr></thead>
          <tbody>
            <tr><td>Familia numerosa (general)</td><td class="v">${m.bonFN}</td><td>Título vigente + vivienda habitual + empadronamiento en ${m.nombre}</td></tr>
            <tr><td>Energía solar / renovables</td><td class="v">${m.bonSolar}</td><td>Certificado instalador autorizado + boletín eléctrico + solicitud en el ejercicio siguiente a la instalación</td></tr>
            <tr><td>Domiciliación SEPA</td><td>1–5%</td><td>Comunicar IBAN antes del inicio del período voluntario de pago</td></tr>
            <tr><td>VPO (nueva construcción)</td><td>Hasta 50%</td><td>Primeros 3 años desde calificación definitiva de VPO</td></tr>
          </tbody>
        </table>
        <div class="note"><strong>📅 Plazo de solicitud:</strong> antes del 31 de marzo del ejercicio fiscal, salvo que la ordenanza establezca otra fecha. Las bonificaciones no se aplican de oficio: debes solicitarlas activamente en la <a href="${m.sedeUrl}" target="_blank" rel="nofollow noopener">sede electrónica</a> o en las oficinas de recaudación.</div>
        <p><a href="${rel}bonificaciones/" style="color:var(--accent);font-weight:600">→ Guía completa de bonificaciones del IBI</a></p>
      </section>

      <section class="sec">
        <h2>Comparativa IBI urbano en ${m.ccaa}</h2>
        <p>El siguiente gráfico compara el tipo de IBI urbano de ${m.nombre} con el de otros municipios de ${m.ccaa} incluidos en nuestra guía. Un tipo más alto no siempre implica cuotas más altas: depende del valor catastral de cada inmueble.</p>
${generateBarChart(regional, m.slug)}
        <p style="font-size:0.82rem;color:var(--mid);margin-top:10px">Fuente: Ordenanzas fiscales municipales publicadas en los boletines oficiales correspondientes (2025-2026).</p>
      </section>

      <section class="sec">
        <h2>Consejo práctico para ${m.nombre}</h2>
        <p>${m.consejo}</p>
      </section>

      <section class="sec">
        <h2>Fuentes oficiales y verificación</h2>
        <ul>
          <li><strong>Ordenanza fiscal:</strong> <a href="${m.fuenteUrl}" target="_blank" rel="nofollow noopener">${m.fuente}</a></li>
          <li><strong>Sede electrónica:</strong> <a href="${m.sedeUrl}" target="_blank" rel="nofollow noopener">${m.sedeUrl}</a></li>
          <li><strong>Catastro:</strong> <a href="https://www.sedecatastro.gob.es" target="_blank" rel="nofollow noopener">sedecatastro.gob.es</a> para consultar el valor catastral de tu inmueble.</li>
        </ul>
        <div class="note"><strong>⚠️ Aviso:</strong> Los datos de esta guía se basan en la ordenanza fiscal publicada en el ${m.fuente}. Confirma siempre los importes y plazos vigentes en la <a href="${m.sedeUrl}" target="_blank" rel="nofollow noopener">sede electrónica del Ayuntamiento de ${m.nombre}</a> antes de pagar, reclamar o solicitar una bonificación.</div>
      </section>

${siblings.length > 0 ? `      <section class="sec">
        <h2>Otros municipios de ${m.prov}</h2>
        <p>Consulta las guías fiscales de municipios cercanos en la misma provincia:</p>
        <ul>
${siblings.map(s => `          <li><a href="${rel}${s.slug}/">${s.nombre}</a> — IBI ${s.ibiU.toFixed(2)}%, Basuras ${s.basura} €/año — <a href="${rel}${s.slug}/" style="color:var(--accent);font-size:.82rem">Ver guía →</a></li>`).join('\n')}
        </ul>
      </section>` : ''}
    </main>

    <aside class="side">
      <div class="card">
        <h2>Navegación</h2>
        <ul>
          <li><a href="${rel}">Inicio</a></li>
          <li><a href="${rel}${m.ccaaSlug}/">Volver a ${m.ccaa}</a></li>
          <li><a href="${rel}municipios/">Todos los municipios</a></li>
          <li><a href="${rel}calculadora-ibi/">Calculadora IBI</a></li>
          <li><a href="${rel}ibi-2026/">IBI 2026</a></li>
          <li><a href="${rel}bonificaciones/">Bonificaciones</a></li>
          <li><a href="${rel}tasa-basuras/">Tasa de basuras</a></li>
          <li><a href="${rel}plusvalia/">Plusvalía</a></li>
          <li><a href="${rel}sobre-nosotros/">Sobre nosotros</a></li>
        </ul>
      </div>
      <div class="card" style="padding:16px">
        <h3 style="font-size:0.88rem;margin-bottom:8px">📊 Resumen fiscal</h3>
        <p style="font-size:0.8rem;color:var(--mid);margin-bottom:6px">Coste anual estimado para un piso de valor catastral medio en ${m.nombre}:</p>
        <table style="width:100%;font-size:0.8rem">
          <tr><td>IBI (VC ${examples[1].vc.toLocaleString('es-ES')} €)</td><td style="text-align:right;font-weight:700;color:var(--accent)">${examples[1].cuota} €</td></tr>
          <tr><td>Basuras</td><td style="text-align:right;font-weight:700;color:var(--accent)">${m.basura} €</td></tr>
          <tr style="border-top:2px solid var(--ink)"><td><strong>Total estimado</strong></td><td style="text-align:right;font-weight:900;color:var(--ink)">${examples[1].cuota + m.basura} €/año</td></tr>
        </table>
      </div>
    </aside>
  </div>
</div>
<footer>© 2026 TasasMunicipales.info · Datos orientativos basados en ordenanzas fiscales municipales. <a href="${rel}aviso-legal/" style="color:var(--gold)">Aviso legal</a> · <a href="${rel}privacidad/" style="color:var(--gold)">Privacidad</a> · <a href="${rel}cookies/" style="color:var(--gold)">Cookies</a></footer>
<script src="${rel}cookie-consent.js" defer></script>
</body>
</html>`;
}

// Generate all pages
console.log(`Processing ${allMunis.length} municipalities...`);
let count = 0;
for (const m of allMunis) {
  const dir = path.join(ROOT, m.slug);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const html = generateMuniPage(m);
  fs.writeFileSync(path.join(dir, 'index.html'), html, 'utf-8');
  count++;
  console.log(`  ✓ ${m.slug} (${m.nombre})`);
}
console.log(`\nDone! Generated ${count} municipality pages.`);
