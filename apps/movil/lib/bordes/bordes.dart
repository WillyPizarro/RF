/// Interfaz de la app hacia afuera (CONTRATO-MIGRACION-FLUTTER §2).
///
/// Solo exporta las interfaces y `Dependencias`. Las implementaciones reales (cámara, ML Kit,
/// almacenamiento seguro) están en `dispositivo.dart` y solo las usa `lib/main.dart`.
library;

export 'almacen_seguro.dart';
export 'dependencias.dart';
export 'lector_placa.dart';
