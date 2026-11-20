import { urlApi } from '../config';
import type { components } from './esquema';

export type SaludRespuesta = components['schemas']['SaludRespuesta'];

/** GET /v1/salud. Cualquier respuesta distinta de 200 o error de red lanza (SPRINT0 M-1 F). */
export async function consultarSalud(): Promise<SaludRespuesta> {
  const respuesta = await fetch(`${urlApi()}/v1/salud`, { cache: 'no-store' }); // CONTRATO-HU-04 v4
  if (respuesta.status !== 200) {
    throw new Error(`Salud respondio ${respuesta.status}`);
  }
  return (await respuesta.json()) as SaludRespuesta;
}
