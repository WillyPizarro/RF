import TextRecognition from '@react-native-ml-kit/text-recognition';
import { Camera, CameraView } from 'expo-camera';
import { File } from 'expo-file-system';
import { createElement, useEffect, useRef } from 'react';
import { Linking, StyleSheet } from 'react-native';

/**
 * Modulo de borde de la camara y el OCR (CONTRATO-HU-04 §1, ADR-0002).
 *
 * Es el UNICO lugar de la app que importa la libreria de camara (expo-camera) y la de OCR
 * (@react-native-ml-kit/text-recognition, ML Kit en el dispositivo, con el modelo incluido: no
 * necesita red). En Jest se reemplaza entero con jest.mock.
 *
 * - Nada lee por su cuenta: el visor solo muestra la imagen; se lee una foto por llamada a
 *   capturarYLeer (regla 6, sin lectura continua).
 * - La foto se guarda en el cache privado de la app solo mientras ML Kit la lee, y se borra en
 *   el `finally`, salga bien o mal. Ninguna funcion devuelve una ruta ni una imagen.
 */

export type PermisoCamara = 'concedido' | 'denegado';

/** Si nunca se pidio, lo pide al sistema. No abre la camara. */
export async function asegurarPermisoCamara(): Promise<PermisoCamara> {
  const actual = await Camera.getCameraPermissionsAsync();
  if (actual.granted) return 'concedido';
  if (!actual.canAskAgain) return 'denegado';
  const pedido = await Camera.requestCameraPermissionsAsync();
  return pedido.granted ? 'concedido' : 'denegado';
}

// La camara montada por VisorCamara (hay un solo visor a la vez: OCR-01).
let camaraActual: CameraView | null = null;
let camaraLista = false;

/** El visor en vivo de OCR-01. No lee nada por su cuenta. */
export function VisorCamara({ activo }: { activo: boolean }) {
  const ref = useRef<CameraView>(null);
  useEffect(() => {
    camaraActual = ref.current;
    return () => {
      if (camaraActual === ref.current) {
        camaraActual = null;
        camaraLista = false;
      }
    };
  }, []);
  return createElement(CameraView, {
    ref,
    style: StyleSheet.absoluteFill,
    facing: 'back',
    active: activo,
    animateShutter: false,
    onCameraReady: () => {
      camaraActual = ref.current;
      camaraLista = true;
    },
    accessibilityLabel: 'Visor de la cámara',
  });
}

function borrar(uri: string): void {
  try {
    const archivo = new File(uri);
    if (archivo.exists) archivo.delete();
  } catch {
    // Si no se pudo borrar, queda en el cache privado de la app (no en la galeria).
  }
}

/**
 * Toma UNA foto, la lee con OCR en el dispositivo, borra la foto y devuelve solo el texto.
 * `texto` es null si no se reconocio ningun texto. Rechaza (throw) si la camara falla.
 */
export async function capturarYLeer(): Promise<{ texto: string | null }> {
  const camara = camaraActual;
  if (!camara || !camaraLista) throw new Error('La cámara no está lista');
  const foto = await camara.takePictureAsync({ quality: 0.8, base64: false, exif: false, shutterSound: false });
  if (!foto?.uri) throw new Error('La cámara no devolvió una foto');
  try {
    const resultado = await TextRecognition.recognize(foto.uri);
    const texto = resultado?.text?.trim() ? resultado.text : null;
    return { texto };
  } finally {
    borrar(foto.uri);
  }
}

/** Abre los ajustes de la app en el sistema (OCR-04). */
export async function abrirAjustes(): Promise<void> {
  await Linking.openSettings();
}
