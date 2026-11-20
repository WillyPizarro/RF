/**
 * CONTRATO-HU-04 v5 — Capturar la placa con la cámara (etapa 1, Jest), con el aviso de
 * telemetría de ML Kit en OCR-01 (§3, v5).
 *
 * Interfaz (HU-04 "Interfaz observable" y §1): se monta `App.tsx` (CONTRATO-HU-01 §4 bis) y la
 * cámara y el OCR se reemplazan por el MÓDULO DE BORDE `src/camara/lectorPlaca.ts`, simulado con
 * `jest.mock`: `asegurarPermisoCamara`, `VisorCamara`, `capturarYLeer` y `abrirAjustes`.
 * El `fetch` global y `expo-secure-store` también se simulan. La API no cambia (HU-03 v4).
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

// --- Módulo de borde simulado (HU-04 §1) ------------------------------------------------------
const mockAsegurarPermiso = jest.fn<Promise<'concedido' | 'denegado'>, []>();
const mockCapturarYLeer = jest.fn<Promise<{ texto: string | null }>, []>();
const mockAbrirAjustes = jest.fn<Promise<void>, []>();
const mockVisorProps: Array<{ activo: boolean }> = [];

jest.mock('../src/camara/lectorPlaca', () => {
  const R = require('react');
  const { View } = require('react-native');
  return {
    asegurarPermisoCamara: () => mockAsegurarPermiso(),
    capturarYLeer: () => mockCapturarYLeer(),
    abrirAjustes: () => mockAbrirAjustes(),
    VisorCamara: (props: { activo: boolean }) => {
      mockVisorProps.push(props);
      return R.createElement(View, { testID: 'visor-simulado' });
    },
  };
});

// eslint-disable-next-line @typescript-eslint/no-var-requires
const App: React.ComponentType = require('../App').default;

jest.setTimeout(60000);
const ESPERA = { timeout: 20000 };

// --- Textos que no se negocian ---------------------------------------------------------------
const T = {
  ingresar: 'Ingresar',
  rolAgente: 'Rol: Agente',
  consultarPlaca: 'Consultar placa',
  motivo: 'Motivo de consulta *',
  consultar: 'Consultar',
  sinMotivo: 'Indique el motivo de la consulta.',
  formato: 'El formato de placa no es válido. Formato esperado: ',
  tiene: 'TIENE REQUISITORIA',
  camara: 'Leer con cámara',
  // OCR-01
  leerPlaca: 'Leer placa',
  encuadre: 'Encuadre la placa y toque Capturar',
  capturar: 'Capturar',
  manual: 'Ingresar manualmente',
  cerrar: '✕',
  // OCR-02
  placaLeida: 'Placa leída',
  confirme: 'Confirme o corrija la placa antes de consultar.',
  usar: 'Usar esta placa',
  recapturar: 'Volver a capturar',
  // OCR-03
  noLeida: 'No se pudo leer la placa. Pruebe de frente y con más luz.',
  reintentar: 'Volver a intentar',
  // OCR-04
  sinPermiso: 'La app no tiene permiso para usar la cámara.',
  comoDar: 'Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara.',
  ajustes: 'Abrir ajustes',
  // Aviso de telemetría (v5)
  avisoTitulo: 'Antes de leer la placa',
  avisoTexto:
    'Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de uso y un código de esta instalación.',
  entendido: 'Entendido',
  salir: 'Salir',
  inactividad: 'Su sesión se cerró por inactividad. Ingrese de nuevo.',
};

// --- Servidor falso --------------------------------------------------------------------------
type Resp = { estado: number; cuerpo?: unknown };
type Llamada = { metodo: string; ruta: string; auth: string | null; cuerpo: unknown };
let llamadas: Llamada[] = [];
let rutas: Record<string, (ll: Llamada) => Resp> = {};

function respuesta(estado: number, cuerpo?: unknown): Response {
  const texto = cuerpo === undefined ? '' : JSON.stringify(cuerpo);
  return new Response(estado === 204 ? null : texto, {
    status: estado,
    headers: { 'Content-Type': 'application/json', 'X-Id-Traza': 'traza-prueba' },
  });
}

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
  const ruta = (url.startsWith(URL_API) ? url.slice(URL_API.length) : url).split('?')[0];
  let cuerpo: unknown = null;
  try {
    cuerpo = init?.body ? JSON.parse(String(init.body)) : null;
  } catch {
    cuerpo = init?.body;
  }
  const ll = { metodo, ruta, auth: cabecera(init, 'Authorization'), cuerpo };
  llamadas.push(ll);
  const m = rutas[`${metodo} ${ruta}`];
  const r = m ? m(ll) : { estado: 404, cuerpo: { codigo: 'NO_ENCONTRADO', mensaje: 'x', id_traza: 't' } };
  return respuesta(r.estado, r.cuerpo);
});

const MOTIVOS = [
  { codigo: 'control_vehicular', descripcion: 'Control vehicular' },
  { codigo: 'intervencion_policial', descripcion: 'Intervención policial' },
  { codigo: 'denuncia', descripcion: 'Denuncia' },
  { codigo: 'operativo', descripcion: 'Operativo' },
  { codigo: 'otro', descripcion: 'Otro' },
];
const FORMATO = { regex: '^[A-Z0-9]{3}-[0-9]{3}$', descripcion: 'ABC-123 (3 letras o números, guion, 3 números)' };

let sec = 0;
function servidor(formato = FORMATO, inactividad_s = 600) {
  const tokens = new Set<string>();
  const dar = () => {
    sec += 1;
    const d = {
      token_acceso: `acceso-${sec}`,
      token_renovacion: `renov-${sec}`,
      expira_en: 900,
      inactividad_s,
      usuario: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente', rol: 'agente' },
    };
    tokens.add(d.token_acceso);
    return d;
  };
  rutas = {
    'POST /v1/auth/login': () => ({ estado: 200, cuerpo: dar() }),
    'POST /v1/auth/refresh': () => ({ estado: 200, cuerpo: dar() }),
    'GET /v1/me': (ll) =>
      ll.auth && tokens.has(ll.auth.replace(/^Bearer\s+/i, ''))
        ? { estado: 200, cuerpo: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente', rol: 'agente' } }
        : { estado: 401, cuerpo: { codigo: 'NO_AUTENTICADO', mensaje: 'Inicie sesión nuevamente', id_traza: 't' } },
    'GET /v1/motivos': () => ({ estado: 200, cuerpo: { motivos: MOTIVOS, formato_placa: formato } }),
    'POST /v1/consultas/placa': (ll) => ({
      estado: 200,
      cuerpo: {
        consulta_id: 'c-1',
        placa: (ll.cuerpo as { placa: string }).placa,
        resultado: 'con_requisitoria',
        motivo: { codigo: 'control_vehicular', texto: null },
        consultado_en: '2026-11-19T15:04:00Z',
      },
    }),
  };
}

// --- Ayudas de pantalla ----------------------------------------------------------------------
const inputs = () => screen.root!.queryAll((i) => i.type === 'TextInput');
const posts = () => llamadas.filter((l) => l.metodo === 'POST' && l.ruta === '/v1/consultas/placa');
const arbol = () => JSON.stringify(screen.toJSON());

function campoPlaca() {
  const ins = inputs();
  return (
    ins.find((i) => i.props.accessibilityLabel === 'Placa' || i.props['aria-label'] === 'Placa' || i.props.placeholder === 'Placa') ??
    ins[0]
  );
}

async function abrirPla01() {
  await render(<App />);
  await waitFor(() => screen.getByText(T.ingresar), ESPERA);
  const ins = inputs();
  await fireEvent.changeText(ins.find((i) => !i.props.secureTextEntry)!, 'agente1');
  await fireEvent.changeText(ins.find((i) => i.props.secureTextEntry)!, 'clave');
  await fireEvent.press(screen.getByText(T.ingresar));
  await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
  await fireEvent.press(screen.getByText(T.consultarPlaca));
  await waitFor(() => screen.getByText(T.motivo), ESPERA);
}

async function elegirMotivo(descripcion: string) {
  if (!screen.queryByText(descripcion)) await fireEvent.press(screen.getByText(T.motivo));
  await waitFor(() => screen.getByText(descripcion), ESPERA);
  const todos = screen.getAllByText(descripcion);
  await fireEvent.press(todos[todos.length - 1]);
}

async function tocarCamara() {
  await fireEvent.press(screen.getByLabelText(T.camara));
}

/** Abre OCR-01 y, si aparece el aviso de telemetría (v5, primera vez por sesión), lo cierra. */
async function abrirOcr01() {
  await abrirOcr01ConAviso();
  if (screen.queryByText(T.entendido)) {
    await fireEvent.press(screen.getByText(T.entendido));
    await waitFor(() => expect(screen.queryByText(T.avisoTitulo)).toBeNull(), ESPERA);
  }
}

