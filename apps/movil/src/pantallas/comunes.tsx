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
  /** Icono delante del texto, oculto para el lector de pantalla (que lee solo el texto). */
  icono?: string;
};

/** Boton grande a todo el ancho, pensado para uso en la calle (HOME-01). */
export function Boton({ texto, onPress, deshabilitado = false, variante = 'primario', icono }: PropsBoton) {
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
        icono ? estilos.botonConIcono : null,
      ]}
    >
      {icono ? (
        <Text style={estilos.icono} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          {icono}
        </Text>
      ) : null}
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

/** Barra superior de las pantallas internas: flecha atras y titulo. */
export function Encabezado({ titulo, alVolver }: { titulo: string; alVolver: () => void }) {
  return (
    <View style={estilos.encabezado}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Atrás"
        onPress={alVolver}
        style={estilos.flecha}
        hitSlop={8}
      >
        <Text style={estilos.textoFlecha}>←</Text>
      </Pressable>
      <Text style={estilos.tituloEncabezado} accessibilityRole="header">
        {titulo}
      </Text>
    </View>
  );
}

function dosDigitos(n: number): string {
  return String(n).padStart(2, '0');
}

/** dd/mm/aaaa hh:mm en hora local. */
export function fechaHora(iso: string): string {
  const f = new Date(iso);
  return `${dosDigitos(f.getDate())}/${dosDigitos(f.getMonth() + 1)}/${f.getFullYear()} ${dosDigitos(f.getHours())}:${dosDigitos(f.getMinutes())}`;
}

/** dd/mm hh:mm en hora local (tarjetas de BIT-01). */
export function fechaHoraCorta(iso: string): string {
  const f = new Date(iso);
  return `${dosDigitos(f.getDate())}/${dosDigitos(f.getMonth() + 1)} ${dosDigitos(f.getHours())}:${dosDigitos(f.getMinutes())}`;
}

/** dd/mm/aaaa hh:mm:ss en hora local (BIT-02). */
export function fechaHoraCompleta(iso: string): string {
  const f = new Date(iso);
  return `${fechaHora(iso)}:${dosDigitos(f.getSeconds())}`;
}

export const colores = {
  fondo: '#FFFFFF',
  // Fondo de la franja "DATOS SINTETICOS · PROTOTIPO" y de la zona de la barra de estado.
  franja: '#1B1F24',
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
  // Gris azulado de PLA-08 (placa no registrada): neutro, distinto del gris de PLA-06.
  neutroAzul: '#E8EEF4',
  neutroAzulBorde: '#7D93AB',
  // Rojo de PLA-05 (tiene requisitoria).
  alerta: '#B42318',
};

const estilos = StyleSheet.create({
  franja: { backgroundColor: colores.franja, paddingVertical: 6, alignItems: 'center' },
  textoFranja: { color: '#FFD54F', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  boton: {
    flexDirection: 'row',
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
  botonConIcono: { justifyContent: 'center' },
  icono: { fontSize: 22, marginRight: 12 },
  encabezado: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
  },
  flecha: { minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  textoFlecha: { fontSize: 24, color: colores.primario },
  tituloEncabezado: { flex: 1, fontSize: 19, fontWeight: '700', color: colores.texto },
  textoBoton: { color: '#FFFFFF', fontSize: 18, fontWeight: '700', textTransform: 'uppercase' },
  textoSecundario: { color: colores.primario, fontSize: 14, textTransform: 'none' },
  textoDeshabilitado: { color: '#8A939E' },
});
