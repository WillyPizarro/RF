import { Pressable, StyleSheet, Text, View } from 'react-native';

/** Franja fija de todas las pantallas (elemento aprobado por UX, 2026-11-18). */
export function FranjaPrototipo() {
  return (
    <View style={estilos.franja} accessibilityRole="header">
      <Text style={estilos.textoFranja}>DATOS SINTÉTICOS · PROTOTIPO</Text>
    </View>
  );
}

type PropsBoton = {
  texto: string;
  onPress?: () => void;
  deshabilitado?: boolean;
  variante?: 'primario' | 'opcion' | 'secundario';
};

/** Boton grande a todo el ancho, pensado para uso en la calle (HOME-01). */
export function Boton({ texto, onPress, deshabilitado = false, variante = 'primario' }: PropsBoton) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: deshabilitado }}
      disabled={deshabilitado}
      onPress={onPress}
      style={({ pressed }) => [
        estilos.boton,
        variante === 'opcion' && estilos.botonOpcion,
        variante === 'secundario' && estilos.botonSecundario,
        deshabilitado && estilos.botonDeshabilitado,
        pressed && !deshabilitado && estilos.botonPresionado,
      ]}
    >
      <Text
        style={[
          estilos.textoBoton,
          variante === 'secundario' && estilos.textoSecundario,
          deshabilitado && estilos.textoDeshabilitado,
        ]}
      >
        {texto}
      </Text>
    </Pressable>
  );
}

export const colores = {
  fondo: '#FFFFFF',
  texto: '#1B1F24',
  tenue: '#5B6470',
  primario: '#0B4F8A',
  borde: '#C9D1DB',
  info: '#E7F1FB',
  infoBorde: '#7AA7D6',
  error: '#FDECEC',
  errorBorde: '#D9534F',
  advertencia: '#FFF4DC',
  advertenciaBorde: '#E0A526',
  neutro: '#F1F3F5',
  neutroBorde: '#9AA4AF',
};

const estilos = StyleSheet.create({
  franja: { backgroundColor: '#1B1F24', paddingVertical: 6, alignItems: 'center' },
  textoFranja: { color: '#FFD54F', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  boton: {
    backgroundColor: colores.primario,
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 16,
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  botonOpcion: { paddingVertical: 24, marginBottom: 16 },
  botonSecundario: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colores.primario, minHeight: 48, paddingVertical: 8 },
  botonDeshabilitado: { backgroundColor: '#E3E7EC', borderColor: '#E3E7EC' },
  botonPresionado: { opacity: 0.8 },
  textoBoton: { color: '#FFFFFF', fontSize: 18, fontWeight: '700', textTransform: 'uppercase' },
  textoSecundario: { color: colores.primario, fontSize: 14, textTransform: 'none' },
  textoDeshabilitado: { color: '#8A939E' },
});