/** Abre OCR-01 sin tocar el aviso. */
async function abrirOcr01ConAviso() {
  mockAsegurarPermiso.mockResolvedValue('concedido');
  await tocarCamara();
  await waitFor(() => screen.getByText(T.encuadre), ESPERA);
}

async function dormir(ms: number) {
  await act(async () => {
    await new Promise((r) => setTimeout(r, ms));
  });
}

/** OCR-02: el campo editable con la placa propuesta (el único TextInput a la vista). */
function campoOcr02() {
  const ins = inputs();
  if (ins.length !== 1) throw new Error(`OCR-02 debería tener un solo campo; hay ${ins.length}`);
  return ins[0];
}

let oyentesAtras: Array<() => boolean | null | undefined> = [];

async function presionarAtras() {
  await act(async () => {
    for (const f of [...oyentesAtras].reverse()) {
      if (f()) break;
    }
  });
}

beforeEach(() => {
  mockAlmacen.clear();
  llamadas = [];
  rutas = {};
  mockVisorProps.length = 0;
  mockAsegurarPermiso.mockReset();
  mockCapturarYLeer.mockReset();
  mockAbrirAjustes.mockReset().mockResolvedValue(undefined);
  (global as unknown as { fetch: unknown }).fetch = fetchSimulado;
  fetchSimulado.mockClear();
  oyentesAtras = [];
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation(((_e: string, f: () => boolean) => {
    oyentesAtras.push(f);
    return { remove: () => (oyentesAtras = oyentesAtras.filter((x) => x !== f)) };
  }) as unknown as typeof BackHandler.addEventListener);
  servidor();
});

