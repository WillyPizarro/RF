import type { RespuestaApi } from './cliente';
import type { components } from './esquema';
import { llamarAutenticado } from '../sesion/controlador';

export type RespuestaMotivos = components['schemas']['RespuestaMotivos'];
export type Motivo = components['schemas']['Motivo'];
export type FormatoPlaca = components['schemas']['FormatoPlaca'];
export type RespuestaConsultaPlaca = components['schemas']['RespuestaConsultaPlaca'];
export type ResultadoPlaca = RespuestaConsultaPlaca['resultado'];

/**
 * GET /v1/motivos (CONTRATO-HU-03 v3 §1): catalogo y formato de placa vigentes.
 * null = la sesion ya resolvio la respuesta (401 al login, 403 a ERR-01). Un error de red lanza.
 */
export function obtenerMotivos(): Promise<RespuestaApi | null> {
  return llamarAutenticado('/v1/motivos');
}

/** POST /v1/consultas/placa (CONTRATO-HU-03 §2). Mismo contrato de retorno que obtenerMotivos. */
export function consultarPlaca(
  placa: string,
  motivoCodigo: string,
  motivoTexto: string | null,
): Promise<RespuestaApi | null> {
  return llamarAutenticado('/v1/consultas/placa', {
    metodo: 'POST',
    cuerpo: { placa, motivo_codigo: motivoCodigo, motivo_texto: motivoTexto },
  });
}
