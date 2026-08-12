import * as XLSX from 'xlsx';
import { armarCliente, calcularTotales, round2 } from './parse-dhn.js';

// Puerto de parsear_deli() (actualizar.py), que lee el .xls/.xlsx "Saldos
// Detallados por Cliente y Comprobante" (formato Crystal Reports) con xlrd
// en Python. Acá se usa SheetJS (xlsx) con `cellDates: true` para que las
// celdas de fecha lleguen como Date en vez de números seriales, igual que
// xlrd.xldate_as_datetime. Los índices de columna (A=cod, B=fecha mov.,
// C=fecha venc., E=comprobante, G=importe, K=total general de la fila de
// dirección) son los mismos que usa el original.

function dateToIso(d) {
  return d.toISOString().slice(0, 10);
}

function celda(ws, r, c) {
  return ws[XLSX.utils.encode_cell({ r, c })];
}

function esHeaderCliente(ws, r) {
  const cell = celda(ws, r, 0);
  if (!cell || cell.t !== 's') return false;
  return /^[\d.]+$/.test(String(cell.v).trim());
}

function parsearDeliXls(buffer, hoyIso) {
  const cutoffNcAlertIso = `${hoyIso.slice(0, 7)}-01`;
  const wb = XLSX.read(buffer, { type: 'buffer', cellDates: true });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const range = XLSX.utils.decode_range(ws['!ref']);
  const n = range.e.r + 1;

  const clientes = [];
  let r = range.s.r;
  while (r < n) {
    if (!esHeaderCliente(ws, r)) { r++; continue; }

    const cod = String(celda(ws, r, 0).v).trim().replace(/\./g, '');
    const nombreCell = celda(ws, r, 1);
    const nombre = String(nombreCell ? nombreCell.v : '').trim().replace(/^@/, '').trim();

    let totalGeneral = null;
    const facturas = [];
    const ncs = [];
    let rr = r + 1;
    while (rr < n && !esHeaderCliente(ws, rr)) {
      const kCell = celda(ws, rr, 10);
      if (totalGeneral === null && kCell && kCell.t === 'n') {
        totalGeneral = kCell.v;
      }
      const bCell = celda(ws, rr, 1);
      if (bCell && bCell.t === 'd') {
        const fechaMov = dateToIso(bCell.v);
        const cCell = celda(ws, rr, 2);
        const fechaVenc = cCell && cCell.t === 'd' ? dateToIso(cCell.v) : fechaMov;
        const compCell = celda(ws, rr, 4);
        const comp = String(compCell ? compCell.v : '').trim();
        const gCell = celda(ws, rr, 6);
        const importe = round2(parseFloat(gCell ? gCell.v : 0));
        const tipoM = comp.match(/^([A-Za-z]+)/);
        const mov = {
          fechaComp: fechaMov,
          fechaVenc,
          tipo: tipoM ? tipoM[1] : '-',
          nro: comp,
          condPago: '-',
          importe,
        };
        if (importe >= 0) {
          const fv = new Date(`${fechaVenc}T00:00:00Z`);
          const hoyDate = new Date(`${hoyIso}T00:00:00Z`);
          mov.diasVenc = Math.max(0, Math.round((hoyDate - fv) / 86400000));
          facturas.push(mov);
        } else {
          ncs.push(mov);
        }
      }
      rr++;
    }
    r = rr;

    if (totalGeneral === null) {
      totalGeneral = facturas.reduce((s, f) => s + f.importe, 0) + ncs.reduce((s, x) => s + x.importe, 0);
    }

    clientes.push(armarCliente(cod, nombre, null, '-', totalGeneral, facturas, ncs, cutoffNcAlertIso));
  }

  const totales = calcularTotales(clientes, hoyIso);
  return { clientes, totales };
}

export { parsearDeliXls };
