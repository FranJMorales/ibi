const fs = require('fs');
const p = 'c:\\Users\\aitha\\Desktop\\ibi\\calculadora-ibi\\index.html';
let html = fs.readFileSync(p, 'utf-8');
html = html.replace(/\r\n/g, '\n');

// Find the broken area - line 167 has footer content inside info-card
// We need to:
// 1. Fix the info-card that got corrupted (lines 164-169)
// 2. Close the info-grid and wrap divs
// 3. Add editorial content
// 4. Add footer

// Find the last good info-card ending (Domiciliación line)
const lastGoodIdx = html.indexOf('</ul>\n    </div>\n    <div class="info-card">\n      <h3>Cuándo se paga el IBI 2026</h3>\n      <ul>');
if (lastGoodIdx === -1) {
  console.log('Cannot find marker, trying alternate...');
}

// Let's rebuild from the last good info-card
const cutPoint = html.indexOf('<div class="info-card">\n      <h3>Cuándo se paga el IBI 2026');
console.log('Cut point:', cutPoint);

const goodPart = html.substring(0, cutPoint);

// Footer template
const footer = `    <div class="info-card">
      <h3>Cuándo se paga el IBI 2026</h3>
      <ul>
        <li><strong>La mayoría de municipios:</strong> 1 oct – 30 nov 2026</li>
        <li><strong>Municipios de Toledo:</strong> 15 sep – 15 nov 2026</li>
        <li>Puedes fraccionar en 2 plazos sin intereses</li>
        <li>La domiciliación evita olvidar el pago</li>
      </ul>
    </div>
  </div>

  <!-- Editorial content for AdSense -->
  <div class="ed">
    <h2 class="sec">Guía completa para calcular tu IBI en 2026</h2>
    <p>El <strong>Impuesto sobre Bienes Inmuebles (IBI)</strong> es el principal tributo que los ayuntamientos cobran a los propietarios de viviendas, locales y terrenos. Su cálculo depende de dos variables fundamentales: el <strong>valor catastral</strong> del inmueble y el <strong>tipo impositivo</strong> que aprueba cada municipio dentro de los márgenes legales fijados por el <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214" target="_blank" rel="nofollow noopener" style="color:var(--accent)">Real Decreto Legislativo 2/2004</a> (TRLRHL).</p>

    <h3>¿Qué es el valor catastral y cómo afecta a tu IBI?</h3>
    <p>El valor catastral es una valoración administrativa del inmueble que realiza la Dirección General del Catastro, dependiente del Ministerio de Hacienda. Este valor se compone de dos partes: el <strong>valor del suelo</strong> y el <strong>valor de la construcción</strong>. Generalmente, el valor catastral se sitúa entre el 40% y el 60% del valor de mercado del inmueble, aunque en municipios donde no se ha realizado una revisión catastral reciente, la diferencia puede ser mayor.</p>
    <p>Las <strong>revisiones catastrales</strong> las promueve cada ayuntamiento y se aplican de forma gradual durante 10 años. Tras una revisión, los valores catastrales se actualizan para acercarlos al valor de mercado, lo que puede incrementar significativamente la cuota del IBI. En 2026, los coeficientes de actualización de valores catastrales están fijados por la Ley de Presupuestos Generales del Estado.</p>

    <h3>Tipos impositivos: mínimos y máximos legales</h3>
    <p>La Ley establece unos tipos mínimos y máximos que cada ayuntamiento puede aplicar:</p>
    <div class="ed-cols">
      <div class="ed-col">
        <h3>IBI Urbano</h3>
        <ul>
          <li>Tipo mínimo: <strong>0,4%</strong></li>
          <li>Tipo máximo: <strong>1,10%</strong></li>
          <li>Media de nuestra guía: <strong>0,62%</strong></li>
        </ul>
      </div>
      <div class="ed-col">
        <h3>IBI Rústico</h3>
        <ul>
          <li>Tipo mínimo: <strong>0,3%</strong></li>
          <li>Tipo máximo: <strong>0,90%</strong></li>
          <li>Media de nuestra guía: <strong>0,75%</strong></li>
        </ul>
      </div>
    </div>

    <h3>Ejemplo práctico de cálculo</h3>
    <p>Para una vivienda en <strong>Plasencia (Cáceres)</strong> con valor catastral de 90.000 € y tipo IBI del 0,65%:</p>
    <p>Cuota bruta = 90.000 × 0,0065 = <strong>585 €/año</strong> (48,75 €/mes)</p>
    <p>Si tienes familia numerosa general con bonificación del 25%: Cuota final = 585 × 0,75 = <strong>438,75 €/año</strong>. El ahorro es de 146,25 € anuales.</p>

    <h3>¿Qué hacer si tu IBI es incorrecto?</h3>
    <p>Si crees que tu valor catastral no refleja la realidad o se ha aplicado un tipo impositivo erróneo, puedes presentar un <strong>recurso de reposición</strong> ante el Ayuntamiento en el plazo de un mes desde la notificación del recibo. También puedes solicitar la <strong>rectificación del valor catastral</strong> directamente ante el Catastro si detectas errores en la descripción del inmueble (superficie, antigüedad, estado de conservación).</p>

    <div class="hb gold">
      <strong>💡 Consejo práctico</strong>
      Domicilia el pago del IBI para obtener entre un 1% y un 5% de descuento (según el municipio) y evitar recargos por impago. En muchos ayuntamientos puedes fraccionar el pago en 2 o 3 plazos sin coste adicional.
    </div>
  </div>

  <!-- FAQ Section -->
  <div class="ed">
    <h2 class="sec">Preguntas frecuentes sobre el IBI</h2>
    <div class="faq-list">
      <details class="faq">
        <summary>¿Quién paga el IBI: el propietario o el inquilino?</summary>
        <div class="faq-body">
          <p>El sujeto pasivo del IBI es siempre el <strong>propietario del inmueble</strong> a 1 de enero del año fiscal. Aunque en algunos contratos de alquiler se pacta que el inquilino asuma el coste, la responsabilidad legal ante el Ayuntamiento recae exclusivamente en el propietario.</p>
        </div>
      </details>
      <details class="faq">
        <summary>¿Puedo fraccionar el pago del IBI?</summary>
        <div class="faq-body">
          <p>Sí, la mayoría de ayuntamientos permiten fraccionar el IBI en 2 o incluso 3 plazos sin intereses. Para ello, normalmente debes domiciliar el recibo y solicitarlo antes del inicio del período voluntario de pago.</p>
        </div>
      </details>
      <details class="faq">
        <summary>¿Cuánto baja el IBI con placas solares?</summary>
        <div class="faq-body">
          <p>La bonificación por instalación de placas solares varía entre el <strong>20% y el 50%</strong> de la cuota del IBI, durante un período de 3 a 5 años según la ordenanza de cada municipio.</p>
        </div>
      </details>
      <details class="faq">
        <summary>¿Qué pasa si no pago el IBI?</summary>
        <div class="faq-body">
          <p>Si no pagas en período voluntario, se aplica un <strong>recargo del 5%, 10% o 20%</strong> según el tiempo transcurrido, más intereses de demora. La deuda prescribe a los 4 años.</p>
        </div>
      </details>
    </div>
  </div>

  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"¿Quién paga el IBI: el propietario o el inquilino?","acceptedAnswer":{"@type":"Answer","text":"El sujeto pasivo del IBI es siempre el propietario del inmueble a 1 de enero del año fiscal."}},{"@type":"Question","name":"¿Puedo fraccionar el pago del IBI?","acceptedAnswer":{"@type":"Answer","text":"Sí, la mayoría de ayuntamientos permiten fraccionar el IBI en 2 o 3 plazos sin intereses."}},{"@type":"Question","name":"¿Cuánto baja el IBI con placas solares?","acceptedAnswer":{"@type":"Answer","text":"La bonificación varía entre el 20% y el 50% de la cuota del IBI, durante 3 a 5 años."}},{"@type":"Question","name":"¿Qué pasa si no pago el IBI?","acceptedAnswer":{"@type":"Answer","text":"Se aplica un recargo del 5%, 10% o 20% según el tiempo, más intereses de demora."}}]}
  </script>

</div>

<footer>
  <div class="ft-grid" style="max-width:1100px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px;padding:40px 24px 24px;">
    <div>
      <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:900;color:#fff;margin-bottom:6px;">TasasMunicipales</div>
      <div style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:10px;">Guía de Impuestos Locales · España 2026</div>
      <p style="font-size:.78rem;line-height:1.7;color:rgba(255,255,255,.45);margin:0;">Guía de IBI, tasa de basuras, plusvalía y bonificaciones para 59 municipios en 7 comunidades autónomas.</p>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Navegación</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="../" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Inicio</a></li>
        <li style="margin-bottom:8px;"><a href="../comunidades/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Comunidades</a></li>
        <li style="margin-bottom:8px;"><a href="../municipios/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Municipios</a></li>
        <li style="margin-bottom:8px;"><a href="../calculadora-ibi/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Calculadora IBI</a></li>
      </ul>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Impuestos</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="../ibi-2026/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">IBI 2026</a></li>
        <li style="margin-bottom:8px;"><a href="../tasa-basuras/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Tasa de Basuras</a></li>
        <li style="margin-bottom:8px;"><a href="../plusvalia/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Plusvalía Municipal</a></li>
        <li style="margin-bottom:8px;"><a href="../bonificaciones/" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Bonificaciones</a></li>
      </ul>
    </div>
    <div>
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.9);margin-bottom:14px;">Legal</div>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="margin-bottom:8px;"><a href="../aviso-legal/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Aviso Legal</a></li>
        <li style="margin-bottom:8px;"><a href="../privacidad/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Privacidad</a></li>
        <li style="margin-bottom:8px;"><a href="../cookies/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Cookies</a></li>
        <li style="margin-bottom:8px;"><a href="../contacto/" rel="nofollow" style="color:rgba(255,255,255,.5);font-size:.8rem;text-decoration:none;">Contacto</a></li>
      </ul>
    </div>
  </div>
  <div style="max-width:1100px;margin:0 auto;padding:16px 24px 28px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:.72rem;color:rgba(255,255,255,.4);">
    <span>© 2026 TasasMunicipales.info · La información no constituye asesoramiento fiscal.</span>
    <span>Datos orientativos. Consulta siempre tu ayuntamiento.</span>
  </div>
</footer>
<script src="../cookie-consent.js" defer></script>
</body>
</html>
`;

const result = goodPart + footer;
fs.writeFileSync(p, result, 'utf-8');

const final = fs.readFileSync(p, 'utf-8');
console.log('Lines:', final.split('\n').length);
console.log('Has </body>:', final.includes('</body>'));
console.log('Has </html>:', final.includes('</html>'));
console.log('Has footer:', final.includes('<footer>'));
console.log('Has ed section:', final.includes('Guía completa para calcular'));
console.log('Has FAQ:', final.includes('Preguntas frecuentes sobre el IBI'));
