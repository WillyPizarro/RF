import { QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { consultarSalud } from '../api/salud';
import { crearClienteConsultas } from '../estado/clienteConsultas';

/** Pantalla tecnica de estado del Sprint 0: consulta GET /v1/salud. Sin logica de negocio. */
function ContenidoEstado() {
  const salud = useQuery({ queryKey: ['salud'], queryFn: consultarSalud });

  return (
    <View style={estilos.contenedor}>
      {salud.isPending ? (
        <ActivityIndicator accessibilityLabel="Cargando" />
      ) : (
        <Text style={estilos.texto}>
          {salud.isSuccess ? 'Conectado' : 'Sin conexión con el servidor'}
        </Text>
      )}
    </View>
  );
}

export default function PantallaEstado() {
  const [cliente] = useState(crearClienteConsultas);
  // Al desmontar no queda nada en cache ni temporizadores pendientes (ADR-0013).
  useEffect(() => () => cliente.clear(), [cliente]);
  return (
    <QueryClientProvider client={cliente}>
      <ContenidoEstado />
    </QueryClientProvider>
  );
}

const estilos = StyleSheet.create({
  contenedor: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  texto: {
    fontSize: 18,
  },
});
