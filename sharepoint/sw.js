// GAE Service Worker v4.2
// Inyecta app-completo.js automáticamente en GestionEmergencias-Classic.aspx
// Registrado desde app-completo.js — persiste en el browser sin necesidad de admin
// v4.2: usa ?v=6 para forzar recarga con fix CatalogoPage

var GAE_SCRIPT = '/sites/SeguridadIndustrial/SiteAssets/SSI-App/app-completo.js?v=6';
var TARGET_PAGE = 'GestionEmergencias-Classic';

self.addEventListener('install', function(e) {
  e.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', function(e) {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(e) {
  if (e.request.mode === 'navigate' && e.request.url.indexOf(TARGET_PAGE) > -1) {
    e.respondWith(
      fetch(e.request).then(function(response) {
        var ct = response.headers.get('content-type') || '';
        if (response.ok && ct.indexOf('text/html') > -1) {
          return response.text().then(function(html) {
            var injection = '<script type="text/javascript">' +
              '(function(){' +
              'if(window.__GE_SW_INJECTED)return;' +
              'window.__GE_SW_INJECTED=true;' +
              'var s=document.createElement("script");' +
              's.src="' + GAE_SCRIPT + '";' +
              'document.documentElement.appendChild(s);' +
              '})();' +
              '<\/script>';

            var modified = html;
            if (html.indexOf('</head>') > -1) {
              modified = html.replace('</head>', injection + '</head>');
            } else if (html.indexOf('</body>') > -1) {
              modified = html.replace('</body>', injection + '</body>');
            } else {
              modified = html + injection;
            }

            var headers = {};
            response.headers.forEach(function(val, key) {
              if (key.toLowerCase() !== 'content-length') {
                headers[key] = val;
              }
            });

            return new Response(modified, {
              status: response.status,
              statusText: response.statusText,
              headers: new Headers(headers)
            });
          });
        }
        return response;
      }).catch(function() {
        return fetch(e.request);
      })
    );
  }
});
