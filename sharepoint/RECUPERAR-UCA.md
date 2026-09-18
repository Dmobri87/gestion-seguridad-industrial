# Recuperar Carga Automática de GAE en SharePoint

## Situación actual

El UserCustomAction que auto-cargaba `app-completo.js` fue eliminado. La política
**NoScript** del tenant bloquea la recreación desde el navegador (REST API y CSOM dan 403).

El archivo `app-completo.js` **SÍ está en SharePoint** en:
`/sites/SeguridadIndustrial/SiteAssets/SSI-App/app-completo.js`

---

## Opción A — Solución inmediata: Bookmarklet

Guardar como marcador en el navegador con esta URL exacta:

```
javascript:void(function(){var s=document.createElement('script');s.src='/sites/SeguridadIndustrial/SiteAssets/SSI-App/app-completo.js?v='+Date.now();document.head.appendChild(s);}());
```

**Cómo usarlo:**
1. Abre `GestionEmergencias-Classic.aspx`
2. Haz clic en el marcador
3. La app carga en ~2 segundos

---

## Opción B — Solución permanente vía SharePoint Admin Center

Requiere acceso al **SharePoint Admin Center** como Global Admin o SharePoint Admin.

### Paso 1: Habilitar scripts personalizados para el sitio

1. Ir a: `https://ssidesarrollo-admin.sharepoint.com`
2. → **Sitios activos** → buscar "SeguridadIndustrial"
3. → Click en el nombre del sitio → **Configuración**
4. → **Scripting personalizado** → Seleccionar **"Permitir"**
5. Esperar ~24 horas (política de propagación del tenant)

### Paso 2: Recrear el UserCustomAction (desde el navegador)

Una vez habilitado el scripting, ejecutar esto en la consola del navegador
estando en `GestionEmergencias-Classic.aspx`:

```javascript
fetch('/sites/SeguridadIndustrial/_api/contextinfo', {
  method: 'POST',
  headers: { 'Accept': 'application/json;odata=verbose', 'Content-Length': '0' }
})
.then(r => r.json())
.then(d => {
  var digest = d.d.GetContextWebInformation.FormDigestValue;
  var sb = "(function(){if(window.__GE_SCRIPT_INJECTED__)return;window.__GE_SCRIPT_INJECTED__=true;function waitReact(n){if(window.React&&window.ReactDOM){var s=document.createElement('script');s.src='/sites/SeguridadIndustrial/SiteAssets/SSI-App/app-completo.js?v=4';document.head.appendChild(s);}else if(n>0){setTimeout(function(){waitReact(n-1);},300);}}waitReact(40);})();";
  return fetch('/sites/SeguridadIndustrial/_api/web/UserCustomActions', {
    method: 'POST',
    headers: {
      'X-RequestDigest': digest,
      'Content-Type': 'application/json;odata=verbose',
      'Accept': 'application/json;odata=verbose'
    },
    body: JSON.stringify({
      '__metadata': { 'type': 'SP.UserCustomAction' },
      'Name': 'GestionEmergenciasLoader',
      'Title': 'GestionEmergenciasLoader',
      'Location': 'ScriptLink',
      'ScriptBlock': sb,
      'Sequence': 100
    })
  });
})
.then(r => r.json())
.then(d => console.log('✅ UCA creado con ID:', d.d.Id));
```

---

## Opción C — Solución permanente vía PnP PowerShell (recomendada)

```powershell
# Instalar PnP PowerShell si no está instalado
Install-Module PnP.PowerShell -Force

# Conectar al sitio
Connect-PnPOnline -Url "https://ssidesarrollo.sharepoint.com/sites/SeguridadIndustrial" -Interactive

# Crear el UserCustomAction
$scriptBlock = "(function(){if(window.__GE_SCRIPT_INJECTED__)return;window.__GE_SCRIPT_INJECTED__=true;function waitReact(n){if(window.React&&window.ReactDOM){var s=document.createElement('script');s.src='/sites/SeguridadIndustrial/SiteAssets/SSI-App/app-completo.js?v=4';document.head.appendChild(s);}else if(n>0){setTimeout(function(){waitReact(n-1);},300);}}waitReact(40);})()"

Add-PnPCustomAction `
  -Scope Web `
  -Name "GestionEmergenciasLoader" `
  -Title "GestionEmergenciasLoader" `
  -Location "ScriptLink" `
  -ScriptBlock $scriptBlock `
  -Sequence 100

Write-Host "✅ UserCustomAction creado correctamente"
```

---

## Estado actual de app-completo.js en SharePoint

| Parche | Estado |
|--------|--------|
| Fix React Error #321 (hook mismatch en tryMount) | ✅ Aplicado |
| Fix Tabs (props.items \|\| props.tabs) | ✅ Aplicado |
| Versión del archivo | v4 (cache-buster) |

