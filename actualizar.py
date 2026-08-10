#!/usr/bin/env python3
"""
DHN - Actualizador de Cuentas Corrientes
Uso: python actualizar.py ARCHIVO1 [ARCHIVO2 ...]
     Acepta el PDF "Saldo Detallado por Cliente" de DHN (.pdf) y/o el Excel
     "Saldos Detallados por Cliente y Comprobante" de Deli (.xls/.xlsx), en
     cualquier orden. Si en una corrida solo se pasa uno de los dos, el otro
     se conserva tal cual estaba en el index.html anterior.
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

EMPRESAS = {
    'dhn':  {'label': 'DHN Distribuciones'},
    'deli': {'label': 'Deli'},
}
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


def armar_cliente(cod: str, nombre: str, vendedor, cond_pago: str,
                  total_general: float, facturas: list, ncs: list,
                  cutoff_nc_alert: date) -> dict:
    """Arma el registro final de un cliente a partir de sus facturas y NC ya
    clasificadas. Común a DHN y Deli para que ambos reportes generen
    exactamente la misma estructura y el HTML los renderice igual."""
    vencidas   = sorted([f for f in facturas if f['diasVenc'] > 0], key=lambda x: -x['diasVenc'])
    por_vencer = sorted([f for f in facturas if f['diasVenc'] == 0], key=lambda x: x['fechaVenc'])

    for n in ncs:
        n['antigua'] = datetime.strptime(n['fechaComp'][:10], '%Y-%m-%d').date() < cutoff_nc_alert
    nc_alertas = [n for n in ncs if n['antigua']]

    total_nc        = sum(n['importe'] for n in ncs)
    saldo_venc_neto = round(sum(f['importe'] for f in vencidas) + total_nc, 2)
    max_dias        = max((f['diasVenc'] for f in vencidas), default=0)

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

    return {
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
    }


def calcular_totales(clientes: list, hoy: date) -> dict:
    return {
        'clientes':         len(clientes),
        'conVencido':       sum(1 for c in clientes if c['saldoVencidoNeto'] > 0),
        'conPorVencer':     sum(1 for c in clientes if c['porVencer']),
        'conNcAlerta':      sum(1 for c in clientes if c['ncAlertas']),
        'totalVencidoNeto': round(sum(c['saldoVencidoNeto'] for c in clientes if c['saldoVencidoNeto'] > 0), 2),
        'totalPorVencer':   round(sum(f['importe'] for c in clientes for f in c['porVencer']), 2),
        'totalNC':          round(sum(c['totalNC'] for c in clientes), 2),
        'fecha':            hoy.strftime('%Y-%m-%d'),
    }


def parsear_clientes(raw: str, hoy: date, cond_pago_map: dict) -> tuple[list, dict]:
    """DHN: parsea el texto extraído del PDF y devuelve (clientes, totales)."""
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

        clientes.append(armar_cliente(cod, nombre, vendedor, cond_pago, total_general,
                                       facturas, ncs, cutoff_nc_alert))

    totales = calcular_totales(clientes, hoy)
    return clientes, totales


def parsear_deli(xls_path: str, hoy: date) -> tuple[list, dict]:
    """Deli: parsea el Excel "Saldos Detallados por Cliente y Comprobante"
    (.xls viejo, formato Crystal Reports) y devuelve (clientes, totales).

    Formato bien distinto al PDF de DHN:
    - No trae condición de pago ni número de vendedor.
    - No tiene una línea de "Total General": el total de cada cliente está en
      la celda de la columna K (índice 10) de la fila de dirección, dos filas
      debajo del encabezado del cliente.
    - No separa facturas de NC por un código de tipo confiable (los prefijos
      de comprobante como PEX/RPX aparecen con importes positivos y negativos
      indistintamente), así que se clasifica por el signo del importe:
      positivo = cargo (factura), negativo = crédito (NC).
    - "Fecha Comprob." no existe: se usa la Fecha Mov. como equivalente.
    """
    import xlrd

    cutoff_nc_alert = date(hoy.year, hoy.month, 1)
    wb = xlrd.open_workbook(xls_path)
    sh = wb.sheet_by_index(0)
    datemode = wb.datemode
    n = sh.nrows

    def xldate_iso(v):
        return xlrd.xldate.xldate_as_datetime(v, datemode).date().isoformat()

    def es_header_cliente(r):
        v0, t0 = sh.cell_value(r, 0), sh.cell_type(r, 0)
        return t0 == 1 and isinstance(v0, str) and re.fullmatch(r'[\d.]+', v0.strip())

    clientes = []
    r = 0
    while r < n:
        if not es_header_cliente(r):
            r += 1
            continue

        cod = sh.cell_value(r, 0).strip().replace('.', '')
        nombre = str(sh.cell_value(r, 1)).strip().lstrip('@').strip()

        total_general = None
        facturas, ncs = [], []
        rr = r + 1
        while rr < n and not es_header_cliente(rr):
            if total_general is None and sh.cell_type(rr, 10) == 2:
                total_general = sh.cell_value(rr, 10)
            if sh.cell_type(rr, 1) == 3:   # fila de movimiento (Fecha Mov. es una fecha real)
                fecha_mov  = xldate_iso(sh.cell_value(rr, 1))
                fecha_venc = xldate_iso(sh.cell_value(rr, 2)) if sh.cell_type(rr, 2) == 3 else fecha_mov
                comp = str(sh.cell_value(rr, 4)).strip()
                importe = round(float(sh.cell_value(rr, 6)), 2)
                tipo_m = re.match(r'^([A-Za-z]+)', comp)
                mov = {
                    'fechaComp': fecha_mov,
                    'fechaVenc': fecha_venc,
                    'tipo':      tipo_m.group(1) if tipo_m else '-',
                    'nro':       comp,
                    'condPago':  '-',
                    'importe':   importe,
                }
                if importe >= 0:
                    fv = datetime.strptime(fecha_venc, '%Y-%m-%d').date()
                    mov['diasVenc'] = max(0, (hoy - fv).days)
                    facturas.append(mov)
                else:
                    ncs.append(mov)
            rr += 1
        r = rr

        if total_general is None:
            total_general = sum(f['importe'] for f in facturas) + sum(x['importe'] for x in ncs)

        clientes.append(armar_cliente(cod, nombre, None, '-', total_general,
                                       facturas, ncs, cutoff_nc_alert))

    totales = calcular_totales(clientes, hoy)
    return clientes, totales


def parsear_deli_pdf(raw: str, hoy: date) -> tuple[list, dict]:
    """Deli: parsea el texto extraído (pdftotext -layout) del PDF "Saldos
    Detallados por Cliente y Comprobante" y devuelve (clientes, totales).

    Mismo reporte de Crystal Reports que el .xls viejo (ver parsear_deli),
    exportado ahora como PDF. A diferencia del .xls, sí trae "Fecha Mov." y
    "FechaVenc" por movimiento (las dos fechas que aparecen en cada línea;
    "Fecha orig." queda siempre en blanco). El encabezado de cada cliente se
    repite al cortar página en medio de sus movimientos, así que los bloques
    se agrupan por código de cliente en vez de asumir uno por encabezado.
    """
    cutoff_nc_alert = date(hoy.year, hoy.month, 1)

    # Cuando "Fecha Mov." no entra en su columna, pdftotext la deja sola en
    # una línea y "FechaVenc" + el resto del movimiento pasan a la siguiente.
    raw = re.sub(
        r'(\d{1,2}/\d{1,2}/\d{4})[ \t]*\n[ \t]*(\d{1,2}/\d{1,2}/\d{4}\s+\S)',
        r'\1 \2', raw,
    )

    header_re = re.compile(r'^(\d[\d.]*)\s{2,}(\S.*?)\s{2,}(\S.*)$', re.MULTILINE)
    mov_re = re.compile(
        r'^\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(?:\d+\s+)?(\S+)\s+'
        r'([\-\d.,]+)\s+([\-\d.,]+)\s+([\-\d.,]+)\s+([\-\d.,]+)(?:\s*[A-Z]+)?\s+(\d+)\s*$',
        re.MULTILINE,
    )

    def to_float(s):
        return round(float(s.replace('.', '').replace(',', '.')), 2)

    def fecha_iso(s):
        d, m, y = s.split('/')
        return date(int(y), int(m), int(d)).isoformat()

    headers = list(header_re.finditer(raw))
    por_cliente = {}   # cod -> {'nombre', 'total', 'facturas', 'ncs'}
    orden = []

    for i, hm in enumerate(headers):
        cod = hm.group(1).replace('.', '')
        nombre = hm.group(2).strip().lstrip('@').strip()
        inicio = hm.end()
        fin = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
        block = raw[inicio:fin]

        entry = por_cliente.get(cod)
        if entry is None:
            entry = {'nombre': nombre, 'total': None, 'facturas': [], 'ncs': []}
            por_cliente[cod] = entry
            orden.append(cod)

        # La línea de dirección, justo debajo del encabezado, termina con el
        # total general del cliente (se repite igual en cada continuación).
        lineas = block.split('\n')
        for linea in lineas[1:3]:
            if not linea.strip() or mov_re.match(linea):
                continue
            tot_m = re.search(r'([\-\d.,]+)\s*$', linea.strip())
            if tot_m:
                try:
                    entry['total'] = to_float(tot_m.group(1))
                except ValueError:
                    pass
            break

        for m in mov_re.finditer(block):
            fecha_mov  = fecha_iso(m.group(1))
            fecha_venc = fecha_iso(m.group(2))
            comp = m.group(3).strip()
            try:
                importe = to_float(m.group(4))
            except ValueError:
                continue
            tipo_m = re.match(r'^([A-Za-z]+)', comp)
            mov = {
                'fechaComp': fecha_mov,
                'fechaVenc': fecha_venc,
                'tipo':      tipo_m.group(1) if tipo_m else '-',
                'nro':       comp,
                'condPago':  '-',
                'importe':   importe,
            }
            if importe >= 0:
                fv = datetime.strptime(fecha_venc, '%Y-%m-%d').date()
                mov['diasVenc'] = max(0, (hoy - fv).days)
                entry['facturas'].append(mov)
            else:
                entry['ncs'].append(mov)

    clientes = []
    for cod in orden:
        entry = por_cliente[cod]
        total_general = entry['total']
        if total_general is None:
            total_general = sum(f['importe'] for f in entry['facturas']) + \
                             sum(n['importe'] for n in entry['ncs'])
        clientes.append(armar_cliente(cod, entry['nombre'], None, '-', total_general,
                                       entry['facturas'], entry['ncs'], cutoff_nc_alert))

    totales = calcular_totales(clientes, hoy)
    return clientes, totales


def cargar_empresas_previas() -> dict:
    """Si ya existe un index.html, recupera los datos embebidos por empresa
    para no perderlos cuando esta corrida solo trae el archivo de una de las
    dos (p.ej. un día solo llega el PDF de DHN)."""
    if not OUTPUT_HTML.exists():
        return {}
    html = OUTPUT_HTML.read_text(encoding='utf-8')
    m = re.search(r'const DATA\s*=\s*(\{.*?\});\n', html, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def generar_html(empresas: dict) -> None:
    """Lee el template de build_pdf_grid.py y genera index.html con los datos
    de todas las empresas presentes en `empresas`."""
    data_json = json.dumps(empresas, ensure_ascii=False)

    build_script = Path(__file__).parent / "build_pdf_grid.py"
    with open(build_script, encoding='utf-8') as f:
        build_src = f.read()

    # Ejecuta el script builder con la nueva data
    import io, contextlib, builtins
    orig_open = builtins.open

    class FakeFile:
        def __init__(self): self._data = data_json
        def read(self): return self._data
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
            exec(compile(build_src, build_script, 'exec'), {'__file__': str(build_script)})
    finally:
        builtins.open = orig_open


def main():
    if len(sys.argv) < 2:
        print("Uso: python actualizar.py ARCHIVO.pdf [ARCHIVO_DELI.xls]")
        print("     Acepta el PDF de DHN y/o el Excel de Deli, en cualquier orden.")
        print("     Si falta alguno de los dos, se conserva el de la corrida anterior.")
        sys.exit(1)

    hoy = date.today()
    empresas = cargar_empresas_previas()

    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if not path.exists():
            print(f"❌ No se encontró el archivo: {path_str}")
            sys.exit(1)

        ext = path.suffix.lower()
        if ext == '.pdf':
            raw = extraer_texto(path_str)
            # El PDF de Deli ("Saldos Detallados por Cliente y Comprobante")
            # y el de DHN ("Saldo Detallado por Cliente") comparten extensión
            # desde que Deli también empezó a exportar en PDF; se distinguen
            # por el título del reporte.
            es_deli = 'Saldos Detallados por Cliente y Comprobante' in raw

            if es_deli:
                print(f"📄 Leyendo PDF Deli: {path_str}")
                print("⚙️  Procesando clientes Deli...")
                clientes, totales = parsear_deli_pdf(raw, hoy)
                empresas['deli'] = {'label': EMPRESAS['deli']['label'], 'clientes': clientes, 'totales': totales}
                empresa_actual = 'deli'
            else:
                cond_pago_map = cargar_condiciones_pago(CLIENTES_XLSX)
                if cond_pago_map:
                    print(f"📇 Condición de pago cargada desde {CLIENTES_XLSX.name}: {len(cond_pago_map)} clientes")
                else:
                    print(f"⚠️  No se encontró {CLIENTES_XLSX.name}, se usa el heurístico del PDF para cond. de pago")

                print(f"📄 Leyendo PDF DHN: {path_str}")
                print("⚙️  Procesando clientes DHN...")
                clientes, totales = parsear_clientes(raw, hoy, cond_pago_map)
                empresas['dhn'] = {'label': EMPRESAS['dhn']['label'], 'clientes': clientes, 'totales': totales}
                empresa_actual = 'dhn'

        elif ext in ('.xls', '.xlsx'):
            print(f"📄 Leyendo Excel Deli: {path_str}")
            print("⚙️  Procesando clientes Deli...")
            clientes, totales = parsear_deli(path_str, hoy)
            empresas['deli'] = {'label': EMPRESAS['deli']['label'], 'clientes': clientes, 'totales': totales}
            empresa_actual = 'deli'

        else:
            print(f"❌ Extensión no reconocida para {path_str} (se espera .pdf o .xls/.xlsx)")
            sys.exit(1)

        totales_actual = empresas[empresa_actual]['totales']
        print(f"✅ {totales_actual['clientes']} clientes · {totales_actual['conVencido']} con vencido · {totales_actual['conNcAlerta']} con NC antiguas")
        print(f"💰 Total vencido neto: ${totales_actual['totalVencidoNeto']:,.2f}")

    if not empresas:
        print("❌ No hay datos para generar el dashboard.")
        sys.exit(1)

    print("🔨 Generando HTML...")
    generar_html(empresas)

    print(f"\n✅ Listo → {OUTPUT_HTML.resolve()}")
    print("📤 Subí ese archivo a Netlify y el dashboard se actualiza.")


if __name__ == "__main__":
    main()
