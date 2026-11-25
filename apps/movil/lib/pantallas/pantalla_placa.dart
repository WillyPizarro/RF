import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';

import '../api/modelos.dart';
import '../bordes/bordes.dart';
import '../placa/placa_leida.dart';
import '../sesion/ambito.dart';
import '../sesion/controlador_sesion.dart';
import 'comunes.dart';
import 'pantalla_ocr.dart';

/// Consulta de placa, PLA-01 a PLA-08 (CONTRATO-HU-03 v5 §6), con la entrada a OCR (HU-04 v6).
///
/// - El catálogo de motivos y el formato de placa salen de GET /v1/motivos: la app no los fija.
/// - Sin motivo, "Otro" corto o formato inválido no se envía nada (PLA-02, PLA-03).
/// - Ningún error se muestra como resultado (regla 7): 503, 502, red o algo inesperado → PLA-07.
/// - El resultado vive solo en el estado de esta pantalla (ADR-0013): nada en el dispositivo.

const _motivoOtro = 'otro';
const _otroMinimo = 10;
const _mensajeError = 'No se pudo completar la consulta; intente nuevamente';
const _textoSinMotivo = 'Indique el motivo de la consulta.';
const _textoOtroCorto = 'Describa el motivo (mínimo 10 caracteres).';

enum _TipoVista { cargando, sinCatalogo, ocr, formulario, consultando, resultado, error }

String _normalizar(String placa) => placa.trim().toUpperCase();

/// Pasa a mayúsculas lo que se escribe, sin mover el cursor.
class _AMayusculas extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue anterior, TextEditingValue nuevo) =>
      nuevo.copyWith(text: nuevo.text.toUpperCase());
}

class PantallaPlaca extends StatefulWidget {
  const PantallaPlaca({super.key});

  @override
  State<PantallaPlaca> createState() => _EstadoPantallaPlaca();
}

class _EstadoPantallaPlaca extends State<PantallaPlaca> {
  late final ControladorSesion _sesion;
  Catalogo? _catalogo;
  _TipoVista _vista = _TipoVista.cargando;
  PasoOcr _inicioOcr = PasoOcr.visor;
  String _placaConsultada = '';
  ResultadoPlaca? _resultado;

  final _placa = TextEditingController();
  final _motivoTexto = TextEditingController();
  final _focoPlaca = FocusNode();
  final _focoOtro = FocusNode();
  final _focoMotivo = FocusNode();
  String? _motivo;
  String? _errorMotivo;
  String? _errorPlaca;
  bool _pidiendoPermiso = false;

  @override
  void initState() {
    super.initState();
    _sesion = AmbitoSesion.leer(context);
    _sesion.registrarAtras(_atras);
    unawaited(_cargarCatalogo());
  }

  @override
  void dispose() {
    _sesion.quitarAtras(_atras);
    _placa.dispose();
    _motivoTexto.dispose();
    _focoPlaca.dispose();
    _focoOtro.dispose();
    _focoMotivo.dispose();
    super.dispose();
  }

  void _ver(_TipoVista vista) {
    if (mounted) setState(() => _vista = vista);
  }

  /// Atrás: desde un resultado, un error u OCR vuelve al formulario; desde el formulario, al
  /// inicio. Mientras consulta, no hace nada.
  bool _atras() {
    switch (_vista) {
      case _TipoVista.consultando:
        return true;
      case _TipoVista.resultado:
      case _TipoVista.error:
      case _TipoVista.ocr: // en OCR-01 a OCR-04, atrás es como "✕": PLA-01 sin cambios
        _volverAlFormulario();
        return true;
      default:
        _sesion.mostrar(Pantalla.inicio);
        return true;
    }
  }

  Future<void> _cargarCatalogo() async {
    _ver(_TipoVista.cargando);
    try {
      final respuesta = await _sesion.llamarAutenticado('/v1/motivos');
      if (!mounted || respuesta == null) return;
      final catalogo = respuesta.estado == 200 ? Catalogo.desde(respuesta.cuerpo) : null;
      if (catalogo != null) {
        setState(() {
          _catalogo = catalogo;
          _vista = _TipoVista.formulario;
        });
        return;
      }
    } catch (_) {
      // sin red: se muestra como error, nunca como formulario sin motivos
    }
    _ver(_TipoVista.sinCatalogo);
  }

  void _volverAlFormulario() => _ver(_TipoVista.formulario);

  void _nuevaConsulta() {
    _placa.clear();
    _motivoTexto.clear();
    setState(() {
      _motivo = null;
      _errorMotivo = null;
      _errorPlaca = null;
      _vista = _TipoVista.formulario;
    });
  }

