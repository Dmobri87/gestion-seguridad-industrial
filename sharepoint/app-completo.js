// ================================================================
// GESTIÓN DE EMERGENCIAS SSI — SharePoint Edition v4.0
// 10 Módulos: Dashboard, Emergencias, Equipos, Certificaciones,
//             Ejecución, Planificación, Catálogo, Reportes,
//             Desempeño TAEs, Administración
// Arquitectura: React 17 (window.React) + SP REST API
// ================================================================
(function () {
  'use strict';

  var R = window.React;
  var RD = window.ReactDOM;
  // React check moved to tryMount() — permite carga via SW antes de que SharePoint cargue React
  if (window.__GE_APP_LOADED__) { console.log('[GE] Ya cargado'); return; }

  var h = R.createElement;
  var useState = R.useState;
  var useEffect = R.useEffect;
  var useCallback = R.useCallback;
  var useMemo = R.useMemo;
  var useRef = R.useRef;

  var BASE = '/sites/SeguridadIndustrial';
  var API  = BASE + '/_api/web/lists/getbytitle';

  // ================================================================
  // CSS INJECTION
  // ================================================================
  var CSS = [
    /* ── Layout raíz ──────────────────────────────────────────── */
    '#ge-root{position:fixed;top:0;left:0;width:100%;height:100%;z-index:99999;display:flex;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;background:#f0f2f5;}',
    '#ge-sidebar{width:220px;min-width:220px;background:#001529;display:flex;flex-direction:column;overflow-y:auto;transition:width .2s;}',
    '#ge-sidebar.collapsed{width:56px;min-width:56px;}',
    '.ge-logo{padding:16px;color:#fff;font-size:16px;font-weight:700;border-bottom:1px solid rgba(255,255,255,.1);white-space:nowrap;overflow:hidden;}',
    '.ge-logo span{color:#1677ff;}',
    '.ge-nav{flex:1;padding:8px 0;}',
    '.ge-nav-item{display:flex;align-items:center;padding:10px 16px;color:rgba(255,255,255,.65);cursor:pointer;transition:all .2s;white-space:nowrap;border-left:3px solid transparent;}',
    '.ge-nav-item:hover{color:#fff;background:rgba(255,255,255,.08);}',
    '.ge-nav-item.active{color:#fff;background:rgba(22,119,255,.2);border-left-color:#1677ff;}',
    '.ge-nav-icon{font-size:16px;min-width:24px;}',
    '.ge-nav-label{margin-left:8px;font-size:13px;}',
    '#ge-sidebar.collapsed .ge-nav-label{display:none;}',
    '#ge-sidebar.collapsed .ge-logo-text{display:none;}',
    '.ge-main{flex:1;display:flex;flex-direction:column;overflow:hidden;}',
    '.ge-header{background:#fff;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #f0f0f0;box-shadow:0 1px 4px rgba(0,0,0,.08);}',
    '.ge-header-title{font-size:16px;font-weight:600;color:#333;}',
    '.ge-header-user{display:flex;align-items:center;gap:8px;color:#666;font-size:13px;}',
    '.ge-content{flex:1;overflow-y:auto;padding:24px;}',
    /* ── Títulos de página ────────────────────────────────────── */
    '.ge-page-title{font-size:20px;font-weight:600;color:#333;margin:0 0 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
    '.ge-page-sub{font-size:13px;color:#999;margin:0 0 20px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
    /* ── KPI grid ─────────────────────────────────────────────── */
    '.ge-kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}',
    '.ge-kpi-card{background:#fff;border-radius:8px;padding:16px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 3px rgba(0,0,0,.08);min-width:0;}',
    '.ge-kpi-icon{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}',
    '.ge-kpi-val{font-size:26px;font-weight:700;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
    '.ge-kpi-label{font-size:12px;color:#999;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
    '.ge-kpi-sub{font-size:11px;color:#bbb;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
    /* ── Cards y filas ────────────────────────────────────────── */
    '.ge-card{background:#fff;border-radius:8px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px;}',
    '.ge-card-title{font-size:15px;font-weight:600;color:#333;margin:0 0 16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}',
    '.ge-row{display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap;}',
    '.ge-col{flex:1;min-width:260px;}',
    /* ── Tablas con scroll horizontal ─────────────────────────── */
    '.ge-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:4px;}',
    '.ge-table{width:100%;border-collapse:collapse;min-width:480px;}',
    '.ge-table th{background:#fafafa;padding:10px 12px;text-align:left;font-size:12px;font-weight:600;color:#666;border-bottom:2px solid #f0f0f0;white-space:nowrap;}',
    '.ge-table td{padding:9px 12px;border-bottom:1px solid #f5f5f5;font-size:13px;color:#333;vertical-align:middle;}',
    '.ge-table tr:hover td{background:#fafafa;}',
    /* ── Badges y tags ────────────────────────────────────────── */
    '.ge-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500;white-space:nowrap;}',
    /* ── Botones ──────────────────────────────────────────────── */
    '.ge-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:8px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .2s;min-height:36px;white-space:nowrap;touch-action:manipulation;}',
    '.ge-btn-primary{background:#1677ff;color:#fff;} .ge-btn-primary:hover{background:#0958d9;}',
    '.ge-btn-danger{background:#ff4d4f;color:#fff;} .ge-btn-danger:hover{background:#cf1322;}',
    '.ge-btn-secondary{background:#f5f5f5;color:#333;border:1px solid #e0e0e0;} .ge-btn-secondary:hover{background:#e8e8e8;}',
    '.ge-btn-default{background:#fff;color:#333;border:1px solid #d9d9d9;} .ge-btn-default:hover{border-color:#1677ff;color:#1677ff;}',
    '.ge-btn-sm{padding:4px 10px;font-size:12px;min-height:28px;}',
    '.ge-btn-link{background:none;border:none;color:#1677ff;cursor:pointer;padding:4px 8px;font-size:13px;min-height:28px;touch-action:manipulation;} .ge-btn-link:hover{text-decoration:underline;}',
    /* ── Toolbar ──────────────────────────────────────────────── */
    '.ge-toolbar{display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;row-gap:8px;}',
    '.ge-toolbar-right{margin-left:auto;}',
    /* ── Inputs y formularios ─────────────────────────────────── */
    '.ge-input{padding:8px 11px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;outline:none;transition:border .2s;width:100%;box-sizing:border-box;min-height:36px;}',
    '.ge-input:focus{border-color:#1677ff;box-shadow:0 0 0 2px rgba(22,119,255,.1);}',
    '.ge-select{padding:8px 11px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;outline:none;background:#fff;width:100%;box-sizing:border-box;min-height:36px;}',
    '.ge-textarea{padding:8px 11px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;outline:none;width:100%;box-sizing:border-box;resize:vertical;min-height:80px;}',
    '.ge-form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}',
    '.ge-form-row.full{grid-template-columns:1fr;}',
    '.ge-form-group{display:flex;flex-direction:column;gap:4px;}',
    '.ge-label{font-size:12px;font-weight:500;color:#555;}',
    '.ge-label.required::after{content:" *";color:#ff4d4f;}',
    /* ── Modales ──────────────────────────────────────────────── */
    '.ge-modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.45);z-index:999999;display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box;}',
    '.ge-modal{background:#fff;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.18);max-width:640px;width:100%;max-height:90vh;display:flex;flex-direction:column;}',
    '.ge-modal-header{padding:16px 20px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}',
    '.ge-modal-title{font-size:16px;font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
    '.ge-modal-close{background:none;border:none;font-size:20px;cursor:pointer;color:#999;padding:4px 8px;line-height:1;flex-shrink:0;touch-action:manipulation;} .ge-modal-close:hover{color:#333;}',
    '.ge-modal-body{padding:20px;overflow-y:auto;flex:1;}',
    '.ge-modal-footer{padding:12px 20px;border-top:1px solid #f0f0f0;display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;flex-shrink:0;}',
    /* ── Tabs con scroll horizontal ───────────────────────────── */
    '.ge-tabs{display:flex;border-bottom:2px solid #f0f0f0;margin-bottom:16px;gap:0;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;}',
    '.ge-tabs::-webkit-scrollbar{display:none;}',
    '.ge-tab{padding:10px 16px;cursor:pointer;font-size:13px;color:#666;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .2s;white-space:nowrap;flex-shrink:0;touch-action:manipulation;}',
    '.ge-tab.active{color:#1677ff;border-bottom-color:#1677ff;font-weight:500;}',
    '.ge-tab:hover:not(.active){color:#333;}',
    /* ── Estado vacío y spinner ───────────────────────────────── */
    '.ge-empty{padding:40px 24px;text-align:center;color:#bbb;}',
    '.ge-empty-icon{font-size:40px;margin-bottom:10px;}',
    '.ge-spinner{display:flex;justify-content:center;padding:48px;}',
    '.ge-spinner-circle{width:32px;height:32px;border:3px solid #f0f0f0;border-top-color:#1677ff;border-radius:50%;animation:ge-spin .8s linear infinite;}',
    '@keyframes ge-spin{to{transform:rotate(360deg)}}',
    /* ── Alertas ──────────────────────────────────────────────── */
    '.ge-alert-success{background:#f6ffed;border:1px solid #b7eb8f;color:#389e0d;padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:12px;}',
    '.ge-alert-error{background:#fff2f0;border:1px solid #ffccc7;color:#cf1322;padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:12px;}',
    '.ge-alert-warning{background:#fffbe6;border:1px solid #ffe58f;color:#d48806;padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:12px;}',
    /* ── Semáforos y stats ────────────────────────────────────── */
    '.ge-tag{display:inline-flex;align-items:center;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;border:1px solid;white-space:nowrap;}',
    '.ge-semaforo-ok{color:#52c41a;background:#f6ffed;border-color:#b7eb8f;}',
    '.ge-semaforo-warn{color:#d48806;background:#fffbe6;border-color:#ffe58f;}',
    '.ge-semaforo-urgent{color:#fa8c16;background:#fff7e6;border-color:#ffd591;}',
    '.ge-semaforo-danger{color:#cf1322;background:#fff2f0;border-color:#ffccc7;}',
    '.ge-stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}',
    '.ge-stat-box{background:#fafafa;border-radius:6px;padding:12px;text-align:center;}',
    '.ge-stat-val{font-size:22px;font-weight:700;}',
    '.ge-stat-label{font-size:11px;color:#999;margin-top:2px;}',
    /* ── Clases auxiliares ────────────────────────────────────── */
    '.ge-page{padding:0;}',
    '.ge-page-header{margin-bottom:16px;}',
    '.ge-error{color:#cf1322;padding:12px;background:#fff2f0;border-radius:6px;border:1px solid #ffccc7;}',
    /* ── Media queries ────────────────────────────────────────── */
    '@media(max-width:1100px){.ge-kpi-grid{grid-template-columns:repeat(2,1fr);}}',
    '@media(max-width:900px){.ge-kpi-grid{grid-template-columns:repeat(2,1fr);}.ge-form-row{grid-template-columns:1fr;}.ge-card{padding:14px 16px;}}',
    '@media(max-width:768px){.ge-kpi-val{font-size:22px;}.ge-kpi-icon{width:38px;height:38px;font-size:18px;}.ge-btn{min-height:40px;padding:10px 16px;font-size:14px;}.ge-input,.ge-select{min-height:40px;font-size:14px;}.ge-modal-overlay{align-items:flex-end;padding:0;}.ge-modal{border-radius:14px 14px 0 0;max-height:92vh;}.ge-kpi-grid{gap:8px;}}',
    '@media(max-width:600px){#ge-sidebar{width:56px;min-width:56px;}.ge-nav-label{display:none;}.ge-logo-text{display:none;}.ge-content{padding:12px;}.ge-kpi-grid{grid-template-columns:repeat(2,1fr);gap:8px;}.ge-row{gap:10px;}.ge-col{min-width:220px;}.ge-card{padding:12px;}.ge-page-title{font-size:16px;}.ge-page-sub{font-size:12px;margin-bottom:14px;}.ge-toolbar{row-gap:6px;}.ge-empty{padding:28px 16px;}}',
    '@media(max-width:400px){.ge-kpi-grid{grid-template-columns:1fr 1fr;}.ge-stat-row{grid-template-columns:1fr 1fr;}.ge-form-row{grid-template-columns:1fr;}.ge-modal-footer{flex-direction:column;}.ge-modal-footer .ge-btn{width:100%;justify-content:center;}}'
  ].join('\n');

  (function injectCSS() {
    var el = document.getElementById('ge-styles');
    if (!el) { el = document.createElement('style'); el.id = 'ge-styles'; document.head.appendChild(el); }
    el.textContent = CSS;
  })();

  // ================================================================
  // UTILIDADES
  // ================================================================
  var digestCache = { val: null, exp: 0 };

  function getDigest() {
    if (digestCache.val && Date.now() < digestCache.exp) return Promise.resolve(digestCache.val);
    return fetch(BASE + '/_api/contextinfo', {
      method: 'POST',
      headers: { 'Accept': 'application/json;odata=verbose', 'Content-Length': '0' }
    }).then(function (r) { return r.json(); }).then(function (d) {
      digestCache.val = d.d.GetContextWebInformation.FormDigestValue;
      digestCache.exp = Date.now() + 1500000;
      return digestCache.val;
    });
  }

  function listType(name) {
    return 'SP.Data.' + name + 'ListItem';
  }

  function getItems(list, opts) {
    var url = API + "('" + list + "')/items";
    var q = [];
    if (opts && opts.select)  q.push('$select='  + opts.select);
    if (opts && opts.filter)  q.push('$filter='  + opts.filter);
    if (opts && opts.orderby) q.push('$orderby=' + opts.orderby);
    if (opts && opts.top)     q.push('$top='     + opts.top);
    if (q.length) url += '?' + q.join('&');
    return fetch(url, { headers: { 'Accept': 'application/json;odata=verbose' } })
      .then(function (r) { return r.json(); })
      .then(function (d) { return (d.d && d.d.results) ? d.d.results : []; });
  }

  // Normalizadores: mapean campos reales de SP a los nombres que espera la UI
  function normalizePlan(p) {
    return Object.assign({}, p, {
      TaeNombre: p.TaeNombre || p.UsuarioNombre || '',
      GrupoTrabajo: p.GrupoTrabajo || '',
      ActividadesPlaneadas: p.ActividadesPlaneadas !== undefined ? p.ActividadesPlaneadas : (p.TotalPlaneado || 0),
      ActividadesEjecutadas: p.ActividadesEjecutadas !== undefined ? p.ActividadesEjecutadas : (p.TotalEjecutado || 0),
      CumplimientoPorcentaje: p.CumplimientoPorcentaje !== undefined ? p.CumplimientoPorcentaje : (p.PorcentajeCumplimiento || 0)
    });
  }
  function normalizeActividad(a) {
    return Object.assign({}, a, {
      Nombre: a.Nombre || a.Title || '',
      Categoria: a.Categoria || a.CategoriaNombre || '',
      Estado: a.Estado || (a.Activo !== false ? 'Activo' : 'Inactivo')
    });
  }

  // ─── PERMISOS / ROL ──────────────────────────────────────────────────────
  function isAdmin(cu) { return cu && cu.Rol === 'Administrador'; }
  function isTAE(cu)   { return cu && cu.Rol === 'TAE'; }
  function isPSE(cu)   { return cu && cu.Rol === 'PSE'; }
  // Verdadero si el usuario actual es Admin o es el propietario del ítem (por nombre)
  function canEditOwn(cu, itemUserName) { return isAdmin(cu) || (cu && cu.Title && cu.Title === itemUserName); }

  function loadCurrentUser() {
    return fetch('/_api/web/currentuser?$select=Email,Title', {
      headers: { 'Accept': 'application/json;odata=verbose' }
    }).then(function(r) { return r.json(); })
      .then(function(d) {
        var email = d.d ? d.d.Email : '';
        var title = d.d ? d.d.Title : '';
        if (!email) return { Title: title || 'Usuario', Email: '', Rol: 'TAE', GrupoTrabajoNombre: '' };
        return getItems('SSI_Usuarios', {
          select: 'Id,Title,Email,Rol,GrupoTrabajoNombre,Activo',
          filter: "Email eq '" + email + "'",
          top: 1
        }).then(function(items) {
          if (items && items.length > 0) return items[0];
          // Si no está en SSI_Usuarios, asumir TAE con privilegios mínimos
          return { Title: title || email, Email: email, Rol: 'TAE', GrupoTrabajoNombre: '' };
        });
      })
      .catch(function() { return null; });
  }

  function createItem(list, data) {
    data.__metadata = { type: listType(list) };
    return getDigest().then(function (dig) {
      return fetch(API + "('" + list + "')/items", {
        method: 'POST',
        headers: {
          'Accept': 'application/json;odata=verbose',
          'Content-Type': 'application/json;odata=verbose',
          'X-RequestDigest': dig
        },
        body: JSON.stringify(data)
      }).then(function (r) { return r.json(); });
    });
  }

  function updateItem(list, id, data) {
    data.__metadata = { type: listType(list) };
    return getDigest().then(function (dig) {
      return fetch(API + "('" + list + "')/items(" + id + ")", {
        method: 'POST',
        headers: {
          'Accept': 'application/json;odata=verbose',
          'Content-Type': 'application/json;odata=verbose',
          'X-RequestDigest': dig,
          'X-HTTP-Method': 'MERGE',
          'IF-MATCH': '*'
        },
        body: JSON.stringify(data)
      });
    });
  }

  function deleteItem(list, id) {
    return getDigest().then(function (dig) {
      return fetch(API + "('" + list + "')/items(" + id + ")", {
        method: 'POST',
        headers: { 'X-RequestDigest': dig, 'X-HTTP-Method': 'DELETE', 'IF-MATCH': '*' }
      });
    });
  }

  function fmtDate(v) {
    if (!v) return '—';
    var d = new Date(v);
    if (isNaN(d)) return v;
    return d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function fmtDT(v) {
    if (!v) return '—';
    var d = new Date(v);
    if (isNaN(d)) return v;
    return d.toLocaleString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function daysUntil(dateStr) {
    if (!dateStr) return null;
    var d = new Date(dateStr);
    if (isNaN(d)) return null;
    return Math.ceil((d - Date.now()) / 86400000);
  }

  function semaforoClass(dias) {
    if (dias === null || dias === undefined) return '';
    if (dias < 0)  return 'ge-semaforo-danger';
    if (dias <= 7)  return 'ge-semaforo-urgent';
    if (dias <= 30) return 'ge-semaforo-warn';
    return 'ge-semaforo-ok';
  }

  function semaforoLabel(dias) {
    if (dias === null || dias === undefined) return '—';
    if (dias < 0)   return 'Vencida (' + Math.abs(dias) + 'd)';
    if (dias === 0) return 'Vence hoy';
    return dias + ' días';
  }

  function estadoColor(estado) {
    var map = {
      'Activo': '#52c41a', 'Operativo': '#52c41a', 'Vigente': '#52c41a', 'Completado': '#52c41a',
      'Aprobado': '#52c41a', 'Cerrada': '#52c41a', 'Controlada': '#52c41a',
      'En Revision': '#faad14', 'En Mantenimiento': '#faad14', 'Por Vencer': '#faad14',
      'En Atención': '#faad14', 'En Progreso': '#faad14', 'Pendiente': '#faad14',
      'Fuera de Servicio': '#ff4d4f', 'Vencido': '#ff4d4f', 'Rechazado': '#ff4d4f',
      'Escalada': '#ff4d4f', 'Reportada': '#1677ff', 'Critica': '#ff4d4f'
    };
    return map[estado] || '#999';
  }

  function severidadColor(sev) {
    var map = { 'Baja': '#52c41a', 'Media': '#faad14', 'Alta': '#fa8c16', 'Critica': '#ff4d4f', 'Crítica': '#ff4d4f' };
    return map[sev] || '#999';
  }

  function todayISO() {
    return new Date().toISOString().split('T')[0];
  }

  function currentMonth() { return new Date().getMonth() + 1; }
  function currentYear()  { return new Date().getFullYear(); }

  var MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

  // ================================================================
  // COMPONENTES COMUNES
  // ================================================================
  function Spinner() {
    return h('div', { className: 'ge-spinner' },
      h('div', { className: 'ge-spinner-circle' })
    );
  }

  function Empty(props) {
    return h('div', { className: 'ge-empty' },
      h('div', { className: 'ge-empty-icon' }, props.icon || '📭'),
      h('div', null, props.text || 'Sin datos')
    );
  }

  function Badge(props) {
    var color = props.color || estadoColor(props.text);
    var style = {
      background: color + '20',
      color: color,
      border: '1px solid ' + color + '40'
    };
    return h('span', { className: 'ge-badge', style: style }, props.text);
  }

  function KPICard(props) {
    return h('div', { className: 'ge-kpi-card' },
      h('div', { className: 'ge-kpi-icon', style: { background: (props.color || '#1677ff') + '15' } },
        h('span', { style: { fontSize: '22px' } }, props.icon)
      ),
      h('div', null,
        h('div', { className: 'ge-kpi-val', style: { color: props.color || '#1677ff' } }, props.value),
        h('div', { className: 'ge-kpi-label' }, props.label),
        props.sub ? h('div', { className: 'ge-kpi-sub' }, props.sub) : null
      )
    );
  }

  function Modal(props) {
    if (!props.open) return null;
    var footer = props.footer;
    if (!footer && props.onSave) {
      footer = h('div', { style: { display: 'flex', justifyContent: 'flex-end', gap: 8 } },
        h('button', { className: 'ge-btn ge-btn-default', onClick: props.onClose }, 'Cancelar'),
        h('button', { className: 'ge-btn ge-btn-primary', disabled: props.saving, onClick: props.onSave },
          props.saving ? 'Guardando...' : 'Guardar')
      );
    }
    return h('div', { className: 'ge-modal-overlay', onClick: function (e) { if (e.target === e.currentTarget) props.onClose && props.onClose(); } },
      h('div', { className: 'ge-modal' },
        h('div', { className: 'ge-modal-header' },
          h('span', { className: 'ge-modal-title' }, props.title),
          h('button', { className: 'ge-modal-close', onClick: props.onClose }, '✕')
        ),
        h('div', { className: 'ge-modal-body' }, props.children),
        footer ? h('div', { className: 'ge-modal-footer' }, footer) : null
      )
    );
  }

  function Tabs(props) {
    var tabItems = props.items || props.tabs || [];
    return h('div', { className: 'ge-tabs' },
      tabItems.map(function (item) {
        return h('div', {
          key: item.key,
          className: 'ge-tab' + (props.active === item.key ? ' active' : ''),
          onClick: function () { props.onChange(item.key); }
        }, item.label);
      })
    );
  }

  function FG(props) { // FormGroup
    return h('div', { className: 'ge-form-group' },
      h('label', { className: 'ge-label' + (props.required ? ' required' : '') }, props.label),
      props.children
    );
  }

  function Alert(props) {
    if (!props.msg) return null;
    return h('div', { className: 'ge-alert-' + (props.type || 'error') }, props.msg);
  }

  // ================================================================
  // DASHBOARD PAGE
  // ================================================================
  function DashboardPage() {
    var s = useState({ loading: true, emergencias: [], equipos: [], certificaciones: [], accidentes: [], ejecuciones: [] });
    var data = s[0]; var setData = s[1];
    var selMes = useState(currentMonth()); var mes = selMes[0]; var setMes = selMes[1];
    var selAno = useState(currentYear()); var ano = selAno[0]; var setAno = selAno[1];

    function load() {
      setData(function (d) { return Object.assign({}, d, { loading: true }); });
      Promise.all([
        getItems('SSI_Emergencias', { select: 'Id,Estado,Severidad,TiempoRespuestaMinutos,FechaReporte', top: 500 }),
        getItems('SSI_Equipos', { select: 'Id,Estado,DisponibleDia,DisponibleNoche', top: 500 }),
        getItems('SSI_Certificaciones', { select: 'Id,Estado,DiasParaVencer', top: 500 }),
        getItems('SSI_Accidentes', { select: 'Id,Estado,Gravedad', top: 500 }),
        getItems('SSI_Ejecuciones', { select: 'Id,Estado,EstadoAprobacion,EjecutorNombre,CategoriaNombre', top: 500 })
      ]).then(function (results) {
        setData({ loading: false, emergencias: results[0], equipos: results[1], certificaciones: results[2], accidentes: results[3], ejecuciones: results[4] });
      }).catch(function () { setData(function (d) { return Object.assign({}, d, { loading: false }); }); });
    }

    useEffect(function () { load(); }, []);

    if (data.loading) return h(Spinner, null);

    var em = data.emergencias; var eq = data.equipos; var ce = data.certificaciones;
    var ac = data.accidentes; var ej = data.ejecuciones;

    var emActivas    = em.filter(function (e) { return e.Estado === 'En Atención' || e.Estado === 'Reportada'; }).length;
    var emCerradas   = em.filter(function (e) { return e.Estado === 'Cerrada' || e.Estado === 'Controlada'; }).length;
    var tiempos      = em.filter(function (e) { return e.TiempoRespuestaMinutos > 0; });
    var tiempoProm   = tiempos.length ? Math.round(tiempos.reduce(function (s, e) { return s + e.TiempoRespuestaMinutos; }, 0) / tiempos.length) : 0;
    var eqTotal      = eq.length;
    var eqOperativos = eq.filter(function (e) { return e.Estado === 'Activo' || e.Estado === 'Operativo'; }).length;
    var eqMantto     = eq.filter(function (e) { return e.Estado === 'En Mantenimiento' || e.Estado === 'En Revision'; }).length;
    var ceVencidas   = ce.filter(function (c) { return c.Estado === 'Vencido' || (c.DiasParaVencer !== null && c.DiasParaVencer < 0); }).length;
    var ce30         = ce.filter(function (c) { return c.DiasParaVencer >= 0 && c.DiasParaVencer <= 30; }).length;
    var acTotal      = ac.length;
    var ejAprobadas  = ej.filter(function (e) { return e.EstadoAprobacion === 'Aprobado'; }).length;
    var ejTotal      = ej.length;
    var cumpl        = ejTotal > 0 ? Math.round(ejAprobadas / ejTotal * 100) : 0;

    // Cumplimiento por categoría
    var catMap = {};
    ej.forEach(function (e) {
      var cat = e.CategoriaNombre || 'Sin categoría';
      if (!catMap[cat]) catMap[cat] = { total: 0, aprobadas: 0 };
      catMap[cat].total++;
      if (e.EstadoAprobacion === 'Aprobado') catMap[cat].aprobadas++;
    });

    return h('div', null,
      h('div', { className: 'ge-page-title' }, '📊 Panel de Control'),
      h('div', { className: 'ge-page-sub' }, 'Sistema de Gestión de Seguridad Industrial'),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '🚨', label: 'Emergencias Activas', value: emActivas, color: emActivas > 0 ? '#ff4d4f' : '#52c41a', sub: emCerradas + ' cerradas' }),
        h(KPICard, { icon: '⚠️', label: 'Accidentes Registrados', value: acTotal, color: acTotal > 0 ? '#fa8c16' : '#52c41a', sub: 'Total registrados' }),
        h(KPICard, { icon: '✅', label: 'Cumplimiento General', value: cumpl + '%', color: cumpl >= 80 ? '#52c41a' : cumpl >= 50 ? '#faad14' : '#ff4d4f', sub: ejAprobadas + '/' + ejTotal + ' ejecuciones' }),
        h(KPICard, { icon: '⏱️', label: 'Tiempo Resp. Prom.', value: tiempoProm + ' min', color: '#1677ff', sub: em.length + ' emergencias' })
      ),
      h('div', { className: 'ge-row' },
        h('div', { className: 'ge-col' },
          h('div', { className: 'ge-card' },
            h('div', { className: 'ge-card-title' }, '🔧 Estado de Equipos'),
            h('div', { className: 'ge-stat-row' },
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#1677ff' } }, eqTotal), h('div', { className: 'ge-stat-label' }, 'Total')),
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#52c41a' } }, eqOperativos), h('div', { className: 'ge-stat-label' }, 'Operativos')),
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#faad14' } }, eqMantto), h('div', { className: 'ge-stat-label' }, 'En Revisión'))
            )
          )
        ),
        h('div', { className: 'ge-col' },
          h('div', { className: 'ge-card' },
            h('div', { className: 'ge-card-title' }, '🎓 Certificaciones'),
            h('div', { className: 'ge-stat-row' },
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#1677ff' } }, ce.length), h('div', { className: 'ge-stat-label' }, 'Total')),
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#faad14' } }, ce30), h('div', { className: 'ge-stat-label' }, 'Por vencer <30d')),
              h('div', { className: 'ge-stat-box' }, h('div', { className: 'ge-stat-val', style: { color: '#ff4d4f' } }, ceVencidas), h('div', { className: 'ge-stat-label' }, 'Vencidas'))
            )
          )
        )
      ),
      Object.keys(catMap).length > 0 ? h('div', { className: 'ge-card' },
        h('div', { className: 'ge-card-title' }, '📈 Cumplimiento por Categoría'),
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              h('th', null, 'Categoría'), h('th', null, 'Ejecutadas'), h('th', null, 'Aprobadas'), h('th', null, 'Cumplimiento')
            )),
            h('tbody', null, Object.keys(catMap).map(function (cat) {
              var d = catMap[cat];
              var pct = d.total > 0 ? Math.round(d.aprobadas / d.total * 100) : 0;
              return h('tr', { key: cat },
                h('td', null, cat),
                h('td', null, d.total),
                h('td', null, d.aprobadas),
                h('td', null,
                  h('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                    h('div', { style: { flex: 1, height: 6, background: '#f0f0f0', borderRadius: 3, minWidth: 60 } },
                      h('div', { style: { width: pct + '%', height: '100%', background: pct >= 80 ? '#52c41a' : pct >= 50 ? '#faad14' : '#ff4d4f', borderRadius: 3 } })
                    ),
                    h('span', { style: { fontSize: 12, color: '#666', minWidth: 36 } }, pct + '%')
                  )
                )
              );
            }))
          )
        )
      ) : null
    );
  }

  // ================================================================
  // EMERGENCIAS PAGE
  // ================================================================
  function EmergenciasPage(props) {
    var cu = props.cu;
    var s = useState({ items: [], tipos: [], loading: true, modal: false, editing: null, error: '', success: '' });
    var d = s[0]; var set = s[1];
    var upd = function (patch) { set(function (prev) { return Object.assign({}, prev, patch); }); };

    var form = useState({ Title: '', TipoEmergenciaNombre: '', Ubicacion: '', Severidad: 'Media', Estado: 'Reportada', Descripcion: '', PersonasAfectadas: 0, PersonasHeridas: 0, AccionesRealizadas: '', Resultado: '' });
    var f = form[0]; var setF = form[1];

    function load() {
      upd({ loading: true });
      Promise.all([
        getItems('SSI_Emergencias', { select: 'Id,Title,CodigoEmergencia,TipoEmergenciaNombre,Severidad,Estado,FechaReporte,Ubicacion,TiempoRespuestaMinutos,PersonasAfectadas,PersonasHeridas', orderby: 'Created desc', top: 200 }),
        getItems('SSI_TiposEmergencia', { select: 'Id,Title,Codigo,Color', top: 50 })
      ]).then(function (r) { upd({ items: r[0], tipos: r[1], loading: false }); })
        .catch(function () { upd({ loading: false, error: 'Error al cargar emergencias' }); });
    }
    useEffect(function () { load(); }, []);

    function openNew() {
      setF({ Title: '', TipoEmergenciaNombre: '', Ubicacion: '', Severidad: 'Media', Estado: 'Reportada', Descripcion: '', PersonasAfectadas: 0, PersonasHeridas: 0, AccionesRealizadas: '', Resultado: '' });
      upd({ modal: true, editing: null, error: '' });
    }

    function openEdit(item) {
      setF({ Title: item.Title || '', TipoEmergenciaNombre: item.TipoEmergenciaNombre || '', Ubicacion: item.Ubicacion || '', Severidad: item.Severidad || 'Media', Estado: item.Estado || 'Reportada', Descripcion: item.Descripcion || '', PersonasAfectadas: item.PersonasAfectadas || 0, PersonasHeridas: item.PersonasHeridas || 0, AccionesRealizadas: item.AccionesRealizadas || '', Resultado: item.Resultado || '' });
      upd({ modal: true, editing: item, error: '' });
    }

    function save() {
      if (!f.Title || !f.TipoEmergenciaNombre) { upd({ error: 'Complete los campos requeridos' }); return; }
      var total = d.items.length;
      var codigo = 'EMR-' + String(total + 1).padStart(3, '0');
      var payload = Object.assign({}, f, { CodigoEmergencia: d.editing ? d.editing.CodigoEmergencia : codigo });
      var op = d.editing ? updateItem('SSI_Emergencias', d.editing.Id, payload) : createItem('SSI_Emergencias', payload);
      op.then(function () { upd({ modal: false, success: d.editing ? 'Emergencia actualizada' : 'Emergencia reportada', error: '' }); load(); })
        .catch(function () { upd({ error: 'Error al guardar. Intente nuevamente.' }); });
    }

    function del(item) {
      if (!confirm('¿Eliminar esta emergencia?')) return;
      deleteItem('SSI_Emergencias', item.Id).then(function () { upd({ success: 'Eliminada' }); load(); });
    }

    var totales = d.items.length;
    var activas  = d.items.filter(function (e) { return e.Estado === 'En Atención' || e.Estado === 'Reportada'; }).length;
    var cerradas = d.items.filter(function (e) { return e.Estado === 'Cerrada'; }).length;
    var tiempos  = d.items.filter(function (e) { return e.TiempoRespuestaMinutos > 0; });
    var tProm    = tiempos.length ? Math.round(tiempos.reduce(function (s, e) { return s + e.TiempoRespuestaMinutos; }, 0) / tiempos.length) : 0;

    return h('div', null,
      h('div', { className: 'ge-page-title' }, '🚨 Emergencias'),
      h('div', { className: 'ge-page-sub' }, 'Registro y seguimiento de emergencias'),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '📋', label: 'Total Emergencias', value: totales, color: '#1677ff' }),
        h(KPICard, { icon: '🔴', label: 'Activas', value: activas, color: activas > 0 ? '#ff4d4f' : '#52c41a' }),
        h(KPICard, { icon: '⏱️', label: 'Tiempo Resp. Prom.', value: tProm + ' min', color: '#1677ff' }),
        h(KPICard, { icon: '✅', label: 'Cerradas', value: cerradas, color: '#52c41a' })
      ),
      h(Alert, { msg: d.success, type: 'success' }),
      h(Alert, { msg: d.error, type: 'error' }),
      h('div', { className: 'ge-card' },
        h('div', { className: 'ge-toolbar' },
          h('span', { style: { fontWeight: 600 } }, '📋 Registro de Emergencias'),
          h('div', { className: 'ge-toolbar-right' },
            h('button', { className: 'ge-btn ge-btn-danger', onClick: openNew }, '+ Reportar Emergencia')
          )
        ),
        d.loading ? h(Spinner, null) :
        d.items.length === 0 ? h(Empty, { icon: '🚨', text: 'No hay emergencias registradas' }) :
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              h('th', null, 'Código'), h('th', null, 'Descripción'), h('th', null, 'Tipo'),
              h('th', null, 'Ubicación'), h('th', null, 'Severidad'), h('th', null, 'Estado'),
              h('th', null, 'Afectados'), h('th', null, 'Acciones')
            )),
            h('tbody', null, d.items.map(function (item) {
              return h('tr', { key: item.Id },
                h('td', null, h('code', { style: { fontSize: 11 } }, item.CodigoEmergencia || '—')),
                h('td', null, item.Title),
                h('td', null, item.TipoEmergenciaNombre),
                h('td', null, item.Ubicacion || '—'),
                h('td', null, h(Badge, { text: item.Severidad, color: severidadColor(item.Severidad) })),
                h('td', null, h(Badge, { text: item.Estado })),
                h('td', null, item.PersonasAfectadas || 0),
                h('td', null,
                  canEditOwn(cu, item.Title) && h('button', { className: 'ge-btn-link', onClick: function () { openEdit(item); } }, '✏️'),
                  isAdmin(cu) && h('button', { className: 'ge-btn-link', style: { color: '#ff4d4f' }, onClick: function () { del(item); } }, '🗑️')
                )
              );
            }))
          )
        )
      ),
      h(Modal, { open: d.modal, title: d.editing ? 'Editar Emergencia' : 'Reportar Emergencia', onClose: function () { upd({ modal: false }); },
        footer: h('div', { style: { display: 'flex', gap: 8 } },
          h('button', { className: 'ge-btn ge-btn-default', onClick: function () { upd({ modal: false }); } }, 'Cancelar'),
          h('button', { className: 'ge-btn ge-btn-danger', onClick: save }, d.editing ? 'Guardar cambios' : 'Reportar')
        )
      },
        h(Alert, { msg: d.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Título / Descripción corta', required: true },
            h('input', { className: 'ge-input', value: f.Title, placeholder: 'Ej: Incendio en bodega', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Title: e.target.value }); }); } })
          ),
          h(FG, { label: 'Tipo de Emergencia', required: true },
            h('select', { className: 'ge-select', value: f.TipoEmergenciaNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { TipoEmergenciaNombre: e.target.value }); }); } },
              h('option', { value: '' }, '-- Selecciona tipo --'),
              d.tipos.map(function (t) { return h('option', { key: t.Id, value: t.Title }, t.Title); })
            )
          )
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Ubicación' },
            h('input', { className: 'ge-input', value: f.Ubicacion, placeholder: 'Ej: Planta A - Sector 3', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Ubicacion: e.target.value }); }); } })
          ),
          h(FG, { label: 'Severidad' },
            h('select', { className: 'ge-select', value: f.Severidad, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Severidad: e.target.value }); }); } },
              ['Baja','Media','Alta','Critica'].map(function (s) { return h('option', { key: s, value: s }, s); })
            )
          )
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Estado' },
            h('select', { className: 'ge-select', value: f.Estado, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Estado: e.target.value }); }); } },
              ['Reportada','En Atención','Controlada','Cerrada','Escalada'].map(function (s) { return h('option', { key: s, value: s }, s); })
            )
          ),
          h(FG, { label: 'Personas Afectadas' },
            h('input', { className: 'ge-input', type: 'number', min: 0, value: f.PersonasAfectadas, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { PersonasAfectadas: parseInt(e.target.value) || 0 }); }); } })
          )
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'Descripción detallada' },
            h('textarea', { className: 'ge-textarea', value: f.Descripcion, placeholder: 'Describe la emergencia...', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Descripcion: e.target.value }); }); } })
          )
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'Acciones Realizadas' },
            h('textarea', { className: 'ge-textarea', value: f.AccionesRealizadas, placeholder: 'Acciones tomadas...', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { AccionesRealizadas: e.target.value }); }); } })
          )
        )
      )
    );
  }

  // ================================================================
  // EQUIPOS PAGE
  // ================================================================
  function EquiposPage(props) {
    var cu = props.cu;
    var s = useState({ items: [], loading: true, modal: false, editing: null, tab: 'todos', error: '', success: '' });
    var d = s[0]; var set = s[1];
    var upd = function (patch) { set(function (p) { return Object.assign({}, p, patch); }); };
    var form = useState({ Title: '', Codigo: '', CategoriaNombre: '', Descripcion: '', Marca: '', Modelo: '', NumeroSerie: '', Estado: 'Activo', DisponibleDia: true, DisponibleNoche: true, Ubicacion: '', FrecuenciaMantenimientoDias: 30 });
    var f = form[0]; var setF = form[1];

    function load() {
      upd({ loading: true });
      getItems('SSI_Equipos', { select: 'Id,Title,Codigo,CategoriaNombre,Estado,DisponibleDia,DisponibleNoche,Ubicacion,FechaProximoMantenimiento,Marca,Modelo,NumeroSerie,Descripcion,FrecuenciaMantenimientoDias', orderby: 'Codigo asc', top: 200 })
        .then(function (r) { upd({ items: r, loading: false }); })
        .catch(function () { upd({ loading: false, error: 'Error al cargar equipos' }); });
    }
    useEffect(function () { load(); }, []);

    function openNew() {
      setF({ Title: '', Codigo: '', CategoriaNombre: '', Descripcion: '', Marca: '', Modelo: '', NumeroSerie: '', Estado: 'Activo', DisponibleDia: true, DisponibleNoche: true, Ubicacion: '', FrecuenciaMantenimientoDias: 30 });
      upd({ modal: true, editing: null, error: '' });
    }
    function openEdit(item) {
      setF({ Title: item.Title || '', Codigo: item.Codigo || '', CategoriaNombre: item.CategoriaNombre || '', Descripcion: item.Descripcion || '', Marca: item.Marca || '', Modelo: item.Modelo || '', NumeroSerie: item.NumeroSerie || '', Estado: item.Estado || 'Activo', DisponibleDia: item.DisponibleDia !== false, DisponibleNoche: item.DisponibleNoche !== false, Ubicacion: item.Ubicacion || '', FrecuenciaMantenimientoDias: item.FrecuenciaMantenimientoDias || 30 });
      upd({ modal: true, editing: item, error: '' });
    }
    function save() {
      if (!f.Title || !f.Codigo) { upd({ error: 'Nombre y Código son obligatorios' }); return; }
      var op = d.editing ? updateItem('SSI_Equipos', d.editing.Id, f) : createItem('SSI_Equipos', f);
      op.then(function () { upd({ modal: false, success: d.editing ? 'Equipo actualizado' : 'Equipo agregado', error: '' }); load(); })
        .catch(function () { upd({ error: 'Error al guardar' }); });
    }
    function del(item) {
      if (!confirm('¿Eliminar ' + item.Title + '?')) return;
      deleteItem('SSI_Equipos', item.Id).then(function () { upd({ success: 'Eliminado' }); load(); });
    }

    var visibles = d.items.filter(function (e) {
      if (d.tab === 'operativos') return e.Estado === 'Activo' || e.Estado === 'Operativo';
      if (d.tab === 'fuera') return e.Estado === 'Fuera de Servicio' || e.Estado === 'Dado de Baja';
      return true;
    });

    var opCount  = d.items.filter(function (e) { return e.Estado === 'Activo' || e.Estado === 'Operativo'; }).length;
    var diaCount = d.items.filter(function (e) { return e.DisponibleDia; }).length;
    var nocCount = d.items.filter(function (e) { return e.DisponibleNoche; }).length;

    return h('div', null,
      h('div', { className: 'ge-page-title' }, '🔧 Equipos / EPP'),
      h('div', { className: 'ge-page-sub' }, 'Inventario de equipos de protección personal'),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '🔧', label: 'Total Equipos', value: d.items.length, color: '#1677ff' }),
        h(KPICard, { icon: '✅', label: 'Operativos', value: opCount + '/' + d.items.length, color: '#52c41a' }),
        h(KPICard, { icon: '☀️', label: 'Disp. Turno Día', value: diaCount + '/' + d.items.length, color: '#fa8c16' }),
        h(KPICard, { icon: '🌙', label: 'Disp. Turno Noche', value: nocCount + '/' + d.items.length, color: '#722ed1' })
      ),
      h(Alert, { msg: d.success, type: 'success' }),
      h('div', { className: 'ge-card' },
        h(Tabs, { items: [{ key: 'todos', label: 'Todos (' + d.items.length + ')' }, { key: 'operativos', label: 'Operativos (' + opCount + ')' }, { key: 'fuera', label: 'Fuera de Servicio' }], active: d.tab, onChange: function (k) { upd({ tab: k }); } }),
        h('div', { className: 'ge-toolbar' },
          isAdmin(cu) && h('div', { className: 'ge-toolbar-right' },
            h('button', { className: 'ge-btn ge-btn-primary', onClick: openNew }, '+ Agregar Equipo')
          )
        ),
        d.loading ? h(Spinner, null) :
        visibles.length === 0 ? h(Empty, { icon: '🔧', text: 'No hay equipos en esta categoría' }) :
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              h('th', null, 'N°'), h('th', null, 'Código'), h('th', null, 'Nombre'), h('th', null, 'Categoría'),
              h('th', null, 'Ubicación'), h('th', null, 'Estado'), h('th', null, 'Disponibilidad'), h('th', null, 'Prox. Mantto.'), h('th', null, 'Acciones')
            )),
            h('tbody', null, visibles.map(function (item, idx) {
              return h('tr', { key: item.Id },
                h('td', null, idx + 1),
                h('td', null, h('code', { style: { fontSize: 11, background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 } }, item.Codigo)),
                h('td', null, item.Title),
                h('td', null, item.CategoriaNombre || '—'),
                h('td', null, item.Ubicacion || '—'),
                h('td', null, h(Badge, { text: item.Estado })),
                h('td', null,
                  h('div', { style: { display: 'flex', gap: 4, flexWrap: 'nowrap' } },
                    item.DisponibleDia ? h('span', { className: 'ge-tag ge-semaforo-ok' }, '☀️ Día') : h('span', { className: 'ge-tag', style: { color: '#bbb', background: '#fafafa', borderColor: '#e8e8e8' } }, '☀️'),
                    item.DisponibleNoche ? h('span', { className: 'ge-tag ge-semaforo-ok' }, '🌙 Noche') : h('span', { className: 'ge-tag', style: { color: '#bbb', background: '#fafafa', borderColor: '#e8e8e8' } }, '🌙')
                  )
                ),
                h('td', null, fmtDate(item.FechaProximoMantenimiento)),
                h('td', null,
                  isAdmin(cu) && h('button', { className: 'ge-btn-link', onClick: function () { openEdit(item); } }, '✏️'),
                  isAdmin(cu) && h('button', { className: 'ge-btn-link', style: { color: '#ff4d4f' }, onClick: function () { del(item); } }, '🗑️')
                )
              );
            }))
          )
        )
      ),
      h(Modal, { open: d.modal, title: d.editing ? 'Editar Equipo' : 'Agregar Equipo', onClose: function () { upd({ modal: false }); },
        footer: h('div', { style: { display: 'flex', gap: 8 } },
          h('button', { className: 'ge-btn ge-btn-default', onClick: function () { upd({ modal: false }); } }, 'Cancelar'),
          h('button', { className: 'ge-btn ge-btn-primary', onClick: save }, d.editing ? 'Guardar' : 'Agregar')
        )
      },
        h(Alert, { msg: d.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre', required: true }, h('input', { className: 'ge-input', value: f.Title, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Title: e.target.value }); }); } })),
          h(FG, { label: 'Código', required: true }, h('input', { className: 'ge-input', value: f.Codigo, placeholder: 'Ej: EPP-CSC-001', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Codigo: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Categoría' }, h('input', { className: 'ge-input', value: f.CategoriaNombre, placeholder: 'Ej: Protección Cabeza', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { CategoriaNombre: e.target.value }); }); } })),
          h(FG, { label: 'Ubicación' }, h('input', { className: 'ge-input', value: f.Ubicacion, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Ubicacion: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Marca' }, h('input', { className: 'ge-input', value: f.Marca, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Marca: e.target.value }); }); } })),
          h(FG, { label: 'Modelo' }, h('input', { className: 'ge-input', value: f.Modelo, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Modelo: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Estado' },
            h('select', { className: 'ge-select', value: f.Estado, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Estado: e.target.value }); }); } },
              ['Activo','Operativo','En Mantenimiento','En Revision','Fuera de Servicio','Dado de Baja'].map(function (s) { return h('option', { key: s, value: s }, s); })
            )
          ),
          h(FG, { label: 'Frec. Mantenimiento (días)' }, h('input', { className: 'ge-input', type: 'number', min: 1, value: f.FrecuenciaMantenimientoDias, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { FrecuenciaMantenimientoDias: parseInt(e.target.value) || 30 }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Disponible Turno Día' },
            h('select', { className: 'ge-select', value: f.DisponibleDia ? 'si' : 'no', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { DisponibleDia: e.target.value === 'si' }); }); } },
              h('option', { value: 'si' }, 'Sí'), h('option', { value: 'no' }, 'No')
            )
          ),
          h(FG, { label: 'Disponible Turno Noche' },
            h('select', { className: 'ge-select', value: f.DisponibleNoche ? 'si' : 'no', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { DisponibleNoche: e.target.value === 'si' }); }); } },
              h('option', { value: 'si' }, 'Sí'), h('option', { value: 'no' }, 'No')
            )
          )
        )
      )
    );
  }

  // ================================================================
  // CERTIFICACIONES PAGE
  // ================================================================
  function CertificacionesPage(props) {
    var cu = props.cu;
    var s = useState({ items: [], tipos: [], loading: true, modal: false, editing: null, tab: 'vencer', filtroTAE: '', error: '', success: '' });
    var d = s[0]; var set = s[1];
    var upd = function (patch) { set(function (p) { return Object.assign({}, p, patch); }); };
    var form = useState({ Title: '', UsuarioNombre: '', TipoCertificacionNombre: '', NumeroCertificado: '', EntidadEmisora: '', FechaEmision: todayISO(), FechaVencimiento: '', Estado: 'Vigente', DiasParaVencer: 365, Notas: '' });
    var f = form[0]; var setF = form[1];

    function load() {
      upd({ loading: true });
      Promise.all([
        getItems('SSI_Certificaciones', { select: 'Id,Title,UsuarioNombre,TipoCertificacionNombre,NumeroCertificado,EntidadEmisora,FechaEmision,FechaVencimiento,Estado,DiasParaVencer,Notas', orderby: 'DiasParaVencer asc', top: 300 }),
        getItems('SSI_TiposCertificacion', { select: 'Id,Title,Codigo,ValidezDias', top: 50 })
      ]).then(function (r) { upd({ items: r[0], tipos: r[1], loading: false }); })
        .catch(function () { upd({ loading: false }); });
    }
    useEffect(function () { load(); }, []);

    function openNew() {
      setF({ Title: '', UsuarioNombre: '', TipoCertificacionNombre: '', NumeroCertificado: '', EntidadEmisora: '', FechaEmision: todayISO(), FechaVencimiento: '', Estado: 'Vigente', DiasParaVencer: 365, Notas: '' });
      upd({ modal: true, editing: null, error: '' });
    }
    function openEdit(item) {
      setF({ Title: item.Title || '', UsuarioNombre: item.UsuarioNombre || '', TipoCertificacionNombre: item.TipoCertificacionNombre || '', NumeroCertificado: item.NumeroCertificado || '', EntidadEmisora: item.EntidadEmisora || '', FechaEmision: item.FechaEmision ? item.FechaEmision.split('T')[0] : '', FechaVencimiento: item.FechaVencimiento ? item.FechaVencimiento.split('T')[0] : '', Estado: item.Estado || 'Vigente', DiasParaVencer: item.DiasParaVencer || 0, Notas: item.Notas || '' });
      upd({ modal: true, editing: item, error: '' });
    }
    function save() {
      if (!f.UsuarioNombre || !f.TipoCertificacionNombre) { upd({ error: 'Nombre de usuario y tipo son obligatorios' }); return; }
      var titulo = f.TipoCertificacionNombre + ' - ' + f.UsuarioNombre;
      var dias = f.FechaVencimiento ? daysUntil(f.FechaVencimiento) : f.DiasParaVencer;
      var estado = dias === null ? f.Estado : (dias < 0 ? 'Vencido' : dias <= 30 ? 'Por Vencer' : 'Vigente');
      var payload = Object.assign({}, f, { Title: titulo, DiasParaVencer: dias || 0, Estado: estado });
      var op = d.editing ? updateItem('SSI_Certificaciones', d.editing.Id, payload) : createItem('SSI_Certificaciones', payload);
      op.then(function () { upd({ modal: false, success: d.editing ? 'Certificación actualizada' : 'Certificación registrada', error: '' }); load(); })
        .catch(function () { upd({ error: 'Error al guardar' }); });
    }
    function del(item) {
      if (!confirm('¿Eliminar esta certificación?')) return;
      deleteItem('SSI_Certificaciones', item.Id).then(function () { upd({ success: 'Eliminada' }); load(); });
    }

    var vencer30 = d.items.filter(function (c) { return c.DiasParaVencer >= 0 && c.DiasParaVencer <= 30; });
    var vencer7  = d.items.filter(function (c) { return c.DiasParaVencer >= 0 && c.DiasParaVencer <= 7; });
    var vencidas = d.items.filter(function (c) { return c.Estado === 'Vencido' || c.DiasParaVencer < 0; });

    var taeSet = {};
    d.items.forEach(function (c) { if (c.UsuarioNombre) taeSet[c.UsuarioNombre] = true; });
    var taes = Object.keys(taeSet).sort();

    var itemsTab = d.tab === 'vencer' ? vencer30 :
                   d.tab === 'tae' ? d.items.filter(function (c) { return !d.filtroTAE || c.UsuarioNombre === d.filtroTAE; }) :
                   d.items;

    return h('div', null,
      h('div', { className: 'ge-page-title' }, '🎓 Certificaciones'),
      h('div', { className: 'ge-page-sub' }, 'Gestión de certificaciones y vigencias del personal'),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '📋', label: 'Total', value: d.items.length, color: '#1677ff' }),
        h(KPICard, { icon: '⚠️', label: 'Por Vencer <30d', value: vencer30.length, color: '#faad14' }),
        h(KPICard, { icon: '🔴', label: 'Críticas <7d', value: vencer7.length, color: '#ff4d4f' }),
        h(KPICard, { icon: '❌', label: 'Vencidas', value: vencidas.length, color: '#ff4d4f' })
      ),
      h(Alert, { msg: d.success, type: 'success' }),
      h('div', { className: 'ge-card' },
        h(Tabs, { items: [{ key: 'vencer', label: 'Por Vencer (' + vencer30.length + ')' }, { key: 'tae', label: 'Por TAE' }, { key: 'todos', label: 'Todos (' + d.items.length + ')' }], active: d.tab, onChange: function (k) { upd({ tab: k }); } }),
        h('div', { className: 'ge-toolbar' },
          d.tab === 'tae' ? h('select', { className: 'ge-select', style: { width: 200 }, value: d.filtroTAE, onChange: function (e) { upd({ filtroTAE: e.target.value }); } },
            h('option', { value: '' }, 'Todos los TAEs'),
            taes.map(function (t) { return h('option', { key: t, value: t }, t); })
          ) : null,
          isAdmin(cu) && h('div', { className: 'ge-toolbar-right' },
            h('button', { className: 'ge-btn ge-btn-primary', onClick: openNew }, '+ Registrar Certificación')
          )
        ),
        d.loading ? h(Spinner, null) :
        itemsTab.length === 0 ? h(Empty, { icon: '🎓', text: 'No hay certificaciones en esta vista' }) :
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              h('th', null, 'Personal'), h('th', null, 'Tipo'), h('th', null, 'Número'), h('th', null, 'Emisor'),
              h('th', null, 'F. Vencimiento'), h('th', null, 'Vigencia'), h('th', null, 'Estado'), h('th', null, 'Acciones')
            )),
            h('tbody', null, itemsTab.map(function (item) {
              var dias = item.DiasParaVencer;
              return h('tr', { key: item.Id },
                h('td', null, h('strong', null, item.UsuarioNombre || '—')),
                h('td', null, item.TipoCertificacionNombre || '—'),
                h('td', null, item.NumeroCertificado || '—'),
                h('td', null, item.EntidadEmisora || '—'),
                h('td', null, fmtDate(item.FechaVencimiento)),
                h('td', null, h('span', { className: 'ge-tag ' + semaforoClass(dias) }, semaforoLabel(dias))),
                h('td', null, h(Badge, { text: item.Estado })),
                h('td', null,
                  isAdmin(cu) && h('button', { className: 'ge-btn-link', onClick: function () { openEdit(item); } }, '✏️'),
                  isAdmin(cu) && h('button', { className: 'ge-btn-link', style: { color: '#ff4d4f' }, onClick: function () { del(item); } }, '🗑️')
                )
              );
            }))
          )
        )
      ),
      h(Modal, { open: d.modal, title: d.editing ? 'Editar Certificación' : 'Registrar Certificación', onClose: function () { upd({ modal: false }); },
        footer: h('div', { style: { display: 'flex', gap: 8 } },
          h('button', { className: 'ge-btn ge-btn-default', onClick: function () { upd({ modal: false }); } }, 'Cancelar'),
          h('button', { className: 'ge-btn ge-btn-primary', onClick: save }, d.editing ? 'Guardar' : 'Registrar')
        )
      },
        h(Alert, { msg: d.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre del personal', required: true }, h('input', { className: 'ge-input', value: f.UsuarioNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { UsuarioNombre: e.target.value }); }); } })),
          h(FG, { label: 'Tipo de Certificación', required: true },
            h('select', { className: 'ge-select', value: f.TipoCertificacionNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { TipoCertificacionNombre: e.target.value }); }); } },
              h('option', { value: '' }, '-- Seleccionar --'),
              d.tipos.map(function (t) { return h('option', { key: t.Id, value: t.Title }, t.Title); })
            )
          )
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Número de Certificado' }, h('input', { className: 'ge-input', value: f.NumeroCertificado, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { NumeroCertificado: e.target.value }); }); } })),
          h(FG, { label: 'Entidad Emisora' }, h('input', { className: 'ge-input', value: f.EntidadEmisora, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { EntidadEmisora: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Fecha de Emisión' }, h('input', { className: 'ge-input', type: 'date', value: f.FechaEmision, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { FechaEmision: e.target.value }); }); } })),
          h(FG, { label: 'Fecha de Vencimiento' }, h('input', { className: 'ge-input', type: 'date', value: f.FechaVencimiento, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { FechaVencimiento: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'Notas' }, h('textarea', { className: 'ge-textarea', value: f.Notas, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Notas: e.target.value }); }); } }))
        )
      )
    );
  }

  // ================================================================
  // EJECUCIÓN PAGE
  // ================================================================
  function EjecucionPage(props) {
    var cu = props.cu;
    var s = useState({ items: [], loading: true, modal: false, editing: null, tab: 'pendientes', error: '', success: '' });
    var d = s[0]; var set = s[1];
    var upd = function (patch) { set(function (p) { return Object.assign({}, p, patch); }); };
    var form = useState({ Title: '', ActividadNombre: '', CategoriaNombre: '', EjecutorNombre: '', FechaEjecucion: todayISO(), NumeroCiclo: 1, Estado: 'Completado', Observacion: '', Cantidad: 1, EstadoAprobacion: 'Pendiente', UrlEvidencias: '' });
    var f = form[0]; var setF = form[1];

    function load() {
      upd({ loading: true });
      getItems('SSI_Ejecuciones', { select: 'Id,Title,ActividadNombre,CategoriaNombre,EjecutorNombre,FechaEjecucion,NumeroCiclo,Estado,EstadoAprobacion,Observacion,Cantidad,UrlEvidencias,AprobadorNombre,MotivoRechazo', orderby: 'Created desc', top: 300 })
        .then(function (r) { upd({ items: r, loading: false }); })
        .catch(function () { upd({ loading: false }); });
    }
    useEffect(function () { load(); }, []);

    function openNew() {
      setF({ Title: '', ActividadNombre: '', CategoriaNombre: '', EjecutorNombre: '', FechaEjecucion: todayISO(), NumeroCiclo: 1, Estado: 'Completado', Observacion: '', Cantidad: 1, EstadoAprobacion: 'Pendiente', UrlEvidencias: '' });
      upd({ modal: true, editing: null, error: '' });
    }
    function openEdit(item) {
      setF({ Title: item.Title || '', ActividadNombre: item.ActividadNombre || '', CategoriaNombre: item.CategoriaNombre || '', EjecutorNombre: item.EjecutorNombre || '', FechaEjecucion: item.FechaEjecucion ? item.FechaEjecucion.split('T')[0] : todayISO(), NumeroCiclo: item.NumeroCiclo || 1, Estado: item.Estado || 'Completado', Observacion: item.Observacion || '', Cantidad: item.Cantidad || 1, EstadoAprobacion: item.EstadoAprobacion || 'Pendiente', UrlEvidencias: item.UrlEvidencias || '' });
      upd({ modal: true, editing: item, error: '' });
    }
    function save() {
      if (!f.ActividadNombre || !f.EjecutorNombre) { upd({ error: 'Actividad y ejecutor son obligatorios' }); return; }
      var titulo = f.ActividadNombre + ' - ' + f.EjecutorNombre;
      var payload = Object.assign({}, f, { Title: titulo });
      var op = d.editing ? updateItem('SSI_Ejecuciones', d.editing.Id, payload) : createItem('SSI_Ejecuciones', payload);
      op.then(function () { upd({ modal: false, success: d.editing ? 'Ejecución actualizada' : 'Ejecución registrada', error: '' }); load(); })
        .catch(function () { upd({ error: 'Error al guardar' }); });
    }
    function aprobar(item) {
      updateItem('SSI_Ejecuciones', item.Id, { EstadoAprobacion: 'Aprobado' })
        .then(function () { upd({ success: 'Aprobada' }); load(); });
    }
    function rechazar(item) {
      var motivo = prompt('Motivo del rechazo:');
      if (!motivo) return;
      updateItem('SSI_Ejecuciones', item.Id, { EstadoAprobacion: 'Rechazado', MotivoRechazo: motivo })
        .then(function () { upd({ success: 'Rechazada' }); load(); });
    }
    function del(item) {
      if (!confirm('¿Eliminar esta ejecución?')) return;
      deleteItem('SSI_Ejecuciones', item.Id).then(function () { upd({ success: 'Eliminada' }); load(); });
    }

    var total     = d.items.length;
    var completadas = d.items.filter(function (e) { return e.Estado === 'Completado'; }).length;
    var novedad   = d.items.filter(function (e) { return e.Estado === 'Con Novedad'; }).length;
    var porAprobar = d.items.filter(function (e) { return e.EstadoAprobacion === 'Pendiente'; }).length;
    var aprobadas = d.items.filter(function (e) { return e.EstadoAprobacion === 'Aprobado'; }).length;
    var rechazadas = d.items.filter(function (e) { return e.EstadoAprobacion === 'Rechazado'; }).length;

    var itemsTab = d.tab === 'pendientes' ? d.items.filter(function (e) { return e.EstadoAprobacion === 'Pendiente'; }) :
                   d.tab === 'aprobar'    ? d.items.filter(function (e) { return e.EstadoAprobacion === 'Pendiente'; }) :
                   d.tab === 'rechazadas' ? d.items.filter(function (e) { return e.EstadoAprobacion === 'Rechazado'; }) :
                   d.items;

    return h('div', null,
      h('div', { className: 'ge-page-title' }, '⚡ Registro de Ejecuciones'),
      h('div', { className: 'ge-page-sub' }, 'Gestiona y registra las actividades ejecutadas'),
      h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 12, marginBottom: 20 } },
        h(KPICard, { icon: '📋', label: 'Total', value: total, color: '#1677ff' }),
        h(KPICard, { icon: '✅', label: 'Completadas', value: completadas, color: '#52c41a' }),
        h(KPICard, { icon: '⚠️', label: 'Con Novedad', value: novedad, color: '#faad14' }),
        h(KPICard, { icon: '🕐', label: 'Por Aprobar', value: porAprobar, color: '#fa8c16' }),
        h(KPICard, { icon: '✔️', label: 'Aprobadas', value: aprobadas, color: '#52c41a' }),
        h(KPICard, { icon: '✗', label: 'Rechazadas', value: rechazadas, color: '#ff4d4f' })
      ),
      h(Alert, { msg: d.success, type: 'success' }),
      h('div', { className: 'ge-card' },
        h(Tabs, { items: [{ key: 'pendientes', label: 'Mis Pendientes (' + porAprobar + ')' }, { key: 'historial', label: 'Historial (' + total + ')' }, { key: 'aprobar', label: 'Por Aprobar (' + porAprobar + ')' }, { key: 'rechazadas', label: 'Rechazadas (' + rechazadas + ')' }], active: d.tab, onChange: function (k) { upd({ tab: k }); } }),
        h('div', { className: 'ge-toolbar' },
          h('div', { className: 'ge-toolbar-right' }, h('button', { className: 'ge-btn ge-btn-primary', onClick: openNew }, '+ Nueva Ejecución'))
        ),
        d.loading ? h(Spinner, null) :
        itemsTab.length === 0 ? h(Empty, { icon: '⚡', text: 'No hay ejecuciones en esta vista' }) :
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null, h('th', null, 'Actividad'), h('th', null, 'Categoría'), h('th', null, 'Ejecutor'), h('th', null, 'Fecha'), h('th', null, 'Ciclo'), h('th', null, 'Estado'), h('th', null, 'Aprobación'), h('th', null, 'Acciones'))),
            h('tbody', null, itemsTab.map(function (item) {
              return h('tr', { key: item.Id },
                h('td', null, item.ActividadNombre || item.Title),
                h('td', null, item.CategoriaNombre || '—'),
                h('td', null, item.EjecutorNombre || '—'),
                h('td', null, fmtDate(item.FechaEjecucion)),
                h('td', null, 'Ciclo ' + (item.NumeroCiclo || 1)),
                h('td', null, h(Badge, { text: item.Estado })),
                h('td', null, h(Badge, { text: item.EstadoAprobacion })),
                h('td', null,
                  (isAdmin(cu) && item.EstadoAprobacion === 'Pendiente') ? h('button', { className: 'ge-btn-link', style: { color: '#52c41a' }, onClick: function () { aprobar(item); } }, '✔ Aprobar') : null,
                  (isAdmin(cu) && item.EstadoAprobacion === 'Pendiente') ? h('button', { className: 'ge-btn-link', style: { color: '#ff4d4f' }, onClick: function () { rechazar(item); } }, '✗ Rechazar') : null,
                  canEditOwn(cu, item.EjecutorNombre) && h('button', { className: 'ge-btn-link', onClick: function () { openEdit(item); } }, '✏️'),
                  canEditOwn(cu, item.EjecutorNombre) && h('button', { className: 'ge-btn-link', style: { color: '#ff4d4f' }, onClick: function () { del(item); } }, '🗑️')
                )
              );
            }))
          )
        )
      ),
      h(Modal, { open: d.modal, title: d.editing ? 'Editar Ejecución' : 'Nueva Ejecución', onClose: function () { upd({ modal: false }); },
        footer: h('div', { style: { display: 'flex', gap: 8 } },
          h('button', { className: 'ge-btn ge-btn-default', onClick: function () { upd({ modal: false }); } }, 'Cancelar'),
          h('button', { className: 'ge-btn ge-btn-primary', onClick: save }, d.editing ? 'Guardar' : 'Registrar')
        )
      },
        h(Alert, { msg: d.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Actividad', required: true }, h('input', { className: 'ge-input', value: f.ActividadNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { ActividadNombre: e.target.value }); }); } })),
          h(FG, { label: 'Categoría' }, h('input', { className: 'ge-input', value: f.CategoriaNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { CategoriaNombre: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Ejecutor', required: true }, h('input', { className: 'ge-input', value: f.EjecutorNombre, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { EjecutorNombre: e.target.value }); }); } })),
          h(FG, { label: 'Fecha de Ejecución' }, h('input', { className: 'ge-input', type: 'date', value: f.FechaEjecucion, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { FechaEjecucion: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Ciclo' },
            h('select', { className: 'ge-select', value: f.NumeroCiclo, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { NumeroCiclo: parseInt(e.target.value) }); }); } },
              [1, 2, 3, 4].map(function (n) { return h('option', { key: n, value: n }, 'Ciclo ' + n); })
            )
          ),
          h(FG, { label: 'Estado' },
            h('select', { className: 'ge-select', value: f.Estado, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Estado: e.target.value }); }); } },
              ['Completado','Pendiente','Con Novedad','Cancelado'].map(function (s) { return h('option', { key: s, value: s }, s); })
            )
          )
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'Observaciones' }, h('textarea', { className: 'ge-textarea', value: f.Observacion, onChange: function (e) { setF(function (p) { return Object.assign({}, p, { Observacion: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'URL de Evidencias' }, h('input', { className: 'ge-input', value: f.UrlEvidencias, placeholder: 'https://...', onChange: function (e) { setF(function (p) { return Object.assign({}, p, { UrlEvidencias: e.target.value }); }); } }))
        )
      )
    );
  }

  // ─── PLANIFICACION PAGE ──────────────────────────────────────────────────
  function PlanificacionPage(props) {
    var cu = props.cu;
    var _a = R.useState({ items: [], loading: true, error: null, mes: new Date().getMonth() + 1, anio: new Date().getFullYear(), showModal: false, editing: null }), d = _a[0], set = _a[1];
    var upd = function(p) { set(function(s) { return Object.assign({}, s, p); }); };

    var MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

    function load() {
      upd({ loading: true, error: null });
      getItems('SSI_PlanesMonsuales', {
        select: 'Id,Title,UsuarioNombre,Mes,Anio,Estado,TotalPlaneado,TotalEjecutado,PorcentajeCumplimiento',
        filter: 'Mes eq ' + d.mes + ' and Anio eq ' + d.anio,
        orderby: 'UsuarioNombre asc', top: 500
      }).then(function(r) { upd({ items: r.map(normalizePlan), loading: false }); })
        .catch(function(e) { upd({ loading: false, error: e.message }); });
    }

    R.useEffect(function() { load(); }, [d.mes, d.anio]);

    var BLANK = { TaeNombre: '', Mes: d.mes, Anio: d.anio, GrupoTrabajo: 'Jaguares', ActividadesPlaneadas: 0, ActividadesEjecutadas: 0, Estado: 'Activo' };
    var _b = R.useState(BLANK), f = _b[0], setF = _b[1];
    var _c = R.useState({ saving: false, error: null }), ds = _c[0], setDs = _c[1];

    function openNew() { setF(BLANK); upd({ showModal: true, editing: null }); }
    function openEdit(item) { setF(Object.assign({}, item)); upd({ showModal: true, editing: item.Id }); }

    function save() {
      setDs({ saving: true, error: null });
      var payload = { UsuarioNombre: f.TaeNombre, Mes: parseInt(f.Mes), Anio: parseInt(f.Anio), TotalPlaneado: parseInt(f.ActividadesPlaneadas) || 0, TotalEjecutado: parseInt(f.ActividadesEjecutadas) || 0, Estado: f.Estado };
      var op = d.editing ? updateItem('SSI_PlanesMonsuales', d.editing, payload) : createItem('SSI_PlanesMonsuales', payload);
      op.then(function() { setDs({ saving: false, error: null }); upd({ showModal: false }); load(); })
        .catch(function(e) { setDs({ saving: false, error: e.message }); });
    }

    function del(id) {
      if (!confirm('¿Eliminar plan?')) return;
      deleteItem('SSI_PlanesMonsuales', id).then(load);
    }

    var cumplProm = d.items.length ? Math.round(d.items.reduce(function(s,i) { return s + (i.CumplimientoPorcentaje || 0); }, 0) / d.items.length) : 0;
    var planeado = d.items.reduce(function(s,i) { return s + (i.ActividadesPlaneadas || 0); }, 0);
    var ejecutado = d.items.reduce(function(s,i) { return s + (i.ActividadesEjecutadas || 0); }, 0);

    return h('div', { className: 'ge-page' },
      h('div', { className: 'ge-page-header' },
        h('div', null, h('h1', { className: 'ge-page-title' }, '📅 Planificación — Planes Mensuales'),
          h('p', { className: 'ge-page-sub' }, MESES[d.mes - 1] + ' ' + d.anio)),
        h('div', { className: 'ge-flex-gap' },
          h('select', { className: 'ge-select', value: d.mes, onChange: function(e) { upd({ mes: parseInt(e.target.value) }); } },
            MESES.map(function(m, i) { return h('option', { key: i, value: i + 1 }, m); })),
          h('select', { className: 'ge-select', value: d.anio, onChange: function(e) { upd({ anio: parseInt(e.target.value) }); } },
            [2024, 2025, 2026, 2027].map(function(y) { return h('option', { key: y, value: y }, y); })),
          !isPSE(cu) && h('button', { className: 'ge-btn ge-btn-primary', onClick: openNew }, '+ Programar Plan'))
      ),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '👥', label: 'TAEs con Plan', value: d.items.length, color: '#3b82f6' }),
        h(KPICard, { icon: '📋', label: 'Actividades Planeadas', value: planeado, color: '#8b5cf6' }),
        h(KPICard, { icon: '✅', label: 'Actividades Ejecutadas', value: ejecutado, color: '#10b981' }),
        h(KPICard, { icon: '📊', label: 'Cumplimiento Promedio', value: cumplProm + '%', color: cumplProm >= 80 ? '#10b981' : cumplProm >= 50 ? '#f59e0b' : '#ef4444' })
      ),
      d.loading ? h(Spinner) : d.error ? h('div', { className: 'ge-error' }, d.error) :
      d.items.length === 0 ? h(Empty, { msg: 'No hay planes para ' + MESES[d.mes - 1] + ' ' + d.anio }) :
      h('div', { className: 'ge-table-wrap' },
        h('table', { className: 'ge-table' },
          h('thead', null, h('tr', null,
            ['Personal','Período','Estado','Planeado','Ejecutado','Cumplimiento','Acciones'].map(function(c) { return h('th', { key: c }, c); })
          )),
          h('tbody', null, d.items.map(function(item) {
            var pct = item.CumplimientoPorcentaje || (item.ActividadesPlaneadas ? Math.round((item.ActividadesEjecutadas / item.ActividadesPlaneadas) * 100) : 0);
            return h('tr', { key: item.Id },
              h('td', null, h('div', null, h('strong', null, item.TaeNombre || '—'), h('br'), h('small', { style: { color: '#6b7280' } }, item.GrupoTrabajo || ''))),
              h('td', null, MESES[(item.Mes || d.mes) - 1] + ' ' + (item.Anio || d.anio)),
              h('td', null, h(Badge, { text: item.Estado || 'Activo', color: item.Estado === 'Cerrado' ? '#6b7280' : '#10b981' })),
              h('td', null, item.ActividadesPlaneadas || 0),
              h('td', null, item.ActividadesEjecutadas || 0),
              h('td', null,
                h('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                  h('div', { style: { flex: 1, background: '#e5e7eb', borderRadius: 4, height: 8 } },
                    h('div', { style: { width: Math.min(pct, 100) + '%', background: pct >= 80 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444', height: 8, borderRadius: 4 } })
                  ),
                  h('span', { style: { fontSize: 12, fontWeight: 600, minWidth: 36 } }, pct + '%')
                )
              ),
              h('td', null,
                canEditOwn(cu, item.TaeNombre) && h('button', { className: 'ge-btn ge-btn-sm ge-btn-secondary', onClick: function() { openEdit(item); }, style: { marginRight: 4 } }, '✏️'),
                isAdmin(cu) && h('button', { className: 'ge-btn ge-btn-sm ge-btn-danger', onClick: function() { del(item.Id); } }, '🗑️')
              )
            );
          }))
        )
      ),
      d.showModal && h(Modal, { open: true, title: d.editing ? 'Editar Plan' : 'Nuevo Plan', onClose: function() { upd({ showModal: false }); }, onSave: save, saving: ds.saving },
        ds.error && h(Alert, { msg: ds.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'TAE / Personal', required: true }, h('input', { className: 'ge-input', value: f.TaeNombre, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { TaeNombre: e.target.value }); }); } })),
          h(FG, { label: 'Grupo de Trabajo' },
            h('select', { className: 'ge-select', value: f.GrupoTrabajo, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { GrupoTrabajo: e.target.value }); }); } },
              ['Jaguares','Valientes','Guerreros','Cardenales','Corsarios','Vikingos'].map(function(g) { return h('option', { key: g, value: g }, g); })
            )
          )
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Mes' },
            h('select', { className: 'ge-select', value: f.Mes, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Mes: parseInt(e.target.value) }); }); } },
              MESES.map(function(m, i) { return h('option', { key: i, value: i + 1 }, m); })
            )
          ),
          h(FG, { label: 'Año' },
            h('select', { className: 'ge-select', value: f.Anio, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Anio: parseInt(e.target.value) }); }); } },
              [2024, 2025, 2026, 2027].map(function(y) { return h('option', { key: y, value: y }, y); })
            )
          )
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Actividades Planeadas' }, h('input', { className: 'ge-input', type: 'number', min: 0, value: f.ActividadesPlaneadas, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { ActividadesPlaneadas: e.target.value }); }); } })),
          h(FG, { label: 'Actividades Ejecutadas' }, h('input', { className: 'ge-input', type: 'number', min: 0, value: f.ActividadesEjecutadas, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { ActividadesEjecutadas: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Estado' },
            h('select', { className: 'ge-select', value: f.Estado, onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Estado: e.target.value }); }); } },
              ['Activo','Cerrado','Borrador'].map(function(s) { return h('option', { key: s, value: s }, s); })
            )
          )
        )
      )
    );
  }

  // ─── CATALOGO PAGE ───────────────────────────────────────────────────────
  function CatalogoPage(props) {
    var cu = props.cu;
    var CATS_DEFAULT = [
      { key: 'PRIMEROS_AUXILIOS', label: 'PRIMEROS AUXILIOS', color: '#ef4444' },
      { key: 'ENTRENAMIENTO', label: 'ENTRENAMIENTO', color: '#3b82f6' },
      { key: 'PROCESOS', label: 'PROCESOS', color: '#8b5cf6' },
      { key: 'INTEGRIDAD_OPERACIONAL', label: 'INTEGRIDAD OPERACIONAL', color: '#f59e0b' },
      { key: 'ASEGURAMIENTO', label: 'ASEGURAMIENTO', color: '#10b981' },
      { key: 'SALUD_Y_SEGURIDAD', label: 'SALUD Y SEGURIDAD', color: '#06b6d4' },
      { key: 'SOPORTE_A_PRODUCCION', label: 'SOPORTE A PRODUCCION', color: '#84cc16' },
      { key: 'OPERACIONAL', label: 'OPERACIONAL', color: '#f97316' },
      { key: 'PLAN_DE_DESARROLLO', label: 'PDI', color: '#ec4899' }
    ];

    var _a = R.useState({ items: [], cats: CATS_DEFAULT, loading: true, error: null, tab: 'plantillas', showModal: false, showCatModal: false, editing: null, editingCat: null, search: '' }), d = _a[0], set = _a[1];
    var upd = function(p) { set(function(s) { return Object.assign({}, s, p); }); };

    function load() {
      upd({ loading: true, error: null });
      Promise.all([
        getItems('SSI_PlantillasActividad', { select: 'Id,Title,Codigo,Descripcion,CategoriaNombre,Activo', orderby: 'CategoriaNombre asc,Title asc', top: 500 }),
        getItems('SSI_Categorias', { select: 'Id,Title,Descripcion,Color,Codigo', orderby: 'Title asc', top: 200 })
          .catch(function() { return []; })
      ]).then(function(r) {
        var spCats = r[1];
        var cats = spCats && spCats.length > 0
          ? spCats.map(function(c) { return { Id: c.Id, key: c.Codigo || c.Title, label: c.Title, color: c.Color || '#6b7280' }; })
          : CATS_DEFAULT;
        upd({ items: r[0].map(normalizeActividad), cats: cats, loading: false });
      }).catch(function(e) { upd({ loading: false, error: e.message }); });
    }

    R.useEffect(function() { load(); }, []);

    var BLANK = { Nombre: '', Codigo: '', Descripcion: '', Categoria: 'ENTRENAMIENTO', Estado: 'Activo' };
    var BLANK_CAT = { Title: '', Codigo: '', Color: '#3b82f6', Descripcion: '' };
    var _b = R.useState(BLANK), f = _b[0], setF = _b[1];
    var _bc = R.useState(BLANK_CAT), fc = _bc[0], setFc = _bc[1];
    var _c = R.useState({ saving: false, error: null }), ds = _c[0], setDs = _c[1];

    function openNew() { setF(BLANK); upd({ showModal: true, editing: null }); }
    function openEdit(item) { setF(Object.assign({}, item)); upd({ showModal: true, editing: item.Id }); }
    function openNewCat() { setFc(BLANK_CAT); setDs({ saving: false, error: null }); upd({ showCatModal: true, editingCat: null }); }
    function openEditCat(cat) { setFc({ Title: cat.label, Codigo: cat.key, Color: cat.color, Descripcion: '' }); setDs({ saving: false, error: null }); upd({ showCatModal: true, editingCat: cat.Id }); }

    function save() {
      setDs({ saving: true, error: null });
      var firstCat = d.cats[0] ? d.cats[0].key : 'ENTRENAMIENTO';
      var payload = { Title: f.Nombre || f.Title, Codigo: f.Codigo, Descripcion: f.Descripcion, CategoriaNombre: f.Categoria || firstCat, Activo: f.Estado !== 'Inactivo' };
      var op = d.editing ? updateItem('SSI_PlantillasActividad', d.editing, payload) : createItem('SSI_PlantillasActividad', payload);
      op.then(function() { setDs({ saving: false, error: null }); upd({ showModal: false }); load(); })
        .catch(function(e) { setDs({ saving: false, error: e.message }); });
    }

    function saveCat() {
      setDs({ saving: true, error: null });
      var payload = { Title: fc.Title, Codigo: fc.Codigo, Color: fc.Color, Descripcion: fc.Descripcion };
      var op = d.editingCat ? updateItem('SSI_Categorias', d.editingCat, payload) : createItem('SSI_Categorias', payload);
      op.then(function() { setDs({ saving: false, error: null }); upd({ showCatModal: false }); load(); })
        .catch(function(e) { setDs({ saving: false, error: e.message }); });
    }

    function del(id) {
      if (!confirm('¿Eliminar plantilla?')) return;
      deleteItem('SSI_PlantillasActividad', id).then(load);
    }

    function delCat(cat) {
      if (!cat.Id) { alert('Las categorías predeterminadas no se pueden eliminar.'); return; }
      if (!confirm('¿Eliminar categoría "' + cat.label + '"?')) return;
      deleteItem('SSI_Categorias', cat.Id).then(load);
    }

    var CATS = d.cats;

    var filtered = d.items.filter(function(i) {
      return !d.search || (i.Nombre || '').toLowerCase().indexOf(d.search.toLowerCase()) >= 0 || (i.Codigo || '').toLowerCase().indexOf(d.search.toLowerCase()) >= 0;
    });

    var groups = {};
    CATS.forEach(function(c) { groups[c.key] = []; });
    filtered.forEach(function(i) { var cat = i.Categoria || i.CategoriaNombre || ''; if (groups[cat]) { groups[cat].push(i); } else { if (!groups['OTROS']) groups['OTROS'] = []; groups['OTROS'].push(i); } });

    var catCount = function(key) { return d.items.filter(function(i) { return i.Categoria === key; }).length; };

    return h('div', { className: 'ge-page' },
      h('div', { className: 'ge-page-header' },
        h('div', null, h('h1', { className: 'ge-page-title' }, '📋 Catálogo de Actividades'),
          h('p', { className: 'ge-page-sub' }, d.items.length + ' plantillas · ' + CATS.length + ' categorías')),
        h('div', { className: 'ge-flex-gap' },
          !isPSE(cu) && d.tab === 'plantillas' && h('button', { className: 'ge-btn ge-btn-primary', onClick: openNew }, '+ Nueva Plantilla'),
          isAdmin(cu) && d.tab === 'categorias' && h('button', { className: 'ge-btn ge-btn-primary', onClick: openNewCat }, '+ Nueva Categoría')
        )
      ),
      h(Tabs, {
        tabs: ['plantillas','categorias'].map(function(t) { return { key: t, label: t === 'plantillas' ? ('Plantillas (' + d.items.length + ')') : ('Categorías (' + CATS.length + ')') }; }),
        active: d.tab, onChange: function(t) { upd({ tab: t }); }
      }),
      d.tab === 'plantillas' && h('div', null,
        h('div', { style: { marginBottom: 16 } },
          h('input', { className: 'ge-input', placeholder: '🔍 Buscar plantilla...', value: d.search, style: { maxWidth: 320 }, onChange: function(e) { upd({ search: e.target.value }); } })
        ),
        d.loading ? h(Spinner) : d.error ? h('div', { className: 'ge-error' }, d.error) :
        filtered.length === 0 ? h(Empty, { msg: 'No hay plantillas registradas. Agrega la primera con "+ Nueva Plantilla".' }) :
        h('div', null, CATS.map(function(cat) {
          var items = groups[cat.key] || [];
          if (items.length === 0) return null;
          return h('div', { key: cat.key, style: { marginBottom: 16 } },
            h('div', { style: { background: cat.color, color: '#fff', padding: '8px 16px', borderRadius: '8px 8px 0 0', fontWeight: 700, fontSize: 13, display: 'flex', justifyContent: 'space-between' } },
              h('span', null, cat.label),
              h('span', null, items.length + ' plantillas')
            ),
            h('div', { style: { background: '#fff', border: '1px solid #e5e7eb', borderTop: 'none', borderRadius: '0 0 8px 8px', overflow: 'hidden' } },
              items.map(function(item, idx) {
                return h('div', { key: item.Id, style: { padding: '12px 16px', borderTop: idx > 0 ? '1px solid #f3f4f6' : 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' } },
                  h('div', { style: { flex: 1 } },
                    h('div', { style: { fontWeight: 600, fontSize: 14 } }, item.Nombre || item.Title || '—'),
                    item.Codigo && h('code', { style: { fontSize: 11, color: '#6b7280', background: '#f3f4f6', padding: '1px 6px', borderRadius: 4 } }, item.Codigo),
                    item.Descripcion && h('p', { style: { margin: '4px 0 0', fontSize: 13, color: '#374151' } }, item.Descripcion)
                  ),
                  !isPSE(cu) && h('div', { style: { display: 'flex', gap: 4, flexShrink: 0, marginLeft: 12 } },
                    h('button', { className: 'ge-btn ge-btn-sm ge-btn-secondary', onClick: function() { openEdit(item); } }, '✏️'),
                    isAdmin(cu) && h('button', { className: 'ge-btn ge-btn-sm ge-btn-danger', onClick: function() { del(item.Id); } }, '🗑️')
                  )
                );
              })
            )
          );
        }))
      ),
      d.tab === 'categorias' && h('div', null,
        h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              ['Color','Código','Nombre','Actividades','Acciones'].map(function(c) { return h('th', { key: c }, c); })
            )),
            h('tbody', null, CATS.map(function(cat) {
              return h('tr', { key: cat.key },
                h('td', null, h('div', { style: { width: 16, height: 16, borderRadius: 3, background: cat.color } })),
                h('td', null, h('code', { style: { fontSize: 11 } }, cat.key)),
                h('td', null, h('strong', null, cat.label)),
                h('td', null, h(Badge, { text: catCount(cat.key), color: cat.color })),
                h('td', null,
                  isAdmin(cu) && h('div', { style: { display: 'flex', gap: 4 } },
                    cat.Id && h('button', { className: 'ge-btn ge-btn-sm ge-btn-secondary', onClick: function() { openEditCat(cat); } }, '✏️'),
                    cat.Id && h('button', { className: 'ge-btn ge-btn-sm ge-btn-danger', onClick: function() { delCat(cat); } }, '🗑️'),
                    !cat.Id && h('span', { style: { color: '#6b7280', fontSize: 12 } }, 'Predeterminada')
                  )
                )
              );
            }))
          )
        )
      ),
      d.showModal && h(Modal, { open: true, title: d.editing ? 'Editar Plantilla' : 'Nueva Plantilla', onClose: function() { upd({ showModal: false }); }, onSave: save, saving: ds.saving },
        ds.error && h(Alert, { msg: ds.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre', required: true }, h('input', { className: 'ge-input', value: f.Nombre || '', onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Nombre: e.target.value }); }); } })),
          h(FG, { label: 'Código' }, h('input', { className: 'ge-input', value: f.Codigo || '', placeholder: 'ENTRENAMIENTO-001', onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Codigo: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Categoría', required: true },
            h('select', { className: 'ge-select', value: f.Categoria || '', onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Categoria: e.target.value }); }); } },
              CATS.map(function(c) { return h('option', { key: c.key, value: c.key }, c.label); })
            )
          ),
          h(FG, { label: 'Estado' },
            h('select', { className: 'ge-select', value: f.Estado || 'Activo', onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Estado: e.target.value }); }); } },
              ['Activo','Inactivo'].map(function(s) { return h('option', { key: s, value: s }, s); })
            )
          )
        ),
        h('div', { className: 'ge-form-row full' },
          h(FG, { label: 'Descripción' }, h('textarea', { className: 'ge-textarea', value: f.Descripcion || '', onChange: function(e) { setF(function(p) { return Object.assign({}, p, { Descripcion: e.target.value }); }); } }))
        )
      ),
      d.showCatModal && h(Modal, { open: true, title: d.editingCat ? 'Editar Categoría' : 'Nueva Categoría', onClose: function() { upd({ showCatModal: false }); }, onSave: saveCat, saving: ds.saving },
        ds.error && h(Alert, { msg: ds.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre', required: true }, h('input', { className: 'ge-input', value: fc.Title || '', onChange: function(e) { setFc(function(p) { return Object.assign({}, p, { Title: e.target.value }); }); } })),
          h(FG, { label: 'Código' }, h('input', { className: 'ge-input', value: fc.Codigo || '', placeholder: 'ENTRENAMIENTO', onChange: function(e) { setFc(function(p) { return Object.assign({}, p, { Codigo: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Color' }, h('input', { type: 'color', className: 'ge-input', value: fc.Color || '#3b82f6', style: { height: 40, padding: 4, cursor: 'pointer' }, onChange: function(e) { setFc(function(p) { return Object.assign({}, p, { Color: e.target.value }); }); } })),
          h(FG, { label: 'Descripción' }, h('input', { className: 'ge-input', value: fc.Descripcion || '', onChange: function(e) { setFc(function(p) { return Object.assign({}, p, { Descripcion: e.target.value }); }); } }))
        )
      )
    );
  }

  // ─── REPORTES PAGE ───────────────────────────────────────────────────────
  function ReportesPage() {
    var MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    var _a = R.useState({ tipo: 'Cumplimiento', formato: 'Excel', mes: new Date().getMonth() + 1, anio: new Date().getFullYear(), loading: false, error: null, preview: null }), d = _a[0], set = _a[1];
    var upd = function(p) { set(function(s) { return Object.assign({}, s, p); }); };

    var TIPOS = [
      { key: 'Cumplimiento', label: 'Cumplimiento Mensual', icon: '📊', listas: 'SSI_PlanesMonsuales + SSI_Ejecuciones' },
      { key: 'Emergencias', label: 'Emergencias', icon: '🚨', listas: 'SSI_Emergencias' },
      { key: 'Equipos', label: 'Equipos EPP', icon: '🔧', listas: 'SSI_Equipos' },
      { key: 'Certificaciones', label: 'Certificaciones', icon: '🎓', listas: 'SSI_Certificaciones' },
      { key: 'Resumen', label: 'Resumen Ejecutivo', icon: '🏆', listas: 'Todas las listas' }
    ];

    function loadXLSX(cb) {
      if (window.XLSX) { cb(window.XLSX); return; }
      var s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
      s.onload = function() { cb(window.XLSX); };
      s.onerror = function() { upd({ loading: false, error: 'No se pudo cargar SheetJS. Verifica conexión a internet.' }); };
      document.head.appendChild(s);
    }

    function generate() {
      upd({ loading: true, error: null, preview: null });
      loadXLSX(function(XLSX) {
        var filter = 'Mes eq ' + d.mes + ' and Anio eq ' + d.anio;
        var promises = [];

        if (d.tipo === 'Cumplimiento') {
          promises = [
            getItems('SSI_PlanesMonsuales', { select: 'Id,UsuarioNombre,Mes,Anio,TotalPlaneado,TotalEjecutado,PorcentajeCumplimiento,Estado', filter: filter, top: 500 }).then(function(r){return r.map(normalizePlan);}),
            getItems('SSI_Ejecuciones', { select: 'Id,EjecutorNombre,ActividadNombre,CategoriaNombre,Estado,EstadoAprobacion,FechaEjecucion,NumeroCiclo', top: 500 })
          ];
        } else if (d.tipo === 'Emergencias') {
          promises = [getItems('SSI_Emergencias', { select: 'Id,CodigoEmergencia,TipoEmergenciaNombre,FechaReporte,Ubicacion,Severidad,Estado,TiempoRespuestaMinutos', top: 500 })];
        } else if (d.tipo === 'Equipos') {
          promises = [getItems('SSI_Equipos', { select: 'Id,Codigo,Title,CategoriaNombre,Ubicacion,Estado,DisponibleDia,DisponibleNoche,FechaProximoMantenimiento', top: 500 })];
        } else if (d.tipo === 'Certificaciones') {
          promises = [getItems('SSI_Certificaciones', { select: 'Id,UsuarioNombre,TipoCertificacionNombre,FechaVencimiento,Estado,DiasParaVencer,CodigoCertificacion', top: 500 })];
        } else {
          promises = [
            getItems('SSI_Emergencias', { select: 'Id,CodigoEmergencia,TipoEmergenciaNombre,FechaReporte,Estado,Severidad', top: 200 }),
            getItems('SSI_Equipos', { select: 'Id,Codigo,Title,Estado,CategoriaNombre', top: 200 }),
            getItems('SSI_Certificaciones', { select: 'Id,UsuarioNombre,TipoCertificacionNombre,Estado,DiasParaVencer', top: 200 }),
            getItems('SSI_Ejecuciones', { select: 'Id,EjecutorNombre,ActividadNombre,Estado,EstadoAprobacion', top: 200 })
          ];
        }

        Promise.all(promises).then(function(results) {
          var wb = XLSX.utils.book_new();

          if (d.tipo === 'Cumplimiento') {
            var planesWs = XLSX.utils.json_to_sheet(results[0].map(function(r) {
              return { 'TAE': r.TaeNombre, 'Grupo': r.GrupoTrabajo, 'Mes': MESES[(r.Mes || d.mes) - 1], 'Año': r.Anio || d.anio, 'Planeado': r.ActividadesPlaneadas || 0, 'Ejecutado': r.ActividadesEjecutadas || 0, 'Cumplimiento %': r.CumplimientoPorcentaje || 0, 'Estado': r.Estado };
            }));
            var ejecWs = XLSX.utils.json_to_sheet(results[1].map(function(r) {
              return { 'Ejecutor': r.EjecutorNombre, 'Actividad': r.ActividadNombre, 'Categoría': r.CategoriaNombre, 'Estado': r.Estado, 'Aprobación': r.EstadoAprobacion, 'Fecha': r.FechaEjecucion ? fmtDate(r.FechaEjecucion) : '', 'Ciclo': r.NumeroCiclo };
            }));
            XLSX.utils.book_append_sheet(wb, planesWs, 'Planes');
            XLSX.utils.book_append_sheet(wb, ejecWs, 'Ejecuciones');
          } else if (d.tipo === 'Emergencias') {
            var ws = XLSX.utils.json_to_sheet(results[0].map(function(r) {
              return { 'Código': r.CodigoEmergencia, 'Tipo': r.TipoEmergenciaNombre, 'Fecha': r.FechaReporte ? fmtDate(r.FechaReporte) : '', 'Ubicación': r.Ubicacion, 'Severidad': r.Severidad, 'Estado': r.Estado, 'T. Respuesta (min)': r.TiempoRespuestaMinutos || 0 };
            }));
            XLSX.utils.book_append_sheet(wb, ws, 'Emergencias');
          } else if (d.tipo === 'Equipos') {
            var ws = XLSX.utils.json_to_sheet(results[0].map(function(r) {
              return { 'Código': r.Codigo, 'Nombre': r.Title, 'Categoría': r.CategoriaNombre, 'Ubicación': r.Ubicacion, 'Estado': r.Estado, 'Turno Día': r.DisponibleDia ? 'Sí' : 'No', 'Turno Noche': r.DisponibleNoche ? 'Sí' : 'No', 'Próx. Mantto': r.FechaProximoMantenimiento ? fmtDate(r.FechaProximoMantenimiento) : '' };
            }));
            XLSX.utils.book_append_sheet(wb, ws, 'Equipos');
          } else if (d.tipo === 'Certificaciones') {
            var ws = XLSX.utils.json_to_sheet(results[0].map(function(r) {
              return { 'Certificación': r.CodigoCertificacion || r.TipoCertificacionNombre, 'TAE': r.UsuarioNombre, 'Tipo': r.TipoCertificacionNombre, 'Vencimiento': r.FechaVencimiento ? fmtDate(r.FechaVencimiento) : '', 'Estado': r.Estado, 'Días Restantes': r.DiasParaVencer || 0 };
            }));
            XLSX.utils.book_append_sheet(wb, ws, 'Certificaciones');
          } else {
            ['Emergencias','Equipos','Certificaciones','Ejecuciones'].forEach(function(name, i) {
              if (results[i] && results[i].length) {
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(results[i]), name);
              }
            });
          }

          var fname = 'GAE_' + d.tipo + '_' + MESES[d.mes - 1] + d.anio + '.xlsx';
          XLSX.writeFile(wb, fname);
          upd({ loading: false, preview: { tipo: d.tipo, rows: results[0] ? results[0].length : 0, mes: MESES[d.mes - 1], anio: d.anio } });
        }).catch(function(e) { upd({ loading: false, error: e.message }); });
      });
    }

    var selTipo = TIPOS.find(function(t) { return t.key === d.tipo; }) || TIPOS[0];

    return h('div', { className: 'ge-page' },
      h('div', { className: 'ge-page-header' },
        h('div', null, h('h1', { className: 'ge-page-title' }, '📈 Reportes y Exportación'),
          h('p', { className: 'ge-page-sub' }, 'Genera reportes Excel desde las listas de SharePoint'))
      ),
      h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 16, marginBottom: 24 } },
        TIPOS.map(function(t) {
          return h('div', { key: t.key, onClick: function() { upd({ tipo: t.key }); }, style: { padding: 16, background: '#fff', border: d.tipo === t.key ? '2px solid #3b82f6' : '1px solid #e5e7eb', borderRadius: 8, cursor: 'pointer', boxShadow: d.tipo === t.key ? '0 0 0 3px rgba(59,130,246,0.1)' : 'none' } },
            h('div', { style: { fontSize: 28, marginBottom: 8 } }, t.icon),
            h('div', { style: { fontWeight: 700, fontSize: 15 } }, t.label),
            h('div', { style: { fontSize: 12, color: '#6b7280', marginTop: 4 } }, t.listas)
          );
        })
      ),
      h('div', { style: { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24 } },
        h('h3', { style: { marginTop: 0, marginBottom: 16 } }, selTipo.icon + ' ' + selTipo.label),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Mes' },
            h('select', { className: 'ge-select', value: d.mes, onChange: function(e) { upd({ mes: parseInt(e.target.value) }); } },
              MESES.map(function(m, i) { return h('option', { key: i, value: i + 1 }, m); }))
          ),
          h(FG, { label: 'Año' },
            h('select', { className: 'ge-select', value: d.anio, onChange: function(e) { upd({ anio: parseInt(e.target.value) }); } },
              [2024, 2025, 2026, 2027].map(function(y) { return h('option', { key: y, value: y }, y); }))
          )
        ),
        d.error && h(Alert, { msg: d.error, type: 'error' }),
        d.preview && h(Alert, { msg: '✅ Reporte generado: ' + d.preview.tipo + ' ' + d.preview.mes + ' ' + d.preview.anio + ' (' + d.preview.rows + ' registros). El archivo se descargó automáticamente.', type: 'success' }),
        h('button', { className: 'ge-btn ge-btn-primary', onClick: generate, disabled: d.loading, style: { marginTop: 8 } },
          d.loading ? '⏳ Generando...' : '📥 Generar y Descargar Excel'
        )
      )
    );
  }

  // ─── DESEMPENO PAGE ──────────────────────────────────────────────────────
  function DesempenoPage() {
    var MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    var _a = R.useState({ items: [], planes: [], loading: true, error: null, tab: 'ranking', mes: new Date().getMonth() + 1, anio: new Date().getFullYear() }), d = _a[0], set = _a[1];
    var upd = function(p) { set(function(s) { return Object.assign({}, s, p); }); };

    function load() {
      upd({ loading: true, error: null });
      Promise.all([
        getItems('SSI_Ejecuciones', { select: 'Id,EjecutorNombre,Estado,EstadoAprobacion,NumeroCiclo', top: 1000 }),
        getItems('SSI_PlanesMonsuales', { select: 'Id,UsuarioNombre,Mes,Anio,TotalPlaneado,TotalEjecutado,PorcentajeCumplimiento', filter: 'Mes eq ' + d.mes + ' and Anio eq ' + d.anio, top: 100 }).then(function(r){return r.map(normalizePlan);})
      ]).then(function(r) { upd({ items: r[0], planes: r[1], loading: false }); })
        .catch(function(e) { upd({ loading: false, error: e.message }); });
    }

    R.useEffect(function() { load(); }, [d.mes, d.anio]);

    // Build ranking from planes
    var TAES = ['Armando Plata', 'Carlos Fonseca', 'Yohana Barrantes', 'Guillermo Castañeda'];
    var ranking = TAES.map(function(nombre) {
      var plan = d.planes.find(function(p) { return p.TaeNombre === nombre; }) || {};
      var misEjec = d.items.filter(function(e) { return e.EjecutorNombre === nombre; });
      var aprobadas = misEjec.filter(function(e) { return e.EstadoAprobacion === 'Aprobado'; }).length;
      var pendientes = misEjec.filter(function(e) { return e.EstadoAprobacion === 'Pendiente' || !e.EstadoAprobacion; }).length;
      var rechazadas = misEjec.filter(function(e) { return e.EstadoAprobacion === 'Rechazado'; }).length;
      var planeado = plan.ActividadesPlaneadas || 0;
      var ejecutado = plan.ActividadesEjecutadas || misEjec.filter(function(e) { return e.Estado === 'Completado'; }).length;
      var pct = plan.CumplimientoPorcentaje || (planeado > 0 ? Math.round((ejecutado / planeado) * 100) : 0);
      return { nombre: nombre, grupo: plan.GrupoTrabajo || 'Jaguares', planeado: planeado, ejecutado: ejecutado, pct: pct, aprobadas: aprobadas, pendientes: pendientes, rechazadas: rechazadas };
    }).sort(function(a, b) { return b.pct - a.pct; });

    var promPct = ranking.length ? Math.round(ranking.reduce(function(s, r) { return s + r.pct; }, 0) / ranking.length) : 0;
    var sobre80 = ranking.filter(function(r) { return r.pct >= 80; }).length;
    var bajo50 = ranking.filter(function(r) { return r.pct < 50; }).length;
    var alertas = ranking.filter(function(r) { return r.pct < 50; });
    var topPerf = ranking.filter(function(r) { return r.pct >= 80; });

    return h('div', { className: 'ge-page' },
      h('div', { className: 'ge-page-header' },
        h('div', null, h('h1', { className: 'ge-page-title' }, '🏅 Desempeño TAEs'),
          h('p', { className: 'ge-page-sub' }, MESES[d.mes - 1] + ' ' + d.anio)),
        h('div', { className: 'ge-flex-gap' },
          h('select', { className: 'ge-select', value: d.mes, onChange: function(e) { upd({ mes: parseInt(e.target.value) }); } },
            MESES.map(function(m, i) { return h('option', { key: i, value: i + 1 }, m); })),
          h('select', { className: 'ge-select', value: d.anio, onChange: function(e) { upd({ anio: parseInt(e.target.value) }); } },
            [2024, 2025, 2026, 2027].map(function(y) { return h('option', { key: y, value: y }, y); }))
        )
      ),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '👥', label: 'Total TAEs', value: TAES.length, color: '#3b82f6' }),
        h(KPICard, { icon: '📊', label: 'Cumplimiento Promedio', value: promPct + '%', color: promPct >= 80 ? '#10b981' : promPct >= 50 ? '#f59e0b' : '#ef4444' }),
        h(KPICard, { icon: '✅', label: 'Cumplimiento > 80%', value: sobre80 + '/' + TAES.length, color: '#10b981' }),
        h(KPICard, { icon: '⚠️', label: 'Cumplimiento < 50%', value: bajo50, color: '#ef4444' })
      ),
      h(Tabs, {
        tabs: [
          { key: 'ranking', label: '🏆 Ranking' },
          { key: 'alertas', label: '⚠️ Alertas (' + alertas.length + ')' },
          { key: 'top', label: '🏅 Top Performers' }
        ],
        active: d.tab, onChange: function(t) { upd({ tab: t }); }
      }),
      d.loading ? h(Spinner) : d.error ? h('div', { className: 'ge-error' }, d.error) :
      h('div', null,
        d.tab === 'ranking' && h('div', { className: 'ge-table-wrap' },
          h('table', { className: 'ge-table' },
            h('thead', null, h('tr', null,
              ['#','TAE','Grupo','Plan','Cumplimiento','Aprobadas','Pendientes','Rechazadas'].map(function(c) { return h('th', { key: c }, c); })
            )),
            h('tbody', null, ranking.map(function(r, idx) {
              return h('tr', { key: r.nombre },
                h('td', null, h('strong', null, idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1))),
                h('td', null, r.nombre),
                h('td', null, r.grupo),
                h('td', null, r.ejecutado + '/' + r.planeado),
                h('td', null,
                  h('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                    h('div', { style: { flex: 1, background: '#e5e7eb', borderRadius: 4, height: 8 } },
                      h('div', { style: { width: Math.min(r.pct, 100) + '%', background: r.pct >= 80 ? '#10b981' : r.pct >= 50 ? '#f59e0b' : '#ef4444', height: 8, borderRadius: 4 } })
                    ),
                    h('span', { style: { fontSize: 12, fontWeight: 700, minWidth: 36, color: r.pct >= 80 ? '#10b981' : r.pct >= 50 ? '#f59e0b' : '#ef4444' } }, r.pct + '%')
                  )
                ),
                h('td', null, h(Badge, { text: r.aprobadas, color: '#10b981' })),
                h('td', null, h(Badge, { text: r.pendientes, color: '#f59e0b' })),
                h('td', null, h(Badge, { text: r.rechazadas, color: '#ef4444' }))
              );
            }))
          )
        ),
        d.tab === 'alertas' && h('div', null,
          alertas.length === 0 ? h(Alert, { msg: '✅ Sin alertas. Todos los TAEs superan el 50% de cumplimiento.', type: 'success' }) :
          h('div', null, alertas.map(function(r) {
            return h('div', { key: r.nombre, style: { background: '#fff', border: '1px solid #fca5a5', borderLeft: '4px solid #ef4444', borderRadius: 8, padding: 16, marginBottom: 12 } },
              h('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
                h('div', null, h('strong', { style: { fontSize: 16 } }, '⚠️ ' + r.nombre), h('div', { style: { color: '#6b7280', fontSize: 13 } }, r.grupo)),
                h('div', { style: { textAlign: 'right' } },
                  h('div', { style: { fontSize: 24, fontWeight: 700, color: '#ef4444' } }, r.pct + '%'),
                  h('div', { style: { fontSize: 12, color: '#6b7280' } }, r.ejecutado + '/' + r.planeado + ' actividades')
                )
              )
            );
          }))
        ),
        d.tab === 'top' && h('div', null,
          topPerf.length === 0 ? h(Empty, { msg: 'Ningún TAE alcanzó el 80% de cumplimiento este período.' }) :
          h('div', null, topPerf.map(function(r, idx) {
            return h('div', { key: r.nombre, style: { background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', borderRadius: 12, padding: 20, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
              h('div', null,
                h('div', { style: { fontSize: 32 } }, idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'),
                h('div', { style: { fontSize: 18, fontWeight: 700, marginTop: 4 } }, r.nombre),
                h('div', { style: { opacity: 0.8, fontSize: 13 } }, r.grupo)
              ),
              h('div', { style: { textAlign: 'right' } },
                h('div', { style: { fontSize: 36, fontWeight: 800 } }, r.pct + '%'),
                h('div', { style: { opacity: 0.8, fontSize: 13 } }, r.ejecutado + '/' + r.planeado + ' completadas')
              )
            );
          }))
        )
      )
    );
  }

  // ─── ADMIN PAGE ──────────────────────────────────────────────────────────
  function AdminPage(props) {
    var cu = props.cu;
    var _a = R.useState({ usuarios: [], grupos: [], loading: true, error: null, tab: 'usuarios', showModal: false, showGrupoModal: false, editing: null, editingGrupo: null }), d = _a[0], set = _a[1];
    var upd = function(p) { set(function(s) { return Object.assign({}, s, p); }); };

    var BLANK_U = { Title: '', Email: '', Rol: 'TAE', GrupoTrabajoNombre: 'Jaguares', Activo: true };
    var BLANK_G = { Title: '', Codigo: '', Color: '#3b82f6', CoordinadorNombre: '' };
    var _b = R.useState(BLANK_U), fu = _b[0], setFu = _b[1];
    var _c = R.useState(BLANK_G), fg = _c[0], setFg = _c[1];
    var _ds = R.useState({ saving: false, error: null }), ds = _ds[0], setDs = _ds[1];

    function load() {
      upd({ loading: true, error: null });
      Promise.all([
        getItems('SSI_Usuarios', { select: 'Id,Title,Email,Rol,GrupoTrabajoNombre,Activo', orderby: 'Rol asc,Title asc', top: 200 }),
        getItems('SSI_GruposTrabajo', { select: 'Id,Title,Codigo,Color,CoordinadorNombre', orderby: 'Title asc', top: 100 })
      ]).then(function(r) { upd({ usuarios: r[0], grupos: r[1], loading: false }); })
        .catch(function(e) { upd({ loading: false, error: e.message }); });
    }

    R.useEffect(function() { load(); }, []);

    function openNewU() { setFu(BLANK_U); setDs({ saving: false, error: null }); upd({ showModal: true, editing: null }); }
    function openEditU(item) { setFu(Object.assign({}, item)); setDs({ saving: false, error: null }); upd({ showModal: true, editing: item.Id }); }
    function openNewG() { setFg(BLANK_G); setDs({ saving: false, error: null }); upd({ showGrupoModal: true, editingGrupo: null }); }
    function openEditG(item) { setFg(Object.assign({}, item)); setDs({ saving: false, error: null }); upd({ showGrupoModal: true, editingGrupo: item.Id }); }

    function saveUser() {
      setDs({ saving: true, error: null });
      var payload = { Title: fu.Title, Email: fu.Email, Rol: fu.Rol, GrupoTrabajoNombre: fu.GrupoTrabajoNombre, Activo: fu.Activo };
      var op = d.editing ? updateItem('SSI_Usuarios', d.editing, payload) : createItem('SSI_Usuarios', payload);
      op.then(function() { setDs({ saving: false, error: null }); upd({ showModal: false }); load(); })
        .catch(function(e) { setDs({ saving: false, error: e.message }); });
    }

    function saveGrupo() {
      setDs({ saving: true, error: null });
      var payload = { Title: fg.Title, Codigo: fg.Codigo, Color: fg.Color, CoordinadorNombre: fg.CoordinadorNombre };
      var op = d.editingGrupo ? updateItem('SSI_GruposTrabajo', d.editingGrupo, payload) : createItem('SSI_GruposTrabajo', payload);
      op.then(function() { setDs({ saving: false, error: null }); upd({ showGrupoModal: false }); load(); })
        .catch(function(e) { setDs({ saving: false, error: e.message }); });
    }

    function delUser(id) {
      if (!confirm('¿Eliminar usuario?')) return;
      deleteItem('SSI_Usuarios', id).then(load);
    }

    function delGrupo(id) {
      if (!confirm('¿Eliminar grupo?')) return;
      deleteItem('SSI_GruposTrabajo', id).then(load);
    }

    var rolColor = function(r) { return r === 'Administrador' ? '#8b5cf6' : r === 'PSE' ? '#3b82f6' : '#10b981'; };
    var taeCount = d.usuarios.filter(function(u) { return u.Rol === 'TAE'; }).length;
    var pseCount = d.usuarios.filter(function(u) { return u.Rol === 'PSE'; }).length;

    return h('div', { className: 'ge-page' },
      h('div', { className: 'ge-page-header' },
        h('div', null,
          h('h1', { className: 'ge-page-title' }, '⚙️ Administración'),
          !isAdmin(cu) && h('p', { className: 'ge-page-sub' }, '👁️ Solo lectura — contacta al administrador para crear o editar')
        )
      ),
      h('div', { className: 'ge-kpi-grid' },
        h(KPICard, { icon: '👥', label: 'Total Usuarios', value: d.usuarios.length, color: '#3b82f6' }),
        h(KPICard, { icon: '🟢', label: 'TAEs', value: taeCount, color: '#10b981' }),
        h(KPICard, { icon: '🔵', label: 'PSEs', value: pseCount, color: '#3b82f6' }),
        h(KPICard, { icon: '🏷️', label: 'Grupos de Trabajo', value: d.grupos.length, color: '#8b5cf6' })
      ),
      h(Tabs, {
        tabs: [
          { key: 'usuarios', label: '👤 Usuarios (' + d.usuarios.length + ')' },
          { key: 'grupos', label: '🏷️ Grupos (' + d.grupos.length + ')' }
        ],
        active: d.tab, onChange: function(t) { upd({ tab: t }); }
      }),
      d.loading ? h(Spinner) : d.error ? h('div', { className: 'ge-error' }, d.error) :
      h('div', null,
        d.tab === 'usuarios' && h('div', null,
          isAdmin(cu) && h('div', { style: { display: 'flex', justifyContent: 'flex-end', marginBottom: 12 } },
            h('button', { className: 'ge-btn ge-btn-primary', onClick: openNewU }, '+ Nuevo Usuario')
          ),
          h('div', { className: 'ge-table-wrap' },
            h('table', { className: 'ge-table' },
              h('thead', null, h('tr', null,
                ['Usuario','Email','Rol','Grupo','Estado','Acciones'].map(function(c) { return h('th', { key: c }, c); })
              )),
              h('tbody', null, d.usuarios.map(function(u) {
                return h('tr', { key: u.Id },
                  h('td', null, h('strong', null, u.Title || '—')),
                  h('td', null, h('span', { style: { fontSize: 13, color: '#6b7280' } }, u.Email || '—')),
                  h('td', null, h(Badge, { text: u.Rol || '—', color: rolColor(u.Rol) })),
                  h('td', null, u.GrupoTrabajoNombre || 'Sin grupo'),
                  h('td', null, h(Badge, { text: u.Activo !== false ? 'Activo' : 'Inactivo', color: u.Activo !== false ? '#10b981' : '#6b7280' })),
                  h('td', null,
                    isAdmin(cu) && h('button', { className: 'ge-btn ge-btn-sm ge-btn-secondary', onClick: function() { openEditU(u); }, style: { marginRight: 4 } }, '✏️'),
                    isAdmin(cu) && h('button', { className: 'ge-btn ge-btn-sm ge-btn-danger', onClick: function() { delUser(u.Id); } }, '🗑️')
                  )
                );
              }))
            )
          )
        ),
        d.tab === 'grupos' && h('div', null,
          isAdmin(cu) && h('div', { style: { display: 'flex', justifyContent: 'flex-end', marginBottom: 12 } },
            h('button', { className: 'ge-btn ge-btn-primary', onClick: openNewG }, '+ Nuevo Grupo')
          ),
          h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 12 } },
            d.grupos.map(function(g) {
              return h('div', { key: g.Id, style: { background: '#fff', border: '1px solid #e5e7eb', borderTop: '4px solid ' + (g.Color || '#3b82f6'), borderRadius: 8, padding: 16 } },
                h('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' } },
                  h('div', null,
                    h('div', { style: { fontWeight: 700, fontSize: 16 } }, g.Title || '—'),
                    h('div', { style: { color: '#6b7280', fontSize: 12, marginTop: 2 } }, g.Codigo || ''),
                    g.CoordinadorNombre && h('div', { style: { fontSize: 13, marginTop: 8, color: '#374151' } }, '👤 ' + g.CoordinadorNombre)
                  ),
                  isAdmin(cu) && h('div', { style: { display: 'flex', gap: 4 } },
                    h('button', { className: 'ge-btn ge-btn-sm ge-btn-secondary', onClick: function() { openEditG(g); } }, '✏️'),
                    h('button', { className: 'ge-btn ge-btn-sm ge-btn-danger', onClick: function() { delGrupo(g.Id); } }, '🗑️')
                  )
                ),
                h('div', { style: { marginTop: 8, fontSize: 13, color: '#6b7280' } },
                  d.usuarios.filter(function(u) { return u.GrupoTrabajoNombre === g.Title; }).length + ' miembros'
                )
              );
            })
          )
        )
      ),
      d.showModal && h(Modal, { open: true, title: d.editing ? 'Editar Usuario' : 'Nuevo Usuario', onClose: function() { upd({ showModal: false }); }, onSave: saveUser, saving: ds.saving },
        ds.error && h(Alert, { msg: ds.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre completo', required: true }, h('input', { className: 'ge-input', value: fu.Title, onChange: function(e) { setFu(function(p) { return Object.assign({}, p, { Title: e.target.value }); }); } })),
          h(FG, { label: 'Email' }, h('input', { className: 'ge-input', type: 'email', value: fu.Email, onChange: function(e) { setFu(function(p) { return Object.assign({}, p, { Email: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Rol' },
            h('select', { className: 'ge-select', value: fu.Rol, onChange: function(e) { setFu(function(p) { return Object.assign({}, p, { Rol: e.target.value }); }); } },
              ['TAE','PSE','Administrador'].map(function(r) { return h('option', { key: r, value: r }, r); })
            )
          ),
          h(FG, { label: 'Grupo de Trabajo' },
            h('select', { className: 'ge-select', value: fu.GrupoTrabajoNombre, onChange: function(e) { setFu(function(p) { return Object.assign({}, p, { GrupoTrabajoNombre: e.target.value }); }); } },
              ['Jaguares','Valientes','Guerreros','Cardenales','Corsarios','Vikingos','Sin grupo'].map(function(g) { return h('option', { key: g, value: g }, g); })
            )
          )
        )
      ),
      d.showGrupoModal && h(Modal, { open: true, title: d.editingGrupo ? 'Editar Grupo' : 'Nuevo Grupo', onClose: function() { upd({ showGrupoModal: false }); }, onSave: saveGrupo, saving: ds.saving },
        ds.error && h(Alert, { msg: ds.error, type: 'error' }),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Nombre', required: true }, h('input', { className: 'ge-input', value: fg.Title, onChange: function(e) { setFg(function(p) { return Object.assign({}, p, { Title: e.target.value }); }); } })),
          h(FG, { label: 'Código' }, h('input', { className: 'ge-input', value: fg.Codigo, onChange: function(e) { setFg(function(p) { return Object.assign({}, p, { Codigo: e.target.value }); }); } }))
        ),
        h('div', { className: 'ge-form-row' },
          h(FG, { label: 'Coordinador' }, h('input', { className: 'ge-input', value: fg.CoordinadorNombre, onChange: function(e) { setFg(function(p) { return Object.assign({}, p, { CoordinadorNombre: e.target.value }); }); } })),
          h(FG, { label: 'Color' }, h('input', { className: 'ge-input', type: 'color', value: fg.Color || '#3b82f6', style: { height: 42, padding: 4 }, onChange: function(e) { setFg(function(p) { return Object.assign({}, p, { Color: e.target.value }); }); } }))
        )
      )
    );
  }

  // ─── MAIN ROUTER + NAVSIDEBAR ─────────────────────────────────────────────
  var NAV_ITEMS = [
    { key: 'dashboard',       icon: '📊', label: 'Dashboard' },
    { key: 'catalogo',        icon: '📋', label: 'Catálogo' },
    { key: 'planificacion',   icon: '📅', label: 'Planificación' },
    { key: 'ejecucion',       icon: '⚡', label: 'Ejecución' },
    { key: 'emergencias',     icon: '🚨', label: 'Emergencias' },
    { key: 'equipos',         icon: '🔧', label: 'Equipos' },
    { key: 'certificaciones', icon: '🎓', label: 'Certificaciones' },
    { key: 'reportes',        icon: '📈', label: 'Reportes' },
    { key: 'desempeno',       icon: '🏅', label: 'Desempeño' },
    { key: 'administracion',  icon: '⚙️', label: 'Administración' }
  ];

  function NavSidebar(props) {
    var active = props.active, onChange = props.onChange, collapsed = props.collapsed, onToggle = props.onToggle, cu = props.cu;
    // Todos los usuarios ven todos los módulos (CRUD gateado dentro de cada página)
    var visibleItems = NAV_ITEMS;
    return h('nav', { style: { position: 'fixed', top: 0, left: 0, height: '100vh', width: collapsed ? 56 : 220, background: 'linear-gradient(180deg,#1e293b 0%,#0f172a 100%)', color: '#fff', zIndex: 100000, transition: 'width 0.2s', display: 'flex', flexDirection: 'column', boxShadow: '2px 0 12px rgba(0,0,0,0.3)' } },
      h('div', { style: { padding: collapsed ? '16px 8px' : '16px 12px', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between' } },
        !collapsed && h('div', null,
          h('div', { style: { fontWeight: 800, fontSize: 14, letterSpacing: 1 } }, '🛡️ GAE'),
          h('div', { style: { fontSize: 10, opacity: 0.6, marginTop: 2 } }, 'Gestión SSI')
        ),
        h('button', { onClick: onToggle, style: { background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: 18, padding: 4, lineHeight: 1 } }, collapsed ? '▶' : '◀')
      ),
      h('div', { style: { flex: 1, overflowY: 'auto', padding: '8px 0' } },
        visibleItems.map(function(item) {
          var isActive = active === item.key;
          return h('button', {
            key: item.key,
            onClick: function() { onChange(item.key); },
            style: {
              display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: collapsed ? '12px 0' : '10px 16px',
              background: isActive ? 'rgba(59,130,246,0.3)' : 'transparent',
              border: 'none', borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
              color: isActive ? '#93c5fd' : '#94a3b8', cursor: 'pointer', fontSize: 13, fontWeight: isActive ? 700 : 400,
              transition: 'all 0.15s', textAlign: 'left', justifyContent: collapsed ? 'center' : 'flex-start'
            }
          },
            h('span', { style: { fontSize: 16, flexShrink: 0 } }, item.icon),
            !collapsed && h('span', null, item.label)
          );
        })
      ),
      h('div', { style: { padding: '12px', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: 10, color: 'rgba(255,255,255,0.3)', textAlign: 'center' } },
        collapsed ? 'v4' : 'GAE v4.0 · SSI'
      )
    );
  }

  function GestionApp() {
    var getHash = function() { return (window.location.hash || '#dashboard').replace('#','') || 'dashboard'; };
    var _a = R.useState(getHash()), page = _a[0], setPage = _a[1];
    var _b = R.useState(window.innerWidth < 768), collapsed = _b[0], setCollapsed = _b[1];
    var _c = R.useState(null), cu = _c[0], setCu = _c[1];

    R.useEffect(function() {
      var onHash = function() { setPage(getHash()); };
      window.addEventListener('hashchange', onHash);
      loadCurrentUser().then(function(user) { setCu(user); });
      // Colapsar sidebar automáticamente al reducir ventana
      var onResize = function() { if (window.innerWidth < 768) { setCollapsed(true); } };
      window.addEventListener('resize', onResize);
      return function() {
        window.removeEventListener('hashchange', onHash);
        window.removeEventListener('resize', onResize);
      };
    }, []);

    function nav(key) {
      window.location.hash = '#' + key;
      setPage(key);
    }

    var sideW = collapsed ? 56 : 220;

    var pageMap = {
      'dashboard':       DashboardPage,
      'catalogo':        CatalogoPage,
      'planificacion':   PlanificacionPage,
      'ejecucion':       EjecucionPage,
      'emergencias':     EmergenciasPage,
      'equipos':         EquiposPage,
      'certificaciones': CertificacionesPage,
      'reportes':        ReportesPage,
      'desempeno':       DesempenoPage,
      'administracion':  AdminPage
    };

    var safePage = page;

    var PageComponent = pageMap[safePage] || DashboardPage;

    return h('div', { id: 'ge-app-root', style: { position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: '#f1f5f9', zIndex: 99999, display: 'flex', fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif' } },
      h(NavSidebar, { active: safePage, onChange: nav, collapsed: collapsed, onToggle: function() { setCollapsed(function(c) { return !c; }); }, cu: cu }),
      h('div', { style: { marginLeft: sideW, flex: 1, overflowY: 'auto', transition: 'margin-left 0.2s', padding: window.innerWidth <= 600 ? '12px' : '20px 24px', boxSizing: 'border-box' } },
        h(PageComponent, { key: safePage, cu: cu })
      )
    );
  }

  // ─── BOOTSTRAP / MOUNT ───────────────────────────────────────────────────
  function mount() {
    if (window.__GE_APP_LOADED__) {
      console.log('[GAE] App ya cargada, omitiendo re-mount');
      return;
    }
    window.__GE_APP_LOADED__ = true;

    // Inject CSS
    if (!document.getElementById('ge-styles')) {
      var style = document.createElement('style');
      style.id = 'ge-styles';
      style.textContent = CSS;
      document.head.appendChild(style);
    }

    // Find or create mount point
    var container = document.getElementById('ge-app-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ge-app-container';
      document.body.appendChild(container);
    }

    // Wait for React to be available
    var attempts = 0;
    function tryMount() {
      attempts++;
      if (!window.React || !window.ReactDOM) {
        if (attempts < 30) { setTimeout(tryMount, 300); }
        else { console.error('[GAE] React no disponible después de 9s'); }
        return;
      }
      R = window.React;
      h = R.createElement;
      useState = R.useState;
      useEffect = R.useEffect;
      useCallback = R.useCallback;
      useMemo = R.useMemo;
      useRef = R.useRef;
      try {
        if (window.ReactDOM.createRoot) {
          window.ReactDOM.createRoot(container).render(R.createElement(GestionApp));
        } else {
          window.ReactDOM.render(R.createElement(GestionApp), container);
        }
        console.log('[GAE] App montada correctamente - v4.0');
      } catch (err) {
        console.error('[GAE] Error al montar:', err);
      }
    }
    tryMount();
  }

  // Auto-mount
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    setTimeout(mount, 500);
  }

  // Expose global API
  window.GestionGAE = { mount: mount, version: '4.0', reload: function() { window.__GE_APP_LOADED__ = false; mount(); } };

  // Auto-registrar Service Worker para carga automática en futuras visitas
  // El SW persiste en el browser — después del primer uso del bookmarklet,
  // las visitas siguientes a GestionEmergencias-Classic.aspx cargan la app solas.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register(
      '/sites/SeguridadIndustrial/SitePages/sw.js',
      { scope: '/sites/SeguridadIndustrial/SitePages/' }
    ).then(function() {
      console.log('[GAE] Service Worker registrado — carga automática activada');
    }).catch(function(e) {
      console.warn('[GAE] SW no pudo registrarse:', e.message);
    });
  }

})(); // End IIFE
