/**
 * CONTRATO-HU-01 v2 §4 y §4 bis, CONTRATO-HU-02 v2 §3 — La app, de caja negra.
 *
 * Interfaz (HU-01 §4 bis): la app completa es el export por defecto de `apps/movil/App.tsx`
 * (sin expo-router); llama a `EXPO_PUBLIC_API_URL + /v1/...` con el `fetch` global; la vista
 * raíz tiene `testID="app-raiz"`; "atrás" es `BackHandler` (`hardwareBackPress`); el token va a
 * `expo-secure-store`.
 *
 * Se simulan: el `fetch` global (un servidor falso por ruta), `expo-secure-store` (en memoria,
 * para ver qué queda guardado) y `BackHandler.addEventListener` (para disparar "atrás").
 * Los campos se encuentran como TextInput: la clave es el que tiene `secureTextEntry`.
 * Escrita para @testing-library/react-native 14 (render y eventos asíncronos).
 */
import React from 'react';
import { BackHandler } from 'react-native';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';

const URL_API = 'https://api.prueba.invalid';
process.env.EXPO_PUBLIC_API_URL = URL_API;

// --- expo-secure-store en memoria -----------------------------------------------------------
const mockAlmacen = new Map<string, string>();
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(async (k: string, v: string) => void mockAlmacen.set(k, v)),
  getItemAsync: jest.fn(async (k: string) => (mockAlmacen.has(k) ? mockAlmacen.get(k)! : null)),
  deleteItemAsync: jest.fn(async (k: string) => void mockAlmacen.delete(k)),
  setItem: jest.fn((k: string, v: string) => void mockAlmacen.set(k, v)),
  getItem: jest.fn((k: string) => (mockAlmacen.has(k) ? mockAlmacen.get(k)! : null)),
  deleteItem: jest.fn((k: string) => void mockAlmacen.delete(k)),
  isAvailableAsync: jest.fn(async () => true),
  AFTER_FIRST_UNLOCK: 0,
  AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY: 1,
  ALWAYS: 2,
  WHEN_PASSCODE_SET_THIS_DEVICE_ONLY: 3,
  ALWAYS_THIS_DEVICE_ONLY: 4,
  WHEN_UNLOCKED: 5,
  WHEN_UNLOCKED_THIS_DEVICE_ONLY: 6,
}));

// eslint-disable-next-line @typescript-eslint/no-var-requires
const App: React.ComponentType = require('../App').default;

jest.setTimeout(60000);
const ESPERA = { timeout: 20000 };

// --- Textos que no se negocian ---------------------------------------------------------------
const T = {
  usuario: 'Usuario',
  clave: 'Clave',
  ingresar: 'Ingresar',
  franja: 'DATOS SINTÉTICOS · PROTOTIPO',
  credenciales: 'Usuario o clave incorrectos',
  inactividad: 'Su sesión se cerró por inactividad. Ingrese de nuevo.',
  otroError: 'No se pudo completar la operación; intente nuevamente',
  salir: 'Salir',
  rolAgente: 'Rol: Agente',
  rolRevisor: 'Rol: Revisor',
  rolSupervisor: 'Rol: Supervisor',
  placa: 'Consultar placa',
  rostro: 'Verificar rostro',
  misVerif: 'Mis verificaciones',
  pendientes: 'Pendientes de revisión',
  bitacora: 'Bitácora',
};

// --- Servidor falso --------------------------------------------------------------------------
type Resp = { estado: number; cuerpo?: unknown } | 'red';
type Llamada = { metodo: string; ruta: string; auth: string | null; cuerpo: unknown };
type Manejador = (ll: Llamada) => Resp;

function respuesta(estado: number, cuerpo?: unknown): Response {
  const texto = cuerpo === undefined ? '' : JSON.stringify(cuerpo);
  const cabeceras = { 'Content-Type': 'application/json', 'X-Id-Traza': 'traza-prueba' };
  if (typeof Response !== 'undefined') {
    return new Response(estado === 204 ? null : texto, { status: estado, headers: cabeceras });
  }
  return {
    ok: estado >= 200 && estado < 300,
    status: estado,
    headers: { get: (k: string) => (cabeceras as Record<string, string>)[k] ?? null },
    json: async () => JSON.parse(texto),
    text: async () => texto,
    clone() {
      return respuesta(estado, cuerpo);
    },
  } as unknown as Response;
}

