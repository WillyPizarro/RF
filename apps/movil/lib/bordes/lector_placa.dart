import 'package:flutter/widgets.dart';

/// Cámara y OCR de la placa (HU-04). Real: camera + google_mlkit_text_recognition.
enum PermisoCamara { concedido, denegado }

class LecturaPlaca {
  const LecturaPlaca(this.texto);

  /// null si no se reconoció ningún texto.
  final String? texto;
}

abstract class LectorPlaca {
  /// Si nunca se pidió, lo pide al sistema. No abre la cámara.
  Future<PermisoCamara> asegurarPermisoCamara();

  /// El visor en vivo de OCR-01. No lee nada por su cuenta.
  Widget visorCamara({required bool activo});

  /// Toma UNA foto, la lee con OCR en el dispositivo, borra la foto y devuelve solo el texto.
  /// Lanza una excepción si la cámara falla.
  Future<LecturaPlaca> capturarYLeer();

  /// Abre los ajustes de la app en el sistema (OCR-04).
  Future<void> abrirAjustes();
}
