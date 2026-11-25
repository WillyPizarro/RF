import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../api/modelos.dart';
import '../sesion/ambito.dart';
import '../sesion/controlador_sesion.dart';
import 'comunes.dart';

/// Bitácora del supervisor, BIT-01 y BIT-02 (CONTRATO-HU-07 v5 §5). Solo lectura: sin editar,
/// borrar ni exportar. Un error al cargar se muestra como error, nunca como lista vacía (regla 7).

const etiquetaTipo = {
  'LOGIN_OK': 'Inicio de sesión',
  'LOGIN_FALLIDO': 'Intento fallido',
  'CUENTA_BLOQUEADA': 'Cuenta bloqueada',
  'LOGOUT': 'Cierre de sesión',
  'SESION_VENCIDA': 'Sesión vencida',
  'ACCESO_DENEGADO': 'Acceso denegado',
  'CONSULTA_PLACA': 'Consulta de placa',
  'ERROR_FUENTE': 'Error de fuente',
  'CONSULTA_BITACORA': 'Consulta de bitácora',
};

const etiquetaResultado = {
  'con_requisitoria': 'Tiene requisitoria',
  'sin_requisitoria': 'Sin requisitoria registrada',
  'placa_no_registrada': 'Placa no registrada',
  'error': 'Error',
};

const _mensajeError = 'No se pudo cargar la bitácora; intente nuevamente';
const _mensajeVacio = 'No hay registros para estos filtros.';

String _tipo(String tipo) => etiquetaTipo[tipo] ?? tipo;
String _resultado(String resultado) => etiquetaResultado[resultado] ?? resultado;

/// "control_vehicular" → "Control vehicular"; "otro: texto" → "Otro: texto".
String _textoMotivo(String motivo) {
  final partes = motivo.split(': ');
  final legible = partes.first.replaceAll('_', ' ');
  final inicial = legible.isEmpty ? legible : legible[0].toUpperCase() + legible.substring(1);
  return partes.length > 1 ? '$inicial: ${partes.sublist(1).join(': ')}' : inicial;
}

/// dd/mm/aaaa (fecha local) → ISO (UTC) del inicio de ese día (más `diasExtra`); null si no es
/// válida.
String? _fechaAIso(String texto, [int diasExtra = 0]) {
  final partes = RegExp(r'^(\d{1,2})/(\d{1,2})/(\d{4})$').firstMatch(texto.trim());
  if (partes == null) return null;
  final d = int.parse(partes[1]!);
  final m = int.parse(partes[2]!);
  final a = int.parse(partes[3]!);
  final fecha = DateTime(a, m, d);
  if (fecha.year != a || fecha.month != m || fecha.day != d) return null;
  return DateTime(a, m, d + diasExtra).toUtc().toIso8601String();
}

class _Filtros {
  const _Filtros({this.usuario, this.desde, this.hasta, this.tipo, this.resultado});
  final String? usuario;
  final String? desde;
  final String? hasta;
  final String? tipo;
  final String? resultado;

  String consulta(String? cursor) {
    final pares = <String>[];
    void poner(String clave, String? valor) {
      if (valor != null && valor.isNotEmpty) {
        pares.add('$clave=${Uri.encodeQueryComponent(valor)}');
      }
    }

    poner('usuario', usuario);
    poner('desde', desde);
    poner('hasta', hasta);
    poner('tipo', tipo);
    poner('resultado', resultado);
    poner('cursor', cursor);
    return pares.isEmpty ? '' : '?${pares.join('&')}';
  }
}

enum _Carga { cargando, lista, error }

class PantallaBitacora extends StatefulWidget {
  const PantallaBitacora({super.key});

  @override
  State<PantallaBitacora> createState() => _EstadoPantallaBitacora();
}

class _EstadoPantallaBitacora extends State<PantallaBitacora> {
  late final ControladorSesion _sesion;
  List<RegistroBitacora> _registros = [];
  String? _cursor;
  _Carga _carga = _Carga.cargando;
  bool _errorMas = false;
  bool _cargandoMas = false;
  RegistroBitacora? _detalle;
  _Filtros _filtros = const _Filtros();
  int _pedido = 0;

  // Valores escritos en los filtros, antes de aplicarlos.
  final _usuario = TextEditingController();
  final _desde = TextEditingController();
  final _hasta = TextEditingController();
  String? _tipoElegido;
  String? _resultadoElegido;
  bool _errorFecha = false;

