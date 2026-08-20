const fs = require('fs');
const path = require('path');
const ROOT = 'c:\\Users\\aitha\\Desktop\\ibi';

// Fix aviso-legal
let avisoHtml = fs.readFileSync(path.join(ROOT, 'aviso-legal', 'index.html'), 'utf-8');
// Fix unclosed </a tag and add missing closing tags
avisoHtml = avisoHtml.replace(/Cookies<\/a\r?\n/, 'Cookies</a>\r\n</footer>\r\n<script src="../cookie-consent.js" defer></script>\r\n</body>\r\n</html>\r\n');
fs.writeFileSync(path.join(ROOT, 'aviso-legal', 'index.html'), avisoHtml, 'utf-8');
console.log('Fixed aviso-legal');

// Fix privacidad
let privHtml = fs.readFileSync(path.join(ROOT, 'privacidad', 'index.html'), 'utf-8');
if (!privHtml.includes('cookie-consent.js')) {
  // Check if it has a broken end too
  if (!privHtml.includes('</body>')) {
    privHtml = privHtml.replace(/Cookies<\/a\r?\n/, 'Cookies</a>\r\n</footer>\r\n<script src="../cookie-consent.js" defer></script>\r\n</body>\r\n</html>\r\n');
  } else {
    privHtml = privHtml.replace('</body>', '<script src="../cookie-consent.js" defer></script>\r\n</body>');
  }
  fs.writeFileSync(path.join(ROOT, 'privacidad', 'index.html'), privHtml, 'utf-8');
  console.log('Fixed privacidad');
} else {
  console.log('Privacidad already has cookie consent');
}

// Verify both
for (const d of ['aviso-legal', 'privacidad']) {
  const html = fs.readFileSync(path.join(ROOT, d, 'index.html'), 'utf-8');
  const hasCookie = html.includes('cookie-consent.js');
  const hasBody = html.includes('</body>');
  const hasHtml = html.includes('</html>');
  console.log(`${d}: cookie=${hasCookie}, </body>=${hasBody}, </html>=${hasHtml}`);
}
