/**
 * CONTRATO-HU-03 v4 §6 (PLA-01 a PLA-08, ERR-01, PLA-01 sin catálogo) y CONTRATO-HU-07 v3 §5
 * (BIT-01 con sus filtros, BIT-02).
 * El caso pendiente de HU-01 (retomar la sesión) está en HU01_retomar_*.test.tsx: un archivo por
 * variante, para que cada una arranque con la app recién cargada (la app guarda estado en
 * memoria de módulo y Jest da un registro de módulos limpio por archivo).
 *
 * Interfaz (HU-01 §4 bis): export por defecto de `App.tsx`, `fetch` global con
 * `EXPO_PUBLIC_API_URL`, `testID="app-raiz"`, token en `expo-secure-store` (simulado en memoria).
 * El selector de motivo no tiene forma fijada: se toca el texto del motivo y, si no está a la
 * vista, primero la etiqueta "Motivo de consulta *" para abrirlo.
 * Escrita para @testing-library/react-native 14 (render y eventos asíncronos).
 */
import React from 'react';
import { BackHandler } from 'react-native';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';

const URL_API = 'https://api.prueba.invalid';
process.env.EXPO_PUBLIC_API_URL = URL_API;

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
  ingresar: 'Ingresar',
  rolAgente: 'Rol: Agente',
  rolSupervisor: 'Rol: Supervisor',
  inactividad: 'Su sesión se cerró por inactividad. Ingrese de nuevo.',
  consultarPlaca: 'Consultar placa',
  verificarRostro: 'Verificar rostro',
  bitacora: 'Bitácora',
  placa: 'Placa',
  motivo: 'Motivo de consulta *',
  describa: 'Describa el motivo *',
  consultar: 'Consultar',
  sinMotivo: 'Indique el motivo de la consulta.',
  otroCorto: 'Describa el motivo (mínimo 10 caracteres).',
  formato: 'El formato de placa no es válido. Formato esperado: ',
  consultando: 'Consultando…',
  tiene: 'TIENE REQUISITORIA',
  sinReq: 'Sin requisitoria registrada en la fuente consultada',
  noReg: 'Placa no registrada en la fuente consultada. Verifique la placa.',
  errorConsulta: 'No se pudo completar la consulta; intente nuevamente',
  reintentar: 'Reintentar',
  volver: 'Volver',
  nueva: 'Nueva consulta',
  sinPermiso: 'No tiene permiso para usar esta función.',
  registrado: 'El intento quedó registrado.',
  volverInicio: 'Volver al inicio',
  sintetico: 'SINTÉTICO',
  pa24: 'PA 24',
  sistema: 'sistema',
  cargarMas: 'Cargar más',
  soloLectura: 'Registro de solo lectura',
  origen: 'Origen: datos sintéticos',
  errorBitacora: 'No se pudo cargar la bitácora; intente nuevamente',
  vacia: 'No hay registros para estos filtros.',
  idCampo: 'ID',
  aplicar: 'Aplicar filtros',
  ayudaFecha: 'dd/mm/aaaa',
  fechaInvalida: 'Use fechas con el formato dd/mm/aaaa.',
};

// --- Servidor falso --------------------------------------------------------------------------
type Resp = { estado: number; cuerpo?: unknown } | 'red' | Promise<{ estado: number; cuerpo?: unknown }>;
type Llamada = { metodo: string; ruta: string; query: string; auth: string | null; cuerpo: unknown };
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
  const resto = url.startsWith(URL_API) ? url.slice(URL_API.length) : url;
  const [ruta, query = ''] = resto.split('?');
  let cuerpo: unknown = null;
  try {
    cuerpo = init?.body ? JSON.parse(String(init.body)) : null;
  } catch {
    cuerpo = init?.body;
  }
  const ll = { metodo, ruta, query, auth: cabecera(init, 'Authorization'), cuerpo };
  llamadas.push(ll);
  const m = rutas[`${metodo} ${ruta}`];
  const r = m ? await m(ll) : { estado: 404, cuerpo: { codigo: 'NO_ENCONTRADO', mensaje: 'x', id_traza: 't' } };
  if (r === 'red') throw new TypeError('Network request failed');
  return respuesta(r.estado, r.cuerpo);
});

