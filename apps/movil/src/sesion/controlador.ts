import type { QueryClient } from '@tanstack/react-query';

import { llamarApi, RespuestaApi } from '../api/cliente';
import {
  cerrarSesionApi,
  iniciarSesion,
  obtenerPerfil,
  Perfil,
  renovarSesion,
  RespuestaSesion,
} from '../api/sesion';
import { Aviso, usarSesion } from '../estado/sesion';
import { borrarTokens, guardarTokens, leerTokenRenovacion } from './almacen';

/**
 * Ciclo de la sesion en la app (CONTRATO-HU-01 §4, ADR-0011, ADR-0013).
 *
 * - Inactividad: un temporizador de `inactividad_s` (lo da el login, no esta fijo en el codigo)
 *   se reinicia con cada interaccion. Al vencer, o ante un 401 SESION_VENCIDA, se cierra la sesion
 *   con el aviso de AUTH-03.
 * - Renovacion: mientras haya interaccion, se renueva el token antes de que venza y con la
 *   frecuencia suficiente para que el servidor no vea la sesion inactiva.
 * - Cierre: se borran SecureStore, la cache de consultas, el store y los tokens en memoria; los
 *   temporizadores se cancelan y ninguna respuesta pendiente de la sesion anterior se usa.
 */

type Sesion = {
  tokenAcceso: string;
  tokenRenovacion: string;
  /** ms epoch en que vence el token de acceso */
  venceAcceso: number;
  inactividadMs: number;
  ultimaInteraccion: number;
  ultimoContacto: number;
};

let sesion: Sesion | null = null;
let generacion = 0;
let temporizador: ReturnType<typeof setTimeout> | null = null;
let renovando = false;
let clienteConsultas: QueryClient | null = null;

export function usarClienteConsultas(cliente: QueryClient): void {
  clienteConsultas = cliente;
}

/**
 * Deja la app como recien abierta, sin tocar el almacenamiento: sin sesion en memoria, sin
 * temporizadores y con el store inicial. Se llama al montar y al desmontar App.
 */
export function reiniciarLocal(): void {
  generacion += 1;
  cancelarTemporizador();
  sesion = null;
  renovando = false;
  usarSesion.setState({ pantalla: 'cargando', perfil: null, aviso: null });
}

function cancelarTemporizador(): void {
  if (temporizador) clearTimeout(temporizador);
  temporizador = null;
}

function programarInactividad(): void {
  cancelarTemporizador();
  if (!sesion) return;
  const restante = sesion.ultimaInteraccion + sesion.inactividadMs - Date.now();
  const actual = generacion;
  temporizador = setTimeout(() => {
    if (actual === generacion) void cerrarSesion({ tipo: 'inactividad' });
  }, Math.max(0, restante));
}

function abrir(respuesta: RespuestaSesion): void {
  const ahora = Date.now();
  sesion = {
    tokenAcceso: respuesta.token_acceso,
    tokenRenovacion: respuesta.token_renovacion,
    venceAcceso: ahora + respuesta.expira_en * 1000,
    inactividadMs: respuesta.inactividad_s * 1000,
    ultimaInteraccion: ahora,
    ultimoContacto: ahora,
  };
  programarInactividad();
}

/** Cierra la sesion local. `aviso` = lo que muestra el login (null = sin mensaje). */
export async function cerrarSesion(aviso: Aviso | null): Promise<void> {
  generacion += 1;
  cancelarTemporizador();
  sesion = null;
  renovando = false;
  clienteConsultas?.clear();
  usarSesion.getState().salir(aviso);
  await borrarTokens();
}

/** "Salir": avisa a la API y cierra sin mensaje (CONTRATO-HU-02 §3). */
export async function salir(): Promise<void> {
  const token = sesion?.tokenAcceso;
  await cerrarSesion(null);
  if (token) {
    try {
      await cerrarSesionApi(token);
    } catch {
      // la sesion local ya esta cerrada; el servidor la vencera por inactividad
    }
  }
}

async function cargarPerfil(actual: number): Promise<Perfil | null> {
  if (!sesion) return null;
  const respuesta = await obtenerPerfil(sesion.tokenAcceso);
  if (actual !== generacion) return null;
  if (respuesta.estado === 200 && respuesta.cuerpo) return respuesta.cuerpo as Perfil;
  return null;
}

/** Login completo: POST /v1/auth/login y luego GET /v1/me (el menu sale de /v1/me). */
export async function ingresar(usuario: string, clave: string): Promise<void> {
  const { avisar, entrar } = usarSesion.getState();
  const actual = generacion;
  try {
    const respuesta = await iniciarSesion(usuario, clave);
    if (actual !== generacion) return;
    if (respuesta.estado === 200 && respuesta.cuerpo) {
      abrir(respuesta.cuerpo as RespuestaSesion);
      await guardarTokens(sesion!.tokenAcceso, sesion!.tokenRenovacion);
      const perfil = await cargarPerfil(actual);
      if (actual !== generacion) return;
      if (perfil) {
        entrar(perfil);
        return;
      }
      await cerrarSesion({ tipo: 'error' });
      return;
    }
    const codigo = respuesta.cuerpo?.codigo;
    if (respuesta.estado === 401 && codigo === 'CREDENCIALES_INVALIDAS') {
      avisar({ tipo: 'credenciales' });
    } else if (respuesta.estado === 423 && codigo === 'CUENTA_BLOQUEADA' && respuesta.cuerpo?.bloqueado_hasta) {
      avisar({ tipo: 'bloqueo', hasta: respuesta.cuerpo.bloqueado_hasta });
    } else {
      avisar({ tipo: 'error' });
    }
  } catch {
    if (actual !== generacion) return;
    if (sesion) {
      await cerrarSesion({ tipo: 'error' });
    } else {
      avisar({ tipo: 'error' });
    }
  }
}

