import { llamarApi, RespuestaApi } from './cliente';
import type { components } from './esquema';

export type RespuestaSesion = components['schemas']['RespuestaSesion'];
export type Perfil = components['schemas']['Perfil'];
export type Rol = Perfil['rol'];

/** POST /v1/auth/login (CONTRATO-HU-01 §1). */
export function iniciarSesion(usuario: string, clave: string): Promise<RespuestaApi> {
  return llamarApi('/v1/auth/login', { metodo: 'POST', cuerpo: { usuario, clave } });
}

/** POST /v1/auth/refresh (CONTRATO-HU-01 §3). */
export function renovarSesion(tokenRenovacion: string): Promise<RespuestaApi> {
  return llamarApi('/v1/auth/refresh', { metodo: 'POST', cuerpo: { token_renovacion: tokenRenovacion } });
}

/** POST /v1/auth/logout (CONTRATO-HU-01 §3). */
export function cerrarSesionApi(tokenAcceso: string): Promise<RespuestaApi> {
  return llamarApi('/v1/auth/logout', { metodo: 'POST', token: tokenAcceso });
}

/** GET /v1/me: el rol sale del servidor (CONTRATO-HU-02 §1). */
export function obtenerPerfil(tokenAcceso: string): Promise<RespuestaApi> {
  return llamarApi('/v1/me', { token: tokenAcceso });
}
