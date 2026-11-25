import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;

import 'app.dart';
import 'bordes/bordes.dart';
import 'bordes/dispositivo.dart';

/// URL base de la API, sin barra final: `--dart-define=API_URL=https://localhost:8443`
/// (CONTRATO-MIGRACION-FLUTTER §2). No es un secreto.
const _urlApi = String.fromEnvironment('API_URL');

/// Arranque real: arma las dependencias del dispositivo. Las pruebas no lo usan.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MovilBuscadorApp(
      dependencias: Dependencias(
        urlApi: _urlApi,
        // package:http sobre dart:io, sin caché HTTP (CONTRATO-HU-04 v6 §6).
        clienteHttp: http.Client(),
        almacen: AlmacenSeguroDispositivo(),
        lectorPlaca: LectorPlacaDispositivo(),
      ),
    ),
  );
}
