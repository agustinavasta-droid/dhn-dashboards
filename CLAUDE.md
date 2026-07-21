# DHN - Actualizador de Cuentas Corrientes

## ¿Qué hace este proyecto?

Toma un PDF de "Saldo Detallado por Cliente" generado por el sistema de DHN
y produce un `index.html` interactivo con:
- Grilla filtrable por semáforo (Crítico / Medio / A tiempo)
- Detalle de facturas por cliente expandible
- Pestaña de NC antiguas (del mes anterior al de la corrida, o más viejas)
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

El corte de "NC antiguas" es automático: se recalcula en cada corrida como el
primer día del mes en curso. Es decir, cualquier NC emitida antes de ese mes
(el mes anterior o más vieja) aparece en la pestaña de alerta. No hace falta
tocar nada a mano.

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

---

## Deploy automático

Después de correr actualizar.py y generar el nuevo index.html (o deli_index.html), 
correr siempre estos comandos para publicar los cambios:

```bash
git add -A
git commit -m "Actualización dashboard $(date +%Y-%m-%d)"
git push
```

Esto dispara el deploy automático en Netlify.
