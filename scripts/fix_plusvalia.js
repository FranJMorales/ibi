const fs = require('fs');
const path = 'c:\\Users\\aitha\\Desktop\\ibi\\plusvalia\\index.html';
let html = fs.readFileSync(path, 'utf-8');

// Normalize line endings
html = html.replace(/\r\n/g, '\n');

// Find key positions
const articleClose = html.indexOf('</article>');
const mainClose = html.indexOf('</main>');
const asideOpen = html.indexOf('<aside>');
const asideClose = html.indexOf('</aside>');
const layoutClose1 = html.indexOf('</div>', asideClose); // first </div> after aside
const layoutClose2 = html.indexOf('</div>', layoutClose1 + 6); // second </div>

console.log('Before fix:');
console.log('  </article>:', articleClose);
console.log('  </main>:', mainClose);
console.log('  <aside>:', asideOpen);

// Extract the 3 parts:
// 1. Everything up to and including </article>
const part1 = html.substring(0, articleClose + '</article>'.length);

// 2. The JSON scripts between </article> and </main>
const scripts = html.substring(articleClose + '</article>'.length, mainClose).trim();

// 3. </main> through </aside></div></div>
// 4. Everything after (footer onwards)
const afterLayout = html.substring(layoutClose2 + '</div>'.length);

// Rebuild: article, close main, aside, close layout divs, scripts, rest
const newAside = `
</main>
<aside>
  <div class="sb"><div class="sbh">📈 Plusvalía por municipio</div>
  <div class="sbb"><ul><li><a href="../extremadura/caceres/plasencia/">Plusvalía Plasencia</a></li><li><a href="../extremadura/caceres/navalmoral-de-la-mata/">Plusvalía Navalmoral de la Mata</a></li><li><a href="../extremadura/caceres/coria/">Plusvalía Coria</a></li><li><a href="../extremadura/badajoz/merida/">Plusvalía Mérida</a></li><li><a href="../extremadura/badajoz/don-benito/">Plusvalía Don Benito</a></li><li><a href="../extremadura/badajoz/almendralejo/">Plusvalía Almendralejo</a></li><li><a href="../extremadura/badajoz/villanueva-de-la-serena/">Plusvalía Villanueva de la Serena</a></li><li><a href="../castilla-la-mancha/toledo/talavera-de-la-reina/">Plusvalía Talavera de la Reina</a></li><li><a href="../castilla-la-mancha/toledo/illescas/">Plusvalía Illescas</a></li><li><a href="../castilla-la-mancha/toledo/sesena/">Plusvalía Seseña</a></li><li><a href="../castilla-la-mancha/ciudad-real/puertollano/">Plusvalía Puertollano</a></li><li><a href="../castilla-la-mancha/ciudad-real/tomelloso/">Plusvalía Tomelloso</a></li></ul>
  <a href="../municipios/" class="cta">Ver todos →</a></div></div>
  <div class="sb"><div class="sbh">📋 Otros impuestos</div>
  <div class="sbb"><ul>
    <li><a href="../ibi-2026/">🏠 IBI 2026</a></li>
    <li><a href="../tasa-basuras/">🗑️ Tasa de Basuras</a></li>
    <li><a href="../bonificaciones/">🎁 Bonificaciones IBI</a></li>
  </ul></div></div>
</aside>
</div>
</div>
`;

const result = part1 + newAside + scripts + afterLayout;
fs.writeFileSync(path, result, 'utf-8');

// Verify
const final = fs.readFileSync(path, 'utf-8');
const mc = final.indexOf('</main>');
const ac = final.indexOf('</article>');
const ao = final.indexOf('<aside>');
console.log('\nAfter fix:');
console.log('  </article>:', ac);
console.log('  </main>:', mc);
console.log('  <aside>:', ao);
console.log('  Correct order:', ac < mc && mc < ao);
console.log('  Has </body>:', final.includes('</body>'));
console.log('  Has </html>:', final.includes('</html>'));
