import json

with open('pdf_data.json', encoding='utf-8') as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False)

html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cuentas Corrientes · DHN</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --v1:#2e1065;--v2:#5b21b6;--v3:#7c3aed;--v4:#a78bfa;
  --ink:#1e1033;--soft:#6b5fa0;--line:#ede9f8;--card:#fff;
  --red:#dc2626;--amber:#d97706;--green:#16a34a;--blue:#2563eb;
  --danger-bg:#fef2f2;--warning-bg:#fffbeb;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{min-height:100vh;background:linear-gradient(135deg,var(--v1) 0%,var(--v2) 50%,var(--v3) 100%);background-attachment:fixed;font-family:'Inter',sans-serif;color:var(--ink);padding:36px 20px 60px;transition:background .25s;}
body.empresa-deli{background:linear-gradient(135deg,#064e3b 0%,#047857 50%,#10b981 100%);}
.wrap{max-width:1200px;margin:0 auto;}

/* Header */
.masthead{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:22px;flex-wrap:wrap;gap:14px;}
.eyebrow{font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.75);font-weight:600;margin-bottom:5px;}
h1{font-size:clamp(24px,3.5vw,36px);font-weight:800;color:#fff;letter-spacing:-.02em;}
.meta{font-size:12.5px;color:rgba(255,255,255,.85);text-align:right;line-height:1.7;}
.meta b{color:#fff;}

/* Stat cards */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;}
@media(max-width:800px){.stats{grid-template-columns:repeat(2,1fr);}}
.stat{background:rgba(255,255,255,.13);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:15px 16px;}
.stat .lbl{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:rgba(255,255,255,.75);font-weight:600;display:block;margin-bottom:5px;}
.stat .val{font-size:21px;font-weight:800;color:#fff;}

/* Tabs */
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;}
.tab{font-size:13px;font-weight:700;padding:9px 18px;border-radius:10px;cursor:pointer;border:2px solid rgba(255,255,255,.25);color:rgba(255,255,255,.8);background:rgba(255,255,255,.1);transition:all .15s;}
.tab:hover{border-color:rgba(255,255,255,.6);color:#fff;}
.tab.active{background:#fff;border-color:#fff;color:var(--v2);}
.tab .pill{display:inline-block;font-size:11px;background:var(--red);color:#fff;border-radius:20px;padding:1px 7px;margin-left:6px;}
.tab.active .pill{background:var(--red);}
.tab .pill.amber{background:var(--amber);}
.tabs-company .tab{font-size:14px;padding:10px 22px;}

/* Panel */
.panel{background:var(--card);border-radius:18px;box-shadow:0 20px 50px rgba(20,5,50,.3);overflow:hidden;}

/* Controls */
.controls{display:flex;gap:10px;flex-wrap:wrap;padding:16px 18px;border-bottom:1px solid var(--line);align-items:center;}
.search{flex:1;min-width:200px;display:flex;align-items:center;gap:8px;background:#f5f3fc;border:1px solid var(--line);border-radius:10px;padding:8px 12px;}
.search input{border:none;background:transparent;outline:none;width:100%;font-family:'Inter',sans-serif;font-size:13.5px;color:var(--ink);}
.chip{font-size:12px;font-weight:600;padding:7px 13px;border-radius:9px;border:1px solid var(--line);background:#f5f3fc;color:var(--soft);cursor:pointer;transition:all .15s;user-select:none;}
.chip:hover{border-color:var(--v3);color:var(--v3);}
.chip.active{background:var(--v2);border-color:var(--v2);color:#fff;}
.export-btn{background:#fff;border-color:var(--green);color:var(--green);cursor:pointer;font-weight:700;}
.export-btn:hover{background:#f0fdf4;border-color:var(--green);}
select.chip{padding:7px 10px;}

/* Grid table */
table{width:100%;border-collapse:collapse;}
thead th{position:sticky;top:0;z-index:2;background:#fff;color:var(--soft);font-size:11px;letter-spacing:.05em;text-transform:uppercase;text-align:right;padding:11px 16px;font-weight:700;cursor:pointer;white-space:nowrap;border-bottom:2px solid var(--line);}
thead th:first-child,thead th:nth-child(2){text-align:left;}
thead th .arr{opacity:.35;font-size:9px;margin-left:3px;}
thead th.sorted{color:var(--v2);}
thead th.sorted .arr{opacity:1;}
tbody tr{border-bottom:1px solid var(--line);cursor:pointer;transition:background .1s;}
tbody tr:hover{background:#faf8ff;}
tbody tr.expanded{background:#f3f0fd;}
td{padding:11px 16px;font-size:13.5px;vertical-align:middle;}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:500;}
td.cod{color:var(--soft);font-size:12.5px;}
td.cod .cod-num{font-weight:800;color:var(--ink);font-size:13.5px;}
td.cod .vendedor-tag{display:inline-block;margin-left:6px;font-size:10.5px;font-weight:700;color:var(--soft);background:#f0edfa;border-radius:5px;padding:1px 6px;vertical-align:middle;}
td.nombre{font-weight:600;}
.neg{color:var(--red);}
.pos{color:var(--green);}
.caret{display:inline-block;width:14px;color:var(--soft);transition:transform .15s;font-size:11px;}
tr.expanded .caret{transform:rotate(90deg);}
.badge{display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:6px;margin-left:7px;}
.badge.venc{background:#fee2e2;color:var(--red);}
.badge.pv{background:#fef3c7;color:var(--amber);}
.badge.nc{background:#fef9c3;color:#854d0e;}
.semaforo{display:inline-block;width:13px;height:13px;border-radius:50%;flex-shrink:0;margin-right:6px;vertical-align:middle;}
.sem-rojo{background:#dc2626;box-shadow:0 0 0 3px #fee2e2;}
.sem-amarillo{background:#d97706;box-shadow:0 0 0 3px #fef3c7;}
.sem-verde{background:#16a34a;box-shadow:0 0 0 3px #dcfce7;}
.totales-bar{display:flex;align-items:center;flex-wrap:wrap;gap:0;padding:12px 20px;border-bottom:1px solid var(--line);background:#fafaff;}
.tot-item{display:flex;align-items:center;gap:7px;padding:4px 16px 4px 0;}
.tot-item:last-child{padding-right:0;}
.tot-lbl{font-size:11.5px;color:var(--soft);font-weight:600;}
.tot-val{font-size:15px;font-weight:800;color:var(--ink);}
.tot-item.rojo .tot-val{color:var(--red);}
.tot-item.amarillo .tot-val{color:var(--amber);}
.tot-item.verde .tot-val{color:var(--green);}
.tot-item.total .tot-val{color:var(--ink);}
.tot-sep{width:1px;height:28px;background:var(--line);margin:0 12px;}
.dias-badge{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px;background:#fee2e2;color:var(--red);margin-left:6px;}

/* Expanded detail */
.detail-row td{padding:0;background:#faf8ff;}
.detail-inner{padding:16px 20px 20px 40px;display:grid;grid-template-columns:1fr 1fr;gap:20px;}
@media(max-width:700px){.detail-inner{grid-template-columns:1fr;}}
.det-col h4{font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;margin-bottom:8px;}
.det-col.venc h4{color:var(--red);}
.det-col.pv h4{color:var(--amber);}
.det-col.nc h4{color:#854d0e;}
.fac-table{width:100%;border-collapse:collapse;font-size:12px;}
.fac-table th{text-align:left;font-weight:600;color:var(--soft);padding:3px 8px 5px;border-bottom:1px solid var(--line);font-size:11px;}
.fac-table th:last-child{text-align:right;}
.fac-table td{padding:5px 8px;border-bottom:1px dashed var(--line);vertical-align:middle;}
.fac-table td:last-child{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;}
.fac-table tr:last-child td{border-bottom:none;}
.empty{font-size:12px;color:var(--soft);font-style:italic;}
.nc-item{display:flex;justify-content:space-between;font-size:12px;padding:4px 8px;border-bottom:1px dashed var(--line);color:#854d0e;}
.nc-item:last-child{border-bottom:none;}
.mini-badge{display:inline-block;font-size:9px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:1px 6px;border-radius:5px;background:#fde68a;color:#854d0e;margin-right:6px;}
.neteo-box{display:flex;flex-direction:column;gap:3px;margin-top:12px;padding:10px 12px;background:#f3f0fd;border-radius:8px;font-size:12px;font-weight:600;color:var(--soft);}
.neteo-box .neteo-total{font-size:13.5px;font-weight:800;color:var(--ink);padding-top:5px;margin-top:2px;border-top:1px dashed var(--line);}

/* NC Alert tab */
.nc-alert-section{padding:20px;}
.nc-alert-card{border:1px solid #fde68a;background:#fffbeb;border-radius:10px;margin-bottom:14px;overflow:hidden;}
.nc-alert-hdr{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;background:#fef3c7;border-bottom:1px solid #fde68a;cursor:pointer;}
.nc-alert-hdr .cliente{font-weight:700;font-size:13.5px;}
.nc-alert-hdr .nc-total{font-weight:700;color:#92400e;}
.nc-alert-body{padding:10px 16px;display:none;}
.nc-alert-body.open{display:block;}

/* Footer */
.foot{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;font-size:12.5px;color:var(--soft);border-top:1px solid var(--line);flex-wrap:wrap;gap:8px;}
.pager{display:flex;gap:6px;align-items:center;}
.pager button{font-size:12.5px;font-weight:600;border:1px solid var(--line);background:#fff;padding:5px 11px;border-radius:8px;cursor:pointer;color:var(--ink);}
.pager button:disabled{opacity:.35;cursor:default;}
.pager button:not(:disabled):hover{border-color:var(--v2);color:var(--v2);}
.source{margin-top:14px;font-size:11px;color:rgba(255,255,255,.65);text-align:center;}
::selection{background:var(--v2);color:#fff;}

/* NC alert tab panel */
#ncPanel{display:none;}
#ncPanel.visible{display:block;}
#mainPanel{display:block;}
#mainPanel.hidden{display:none;}
</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <div>
      <div class="eyebrow" id="eyebrowTxt">Reporte</div>
      <h1>Saldo Detallado por Cliente</h1>
    </div>
    <div class="meta">
      <div><b id="mCli">0</b> clientes en cartera</div>
      <div><b id="mVenc">0</b> con saldo vencido</div>
    </div>
  </div>

  <div class="tabs tabs-company" id="companyTabs"></div>

  <div class="stats">
    <div class="stat"><span class="lbl">Total Vencido (neto NC)</span><div class="val" id="sVencido"></div></div>
    <div class="stat"><span class="lbl">Total Por Vencer</span><div class="val" id="sPorVencer"></div></div>
    <div class="stat"><span class="lbl">Total NC Aplicadas</span><div class="val" id="sNC"></div></div>
    <div class="stat"><span class="lbl">NC antiguas c/ alerta</span><div class="val" id="sNcAlert"></div></div>
  </div>

  <div class="tabs">
    <div class="tab active" id="tabMain" onclick="showTab('main')">Cuentas Corrientes</div>
    <div class="tab" id="tabNC" onclick="showTab('nc')">NC Antiguas <span class="pill amber" id="ncCount">0</span></div>
  </div>

  <!-- MAIN PANEL -->
  <div class="panel" id="mainPanel">
    <div class="controls">
      <div class="search">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" id="searchInput" placeholder="Buscar cliente…">
      </div>
      <div class="chip active" data-filter="vencido">Con vencido</div>
      <div class="chip" data-filter="porvencer">Por vencer</div>
      <button class="chip export-btn" onclick="exportExcel()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:-2px;margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Exportar Excel
      </button>
      <select class="chip" id="condFilter">
        <option value="">Todas las condiciones</option>
      </select>
      <div class="chip active" data-sem="">Todos</div>
      <div class="chip" data-sem="rojo" style="display:flex;align-items:center;gap:5px;"><span class="semaforo sem-rojo"></span>Crítico</div>
      <div class="chip" data-sem="amarillo" style="display:flex;align-items:center;gap:5px;"><span class="semaforo sem-amarillo"></span>Medio</div>
      <div class="chip" data-sem="verde" style="display:flex;align-items:center;gap:5px;"><span class="semaforo sem-verde"></span>A tiempo</div>
    </div>
    <div class="totales-bar" id="totalesBar">
      <div class="tot-item rojo"><span class="semaforo sem-rojo"></span><span class="tot-lbl">Crítico</span><span class="tot-val" id="totRojo">—</span></div>
      <div class="tot-sep"></div>
      <div class="tot-item amarillo"><span class="semaforo sem-amarillo"></span><span class="tot-lbl">Medio</span><span class="tot-val" id="totAmarillo">—</span></div>
      <div class="tot-sep"></div>
      <div class="tot-item verde"><span class="semaforo sem-verde"></span><span class="tot-lbl">A tiempo (por vencer)</span><span class="tot-val" id="totVerde">—</span></div>
      <div class="tot-sep"></div>
      <div class="tot-item total"><span class="tot-lbl">Total vencido</span><span class="tot-val" id="totTotal">—</span></div>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th data-key="cod" style="width:80px;">N° <span class="arr">↕</span></th>
            <th data-key="nombre">Cliente <span class="arr">↕</span></th>
            <th data-key="condPago" style="text-align:left;">Cond. Pago <span class="arr">↕</span></th>
            <th data-key="saldoVencidoNeto">Saldo Vencido <span class="arr">↕</span></th>
            <th data-key="maxDiasVenc">Días venc. <span class="arr">↕</span></th>
            <th data-key="porVencerTotal">Por vencer <span class="arr">↕</span></th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="foot">
      <div id="footInfo"></div>
      <div class="pager" id="pager"></div>
    </div>
  </div>

  <!-- NC ALERT PANEL -->
  <div class="panel" id="ncPanel">
    <div class="nc-alert-section" id="ncBody"></div>
  </div>

  <div class="source" id="sourceLine">Clic en fila para ver detalle de facturas</div>
</div>

<script>
const DATA = __DATA_JSON__;
const EMPRESAS = Object.keys(DATA);

let currentEmpresa = EMPRESAS[0];
let currentTab = 'main';

const states = {};
EMPRESAS.forEach(k => {
  states[k] = {filter:'vencido',search:'',sortKey:'saldoVencidoNeto',sortDir:-1,page:1,pageSize:50,expanded:null,cond:'',sem:''};
});

function money(n){
  if(n===null||n===undefined) return '—';
  const neg=n<0; const s=Math.abs(n).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2});
  return (neg?'-$':'$')+s;
}
function fmt(s){ return s ? s.slice(0,10).split('-').reverse().join('-') : ''; }

function clientesActuales(){ return DATA[currentEmpresa].clientes; }
function totalesActuales(){ return DATA[currentEmpresa].totales; }
function stateActual(){ return states[currentEmpresa]; }

// Precompute por vencer total y semáforo por cliente, para todas las empresas
EMPRESAS.forEach(k => {
  DATA[k].clientes.forEach(c => {
    c.porVencerTotal = c.porVencer.reduce((s,f)=>s+f.importe,0);
    // semaforo: rojo=critico, amarillo=medio, verde=ok/a tiempo
    if(c.saldoVencidoNeto>0){
      const score=c.prioScore||0;
      if(score>=60 || c.maxDiasVenc>60) c.semaforo='rojo';
      else if(score>=20 || c.maxDiasVenc>30) c.semaforo='amarillo';
      else c.semaforo='amarillo';
    } else if(c.porVencerTotal>0){
      c.semaforo='verde';
    } else {
      c.semaforo='neutro';
    }
  });
});

// ---- COMPANY TABS ----
function renderCompanyTabs(){
  const el = document.getElementById('companyTabs');
  el.innerHTML = EMPRESAS.map(k=>`<div class="tab ${k===currentEmpresa?'active':''}" data-empresa="${k}">${DATA[k].label}</div>`).join('');
  el.querySelectorAll('.tab').forEach(t=>{
    t.addEventListener('click',()=>{
      if(t.dataset.empresa===currentEmpresa) return;
      currentEmpresa = t.dataset.empresa;
      onEmpresaChange();
    });
  });
}

function onEmpresaChange(){
  document.body.classList.toggle('empresa-deli', currentEmpresa==='deli');
  renderCompanyTabs();
  renderMasthead();
  poblarCondFilter();
  syncControlsUI();
  if(currentTab==='main') render(); else renderNC();
}

function renderMasthead(){
  const tot = totalesActuales();
  const label = DATA[currentEmpresa].label;
  document.getElementById('eyebrowTxt').textContent = `${label} · Reporte al ${fmt(tot.fecha)}`;
  document.getElementById('mCli').textContent = tot.clientes.toLocaleString('es-AR');
  document.getElementById('mVenc').textContent = tot.conVencido.toLocaleString('es-AR');
  document.getElementById('sVencido').textContent = money(tot.totalVencidoNeto);
  document.getElementById('sPorVencer').textContent = money(tot.totalPorVencer);
  document.getElementById('sNC').textContent = money(tot.totalNC);
  document.getElementById('sNcAlert').textContent = tot.conNcAlerta.toLocaleString('es-AR') + ' clientes';
  document.getElementById('ncCount').textContent = tot.conNcAlerta;
  document.getElementById('sourceLine').textContent = `${label} · Fecha reporte: ${fmt(tot.fecha)} · Clic en fila para ver detalle de facturas`;
}

function syncControlsUI(){
  const st = stateActual();
  document.querySelectorAll('.chip[data-filter]').forEach(c=>c.classList.toggle('active', c.dataset.filter===st.filter));
  document.querySelectorAll('.chip[data-sem]').forEach(c=>c.classList.toggle('active', c.dataset.sem===st.sem));
  document.getElementById('searchInput').value = st.search;
  document.getElementById('condFilter').value = st.cond;
}

// ---- TABS (Cuentas Corrientes / NC Antiguas) ----
function showTab(t){
  currentTab = t;
  document.getElementById('tabMain').classList.toggle('active',t==='main');
  document.getElementById('tabNC').classList.toggle('active',t==='nc');
  document.getElementById('mainPanel').classList.toggle('hidden',t==='nc');
  document.getElementById('ncPanel').classList.toggle('visible',t==='nc');
  if(t==='nc') renderNC(); else render();
}

// ---- NC ALERT PANEL ----
function renderNC(){
  const el = document.getElementById('ncBody');
  const con = clientesActuales().filter(c=>c.ncAlertas && c.ncAlertas.length>0).sort((a,b)=>a.ncAlertas.reduce((s,n)=>s+n.importe,0)-b.ncAlertas.reduce((s,n)=>s+n.importe,0));
  if(!con.length){el.innerHTML='<div class="empty">Sin NC antiguas.</div>';return;}
  el.innerHTML = con.map((c,i)=>{
    const tot = c.ncAlertas.reduce((s,n)=>s+n.importe,0);
    const rows = c.ncAlertas.map(n=>`<div class="nc-item"><span>${n.nro} &middot; ${fmt(n.fechaComp)}</span><span>${money(n.importe)}</span></div>`).join('');
    return `<div class="nc-alert-card">
      <div class="nc-alert-hdr" onclick="toggleNC(${i})">
        <span class="cliente">${c.cod} &mdash; ${c.nombre}</span>
        <span class="nc-total">${c.ncAlertas.length} NC &middot; ${money(tot)}</span>
      </div>
      <div class="nc-alert-body" id="nc${i}">${rows}</div>
    </div>`;
  }).join('');
}
function toggleNC(i){
  const el=document.getElementById('nc'+i);
  el.classList.toggle('open');
}

// ---- MAIN GRID ----
function applyFilters(){
  const state = stateActual();
  let list = clientesActuales();
  if(state.filter==='vencido') list=list.filter(c=>c.saldoVencidoNeto>0);
  else if(state.filter==='porvencer') list=list.filter(c=>c.porVencerTotal>0);
  if(state.cond) list=list.filter(c=>c.condPago===state.cond);
  if(state.sem) list=list.filter(c=>c.semaforo===state.sem);
  if(state.search){const q=state.search.toLowerCase();list=list.filter(c=>c.nombre.toLowerCase().includes(q)||c.cod.includes(q));}
  list=[...list].sort((a,b)=>{
    let va=a[state.sortKey],vb=b[state.sortKey];
    if(typeof va==='string'){va=va.toLowerCase();vb=vb.toLowerCase();}
    if(va<vb)return -1*state.sortDir;if(va>vb)return 1*state.sortDir;return 0;
  });
  return list;
}

const COND = {'CON':'Contado','EFV':'Efectivo','01D':'1 día','07D':'7 días','14D':'14 días','15D':'15 días','21D':'21 días','30D':'30 días','45D':'45 días','60D':'60 días','90D':'90 días'};
const COND_ORDER = ['CON','EFV','01D','07D','14D','15D','21D','30D','45D','60D','90D'];

// Solo mostrar en el filtro las condiciones de pago que realmente existen en los datos de la empresa actual
function poblarCondFilter(){
  const sel = document.getElementById('condFilter');
  sel.innerHTML = '<option value="">Todas las condiciones</option>';
  const presentes = new Set(clientesActuales().map(c=>c.condPago).filter(v=>v && v!=='-'));
  const ordenadas = COND_ORDER.filter(k=>presentes.has(k))
    .concat([...presentes].filter(k=>!COND_ORDER.includes(k)));
  ordenadas.forEach(k=>{
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = COND[k] || k;
    sel.appendChild(opt);
  });
}

function facTable(rows, tipo){
  if(!rows||!rows.length) return '<div class="empty">Sin movimientos.</div>';
  const color = tipo==='venc'?'var(--red)':tipo==='pv'?'var(--amber)':'#854d0e';
  return `<table class="fac-table">
    <thead><tr><th>Comprobante</th><th>F. Comprobante</th><th>F. Vencimiento</th><th>${tipo==='venc'?'Días venc.':''}</th><th>Importe</th></tr></thead>
    <tbody>${rows.map(f=>`<tr>
      <td>${f.nro}</td>
      <td>${fmt(f.fechaComp)}</td>
      <td>${fmt(f.fechaVenc)}</td>
      <td>${tipo==='venc'?'<span style="color:'+color+';font-weight:700;">'+f.diasVenc+' días</span>':''}</td>
      <td style="color:${f.importe<0?'var(--red)':'inherit'}">${money(f.importe)}</td>
    </tr>`).join('')}
    </tbody>
  </table>`;
}

function render(){
  const state = stateActual();
  const filtered=applyFilters();
  updateTotales(filtered);
  const totalPages=Math.max(1,Math.ceil(filtered.length/state.pageSize));
  if(state.page>totalPages)state.page=totalPages;
  const start=(state.page-1)*state.pageSize;
  const pageItems=filtered.slice(start,start+state.pageSize);
  const tbody=document.getElementById('tbody');
  tbody.innerHTML='';

  pageItems.forEach(c=>{
    const isExp=state.expanded===c.cod;
    const tr=document.createElement('tr');
    if(isExp)tr.classList.add('expanded');
    const hasBadgeVenc=c.saldoVencidoNeto>0;
    const hasBadgePV=c.porVencerTotal>0;
    const hasNC=c.ncAlertas&&c.ncAlertas.length>0;
    tr.innerHTML=`
      <td class="cod"><span class="caret">&#9658;</span><span class="cod-num">${c.cod}</span>${c.vendedor?'<span class="vendedor-tag">V'+c.vendedor+'</span>':''}</td>
      <td class="nombre">${c.nombre}${hasBadgeVenc?'<span class="badge venc">Vencido</span>':''}${hasBadgePV?'<span class="badge pv">Por vencer</span>':''}${hasNC?'<span class="badge nc">NC antigua</span>':''}</td>
      <td>${COND[c.condPago]||c.condPago}</td>
      <td><span class="semaforo ${c.semaforo==='rojo'?'sem-rojo':c.semaforo==='amarillo'?'sem-amarillo':'sem-verde'}"></span>${c.semaforo==='rojo'?'Crítico':c.semaforo==='amarillo'?'Medio':'A tiempo'}</td>
      <td class="num ${c.saldoVencidoNeto>0?'neg':c.saldoVencidoNeto<0?'pos':''}">${c.saldoVencidoNeto!==0?money(c.saldoVencidoNeto):'—'}</td>
      <td class="num">${c.maxDiasVenc>0?'<span class="dias-badge">'+c.maxDiasVenc+' días</span>':'—'}</td>
      <td class="num">${c.porVencerTotal>0?money(c.porVencerTotal):'—'}</td>
    `;
    tr.addEventListener('click',()=>{const st=stateActual();st.expanded=(st.expanded===c.cod)?null:c.cod;render();});
    tbody.appendChild(tr);

    if(isExp){
      const dtr=document.createElement('tr');
      dtr.className='detail-row';
      const ncRows=c.ncs&&c.ncs.length?c.ncs.map(n=>`<div class="nc-item"><span>${n.antigua?'<span class="mini-badge">Antigua</span>':''}${n.nro} &middot; ${fmt(n.fechaComp)}</span><span>${money(n.importe)}</span></div>`).join(''):'<div class="empty">Sin NC.</div>';
      const brutoVenc=c.vencidas.reduce((s,f)=>s+f.importe,0);
      dtr.innerHTML=`<td colspan="7"><div class="detail-inner">
        <div class="det-col venc">
          <h4>Facturas Vencidas (${c.vencidas.length})</h4>
          ${facTable(c.vencidas,'venc')}
          <div class="det-col nc" style="margin-top:14px;">
            <h4>Notas de Crédito (${c.ncs?c.ncs.length:0})</h4>
            ${ncRows}
          </div>
          <div class="neteo-box">
            <span>Bruto vencido: ${money(brutoVenc)}</span>
            <span>NC aplicadas: ${money(c.totalNC)}</span>
            <span class="neteo-total">Neto a cobrar: ${money(c.saldoVencidoNeto)}</span>
          </div>
        </div>
        <div class="det-col pv">
          <h4>Por Vencer (${c.porVencer.length})</h4>
          ${facTable(c.porVencer,'pv')}
        </div>
      </div></td>`;
      tbody.appendChild(dtr);
    }
  });

  document.getElementById('footInfo').textContent=`Mostrando ${filtered.length===0?0:start+1}–${Math.min(start+state.pageSize,filtered.length)} de ${filtered.length}`;
  const pager=document.getElementById('pager');
  pager.innerHTML=`<button id="pb" ${state.page<=1?'disabled':''}>← Anterior</button><span>Pág. ${state.page}/${totalPages}</span><button id="nb" ${state.page>=totalPages?'disabled':''}>Siguiente →</button>`;
  document.getElementById('pb').addEventListener('click',()=>{stateActual().page--;render();});
  document.getElementById('nb').addEventListener('click',()=>{stateActual().page++;render();});
  document.querySelectorAll('thead th').forEach(th=>{
    const isSorted=th.dataset.key===state.sortKey;
    th.classList.toggle('sorted',isSorted);
    const arr=th.querySelector('.arr');
    if(arr) arr.textContent=isSorted?(state.sortDir===1?'↑':'↓'):'↕';
  });
}

document.querySelectorAll('thead th').forEach(th=>{
  th.addEventListener('click',()=>{
    const state = stateActual();
    const key=th.dataset.key;
    if(state.sortKey===key){state.sortDir*=-1;}else{state.sortKey=key;state.sortDir=key==='nombre'||key==='cod'||key==='condPago'?1:-1;}
    render();
  });
});
document.querySelectorAll('.chip[data-filter]').forEach(chip=>{
  chip.addEventListener('click',()=>{
    document.querySelectorAll('.chip[data-filter]').forEach(c=>c.classList.remove('active'));
    chip.classList.add('active');
    const state = stateActual();
    state.filter=chip.dataset.filter;state.page=1;state.expanded=null;render();
  });
});
document.getElementById('condFilter').addEventListener('change',e=>{
  const state = stateActual();
  state.cond=e.target.value;state.page=1;state.expanded=null;render();
});
document.querySelectorAll('.chip[data-sem]').forEach(chip=>{
  chip.addEventListener('click',()=>{
    document.querySelectorAll('.chip[data-sem]').forEach(c=>c.classList.remove('active'));
    chip.classList.add('active');
    const state = stateActual();
    state.sem=chip.dataset.sem;state.page=1;state.expanded=null;render();
  });
});
let st;
document.getElementById('searchInput').addEventListener('input',e=>{
  clearTimeout(st);st=setTimeout(()=>{const state=stateActual();state.search=e.target.value.trim();state.page=1;state.expanded=null;render();},150);
});

function updateTotales(filtered){
  const rojo = filtered.filter(c=>c.semaforo==='rojo');
  const amarillo = filtered.filter(c=>c.semaforo==='amarillo');
  const verde = filtered.filter(c=>c.semaforo==='verde');
  document.getElementById('totRojo').textContent = money(rojo.reduce((s,c)=>s+c.saldoVencidoNeto,0));
  document.getElementById('totAmarillo').textContent = money(amarillo.reduce((s,c)=>s+c.saldoVencidoNeto,0));
  document.getElementById('totVerde').textContent = money(verde.reduce((s,c)=>s+c.porVencerTotal,0));
  const totalVenc = [...rojo,...amarillo].reduce((s,c)=>s+c.saldoVencidoNeto,0);
  document.getElementById('totTotal').textContent = money(totalVenc);
}

// ---- INIT ----
document.body.classList.toggle('empresa-deli', currentEmpresa==='deli');
renderCompanyTabs();
renderMasthead();
poblarCondFilter();
syncControlsUI();
render();

// ---- EXCEL EXPORT ----
function exportExcel(){
  const state = stateActual();
  const filtered = applyFilters();
  const COND2 = {'CON':'Contado','EFV':'Efectivo','01D':'1 día','07D':'7 días','14D':'14 días','15D':'15 días','21D':'21 días','30D':'30 días','45D':'45 días','60D':'60 días','90D':'90 días'};
  const SEM = {'rojo':'Crítico','amarillo':'Medio','verde':'A tiempo','neutro':'-'};
  const rows = filtered.map(c=>({
    'N°': c.cod,
    'Cliente': c.nombre,
    'Condición Pago': COND2[c.condPago]||c.condPago,
    'Estado': SEM[c.semaforo]||'-',
    'Saldo Vencido Neto ($)': c.saldoVencidoNeto||0,
    'Días Vencido (máx)': c.maxDiasVenc||0,
    'Vencido Desde': c.vencidoDesde||'',
    'Por Vencer ($)': c.porVencerTotal||0,
    'Vence El': c.porVencer&&c.porVencer[0]?c.porVencer[0].fecha:'',
    'NC Antiguas (cant)': c.ncAlertas?c.ncAlertas.length:0,
  }));
  const ws = XLSX.utils.json_to_sheet(rows);
  const wscols = [8,40,16,12,20,16,16,16,14,16].map(w=>({wch:w}));
  ws['!cols'] = wscols;
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Cuentas Corrientes');
  const label = DATA[currentEmpresa].label;
  const fechaReporte = totalesActuales().fecha;
  // Summary sheet
  const sumRows = [
    ['Reporte', label + ' - Cuentas Corrientes'],
    ['Fecha', fechaReporte],
    ['Filtro aplicado', state.sem ? (state.sem==='rojo'?'Crítico':state.sem==='amarillo'?'Medio':'A tiempo') : state.filter==='vencido'?'Con vencido':state.filter==='porvencer'?'Por vencer':'Todos'],
    [''],
    ['Estado','Clientes','Total ($)'],
    ['Crítico', filtered.filter(c=>c.semaforo==='rojo').length, filtered.filter(c=>c.semaforo==='rojo').reduce((s,c)=>s+c.saldoVencidoNeto,0)],
    ['Medio', filtered.filter(c=>c.semaforo==='amarillo').length, filtered.filter(c=>c.semaforo==='amarillo').reduce((s,c)=>s+c.saldoVencidoNeto,0)],
    ['A tiempo (por vencer)', filtered.filter(c=>c.semaforo==='verde').length, filtered.filter(c=>c.semaforo==='verde').reduce((s,c)=>s+c.porVencerTotal,0)],
    [''],
    ['Total vencido', '', filtered.filter(c=>c.saldoVencidoNeto>0).reduce((s,c)=>s+c.saldoVencidoNeto,0)],
  ];
  const ws2 = XLSX.utils.aoa_to_sheet(sumRows);
  ws2['!cols'] = [{wch:28},{wch:18},{wch:20}];
  XLSX.utils.book_append_sheet(wb, ws2, 'Resumen');
  XLSX.writeFile(wb, 'CuentasCorrientes_' + label.replace(/\s+/g,'') + '_' + fechaReporte + '.xlsx');
}
</script>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
</body>
</html>"""

html_out = html.replace('__DATA_JSON__', data_json)
with open('/root/proyectos/dhn/index.html','w',encoding='utf-8') as f:
    f.write(html_out)
print("bytes:", len(html_out))