afterEach(() => {
  jest.restoreAllMocks();
});

// =============================================================================================
// §2 Entrada desde PLA-01
// =============================================================================================

describe('HU-04 §2 — entrada desde PLA-01', () => {
  test('el botón 📷 "Leer con cámara" está habilitado', async () => {
    await abrirPla01();
    expect(screen.getByLabelText(T.camara)).toBeEnabled();
  });

  test('permiso concedido → OCR-01 con sus textos y el visor activo; capturarYLeer no se llama', async () => {
    await abrirPla01();
    await abrirOcr01();
    expect(mockAsegurarPermiso).toHaveBeenCalledTimes(1);
    for (const t of [T.leerPlaca, T.encuadre, T.capturar, T.manual, T.cerrar]) expect(screen.getByText(t)).toBeTruthy();
    expect(screen.getByTestId('visor-simulado')).toBeTruthy();
    expect(mockVisorProps[mockVisorProps.length - 1]).toEqual({ activo: true });
    expect(mockCapturarYLeer).not.toHaveBeenCalled();
  });

  test('permiso denegado → OCR-04 con sus textos; capturarYLeer nunca se llama', async () => {
    mockAsegurarPermiso.mockResolvedValue('denegado');
    await abrirPla01();
    await tocarCamara();
    await waitFor(() => screen.getByText(T.sinPermiso), ESPERA);
    for (const t of [T.comoDar, T.ajustes, T.manual]) expect(screen.getByText(t)).toBeTruthy();
    expect(mockCapturarYLeer).not.toHaveBeenCalled();
    expect(screen.queryByTestId('visor-simulado')).toBeNull();
  });
});

