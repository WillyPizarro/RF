import 'package:http/http.dart' as http;

import 'almacen_seguro.dart';
import 'lector_placa.dart';

/// Todo lo que la app recibe de afuera. Las pruebas pasan dobles.
class Dependencias {
  const Dependencias({
    required this.urlApi,
    required this.clienteHttp,
    required this.almacen,
    required this.lectorPlaca,
  });

  /// Por ejemplo 'https://localhost:8443'; la app llama a urlApi + '/v1/...'.
  final String urlApi;

  /// Toda la red de la app pasa por aquí (package:http). En las pruebas, MockClient.
  final http.Client clienteHttp;

  /// Token de la sesión.
  final AlmacenSeguro almacen;

  /// Cámara + OCR (HU-04).
  final LectorPlaca lectorPlaca;
}
