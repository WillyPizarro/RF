import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from 'react-native';

import type { Aviso } from '../estado/sesion';
import { usarSesion } from '../estado/sesion';
import { ingresar } from '../sesion/controlador';
import { Boton, colores, FranjaPrototipo } from './comunes';

const MENSAJE_ERROR = 'No se pudo completar la operación; intente nuevamente';

function dosDigitos(n: number): string {
  return String(n).padStart(2, '0');
}

/** "Podrá volver a intentar a las HH:MM (en N min)", en hora local, desde bloqueado_hasta. */
export function textoBloqueo(hastaIso: string, ahora: number = Date.now()): string {
  const hasta = new Date(hastaIso);
  const minutos = Math.max(1, Math.ceil((hasta.getTime() - ahora) / 60_000));
  const hora = `${dosDigitos(hasta.getHours())}:${dosDigitos(hasta.getMinutes())}`;
  return `Cuenta bloqueada temporalmente. Podrá volver a intentar a las ${hora} (en ${minutos} min).`;
}

function Mensaje({ aviso }: { aviso: Aviso }) {
  let texto: string;
  let estilo;
  switch (aviso.tipo) {
    case 'inactividad':
      texto = 'Su sesión se cerró por inactividad. Ingrese de nuevo.';
      estilo = estilos.info;
      break;
    case 'credenciales':
      texto = 'Usuario o clave incorrectos';
      estilo = estilos.error;
      break;
    case 'bloqueo':
      texto = textoBloqueo(aviso.hasta);
      estilo = estilos.advertencia;
      break;
    default:
      texto = MENSAJE_ERROR;
      estilo = estilos.error;
  }
  return (
    <View style={[estilos.mensaje, estilo]} accessibilityRole="alert" accessibilityLiveRegion="polite">
      <Text style={estilos.textoMensaje}>{texto}</Text>
    </View>
  );
}

/** AUTH-01 a AUTH-04 (CONTRATO-HU-01 §4). */
export default function PantallaLogin() {
  const aviso = usarSesion((estado) => estado.aviso);
  const [usuario, setUsuario] = useState('');
  const [clave, setClave] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function alIngresar() {
    if (enviando || !usuario.trim() || !clave) return;
    setEnviando(true);
    const claveEnviada = clave;
    setClave(''); // la clave se vacia en cualquier resultado (AUTH-02, AUTH-04)
    try {
      await ingresar(usuario, claveEnviada);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <View style={estilos.cuerpo}>
        <Text style={estilos.titulo}>Movil Buscador</Text>
        <Text style={estilos.subtitulo}>Acceso solo para personal autorizado</Text>
        {aviso ? <Mensaje aviso={aviso} /> : null}
        <Text style={estilos.etiqueta} nativeID="etiqueta-usuario">
          Usuario
        </Text>
        <TextInput
          accessibilityLabel="Usuario"
          accessibilityLabelledBy="etiqueta-usuario"
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="username"
          value={usuario}
          onChangeText={setUsuario}
          style={estilos.campo}
          editable={!enviando}
        />
        <Text style={estilos.etiqueta} nativeID="etiqueta-clave">
          Clave
        </Text>
        <TextInput
          accessibilityLabel="Clave"
          accessibilityLabelledBy="etiqueta-clave"
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="password"
          secureTextEntry
          value={clave}
          onChangeText={setClave}
          onSubmitEditing={alIngresar}
          style={estilos.campo}
          editable={!enviando}
        />
        <View style={estilos.espacio} />
        <Boton texto="Ingresar" onPress={alIngresar} />
        {enviando ? <ActivityIndicator style={estilos.cargando} accessibilityLabel="Ingresando" /> : null}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  cuerpo: { flex: 1, paddingHorizontal: 24, paddingTop: 48 },
  titulo: { fontSize: 26, fontWeight: '700', color: colores.texto, textAlign: 'center' },
  subtitulo: { fontSize: 15, color: colores.tenue, textAlign: 'center', marginTop: 4, marginBottom: 24 },
  etiqueta: { fontSize: 15, color: colores.texto, marginTop: 12, marginBottom: 4 },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 17,
    color: colores.texto,
  },
  espacio: { height: 24 },
  cargando: { marginTop: 16 },
  mensaje: { borderWidth: 1, borderRadius: 6, padding: 12, marginBottom: 8 },
  textoMensaje: { fontSize: 15, color: colores.texto },
  info: { backgroundColor: colores.info, borderColor: colores.infoBorde },
  error: { backgroundColor: colores.error, borderColor: colores.errorBorde },
  advertencia: { backgroundColor: colores.advertencia, borderColor: colores.advertenciaBorde },
});