// =============================================================================================
// §3 Captura
// =============================================================================================

describe('HU-04 §3 — captura', () => {
  test('sin tocar "Capturar" no se lee nada, por más tiempo que pase (regla 6)', async () => {
    await abrirPla01();
    await abrirOcr01();
    await dormir(3000);
    expect(mockCapturarYLeer).not.toHaveBeenCalled();
    expect(screen.queryByText(T.placaLeida)).toBeNull();
  });

  test('una sola lectura por toque; mientras espera "Capturar" queda desactivado y un 2.º toque no lee', async () => {
    let soltar: (v: { texto: string | null }) => void = () => undefined;
    mockCapturarYLeer.mockImplementation(() => new Promise((r) => (soltar = r)));
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(1);
    const boton = screen.queryByText(T.capturar);
    if (boton) {
      expect(boton).toBeDisabled();
      await fireEvent.press(boton);
    }
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(1);
    await act(async () => soltar({ texto: 'ZZA-101' }));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(1);
  });

  test('cada toque de "Capturar" es una lectura: volver a capturar y tocar de nuevo → 2 en total', async () => {
    mockCapturarYLeer.mockResolvedValue({ texto: 'ZZA-101' });
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    await fireEvent.press(screen.getByText(T.recapturar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(1);
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(2);
  });

  test('falla de la cámara (capturarYLeer rechaza) → OCR-03, nunca un resultado', async () => {
    mockCapturarYLeer.mockRejectedValue(new Error('cámara'));
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA);
    expect(screen.getByText(T.reintentar)).toBeTruthy();
    expect(screen.getByText(T.manual)).toBeTruthy();
    expect(screen.queryByText(T.placaLeida)).toBeNull();
    expect(arbol()).not.toMatch(/sin requisitoria/i);
  });

  test('"✕" vuelve a PLA-01 sin cambios (placa y motivo como estaban)', async () => {
    await abrirPla01();
    await fireEvent.changeText(campoPlaca(), 'ZZB-201');
    await elegirMotivo('Operativo');
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.cerrar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(campoPlaca().props.value).toBe('ZZB-201');
    await fireEvent.press(screen.getByText(T.consultar));
    await waitFor(() => expect(posts().length).toBe(1), ESPERA);
    expect(posts()[0].cuerpo).toMatchObject({ placa: 'ZZB-201', motivo_codigo: 'operativo' });
  });

  test.each(['OCR-01', 'OCR-03', 'OCR-04'])('"Ingresar manualmente" desde %s vuelve a PLA-01 sin cambios', async (desde) => {
    await abrirPla01();
    await fireEvent.changeText(campoPlaca(), 'ZZB-201');
    if (desde === 'OCR-04') {
      mockAsegurarPermiso.mockResolvedValue('denegado');
      await tocarCamara();
      await waitFor(() => screen.getByText(T.sinPermiso), ESPERA);
    } else {
      await abrirOcr01();
      if (desde === 'OCR-03') {
        mockCapturarYLeer.mockResolvedValue({ texto: null });
        await fireEvent.press(screen.getByText(T.capturar));
        await waitFor(() => screen.getByText(T.noLeida), ESPERA);
      }
    }
    await fireEvent.press(screen.getByText(T.manual));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(campoPlaca().props.value).toBe('ZZB-201');
    expect(posts()).toEqual([]);
  });
});

// =============================================================================================
// §4 Del texto leído a la placa propuesta (tabla completa)
// =============================================================================================

describe('HU-04 §4 — texto leído → placa propuesta', () => {
  test.each([
    ['ZZA-101', 'ZZA-101'],
    ['zza-101', 'ZZA-101'],
    ['ZZA 101', 'ZZA-101'],
    ['ZZA.101', 'ZZA-101'],
    ['PERU\nZZB-201\nLIMA', 'ZZB-201'],
    ['ZZA-101 ZZB-201', 'ZZA-101'],
  ])('%j → OCR-02 con %s', async (texto, esperado) => {
    mockCapturarYLeer.mockResolvedValue({ texto });
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    expect(campoOcr02().props.value).toBe(esperado);
  });

  test.each([['ZZA-1O1'], ['PERU'], [''], [null]])('%j → OCR-03 (la app no adivina caracteres)', async (texto) => {
    mockCapturarYLeer.mockResolvedValue({ texto: texto as string | null });
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA);
    expect(screen.queryByText(T.placaLeida)).toBeNull();
  });

  test('si la API cambia formato_placa.regex, cambia lo que se acepta (sin tocar código)', async () => {
    servidor({ regex: '^[A-Z]{2}[0-9]{4}$', descripcion: 'AB1234' });
    mockCapturarYLeer.mockResolvedValueOnce({ texto: 'ZZA-101' }).mockResolvedValueOnce({ texto: 'ab1234' });
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA); // ZZA-101 no cumple la regex nueva
    await fireEvent.press(screen.getByText(T.reintentar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    expect(campoOcr02().props.value).toBe('AB1234');
  });
});

// =============================================================================================
// §5 Confirmar y volver a la consulta
// =============================================================================================

async function leerYConfirmar(texto: string) {
  mockCapturarYLeer.mockResolvedValue({ texto });
  await abrirOcr01();
  await fireEvent.press(screen.getByText(T.capturar));
  await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
}

describe('HU-04 §5 — confirmar y volver', () => {
  test('OCR-02: "Placa leída", campo editable, aviso, "Usar esta placa", "Volver a capturar"; ninguna imagen', async () => {
    await abrirPla01();
    await leerYConfirmar('ZZA-101');
    for (const t of [T.confirme, T.usar, T.recapturar]) expect(screen.getByText(t)).toBeTruthy();
    expect(campoOcr02().props.editable).not.toBe(false);
    expect(screen.root!.queryAll((i) => i.type === 'Image')).toEqual([]);
    expect(arbol()).not.toMatch(/file:\/\/|data:image|\.jpe?g|\.png/i);
  });

  test('corregir: el texto editado vuelve a PLA-01 en "Placa"', async () => {
    await abrirPla01();
    await leerYConfirmar('ZZA-101');
    await fireEvent.changeText(campoOcr02(), 'ZZB-201');
    await fireEvent.press(screen.getByText(T.usar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(campoPlaca().props.value).toBe('ZZB-201');
  });

  test('nunca consulta sola: entre 📷 y "Consultar" no hay ninguna llamada a fetch; sin motivo previo, el motivo sigue vacío', async () => {
    await abrirPla01();
    const desde = llamadas.length;
    await leerYConfirmar('ZZA-101');
    await fireEvent.press(screen.getByText(T.usar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(campoPlaca().props.value).toBe('ZZA-101');
    expect(llamadas.slice(desde)).toEqual([]);
    await fireEvent.press(screen.getByText(T.consultar));
    await waitFor(() => screen.getByText(T.sinMotivo), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('el motivo elegido antes de abrir la cámara se conserva; la consulta es la de HU-03 (sin imagen ni campos nuevos)', async () => {
    await abrirPla01();
    await elegirMotivo('Control vehicular');
    const desde = llamadas.length;
    await leerYConfirmar('zza 101');
    await fireEvent.press(screen.getByText(T.usar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(llamadas.slice(desde)).toEqual([]);
    await fireEvent.press(screen.getByText(T.consultar));
    await waitFor(() => screen.getByText(T.tiene), ESPERA);
    expect(posts().length).toBe(1);
    const cuerpo = posts()[0].cuerpo as Record<string, unknown>;
    expect(cuerpo).toMatchObject({ placa: 'ZZA-101', motivo_codigo: 'control_vehicular' });
    expect(Object.keys(cuerpo).every((k) => ['placa', 'motivo_codigo', 'motivo_texto'].includes(k))).toBe(true);
  });

  test('sigue HU-03: una corrección con formato inválido se rechaza en PLA-03 sin enviar', async () => {
    await abrirPla01();
    await elegirMotivo('Control vehicular');
    await leerYConfirmar('ZZA-101');
    await fireEvent.changeText(campoOcr02(), 'ZZA-1O1');
    await fireEvent.press(screen.getByText(T.usar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await fireEvent.press(screen.getByText(T.consultar));
    await waitFor(() => screen.getByText(T.formato + FORMATO.descripcion), ESPERA);
    expect(posts()).toEqual([]);
  });

  test('"Volver a capturar" → OCR-01 y el valor leído se descarta', async () => {
    await abrirPla01();
    await leerYConfirmar('ZZA-101');
    await fireEvent.press(screen.getByText(T.recapturar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    expect(screen.queryByText(T.placaLeida)).toBeNull();
    await fireEvent.press(screen.getByText(T.cerrar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect(campoPlaca().props.value ?? '').toBe('');
  });

  test('"Volver a intentar" en OCR-03 → OCR-01', async () => {
    mockCapturarYLeer.mockResolvedValue({ texto: null });
    await abrirPla01();
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA);
    await fireEvent.press(screen.getByText(T.reintentar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
  });

  test('"Abrir ajustes" en OCR-04 llama a abrirAjustes()', async () => {
    mockAsegurarPermiso.mockResolvedValue('denegado');
    await abrirPla01();
    await tocarCamara();
    await waitFor(() => screen.getByText(T.ajustes), ESPERA);
    await fireEvent.press(screen.getByText(T.ajustes));
    await waitFor(() => expect(mockAbrirAjustes).toHaveBeenCalledTimes(1), ESPERA);
  });

  test('volver con permiso: tras OCR-04, si ahora está concedido, 📷 abre OCR-01', async () => {
    mockAsegurarPermiso.mockResolvedValueOnce('denegado').mockResolvedValueOnce('concedido');
    await abrirPla01();
    await tocarCamara();
    await waitFor(() => screen.getByText(T.sinPermiso), ESPERA);
    await fireEvent.press(screen.getByText(T.manual));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await tocarCamara();
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    expect(mockAsegurarPermiso).toHaveBeenCalledTimes(2);
  });
});

// =============================================================================================
// §6 Nada se guarda ni sale del dispositivo (parte de Jest)
// =============================================================================================

describe('HU-04 §6 — nada se guarda ni sale', () => {
  test('en todo el flujo OCR-01 → OCR-03 no hay llamadas a fetch', async () => {
    mockCapturarYLeer.mockResolvedValueOnce({ texto: null }).mockRejectedValueOnce(new Error('x'));
    await abrirPla01();
    const desde = llamadas.length;
    await abrirOcr01();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA);
    await fireEvent.press(screen.getByText(T.reintentar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.noLeida), ESPERA);
    expect(llamadas.slice(desde)).toEqual([]);
  });

  test('después de leer, SecureStore no tiene ninguna clave nueva', async () => {
    await abrirPla01();
    const antes = new Map(mockAlmacen);
    await leerYConfirmar('ZZA-101');
    await fireEvent.press(screen.getByText(T.usar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    expect([...mockAlmacen.keys()].sort()).toEqual([...antes.keys()].sort());
    expect([...mockAlmacen.values()].join('\n')).not.toContain('ZZA-101');
  });
});

// =============================================================================================
// §1 Las librerías nativas solo se importan desde el módulo de borde
// =============================================================================================

describe('HU-04 §1 — módulo de borde', () => {
  const fs = jest.requireActual('fs') as typeof import('fs');
  const path = jest.requireActual('path') as typeof import('path');
  const SRC = path.join(__dirname, '..', 'src');
  const BORDE = path.join(SRC, 'camara', 'lectorPlaca.ts');
  // Importaciones de paquetes (no rutas relativas) de cámara u OCR/ML Kit.
  const NATIVA = /(?:from\s+|require\(\s*|import\(\s*)['"]([^'".][^'"]*(?:camera|ml-?kit|text-?recognition|vision|\bocr)[^'"]*)['"]/gi;

  function archivos(dir: string): string[] {
    return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
      const p = path.join(dir, e.name);
      return e.isDirectory() ? archivos(p) : /\.(t|j)sx?$/.test(e.name) ? [p] : [];
    });
  }

  test('existe src/camara/lectorPlaca.ts', () => {
    expect(fs.existsSync(BORDE)).toBe(true);
  });

  test('ningún archivo de src fuera del módulo de borde importa la librería de cámara ni la de ML Kit', () => {
    const fuera = archivos(SRC)
      .filter((f) => path.resolve(f) !== path.resolve(BORDE))
      .flatMap((f) => [...fs.readFileSync(f, 'utf8').matchAll(NATIVA)].map((m) => `${path.relative(SRC, f)}: ${m[1]}`));
    expect(fuera).toEqual([]);
  });

  test('App.tsx tampoco las importa', () => {
    const app = fs.readFileSync(path.join(__dirname, '..', 'App.tsx'), 'utf8');
    expect([...app.matchAll(NATIVA)].map((m) => m[1])).toEqual([]);
  });
});

// =============================================================================================
// §3 Aviso de telemetría de ML Kit (v5)
// =============================================================================================

describe('HU-04 §3 (v5) — aviso de telemetría en OCR-01', () => {
  test('la primera vez por sesión aparece la tarjeta con sus textos; "Capturar" desactivado; "Ingresar manualmente" activo', async () => {
    mockCapturarYLeer.mockResolvedValue({ texto: 'ZZA-101' });
    await abrirPla01();
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
    expect(screen.getByText(T.avisoTexto)).toBeTruthy();
    expect(screen.getByText(T.entendido)).toBeTruthy();
    const capturar = screen.getByText(T.capturar);
    expect(capturar).toBeDisabled();
    await fireEvent.press(capturar);
    expect(mockCapturarYLeer).not.toHaveBeenCalled();
    expect(screen.getByText(T.manual)).toBeEnabled();
  });

  test('tocar fuera de la tarjeta (el visor) no hace nada', async () => {
    await abrirPla01();
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
    await fireEvent.press(screen.getByTestId('visor-simulado'));
    expect(screen.getByText(T.avisoTitulo)).toBeTruthy();
    expect(screen.getByText(T.capturar)).toBeDisabled();
    expect(mockCapturarYLeer).not.toHaveBeenCalled();
  });

  test('"Entendido": la tarjeta desaparece, "Capturar" se activa y en esa sesión no vuelve a aparecer', async () => {
    mockCapturarYLeer.mockResolvedValue({ texto: 'ZZA-101' });
    await abrirPla01();
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
    await fireEvent.press(screen.getByText(T.entendido));
    await waitFor(() => expect(screen.queryByText(T.avisoTitulo)).toBeNull(), ESPERA);
    expect(screen.getByText(T.capturar)).toBeEnabled();
    await fireEvent.press(screen.getByText(T.capturar));
    await waitFor(() => screen.getByText(T.placaLeida), ESPERA);
    expect(mockCapturarYLeer).toHaveBeenCalledTimes(1);
    // Salir y volver a OCR-01 en la misma sesión: no aparece.
    await fireEvent.press(screen.getByText(T.recapturar));
    await waitFor(() => screen.getByText(T.encuadre), ESPERA);
    expect(screen.queryByText(T.avisoTitulo)).toBeNull();
    await fireEvent.press(screen.getByText(T.cerrar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await abrirOcr01ConAviso();
    expect(screen.queryByText(T.avisoTitulo)).toBeNull();
    expect(screen.getByText(T.capturar)).toBeEnabled();
  });

  test.each(['✕', 'atrás', 'Ingresar manualmente'])(
    'salir con "%s" con la tarjeta a la vista no la da por vista: al volver a OCR-01 aparece de nuevo',
    async (como) => {
      await abrirPla01();
      await abrirOcr01ConAviso();
      await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
      if (como === '✕') await fireEvent.press(screen.getByText(T.cerrar));
      else if (como === 'atrás') await presionarAtras();
      else await fireEvent.press(screen.getByText(T.manual));
      await waitFor(() => screen.getByText(T.motivo), ESPERA);
      expect(screen.queryByText(T.avisoTitulo)).toBeNull();
      await abrirOcr01ConAviso();
      await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
      expect(mockCapturarYLeer).not.toHaveBeenCalled();
    },
  );

  test('solo en memoria: tras "Salir" y volver a entrar, aparece otra vez; SecureStore sin claves nuevas por el aviso', async () => {
    await abrirPla01();
    const antes = [...mockAlmacen.keys()].sort();
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
    await fireEvent.press(screen.getByText(T.entendido));
    await waitFor(() => expect(screen.queryByText(T.avisoTitulo)).toBeNull(), ESPERA);
    expect([...mockAlmacen.keys()].sort()).toEqual(antes);
    expect([...mockAlmacen.values()].join('\n')).not.toMatch(/entendido|aviso|telemetr|mlkit|ml kit/i);
    // Volver al inicio y salir.
    await fireEvent.press(screen.getByText(T.cerrar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    for (let i = 0; i < 5 && !screen.queryByText(T.salir); i += 1) await presionarAtras();
    await fireEvent.press(screen.getByText(T.salir));
    await waitFor(() => screen.getByText(T.ingresar), ESPERA);
    // Nueva sesión.
    const ins = inputs();
    await fireEvent.changeText(ins.find((i) => !i.props.secureTextEntry)!, 'agente1');
    await fireEvent.changeText(ins.find((i) => i.props.secureTextEntry)!, 'clave');
    await fireEvent.press(screen.getByText(T.ingresar));
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    await fireEvent.press(screen.getByText(T.consultarPlaca));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
  });

  test('solo en memoria: tras el cierre por inactividad, el aviso aparece otra vez y AUTH-03 sigue igual', async () => {
    servidor(FORMATO, 2);
    await abrirPla01();
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
    await fireEvent.press(screen.getByText(T.entendido));
    await waitFor(() => expect(screen.queryByText(T.avisoTitulo)).toBeNull(), ESPERA);
    await fireEvent.press(screen.getByText(T.cerrar));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await dormir(3500);
    await waitFor(() => screen.getByText(T.inactividad), ESPERA);
    servidor(FORMATO, 600);
    const ins = inputs();
    await fireEvent.changeText(ins.find((i) => !i.props.secureTextEntry)!, 'agente1');
    await fireEvent.changeText(ins.find((i) => i.props.secureTextEntry)!, 'clave');
    await fireEvent.press(screen.getByText(T.ingresar));
    await waitFor(() => screen.getByText(T.rolAgente), ESPERA);
    await fireEvent.press(screen.getByText(T.consultarPlaca));
    await waitFor(() => screen.getByText(T.motivo), ESPERA);
    await abrirOcr01ConAviso();
    await waitFor(() => screen.getByText(T.avisoTitulo), ESPERA);
  });

  test('sin permiso: OCR-04 no muestra el aviso', async () => {
    mockAsegurarPermiso.mockResolvedValue('denegado');
    await abrirPla01();
    await tocarCamara();
    await waitFor(() => screen.getByText(T.sinPermiso), ESPERA);
    expect(screen.queryByText(T.avisoTitulo)).toBeNull();
    expect(screen.queryByText(T.entendido)).toBeNull();
  });
});
