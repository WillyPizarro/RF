/**
 * URL de la API, por configuracion (ADR-0001: la app solo habla con la API).
 * Se lee en cada llamada para no fijarla al importar el modulo.
 */
export function urlApi(): string {
  const url = process.env.EXPO_PUBLIC_API_URL;
  if (!url) {
    throw new Error('Falta EXPO_PUBLIC_API_URL');
  }
  return url.replace(/\/+$/, '');
}
