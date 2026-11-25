/// Modelos de la app, escritos a mano desde `contratos/api/openapi.json` (ADR-0007; el contrato
/// de la API no cambia). Solo los campos que la app usa. `desde` devuelve null si el cuerpo no
/// tiene la forma esperada: quien llama lo trata como error, nunca como resultado (regla 7).
library;

String? _texto(Object? v) => v is String ? v : null;
int? _entero(Object? v) => v is int ? v : (v is num ? v.toInt() : null);

/// Schema `Perfil` (GET /v1/me).
class Perfil {
  const Perfil({required this.id, required this.usuario, required this.nombre, required this.rol});

  final String id;
  final String usuario;
  final String nombre;

  /// 'agente' | 'revisor' | 'supervisor'.
  final String rol;

  static Perfil? desde(Object? json) {
    if (json is! Map) return null;
    final id = _texto(json['id']);
    final usuario = _texto(json['usuario']);
    final nombre = _texto(json['nombre']);
    final rol = _texto(json['rol']);
    if (id == null || usuario == null || nombre == null || rol == null) return null;
    return Perfil(id: id, usuario: usuario, nombre: nombre, rol: rol);
  }
}

/// Schema `RespuestaSesion` (login y refresh).
class RespuestaSesion {
  const RespuestaSesion({
    required this.tokenAcceso,
    required this.tokenRenovacion,
    required this.expiraEn,
    required this.inactividadS,
  });

  final String tokenAcceso;
  final String tokenRenovacion;
  final int expiraEn;
  final int inactividadS;

  static RespuestaSesion? desde(Object? json) {
    if (json is! Map) return null;
    final acceso = _texto(json['token_acceso']);
    final renovacion = _texto(json['token_renovacion']);
    final expira = _entero(json['expira_en']);
    final inactividad = _entero(json['inactividad_s']);
    if (acceso == null || renovacion == null || expira == null || inactividad == null) return null;
    return RespuestaSesion(
      tokenAcceso: acceso,
      tokenRenovacion: renovacion,
      expiraEn: expira,
      inactividadS: inactividad,
    );
  }
}

/// Schemas `Motivo` y `FormatoPlaca` (GET /v1/motivos).
class Motivo {
  const Motivo(this.codigo, this.descripcion);
  final String codigo;
  final String descripcion;
}

class FormatoPlaca {
  const FormatoPlaca(this.regex, this.descripcion);
  final String regex;
  final String descripcion;
}

class Catalogo {
  const Catalogo(this.motivos, this.formato);
  final List<Motivo> motivos;
  final FormatoPlaca formato;

  static Catalogo? desde(Object? json) {
    if (json is! Map) return null;
    final lista = json['motivos'];
    final formato = json['formato_placa'];
    if (lista is! List || formato is! Map) return null;
    final motivos = <Motivo>[];
    for (final m in lista) {
      if (m is! Map) return null;
      final codigo = _texto(m['codigo']);
      final descripcion = _texto(m['descripcion']);
      if (codigo == null || descripcion == null) return null;
      motivos.add(Motivo(codigo, descripcion));
    }
    final regex = _texto(formato['regex']);
    final descripcion = _texto(formato['descripcion']);
    if (regex == null || descripcion == null) return null;
    return Catalogo(motivos, FormatoPlaca(regex, descripcion));
  }
}

/// Schema `RespuestaConsultaPlaca` (POST /v1/consultas/placa).
class ResultadoPlaca {
  const ResultadoPlaca({
    required this.placa,
    required this.resultado,
    required this.motivoCodigo,
    required this.motivoTexto,
    required this.consultadoEn,
  });

  final String placa;

  /// 'con_requisitoria' | 'sin_requisitoria' | 'placa_no_registrada'.
  final String resultado;
  final String motivoCodigo;
  final String? motivoTexto;
  final String consultadoEn;

  static const resultadosValidos = {'con_requisitoria', 'sin_requisitoria', 'placa_no_registrada'};

  static ResultadoPlaca? desde(Object? json) {
    if (json is! Map) return null;
    final placa = _texto(json['placa']);
    final resultado = _texto(json['resultado']);
    final motivo = json['motivo'];
    final consultado = _texto(json['consultado_en']);
    if (placa == null || resultado == null || consultado == null || motivo is! Map) return null;
    if (!resultadosValidos.contains(resultado)) return null;
    final codigo = _texto(motivo['codigo']);
    if (codigo == null) return null;
    return ResultadoPlaca(
      placa: placa,
      resultado: resultado,
      motivoCodigo: codigo,
      motivoTexto: _texto(motivo['texto']),
      consultadoEn: consultado,
    );
  }
}

/// Schema `Registro` (GET /v1/bitacora).
class RegistroBitacora {
  const RegistroBitacora({
    required this.id,
    required this.ocurridoEn,
    required this.usuario,
    required this.tipoEvento,
    required this.motivo,
    required this.placa,
    required this.resultado,
    required this.score,
    required this.capturaId,
    required this.codigoError,
  });

  final String id;
  final String ocurridoEn;
  final String? usuario;
  final String tipoEvento;
  final String? motivo;

  /// `parametros.placa`, si es texto.
  final String? placa;
  final String? resultado;
  final num? score;
  final String? capturaId;
  final String? codigoError;

  static RegistroBitacora? desde(Object? json) {
    if (json is! Map) return null;
    final id = _texto(json['id']);
    final ocurrido = _texto(json['ocurrido_en']);
    final tipo = _texto(json['tipo_evento']);
    if (id == null || ocurrido == null || tipo == null) return null;
    final parametros = json['parametros'];
    final score = json['score'];
    return RegistroBitacora(
      id: id,
      ocurridoEn: ocurrido,
      usuario: _texto(json['usuario']),
      tipoEvento: tipo,
      motivo: _texto(json['motivo']),
      placa: parametros is Map ? _texto(parametros['placa']) : null,
      resultado: _texto(json['resultado']),
      score: score is num ? score : null,
      capturaId: _texto(json['captura_id']),
      codigoError: _texto(json['codigo_error']),
    );
  }
}

/// Schema `RespuestaBitacora`.
class PaginaBitacora {
  const PaginaBitacora(this.registros, this.siguienteCursor);
  final List<RegistroBitacora> registros;
  final String? siguienteCursor;

  static PaginaBitacora? desde(Object? json) {
    if (json is! Map) return null;
    final lista = json['registros'];
    if (lista is! List) return null;
    final registros = <RegistroBitacora>[];
    for (final r in lista) {
      final registro = RegistroBitacora.desde(r);
      if (registro == null) return null;
      registros.add(registro);
    }
    return PaginaBitacora(registros, _texto(json['siguiente_cursor']));
  }
}
