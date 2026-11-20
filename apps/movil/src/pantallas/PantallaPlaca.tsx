import { ComponentRef, useCallback, useEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  ActivityIndicator,
  BackHandler,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  consultarPlaca,
  FormatoPlaca,
  Motivo,
  obtenerMotivos,
  RespuestaConsultaPlaca,
  RespuestaMotivos,
} from '../api/placas';
import { usarSesion } from '../estado/sesion';
import { Boton, colores, Encabezado, fechaHora, FranjaPrototipo } from './comunes';

/**
 * Consulta de placa, PLA-01 a PLA-08 (CONTRATO-HU-03 v3 §6).
 *
 * - El catalogo de motivos y el formato de placa salen de GET /v1/motivos: la app no los fija.
 * - Sin motivo, "Otro" corto o formato invalido no se envia nada (PLA-02, PLA-03).
 * - Ningun error se muestra como resultado (regla 7): 503, 502, red o algo inesperado → PLA-07.
 * - El resultado vive solo en el estado de esta pantalla (ADR-0013): nada en el dispositivo.
 */

const MOTIVO_OTRO = 'otro';
const OTRO_MINIMO = 10;
const MENSAJE_ERROR = 'No se pudo completar la consulta; intente nuevamente';
const TEXTO_SIN_MOTIVO = 'Indique el motivo de la consulta.';
const TEXTO_OTRO_CORTO = 'Describa el motivo (mínimo 10 caracteres).';

type Catalogo = { motivos: Motivo[]; formato: FormatoPlaca };

type Vista =
  | { tipo: 'cargando' }
  | { tipo: 'sin_catalogo' }
  | { tipo: 'formulario' }
  | { tipo: 'consultando'; placa: string }
  | { tipo: 'resultado'; respuesta: RespuestaConsultaPlaca }
  | { tipo: 'error' };

function normalizar(placa: string): string {
  return placa.trim().toUpperCase();
}

function cumpleFormato(placa: string, regex: string): boolean {
  try {
    return new RegExp(regex).test(placa);
  } catch {
    // Una regex que JavaScript no entiende no bloquea: la API valida igual (§2).
    return true;
  }
}