const err = (estado: number, codigo: string, mensaje: string) => ({
  estado,
  cuerpo: { codigo, mensaje, id_traza: 'traza-prueba' },
});

type Rol = 'agente' | 'revisor' | 'supervisor';
const PERSONAS: Record<Rol, { id: string; usuario: string; nombre: string }> = {
  agente: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente' },
  revisor: { id: 'u-revisor', usuario: 'revisor1', nombre: 'Raúl Revisor' },
  supervisor: { id: 'u-super', usuario: 'supervisor1', nombre: 'Sara Supervisora' },
};

const MOTIVOS = [
  { codigo: 'control_vehicular', descripcion: 'Control vehicular' },
  { codigo: 'intervencion_policial', descripcion: 'Intervención policial' },
  { codigo: 'denuncia', descripcion: 'Denuncia' },
  { codigo: 'operativo', descripcion: 'Operativo' },
  { codigo: 'otro', descripcion: 'Otro' },
];
const FORMATO = { regex: '^[A-Z0-9]{3}-[0-9]{3}$', descripcion: 'ABC-123 (3 letras o números, guion, 3 números)' };

let secuencia = 0;
function servidor(rol: Rol, formato = FORMATO) {
  const tokens = new Set<string>();
  const dar = () => {
    secuencia += 1;
    const d = {
      token_acceso: `acceso-${rol}-${secuencia}`,
      token_renovacion: `renov-${rol}-${secuencia}`,
      expira_en: 900,
      inactividad_s: 600,
      usuario: { ...PERSONAS[rol], rol },
    };
    tokens.add(d.token_acceso);
    return d;
  };
  rutas = {
    'POST /v1/auth/login': () => ({ estado: 200, cuerpo: dar() }),
    'POST /v1/auth/refresh': () => ({ estado: 200, cuerpo: dar() }),
    'POST /v1/auth/logout': () => ({ estado: 204 }),
    'GET /v1/me': (ll) =>
      ll.auth && tokens.has(ll.auth.replace(/^Bearer\s+/i, ''))
        ? { estado: 200, cuerpo: { ...PERSONAS[rol], rol } }
        : err(401, 'NO_AUTENTICADO', 'Inicie sesión nuevamente'),
    'GET /v1/motivos': () => ({ estado: 200, cuerpo: { motivos: MOTIVOS, formato_placa: formato } }),
  };
}

const CONSULTADO_EN = '2026-11-19T15:04:00Z';
function resultadoPlaca(placa: string, resultado: string, motivo = 'control_vehicular', texto: string | null = null) {
  return {
    estado: 200,
    cuerpo: {
      consulta_id: 'c-1',
      placa,
      resultado,
      motivo: { codigo: motivo, texto },
      consultado_en: CONSULTADO_EN,
    },
  };
}

// --- BackHandler ---------------------------------------------------------------------------
let oyentesAtras: Array<() => boolean | null | undefined> = [];

// --- Ayudas de pantalla ----------------------------------------------------------------------
function inputs() {
  return screen.root!.queryAll((i) => i.type === 'TextInput');
}

async function entrar(rol: Rol) {
  await render(<App />);
  await waitFor(() => screen.getByText(T.ingresar), ESPERA);
  const ins = inputs();
  await fireEvent.changeText(ins.find((i) => !i.props.secureTextEntry)!, PERSONAS[rol].usuario);
  await fireEvent.changeText(ins.find((i) => i.props.secureTextEntry)!, 'clave');
  await fireEvent.press(screen.getByText(T.ingresar));
}

async function abrirPla01() {
  await entrar('agente');
  await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
  await fireEvent.press(screen.getByText(T.consultarPlaca));
  await waitFor(() => screen.getByText(T.motivo), ESPERA);
}

function campoPlaca() {
  const ins = inputs();
  const p = ins.find(
    (i) =>
      i.props.accessibilityLabel === T.placa ||
      i.props['aria-label'] === T.placa ||
      i.props.placeholder === T.placa,
  );
  return p ?? ins[0];
}

async function escribirPlaca(texto: string) {
  await fireEvent.changeText(campoPlaca(), texto);
}

