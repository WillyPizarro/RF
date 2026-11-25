import 'package:flutter/widgets.dart';
import 'package:ok_http/ok_http.dart';

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
        // OkHttp de Android por package:ok_http (CONTRATO-MIGRACION-FLUTTER v1.5 §6): respeta el
        // network_security_config (la CA de usuario solo en depuración, por <debug-overrides>).
        // `OkHttpClient()` usa `new OkHttpClient()` sin `Cache`: no deja caché HTTP en el
        // dispositivo (CONTRATO-HU-04 v6 §6).
        clienteHttp: OkHttpClient(),
        almacen: AlmacenSeguroDispositivo(),
        lectorPlaca: LectorPlacaDispositivo(),
      ),
    ),
  );
}
