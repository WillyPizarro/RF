import { StyleSheet, Text, View } from 'react-native';

import { Boton, colores, FranjaPrototipo } from './comunes';

/** ERR-01: respuesta 403 SIN_PERMISO de la API (CONTRATO-HU-02 §3; su prueba es de HU-03). */
export default function PantallaSinPermiso({ alVolver }: { alVolver: () => void }) {
  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <View style={estilos.cuerpo}>
        <Text style={estilos.icono} accessibilityElementsHidden importantForAccessibility="no">
          ⛔
        </Text>
        <Text style={estilos.titulo}>No tiene permiso para usar esta función.</Text>
        <Text style={estilos.detalle}>El intento quedó registrado.</Text>
        <View style={estilos.espacio} />
        <Boton texto="Volver al inicio" onPress={alVolver} />
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  cuerpo: { flex: 1, padding: 24, justifyContent: 'center' },
  icono: { fontSize: 48, textAlign: 'center', marginBottom: 16 },
  titulo: { fontSize: 20, fontWeight: '700', color: colores.texto, textAlign: 'center' },
  detalle: { fontSize: 16, color: colores.tenue, textAlign: 'center', marginTop: 12 },
  espacio: { height: 32 },
});