export default function PantallaPlaca() {
  const mostrar = usarSesion((estado) => estado.mostrar);
  const [catalogo, setCatalogo] = useState<Catalogo | null>(null);
  const [vista, setVista] = useState<Vista>({ tipo: 'cargando' });
  const [placa, setPlaca] = useState('');
  const [motivo, setMotivo] = useState<string | null>(null);
  const [motivoTexto, setMotivoTexto] = useState('');
  const [errorMotivo, setErrorMotivo] = useState<string | null>(null);
  const [errorPlaca, setErrorPlaca] = useState<string | null>(null);
  const montada = useRef(true);
  const refMotivo = useRef<ComponentRef<typeof Text>>(null);
  const refOtro = useRef<ComponentRef<typeof TextInput>>(null);

  const cargarCatalogo = useCallback(async () => {
    setVista({ tipo: 'cargando' });
    try {
      const respuesta = await obtenerMotivos();
      if (!montada.current || respuesta === null) return;
      if (respuesta.estado === 200 && respuesta.cuerpo?.motivos && respuesta.cuerpo?.formato_placa) {
        const cuerpo = respuesta.cuerpo as RespuestaMotivos;
        setCatalogo({ motivos: cuerpo.motivos, formato: cuerpo.formato_placa });
        setVista({ tipo: 'formulario' });
        return;
      }
    } catch {
      // sin red: se muestra como error, nunca como formulario sin motivos
    }
    if (montada.current) setVista({ tipo: 'sin_catalogo' });
  }, []);

  useEffect(() => {
    montada.current = true;
    void cargarCatalogo();
    return () => {
      montada.current = false;
    };
  }, [cargarCatalogo]);

  const volverAlFormulario = useCallback(() => setVista({ tipo: 'formulario' }), []);

  const nuevaConsulta = useCallback(() => {
    setPlaca('');
    setMotivo(null);
    setMotivoTexto('');
    setErrorMotivo(null);
    setErrorPlaca(null);
    setVista({ tipo: 'formulario' });
  }, []);

  // Atras: desde un resultado o un error vuelve al formulario; desde el formulario, al inicio.
  useEffect(() => {
    const suscripcion = BackHandler.addEventListener('hardwareBackPress', () => {
      if (vista.tipo === 'consultando') return true;
      if (vista.tipo === 'resultado' || vista.tipo === 'error') {
        volverAlFormulario();
      } else {
        mostrar('inicio');
      }
      return true;
    });
    return () => suscripcion.remove();
  }, [vista.tipo, mostrar, volverAlFormulario]);

  /** Lleva el foco (y el del lector de pantalla) al campo del motivo (PLA-02). */
  function enfocarMotivo() {
    if (motivo === MOTIVO_OTRO && refOtro.current) {
      refOtro.current.focus();
      AccessibilityInfo.sendAccessibilityEvent(refOtro.current, 'focus');
    } else if (refMotivo.current) {
      AccessibilityInfo.sendAccessibilityEvent(refMotivo.current, 'focus');
    }
  }

  async function enviar(placaEnviada: string, codigo: string, texto: string | null) {
    setVista({ tipo: 'consultando', placa: placaEnviada });
    try {
      const respuesta = await consultarPlaca(placaEnviada, codigo, texto);
      if (!montada.current || respuesta === null) return;
      const cuerpo = respuesta.cuerpo;
      if (respuesta.estado === 200 && cuerpo?.resultado && cuerpo?.placa) {
        const resultado = (cuerpo as RespuestaConsultaPlaca).resultado;
        if (resultado === 'con_requisitoria' || resultado === 'sin_requisitoria' || resultado === 'placa_no_registrada') {
          setVista({ tipo: 'resultado', respuesta: cuerpo as RespuestaConsultaPlaca });
          return;
        }
      }
      if (respuesta.estado === 422 && cuerpo?.codigo === 'MOTIVO_REQUERIDO' && cuerpo?.mensaje) {
        setErrorMotivo(`${cuerpo.mensaje}.`);
        setVista({ tipo: 'formulario' });
        return;
      }
      if (respuesta.estado === 422 && cuerpo?.codigo === 'PLACA_FORMATO_INVALIDO' && cuerpo?.mensaje) {
        setErrorPlaca(cuerpo.mensaje);
        setVista({ tipo: 'formulario' });
        return;
      }
    } catch {
      // red caida: PLA-07
    }
    if (montada.current) setVista({ tipo: 'error' });
  }

  function alConsultar() {
    if (!catalogo || vista.tipo === 'consultando') return;
    const placaNormal = normalizar(placa);
    let faltaMotivo: string | null = null;
    if (!motivo) {
      faltaMotivo = TEXTO_SIN_MOTIVO;
    } else if (motivo === MOTIVO_OTRO && motivoTexto.trim().length < OTRO_MINIMO) {
      faltaMotivo = TEXTO_OTRO_CORTO;
    }
    const formatoMalo = cumpleFormato(placaNormal, catalogo.formato.regex)
      ? null
      : `El formato de placa no es válido. Formato esperado: ${catalogo.formato.descripcion}`;
    setErrorMotivo(faltaMotivo);
    setErrorPlaca(formatoMalo);
    if (faltaMotivo) {
      // El foco va al campo del motivo (PLA-02).
      setTimeout(enfocarMotivo, 0);
      return;
    }
    if (formatoMalo || !motivo) return;
    void enviar(placaNormal, motivo, motivo === MOTIVO_OTRO ? motivoTexto.trim() : null);
  }

  function reintentar() {
    if (!motivo) {
      volverAlFormulario();
      return;
    }
    void enviar(normalizar(placa), motivo, motivo === MOTIVO_OTRO ? motivoTexto.trim() : null);
  }

  function textoDelMotivo(codigo: string, texto: string | null | undefined): string {
    if (codigo === MOTIVO_OTRO && texto) return texto;
    return catalogo?.motivos.find((m) => m.codigo === codigo)?.descripcion ?? codigo;
  }

  // --- vistas -------------------------------------------------------------------------------------

  if (vista.tipo === 'resultado') {
    const r = vista.respuesta;
    const estilo =
      r.resultado === 'con_requisitoria'
        ? estilos.bloqueCon
        : r.resultado === 'sin_requisitoria'
          ? estilos.bloqueSin
          : estilos.bloqueNoRegistrada;
    const estiloTexto = r.resultado === 'con_requisitoria' ? estilos.textoCon : estilos.textoNeutro;
    const enunciado =
      r.resultado === 'con_requisitoria'
        ? 'TIENE REQUISITORIA'
        : r.resultado === 'sin_requisitoria'
          ? 'Sin requisitoria registrada en la fuente consultada'
          : 'Placa no registrada en la fuente consultada. Verifique la placa.';
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Encabezado titulo="Resultado" alVolver={volverAlFormulario} />
        <ScrollView contentContainerStyle={estilos.cuerpo}>
          <View style={[estilos.bloque, estilo]} accessibilityRole="summary">
            <Text style={[estilos.placaResultado, estiloTexto]}>{r.placa}</Text>
            <Text style={[estilos.enunciado, estiloTexto, r.resultado === 'con_requisitoria' && estilos.enunciadoCon]}>
              {enunciado}
            </Text>
          </View>
          <Text style={estilos.dato}>Motivo: {textoDelMotivo(r.motivo.codigo, r.motivo.texto)}</Text>
          <Text style={estilos.dato}>Consultado: {fechaHora(r.consultado_en)}</Text>
          <View style={estilos.espacio} />
          {r.resultado === 'placa_no_registrada' ? (
            <Boton texto="Volver" onPress={volverAlFormulario} />
          ) : (
            <Boton texto="Nueva consulta" onPress={nuevaConsulta} />
          )}
        </ScrollView>
      </View>
    );
  }

  if (vista.tipo === 'error') {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Encabezado titulo="Consultar placa" alVolver={volverAlFormulario} />
        <View style={[estilos.cuerpo, estilos.centro]}>
          <View style={[estilos.bloque, estilos.bloqueError]} accessibilityRole="alert">
            <Text style={estilos.iconoError} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
              ⚠
            </Text>
            <Text style={estilos.textoError}>{MENSAJE_ERROR}</Text>
          </View>
          <Boton texto="Reintentar" onPress={reintentar} />
          <View style={estilos.separador} />
          <Boton texto="Volver" variante="secundario" onPress={volverAlFormulario} />
        </View>
      </View>
    );
  }

  if (vista.tipo === 'sin_catalogo') {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Encabezado titulo="Consultar placa" alVolver={() => mostrar('inicio')} />
        <View style={[estilos.cuerpo, estilos.centro]}>
          <View style={[estilos.bloque, estilos.bloqueError]} accessibilityRole="alert">
            <Text style={estilos.iconoError} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
              ⚠
            </Text>
            <Text style={estilos.textoError}>{MENSAJE_ERROR}</Text>
          </View>
          <Boton texto="Reintentar" onPress={() => void cargarCatalogo()} />
          <View style={estilos.separador} />
          <Boton texto="Volver" variante="secundario" onPress={() => mostrar('inicio')} />
        </View>
      </View>
    );
  }

  if (vista.tipo === 'cargando' || !catalogo) {
    return (
      <View style={estilos.contenedor}>
        <FranjaPrototipo />
        <Encabezado titulo="Consultar placa" alVolver={() => mostrar('inicio')} />
        <View style={[estilos.cuerpo, estilos.centro]}>
          <ActivityIndicator accessibilityLabel="Cargando" />
        </View>
      </View>
    );
  }

  const consultando = vista.tipo === 'consultando';
  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <Encabezado titulo="Consultar placa" alVolver={() => mostrar('inicio')} />
      <ScrollView contentContainerStyle={estilos.cuerpo} keyboardShouldPersistTaps="handled">
        <Text style={estilos.etiqueta} nativeID="etiqueta-placa">
          Placa
        </Text>
        <View style={estilos.filaPlaca}>
          <TextInput
            accessibilityLabel="Placa"
            accessibilityLabelledBy="etiqueta-placa"
            autoCapitalize="characters"
            autoCorrect={false}
            value={placa}
            onChangeText={(valor) => setPlaca(valor.toUpperCase())}
            style={[estilos.campo, estilos.campoPlaca, errorPlaca && estilos.campoConError]}
            editable={!consultando}
            placeholder="ABC-123"
          />
          {/* Lectura con camara: llega con HU-04 (CONTRATO-HU-02 decision 4). */}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Leer con cámara"
            accessibilityState={{ disabled: true }}
            disabled
            style={estilos.camara}
          >
            <Text style={estilos.textoCamara}>📷</Text>
          </Pressable>
        </View>
        {errorPlaca ? <MensajeCampo texto={errorPlaca} /> : null}

        <Text ref={refMotivo} style={estilos.etiqueta} nativeID="etiqueta-motivo">
          Motivo de consulta *
        </Text>
        <View
          accessible={false}
          accessibilityRole="radiogroup"
          accessibilityLabelledBy="etiqueta-motivo"
          style={[estilos.grupoMotivo, errorMotivo && motivo !== MOTIVO_OTRO && estilos.campoConError]}
        >
          {catalogo.motivos.map((m) => {
            const elegido = motivo === m.codigo;
            return (
              <Pressable
                key={m.codigo}
                accessibilityRole="radio"
                accessibilityState={{ checked: elegido, disabled: consultando }}
                disabled={consultando}
                onPress={() => {
                  setMotivo(m.codigo);
                  setErrorMotivo(null);
                }}
                style={[estilos.opcionMotivo, elegido && estilos.opcionElegida]}
              >
                <Text style={estilos.marcaRadio} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
                  {elegido ? '◉' : '○'}
                </Text>
                <Text style={estilos.textoOpcion}>{m.descripcion}</Text>
              </Pressable>
            );
          })}
        </View>
        {motivo === MOTIVO_OTRO ? (
          <>
            <Text style={estilos.etiqueta} nativeID="etiqueta-otro">
              Describa el motivo *
            </Text>
            <TextInput
              ref={refOtro}
              accessibilityLabel="Describa el motivo *"
              accessibilityLabelledBy="etiqueta-otro"
              value={motivoTexto}
              onChangeText={setMotivoTexto}
              style={[estilos.campo, errorMotivo && estilos.campoConError]}
              editable={!consultando}
              placeholder="Mínimo 10 caracteres"
            />
          </>
        ) : null}
        {errorMotivo ? <MensajeCampo texto={errorMotivo} /> : null}

        <View style={estilos.espacio} />
        <Boton texto="Consultar" onPress={alConsultar} deshabilitado={consultando} />
        {consultando ? (
          <View style={estilos.consultando} accessibilityLiveRegion="polite">
            <ActivityIndicator />
            <Text style={estilos.textoConsultando}>Consultando…</Text>
            <Text style={estilos.textoConsultando}>Placa {vista.placa}</Text>
          </View>
        ) : null}
      </ScrollView>
    </View>
  );
}

