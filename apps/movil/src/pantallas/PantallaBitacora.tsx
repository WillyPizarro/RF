import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, BackHandler, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { FiltrosBitacora, obtenerBitacora, RegistroBitacora, RespuestaBitacora } from '../api/bitacora';
import { usarSesion } from '../estado/sesion';
import { Boton, colores, Encabezado, fechaHoraCompleta, fechaHoraCorta, FranjaPrototipo } from './comunes';

/**
 * Bitacora del supervisor, BIT-01 y BIT-02 (CONTRATO-HU-07 §5). Solo lectura: sin editar, borrar
 * ni exportar. Un error al cargar se muestra como error, nunca como lista vacia (regla 7).
 */

export const ETIQUETA_TIPO: Record<string, string> = {
  LOGIN_OK: 'Inicio de sesión',
  LOGIN_FALLIDO: 'Intento fallido',
  CUENTA_BLOQUEADA: 'Cuenta bloqueada',
  LOGOUT: 'Cierre de sesión',
  SESION_VENCIDA: 'Sesión vencida',
  ACCESO_DENEGADO: 'Acceso denegado',
  CONSULTA_PLACA: 'Consulta de placa',
  ERROR_FUENTE: 'Error de fuente',
  CONSULTA_BITACORA: 'Consulta de bitácora',
};

export const ETIQUETA_RESULTADO: Record<string, string> = {
  con_requisitoria: 'Tiene requisitoria',
  sin_requisitoria: 'Sin requisitoria registrada',
  placa_no_registrada: 'Placa no registrada',
  error: 'Error',
};

const MENSAJE_ERROR = 'No se pudo cargar la bitácora; intente nuevamente';
const MENSAJE_VACIO = 'No hay registros para estos filtros.';

function etiquetaTipo(tipo: string): string {
  return ETIQUETA_TIPO[tipo] ?? tipo;
}

function etiquetaResultado(resultado: string): string {
  return ETIQUETA_RESULTADO[resultado] ?? resultado;
}

/** "control_vehicular" → "Control vehicular"; "otro: texto" → "Otro: texto". */
function textoMotivo(motivo: string): string {
  const [codigo, ...resto] = motivo.split(': ');
  const legible = codigo.replace(/_/g, ' ');
  const inicial = legible.charAt(0).toUpperCase() + legible.slice(1);
  return resto.length ? `${inicial}: ${resto.join(': ')}` : inicial;
}

/** dd/mm/aaaa (fecha local) → ISO del inicio de ese dia (mas `diasExtra`); null si no es valida. */
function fechaAIso(texto: string, diasExtra = 0): string | null {
  const partes = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(texto.trim());
  if (!partes) return null;
  const [d, m, a] = [Number(partes[1]), Number(partes[2]), Number(partes[3])];
  const fecha = new Date(a, m - 1, d);
  if (fecha.getFullYear() !== a || fecha.getMonth() !== m - 1 || fecha.getDate() !== d) return null;
  return new Date(a, m - 1, d + diasExtra).toISOString();
}

type Carga = 'cargando' | 'lista' | 'error';

