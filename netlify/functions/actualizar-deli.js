import { crearHandler } from './lib/handler-factory.js';
import { parsearDeliXls } from './lib/parse-deli-xls.js';

async function parse(buffer, hoyIso) {
  return parsearDeliXls(buffer, hoyIso);
}

export const handler = crearHandler({ empresaKey: 'deli', label: 'Deli', parse });
