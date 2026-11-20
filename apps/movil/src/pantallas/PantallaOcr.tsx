import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { abrirAjustes, capturarYLeer, VisorCamara } from '../camara/lectorPlaca';
import { proponerPlaca } from '../camara/placaLeida';
import { Boton, colores, FranjaPrototipo } from './comunes';

/**
 * Lectura de la placa con la camara, OCR-01 a OCR-04 (CONTRATO-HU-04 §3 a §5).
 *
 * - Una foto por toque de "Capturar"; nada se lee sin tocar (regla 6).
 * - Nunca consulta: "Usar esta placa" devuelve la placa a PLA-01 y alli el agente elige el
 *   motivo y toca "Consultar" (§5, decision 3).
 * - No muestra ni guarda ninguna imagen: solo el texto leido, en memoria.
 */

export type PasoOcr = 'visor' | 'confirmar' | 'fallo' | 'sin_permiso';

type Props = {
  /** Paso inicial: el visor si hay permiso, OCR-04 si no. */
  inicio: PasoOcr;
  /** `formato_placa.regex` de GET /v1/motivos (§4). */
  regex: string;
  /** "Usar esta placa": la placa (quiza corregida) vuelve a PLA-01. */
  alUsar: (placa: string) => void;
  /** "✕" (sin cambios) o "Ingresar manualmente" (`manual`: foco en "Placa"). */
  alSalir: (manual: boolean) => void;
};

export default function PantallaOcr({ inicio, regex, alUsar, alSalir }: Props) {
  const [paso, setPaso] = useState<PasoOcr>(inicio);
  const [leida, setLeida] = useState('');
  const [leyendo, setLeyendo] = useState(false);
  const montada = useRef(true);
  const intento = useRef(0);

  useEffect(() => {
    montada.current = true;
    return () => {
      montada.current = false;
      intento.current += 1; // una lectura en curso ya no se usa
    };
  }, []);

  // El "atras" del sistema lo maneja PantallaPlaca: es igual que "✕" (PLA-01 sin cambios).

  async function capturar() {
    if (leyendo) return; // un segundo toque no dispara otra lectura
    const actual = ++intento.current;
    setLeyendo(true);
    let propuesta: string | null = null;
    try {
      const { texto } = await capturarYLeer();
      propuesta = proponerPlaca(texto, regex);
    } catch {
      propuesta = null; // la camara fallo: OCR-03, nunca un resultado (regla 7)
    }
    if (!montada.current || actual !== intento.current) return;
    setLeyendo(false);
    if (propuesta) {
      setLeida(propuesta);
      setPaso('confirmar');
    } else {
      setPaso('fallo');
    }
  }

  function volverAlVisor() {
    setLeida('');
    setPaso('visor');
  }

  const manual = <Boton texto="Ingresar manualmente" variante="secundario" onPress={() => alSalir(true)} />;

  if (paso === 'visor') {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Cabecera alCerrar={() => alSalir(false)} />
        <View style={estilos.visor}>
          <VisorCamara activo />
          {/* Marco de la placa: solo guia visual, no recorta ni lee. */}
          <View style={estilos.capaMarco} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            <View style={estilos.marco} />
          </View>
          {/* Mientras se lee la foto (revision UX HU-04, obs. 1): sin texto nuevo. */}
          {leyendo ? (
            <View style={estilos.capaMarco} pointerEvents="none">
              <View style={estilos.leyendo}>
                <ActivityIndicator size="large" color="#FFFFFF" accessibilityLabel="Cargando" />
              </View>
            </View>
          ) : null}
        </View>
        <View style={estilos.pie}>
          <Text style={estilos.indicacion}>Encuadre la placa y toque Capturar</Text>
          <Boton texto="Capturar" icono="◉" onPress={() => void capturar()} deshabilitado={leyendo} />
          <View style={estilos.separador} />
          {manual}
        </View>
      </View>
    );
  }

  if (paso === 'confirmar') {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Cabecera alCerrar={() => alSalir(false)} />
        <View style={estilos.cuerpo}>
          <Text style={estilos.titulo} nativeID="etiqueta-placa-leida">
            Placa leída
          </Text>
          <TextInput
            accessibilityLabel="Placa leída"
            accessibilityLabelledBy="etiqueta-placa-leida"
            autoCapitalize="characters"
            autoCorrect={false}
            value={leida}
            onChangeText={(valor) => setLeida(valor.toUpperCase())}
            style={estilos.campo}
          />
          <Text style={estilos.ayuda}>Confirme o corrija la placa antes de consultar.</Text>
          <View style={estilos.espacio} />
          <Boton texto="Usar esta placa" onPress={() => alUsar(leida.trim().toUpperCase())} />
          <View style={estilos.separador} />
          <Boton texto="Volver a capturar" variante="secundario" onPress={volverAlVisor} />
        </View>
      </View>
    );
  }

  if (paso === 'fallo') {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Cabecera alCerrar={() => alSalir(false)} />
        <View style={[estilos.cuerpo, estilos.centro]}>
          <View style={estilos.aviso} accessibilityRole="alert">
            <Text style={estilos.iconoAviso} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
              ⚠
            </Text>
            <Text style={estilos.textoAviso}>No se pudo leer la placa. Pruebe de frente y con más luz.</Text>
          </View>
          <Boton texto="Volver a intentar" onPress={volverAlVisor} />
          <View style={estilos.separador} />
          {manual}
        </View>
      </View>
    );
  }

  // OCR-04: sin permiso de camara.
  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <Cabecera alCerrar={() => alSalir(false)} />
      <View style={[estilos.cuerpo, estilos.centro]}>
        <View style={estilos.permiso}>
          <Text style={estilos.iconoPermiso} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            📷✕
          </Text>
          <Text style={estilos.textoPermiso}>La app no tiene permiso para usar la cámara.</Text>
          <Text style={estilos.rutaAjustes}>
            Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara.
          </Text>
        </View>
        <Boton texto="Abrir ajustes" onPress={() => void abrirAjustes().catch(() => undefined)} />
        <View style={estilos.separador} />
        {manual}
      </View>
    </View>
  );
}

