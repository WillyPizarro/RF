import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';

import '../placa/placa_leida.dart';
import '../sesion/ambito.dart';
import 'comunes.dart';

/// Lectura de la placa con la cámara, OCR-01 a OCR-04 (CONTRATO-HU-04 v6 §3 a §5).
///
/// - Una foto por toque de "Capturar"; nada se lee sin tocar (regla 6).
/// - Nunca consulta: "Usar esta placa" devuelve la placa a PLA-01 y allí el agente elige el motivo
///   y toca "Consultar" (§5, decisión 3).
/// - No muestra ni guarda ninguna imagen: solo el texto leído, en memoria.
/// - El "atrás" del sistema lo maneja PantallaPlaca: es igual que "✕" (PLA-01 sin cambios).

enum PasoOcr { visor, confirmar, fallo, sinPermiso }

const _textoAviso =
    'Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. '
    'Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de '
    'uso y un código de esta instalación.';

class _AMayusculas extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue anterior, TextEditingValue nuevo) =>
      nuevo.copyWith(text: nuevo.text.toUpperCase());
}

class PantallaOcr extends StatefulWidget {
  const PantallaOcr({
    super.key,
    required this.inicio,
    required this.regex,
    required this.alUsar,
    required this.alSalir,
  });

  /// Paso inicial: el visor si hay permiso, OCR-04 si no.
  final PasoOcr inicio;

  /// `formato_placa.regex` de GET /v1/motivos (§4).
  final String regex;

  /// "Usar esta placa": la placa (quizá corregida) vuelve a PLA-01.
  final ValueChanged<String> alUsar;

  /// "✕" (sin cambios) o "Ingresar manualmente" (`true`: foco en "Placa").
  final ValueChanged<bool> alSalir;

  @override
  State<PantallaOcr> createState() => _EstadoPantallaOcr();
}

class _EstadoPantallaOcr extends State<PantallaOcr> {
  late PasoOcr _paso = widget.inicio;
  final _leida = TextEditingController();
  bool _leyendo = false;
  int _intento = 0;

  @override
  void dispose() {
    _intento += 1; // una lectura en curso ya no se usa
    _leida.dispose();
    super.dispose();
  }

  Future<void> _capturar() async {
    final sesion = AmbitoSesion.leer(context);
    if (_leyendo || !sesion.avisoMlkitVisto) return; // un segundo toque no dispara otra lectura
    final actual = ++_intento;
    setState(() => _leyendo = true);
    String? propuesta;
    try {
      final lectura = await AmbitoSesion.lector(context).capturarYLeer();
      propuesta = proponerPlaca(lectura.texto, widget.regex);
    } catch (_) {
      propuesta = null; // la cámara falló: OCR-03, nunca un resultado (regla 7)
    }
    if (!mounted || actual != _intento) return;
    setState(() {
      _leyendo = false;
      if (propuesta != null) {
        _leida.text = propuesta;
        _paso = PasoOcr.confirmar;
      } else {
        _paso = PasoOcr.fallo;
      }
    });
  }

  void _volverAlVisor() {
    _leida.clear();
    setState(() => _paso = PasoOcr.visor);
  }

