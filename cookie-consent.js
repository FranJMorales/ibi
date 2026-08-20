/* ═══ Cookie Consent Banner ═══
   Gestion de consentimiento (RGPD) para Google AdSense.
   Se carga en todas las paginas via <script src="/cookie-consent.js" defer></script>

   IMPORTANTE: el estado por defecto de Consent Mode v2 se declara en el <head>
   de cada pagina (script id="tm-consent-default"), antes de que cargue AdSense.
   Este fichero solo se encarga del banner y de ACTUALIZAR el consentimiento.
*/
(function() {
  'use strict';

  var COOKIE_NAME = 'tm_cookie_consent';
  var COOKIE_DAYS = 365;

  function getCookie(name) {
    var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  function setCookie(name, value, days) {
    var d = new Date();
    d.setTime(d.getTime() + days * 86400000);
    document.cookie = name + '=' + value + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
  }

  function pushConsent(state) {
    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    gtag('consent', 'update', {
      ad_storage: state,
      ad_user_data: state,
      ad_personalization: state,
      analytics_storage: state
    });
  }

  function hideBanner() {
    var banner = document.getElementById('cookie-consent-banner');
    if (banner) banner.classList.add('cookie-hidden');
  }

  var existing = getCookie(COOKIE_NAME);

  // Visitante recurrente: reaplicamos su decision y no mostramos el banner.
  if (existing) {
    pushConsent(existing === 'accepted' ? 'granted' : 'denied');
    return;
  }

  function onAccept() {
    setCookie(COOKIE_NAME, 'accepted', COOKIE_DAYS);
    hideBanner();
    pushConsent('granted');
  }

  function onReject() {
    setCookie(COOKIE_NAME, 'rejected', COOKIE_DAYS);
    hideBanner();
    pushConsent('denied');
  }

  function injectBanner() {
    if (document.getElementById('cookie-consent-banner')) return;
    var banner = document.createElement('div');
    banner.id = 'cookie-consent-banner';
    banner.className = 'cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Consentimiento de cookies');
    banner.innerHTML =
      '<p>Utilizamos cookies propias y de terceros para mejorar tu experiencia y mostrar publicidad relevante. ' +
      'Puedes aceptar todas las cookies o rechazar las no esenciales. ' +
      '<a href="/cookies/">Más información</a>.</p>' +
      '<button class="cookie-btn cookie-accept" id="cookie-accept">Aceptar cookies</button>' +
      '<button class="cookie-btn cookie-reject" id="cookie-reject">Solo esenciales</button>';
    document.body.appendChild(banner);

    document.getElementById('cookie-accept').addEventListener('click', onAccept);
    document.getElementById('cookie-reject').addEventListener('click', onReject);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectBanner);
  } else {
    injectBanner();
  }
})();