  // Los filtros van plegados (como en BIT-01): así sus etiquetas no se confunden con las de la lista.
  bool _verFiltros = false;

  @override
  void initState() {
    super.initState();
    _sesion = AmbitoSesion.leer(context);
    _sesion.registrarAtras(_atras);
    unawaited(_cargar(const _Filtros()));
  }

  @override
  void dispose() {
    _sesion.quitarAtras(_atras);
    _usuario.dispose();
    _desde.dispose();
    _hasta.dispose();
    super.dispose();
  }

  /// Atrás: del detalle a la lista; de la lista al inicio del supervisor.
  bool _atras() {
    if (_detalle != null) {
      setState(() => _detalle = null);
    } else {
      _sesion.mostrar(Pantalla.inicio);
    }
    return true;
  }

  Future<void> _cargar(_Filtros aplicados) async {
    final actual = ++_pedido;
    setState(() {
      _carga = _Carga.cargando;
      _errorMas = false;
    });
    try {
      final respuesta = await _sesion.llamarAutenticado('/v1/bitacora${aplicados.consulta(null)}');
      if (!mounted || actual != _pedido || respuesta == null) return;
      final pagina = respuesta.estado == 200 ? PaginaBitacora.desde(respuesta.cuerpo) : null;
      if (pagina != null) {
        setState(() {
          _registros = pagina.registros;
          _cursor = pagina.siguienteCursor;
          _carga = _Carga.lista;
        });
        return;
      }
    } catch (_) {
      // sin red: error, nunca lista vacía
    }
    if (mounted && actual == _pedido) setState(() => _carga = _Carga.error);
  }

  Future<void> _cargarMas() async {
    final cursor = _cursor;
    if (cursor == null || _cargandoMas) return;
    final actual = _pedido;
    setState(() {
      _cargandoMas = true;
      _errorMas = false;
    });
    try {
      final respuesta = await _sesion.llamarAutenticado('/v1/bitacora${_filtros.consulta(cursor)}');
      if (!mounted || actual != _pedido || respuesta == null) return;
      final pagina = respuesta.estado == 200 ? PaginaBitacora.desde(respuesta.cuerpo) : null;
      if (pagina != null) {
        setState(() {
          _registros = [..._registros, ...pagina.registros];
          _cursor = pagina.siguienteCursor;
        });
        return;
      }
      setState(() => _errorMas = true);
    } catch (_) {
      if (mounted) setState(() => _errorMas = true);
    } finally {
      if (mounted) setState(() => _cargandoMas = false);
    }
  }

  void _aplicarFiltros() {
    final desde = _desde.text.trim();
    final hasta = _hasta.text.trim();
    final isoDesde = desde.isEmpty ? '' : _fechaAIso(desde);
    final isoHasta = hasta.isEmpty ? '' : _fechaAIso(hasta, 1); // "hasta" incluye ese día
    if (isoDesde == null || isoHasta == null) {
      setState(() => _errorFecha = true);
      return;
    }
    final usuario = _usuario.text.trim();
    final nuevos = _Filtros(
      usuario: usuario.isEmpty ? null : usuario,
      desde: isoDesde.isEmpty ? null : isoDesde,
      hasta: isoHasta.isEmpty ? null : isoHasta,
      tipo: _tipoElegido,
      resultado: _resultadoElegido,
    );
    setState(() {
      _errorFecha = false;
      _filtros = nuevos;
      _verFiltros = false;
    });
    unawaited(_cargar(nuevos));
  }