export default function PantallaBitacora() {
  const mostrar = usarSesion((estado) => estado.mostrar);
  const [registros, setRegistros] = useState<RegistroBitacora[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [carga, setCarga] = useState<Carga>('cargando');
  const [errorMas, setErrorMas] = useState(false);
  const [cargandoMas, setCargandoMas] = useState(false);
  const [detalle, setDetalle] = useState<RegistroBitacora | null>(null);
  const [filtros, setFiltros] = useState<FiltrosBitacora>({});
  // Valores escritos en los filtros, antes de aplicarlos.
  const [usuario, setUsuario] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [tipo, setTipo] = useState<string | null>(null);
  const [resultado, setResultado] = useState<string | null>(null);
  const [errorFecha, setErrorFecha] = useState(false);
  // Los filtros van plegados (como en BIT-01): asi sus etiquetas no se confunden con las de la lista.
  const [verFiltros, setVerFiltros] = useState(false);
  const montada = useRef(true);
  const pedido = useRef(0);

  const cargar = useCallback(async (aplicados: FiltrosBitacora) => {
    const actual = ++pedido.current;
    setCarga('cargando');
    setErrorMas(false);
    try {
      const respuesta = await obtenerBitacora(aplicados, null);
      if (!montada.current || actual !== pedido.current || respuesta === null) return;
      if (respuesta.estado === 200 && Array.isArray(respuesta.cuerpo?.registros)) {
        const cuerpo = respuesta.cuerpo as RespuestaBitacora;
        setRegistros(cuerpo.registros);
        setCursor(cuerpo.siguiente_cursor ?? null);
        setCarga('lista');
        return;
      }
    } catch {
      // sin red: error, nunca lista vacia
    }
    if (montada.current && actual === pedido.current) setCarga('error');
  }, []);

  useEffect(() => {
    montada.current = true;
    void cargar({});
    return () => {
      montada.current = false;
    };
  }, [cargar]);

  async function cargarMas() {
    if (!cursor || cargandoMas) return;
    const actual = pedido.current;
    setCargandoMas(true);
    setErrorMas(false);
    try {
      const respuesta = await obtenerBitacora(filtros, cursor);
      if (!montada.current || actual !== pedido.current || respuesta === null) return;
      if (respuesta.estado === 200 && Array.isArray(respuesta.cuerpo?.registros)) {
        const cuerpo = respuesta.cuerpo as RespuestaBitacora;
        setRegistros((previos) => [...previos, ...cuerpo.registros]);
        setCursor(cuerpo.siguiente_cursor ?? null);
        return;
      }
      setErrorMas(true);
    } catch {
      if (montada.current) setErrorMas(true);
    } finally {
      if (montada.current) setCargandoMas(false);
    }
  }

  function aplicarFiltros() {
    const isoDesde = desde.trim() ? fechaAIso(desde) : undefined;
    const isoHasta = hasta.trim() ? fechaAIso(hasta, 1) : undefined; // "hasta" incluye ese dia
    if (isoDesde === null || isoHasta === null) {
      setErrorFecha(true);
      return;
    }
    setErrorFecha(false);
    const nuevos: FiltrosBitacora = {
      usuario: usuario.trim() || undefined,
      desde: isoDesde,
      hasta: isoHasta,
      tipo: tipo ?? undefined,
      resultado: resultado ?? undefined,
    };
    setFiltros(nuevos);
    setVerFiltros(false);
    void cargar(nuevos);
  }

  // Atras: del detalle a la lista; de la lista al inicio del supervisor.
  useEffect(() => {
    const suscripcion = BackHandler.addEventListener('hardwareBackPress', () => {
      if (detalle) setDetalle(null);
      else mostrar('inicio');
      return true;
    });
    return () => suscripcion.remove();
  }, [detalle, mostrar]);

  if (detalle) {
    return <DetalleRegistro registro={detalle} alVolver={() => setDetalle(null)} />;
  }

  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      <Encabezado titulo="Bitácora" alVolver={() => mostrar('inicio')} />
      <ScrollView contentContainerStyle={estilos.cuerpo} keyboardShouldPersistTaps="handled">
        <View style={estilos.filtros}>
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ expanded: verFiltros }}
            onPress={() => setVerFiltros((v) => !v)}
            style={estilos.filaTitulo}
          >
            <Text style={estilos.tituloFiltros}>Filtros</Text>
            <Text style={estilos.flechaFiltros} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
              {verFiltros ? '▴' : '▾'}
            </Text>
            <Text style={estilos.marcaPa}>PA 24</Text>
          </Pressable>
          {verFiltros ? (
            <>
              <Text style={estilos.etiqueta}>Usuario</Text>
              <TextInput
                accessibilityLabel="Usuario"
                autoCapitalize="none"
                autoCorrect={false}
                value={usuario}
                onChangeText={setUsuario}
                style={estilos.campo}
              />
              <View style={estilos.filaFechas}>
                <View style={estilos.columna}>
                  <Text style={estilos.etiqueta}>Desde</Text>
                  <TextInput
                    accessibilityLabel="Desde"
                    keyboardType="numbers-and-punctuation"
                    placeholder="dd/mm/aaaa"
                    value={desde}
                    onChangeText={setDesde}
                    style={estilos.campo}
                  />
                </View>
                <View style={estilos.espacioH} />
                <View style={estilos.columna}>
                  <Text style={estilos.etiqueta}>Hasta</Text>
                  <TextInput
                    accessibilityLabel="Hasta"
                    keyboardType="numbers-and-punctuation"
                    placeholder="dd/mm/aaaa"
                    value={hasta}
                    onChangeText={setHasta}
                    style={estilos.campo}
                  />
                </View>
              </View>
              {errorFecha ? <Text style={estilos.errorFecha}>Use fechas con el formato dd/mm/aaaa.</Text> : null}
              <Text style={estilos.etiqueta}>Tipo</Text>
              <Chips opciones={ETIQUETA_TIPO} elegido={tipo} alElegir={setTipo} />
              <Text style={estilos.etiqueta}>Resultado</Text>
              <Chips opciones={ETIQUETA_RESULTADO} elegido={resultado} alElegir={setResultado} />
              <View style={estilos.separador} />
              <Boton texto="Aplicar filtros" variante="secundario" onPress={aplicarFiltros} />
            </>
          ) : null}
        </View>

        {carga === 'cargando' ? (
          <ActivityIndicator style={estilos.cargando} accessibilityLabel="Cargando" />
        ) : null}
        {carga === 'error' ? (
          <ErrorCarga alReintentar={() => void cargar(filtros)} />
        ) : null}
        {carga === 'lista' && registros.length === 0 ? <Text style={estilos.vacio}>{MENSAJE_VACIO}</Text> : null}
        {carga === 'lista'
          ? registros.map((r) => <Tarjeta key={r.id} registro={r} alTocar={() => setDetalle(r)} />)
          : null}
        {carga === 'lista' && errorMas ? <ErrorCarga alReintentar={() => void cargarMas()} /> : null}
        {carga === 'lista' && cursor && !errorMas ? (
          cargandoMas ? (
            <ActivityIndicator style={estilos.cargando} accessibilityLabel="Cargando" />
          ) : (
            <Boton texto="Cargar más" variante="secundario" onPress={() => void cargarMas()} />
          )
        ) : null}
      </ScrollView>
    </View>
  );
}

