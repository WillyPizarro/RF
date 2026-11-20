import { QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { ReactNode, useEffect, useState } from 'react';
import { ActivityIndicator, AppState, BackHandler, StyleSheet, View } from 'react-native';
import {
  initialWindowMetrics,
  Metrics,
  SafeAreaProvider,
  useSafeAreaInsets,
} from 'react-native-safe-area-context';

import { crearClienteConsultas } from './src/estado/clienteConsultas';
import { colores } from './src/pantallas/comunes';
import { usarSesion } from './src/estado/sesion';
import PantallaBitacora from './src/pantallas/PantallaBitacora';
import PantallaInicio from './src/pantallas/PantallaInicio';
import PantallaLogin from './src/pantallas/PantallaLogin';
import PantallaPlaca from './src/pantallas/PantallaPlaca';
import PantallaSinPermiso from './src/pantallas/PantallaSinPermiso';
import {
  registrarInteraccion,
  reiniciarLocal,
  restaurar,
  revisarAlVolver,
  usarClienteConsultas,
} from './src/sesion/controlador';

/**
 * App completa (CONTRATO-HU-01 §4 bis): sin expo-router, una pantalla a la vez segun la sesion.
 * Sin pila de navegacion: al cerrar la sesion, "atras" no puede volver a la pantalla anterior.
 */
export default function App() {
  const [cliente] = useState(() => {
    reiniciarLocal();
    return crearClienteConsultas();
  });
  const pantalla = usarSesion((estado) => estado.pantalla);
  const perfil = usarSesion((estado) => estado.perfil);
  const generacion = usarSesion((estado) => estado.generacion);
  const mostrar = usarSesion((estado) => estado.mostrar);

  useEffect(() => {
    usarClienteConsultas(cliente);
    void restaurar();
    return () => {
      reiniciarLocal();
      cliente.clear();
    };
  }, [cliente]);

  useEffect(() => {
    const suscripcion = AppState.addEventListener('change', (estado) => {
      if (estado === 'active') revisarAlVolver();
    });
    return () => suscripcion.remove();
  }, []);

  useEffect(() => {
    // Atras desde ERR-01 vuelve al inicio del rol. Placa y bitacora manejan su propio "atras"
    // (registran su escucha despues, asi que la reciben primero). En el resto, lo maneja el
    // sistema (no hay pantalla anterior a la que volver).
    const suscripcion = BackHandler.addEventListener('hardwareBackPress', () => {
      if (usarSesion.getState().pantalla === 'sin_permiso') {
        usarSesion.getState().mostrar('inicio');
        return true;
      }
      return false;
    });
    return () => suscripcion.remove();
  }, []);

  let contenido;
  if (pantalla === 'inicio' && perfil) {
    contenido = <PantallaInicio perfil={perfil} />;
  } else if (pantalla === 'placa' && perfil) {
    contenido = <PantallaPlaca />;
  } else if (pantalla === 'bitacora' && perfil) {
    contenido = <PantallaBitacora />;
  } else if (pantalla === 'sin_permiso' && perfil) {
    contenido = <PantallaSinPermiso alVolver={() => mostrar('inicio')} />;
  } else if (pantalla === 'cargando') {
    contenido = (
      <View style={estilos.cargando}>
        <ActivityIndicator accessibilityLabel="Cargando" />
      </View>
    );
  } else {
    contenido = <PantallaLogin key={generacion} />;
  }

  return (
    <SafeAreaProvider initialMetrics={initialWindowMetrics ?? METRICAS_SIN_DISPOSITIVO}>
      <QueryClientProvider client={cliente}>
        <ZonaSegura>
          <View testID="app-raiz" style={estilos.raiz} onTouchStart={registrarInteraccion}>
            {contenido}
          </View>
        </ZonaSegura>
        {/* Iconos claros sobre el fondo oscuro de la franja (revision UX HU-04, obs. 2). */}
        <StatusBar style="light" />
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

/** Sin dispositivo (Jest) no hay medidas nativas: se dibuja sin margenes en vez de esperar. */
const METRICAS_SIN_DISPOSITIVO: Metrics = {
  frame: { x: 0, y: 0, width: 0, height: 0 },
  insets: { top: 0, left: 0, right: 0, bottom: 0 },
};

/**
 * Safe area de todas las pantallas, resuelta una sola vez (revision UX HU-04, obs. 2, BLOQUEA):
 * la zona de la barra de estado lleva el fondo de la franja "DATOS SINTETICOS · PROTOTIPO", asi la
 * franja queda debajo de la barra y no la tapa; abajo, la zona de navegacion queda en blanco.
 */
function ZonaSegura({ children }: { children: ReactNode }) {
  const margenes = useSafeAreaInsets();
  return (
    <View style={[estilos.zonaSegura, { paddingTop: margenes.top }]}>
      <View
        style={[
          estilos.contenido,
          { paddingBottom: margenes.bottom, paddingLeft: margenes.left, paddingRight: margenes.right },
        ]}
      >
        {children}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  zonaSegura: { flex: 1, backgroundColor: colores.franja },
  contenido: { flex: 1, backgroundColor: colores.fondo },
  raiz: { flex: 1, backgroundColor: colores.fondo },
  cargando: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