let llamadas: Llamada[] = [];
let rutas: Record<string, Manejador> = {};

function cabecera(init: RequestInit | undefined, nombre: string): string | null {
  const h = init?.headers as Record<string, string> | Headers | undefined;
  if (!h) return null;
  if (typeof (h as Headers).get === 'function') return (h as Headers).get(nombre);
  const k = Object.keys(h).find((x) => x.toLowerCase() === nombre.toLowerCase());
  return k ? (h as Record<string, string>)[k] : null;
}

const fetchSimulado = jest.fn(async (entrada: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof entrada === 'string' ? entrada : entrada.toString();
  const metodo = (init?.method ?? 'GET').toUpperCase();
  const ruta = url.startsWith(URL_API) ? url.slice(URL_API.length).split('?')[0] : url;
  let cuerpo: unknown = null;
  try {
    cuerpo = init?.body ? JSON.parse(String(init.body)) : null;
  } catch {
    cuerpo = init?.body;
  }
  const ll = { metodo, ruta, auth: cabecera(init, 'Authorization'), cuerpo };
  llamadas.push(ll);
  const m = rutas[`${metodo} ${ruta}`];
  const r: Resp = m ? m(ll) : { estado: 404, cuerpo: { codigo: 'NO_ENCONTRADO', mensaje: 'x', id_traza: 't' } };
  if (r === 'red') throw new TypeError('Network request failed');
  return respuesta(r.estado, r.cuerpo);
});

// --- Datos ---------------------------------------------------------------------------------
type Rol = 'agente' | 'revisor' | 'supervisor';
const PERSONAS: Record<Rol, { id: string; usuario: string; nombre: string }> = {
  agente: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente' },
  revisor: { id: 'u-revisor', usuario: 'revisor1', nombre: 'Raúl Revisor' },
  supervisor: { id: 'u-super', usuario: 'supervisor1', nombre: 'Sara Supervisora' },
};
let secuencia = 0;

function loginOk(rol: Rol, inactividad_s = 600) {
  secuencia += 1;
  return {
    token_acceso: `acceso-${rol}-${secuencia}`,
    token_renovacion: `renov-${rol}-${secuencia}`,
    expira_en: 900,
    inactividad_s,
    usuario: { ...PERSONAS[rol], rol },
  };
}

function errorApi(estado: number, codigo: string, mensaje: string, extra = {}): Resp {
  return { estado, cuerpo: { codigo, mensaje, id_traza: 'traza-prueba', ...extra } };
}

/** Servidor con sesión válida para `rol`; /v1/me devuelve `rolMe` (por defecto el mismo). */
function servidorCon(rol: Rol, opciones: { inactividad_s?: number; rolMe?: Rol } = {}) {
  const tokens = new Set<string>();
  const dar = () => {
    const d = loginOk(rol, opciones.inactividad_s);
    tokens.add(d.token_acceso);
    return d;
  };
  const me = opciones.rolMe ?? rol;
  rutas = {
    'POST /v1/auth/login': () => ({ estado: 200, cuerpo: dar() }),
    'POST /v1/auth/refresh': () => ({ estado: 200, cuerpo: dar() }),
    'POST /v1/auth/logout': () => ({ estado: 204 }),
    'GET /v1/me': (ll) =>
      ll.auth && tokens.has(ll.auth.replace(/^Bearer\s+/i, ''))
        ? { estado: 200, cuerpo: { ...PERSONAS[me], rol: me } }
        : errorApi(401, 'NO_AUTENTICADO', 'Inicie sesión nuevamente'),
  };
  return tokens;
}

// --- BackHandler ---------------------------------------------------------------------------
let oyentesAtras: Array<() => boolean | null | undefined> = [];

async function presionarAtras() {
  await act(async () => {
    for (const f of [...oyentesAtras].reverse()) {
      if (f()) break;
    }
  });
}