async function elegirMotivo(descripcion: string) {
  if (!screen.queryByText(descripcion)) {
    await fireEvent.press(screen.getByText(T.motivo));
  }
  await waitFor(() => screen.getByText(descripcion), ESPERA);
  const todos = screen.getAllByText(descripcion);
  await fireEvent.press(todos[todos.length - 1]);
}

async function consultar() {
  await fireEvent.press(screen.getByText(T.consultar));
}

const posts = () => llamadas.filter((l) => l.metodo === 'POST' && l.ruta === '/v1/consultas/placa');
const arbol = () => JSON.stringify(screen.toJSON());

beforeEach(() => {
  mockAlmacen.clear();
  llamadas = [];
  rutas = {};
  oyentesAtras = [];
  (global as unknown as { fetch: unknown }).fetch = fetchSimulado;
  fetchSimulado.mockClear();
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation(((_e: string, f: () => boolean) => {
    oyentesAtras.push(f);
    return { remove: () => (oyentesAtras = oyentesAtras.filter((x) => x !== f)) };
  }) as unknown as typeof BackHandler.addEventListener);
});

afterEach(() => {
  jest.restoreAllMocks();
});

// =============================================================================================
// HU-03 §6
// =============================================================================================

describe('HU-03 — acceso y PLA-01', () => {
  test('HOME-01: "Consultar placa" habilitada; "Verificar rostro" sigue deshabilitada', async () => {
    servidor('agente');
    await entrar('agente');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    expect(screen.getByText(T.consultarPlaca)).toBeEnabled();
    expect(screen.getByText(T.verificarRostro)).toBeDisabled();
  });

  test('PLA-01: campo Placa, selector con el catálogo de /v1/motivos, Consultar; "Describa el motivo *" solo con Otro', async () => {
    servidor('agente');
    await abrirPla01();
    expect(screen.getByText(T.placa)).toBeTruthy();
    expect(screen.getByText(T.consultar)).toBeTruthy();
    expect(llamadas.some((l) => l.metodo === 'GET' && l.ruta === '/v1/motivos')).toBe(true);
    expect(screen.queryByText(T.describa)).toBeNull();
    for (const m of MOTIVOS.slice(0, 4)) {
      await elegirMotivo(m.descripcion);
      expect(screen.queryByText(T.describa)).toBeNull();
    }
    await elegirMotivo('Otro');
    await waitFor(() => screen.getByText(T.describa), ESPERA);
  });

  test('PLA-01: el campo Placa va en mayúsculas y con fuente monoespaciada', async () => {
    servidor('agente');
    await abrirPla01();
    await escribirPlaca('zza-101');
    const campo = campoPlaca();
    const mayus = campo.props.autoCapitalize === 'characters' || campo.props.value === 'ZZA-101';
    expect(mayus).toBe(true);
    const estilo = [campo.props.style].flat(Infinity).filter(Boolean) as Array<Record<string, unknown>>;
    const fuente = estilo.map((e) => String(e.fontFamily ?? '')).join(' ');
    expect(fuente).toMatch(/mono|courier/i);
  });
});

