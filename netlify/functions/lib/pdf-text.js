import * as pdfjsLibNs from 'pdfjs-dist/legacy/build/pdf.mjs';
import * as pdfjsWorkerNs from 'pdfjs-dist/legacy/build/pdf.worker.mjs';

// El bundler de Netlify empaqueta las funciones como CJS, y el interop
// ESM/CJS resultante a veces deja las exportaciones reales colgando de
// `.default` en vez de en el namespace importado directamente — se prueban
// ambas formas para no depender de un detalle interno del bundler.
const pdfjsLib = typeof pdfjsLibNs.getDocument === 'function' ? pdfjsLibNs : pdfjsLibNs.default;
const pdfjsWorker = typeof pdfjsWorkerNs.WorkerMessageHandler !== 'undefined' ? pdfjsWorkerNs : pdfjsWorkerNs.default;

// pdfjs-dist corre sin Worker real en Node: si no encuentra
// `globalThis.pdfjsWorker` con el handler ya cargado, intenta un
// `import()` dinámico relativo a "pdf.worker.mjs" que el bundler de Netlify
// no resuelve bien (el archivo termina en otra ruta tras empaquetar).
// Registrar el worker acá, importado estáticamente, evita ese import
// dinámico por completo — es el patrón documentado para uso en Node.
globalThis.pdfjsWorker = pdfjsWorker;

// Reconstruye, a partir de los items posicionados que da pdfjs-dist, un texto
// plano equivalente al de `pdftotext -layout`: una línea por fila visual,
// con huecos horizontales convertidos en huecos de espacios proporcionales
// al ancho de carácter estimado. Las regex de parsear_clientes solo asumen
// "\s+" entre columnas y "\s{3,}" para separar el nombre del resto del
// encabezado, así que no hace falta reproducir la grilla de pdftotext al
// pixel, solo el orden de lectura y la proporción de los huecos.
// Tolerancia "ajustada" para agrupar por Y: alcanza para el jitter normal
// dentro de una misma fila (~1-2pt observado), pero es más chica que el
// espaciado mínimo entre filas realmente distintas (~5pt en el bloque de
// encabezado de cada cliente, ~12-13pt en la tabla de movimientos).
const Y_TOLERANCE = 2.2;
// Algunas columnas (p.ej. "Días Venc") vienen con su propio jitter vertical
// más grande (hasta ~4pt observado) que las separa de su fila con la
// tolerancia ajustada de arriba, quedando como una "línea" propia de 1-2
// items cortos. ORPHAN_MERGE_DIST las reincorpora a la fila vecina más
// cercana en vez de dejarlas sueltas (lo que rompería las columnas de las
// regex que esperan todo el movimiento en un renglón).
const ORPHAN_MERGE_DIST = 6;

async function extraerTexto(buffer) {
  // pdfjs-dist exige un Uint8Array "puro": rechaza instancias de Buffer de
  // Node (aunque Buffer herede de Uint8Array) con un chequeo de tipo estricto.
  const data = new Uint8Array(buffer);
  const doc = await pdfjsLib.getDocument({
    data,
    useWorkerFetch: false,
    isEvalSupported: false,
    disableFontFace: true,
    verbosity: 0, // silencia warnings de fuentes no embebidas, no afecta la extracción de texto
  }).promise;

  const paginas = [];
  for (let n = 1; n <= doc.numPages; n++) {
    const page = await doc.getPage(n);
    const content = await page.getTextContent();
    paginas.push(reconstruirPagina(content.items));
  }
  return paginas.join('\n\n');
}

function reconstruirPagina(items) {
  const usables = items.filter((it) => it.str !== undefined);
  if (!usables.length) return '';

  // Ancho de carácter de referencia: promedio ponderado tomado SOLO de items
  // con texto real (no de "items" que son puro relleno de espacio, cuyo
  // `width` representa el hueco completo y no un ancho de glifo — usarlo
  // como referencia local hace colapsar el cálculo del hueco siguiente).
  let totalWidth = 0;
  let totalChars = 0;
  for (const it of usables) {
    if (it.str.trim() === '' || !(it.width > 0)) continue;
    totalWidth += it.width;
    totalChars += it.str.length;
  }
  const avgCharWidth = totalChars > 0 ? totalWidth / totalChars : 5;

  // Agrupa por Y (redondeando con tolerancia) para formar líneas.
  const lineas = [];
  for (const it of usables) {
    const y = it.transform[5];
    let linea = lineas.find((l) => Math.abs(l.y - y) <= Y_TOLERANCE);
    if (!linea) {
      linea = { y, items: [] };
      lineas.push(linea);
    }
    linea.items.push(it);
  }
  // Orden de lectura: de arriba hacia abajo (Y grande -> chico en espacio PDF).
  lineas.sort((a, b) => b.y - a.y);

  const finales = fusionarLineasHuerfanas(lineas);
  return finales.map((l) => lineaATexto(l, avgCharWidth)).join('\n');
}

// Una "línea huérfana" es una columna que quedó sola (texto cortito, uno o
// dos items) por su propio jitter vertical — se reincorpora a la fila
// vecina real más cercana en vez de quedar como renglón propio.
function esHuerfana(linea) {
  const items = linea.items.filter((it) => it.str.trim() !== '');
  if (!items.length || items.length > 2) return false;
  const texto = items.map((it) => it.str).join('').trim();
  return texto.length > 0 && texto.length <= 3;
}

function fusionarLineasHuerfanas(lineas) {
  const usada = new Array(lineas.length).fill(false);
  for (let i = 0; i < lineas.length; i++) {
    if (!esHuerfana(lineas[i])) continue;
    let mejorIdx = -1;
    let mejorDist = Infinity;
    for (let j = 0; j < lineas.length; j++) {
      if (j === i || esHuerfana(lineas[j])) continue;
      const d = Math.abs(lineas[j].y - lineas[i].y);
      if (d <= ORPHAN_MERGE_DIST && d < mejorDist) { mejorDist = d; mejorIdx = j; }
    }
    if (mejorIdx !== -1) {
      lineas[mejorIdx].items.push(...lineas[i].items);
      usada[i] = true;
    }
  }
  return lineas.filter((_, i) => !usada[i]);
}

function lineaATexto(linea, avgCharWidth) {
  // Los items "en blanco" (str vacío o solo espacios) de este reporte no son
  // huecos confiables: a veces son un único carácter espacio estirado a un
  // ancho enorme que se SUPERPONE con varios items reales siguientes (cada
  // columna de esta tabla se posiciona con coordenadas absolutas propias, no
  // secuencialmente). Se descartan del todo y el espaciado se calcula solo
  // a partir de la distancia real entre items con texto.
  const items = linea.items
    .filter((it) => it.str.trim() !== '')
    .sort((a, b) => a.transform[4] - b.transform[4]);
  let out = '';
  let prevEndX = null;
  for (const it of items) {
    const x = it.transform[4];
    if (prevEndX !== null) {
      const gap = x - prevEndX;
      if (gap > avgCharWidth * 0.35) {
        out += ' '.repeat(Math.max(1, Math.round(gap / avgCharWidth)));
      }
    }
    out += it.str;
    prevEndX = x + (it.width || 0);
  }
  return out;
}

export { extraerTexto };