  /// 📷 de PLA-01 (CONTRATO-HU-04 §2): con permiso, OCR-01; sin permiso, OCR-04.
  Future<void> _abrirCamara() async {
    if (_pidiendoPermiso) return;
    setState(() => _pidiendoPermiso = true);
    PasoOcr inicio;
    try {
      final permiso = await AmbitoSesion.lector(context).asegurarPermisoCamara();
      inicio = permiso == PermisoCamara.concedido ? PasoOcr.visor : PasoOcr.sinPermiso;
    } catch (_) {
      inicio = PasoOcr.fallo; // no se pudo consultar el permiso: OCR-03, nunca una pantalla en blanco
    }
    if (!mounted) return;
    setState(() {
      _pidiendoPermiso = false;
      _inicioOcr = inicio;
      _vista = _TipoVista.ocr;
    });
  }

  /// Vuelta de OCR a PLA-01. "Usar esta placa" solo cambia la placa: el motivo queda igual.
  void _usarPlacaLeida(String leida) {
    _placa.text = leida;
    setState(() {
      _errorPlaca = null;
      _vista = _TipoVista.formulario;
    });
  }

  void _salirDeOcr(bool manual) {
    _volverAlFormulario();
    if (manual) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _focoPlaca.requestFocus();
      });
    }
  }

  /// Lleva el foco al campo del motivo (PLA-02).
  void _enfocarMotivo() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_motivo == _motivoOtro) {
        _focoOtro.requestFocus();
      } else {
        _focoMotivo.requestFocus();
      }
    });
  }

  Future<void> _enviar(String placa, String codigo, String? texto) async {
    setState(() {
      _placaConsultada = placa;
      _vista = _TipoVista.consultando;
    });
    try {
      final respuesta = await _sesion.llamarAutenticado(
        '/v1/consultas/placa',
        metodo: 'POST',
        cuerpo: {'placa': placa, 'motivo_codigo': codigo, 'motivo_texto': texto},
      );
      if (!mounted || respuesta == null) return;
      if (respuesta.estado == 200) {
        final resultado = ResultadoPlaca.desde(respuesta.cuerpo);
        if (resultado != null) {
          setState(() {
            _resultado = resultado;
            _vista = _TipoVista.resultado;
          });
          return;
        }
      }
      final mensaje = respuesta.objeto?['mensaje'];
      if (respuesta.estado == 422 && respuesta.codigo == 'MOTIVO_REQUERIDO' && mensaje is String) {
        setState(() {
          _errorMotivo = '$mensaje.';
          _vista = _TipoVista.formulario;
        });
        return;
      }
      if (respuesta.estado == 422 &&
          respuesta.codigo == 'PLACA_FORMATO_INVALIDO' &&
          mensaje is String) {
        setState(() {
          _errorPlaca = mensaje;
          _vista = _TipoVista.formulario;
        });
        return;
      }
    } catch (_) {
      // red caída: PLA-07
    }
    _ver(_TipoVista.error);
  }

  void _alConsultar() {
    final catalogo = _catalogo;
    if (catalogo == null || _vista == _TipoVista.consultando) return;
    final placa = _normalizar(_placa.text);
    String? faltaMotivo;
    if (_motivo == null) {
      faltaMotivo = _textoSinMotivo;
    } else if (_motivo == _motivoOtro && _motivoTexto.text.trim().length < _otroMinimo) {
      faltaMotivo = _textoOtroCorto;
    }
    final formatoMalo = cumpleFormato(placa, catalogo.formato.regex)
        ? null
        : 'El formato de placa no es válido. Formato esperado: ${catalogo.formato.descripcion}';
    setState(() {
      _errorMotivo = faltaMotivo;
      _errorPlaca = formatoMalo;
    });
    if (faltaMotivo != null) {
      _enfocarMotivo();
      return;
    }
    final motivo = _motivo;
    if (formatoMalo != null || motivo == null) return;
    unawaited(_enviar(placa, motivo, motivo == _motivoOtro ? _motivoTexto.text.trim() : null));
  }

  void _reintentar() {
    final motivo = _motivo;
    if (motivo == null) {
      _volverAlFormulario();
      return;
    }
    unawaited(_enviar(
      _normalizar(_placa.text),
      motivo,
      motivo == _motivoOtro ? _motivoTexto.text.trim() : null,
    ));
  }

  String _textoDelMotivo(String codigo, String? texto) {
    if (codigo == _motivoOtro && texto != null && texto.isNotEmpty) return texto;
    for (final m in _catalogo?.motivos ?? const <Motivo>[]) {
      if (m.codigo == codigo) return m.descripcion;
    }
    return codigo;
  }

  // --- vistas ----------------------------------------------------------------------------------

  Widget _marco({required String titulo, required VoidCallback alVolver, required Widget cuerpo}) {
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          Encabezado(titulo: titulo, alVolver: alVolver),
          Expanded(child: cuerpo),
        ],
      ),
    );
  }

  Widget _bloqueError(VoidCallback alReintentar, VoidCallback alVolver) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            liveRegion: true,
            child: Container(
              padding: const EdgeInsets.all(20),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Colores.advertencia,
                border: Border.all(color: Colores.advertenciaBorde, width: 2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Column(
                children: [
                  ExcludeSemantics(child: Text('⚠', style: TextStyle(fontSize: 36))),
                  SizedBox(height: 8),
                  Text(
                    _mensajeError,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 17, color: Colores.texto),
                  ),
                ],
              ),
            ),
          ),
          Boton(texto: 'Reintentar', alTocar: alReintentar),
          const SizedBox(height: 12),
          Boton(texto: 'Volver', variante: VarianteBoton.secundario, alTocar: alVolver),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final catalogo = _catalogo;
    void alInicio() => _sesion.mostrar(Pantalla.inicio);

    if (_vista == _TipoVista.ocr && catalogo != null) {
      return PantallaOcr(
        inicio: _inicioOcr,
        regex: catalogo.formato.regex,
        alUsar: _usarPlacaLeida,
        alSalir: _salirDeOcr,
      );
    }
    if (_vista == _TipoVista.resultado && _resultado != null) return _vistaResultado(_resultado!);
    if (_vista == _TipoVista.error) {
      return _marco(
        titulo: 'Consultar placa',
        alVolver: _volverAlFormulario,
        cuerpo: _bloqueError(_reintentar, _volverAlFormulario),
      );
    }
    if (_vista == _TipoVista.sinCatalogo) {
      return _marco(
        titulo: 'Consultar placa',
        alVolver: alInicio,
        cuerpo: _bloqueError(() => unawaited(_cargarCatalogo()), alInicio),
      );
    }
    if (_vista == _TipoVista.cargando || catalogo == null) {
      return _marco(titulo: 'Consultar placa', alVolver: alInicio, cuerpo: const Espera());
    }
    return _marco(
      titulo: 'Consultar placa',
      alVolver: alInicio,
      cuerpo: _formulario(catalogo),
    );
  }

  Widget _formulario(Catalogo catalogo) {
    final consultando = _vista == _TipoVista.consultando;
    const estiloEtiqueta = TextStyle(fontSize: 15, color: Colores.texto, fontWeight: FontWeight.w600);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const EtiquetaCampo('Placa', estilo: estiloEtiqueta),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: _CampoPlaca(
                  controlador: _placa,
                  foco: _focoPlaca,
                  conError: _errorPlaca != null,
                  soloLectura: consultando,
                ),
              ),
              const SizedBox(width: 8),
              // Lectura con cámara (HU-04): solo lee al tocar "Capturar" en OCR-01.
              BotonIcono(
                etiqueta: 'Leer con cámara',
                simbolo: '📷',
                tamano: 52,
                deshabilitado: consultando || _pidiendoPermiso,
                alTocar: () => unawaited(_abrirCamara()),
                estilo: const TextStyle(fontSize: 22),
                decoracion: BoxDecoration(
                  color: Colores.info,
                  border: Border.all(color: Colores.primario),
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
            ],
          ),
          if (_errorPlaca != null) MensajeCampo(_errorPlaca!),
          const SizedBox(height: 16),
          const Text('Motivo de consulta *', style: estiloEtiqueta),
          const SizedBox(height: 6),
          Focus(
            focusNode: _focoMotivo,
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(
                  color: _errorMotivo != null && _motivo != _motivoOtro
                      ? Colores.errorBorde
                      : Colores.borde,
                  width: _errorMotivo != null && _motivo != _motivoOtro ? 2 : 1,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Column(
                children: [
                  for (final m in catalogo.motivos)
                    _OpcionMotivo(
                      descripcion: m.descripcion,
                      elegido: _motivo == m.codigo,
                      deshabilitado: consultando,
                      alElegir: () => setState(() {
                        _motivo = m.codigo;
                        _errorMotivo = null;
                      }),
                    ),
                ],
              ),
            ),
          ),
          if (_motivo == _motivoOtro) ...[
            const SizedBox(height: 16),
            const EtiquetaCampo('Describa el motivo *', estilo: estiloEtiqueta),
            const SizedBox(height: 6),
            CampoTexto(
              etiqueta: 'Describa el motivo *',
              controlador: _motivoTexto,
              focusNode: _focoOtro,
              soloLectura: consultando,
              conError: _errorMotivo != null,
              pista: 'Mínimo 10 caracteres',
            ),
          ],
          if (_errorMotivo != null) MensajeCampo(_errorMotivo!),
          const SizedBox(height: 24),
          Boton(texto: 'Consultar', alTocar: _alConsultar, deshabilitado: consultando),
          if (consultando)
            Semantics(
              liveRegion: true,
              child: Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Column(
                  children: [
                    const Espera(),
                    const SizedBox(height: 6),
                    const Text('Consultando…', style: TextStyle(fontSize: 16, color: Colores.texto)),
                    const SizedBox(height: 6),
                    Text(
                      'Placa $_placaConsultada',
                      style: const TextStyle(fontSize: 16, color: Colores.texto),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _vistaResultado(ResultadoPlaca r) {
    final con = r.resultado == 'con_requisitoria';
    final Color fondo;
    final Color borde;
    final String enunciado;
    switch (r.resultado) {
      case 'con_requisitoria':
        fondo = Colores.alerta;
        borde = Colores.alerta;
        enunciado = 'TIENE REQUISITORIA';
      case 'sin_requisitoria':
        fondo = Colores.neutro;
        borde = Colores.neutroBorde;
        enunciado = 'Sin requisitoria registrada en la fuente consultada';
      default:
        fondo = Colores.neutroAzul;
        borde = Colores.neutroAzulBorde;
        enunciado = 'Placa no registrada en la fuente consultada. Verifique la placa.';
    }
    final colorTexto = con ? Colors.white : Colores.texto;
    const estiloDato = TextStyle(fontSize: 16, color: Colores.texto);
    return _marco(
      titulo: 'Resultado',
      alVolver: _volverAlFormulario,
      cuerpo: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: fondo,
                border: Border.all(color: borde, width: 2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    r.placa,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 28,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 2,
                      color: colorTexto,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    enunciado,
                    style: TextStyle(
                      fontSize: con ? 22 : 18,
                      fontWeight: con ? FontWeight.w800 : FontWeight.w400,
                      color: colorTexto,
                    ),
                  ),
                ],
              ),
            ),
            Text('Motivo: ${_textoDelMotivo(r.motivoCodigo, r.motivoTexto)}', style: estiloDato),
            const SizedBox(height: 6),
            Text('Consultado: ${fechaHora(r.consultadoEn)}', style: estiloDato),
            const SizedBox(height: 24),
            if (r.resultado == 'placa_no_registrada')
              Boton(texto: 'Volver', alTocar: _volverAlFormulario)
            else
              Boton(texto: 'Nueva consulta', alTocar: _nuevaConsulta),
          ],
        ),
      ),
    );
  }
}