describe('HU-03 v4 — PLA-01 sin catálogo', () => {
  test.each([
    ['503', () => err(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')],
    ['error de red', () => 'red' as const],
    ['respuesta inesperada', () => ({ estado: 200, cuerpo: { otra: 'cosa' } })],
  ])('GET /v1/motivos con %s → error de PLA-07, no se puede consultar; "Reintentar" vuelve a pedir el catálogo', async (_n, falla) => {
    servidor('agente');
    let veces = 0;
    rutas['GET /v1/motivos'] = (ll) =>
      ++veces === 1 ? (falla as Manejador)(ll) : { estado: 200, cuerpo: { motivos: MOTIVOS, formato_placa: FORMATO } };
    await entrar('agente');
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    await fireEvent.press(screen.getByText(T.consultarPlaca));
    await waitFor(() => screen.getByText(T.errorConsulta), ESPERA);
    expect(screen.getByText(T.reintentar)).toBeTruthy();
    expect(screen.getByText(T.volver)).toBeTruthy();
    const boton = screen.queryByText(T.consultar);
    if (boton) {
      expect(boton).toBeDisabled();
      await fireEvent.press(boton);
    }
    expect(posts()).toEqual([]);
    expect(arbol()).not.toMatch(/sin requisitoria/i);
    await fireEvent.press(screen.getByText(T.reintentar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(veces).toBe(2);
    expect(screen.queryByText(T.errorConsulta)).toBeNull();
  });
});

describe('HU-03 — validación local (no se envía nada)', () => {
  test('PLA-02: sin motivo → "Indique el motivo de la consulta." y ningún POST', async () => {
    servidor('agente');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await consultar();
    await waitFor(() => screen.getByText(T.sinMotivo), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('PLA-02: "Otro" con menos de 10 caracteres → aviso y ningún POST', async () => {
    servidor('agente');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Otro');
    await waitFor(() => screen.getByText(T.describa), ESPERA);
    const ins = inputs();
    await fireEvent.changeText(ins[ins.length - 1], 'corto');
    await consultar();
    await waitFor(() => screen.getByText(T.otroCorto), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('PLA-03: formato inválido → mensaje con la descripción de /v1/motivos, sin enviar', async () => {
    servidor('agente', { regex: FORMATO.regex, descripcion: 'DESCRIPCION-QUE-MANDA-LA-API' });
    await abrirPla01();
    await escribirPlaca('HOLA MUNDO');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.formato + 'DESCRIPCION-QUE-MANDA-LA-API'), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('PLA-03: la app valida con formato_placa.regex de la API, no con uno fijo', async () => {
    servidor('agente', { regex: '^ZZ[A-Z]-[0-9]{3}$', descripcion: 'ZZX-999' });
    await abrirPla01();
    await escribirPlaca('ZZ1-101'); // vale con el formato por defecto, no con el de la API
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.formato + 'ZZX-999'), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('PLA-03: sin motivo y con formato inválido se muestran los dos mensajes', async () => {
    servidor('agente');
    await abrirPla01();
    await escribirPlaca('HOLA');
    await consultar();
    await waitFor(() => screen.getByText(T.sinMotivo), ESPERA);
    expect(screen.getByText(T.formato + FORMATO.descripcion)).toBeTruthy();
    expect(posts()).toEqual([]);
  });

  test('PLA-03: si la API rechaza el formato (422), se muestra su mensaje', async () => {
    servidor('agente', { regex: '^.+$', descripcion: 'cualquiera' });
    rutas['POST /v1/consultas/placa'] = () =>
      err(422, 'PLACA_FORMATO_INVALIDO', 'El formato de placa no es válido. Formato esperado: DESDE-EL-422');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.formato + 'DESDE-EL-422', { exact: false }), ESPERA);
    expect(screen.queryByText(T.sinReq)).toBeNull();
  });
});

describe('HU-03 — consulta y resultados', () => {
  test('envía placa, motivo_codigo y motivo_texto a POST /v1/consultas/placa con el token', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => resultadoPlaca('ZZA-101', 'con_requisitoria');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => expect(posts().length).toBe(1), ESPERA);
    const p = posts()[0];
    expect(p.auth).toMatch(/^Bearer acceso-agente-/);
    expect(p.cuerpo).toMatchObject({ placa: 'ZZA-101', motivo_codigo: 'control_vehicular' });
    expect((p.cuerpo as Record<string, unknown>).motivo_texto ?? null).toBeNull();
  });

  test('PLA-04: "Consultando…" con la placa y el botón desactivado (no se envía dos veces)', async () => {
    servidor('agente');
    let soltar: (v: { estado: number; cuerpo?: unknown }) => void = () => undefined;
    rutas['POST /v1/consultas/placa'] = () => new Promise((r) => (soltar = r));
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.consultando, { exact: false }), ESPERA);
    expect(arbol()).toContain('ZZA-101');
    const boton = screen.queryByText(T.consultar);
    if (boton) {
      expect(boton).toBeDisabled();
      await fireEvent.press(boton);
    }
    expect(posts().length).toBe(1);
    await act(async () => soltar(resultadoPlaca('ZZA-101', 'con_requisitoria')));
    await waitFor(() => screen.getByText(T.tiene), ESPERA);
  });

  test('PLA-05: con_requisitoria → TIENE REQUISITORIA, placa, Motivo:, Consultado: dd/mm/aaaa hh:mm local, Nueva consulta', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => resultadoPlaca('ZZA-101', 'con_requisitoria');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.tiene), ESPERA);
    const d = new Date(CONSULTADO_EN);
    const p2 = (n: number) => String(n).padStart(2, '0');
    const fecha = `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()} ${p2(d.getHours())}:${p2(d.getMinutes())}`;
    expect(arbol()).toContain('ZZA-101');
    expect(screen.getByText(/^Motivo:/)).toBeTruthy();
    expect(screen.getByText(`Consultado: ${fecha}`, { exact: false })).toBeTruthy();
    expect(screen.getByText(T.nueva)).toBeTruthy();
    expect(screen.queryByText(T.sinReq)).toBeNull();
    for (const dato of ['marca', 'modelo', 'autoridad']) expect(arbol().toLowerCase()).not.toContain(dato);
    expect(arbol().toLowerCase()).not.toContain('identificad');
  });

  test('PLA-06: sin_requisitoria → texto neutro, sin ✓', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => resultadoPlaca('ZZB-201', 'sin_requisitoria');
    await abrirPla01();
    await escribirPlaca('ZZB-201');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.sinReq, { exact: false }), ESPERA);
    expect(arbol()).toContain('ZZB-201');
    expect(arbol()).not.toMatch(/[✓✔☑]/);
    expect(screen.queryByText(T.tiene)).toBeNull();
  });

  test('PLA-08: placa_no_registrada → su texto, distinto de PLA-06, sin ✓', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => resultadoPlaca('ZZZ-999', 'placa_no_registrada');
    await abrirPla01();
    await escribirPlaca('ZZZ-999');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.noReg, { exact: false }), ESPERA);
    expect(screen.queryByText(T.sinReq, { exact: false })).toBeNull();
    expect(arbol()).not.toMatch(/[✓✔☑]/);
  });

  test.each([
    ['503 FUENTE_NO_DISPONIBLE', () => err(503, 'FUENTE_NO_DISPONIBLE', 'No se pudo completar la consulta; intente nuevamente')],
    ['502 FUENTE_RESPUESTA_INVALIDA', () => err(502, 'FUENTE_RESPUESTA_INVALIDA', 'No se pudo completar la consulta; intente nuevamente')],
    ['503 SERVICIO_NO_DISPONIBLE', () => err(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')],
    ['error de red', () => 'red' as const],
    ['500 inesperado', () => err(500, 'ERROR_INTERNO', 'x')],
    ['200 con resultado desconocido', () => resultadoPlaca('ZZA-101', 'otra_cosa')],
  ])('PLA-07: %s → mensaje de error, Reintentar y Volver; nunca "sin requisitoria"', async (_n, r) => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = r as Manejador;
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.errorConsulta), ESPERA);
    expect(screen.getByText(T.reintentar)).toBeTruthy();
    expect(screen.getByText(T.volver)).toBeTruthy();
    expect(arbol()).not.toMatch(/sin requisitoria/i);
    expect(screen.queryByText(T.noReg, { exact: false })).toBeNull();
    expect(screen.queryByText(T.tiene)).toBeNull();
  });

  test('PLA-07: "Reintentar" vuelve a enviar la misma placa y el mismo motivo', async () => {
    servidor('agente');
    let n = 0;
    rutas['POST /v1/consultas/placa'] = () =>
      ++n === 1
        ? err(503, 'FUENTE_NO_DISPONIBLE', 'No se pudo completar la consulta; intente nuevamente')
        : resultadoPlaca('ZZA-101', 'con_requisitoria');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.reintentar), ESPERA);
    await fireEvent.press(screen.getByText(T.reintentar));
    await waitFor(() => expect(posts().length).toBe(2), ESPERA);
    expect(posts()[1].cuerpo).toMatchObject({ placa: 'ZZA-101', motivo_codigo: 'control_vehicular' });
  });

  test('403 SIN_PERMISO → ERR-01; "Volver al inicio" lleva al inicio del rol', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => err(403, 'SIN_PERMISO', 'No tiene permiso para usar esta función');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.sinPermiso), ESPERA);
    expect(screen.getByText(T.registrado)).toBeTruthy();
    await fireEvent.press(screen.getByText(T.volverInicio));
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
  });

  test('nada en el dispositivo: el resultado no queda en SecureStore', async () => {
    servidor('agente');
    rutas['POST /v1/consultas/placa'] = () => resultadoPlaca('ZZA-101', 'con_requisitoria');
    await abrirPla01();
    await escribirPlaca('ZZA-101');
    await elegirMotivo('Control vehicular');
    await consultar();
    await waitFor(() => screen.getByText(T.tiene), ESPERA);
    const guardado = [...mockAlmacen.entries()].map(([k, v]) => `${k}=${v}`).join('\n');
    expect(guardado).not.toMatch(/ZZA-101|con_requisitoria|c-1/);
  });
});