  @override
  Widget build(BuildContext context) {
    final detalle = _detalle;
    if (detalle != null) {
      return _DetalleRegistro(registro: detalle, alVolver: () => setState(() => _detalle = null));
    }
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          Encabezado(titulo: 'Bitácora', alVolver: () => _sesion.mostrar(Pantalla.inicio)),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _panelFiltros(),
                  if (_carga == _Carga.cargando)
                    const Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Espera()),
                  if (_carga == _Carga.error)
                    _ErrorCarga(alReintentar: () => unawaited(_cargar(_filtros))),
                  if (_carga == _Carga.lista && _registros.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: Text(
                        _mensajeVacio,
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 16, color: Colores.tenue),
                      ),
                    ),
                  if (_carga == _Carga.lista)
                    for (final r in _registros)
                      _Tarjeta(registro: r, alTocar: () => setState(() => _detalle = r)),
                  if (_carga == _Carga.lista && _errorMas)
                    _ErrorCarga(alReintentar: () => unawaited(_cargarMas())),
                  if (_carga == _Carga.lista && _cursor != null && !_errorMas)
                    _cargandoMas
                        ? const Padding(
                            padding: EdgeInsets.symmetric(vertical: 16),
                            child: Espera(),
                          )
                        : Boton(
                            texto: 'Cargar más',
                            variante: VarianteBoton.secundario,
                            alTocar: () => unawaited(_cargarMas()),
                          ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _panelFiltros() {
    const estiloEtiqueta = TextStyle(fontSize: 14, color: Colores.texto);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colores.neutroBorde),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            button: true,
            expanded: _verFiltros,
            child: InkWell(
              onTap: () => setState(() => _verFiltros = !_verFiltros),
              child: ConstrainedBox(
                constraints: const BoxConstraints(minHeight: 44),
                child: Row(
                  children: [
                    const Text(
                      'Filtros',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Colores.texto,
                      ),
                    ),
                    Expanded(
                      child: ExcludeSemantics(
                        child: Padding(
                          padding: const EdgeInsets.only(left: 6),
                          child: Text(
                            _verFiltros ? '▴' : '▾',
                            style: const TextStyle(fontSize: 14, color: Colores.texto),
                          ),
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colores.neutroBorde),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'PA 24',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: Colores.tenue,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          if (_verFiltros) ...[
            const SizedBox(height: 10),
            const EtiquetaCampo('Usuario', estilo: estiloEtiqueta),
            const SizedBox(height: 4),
            CampoTexto(etiqueta: 'Usuario', controlador: _usuario),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const EtiquetaCampo('Desde', estilo: estiloEtiqueta),
                      const SizedBox(height: 4),
                      CampoTexto(
                        etiqueta: 'Desde',
                        controlador: _desde,
                        pista: 'dd/mm/aaaa',
                        teclado: TextInputType.datetime,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const EtiquetaCampo('Hasta', estilo: estiloEtiqueta),
                      const SizedBox(height: 4),
                      CampoTexto(
                        etiqueta: 'Hasta',
                        controlador: _hasta,
                        pista: 'dd/mm/aaaa',
                        teclado: TextInputType.datetime,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (_errorFecha)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Text(
                  'Use fechas con el formato dd/mm/aaaa.',
                  style: TextStyle(color: Colores.errorBorde),
                ),
              ),
            const SizedBox(height: 10),
            const Text('Tipo', style: estiloEtiqueta),
            const SizedBox(height: 4),
            _Chips(
              opciones: etiquetaTipo,
              elegido: _tipoElegido,
              alElegir: (v) => setState(() => _tipoElegido = v),
            ),
            const SizedBox(height: 10),
            const Text('Resultado', style: estiloEtiqueta),
            const SizedBox(height: 4),
            _Chips(
              opciones: etiquetaResultado,
              elegido: _resultadoElegido,
              alElegir: (v) => setState(() => _resultadoElegido = v),
            ),
            const SizedBox(height: 12),
            Boton(
              texto: 'Aplicar filtros',
              variante: VarianteBoton.secundario,
              alTocar: _aplicarFiltros,
            ),
          ],
        ],
      ),
    );
  }
}

class _Chips extends StatelessWidget {
  const _Chips({required this.opciones, required this.elegido, required this.alElegir});

  final Map<String, String> opciones;
  final String? elegido;
  final ValueChanged<String?> alElegir;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        for (final MapEntry(key: valor, value: etiqueta) in opciones.entries)
          Semantics(
            checked: elegido == valor,
            child: Material(
              color: elegido == valor ? Colores.primario : Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24),
                side: BorderSide(color: elegido == valor ? Colores.primario : Colores.borde),
              ),
              child: InkWell(
                customBorder: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                onTap: () => alElegir(elegido == valor ? null : valor),
                // Mide lo que su texto (varias por fila en el Wrap) y 48 dp de alto (UX obs. 2).
                child: ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 48),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    child: Align(
                      widthFactor: 1,
                      heightFactor: 1,
                      child: Text(
                        etiqueta,
                        style: TextStyle(
                          fontSize: 14,
                          color: elegido == valor ? Colors.white : Colores.texto,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _ErrorCarga extends StatelessWidget {
  const _ErrorCarga({required this.alReintentar});

  final VoidCallback alReintentar;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colores.advertencia,
          border: Border.all(color: Colores.advertenciaBorde),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Ícono como en PLA-07 (revisión UX HU-03/07, obs. 2), oculto para el lector.
            const ExcludeSemantics(
              child: Text('⚠', textAlign: TextAlign.center, style: TextStyle(fontSize: 32)),
            ),
            const SizedBox(height: 6),
            const Text(
              _mensajeError,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colores.texto),
            ),
            const SizedBox(height: 12),
            Boton(texto: 'Reintentar', alTocar: alReintentar),
          ],
        ),
      ),
    );
  }
}

