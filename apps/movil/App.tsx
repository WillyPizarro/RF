import { QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, AppState, BackHandler, StyleSheet, View } from 'react-native';

import { crearClienteConsultas } from './src/estado/clienteConsultas';
import { usarSesion } from './src/estado/sesion';
import PantallaInicio from './src/pantallas/PantallaInicio';
import PantallaLogin from './src/pantallas/PantallaLogin';
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
    // Atras desde ERR-01 vuelve al inicio del rol; en el resto, lo maneja el sistema
    // (no hay pantalla anterior a la que volver).
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
    <QueryClientProvider client={cliente}>
      <View testID="app-raiz" style={estilos.raiz} onTouchStart={registrarInteraccion}>
        {contenido}
      </View>
      <StatusBar style="auto" />
    </QueryClientProvider>
  );
}

const estilos = StyleSheet.create({
  raiz: { flex: 1, backgroundColor: '#FFFFFF' },
  cargando: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