/** Al abrir la app: si quedo una sesion guardada, se intenta retomar; si no, login. */
export async function restaurar(): Promise<void> {
  const actual = generacion;
  const tokenRenovacion = await leerTokenRenovacion();
  if (actual !== generacion) return;
  if (!tokenRenovacion) {
    usarSesion.getState().mostrar('login');
    return;
  }
  try {
    const respuesta = await renovarSesion(tokenRenovacion);
    if (actual !== generacion) return;
    if (respuesta.estado === 200 && respuesta.cuerpo) {
      abrir(respuesta.cuerpo as RespuestaSesion);
      await guardarTokens(sesion!.tokenAcceso, sesion!.tokenRenovacion);
      const perfil = await cargarPerfil(actual);
      if (actual !== generacion) return;
      if (perfil) {
        usarSesion.getState().entrar(perfil);
        return;
      }
    }
    const vencida = respuesta.estado === 401 && respuesta.cuerpo?.codigo === 'SESION_VENCIDA';
    await cerrarSesion(vencida ? { tipo: 'inactividad' } : null);
  } catch {
    if (actual === generacion) await cerrarSesion(null);
  }
}

async function renovar(): Promise<void> {
  if (!sesion || renovando) return;
  renovando = true;
  const actual = generacion;
  try {
    const respuesta = await renovarSesion(sesion.tokenRenovacion);
    if (actual !== generacion || !sesion) return;
    if (respuesta.estado === 200 && respuesta.cuerpo) {
      const datos = respuesta.cuerpo as RespuestaSesion;
      const ahora = Date.now();
      sesion.tokenAcceso = datos.token_acceso;
      sesion.tokenRenovacion = datos.token_renovacion;
      sesion.venceAcceso = ahora + datos.expira_en * 1000;
      sesion.inactividadMs = datos.inactividad_s * 1000;
      sesion.ultimoContacto = ahora;
      await guardarTokens(datos.token_acceso, datos.token_renovacion);
      programarInactividad();
    } else if (respuesta.estado === 401) {
      const vencida = respuesta.cuerpo?.codigo === 'SESION_VENCIDA';
      await cerrarSesion(vencida ? { tipo: 'inactividad' } : null);
    }
  } catch {
    // sin red: se reintenta con la siguiente interaccion
  } finally {
    if (actual === generacion) renovando = false;
  }
}

/** Cada toque en la vista raiz (testID="app-raiz") cuenta como interaccion. */
export function registrarInteraccion(): void {
  if (!sesion) return;
  const ahora = Date.now();
  if (ahora - sesion.ultimaInteraccion >= sesion.inactividadMs) {
    // El temporizador pudo no correr (app en segundo plano): la sesion ya vencio.
    void cerrarSesion({ tipo: 'inactividad' });
    return;
  }
  sesion.ultimaInteraccion = ahora;
  programarInactividad();
  const margenServidor = Math.min(60_000, sesion.inactividadMs / 3);
  const margenToken = Math.min(60_000, (sesion.venceAcceso - sesion.ultimoContacto) / 3);
  if (ahora - sesion.ultimoContacto >= margenServidor || sesion.venceAcceso - ahora <= margenToken) {
    void renovar();
  }
}

/** Al volver del segundo plano: si paso el tiempo de inactividad, se cierra la sesion. */
export function revisarAlVolver(): void {
  if (sesion && Date.now() - sesion.ultimaInteraccion >= sesion.inactividadMs) {
    void cerrarSesion({ tipo: 'inactividad' });
  }
}

/**
 * Llamada autenticada para las pantallas de las HUs siguientes. Maneja 401 (sesion vencida o no
 * autenticada) y 403 SIN_PERMISO (ERR-01). El resto lo decide quien llama.
 */
export async function llamarAutenticado(
  ruta: string,
  opciones: { metodo?: 'GET' | 'POST'; cuerpo?: unknown } = {},
): Promise<RespuestaApi | null> {
  if (!sesion) return null;
  const actual = generacion;
  if (sesion.venceAcceso - Date.now() < 30_000) await renovar();
  if (!sesion || actual !== generacion) return null;
  const respuesta = await llamarApi(ruta, { ...opciones, token: sesion.tokenAcceso });
  if (actual !== generacion) return null;
  if (sesion) sesion.ultimoContacto = Date.now();
  if (respuesta.estado === 401) {
    const vencida = respuesta.cuerpo?.codigo === 'SESION_VENCIDA';
    await cerrarSesion(vencida ? { tipo: 'inactividad' } : null);
    return null;
  }
  if (respuesta.estado === 403 && respuesta.cuerpo?.codigo === 'SIN_PERMISO') {
    usarSesion.getState().mostrar('sin_permiso');
    return null;
  }
  return respuesta;
}
