/**
 * CONTRATO-HU-01 v5 §4, AUTH-03 (arbitraje A1 del veredicto HU-01/02: "venga de la solicitud que
 * venga"): al volver a abrir la app con la sesión guardada, la renovación y /v1/me responden 401 SESION_VENCIDA → aviso de AUTH-03.
 *
 * Una variante por archivo: la app guarda estado en memoria de módulo y Jest da a cada archivo un
 * registro de módulos limpio, así que el caso empieza con la app recién cargada.
 * Interfaz (HU-01 §4 bis): `App.tsx`, `fetch` global con `EXPO_PUBLIC_API_URL`, SecureStore.
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

// eslint-disable-next-line @typescript-eslint/no-var-requires
const App: React.ComponentType = require('../App').default;

jest.setTimeout(60000);
const ESPERA = { timeout: 20000 };
const INACTIVIDAD = 'Su sesión se cerró por inactividad. Ingrese de nuevo.';
const RENOVACION_VENCIDA = true;

type R = { estado: number; cuerpo?: unknown };
let rutas: Record<string, (auth: string | null) => R> = {};

function respuesta(estado: number, cuerpo?: unknown): Response {
  const texto = cuerpo === undefined ? '' : JSON.stringify(cuerpo);
  return new Response(estado === 204 ? null : texto, {
    status: estado,
    headers: { 'Content-Type': 'application/json', 'X-Id-Traza': 'traza-prueba' },
  });
}

function auth(init?: RequestInit): string | null {
  const h = init?.headers as Record<string, string> | Headers | undefined;
  if (!h) return null;
  if (typeof (h as Headers).get === 'function') return (h as Headers).get('Authorization');
  const k = Object.keys(h).find((x) => x.toLowerCase() === 'authorization');
  return k ? (h as Record<string, string>)[k] : null;
}

const vencida = (): R => ({
  estado: 401,
  cuerpo: { codigo: 'SESION_VENCIDA', mensaje: 'Su sesión se cerró por inactividad', id_traza: 't' },
});

let n = 0;
const sesion = (): R => {
  n += 1;
  return {
    estado: 200,
    cuerpo: {
      token_acceso: `acceso-${n}`,
      token_renovacion: `renov-${n}`,
      expira_en: 900,
      inactividad_s: 600,
      usuario: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente', rol: 'agente' },
    },
  };
};

beforeEach(() => {
  mockAlmacen.clear();
  rutas = {
    'POST /v1/auth/login': sesion,
    'POST /v1/auth/refresh': sesion,
    'GET /v1/me': () => ({
      estado: 200,
      cuerpo: { id: 'u-agente', usuario: 'agente1', nombre: 'Ana Agente', rol: 'agente' },
    }),
  };
  (global as unknown as { fetch: unknown }).fetch = jest.fn(
    async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === 'string' ? entrada : entrada.toString();
      const ruta = url.slice(URL_API.length).split('?')[0];
      const m = rutas[`${(init?.method ?? 'GET').toUpperCase()} ${ruta}`];
      const r = m ? m(auth(init)) : { estado: 404, cuerpo: { codigo: 'NO_ENCONTRADO', mensaje: 'x', id_traza: 't' } };
      return respuesta(r.estado, r.cuerpo);
    },
  );
});

test('al volver a abrir la app con sesión guardada: la renovación y /v1/me responden 401 SESION_VENCIDA → AUTH-03', async () => {
  await render(<App />);
  await waitFor(() => screen.getByText('Ingresar'), ESPERA);
  const ins = screen.root!.queryAll((i) => i.type === 'TextInput');
  await fireEvent.changeText(ins.find((i) => !i.props.secureTextEntry)!, 'agente1');
  await fireEvent.changeText(ins.find((i) => i.props.secureTextEntry)!, 'clave');
  await fireEvent.press(screen.getByText('Ingresar'));
  await waitFor(() => screen.getByText('Rol: Agente'), ESPERA);
  expect(mockAlmacen.size).toBeGreaterThan(0);

  screen.unmount();
  rutas['GET /v1/me'] = vencida;
  if (RENOVACION_VENCIDA) rutas['POST /v1/auth/refresh'] = vencida;

  await render(<App />);
  await waitFor(() => screen.getByText(INACTIVIDAD), ESPERA);
  expect(screen.queryByText('Rol: Agente')).toBeNull();
});
