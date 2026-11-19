import { QueryClient } from '@tanstack/react-query';

/**
 * Crea un cliente de TanStack Query con cache solo en memoria y sin persistor (ADR-0013).
 * Sin reintentos automaticos: un error se muestra como error, nunca como resultado.
 * gcTime infinito: no deja temporizadores vivos; la cache se borra al desmontar la pantalla.
 */
export function crearClienteConsultas(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
    },
  });
}
