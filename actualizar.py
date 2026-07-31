#!/usr/bin/env python3
"""
DHN - Actualizador de Cuentas Corrientes
Uso: python actualizar.py NOMBRE_DEL_PDF.pdf
Genera: index.html listo para subir a Netlify
"""

import sys
import re
import json
import subprocess
from datetime import datetime, date
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
OUTPUT_HTML     = Path("index.html")
CLIENTES_XLSX   = Path(__file__).parent / "cliente.xlsx"
# ────────────────────────────────────────────────────────────────────────────

def cargar_condiciones_pago(xlsx_path: Path) -> dict:
    """Lee cliente.xlsx y devuelve {codigo: codigoCondicionPago}."""
    if not xlsx_path.exists():
        return {}
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb['clientes']
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    idx_cod = header.index('codigo')
    idx_cp  = header.index('codigoCondicionPago')
    return {
        str(row[idx_cod]): row[idx_cp]
        for row in rows
        if row[idx_cod] is not None and row[idx_cp]
    }


def extraer_texto(pdf_path: str) -> str:
    """Extrae el texto del PDF preservando el layout."""
    result = subprocess.run(
        ["pdftotext", "-layout", pdf_path, "-"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"Error al leer el PDF: {result.stderr}")
    return result.stdout


def parsear_clientes(raw: str, hoy: date, cond_pago_map: dict) -> tuple[list, dict]:
    """Parsea el texto extraído y devuelve (clientes, totales)."""
    cutoff_nc_alert = date(hoy.year, hoy.month, 1)   # NC del mes anterior o más viejas → alerta
    # El corte de bloque solo depende del inicio "NNN - " en la línea: cuando el
    # nombre del cliente es largo y se parte en dos líneas, "Total General:" queda
    # en la línea siguiente, no en la misma, así que no puede exigirse acá.
    client_blocks = re.split(r'\n(?=\s*\d+ - )', raw)

    # La columna "Cod Cliente" (número de cliente repetido en cada línea de
    # movimiento) es opcional: algunos reportes la incluyen antes del número
    # de línea del Concepto y otros no (p.ej. desde el reporte del 2026-07-29).
    # Al final de la línea viene "Saldo Acum" (se descarta) y "Vend" (nro. de vendedor).
    line_re = re.compile(
        r'(\d{4}-\d{2}-\d{2})\s+(\S+)\s+(?:\d+\s+)?(\d+)\s+'
        r'(FAC-[AB]|NCR-[AB]|NDB-[AB]|DAJ|CAJ|COB-R)\s+'
        r'(\S+)\s+([A-Z0-9]+)\s+'
        r'\$\s*([\-\d.,]+)\s+\$\s*([\-\d.,]+)\s+(\d*)\s+'
        r'\$\s*[\-\d.,]+\s+(\d+)'
    )

    clientes = []
    for block in client_blocks:
        hdr = re.search(r'^\s*(\d+) - ([^\n]*)', block, re.MULTILINE)
        if not hdr:
            continue
        cod = hdr.group(1).strip()
        name_line1 = hdr.group(2)

        total_m = re.search(r'Total General:\s*\$\s*([\d.,\-]+)', block)
        if not total_m:
            continue
        total_str = total_m.group(1).replace('.', '').replace(',', '.')
        try:
            total_general = float(total_str)
        except ValueError:
            continue

        nombre = re.split(r'\s{3,}', name_line1)[0].strip()
        if 'Total General:' not in name_line1:
            # Nombre partido en dos líneas: la continuación viene justo
            # después de la línea con "Total General:".
            cont_m = re.search(r'Total General:[^\n]*\n([^\n]*)', block)
            if cont_m:
                cont = re.split(r'\s{3,}', cont_m.group(1))[0].strip()
                if cont and not re.match(r'^\d', cont):
                    nombre = f'{nombre} {cont}'.strip()

        cond_pago = cond_pago_map.get(cod)
        if not cond_pago:
            cond_pagos = re.findall(r'\b(CON|07D|14D|21D|30D|45D|60D|90D)\b', block)
            cond_pago  = max(set(cond_pagos), key=cond_pagos.count) if cond_pagos else '-'

        movs = []
        vend_counts = {}
        for m in line_re.finditer(block):
            importe_str = m.group(7).replace('.', '').replace(',', '.')
            try:
                importe = float(importe_str)
            except ValueError:
                continue
            movs.append({
                'fechaComp':  m.group(1),
                'fechaVenc':  m.group(2),
                'tipo':       m.group(4),
                'nro':        m.group(5),
                'condPago':   m.group(6),
                'importe':    round(importe, 2),
                'diasVenc':   int(m.group(9)) if m.group(9) else 0,
            })
            vend = m.group(10)
            if vend:
                vend_counts[vend] = vend_counts.get(vend, 0) + 1

        # El vendedor es (normalmente) el mismo en todas las líneas del cliente;
        # por las dudas, si hubiera más de uno, nos quedamos con el más frecuente.
        vendedor = max(vend_counts, key=vend_counts.get) if vend_counts else None

        facturas  = [m for m in movs if m['tipo'].startswith('FAC')]
        ncs       = [m for m in movs if m['tipo'].startswith('NCR') or m['tipo'].startswith('NDB')]

        vencidas   = sorted([f for f in facturas if f['diasVenc'] > 0], key=lambda x: -x['diasVenc'])
        por_vencer = sorted([f for f in facturas if f['diasVenc'] == 0], key=lambda x: x['fechaVenc'])

        for n in ncs:
            n['antigua'] = datetime.strptime(n['fechaComp'][:10], '%Y-%m-%d').date() < cutoff_nc_alert

        nc_alertas = [n for n in ncs if n['antigua']]

        total_nc       = sum(n['importe'] for n in ncs)
        saldo_venc_neto = round(sum(f['importe'] for f in vencidas) + total_nc, 2)
        max_dias       = max((f['diasVenc'] for f in vencidas), default=0)

        # Score de prioridad
        score = 0
        if saldo_venc_neto > 20_000_000: score += 50
        elif saldo_venc_neto > 10_000_000: score += 40
        elif saldo_venc_neto > 5_000_000: score += 30
        elif saldo_venc_neto > 2_000_000: score += 20
        elif saldo_venc_neto > 500_000:   score += 10
        if max_dias > 60: score += 30
        elif max_dias > 45: score += 20
        elif max_dias > 30: score += 10
        nc_n = len(nc_alertas)
        if nc_n > 20: score += 20
        elif nc_n > 10: score += 15
        elif nc_n > 0: score += 5

        # Fecha vencido más antigua
        venc_fechas = [
            datetime.strptime(f['fechaVenc'][:10], '%Y-%m-%d').date()
            for f in vencidas if f['fechaVenc'] != '0001-01-01'
        ]
        vencido_desde = min(venc_fechas).strftime('%d-%m-%Y') if venc_fechas else None

        clientes.append({
            'cod':             cod,
            'nombre':          nombre,
            'vendedor':        vendedor,
            'totalGeneral':    round(total_general, 2),
            'condPago':        cond_pago,
            'totalNC':         round(total_nc, 2),
            'saldoVencidoNeto': saldo_venc_neto,
            'maxDiasVenc':     max_dias,
            'vencidoDesde':    vencido_desde,
            'prioScore':       score,
            'vencidas':        vencidas,
            'porVencer':       por_vencer,
            'ncAlertas':       nc_alertas,
            'ncs':             ncs,
        })

    totales = {
        'clientes':         len(clientes),
        'conVencido':       sum(1 for c in clientes if c['saldoVencidoNeto'] > 0),
        'conPorVencer':     sum(1 for c in clientes if c['porVencer']),
        'conNcAlerta':      sum(1 for c in clientes if c['ncAlertas']),
        'totalVencidoNeto': round(sum(c['saldoVencidoNeto'] for c in clientes if c['saldoVencidoNeto'] > 0), 2),
        'totalPorVencer':   round(sum(f['importe'] for c in clientes for f in c['porVencer']), 2),
        'totalNC':          round(sum(c['totalNC'] for c in clientes), 2),
        'fecha':            hoy.strftime('%Y-%m-%d'),
    }
    return clientes, totales


def generar_html(clientes: list, totales: dict, fecha_reporte: str) -> str:
    """Lee el template de build_pdf_grid.py y genera el HTML final."""
    data_json = json.dumps({'clientes': clientes, 'totales': totales}, ensure_ascii=False)

    # Lee el script builder y extrae el template HTML
    build_script = Path(__file__).parent / "build_pdf_grid.py"
    exec_globals = {}
    # Reemplaza la data embebida con la nueva
    with open(build_script, encoding='utf-8') as f:
        build_src = f.read()

    # Actualiza fecha en el HTML
    build_src_mod = re.sub(r'DHN Distribuciones · Reporte al \d{2}-\d{2}-\d{4}',
                           f'DHN Distribuciones · Reporte al {datetime.strptime(fecha_reporte, "%Y-%m-%d").strftime("%d-%m-%Y")}',
                           build_src)
    build_src_mod = re.sub(r"'fecha': '\d{4}-\d{2}-\d{2}'",
                           f"'fecha': '{fecha_reporte}'", build_src_mod)

    # Ejecuta el script builder con la nueva data
    import io, contextlib
    import importlib.util, types

    # Patch: intercept open() for grid_data.json to serve our data
    import builtins
    orig_open = builtins.open

    class FakeFile:
        def __init__(self): self._data = data_json.encode()
        def read(self): return data_json
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def patched_open(path, *args, **kwargs):
        if str(path) == 'pdf_data.json':
            return FakeFile()
        return orig_open(path, *args, **kwargs)

    builtins.open = patched_open
    try:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exec(compile(build_src_mod, build_script, 'exec'), {'__file__': str(build_script)})
    finally:
        builtins.open = orig_open

    # Lee el HTML generado
    html_out = OUTPUT_HTML.read_text(encoding='utf-8')
    return html_out


def main():
    if len(sys.argv) < 2:
        print("Uso: python actualizar.py RUTA_AL_PDF.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"❌ No se encontró el archivo: {pdf_path}")
        sys.exit(1)

    hoy = date.today()
    cond_pago_map = cargar_condiciones_pago(CLIENTES_XLSX)
    if cond_pago_map:
        print(f"📇 Condición de pago cargada desde {CLIENTES_XLSX.name}: {len(cond_pago_map)} clientes")
    else:
        print(f"⚠️  No se encontró {CLIENTES_XLSX.name}, se usa el heurístico del PDF para cond. de pago")

    print(f"📄 Leyendo PDF: {pdf_path}")
    raw = extraer_texto(pdf_path)

    print("⚙️  Procesando clientes...")
    clientes, totales = parsear_clientes(raw, hoy, cond_pago_map)

    print(f"✅ {totales['clientes']} clientes · {totales['conVencido']} con vencido · {totales['conNcAlerta']} con NC antiguas")
    print(f"💰 Total vencido neto: ${totales['totalVencidoNeto']:,.2f}")

    print("🔨 Generando HTML...")
    generar_html(clientes, totales, hoy.strftime('%Y-%m-%d'))

    print(f"\n✅ Listo → {OUTPUT_HTML.resolve()}")
    print("📤 Subí ese archivo a Netlify y el dashboard se actualiza.")


if __name__ == "__main__":
    main()
