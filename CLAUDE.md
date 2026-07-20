# DHN - Actualizador de Cuentas Corrientes

## ¿Qué hace este proyecto?

Toma un PDF de "Saldo Detallado por Cliente" generado por el sistema de DHN
y produce un `index.html` interactivo con:
- Grilla filtrable por semáforo (Crítico / Medio / A tiempo)
- Detalle de facturas por cliente expandible
- Pestaña de NC antiguas (anteriores a junio 2024)
- Exportación a Excel directamente desde el browser
- Totalizadores reactivos por estado

El `index.html` resultante se sube a Netlify y se comparte como link.

---

## Uso diario (lo único que hay que hacer)

```bash
python actualizar.py PDFCUENTASCORR7_17.pdf
```

Reemplazá `PDFCUENTASCORR7_17.pdf` por el nombre del PDF del día.
El script genera `index.html` en esta misma carpeta.

---

## Requisitos

- Python 3.9+
- `pdftotext` instalado (viene con `poppler-utils`)
  - Mac: `brew install poppler`
  - Ubuntu/Debian: `sudo apt install poppler-utils`
- Librerías Python: `pip install -r requirements.txt`

---

## Estructura del proyecto

```
dhn_project/
├── actualizar.py       ← Script principal (correr esto)
├── build_pdf_grid.py   ← Template del HTML (no tocar)
├── CLAUDE.md           ← Este archivo
├── requirements.txt    ← Dependencias Python
└── index.html          ← Output generado (subir a Netlify)
```

---

## Configuración

En `actualizar.py`, línea ~15, podés ajustar:

```python
CUTOFF_NC_ALERT = date(2024, 6, 1)  # NC anteriores a esta fecha → alerta
```

---

## Cómo subir a Netlify

1. Corrés `python actualizar.py PDF_DEL_DIA.pdf`
2. Se genera `index.html` en esta carpeta
3. Entrás a tu panel de Netlify → tu sitio → pestaña "Deploys"
4. Arrastrás el `index.html` ahí
5. El link se actualiza al instante, sin cambiar la URL

---

## Lógica de semáforos

| Color | Criterio |
|-------|----------|
| 🔴 Crítico | Score ≥ 60 O más de 60 días vencido |
| 🟡 Medio | Score ≥ 20 O entre 30-60 días |
| 🟢 A tiempo | Sin vencido, solo facturas por vencer |

El score combina: monto vencido (hasta 50 pts) + días vencido (hasta 30 pts) + NC antiguas (hasta 20 pts).

---

## Problemas comunes

**"No se encontró pdftotext"**
→ Instalá poppler: `brew install poppler` (Mac) o `sudo apt install poppler-utils` (Linux)

**El PDF no parsea bien algún cliente**
→ Avisale a quien mantiene el script con el nombre del cliente y el número,
  se puede ajustar el regex en `parsear_clientes()`.

**Quiero cambiar el diseño del HTML**
→ Editá `build_pdf_grid.py` y volvé a correr `actualizar.py`.