class _CampoPlaca extends StatelessWidget {
  const _CampoPlaca({
    required this.controlador,
    required this.foco,
    required this.conError,
    required this.soloLectura,
  });

  final TextEditingController controlador;
  final FocusNode foco;
  final bool conError;
  final bool soloLectura;

  @override
  Widget build(BuildContext context) {
    OutlineInputBorder borde(Color color, double ancho) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: color, width: ancho),
        );
    final normal = conError ? borde(Colores.errorBorde, 2) : borde(Colores.borde, 1);
    return Semantics(
      // Nodo propio: la etiqueta queda exacta (el texto de ayuda no se le suma).
      container: true,
      label: 'Placa',
      child: TextField(
        controller: controlador,
        focusNode: foco,
        readOnly: soloLectura,
        autocorrect: false,
        enableSuggestions: false,
        textCapitalization: TextCapitalization.characters,
        inputFormatters: [_AMayusculas()],
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 22,
          letterSpacing: 2,
          color: Colores.texto,
        ),
        decoration: InputDecoration(
          isDense: true,
          // La ayuda no entra en la etiqueta de accesibilidad ("Placa" exacto).
          hint: const ExcludeSemantics(
            child: Text(
              'ABC-123',
              style: TextStyle(fontFamily: 'monospace', fontSize: 22, color: Colores.tenue),
            ),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          enabledBorder: normal,
          border: normal,
          focusedBorder: conError ? borde(Colores.errorBorde, 2) : borde(Colores.primario, 2),
        ),
      ),
    );
  }
}

class _OpcionMotivo extends StatelessWidget {
  const _OpcionMotivo({
    required this.descripcion,
    required this.elegido,
    required this.deshabilitado,
    required this.alElegir,
  });

  final String descripcion;
  final bool elegido;
  final bool deshabilitado;
  final VoidCallback alElegir;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      inMutuallyExclusiveGroup: true,
      checked: elegido,
      enabled: !deshabilitado,
      child: Material(
        color: elegido ? Colores.info : Colors.transparent,
        child: InkWell(
          onTap: deshabilitado ? null : alElegir,
          child: Container(
            constraints: const BoxConstraints(minHeight: 48),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colores.borde, width: 0.5)),
            ),
            child: Row(
              children: [
                ExcludeSemantics(
                  child: Padding(
                    padding: const EdgeInsets.only(right: 10),
                    child: Text(
                      elegido ? '◉' : '○',
                      style: const TextStyle(fontSize: 18, color: Colores.primario),
                    ),
                  ),
                ),
                Expanded(
                  child: Text(descripcion, style: const TextStyle(fontSize: 16, color: Colores.texto)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
