import { crearHandler } from './lib/handler-factory.js';
import { extraerTexto } from './lib/pdf-text.js';
import { parsearClientes } from './lib/parse-dhn.js';
import condPagoDhn from './lib/cond-pago-dhn.json' with { type: 'json' };

// cliente.xlsx no se sube al repo público (tiene datos personales de
// clientes), pero actualizar.py vuelca {codigo: condicionPago} sin PII a
// cond-pago-dhn.json en cada corrida local, y eso sí se versiona. Así la
// carga web usa la misma condición de pago que el flujo local en vez de
// caer siempre al heurístico de respaldo de parsearClientes.
const CON_PAGO_MAP = new Map(Object.entries(condPagoDhn));

async function parse(buffer, hoyIso) {
  const texto = await extraerTexto(buffer);
  return parsearClientes(texto, hoyIso, CON_PAGO_MAP);
}

export const handler = crearHandler({ empresaKey: 'dhn', label: 'DHN Distribuciones', parse });