class _Tarjeta extends StatelessWidget {
  const _Tarjeta({required this.registro, required this.alTocar});

  final RegistroBitacora registro;
  final VoidCallback alTocar;

  @override
  Widget build(BuildContext context) {
    const estiloDetalle = TextStyle(fontSize: 14, color: Colores.texto);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Semantics(
        button: true,
        child: Material(
          color: Colores.fondo,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: Colores.borde),
          ),
          child: InkWell(
            onTap: alTocar,
            customBorder: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            child: Container(
              constraints: const BoxConstraints(minHeight: 48),
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${fechaHoraCorta(registro.ocurridoEn)} · ${registro.usuario ?? 'sistema'}',
                          style: const TextStyle(fontSize: 14, color: Colores.tenue),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF4DC),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: const Text(
                          'SINTÉTICO',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF7A5A00),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _tipo(registro.tipoEvento),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colores.texto,
                    ),
                  ),
                  if (registro.placa != null) ...[
                    const SizedBox(height: 2),
                    Text('Placa ${registro.placa}', style: estiloDetalle),
                  ],
                  if (registro.resultado != null) ...[
                    const SizedBox(height: 2),
                    Text(_resultado(registro.resultado!), style: estiloDetalle),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DetalleRegistro extends StatelessWidget {
  const _DetalleRegistro({required this.registro, required this.alVolver});

  final RegistroBitacora registro;
  final VoidCallback alVolver;

  @override
  Widget build(BuildContext context) {
    final r = registro;
    final idCorto = r.id.length > 8 ? r.id.substring(0, 8) : r.id;
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          // Título corto; el id completo va en el campo "ID" (CONTRATO-HU-07 v3).
          Encabezado(titulo: 'Registro #$idCorto', alVolver: alVolver),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: Colores.neutro,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Row(
                      children: [
                        ExcludeSemantics(
                          child: Padding(
                            padding: EdgeInsets.only(right: 8),
                            child: Text('🔒', style: TextStyle(fontSize: 16)),
                          ),
                        ),
                        Text(
                          'Registro de solo lectura',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Colores.texto,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _Campo('ID', r.id),
                  _Campo('Usuario', r.usuario ?? 'sistema'),
                  _Campo('Fecha y hora', fechaHoraCompleta(r.ocurridoEn)),
                  _Campo('Tipo', _tipo(r.tipoEvento)),
                  if (r.placa != null) _Campo('Placa', r.placa!),
                  if (r.motivo != null && r.motivo!.isNotEmpty)
                    _Campo('Motivo', _textoMotivo(r.motivo!)),
                  if (r.resultado != null && r.resultado!.isNotEmpty)
                    _Campo('Resultado', _resultado(r.resultado!)),
                  if (r.codigoError != null && r.codigoError!.isNotEmpty)
                    _Campo('Código de error', r.codigoError!),
                  // Solo en los registros faciales (HU-05); nunca en los de placa.
                  if (r.capturaId != null && r.capturaId!.isNotEmpty)
                    _Campo('ID de captura', r.capturaId!),
                  if (r.score != null) _Campo('Score', _numero(r.score!)),
                  const SizedBox(height: 20),
                  const Text(
                    'Origen: datos sintéticos',
                    style: TextStyle(fontSize: 15, color: Colores.tenue),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Como `String(numero)` en JavaScript: 1.0 → "1", 0.42 → "0.42".
String _numero(num n) => n == n.truncate() ? n.toInt().toString() : n.toString();

class _Campo extends StatelessWidget {
  const _Campo(this.nombre, this.valor);

  final String nombre;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Text.rich(
        TextSpan(
          children: [
            TextSpan(
              text: '$nombre: ',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            TextSpan(text: valor),
          ],
        ),
        style: const TextStyle(fontSize: 16, color: Colores.texto),
      ),
    );
  }
}
