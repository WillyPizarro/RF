import { urlApi } from '../config';

export type RespuestaApi = { estado: number; cuerpo: any };

/**
 * Llama a la API con el fetch global (ADR-0001: la app solo habla con la API).
 * Devuelve el estado y el cuerpo JSON (o null). Un error de red lanza: nunca se convierte en un
 * resultado (AGENTS.md regla 7).
 */
export async function llamarApi(
  ruta: string,
  opciones: { metodo?: 'GET' | 'POST'; cuerpo?: unknown; token?: string } = {},
): Promise<RespuestaApi> {
  const cabeceras: Record<string, string> = { Accept: 'application/json' };
  if (opciones.cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json';
  if (opciones.token) cabeceras.Authorization = `Bearer ${opciones.token}`;
  const respuesta = await fetch(`${urlApi()}${ruta}`, {
    method: opciones.metodo ?? 'GET',
    headers: cabeceras,
    body: opciones.cuerpo === undefined ? undefined : JSON.stringify(opciones.cuerpo),
  });
  let cuerpo: any = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    cuerpo = null;
  }
  return { estado: respuesta.status, cuerpo };
}
