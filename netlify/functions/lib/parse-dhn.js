// Puerto 1:1 de parsear_clientes()/armar_cliente()/calcular_totales() de
// actualizar.py (Python). Usa comparación de strings ISO (YYYY-MM-DD) en vez
// de objetos Date para evitar cualquier problema de timezone: las fechas ya
// vienen en ese formato desde el regex de movimientos, y ese formato
// ordena igual lexicográfica que cronológicamente.

function round2(n) {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

function isoAFechaCorta(iso) {
  // 'YYYY-MM-DD' -> 'DD-MM-YYYY'
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}-${m}-${y}`;
}

function moda(valores) {
  if (!valores.length) return null;
  const counts = new Map();
  for (const v of valores) counts.set(v, (counts.get(v) || 0) + 1);
  let best = null;
  let bestCount = -1;
  for (const [v, c] of counts) {
    if (c > bestCount) { best = v; bestCount = c; }
  }
  return best;
}

function armarCliente(cod, nombre, vendedor, condPago, totalGeneral, facturas, ncs, cutoffNcAlertIso) {
  const vencidas = facturas.filter((f) => f.diasVenc > 0).sort((a, b) => b.diasVenc - a.diasVenc);
  const porVencer = facturas.filter((f) => f.diasVenc === 0).sort((a, b) => (a.fechaVenc < b.fechaVenc ? -1 : a.fechaVenc > b.fechaVenc ? 1 : 0));

  for (const n of ncs) {
    n.antigua = n.fechaComp.slice(0, 10) < cutoffNcAlertIso;
  }
  const ncAlertas = ncs.filter((n) => n.antigua);

  const totalNc = round2(ncs.reduce((s, n) => s + n.importe, 0));
  const saldoVencNeto = round2(vencidas.reduce((s, f) => s + f.importe, 0) + totalNc);
  const maxDias = vencidas.length ? Math.max(...vencidas.map((f) => f.diasVenc)) : 0;

  let score = 0;
  if (saldoVencNeto > 20_000_000) score += 50;
  else if (saldoVencNeto > 10_000_000) score += 40;
  else if (saldoVencNeto > 5_000_000) score += 30;
  else if (saldoVencNeto > 2_000_000) score += 20;
  else if (saldoVencNeto > 500_000) score += 10;
  if (maxDias > 60) score += 30;
  else if (maxDias > 45) score += 20;
  else if (maxDias > 30) score += 10;
  const ncN = ncAlertas.length;
  if (ncN > 20) score += 20;
  else if (ncN > 10) score += 15;
  else if (ncN > 0) score += 5;

  const vencFechas = vencidas.map((f) => f.fechaVenc).filter((f) => f !== '0001-01-01');
  const vencidoDesde = vencFechas.length ? isoAFechaCorta(vencFechas.reduce((a, b) => (a < b ? a : b))) : null;

  return {
    cod,
    nombre,
    vendedor,
    totalGeneral: round2(totalGeneral),
    condPago,
    totalNC: totalNc,
    saldoVencidoNeto: saldoVencNeto,
    maxDiasVenc: maxDias,
    vencidoDesde,
    prioScore: score,
    vencidas,
    porVencer,
    ncAlertas,
    ncs,
  };
}

function calcularTotales(clientes, hoyIso) {
  return {
    clientes: clientes.length,
    conVencido: clientes.filter((c) => c.saldoVencidoNeto > 0).length,
    conPorVencer: clientes.filter((c) => c.porVencer.length > 0).length,
    conNcAlerta: clientes.filter((c) => c.ncAlertas.length > 0).length,
    totalVencidoNeto: round2(clientes.filter((c) => c.saldoVencidoNeto > 0).reduce((s, c) => s + c.saldoVencidoNeto, 0)),
    totalPorVencer: round2(clientes.reduce((s, c) => s + c.porVencer.reduce((s2, f) => s2 + f.importe, 0), 0)),
    totalNC: round2(clientes.reduce((s, c) => s + c.totalNC, 0)),
    fecha: hoyIso,
  };
}

const LINE_RE = /(\d{4}-\d{2}-\d{2})\s+(\S+)\s+(?:\d+\s+)?(\d+)\s+(FAC-[AB]|NCR-[AB]|NDB-[AB]|DAJ|CAJ|COB-R)\s+(\S+)\s+([A-Z0-9]+)\s+\$\s*([\-\d.,]+)\s+\$\s*([\-\d.,]+)\s+(\d*)\s+\$\s*[\-\d.,]+\s+(\d+)/g;
const COND_PAGO_RE = /\b(CON|07D|14D|21D|30D|45D|60D|90D)\b/g;

function parsearClientes(raw, hoyIso, condPagoMap = new Map()) {
  const cutoffNcAlertIso = `${hoyIso.slice(0, 7)}-01`;
  const clientBlocks = raw.split(/\n(?=\s*\d+ - )/);

  const clientes = [];
  for (const block of clientBlocks) {
    const hdr = block.match(/^\s*(\d+) - ([^\n]*)/m);
    if (!hdr) continue;
    const cod = hdr[1].trim();
    const nameLine1 = hdr[2];

    const totalM = block.match(/Total General:\s*\$\s*([\d.,\-]+)/);
    if (!totalM) continue;
    const totalGeneral = parseFloat(totalM[1].replace(/\./g, '').replace(/,/g, '.'));
    if (Number.isNaN(totalGeneral)) continue;

    let nombre = nameLine1.split(/\s{3,}/)[0].trim();
    if (!nameLine1.includes('Total General:')) {
      const contM = block.match(/Total General:[^\n]*\n([^\n]*)/);
      if (contM) {
        const cont = contM[1].split(/\s{3,}/)[0].trim();
        if (cont && !/^\d/.test(cont)) nombre = `${nombre} ${cont}`.trim();
      }
    }

    let condPago = condPagoMap.get(cod);
    if (!condPago) {
      const condPagos = [...block.matchAll(COND_PAGO_RE)].map((m) => m[1]);
      condPago = condPagos.length ? moda(condPagos) : '-';
    }

    const movs = [];
    const vendCounts = new Map();
    for (const m of block.matchAll(LINE_RE)) {
      const importe = parseFloat(m[7].replace(/\./g, '').replace(/,/g, '.'));
      if (Number.isNaN(importe)) continue;
      movs.push({
        fechaComp: m[1],
        fechaVenc: m[2],
        tipo: m[4],
        nro: m[5],
        condPago: m[6],
        importe: round2(importe),
        diasVenc: m[9] ? parseInt(m[9], 10) : 0,
      });
      const vend = m[10];
      if (vend) vendCounts.set(vend, (vendCounts.get(vend) || 0) + 1);
    }

    let vendedor = null;
    let bestCount = -1;
    for (const [v, c] of vendCounts) {
      if (c > bestCount) { vendedor = v; bestCount = c; }
    }

    const facturas = movs.filter((m) => m.tipo.startsWith('FAC'));
    const ncs = movs.filter((m) => m.tipo.startsWith('NCR') || m.tipo.startsWith('NDB'));

    clientes.push(armarCliente(cod, nombre, vendedor, condPago, totalGeneral, facturas, ncs, cutoffNcAlertIso));
  }

  const totales = calcularTotales(clientes, hoyIso);
  return { clientes, totales };
}

export { parsearClientes, armarCliente, calcularTotales, round2 };
