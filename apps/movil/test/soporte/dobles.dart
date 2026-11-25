// Dobles de los bordes de la app (CONTRATO-MIGRACION-FLUTTER v1.1 §2): `AlmacenSeguro` en
// memoria y `LectorPlaca` sin cámara ni ML Kit. Equivalen a la simulación de
// `expo-secure-store` y al `jest.mock` de `src/camara/lectorPlaca.ts` de la referencia Expo.
import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:movil_buscador/bordes/bordes.dart';

import 'servidor_falso.dart';

/// Almacenamiento seguro en memoria: la prueba ve qué queda guardado.
class AlmacenFalso implements AlmacenSeguro {
  final Map<String, String> datos = {};

  @override
  Future<String?> leer(String clave) async => datos[clave];

  @override
  Future<void> escribir(String clave, String valor) async => datos[clave] = valor;

  @override
  Future<void> borrar(String clave) async => datos.remove(clave);

  @override
  Future<Map<String, String>> leerTodo() async => Map.of(datos);
}

/// Llave del visor simulado (equivale a `testID="visor-simulado"` en Jest).
const Key llaveVisor = Key('visor-simulado');

/// Cámara y OCR simulados. Cuenta las llamadas y registra cada `visorCamara(activo:)`.
class LectorFalso implements LectorPlaca {
  /// Respuestas de `asegurarPermisoCamara`, en orden; cuando se acaban, `permisoPorDefecto`.
  final List<PermisoCamara> permisos = [];
  PermisoCamara permisoPorDefecto = PermisoCamara.concedido;

  /// Lecturas de `capturarYLeer`, en orden; cuando se acaban, `lecturaPorDefecto`.
  final List<FutureOr<LecturaPlaca> Function()> lecturas = [];
  FutureOr<LecturaPlaca> Function() lecturaPorDefecto = () => const LecturaPlaca('ZZA-101');

  int llamadasPermiso = 0;
  int llamadasCaptura = 0;
  int llamadasAjustes = 0;
  final List<bool> visores = [];

  /// Programa una sola lectura con este texto.
  void leera(String? texto) => lecturas.add(() => LecturaPlaca(texto));

  /// Programa una falla de la cámara.
  void fallara() => lecturas.add(() => throw StateError('cámara'));

  /// Todas las lecturas siguientes devuelven este texto.
  void leeraSiempre(String? texto) => lecturaPorDefecto = () => LecturaPlaca(texto);

  @override
  Future<PermisoCamara> asegurarPermisoCamara() async {
    llamadasPermiso += 1;
    return permisos.isNotEmpty ? permisos.removeAt(0) : permisoPorDefecto;
  }

  @override
  Widget visorCamara({required bool activo}) {
    visores.add(activo);
    return const SizedBox.expand(key: llaveVisor, child: ColoredBox(color: Color(0xFF000000)));
  }

  @override
  Future<LecturaPlaca> capturarYLeer() async {
    llamadasCaptura += 1;
    final f = lecturas.isNotEmpty ? lecturas.removeAt(0) : lecturaPorDefecto;
    return await f();
  }

  @override
  Future<void> abrirAjustes() async {
    llamadasAjustes += 1;
  }
}

/// Las cuatro dependencias de la app con sus dobles.
class Entorno {
  Entorno() : servidor = ServidorFalso(), almacen = AlmacenFalso(), lector = LectorFalso();

  final ServidorFalso servidor;
  final AlmacenFalso almacen;
  final LectorFalso lector;

  Dependencias get dependencias => Dependencias(
        urlApi: urlApi,
        clienteHttp: servidor.cliente,
        almacen: almacen,
        lectorPlaca: lector,
      );
}