// --- Ayudas de pantalla ----------------------------------------------------------------------
function campos() {
  const inputs = screen.root!.queryAll((i) => i.type === 'TextInput');
  const clave = inputs.find((i) => i.props.secureTextEntry);
  const usuario = inputs.find((i) => !i.props.secureTextEntry);
  if (!usuario || !clave) throw new Error(`No se encuentran los campos (hay ${inputs.length})`);
  return { usuario, clave };
}

async function ingresar(usuario: string, clave: string) {
  await waitFor(() => screen.getByText(T.ingresar), ESPERA);
  const c = campos();
  await fireEvent.changeText(c.usuario, usuario);
  await fireEvent.changeText(c.clave, clave);
  await fireEvent.press(screen.getByText(T.ingresar));
}

async function montar() {
  await render(<App />);
}

async function dormir(ms: number) {
  await act(async () => {
    await new Promise((r) => setTimeout(r, ms));
  });
}

beforeEach(() => {
  mockAlmacen.clear();
  llamadas = [];
  rutas = {};
  oyentesAtras = [];
  (global as unknown as { fetch: unknown }).fetch = fetchSimulado;
  fetchSimulado.mockClear();
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation(((_e: string, f: () => boolean) => {
    oyentesAtras.push(f);
    return {
      remove: () => {
        oyentesAtras = oyentesAtras.filter((x) => x !== f);
      },
    };
  }) as unknown as typeof BackHandler.addEventListener);
});

afterEach(() => {
  jest.restoreAllMocks();
});

// =============================================================================================
// HU-01 §4
// =============================================================================================

describe('HU-01 AUTH-01 — login', () => {
  test('sin sesión muestra Usuario, Clave, Ingresar y la franja de datos sintéticos', async () => {
    await montar();
    await waitFor(() => screen.getByText(T.ingresar), ESPERA);
    expect(screen.getByText(T.usuario)).toBeTruthy();
    expect(screen.getByText(T.clave)).toBeTruthy();
    expect(screen.getByText(T.franja)).toBeTruthy();
    expect(screen.getByTestId('app-raiz')).toBeTruthy();
    expect(JSON.stringify(screen.toJSON()).toLowerCase()).not.toContain('identificad');
  });

  test('envía usuario y clave a EXPO_PUBLIC_API_URL + /v1/auth/login con el fetch global', async () => {
    servidorCon('agente');
    await montar();
    await ingresar('agente1', 'clave-buena');
    await waitFor(() => expect(llamadas.some((l) => l.ruta === '/v1/auth/login')).toBe(true), ESPERA);
    const l = llamadas.find((x) => x.ruta === '/v1/auth/login')!;
    expect(l.metodo).toBe('POST');
    expect(l.cuerpo).toEqual({ usuario: 'agente1', clave: 'clave-buena' });
    expect(fetchSimulado.mock.calls.every(([u]) => String(u).startsWith(URL_API))).toBe(true);
  });

  test('login correcto lleva al inicio de su rol y guarda el token en expo-secure-store', async () => {
    servidorCon('agente');
    await montar();
    await ingresar('agente1', 'clave-buena');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    expect(mockAlmacen.size).toBeGreaterThan(0);
  });
});

describe('HU-01 AUTH-02 — usuario o clave incorrectos', () => {
  test('mensaje único, el usuario queda escrito, la clave se vacía, sin intentos restantes', async () => {
    rutas = {
      'POST /v1/auth/login': () =>
        errorApi(401, 'CREDENCIALES_INVALIDAS', 'Usuario o clave incorrectos'),
    };
    await montar();
    await ingresar('agente1', 'clave-mala');
    await waitFor(() => screen.getByText(T.credenciales), ESPERA);
    const c = campos();
    expect(c.usuario.props.value).toBe('agente1');
    expect(c.clave.props.value ?? '').toBe('');
    expect(JSON.stringify(screen.toJSON())).not.toMatch(/intento/i);
    expect(screen.queryByText(T.rolAgente)).toBeNull();
  });
});

