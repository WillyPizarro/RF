import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:permission_handler/permission_handler.dart';

import 'almacen_seguro.dart';
import 'lector_placa.dart';

/// Implementaciones reales de los bordes, solo para `lib/main.dart` (CONTRATO-MIGRACION-FLUTTER
/// §2, ADR-0017 regla 1). Es el ÚNICO lugar de la app que importa la cámara, ML Kit, los permisos
/// y el almacenamiento seguro. Las pruebas no lo usan: pasan dobles.

/// Tokens de la sesión en el almacenamiento seguro de Android (ADR-0013).
class AlmacenSeguroDispositivo implements AlmacenSeguro {
  AlmacenSeguroDispositivo() : _almacen = const FlutterSecureStorage();

  final FlutterSecureStorage _almacen;

  @override
  Future<String?> leer(String clave) => _almacen.read(key: clave);

  @override
  Future<void> escribir(String clave, String valor) => _almacen.write(key: clave, value: valor);

  @override
  Future<void> borrar(String clave) => _almacen.delete(key: clave);

  @override
  Future<Map<String, String>> leerTodo() => _almacen.readAll();
}

/// Cámara (`camera`, solo `takePicture()`) y OCR en el dispositivo (ML Kit, modelo incluido en el
/// APK: no necesita red).
///
/// - Nada lee por su cuenta: el visor solo muestra la imagen y se lee una foto por llamada a
///   [capturarYLeer] (regla 6, sin lectura continua; nunca se usa el flujo de imágenes).
/// - La foto queda en el caché privado de la app solo mientras ML Kit la lee y se borra en el
///   `finally`, salga bien o mal. Ninguna función devuelve una ruta ni una imagen.
class LectorPlacaDispositivo implements LectorPlaca {
  /// La cámara del visor montado (hay un solo visor a la vez: OCR-01).
  CameraController? _camara;

  @override
  Future<PermisoCamara> asegurarPermisoCamara() async {
    final actual = await Permission.camera.status;
    if (actual.isGranted) return PermisoCamara.concedido;
    if (actual.isPermanentlyDenied || actual.isRestricted) return PermisoCamara.denegado;
    final pedido = await Permission.camera.request();
    return pedido.isGranted ? PermisoCamara.concedido : PermisoCamara.denegado;
  }

  @override
  Widget visorCamara({required bool activo}) => _VisorCamara(lector: this, activo: activo);

  @override
  Future<LecturaPlaca> capturarYLeer() async {
    final camara = _camara;
    if (camara == null || !camara.value.isInitialized) {
      throw StateError('La cámara no está lista');
    }
    if (camara.value.isTakingPicture) throw StateError('La cámara está ocupada');
    final foto = await camara.takePicture();
    try {
      final reconocedor = TextRecognizer(script: TextRecognitionScript.latin);
      try {
        final resultado = await reconocedor.processImage(InputImage.fromFilePath(foto.path));
        final texto = resultado.text;
        return LecturaPlaca(texto.trim().isEmpty ? null : texto);
      } finally {
        await reconocedor.close();
      }
    } finally {
      _borrar(foto.path);
    }
  }

  @override
  Future<void> abrirAjustes() async {
    await openAppSettings();
  }

  static void _borrar(String ruta) {
    try {
      final archivo = File(ruta);
      if (archivo.existsSync()) archivo.deleteSync();
    } catch (_) {
      // Si no se pudo borrar, queda en el caché privado de la app (nunca en la galería).
    }
  }
}

/// El visor en vivo. Libera la cámara al salir de OCR-01 y cuando la app pasa a segundo plano.
class _VisorCamara extends StatefulWidget {
  const _VisorCamara({required this.lector, required this.activo});

  final LectorPlacaDispositivo lector;
  final bool activo;

  @override
  State<_VisorCamara> createState() => _EstadoVisorCamara();
}

class _EstadoVisorCamara extends State<_VisorCamara> with WidgetsBindingObserver {
  CameraController? _camara;
  bool _abriendo = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (widget.activo) unawaited(_abrir());
  }

  @override
  void didUpdateWidget(_VisorCamara anterior) {
    super.didUpdateWidget(anterior);
    if (widget.activo && !anterior.activo) unawaited(_abrir());
    if (!widget.activo && anterior.activo) unawaited(_cerrar());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState estado) {
    if (estado == AppLifecycleState.inactive || estado == AppLifecycleState.paused) {
      unawaited(_cerrar());
    } else if (estado == AppLifecycleState.resumed && widget.activo) {
      unawaited(_abrir());
    }
  }

  Future<void> _abrir() async {
    if (_abriendo || _camara != null) return;
    _abriendo = true;
    try {
      final camaras = await availableCameras();
      if (camaras.isEmpty || !mounted) return;
      final trasera = camaras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => camaras.first,
      );
      final camara = CameraController(
        trasera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      await camara.initialize();
      if (!mounted || !widget.activo) {
        await camara.dispose();
        return;
      }
      setState(() => _camara = camara);
      widget.lector._camara = camara;
    } catch (_) {
      // Sin cámara: el visor queda en negro y "Capturar" lleva a OCR-03 (capturarYLeer lanza).
    } finally {
      _abriendo = false;
    }
  }

  Future<void> _cerrar() async {
    final camara = _camara;
    if (camara == null) return;
    if (widget.lector._camara == camara) widget.lector._camara = null;
    if (mounted) setState(() => _camara = null);
    await camara.dispose();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    final camara = _camara;
    if (camara != null) {
      if (widget.lector._camara == camara) widget.lector._camara = null;
      unawaited(camara.dispose());
    }
    _camara = null;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final camara = _camara;
    if (camara == null || !camara.value.isInitialized) return const SizedBox.expand();
    return Semantics(
      label: 'Visor de la cámara',
      child: ClipRect(
        child: FittedBox(
          fit: BoxFit.cover,
          child: SizedBox(
            width: camara.value.previewSize?.height ?? 1,
            height: camara.value.previewSize?.width ?? 1,
            child: CameraPreview(camara),
          ),
        ),
      ),
    );
  }
}