// =============================================================================================
// HU-07 §5
// =============================================================================================

/** UUID determinista a partir de un número (la columna `id` de `bitacora` es uuid). */
function uuid(n: number) {
  const h = n.toString(16).padStart(8, '0');
  return `${h}-0000-4000-8000-${h.padStart(12, '0')}`;
}

function registro(n: number, tipo: string, extra: Record<string, unknown> = {}) {
  return {
    id: uuid(n),
    ocurrido_en: '2026-11-19T15:04:00Z',
    usuario: 'agente1',
    rol: 'agente',
    tipo_evento: tipo,
    motivo: null,
    parametros: {},
    resultado: null,
    score: null,
    captura_id: null,
    consulta_id: null,
    codigo_error: null,
    es_sintetico: true,
    ...extra,
  };
}

const ETIQUETAS_TIPO: Record<string, string> = {
  LOGIN_OK: 'Inicio de sesión',
  LOGIN_FALLIDO: 'Intento fallido',
  CUENTA_BLOQUEADA: 'Cuenta bloqueada',
  LOGOUT: 'Cierre de sesión',
  SESION_VENCIDA: 'Sesión vencida',
  ACCESO_DENEGADO: 'Acceso denegado',
  CONSULTA_PLACA: 'Consulta de placa',
  ERROR_FUENTE: 'Error de fuente',
  CONSULTA_BITACORA: 'Consulta de bitácora',
};
const ETIQUETAS_RESULTADO: Record<string, string> = {
  con_requisitoria: 'Tiene requisitoria',
  sin_requisitoria: 'Sin requisitoria registrada',
  placa_no_registrada: 'Placa no registrada',
  error: 'Error',
};