describe('HU-01 AUTH-04 — cuenta bloqueada', () => {
  test('muestra la hora local (HH:MM) y los minutos, vacía la clave e Ingresar sigue activo', async () => {
    const hasta = new Date(Date.now() + 15 * 60000);
    hasta.setSeconds(0, 0);
    hasta.setTime(hasta.getTime() + 60000); // minuto entero siguiente: HH:MM sin ambigüedad
    rutas = {
      'POST /v1/auth/login': () =>
        errorApi(423, 'CUENTA_BLOQUEADA', 'Cuenta bloqueada temporalmente', {
          bloqueado_hasta: hasta.toISOString(),
        }),
    };
    await montar();
    await ingresar('agente1', 'cualquiera');
    const hhmm = `${String(hasta.getHours()).padStart(2, '0')}:${String(hasta.getMinutes()).padStart(2, '0')}`;
    const restante = (hasta.getTime() - Date.now()) / 60000;
    const posibles = [Math.floor(restante), Math.ceil(restante)].map(
      (n) => `Cuenta bloqueada temporalmente. Podrá volver a intentar a las ${hhmm} (en ${n} min).`,
    );
    await waitFor(() => {
      const texto = posibles.find((p) => screen.queryByText(p));
      expect(texto).toBeDefined();
    }, ESPERA);
    expect(campos().clave.props.value ?? '').toBe('');
    expect(screen.getByText(T.ingresar)).toBeEnabled();
    expect(screen.queryByText(T.credenciales)).toBeNull();
  });
});

describe('HU-01 — otro error (regla 7)', () => {
  test.each([
    ['error de red', 'red' as Resp],
    ['500', errorApi(500, 'ERROR_INTERNO', 'Error interno')],
    ['503', errorApi(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')],
  ])('%s en el login → mensaje genérico, nunca el de credenciales', async (_n, r) => {
    rutas = { 'POST /v1/auth/login': () => r };
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.otroError), ESPERA);
    expect(screen.queryByText(T.credenciales)).toBeNull();
    expect(screen.queryByText(T.rolAgente)).toBeNull();
  });
});

describe('HU-01 AUTH-03 — sesión cerrada por inactividad', () => {
  test('sin tocar la pantalla durante inactividad_s (del login): vuelve al login con el aviso', async () => {
    servidorCon('agente', { inactividad_s: 2 });
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    await dormir(3500);
    await waitFor(() => screen.getByText(T.inactividad), ESPERA);
    expect(screen.queryByText(T.rolAgente)).toBeNull();
  });

  test('tras el cierre: SecureStore sin claves, atrás no vuelve, otro usuario no ve datos del anterior ni se reenvía el token viejo', async () => {
    const tokensAgente = servidorCon('agente', { inactividad_s: 2 });
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(PERSONAS.agente.nombre, { exact: false }), ESPERA);
    await dormir(3500);
    await waitFor(() => screen.getByText(T.inactividad), ESPERA);

    expect([...mockAlmacen.keys()]).toEqual([]);

    await presionarAtras();
    expect(screen.queryByText(T.rolAgente)).toBeNull();
    expect(screen.queryByText(PERSONAS.agente.nombre, { exact: false })).toBeNull();

    const viejos = new Set(tokensAgente);
    const desde = llamadas.length;
    servidorCon('revisor');
    await ingresar('revisor1', 'clave');
    await waitFor(() => screen.getByText(T.rolRevisor), ESPERA);
    expect(screen.queryByText(PERSONAS.agente.nombre, { exact: false })).toBeNull();
    expect(screen.queryByText(T.rolAgente)).toBeNull();
    expect(screen.queryByText(T.placa)).toBeNull();
    const reenviados = llamadas
      .slice(desde)
      .filter((l) => l.auth && viejos.has(l.auth.replace(/^Bearer\s+/i, '')));
    expect(reenviados).toEqual([]);
  });

  test('un 401 SESION_VENCIDA de la API también cierra la sesión con el aviso', async () => {
    servidorCon('agente');
    rutas['GET /v1/me'] = () => errorApi(401, 'SESION_VENCIDA', 'Su sesión se cerró por inactividad');
    rutas['POST /v1/auth/refresh'] = () =>
      errorApi(401, 'SESION_VENCIDA', 'Su sesión se cerró por inactividad');
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.inactividad), ESPERA);
    expect(screen.queryByText(T.rolAgente)).toBeNull();
    expect([...mockAlmacen.keys()]).toEqual([]);
  });

  test('sesión activa: con touchStart sobre app-raiz la sesión no vence', async () => {
    servidorCon('agente', { inactividad_s: 2 });
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    for (let i = 0; i < 10; i += 1) {
      await fireEvent(screen.getByTestId('app-raiz'), 'touchStart', { nativeEvent: {} });
      await dormir(500);
    }
    expect(screen.getByText(T.rolAgente)).toBeTruthy();
    expect(screen.queryByText(T.inactividad)).toBeNull();
  });
});

