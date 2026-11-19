import * as SecureStore from 'expo-secure-store';

/** Tokens de la sesion en expo-secure-store (ADR-0013). Nada mas se guarda en el dispositivo. */
const CLAVE_ACCESO = 'sesion.token_acceso';
const CLAVE_RENOVACION = 'sesion.token_renovacion';

export async function guardarTokens(tokenAcceso: string, tokenRenovacion: string): Promise<void> {
  await SecureStore.setItemAsync(CLAVE_ACCESO, tokenAcceso);
  await SecureStore.setItemAsync(CLAVE_RENOVACION, tokenRenovacion);
}

export async function leerTokenRenovacion(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(CLAVE_RENOVACION);
  } catch {
    return null;
  }
}

/** Borra todas las claves de la sesion. Nunca falla. */
export async function borrarTokens(): Promise<void> {
  await Promise.all(
    [CLAVE_ACCESO, CLAVE_RENOVACION].map((clave) =>
      SecureStore.deleteItemAsync(clave).catch(() => undefined),
    ),
  );
}
