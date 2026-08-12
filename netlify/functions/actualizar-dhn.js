import { crearHandler } from './lib/handler-factory.js';
import { extraerTexto } from './lib/pdf-text.js';
import { parsearClientes } from './lib/parse-dhn.js';

async function parse(buffer, hoyIso) {
  const texto = await extraerTexto(buffer);
  // Sin cliente.xlsx en el servidor (no se sube al repo público): usa el
  // mismo heurístico de parsearClientes para la condición de pago.
  return parsearClientes(texto, hoyIso, new Map());
}

export const handler = crearHandler({ empresaKey: 'dhn', label: 'DHN Distribuciones', parse });