function Chips({
  opciones,
  elegido,
  alElegir,
}: {
  opciones: Record<string, string>;
  elegido: string | null;
  alElegir: (valor: string | null) => void;
}) {
  return (
    <View style={estilos.chips}>
      {Object.entries(opciones).map(([valor, etiqueta]) => {
        const activo = elegido === valor;
        return (
          <Pressable
            key={valor}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: activo }}
            onPress={() => alElegir(activo ? null : valor)}
            style={[estilos.chip, activo && estilos.chipActivo]}
          >
            <Text style={[estilos.textoChip, activo && estilos.textoChipActivo]}>{etiqueta}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function ErrorCarga({ alReintentar }: { alReintentar: () => void }) {
  return (
    <View style={estilos.error} accessibilityRole="alert">
      {/* Icono como en PLA-07 (revision UX HU-03/07, obs. 2), oculto para el lector. */}
      <Text style={estilos.iconoError} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        ⚠
      </Text>
      <Text style={estilos.textoError}>{MENSAJE_ERROR}</Text>
      <View style={estilos.separador} />
      <Boton texto="Reintentar" onPress={alReintentar} />
    </View>
  );
}

function Tarjeta({ registro, alTocar }: { registro: RegistroBitacora; alTocar: () => void }) {
  const placa = (registro.parametros as { placa?: unknown } | null)?.placa;
  return (
    <Pressable accessibilityRole="button" onPress={alTocar} style={estilos.tarjeta}>
      <View style={estilos.filaTarjeta}>
        <Text style={estilos.cuando}>
          {fechaHoraCorta(registro.ocurrido_en)} · {registro.usuario ?? 'sistema'}
        </Text>
        <Text style={estilos.sintetico}>SINTÉTICO</Text>
      </View>
      <Text style={estilos.tipo}>{etiquetaTipo(registro.tipo_evento)}</Text>
      {typeof placa === 'string' ? <Text style={estilos.detalleTarjeta}>Placa {placa}</Text> : null}
      {registro.resultado ? (
        <Text style={estilos.detalleTarjeta}>{etiquetaResultado(registro.resultado)}</Text>
      ) : null}
    </Pressable>
  );
}

function DetalleRegistro({ registro, alVolver }: { registro: RegistroBitacora; alVolver: () => void }) {
  const placa = (registro.parametros as { placa?: unknown } | null)?.placa;
  return (
    <View style={estilos.contenedor}>
      <FranjaPrototipo />
      {/* Titulo corto; el id completo va en el campo "ID" (CONTRATO-HU-07 v3). */}
      <Encabezado titulo={`Registro #${registro.id.slice(0, 8)}`} alVolver={alVolver} />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <View style={estilos.soloLectura}>
          <Text style={estilos.candado} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            🔒
          </Text>
          <Text style={estilos.textoSoloLectura}>Registro de solo lectura</Text>
        </View>
        <Campo nombre="ID" valor={registro.id} />
        <Campo nombre="Usuario" valor={registro.usuario ?? 'sistema'} />
        <Campo nombre="Fecha y hora" valor={fechaHoraCompleta(registro.ocurrido_en)} />
        <Campo nombre="Tipo" valor={etiquetaTipo(registro.tipo_evento)} />
        {typeof placa === 'string' ? <Campo nombre="Placa" valor={placa} /> : null}
        {registro.motivo ? <Campo nombre="Motivo" valor={textoMotivo(registro.motivo)} /> : null}
        {registro.resultado ? <Campo nombre="Resultado" valor={etiquetaResultado(registro.resultado)} /> : null}
        {registro.codigo_error ? <Campo nombre="Código de error" valor={registro.codigo_error} /> : null}
        {/* Solo en los registros faciales (HU-05); nunca en los de placa. */}
        {registro.captura_id ? <Campo nombre="ID de captura" valor={registro.captura_id} /> : null}
        {registro.score !== null && registro.score !== undefined ? (
          <Campo nombre="Score" valor={String(registro.score)} />
        ) : null}
        <Text style={estilos.origen}>Origen: datos sintéticos</Text>
      </ScrollView>
    </View>
  );
}

function Campo({ nombre, valor }: { nombre: string; valor: string }) {
  return (
    <Text style={estilos.campoDetalle}>
      <Text style={estilos.nombreCampo}>{nombre}: </Text>
      {valor}
    </Text>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  cuerpo: { padding: 16 },
  filtros: {
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colores.neutroBorde,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  filaTitulo: { flexDirection: 'row', alignItems: 'center', minHeight: 44 },
  tituloFiltros: { fontSize: 16, fontWeight: '700', color: colores.texto },
  flechaFiltros: { fontSize: 14, color: colores.texto, marginLeft: 6, flex: 1 },
  marcaPa: {
    fontSize: 12,
    fontWeight: '700',
    color: colores.tenue,
    borderWidth: 1,
    borderColor: colores.neutroBorde,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  etiqueta: { fontSize: 14, color: colores.texto, marginTop: 10, marginBottom: 4 },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 16,
    color: colores.texto,
  },
  filaFechas: { flexDirection: 'row' },
  columna: { flex: 1 },
  espacioH: { width: 12 },
  errorFecha: { color: colores.errorBorde, marginTop: 4 },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 16,
    paddingHorizontal: 12,
    minHeight: 36,
    justifyContent: 'center',
    marginRight: 6,
    marginBottom: 6,
  },
  chipActivo: { backgroundColor: colores.primario, borderColor: colores.primario },
  textoChip: { fontSize: 14, color: colores.texto },
  textoChipActivo: { color: '#FFFFFF' },
  separador: { height: 12 },
  cargando: { marginVertical: 16 },
  vacio: { fontSize: 16, color: colores.tenue, textAlign: 'center', marginVertical: 24 },
  error: {
    backgroundColor: colores.advertencia,
    borderColor: colores.advertenciaBorde,
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    marginVertical: 12,
  },
  iconoError: { fontSize: 32, textAlign: 'center', marginBottom: 6 },
  textoError: { fontSize: 16, color: colores.texto, textAlign: 'center' },
  tarjeta: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    minHeight: 48,
  },
  filaTarjeta: { flexDirection: 'row', alignItems: 'center' },
  cuando: { flex: 1, fontSize: 14, color: colores.tenue },
  sintetico: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7A5A00',
    backgroundColor: '#FFF4DC',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tipo: { fontSize: 16, fontWeight: '700', color: colores.texto, marginTop: 4 },
  detalleTarjeta: { fontSize: 14, color: colores.texto, marginTop: 2 },
  soloLectura: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.neutro,
    borderRadius: 6,
    padding: 10,
    marginBottom: 12,
  },
  candado: { fontSize: 16, marginRight: 8 },
  textoSoloLectura: { fontSize: 15, fontWeight: '700', color: colores.texto },
  campoDetalle: { fontSize: 16, color: colores.texto, marginTop: 8 },
  nombreCampo: { fontWeight: '700' },
  origen: { fontSize: 15, color: colores.tenue, marginTop: 20 },
});