  Widget _marco(Widget cuerpo) {
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          _Cabecera(alCerrar: () => widget.alSalir(false)),
          Expanded(child: cuerpo),
        ],
      ),
    );
  }

  Widget get _manual => Boton(
        texto: 'Ingresar manualmente',
        variante: VarianteBoton.secundario,
        alTocar: () => widget.alSalir(true),
      );

  @override
  Widget build(BuildContext context) {
    switch (_paso) {
      case PasoOcr.visor:
        return _vistaVisor(context);
      case PasoOcr.confirmar:
        return _vistaConfirmar();
      case PasoOcr.fallo:
        return _vistaFallo();
      case PasoOcr.sinPermiso:
        return _vistaSinPermiso();
    }
  }

  Widget _vistaVisor(BuildContext context) {
    final avisoVisto = AmbitoSesion.de(context).avisoMlkitVisto;
    final lector = AmbitoSesion.lector(context);
    return _marco(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: ColoredBox(
              color: Colors.black,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  lector.visorCamara(activo: true),
                  // Marco de la placa: solo guía visual, no recorta ni lee.
                  IgnorePointer(
                    child: ExcludeSemantics(
                      child: Center(
                        child: FractionallySizedBox(
                          widthFactor: 0.8,
                          child: AspectRatio(
                            aspectRatio: 2.4,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.white, width: 3),
                                borderRadius: BorderRadius.circular(8),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  if (!avisoVisto)
                    // Sobre el visor; tocar fuera de la tarjeta no hace nada (v5).
                    ColoredBox(
                      color: const Color(0x99000000),
                      child: Center(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(20),
                          child: Semantics(
                            liveRegion: true,
                            child: Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: Colores.fondo,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  const Text(
                                    'Antes de leer la placa',
                                    style: TextStyle(
                                      fontSize: 19,
                                      fontWeight: FontWeight.w700,
                                      color: Colores.texto,
                                    ),
                                  ),
                                  const SizedBox(height: 10),
                                  const Text(
                                    _textoAviso,
                                    style: TextStyle(fontSize: 16, height: 1.44, color: Colores.texto),
                                  ),
                                  const SizedBox(height: 12),
                                  Boton(
                                    texto: 'Entendido',
                                    alTocar: AmbitoSesion.leer(context).marcarAvisoMlkitVisto,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  // Mientras se lee la foto (revisión UX HU-04, obs. 1): sin texto nuevo.
                  if (_leyendo)
                    IgnorePointer(
                      child: Center(
                        child: Container(
                          padding: const EdgeInsets.all(18),
                          decoration: const BoxDecoration(
                            color: Color(0x8C000000),
                            shape: BoxShape.circle,
                          ),
                          child: const Espera(color: Colors.white, grande: true),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Encuadre la placa y toque Capturar',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colores.texto),
                ),
                const SizedBox(height: 12),
                Boton(
                  texto: 'Capturar',
                  icono: '◉',
                  alTocar: () => unawaited(_capturar()),
                  deshabilitado: _leyendo || !avisoVisto,
                ),
                const SizedBox(height: 12),
                _manual,
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _vistaConfirmar() {
    return _marco(
      SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const EtiquetaCampo(
              'Placa leída',
              estilo: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colores.texto),
            ),
            const SizedBox(height: 8),
            Semantics(
              label: 'Placa leída',
              child: TextField(
                controller: _leida,
                autocorrect: false,
                enableSuggestions: false,
                textCapitalization: TextCapitalization.characters,
                inputFormatters: [_AMayusculas()],
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 24,
                  letterSpacing: 2,
                  color: Colores.texto,
                ),
                decoration: InputDecoration(
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: const BorderSide(color: Colores.borde),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: const BorderSide(color: Colores.borde),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Confirme o corrija la placa antes de consultar.',
              style: TextStyle(fontSize: 15, color: Colores.tenue),
            ),
            const SizedBox(height: 24),
            Boton(
              texto: 'Usar esta placa',
              alTocar: () => widget.alUsar(_leida.text.trim().toUpperCase()),
            ),
            const SizedBox(height: 12),
            Boton(
              texto: 'Volver a capturar',
              variante: VarianteBoton.secundario,
              alTocar: _volverAlVisor,
            ),
          ],
        ),
      ),
    );
  }

  Widget _vistaFallo() {
    return _marco(
      Padding(
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
                      'No se pudo leer la placa. Pruebe de frente y con más luz.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 17, color: Colores.texto),
                    ),
                  ],
                ),
              ),
            ),
            Boton(texto: 'Volver a intentar', alTocar: _volverAlVisor),
            const SizedBox(height: 12),
            _manual,
          ],
        ),
      ),
    );
  }

  Widget _vistaSinPermiso() {
    final lector = AmbitoSesion.lector(context);
    return _marco(
      Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const ExcludeSemantics(
              child: Text('📷✕', textAlign: TextAlign.center, style: TextStyle(fontSize: 40)),
            ),
            const SizedBox(height: 12),
            const Text(
              'La app no tiene permiso para usar la cámara.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colores.texto),
            ),
            const SizedBox(height: 8),
            const Text(
              'Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 15, color: Colores.tenue),
            ),
            const SizedBox(height: 24),
            Boton(
              texto: 'Abrir ajustes',
              alTocar: () => unawaited(lector.abrirAjustes().catchError((Object _) {})),
            ),
            const SizedBox(height: 12),
            _manual,
          ],
        ),
      ),
    );
  }
}

class _Cabecera extends StatelessWidget {
  const _Cabecera({required this.alCerrar});

  final VoidCallback alCerrar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Colores.borde))),
      child: Row(
        children: [
          BotonIcono(
            etiqueta: 'Cerrar',
            simbolo: '✕',
            alTocar: alCerrar,
            estilo: const TextStyle(fontSize: 22, color: Colores.primario),
          ),
          const Expanded(
            child: Text(
              'Leer placa',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: Colores.texto),
            ),
          ),
        ],
      ),
    );
  }
}