// =============================================================================================
// HU-02 §3
// =============================================================================================

describe('HU-02 — inicio por rol', () => {
  test('agente (HOME-01): saludo, rol, Salir, sus tres opciones deshabilitadas y nada de otros roles', async () => {
    servidorCon('agente');
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    expect(screen.getByText(`Hola, ${PERSONAS.agente.nombre}`, { exact: false })).toBeTruthy();
    expect(screen.getByText(T.salir)).toBeTruthy();
    for (const t of [T.placa, T.rostro, T.misVerif]) expect(screen.getByText(t)).toBeDisabled();
    expect(screen.queryByText(T.pendientes)).toBeNull();
    expect(screen.queryByText(T.bitacora)).toBeNull();
  });

  test('revisor: "Pendientes de revisión" (deshabilitada), nada de consulta ni bitácora', async () => {
    servidorCon('revisor');
    await montar();
    await ingresar('revisor1', 'clave');
    await waitFor(() => screen.getByText(T.rolRevisor), ESPERA);
    expect(screen.getByText(`Hola, ${PERSONAS.revisor.nombre}`, { exact: false })).toBeTruthy();
    expect(screen.getByText(T.salir)).toBeTruthy();
    expect(screen.getByText(T.pendientes)).toBeDisabled();
    for (const t of [T.placa, T.rostro, T.misVerif, T.bitacora]) expect(screen.queryByText(t)).toBeNull();
  });

  test('supervisor: "Bitácora" (deshabilitada), nada de consulta ni revisión', async () => {
    servidorCon('supervisor');
    await montar();
    await ingresar('supervisor1', 'clave');
    await waitFor(() => screen.getByText(T.rolSupervisor), ESPERA);
    expect(screen.getByText(`Hola, ${PERSONAS.supervisor.nombre}`, { exact: false })).toBeTruthy();
    expect(screen.getByText(T.salir)).toBeTruthy();
    expect(screen.getByText(T.bitacora)).toBeDisabled();
    for (const t of [T.placa, T.rostro, T.misVerif, T.pendientes]) expect(screen.queryByText(t)).toBeNull();
  });

  test('el menú sale de GET /v1/me (con el token), no de un valor guardado', async () => {
    servidorCon('agente', { rolMe: 'revisor' });
    await montar();
    await ingresar('agente1', 'clave');
    await waitFor(() => screen.getByText(T.rolRevisor), ESPERA);
    expect(screen.queryByText(T.placa)).toBeNull();
    const me = llamadas.find((l) => l.ruta === '/v1/me');
    expect(me?.auth).toMatch(/^Bearer acceso-agente-/);
  });

  test('Salir: POST /v1/auth/logout con el token, SecureStore vacío y AUTH-01 sin mensaje', async () => {
    servidorCon('supervisor');
    await montar();
    await ingresar('supervisor1', 'clave');
    await waitFor(() => screen.getByText(T.rolSupervisor), ESPERA);
    await fireEvent.press(screen.getByText(T.salir));
    await waitFor(() => screen.getByText(T.ingresar), ESPERA);
    const salida = llamadas.find((l) => l.ruta === '/v1/auth/logout');
    expect(salida?.metodo).toBe('POST');
    expect(salida?.auth).toMatch(/^Bearer acceso-supervisor-/);
    await waitFor(() => expect([...mockAlmacen.keys()]).toEqual([]), ESPERA);
    for (const t of [T.inactividad, T.credenciales, T.otroError]) expect(screen.queryByText(t)).toBeNull();
    await presionarAtras();
    expect(screen.queryByText(T.rolSupervisor)).toBeNull();
  });
});