function MensajeCampo({ texto }: { texto: string }) {
  return (
    <View style={estilos.mensajeCampo} accessibilityRole="alert" accessibilityLiveRegion="polite">
      <Text style={estilos.iconoCampo} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        ⚠
      </Text>
      <Text style={estilos.textoMensajeCampo}>{texto}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  cuerpo: { padding: 20 },
  centro: { flex: 1, justifyContent: 'center' },
  etiqueta: { fontSize: 15, color: colores.texto, marginTop: 16, marginBottom: 6, fontWeight: '600' },
  filaPlaca: { flexDirection: 'row', alignItems: 'center' },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 17,
    color: colores.texto,
  },
  campoPlaca: { flex: 1, fontFamily: 'monospace', fontSize: 22, letterSpacing: 2 },
  campoConError: { borderColor: colores.errorBorde, borderWidth: 2 },
  camara: {
    marginLeft: 8,
    minWidth: 52,
    minHeight: 52,
    borderRadius: 6,
    backgroundColor: '#E3E7EC',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.6,
  },
  textoCamara: { fontSize: 22 },
  grupoMotivo: { borderWidth: 1, borderColor: colores.borde, borderRadius: 6 },
  opcionMotivo: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 48,
    paddingHorizontal: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colores.borde,
  },
  opcionElegida: { backgroundColor: colores.info },
  marcaRadio: { fontSize: 18, marginRight: 10, color: colores.primario },
  textoOpcion: { fontSize: 16, color: colores.texto },
  mensajeCampo: { flexDirection: 'row', marginTop: 6 },
  iconoCampo: { color: colores.errorBorde, marginRight: 6, fontSize: 15 },
  textoMensajeCampo: { flex: 1, color: colores.errorBorde, fontSize: 15 },
  espacio: { height: 24 },
  separador: { height: 12 },
  consultando: { alignItems: 'center', marginTop: 16 },
  textoConsultando: { fontSize: 16, color: colores.texto, marginTop: 6 },
  bloque: { borderRadius: 8, padding: 20, marginBottom: 16, borderWidth: 2 },
  bloqueCon: { backgroundColor: colores.alerta, borderColor: colores.alerta },
  bloqueSin: { backgroundColor: colores.neutro, borderColor: colores.neutroBorde },
  bloqueNoRegistrada: { backgroundColor: colores.neutroAzul, borderColor: colores.neutroAzulBorde },
  bloqueError: {
    backgroundColor: colores.advertencia,
    borderColor: colores.advertenciaBorde,
    alignItems: 'center',
  },
  placaResultado: { fontFamily: 'monospace', fontSize: 28, fontWeight: '700', letterSpacing: 2 },
  enunciado: { fontSize: 18, marginTop: 8 },
  enunciadoCon: { fontSize: 22, fontWeight: '800' },
  textoCon: { color: '#FFFFFF' },
  textoNeutro: { color: colores.texto },
  dato: { fontSize: 16, color: colores.texto, marginTop: 6 },
  iconoError: { fontSize: 36, marginBottom: 8 },
  textoError: { fontSize: 17, color: colores.texto, textAlign: 'center' },
});
