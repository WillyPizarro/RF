/**
 * CONTRATO-HU-04 v4 §6 "Sin caché HTTP: la app" — toda llamada de la app a la API usa el `fetch`
 * global con `cache: 'no-store'` en sus opciones.
 *
 * Se recorre un flujo que toca todas las rutas que usa la app hoy (login, /v1/me, /v1/motivos,
 * consulta de placa, renovación al retomar, bitácora del supervisor, logout) y se inspeccionan las
 * opciones de CADA llamada al `fetch` simulado. Interfaz: `App.tsx` (CONTRATO-HU-01 §4 bis), con
 * el módulo de borde de la cámara simulado (HU-04 §1) y `expo-secure-store` en memoria.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

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

jest.mock('../src/camara/lectorPlaca', () => {
  const R = require('react');
  const { View } = require('react-native');
  return {
    asegurarPermisoCamara: async () => 'concedido',
    capturarYLeer: async () => ({ texto: 'ZZA-101' }),
    abrirAjustes: async () => undefined,
    VisorCamara: () => R.createElement(View, { testID: 'visor-simulado' }),
  };
});

// eslint-disable-next-line @typescript-eslint/no-var-requires
const App: React.ComponentType = require('../App').default;

jest.setTimeout(60000);
const ESPERA = { timeout: 20000 };

type Llamada = { url: string; metodo: string; init: RequestInit | undefined };
let llamadas: Llamada[] = [];
let rol: 'agente' | 'supervisor' = 'agente';
let sec = 0;

function respuesta(estado: number, cuerpo?: unknown): Response {
  return new Response(estado === 204 ? null : JSON.stringify(cuerpo ?? {}), {
    status: estado,
    headers: { 'Content-Type': 'application/json', 'X-Id-Traza': 't', 'Cache-Control': 'no-store' },
  });
}

const persona = () =>
  rol === 'agente'
    ? { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente', rol: 'agente' }
    : { id: 'u-super', usuario: 'supervisor1', nombre: 'Sara Supervisora', rol: 'supervisor' };

function sesion() {
  sec += 1;
  return { token_acceso: `a-${sec}`, token_renovacion: `r-${sec}`, expira_en: 900, inactividad_s: 600, usuario: persona() };
}

const fetchSimulado = jest.fn(async (entrada: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof entrada === 'string' ? entrada : entrada.toString();
  const metodo = (init?.method ?? 'GET').toUpperCase();
  llamadas.push({ url, metodo, init });
  const ruta = url.slice(URL_API.length).split('?')[0];
  switch (`${metodo} ${ruta}`) {
    case 'POST /v1/auth/login':
    case 'POST /v1/auth/refresh':
      return respuesta(200, sesion());
    case 'POST /v1/auth/logout':
      return respuesta(204);
    case 'GET /v1/me':
      return respuesta(200, persona());
    case 'GET /v1/motivos':
      return respuesta(200, {
        motivos: [
          { codigo: 'control_vehicular', descripcion: 'Control vehicular' },
          { codigo: 'otro', descripcion: 'Otro' },
        ],
        formato_placa: { regex: '^[A-Z0-9]{3}-[0-9]{3}$', descripcion: 'ABC-123' },
      });
    case 'POST /v1/consultas/placa':
      return respuesta(200, {
        consulta_id: 'c-1', placa: 'ZZA-101', resultado: 'con_requisitoria',
        motivo: { codigo: 'control_vehicular', texto: null }, consultado_en: '2026-11-19T15:04:00Z',
      });
    case 'GET /v1/bitacora':
      return respuesta(200, { registros: [], siguiente_cursor: null });
    default:
      return respuesta(404, { codigo: 'NO_ENCONTRADO', mensaje: 'x', id_traza: 't' });
  }
});

async function entrar(usuario: string) {
  await waitFor(() => screen.getByText('Ingresar'), ESPERA);
  // Tras "Salir" la pantalla puede volver a dibujarse: se escribe y se espera a ver el valor en
  // los campos actuales antes de tocar "Ingresar".
  const campos = () => {
    const ins = screen.root!.queryAll((i) => i.type === 'TextInput');
    return { u: ins.find((i) => !i.props.secureTextEntry)!, c: ins.find((i) => i.props.secureTextEntry)! };
  };
  await waitFor(async () => {
    await fireEvent.changeText(campos().u, usuario);
    await fireEvent.changeText(campos().c, 'clave');
    expect(campos().u.props.value).toBe(usuario);
    expect(campos().c.props.value).toBe('clave');
  }, ESPERA);
  await fireEvent.press(screen.getByText('Ingresar'));
}

beforeEach(() => {
  mockAlmacen.clear();
  llamadas = [];
  (global as unknown as { fetch: unknown }).fetch = fetchSimulado;
  fetchSimulado.mockClear();
});

test('cada llamada de la app a la API lleva cache: "no-store" (login, me, motivos, consulta, retomar, bitácora, logout)', async () => {
  // Agente: login, /v1/me, /v1/motivos, consulta de placa.
  rol = 'agente';
  await render(<App />);
  await entrar('agente1');
  await waitFor(() => screen.getByText('Rol: Agente'), ESPERA);
  await fireEvent.press(screen.getByText('Consultar placa'));
  await waitFor(() => screen.getByText('Motivo de consulta *'), ESPERA);
  const ins = screen.root!.queryAll((i) => i.type === 'TextInput');
  await fireEvent.changeText(ins[0], 'ZZA-101');
  if (!screen.queryByText('Control vehicular')) await fireEvent.press(screen.getByText('Motivo de consulta *'));
  await waitFor(() => screen.getByText('Control vehicular'), ESPERA);
  const opciones = screen.getAllByText('Control vehicular');
  await fireEvent.press(opciones[opciones.length - 1]);
  await fireEvent.press(screen.getByText('Consultar'));
  await waitFor(() => screen.getByText('TIENE REQUISITORIA'), ESPERA);

  // Retomar la sesión al volver a abrir la app (renovación y /v1/me).
  screen.unmount();
  await render(<App />);
  await waitFor(() => screen.getByText('Rol: Agente'), ESPERA);
  await fireEvent.press(screen.getByText('Salir'));
  await waitFor(() => screen.getByText('Ingresar'), ESPERA);

  // Supervisor: bitácora.
  rol = 'supervisor';
  await entrar('supervisor1');
  await waitFor(() => screen.getByText('Rol: Supervisor'), ESPERA);
  await fireEvent.press(screen.getByText('Bitácora'));
  await waitFor(() => expect(llamadas.some((l) => l.url.includes('/v1/bitacora'))).toBe(true), ESPERA);

  const rutas = new Set(llamadas.map((l) => `${l.metodo} ${l.url.slice(URL_API.length).split('?')[0]}`));
  for (const r of ['POST /v1/auth/login', 'GET /v1/me', 'GET /v1/motivos', 'POST /v1/consultas/placa',
    'POST /v1/auth/logout', 'GET /v1/bitacora']) {
    expect(rutas).toContain(r);
  }
  const sinNoStore = llamadas
    .filter((l) => l.url.startsWith(URL_API))
    .filter((l) => l.init?.cache !== 'no-store')
    .map((l) => `${l.metodo} ${l.url.slice(URL_API.length)} (cache=${String(l.init?.cache)})`);
  expect(sinNoStore).toEqual([]);
});
