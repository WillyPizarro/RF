/**
 * DoD criterio 10 — La app llama a la API solo a través de la URL configurada.
 *
 * Contrato (SPRINT0.md §5 + M-1 D y F):
 * - Pantalla: `src/pantallas/PantallaEstado.tsx`, export por defecto; se renderiza directamente.
 * - Usa el `fetch` global con `EXPO_PUBLIC_API_URL + '/v1/salud'`.
 * - Muestra "Conectado" cuando /v1/salud responde 200.
 * - Muestra "Sin conexión con el servidor" ante cualquier respuesta distinta de 200
 *   o error de red.
 *
 * El `fetch` global se simula. Se envuelve en un QueryClientProvider por si la pantalla
 * usa TanStack Query (ADR-0013); no fija opciones, así que no altera el comportamiento.
 * Escrita para @testing-library/react-native 14 (`render` asíncrono).
 */
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const URL_API = 'https://api.prueba.invalid';

// La URL se fija ANTES de cargar la pantalla. Se usa `require` (no `import`) porque los
// `import` se elevan al inicio del archivo; `require` respeta este orden. No se aísla el
// registro de módulos: la pantalla usa el mismo React que la librería de pruebas.
process.env.EXPO_PUBLIC_API_URL = URL_API;
// eslint-disable-next-line @typescript-eslint/no-var-requires
const PantallaEstado: React.ComponentType = require('../src/pantallas/PantallaEstado').default;

const TEXTO_OK = 'Conectado';
const TEXTO_SIN_CONEXION = 'Sin conexión con el servidor';
// TanStack Query reintenta por defecto con espera exponencial (~7 s en total).
const ESPERA_MS = 20000;

jest.setTimeout(30000);

type Simulada = { estado: number; cuerpo: unknown };

function respuesta({ estado, cuerpo }: Simulada): Response {
  const texto = JSON.stringify(cuerpo);
  const cabeceras = { 'Content-Type': 'application/json', 'X-Id-Traza': 'traza-prueba' };
  if (typeof Response !== 'undefined') {
    return new Response(texto, { status: estado, headers: cabeceras });
  }
  return {
    ok: estado >= 200 && estado < 300,
    status: estado,
    headers: { get: (k: string) => (cabeceras as Record<string, string>)[k] ?? null },
    json: async () => JSON.parse(texto),
    text: async () => texto,
    clone() {
      return respuesta({ estado, cuerpo });
    },
  } as unknown as Response;
}

const SALUD_OK = { estado: 'ok', bd: 'ok', simuladores: 'ok', version: '0.1.0' };
const SALUD_503 = { estado: 'error', bd: 'error', simuladores: 'ok', version: '0.1.0' };
const ERROR_404 = { codigo: 'NO_ENCONTRADO', mensaje: 'No encontrado', id_traza: 't' };
const ERROR_500 = { codigo: 'ERROR_INTERNO', mensaje: 'Error interno', id_traza: 't' };

let fetchSimulado: jest.Mock;
let cliente: QueryClient;
const fetchOriginal = global.fetch;

async function renderizar() {
  cliente = new QueryClient();
  return render(
    <QueryClientProvider client={cliente}>
      <PantallaEstado />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchSimulado = jest.fn();
  global.fetch = fetchSimulado as unknown as typeof fetch;
});

afterEach(() => {
  cliente?.clear();
  global.fetch = fetchOriginal;
});

function urlDe(llamada: unknown[]): string {
  const objetivo = llamada[0] as string | URL | Request;
  if (typeof objetivo === 'string') return objetivo;
  if (objetivo instanceof URL) return objetivo.toString();
  return (objetivo as Request).url;
}

describe('PantallaEstado — /v1/salud responde 200', () => {
  it('muestra "Conectado"', async () => {
    fetchSimulado.mockImplementation(async () => respuesta({ estado: 200, cuerpo: SALUD_OK }));
    await renderizar();
    expect(await screen.findByText(TEXTO_OK, {}, { timeout: ESPERA_MS })).toBeTruthy();
    expect(screen.queryByText(TEXTO_SIN_CONEXION)).toBeNull();
  });

  it('llama a EXPO_PUBLIC_API_URL + "/v1/salud" con el fetch global, y a nada más', async () => {
    fetchSimulado.mockImplementation(async () => respuesta({ estado: 200, cuerpo: SALUD_OK }));
    await renderizar();
    await screen.findByText(TEXTO_OK, {}, { timeout: ESPERA_MS });
    expect(fetchSimulado).toHaveBeenCalled();
    for (const llamada of fetchSimulado.mock.calls) {
      expect(urlDe(llamada)).toBe(`${URL_API}/v1/salud`);
    }
  });
});

describe('PantallaEstado — respuesta distinta de 200 o error de red', () => {
  const casos: Array<[string, () => Promise<Response>]> = [
    ['503 de salud (M-1 A)', async () => respuesta({ estado: 503, cuerpo: SALUD_503 })],
    ['500 ERROR_INTERNO', async () => respuesta({ estado: 500, cuerpo: ERROR_500 })],
    ['404 NO_ENCONTRADO', async () => respuesta({ estado: 404, cuerpo: ERROR_404 })],
    [
      'error de red',
      async () => {
        throw new TypeError('Network request failed');
      },
    ],
  ];

  it.each(casos)('%s → muestra "Sin conexión con el servidor"', async (_nombre, simular) => {
    fetchSimulado.mockImplementation(simular);
    await renderizar();
    expect(
      await screen.findByText(TEXTO_SIN_CONEXION, {}, { timeout: ESPERA_MS }),
    ).toBeTruthy();
    expect(screen.queryByText(TEXTO_OK)).toBeNull();
  });

  it.each(casos)('%s → no muestra resultados negativos ni la palabra prohibida', async (_n, simular) => {
    // AGENTS.md reglas 1 y 7: un error nunca se convierte en "sin requisitoria"/"sin coincidencia".
    fetchSimulado.mockImplementation(simular);
    await renderizar();
    await screen.findByText(TEXTO_SIN_CONEXION, {}, { timeout: ESPERA_MS });
    const arbol = JSON.stringify(screen.toJSON()).toLowerCase();
    expect(arbol).not.toMatch(/sin requisitoria|sin coincidencia|identificad/);
  });
});
