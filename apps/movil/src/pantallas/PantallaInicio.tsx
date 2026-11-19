import { StyleSheet, Text, View } from 'react-native';

import type { Perfil, Rol } from '../api/sesion';
import { salir } from '../sesion/controlador';
import { Boton, colores, FranjaPrototipo } from './comunes';

const NOMBRE_ROL: Record<Rol, string> = {
  agente: 'Agente',
  revisor: 'Revisor',
  supervisor: 'Supervisor',
};

/**
 * Opciones de cada rol (CONTRATO-HU-02 §3). Todas deshabilitadas hasta que su HU construya la
 * pantalla (decision 4): placa en HU-03, rostro y "Mis verificaciones" en HU-05/HU-06,
 * revision en HU-06 y bitacora en HU-07.
 */
const OPCIONES: Record<Rol, { principales: string[]; enlace?: string }> = {
  agente: { principales: ['Consultar placa', 'Verificar rostro'], enlace: 'Mis verificaciones' },
  revisor: { principales: ['Pendientes de revisión'] },
  supervisor: { principales: ['Bitácora'] },
};

/** HOME-01 (agente) y los inicios del revisor y del supervisor. El rol sale de GET /v1/me. */
export default function PantallaInicio({ perfil }: { perfil: Perfil }) {
  const opciones = OPCIONES[perfil.rol];
  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <View style={estilos.encabezado}>
        <View style={estilos.quien}>
          <Text style={estilos.saludo}>Hola, {perfil.nombre}</Text>
          <Text style={estilos.rol}>Rol: {NOMBRE_ROL[perfil.rol]}</Text>
        </View>
        <View style={estilos.salir}>
          <Boton texto="Salir" variante="secundario" onPress={() => void salir()} />
        </View>
      </View>
      <View style={estilos.cuerpo}>
        {opciones?.principales.map((texto) => (
          <Boton key={texto} texto={texto} variante="opcion" deshabilitado />
        ))}
        {opciones?.enlace ? <Boton texto={opciones.enlace} variante="secundario" deshabilitado /> : null}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  encabezado: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
  },
  quien: { flex: 1 },
  saludo: { fontSize: 20, fontWeight: '700', color: colores.texto },
  rol: { fontSize: 15, color: colores.tenue, marginTop: 2 },
  salir: { width: 96 },
  cuerpo: { padding: 20 },
});
