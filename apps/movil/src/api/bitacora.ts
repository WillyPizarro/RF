import type { RespuestaApi } from './cliente';
import type { components } from './esquema';
import { llamarAutenticado } from '../sesion/controlador';

export type RespuestaBitacora = components['schemas']['RespuestaBitacora'];
export type RegistroBitacora = components['schemas']['Registro'];

export type FiltrosBitacora = {
  usuario?: string;
  desde?: string;
  hasta?: string;
  tipo?: string;
  resultado?: string;
};

/**
 * GET /v1/bitacora (CONTRATO-HU-07 §4). null = la sesion ya resolvio la respuesta (401 o 403).
 * Un error de red lanza: nunca se convierte en una lista vacia (regla 7).
 */
export function obtenerBitacora(filtros: FiltrosBitacora, cursor: string | null): Promise<RespuestaApi | null> {
  const parametros = new URLSearchParams();
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor) parametros.set(clave, valor);
  }
  if (cursor) parametros.set('cursor', cursor);
  const consulta = parametros.toString();
  return llamarAutenticado(`/v1/bitacora${consulta ? `?${consulta}` : ''}`);
}
