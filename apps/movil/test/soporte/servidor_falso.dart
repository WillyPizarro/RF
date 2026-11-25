// Servidor falso de la API para flutter_test (CONTRATO-MIGRACION-FLUTTER v1.1 §2 y §3).
//
// Equivale al `fetch` global simulado de Jest: un `MockClient` de package:http/testing.dart que
// la prueba pasa en `Dependencias.clienteHttp`. Registra cada solicitud (método, URL, cabeceras y
// cuerpo) y responde según la ruta. Solo datos sintéticos (placas con prefijo ZZ).
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// URL de la API que reciben las pruebas en `Dependencias.urlApi`.
const String urlApi = 'https://api.prueba.invalid';

/// Una solicitud que recibió el servidor falso.
class Llamada {
  Llamada(this.metodo, this.url, this.cabeceras, this.cuerpoTexto);

  final String metodo;
  final Uri url;
  final Map<String, String> cabeceras;
  final String cuerpoTexto;

  /// Ruta sin la URL de la API ni la consulta, p. ej. `/v1/me`.
  String get ruta => url.toString().startsWith(urlApi) ? url.path : url.toString();

  Map<String, String> get consulta => url.queryParameters;

  String? get auth {
    for (final e in cabeceras.entries) {
      if (e.key.toLowerCase() == 'authorization') return e.value;
    }
    return null;
  }

  /// El token sin el prefijo `Bearer`.
  String? get token => auth?.replaceFirst(RegExp(r'^Bearer\s+', caseSensitive: false), '');

  /// El cuerpo como JSON (o el texto si no es JSON; null si no hay cuerpo).
  Object? get cuerpo {
    if (cuerpoTexto.isEmpty) return null;
    try {
      return jsonDecode(cuerpoTexto);
    } on FormatException {
      return cuerpoTexto;
    }
  }

  Map<String, dynamic> get cuerpoMapa => (cuerpo as Map).cast<String, dynamic>();

  @override
  String toString() => '$metodo ${url.toString().replaceFirst(urlApi, '')}';
}

/// Respuesta del servidor falso.
class Resp {
  const Resp(this.estado, [this.cuerpo]);

  final int estado;
  final Object? cuerpo;
}

/// Respuesta especial: la red falla (el cliente lanza una excepción).
const Resp red = Resp(-1);

typedef Manejador = FutureOr<Resp> Function(Llamada ll);

Resp errorApi(int estado, String codigo, String mensaje, [Map<String, Object?> extra = const {}]) =>
    Resp(estado, {'codigo': codigo, 'mensaje': mensaje, 'id_traza': 'traza-prueba', ...extra});

// --- Datos sintéticos ----------------------------------------------------------------------

class Persona {
  const Persona(this.id, this.usuario, this.nombre, this.rol);

  final String id;
  final String usuario;
  final String nombre;
  final String rol;

  Map<String, Object?> get json => {'id': id, 'usuario': usuario, 'nombre': nombre, 'rol': rol};
}

const Map<String, Persona> personas = {
  'agente': Persona('u-agente', 'agente1', 'Ana Agente', 'agente'),
  'revisor': Persona('u-revisor', 'revisor1', 'Raúl Revisor', 'revisor'),
  'supervisor': Persona('u-super', 'supervisor1', 'Sara Supervisora', 'supervisor'),
};

const List<Map<String, String>> motivos = [
  {'codigo': 'control_vehicular', 'descripcion': 'Control vehicular'},
  {'codigo': 'intervencion_policial', 'descripcion': 'Intervención policial'},
  {'codigo': 'denuncia', 'descripcion': 'Denuncia'},
  {'codigo': 'operativo', 'descripcion': 'Operativo'},
  {'codigo': 'otro', 'descripcion': 'Otro'},
];

const Map<String, String> formatoPorDefecto = {
  'regex': r'^[A-Z0-9]{3}-[0-9]{3}$',
  'descripcion': 'ABC-123 (3 letras o números, guion, 3 números)',
};

const String consultadoEn = '2026-11-19T15:04:00Z';

Resp resultadoPlaca(String placa, String resultado, {String motivo = 'control_vehicular', String? texto}) =>
    Resp(200, {
      'consulta_id': 'c-1',
      'placa': placa,
      'resultado': resultado,
      'motivo': {'codigo': motivo, 'texto': texto},
      'consultado_en': consultadoEn,
    });

int _secuencia = 0;

class ServidorFalso {
  final List<Llamada> llamadas = [];
  final Map<String, Manejador> rutas = {};

  /// Tokens de acceso entregados por la sesión actual del servidor (login o renovación).
  final Set<String> tokensAcceso = {};

  /// Tokens de renovación entregados, en orden.
  final List<String> tokensRenovacion = [];

  /// Último token de acceso entregado.
  String? ultimoAcceso;

  late final http.Client cliente = MockClient((http.Request req) async {
    final ll = Llamada(req.method.toUpperCase(), req.url, req.headers, req.body);
    llamadas.add(ll);
    final m = rutas['${ll.metodo} ${ll.ruta}'];
    final Resp r = m == null ? errorApi(404, 'NO_ENCONTRADO', 'x') : await m(ll);
    if (identical(r, red)) {
      throw http.ClientException('Network request failed', req.url);
    }
    final texto = (r.cuerpo == null || r.estado == 204) ? '' : jsonEncode(r.cuerpo);
    return http.Response.bytes(utf8.encode(texto), r.estado, headers: const {
      'content-type': 'application/json; charset=utf-8',
      'x-id-traza': 'traza-prueba',
    });
  });

  /// Solicitudes a una ruta (`'POST /v1/consultas/placa'`).
  List<Llamada> a(String metodoRuta) => llamadas.where((l) => '${l.metodo} ${l.ruta}' == metodoRuta).toList();

  List<Llamada> get postsPlaca => a('POST /v1/consultas/placa');

  Map<String, Object?> darSesion(String rol, {int inactividadS = 600}) {
    _secuencia += 1;
    final acceso = 'acceso-$rol-$_secuencia';
    final renovacion = 'renov-$rol-$_secuencia';
    tokensAcceso.add(acceso);
    tokensRenovacion.add(renovacion);
    ultimoAcceso = acceso;
    return {
      'token_acceso': acceso,
      'token_renovacion': renovacion,
      'expira_en': 900,
      'inactividad_s': inactividadS,
      'usuario': personas[rol]!.json,
    };
  }

  /// Sesión válida para `rol`: login, renovación, logout, `/v1/me` (con `rolMe`) y `/v1/motivos`.
  void sesionValida(
    String rol, {
    int inactividadS = 600,
    String? rolMe,
    Map<String, String> formato = formatoPorDefecto,
  }) {
    final me = rolMe ?? rol;
    tokensAcceso.clear();
    rutas
      ..clear()
      ..['POST /v1/auth/login'] = (_) => Resp(200, darSesion(rol, inactividadS: inactividadS))
      ..['POST /v1/auth/refresh'] = (_) => Resp(200, darSesion(rol, inactividadS: inactividadS))
      ..['POST /v1/auth/logout'] = (_) => const Resp(204)
      ..['GET /v1/me'] = (ll) => (ll.token != null && tokensAcceso.contains(ll.token))
          ? Resp(200, personas[me]!.json)
          : errorApi(401, 'NO_AUTENTICADO', 'Inicie sesión nuevamente')
      ..['GET /v1/motivos'] = (_) => Resp(200, {'motivos': motivos, 'formato_placa': formato});
  }
}