function campoTexto(etiqueta: string) {
  const c = inputs().find(
    (i) =>
      i.props.accessibilityLabel === etiqueta ||
      i.props['aria-label'] === etiqueta ||
      i.props.placeholder === etiqueta,
  );
  if (!c) throw new Error(`No se encuentra el campo "${etiqueta}" (sin etiqueta accesible ni ayuda con ese texto)`);
  return c;
}

/** "Desde" y "Hasta": por etiqueta accesible; si no la tienen, por orden entre los campos con la ayuda dd/mm/aaaa. */
function campoFecha(etiqueta: 'Desde' | 'Hasta') {
  const ins = inputs();
  const porEtiqueta = ins.find((i) => i.props.accessibilityLabel === etiqueta || i.props['aria-label'] === etiqueta);
  if (porEtiqueta) return porEtiqueta;
  const fechas = ins.filter((i) => i.props.placeholder === T.ayudaFecha);
  if (fechas.length < 2) throw new Error('No se encuentran los campos de fecha');
  return fechas[etiqueta === 'Desde' ? 0 : 1];
}

async function abrirBitacora(manejador: Manejador) {
  servidor('supervisor');
  rutas['GET /v1/bitacora'] = manejador;
  await entrar('supervisor');
  await waitFor(() => screen.getByText(T.rolSupervisor), ESPERA);
  expect(screen.getByText(T.bitacora)).toBeEnabled();
  await fireEvent.press(screen.getByText(T.bitacora));
}

