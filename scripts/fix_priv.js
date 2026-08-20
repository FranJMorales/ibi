const fs = require('fs');
const ROOT = 'c:\\Users\\aitha\\Desktop\\ibi';

// Fix privacidad - append the missing closing tags
const privFile = ROOT + '\\privacidad\\index.html';
let privHtml = fs.readFileSync(privFile, 'utf-8');

// Find the truncated footer and replace from there
const footerIdx = privHtml.lastIndexOf('<footer>');
if (footerIdx > 0) {
  privHtml = privHtml.substring(0, footerIdx) + 
`<footer>
  <a href="../">Inicio</a>
  <a href="../aviso-legal/" rel="nofollow">Aviso Legal</a>
  <a href="../privacidad/" rel="nofollow">Privacidad</a>
  <a href="../cookies/" rel="nofollow">Cookies</a>
</footer>
<script src="../cookie-consent.js" defer></script>
</body>
</html>
`;
  fs.writeFileSync(privFile, privHtml, 'utf-8');
  console.log('Fixed privacidad');
}

// Verify
const html = fs.readFileSync(privFile, 'utf-8');
console.log('cookie=' + html.includes('cookie-consent.js'));
console.log('</body>=' + html.includes('</body>'));
console.log('</html>=' + html.includes('</html>'));