function Cabecera({ alCerrar }: { alCerrar: () => void }) {
  return (
    <View style={estilos.cabecera}>
      <Pressable accessibilityRole="button" accessibilityLabel="Cerrar" onPress={alCerrar} style={estilos.cerrar} hitSlop={8}>
        <Text style={estilos.textoCerrar}>✕</Text>
      </Pressable>
      <Text style={estilos.tituloCabecera} accessibilityRole="header">
        Leer placa
      </Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  cabecera: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
  },
  cerrar: { minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  textoCerrar: { fontSize: 22, color: colores.primario },
  tituloCabecera: { flex: 1, fontSize: 19, fontWeight: '700', color: colores.texto },
  visor: { flex: 1, backgroundColor: '#000000', alignItems: 'center', justifyContent: 'center' },
  capaMarco: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, alignItems: 'center', justifyContent: 'center' },
  leyendo: { backgroundColor: 'rgba(0,0,0,0.55)', borderRadius: 40, padding: 18 },
  marco: {
    width: '80%',
    aspectRatio: 2.4,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    borderRadius: 8,
  },
  pie: { padding: 20 },
  indicacion: { fontSize: 16, color: colores.texto, textAlign: 'center', marginBottom: 12 },
  cuerpo: { padding: 20 },
  centro: { flex: 1, justifyContent: 'center' },
  titulo: { fontSize: 20, fontWeight: '700', color: colores.texto, marginBottom: 8 },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 24,
    letterSpacing: 2,
    fontFamily: 'monospace',
    color: colores.texto,
  },
  ayuda: { fontSize: 15, color: colores.tenue, marginTop: 8 },
  espacio: { height: 24 },
  separador: { height: 12 },
  aviso: {
    backgroundColor: colores.advertencia,
    borderColor: colores.advertenciaBorde,
    borderWidth: 2,
    borderRadius: 8,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  iconoAviso: { fontSize: 36, marginBottom: 8 },
  textoAviso: { fontSize: 17, color: colores.texto, textAlign: 'center' },
  permiso: { alignItems: 'center', marginBottom: 24 },
  iconoPermiso: { fontSize: 40, marginBottom: 12 },
  textoPermiso: { fontSize: 18, fontWeight: '700', color: colores.texto, textAlign: 'center' },
  rutaAjustes: { fontSize: 15, color: colores.tenue, textAlign: 'center', marginTop: 8 },
});
