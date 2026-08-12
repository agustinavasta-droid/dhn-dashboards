import { leerEstadoActual, commitNuevoIndex } from './github.js';

const MAX_BYTES = 4 * 1024 * 1024;

// Netlify Functions corre en UTC; actualizar.py corre en la máquina de
// Agustina (hora Argentina). Se calcula "hoy" en ART (UTC-3, sin horario de
// verano) para que el corte de NC antiguas y los días vencidos de Deli den
// lo mismo que si se corriera el script local esa misma noche.
function hoyArgentinaIso() {
  return new Date(Date.now() - 3 * 3600 * 1000).toISOString().slice(0, 10);
}

function respuesta(statusCode, data) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  };
}

function crearHandler({ empresaKey, label, parse }) {
  return async function handler(event) {
    if (event.httpMethod !== 'POST') {
      return respuesta(405, { ok: false, error: 'Método no permitido.' });
    }

    let payload;
    try {
      payload = JSON.parse(event.body || '{}');
    } catch {
      return respuesta(400, { ok: false, error: 'Solicitud inválida.' });
    }

    const { password, contentBase64 } = payload;
    if (!password || password !== process.env.UPLOAD_PASSWORD) {
      return respuesta(401, { ok: false, error: 'Contraseña incorrecta.' });
    }
    if (!contentBase64) {
      return respuesta(400, { ok: false, error: 'Falta el archivo.' });
    }

    let buffer;
    try {
      buffer = Buffer.from(contentBase64, 'base64');
    } catch {
      return respuesta(400, { ok: false, error: 'Archivo inválido.' });
    }
    if (buffer.length > MAX_BYTES) {
      return respuesta(400, { ok: false, error: 'Archivo muy grande para el formulario web (máx. 4MB). Usá el flujo local (actualizar.py).' });
    }

    const hoyIso = hoyArgentinaIso();

    let clientes;
    let totales;
    try {
      ({ clientes, totales } = await parse(buffer, hoyIso));
    } catch (e) {
      return respuesta(422, { ok: false, error: `No se pudo procesar el archivo: ${e.message}` });
    }

    if (!clientes.length) {
      return respuesta(422, { ok: false, error: 'No se encontraron clientes en el archivo. Verificá que sea el reporte correcto.' });
    }

    try {
      const estado = await leerEstadoActual();
      await commitNuevoIndex(
        empresaKey,
        { label, clientes, totales },
        `Actualización dashboard ${label} ${hoyIso} (vía formulario web)`,
        estado,
      );
    } catch (e) {
      return respuesta(502, { ok: false, error: `No se pudo publicar en GitHub: ${e.message}` });
    }

    return respuesta(200, { ok: true, clientes: totales.clientes, conVencido: totales.conVencido });
  };
}

export { crearHandler };