describe('HU-07 — BIT-01 y BIT-02', () => {
  test('BIT-01: una tarjeta por registro con fecha dd/mm hh:mm, usuario o "sistema", etiqueta, resultado y SINTÉTICO; PA 24; sin editar/borrar/exportar', async () => {
    const tipos = Object.keys(ETIQUETAS_TIPO);
    const regs = tipos.map((t, i) =>
      registro(100 - i, t, {
        // Solo un LOGIN_FALLIDO de un usuario inexistente va sin usuario ("sistema"). CONSULTA_PLACA
        // y ERROR_FUENTE llevan usuario, motivo, placa y consulta_id (HU-07 §2, M-2).
        usuario: t === 'LOGIN_FALLIDO' ? null : 'agente1',
        resultado: t === 'CONSULTA_PLACA' ? 'con_requisitoria' : t === 'ERROR_FUENTE' ? 'error' : null,
        ...(t === 'CONSULTA_PLACA' || t === 'ERROR_FUENTE'
          ? {
              motivo: 'control_vehicular',
              parametros: t === 'ERROR_FUENTE' ? { placa: 'ZZA-101', fuente: 'placas' } : { placa: 'ZZA-101' },
              consulta_id: `c-${i}`,
              codigo_error: t === 'ERROR_FUENTE' ? 'FUENTE_NO_DISPONIBLE' : null,
            }
          : {}),
      }),
    );
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: regs, siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(ETIQUETAS_TIPO.LOGIN_OK), ESPERA);
    for (const etiqueta of Object.values(ETIQUETAS_TIPO)) expect(screen.getByText(etiqueta)).toBeTruthy();
    expect(screen.getByText(ETIQUETAS_RESULTADO.con_requisitoria)).toBeTruthy();
    expect(screen.getAllByText(T.sintetico).length).toBe(regs.length);
    expect(screen.getAllByText(T.sistema, { exact: false }).length).toBeGreaterThan(0);
    const d = new Date('2026-11-19T15:04:00Z');
    const p2 = (n: number) => String(n).padStart(2, '0');
    expect(screen.getAllByText(`${p2(d.getDate())}/${p2(d.getMonth() + 1)} ${p2(d.getHours())}:${p2(d.getMinutes())}`, { exact: false }).length).toBeGreaterThan(0);
    expect(screen.getAllByText(T.pa24, { exact: false }).length).toBeGreaterThan(0);
    expect(arbol()).not.toMatch(/editar|borrar|eliminar|exportar/i);
    expect(screen.queryByText(T.cargarMas)).toBeNull();
  });

  test('BIT-01: etiquetas de resultado', async () => {
    const regs = Object.keys(ETIQUETAS_RESULTADO).map((r, i) =>
      registro(50 - i, r === 'error' ? 'ERROR_FUENTE' : 'CONSULTA_PLACA', { resultado: r }),
    );
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: regs, siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(ETIQUETAS_RESULTADO.con_requisitoria), ESPERA);
    for (const e of Object.values(ETIQUETAS_RESULTADO)) expect(screen.getAllByText(e).length).toBeGreaterThan(0);
  });

  test('BIT-01: "Cargar más" pide la página siguiente con el cursor y la agrega', async () => {
    await abrirBitacora((ll) =>
      /cursor=CUR-2/.test(ll.query)
        ? { estado: 200, cuerpo: { registros: [registro(1, 'LOGOUT')], siguiente_cursor: null } }
        : { estado: 200, cuerpo: { registros: [registro(2, 'LOGIN_OK')], siguiente_cursor: 'CUR-2' } },
    );
    await waitFor(() => screen.getByText(T.cargarMas), ESPERA);
    await fireEvent.press(screen.getByText(T.cargarMas));
    await waitFor(() => screen.getByText(ETIQUETAS_TIPO.LOGOUT), ESPERA);
    expect(screen.getByText(ETIQUETAS_TIPO.LOGIN_OK)).toBeTruthy();
    expect(screen.queryByText(T.cargarMas)).toBeNull();
  });

  test('BIT-02 (v3): "Registro #<8 primeros del id>", "ID" con el id completo, solo lectura; sin "ID de captura" ni "Score"', async () => {
    const r = registro(0x77abcdef, 'ERROR_FUENTE', {
      motivo: 'control_vehicular',
      resultado: 'error',
      codigo_error: 'FUENTE_NO_DISPONIBLE',
      parametros: { placa: 'ZZA-101', fuente: 'placas' },
      consulta_id: 'c-77',
    });
    const id = String(r.id);
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: [r], siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(ETIQUETAS_TIPO.ERROR_FUENTE), ESPERA);
    await fireEvent.press(screen.getByText(ETIQUETAS_TIPO.ERROR_FUENTE));
    await waitFor(() => screen.getByText(`Registro #${id.slice(0, 8)}`, { exact: false }), ESPERA);
    expect(screen.queryByText(`Registro #${id}`, { exact: false })).toBeNull();
    expect(screen.getByText(T.idCampo)).toBeTruthy();
    expect(screen.getByText(id, { exact: false })).toBeTruthy();
    expect(screen.getByText(T.soloLectura)).toBeTruthy();
    expect(screen.getByText(T.origen, { exact: false })).toBeTruthy();
    expect(arbol()).toContain('FUENTE_NO_DISPONIBLE');
    expect(arbol()).toContain('agente1');
    expect(arbol()).not.toMatch(/ID de captura|Score/);
  });

  test('BIT-01 (v3): filtros con "Filtros", "Usuario", "Desde", "Hasta", "Tipo", "Resultado", ayuda dd/mm/aaaa y "Aplicar filtros"', async () => {
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: [registro(1, 'LOGIN_OK')], siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(T.aplicar), ESPERA);
    for (const t of ['Filtros', 'Usuario', 'Desde', 'Hasta', 'Tipo', 'Resultado']) {
      expect(screen.getAllByText(t).length).toBeGreaterThan(0);
    }
    const ayudas =
      screen.queryAllByText(T.ayudaFecha, { exact: false }).length +
      inputs().filter((i) => i.props.placeholder === T.ayudaFecha).length;
    expect(ayudas).toBeGreaterThanOrEqual(2); // en "Desde" y en "Hasta"
  });

  test.each(['2026-11-19', '19-11-2026', '32/13/2026', 'ayer'])(
    'BIT-01 (v3): fecha inválida "%s" → "Use fechas con el formato dd/mm/aaaa." y no envía la solicitud',
    async (fecha) => {
      await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: [registro(1, 'LOGIN_OK')], siguiente_cursor: null } }));
      await waitFor(() => screen.getByText(T.aplicar), ESPERA);
      const antes = llamadas.filter((l) => l.ruta === '/v1/bitacora').length;
      await fireEvent.changeText(campoFecha('Desde'), fecha);
      await fireEvent.press(screen.getByText(T.aplicar));
      await waitFor(() => screen.getByText(T.fechaInvalida), ESPERA);
      expect(llamadas.filter((l) => l.ruta === '/v1/bitacora').length).toBe(antes);
    },
  );

  test('BIT-01: "Aplicar filtros" con usuario y una fecha válida pide la bitácora con usuario y desde', async () => {
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: [registro(1, 'LOGIN_OK')], siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(T.aplicar), ESPERA);
    const antes = llamadas.filter((l) => l.ruta === '/v1/bitacora').length;
    await fireEvent.changeText(campoTexto('Usuario'), 'agente1');
    await fireEvent.changeText(campoFecha('Desde'), '19/11/2026');
    await fireEvent.press(screen.getByText(T.aplicar));
    await waitFor(() => expect(llamadas.filter((l) => l.ruta === '/v1/bitacora').length).toBe(antes + 1), ESPERA);
    const q = new URLSearchParams(llamadas.filter((l) => l.ruta === '/v1/bitacora').pop()!.query);
    expect(q.get('usuario')).toBe('agente1');
    expect(q.get('desde')).toBeTruthy();
    expect(screen.queryByText(T.fechaInvalida)).toBeNull();
  });

  test.each([
    ['503', () => err(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')],
    ['error de red', () => 'red' as const],
    ['respuesta inesperada', () => ({ estado: 200, cuerpo: { otra: 'cosa' } })],
  ])('error al cargar (%s) → mensaje y Reintentar; nunca la lista vacía', async (_n, r) => {
    await abrirBitacora(r as Manejador);
    await waitFor(() => screen.getByText(T.errorBitacora), ESPERA);
    expect(screen.getByText(T.reintentar)).toBeTruthy();
    expect(screen.queryByText(T.vacia)).toBeNull();
  });

  test('lista vacía real → "No hay registros para estos filtros."', async () => {
    await abrirBitacora(() => ({ estado: 200, cuerpo: { registros: [], siguiente_cursor: null } }));
    await waitFor(() => screen.getByText(T.vacia), ESPERA);
    expect(screen.queryByText(T.errorBitacora)).toBeNull();
  });
});

// =============================================================================================
// HU-01 (pendiente de HU-01/02): retomar la sesión al abrir la app
// =============================================================================================
