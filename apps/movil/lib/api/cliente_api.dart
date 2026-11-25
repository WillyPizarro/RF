import 'dart:convert';

import 'package:http/http.dart' as http;

/// Estado HTTP y cuerpo JSON (o null si no hay cuerpo o no es JSON).
class RespuestaApi {
  const RespuestaApi(this.estado, this.cuerpo);

  final int estado;
  final Object? cuerpo;

  /// El cuerpo como objeto JSON, o null.
  Map<String, Object?>? get objeto {
    final c = cuerpo;
    return c is Map<String, Object?> ? c : null;
  }

  /// `codigo` del cuerpo de error de la API, o null.
  String? get codigo {
    final c = objeto?['codigo'];
    return c is String ? c : null;
  }
}

/// Llama a la API por el `http.Client` inyectado (ADR-0001: la app solo habla con la API;
/// CONTRATO-MIGRACION-FLUTTER §2: toda la red pasa por `clienteHttp`).
///
/// Sin caché HTTP de ningún tipo (ADR-0013, CONTRATO-HU-04 v6 §6). Un error de red lanza: nunca
/// se convierte en un resultado (AGENTS.md regla 7).
class ClienteApi {
  ClienteApi({required String urlApi, required http.Client clienteHttp})
      : _base = urlApi.replaceFirst(RegExp(r'/+$'), ''),
        _http = clienteHttp;

  final String _base;
  final http.Client _http;

  Future<RespuestaApi> llamar(
    String ruta, {
    String metodo = 'GET',
    Object? cuerpo,
    String? token,
  }) async {
    final cabeceras = <String, String>{'Accept': 'application/json'};
    if (cuerpo != null) cabeceras['Content-Type'] = 'application/json';
    if (token != null) cabeceras['Authorization'] = 'Bearer $token';
    final uri = Uri.parse('$_base$ruta');
    final http.Response respuesta;
    if (metodo == 'POST') {
      respuesta = await _http.post(
        uri,
        headers: cabeceras,
        body: cuerpo == null ? null : utf8.encode(jsonEncode(cuerpo)),
      );
    } else {
      respuesta = await _http.get(uri, headers: cabeceras);
    }
    Object? json;
    try {
      json = respuesta.bodyBytes.isEmpty ? null : jsonDecode(utf8.decode(respuesta.bodyBytes));
    } catch (_) {
      json = null;
    }
    return RespuestaApi(respuesta.statusCode, json);
  }
}
