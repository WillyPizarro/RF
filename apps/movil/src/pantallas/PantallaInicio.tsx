import { StyleSheet, Text, View } from 'react-native';

import type { Perfil, Rol } from '../api/sesion';
import { Pantalla, usarSesion } from '../estado/sesion';
import { salir } from '../sesion/controlador';
import { Boton, colores, FranjaPrototipo } from './comunes';

const NOMBRE_ROL: Record<Rol, string> = {
  agente: 'Agente',
  revisor: 'Revisor',
  supervisor: 'Supervisor',
};

type Opcion = {
  texto: string;
  /** Pantalla que abre; sin pantalla, la opcion se muestra deshabilitada (CONTRATO-HU-02 decision 4). */
  abre?: Pantalla;
  icono?: string;
};

/**
 * Opciones de cada rol (CONTRATO-HU-02 §3). Habilitadas las que ya tienen pantalla: placa (HU-03)
 * y bitacora (HU-07). Rostro y "Mis verificaciones" llegan con HU-05/HU-06 y la revision con HU-06.
 */
const OPCIONES: Record<Rol, { principales: Opcion[]; enlace?: Opcion }> = {
  agente: {
    // Icono 🚗: revision UX de HU-01/02, observacion 2. El 👤 de "Verificar rostro" llega con HU-05.
    principales: [{ texto: 'Consultar placa', abre: 'placa', icono: '🚗' }, { texto: 'Verificar rostro' }],
    enlace: { texto: 'Mis verificaciones' },
  },
  revisor: { principales: [{ texto: 'Pendientes de revisión' }] },
  supervisor: { principales: [{ texto: 'Bitácora', abre: 'bitacora' }] },
};

/** HOME-01 (agente) y los inicios del revisor y del supervisor. El rol sale de GET /v1/me. */
export default function PantallaInicio({ perfil }: { perfil: Perfil }) {
  const mostrar = usarSesion((estado) => estado.mostrar);
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
        {opciones?.principales.map(({ texto, abre, icono }) => (
          <Boton
            key={texto}
            texto={texto}
            icono={icono}
            variante="opcion"
            deshabilitado={!abre}
            onPress={abre ? () => mostrar(abre) : undefined}
          />
        ))}
        {opciones?.enlace ? (
          <Boton
            texto={opciones.enlace.texto}
            variante="secundario"
            deshabilitado={!opciones.enlace.abre}
            onPress={opciones.enlace.abre ? () => mostrar(opciones.enlace!.abre!) : undefined}
          />
        ) : null}
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
