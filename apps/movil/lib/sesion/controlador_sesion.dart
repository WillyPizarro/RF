import 'dart:async';
import 'dart:math' as math;

import 'package:clock/clock.dart';
import 'package:flutter/foundation.dart';

import '../api/cliente_api.dart';
import '../api/modelos.dart';
import '../bordes/bordes.dart';

/// Pantalla que muestra la app. 'placa' = PLA-01 a PLA-08 y OCR-01 a OCR-04 (HU-03, HU-04);
/// 'bitacora' = BIT-01 y BIT-02 (HU-07).
enum Pantalla { cargando, login, inicio, sinPermiso, placa, bitacora }

/// Aviso que muestra el login al volver (AUTH-03) o al fallar (AUTH-02, AUTH-04, otro error).
enum TipoAviso { vacios, inactividad, credenciales, bloqueo, error }

class Aviso {
  const Aviso(this.tipo, {this.hasta});
  final TipoAviso tipo;

  /// `bloqueado_hasta` (ISO) de AUTH-04.
  final String? hasta;
}

class _Sesion {
  _Sesion({
    required this.tokenAcceso,
    required this.tokenRenovacion,
    required this.venceAcceso,
    required this.inactividadMs,
    required this.ultimaInteraccion,
    required this.ultimoContacto,
  });

  String tokenAcceso;
  String tokenRenovacion;

  /// ms epoch en que vence el token de acceso.
  int venceAcceso;
  int inactividadMs;
  int ultimaInteraccion;
  int ultimoContacto;
}

/// Claves internas del almacenamiento seguro (ADR-0013). Nada más se guarda en el dispositivo.
const _claveAcceso = 'sesion.token_acceso';
const _claveRenovacion = 'sesion.token_renovacion';

/// Ciclo de la sesión en la app (CONTRATO-HU-01 §4, ADR-0011, ADR-0013) y estado mínimo en
/// memoria (perfil y pantalla). Uno por montaje de `MovilBuscadorApp`.
///
/// - Inactividad: un temporizador de `inactividad_s` (lo da la API, no está fijo en el código)
///   se reinicia con cada interacción. Al vencer, o ante un 401 SESION_VENCIDA, se cierra la
///   sesión con el aviso de AUTH-03.
/// - Renovación: mientras haya interacción, se renueva el token antes de que venza y con la
///   frecuencia suficiente para que el servidor no vea la sesión inactiva.
/// - Cierre: se borran el almacenamiento seguro, el estado y los tokens en memoria; el
///   temporizador se cancela y ninguna respuesta pendiente de la sesión anterior se usa.
class ControladorSesion extends ChangeNotifier {
  ControladorSesion(this._api, this._almacen);

  final ClienteApi _api;
  final AlmacenSeguro _almacen;

  // --- estado visible --------------------------------------------------------------------------

  Pantalla _pantalla = Pantalla.cargando;
  Perfil? _perfil;
  Aviso? _aviso;
  int _generacionLogin = 0;
  bool _avisoMlkitVisto = false;

  Pantalla get pantalla => _pantalla;
  Perfil? get perfil => _perfil;
  Aviso? get aviso => _aviso;

  /// Cambia en cada cierre de sesión: el login se vuelve a montar vacío.
  int get generacionLogin => _generacionLogin;

  /// El agente ya tocó "Entendido" en el aviso de ML Kit en esta sesión (CONTRATO-HU-04 v5).
  /// Solo en memoria.
  bool get avisoMlkitVisto => _avisoMlkitVisto;

  // --- estado interno --------------------------------------------------------------------------

  _Sesion? _sesion;
  int _generacion = 0;
  Timer? _temporizador;
  bool _renovando = false;
  bool _desechado = false;
  final List<bool Function()> _manejadoresAtras = [];

  int get _ahora => clock.now().millisecondsSinceEpoch;

  void _avisar() {
    if (!_desechado) notifyListeners();
  }

  @override
  void dispose() {
    _desechado = true;
    _generacion += 1;
    _cancelarTemporizador();
    _sesion = null;
    _manejadoresAtras.clear();
    super.dispose();
  }

  // --- navegación ------------------------------------------------------------------------------

  void mostrar(Pantalla pantalla) {
    _pantalla = pantalla;
    _avisar();
  }

  void avisar(Aviso? aviso) {
    _aviso = aviso;
    _avisar();
  }

  void marcarAvisoMlkitVisto() {
    _avisoMlkitVisto = true;
    _avisar();
  }

  void _entrar(Perfil perfil) {
    _perfil = perfil;
    _aviso = null;
    _pantalla = Pantalla.inicio;
    _avisar();
  }

  /// Las pantallas con "atrás" propio lo registran (como `BackHandler` en Expo).
  void registrarAtras(bool Function() manejador) => _manejadoresAtras.add(manejador);

  void quitarAtras(bool Function() manejador) => _manejadoresAtras.remove(manejador);

  /// "Atrás" del sistema. true = la app lo manejó; false = lo maneja el sistema (no hay pantalla
  /// anterior a la que volver).
  bool atras() {
    for (final manejador in _manejadoresAtras.reversed.toList()) {
      if (manejador()) return true;
    }
    if (_pantalla == Pantalla.sinPermiso && _perfil != null) {
      mostrar(Pantalla.inicio);
      return true;
    }
    return false;
  }

  // --- temporizador de inactividad -------------------------------------------------------------

  void _cancelarTemporizador() {
    _temporizador?.cancel();
    _temporizador = null;
  }

  void _programarInactividad() {
    _cancelarTemporizador();
    final sesion = _sesion;
    if (sesion == null) return;
    final restante = sesion.ultimaInteraccion + sesion.inactividadMs - _ahora;
    final actual = _generacion;
    _temporizador = Timer(Duration(milliseconds: math.max(0, restante)), () {
      if (actual == _generacion) unawaited(cerrarSesion(const Aviso(TipoAviso.inactividad)));
    });
  }

  void _abrir(RespuestaSesion datos) {
    final ahora = _ahora;
    _sesion = _Sesion(
      tokenAcceso: datos.tokenAcceso,
      tokenRenovacion: datos.tokenRenovacion,
      venceAcceso: ahora + datos.expiraEn * 1000,
      inactividadMs: datos.inactividadS * 1000,
      ultimaInteraccion: ahora,
      ultimoContacto: ahora,
    );
    _programarInactividad();
  }

  Future<void> _guardarTokens(String acceso, String renovacion) async {
    await _almacen.escribir(_claveAcceso, acceso);
    await _almacen.escribir(_claveRenovacion, renovacion);
  }

  /// Borra todas las claves de la sesión. Nunca falla.
  Future<void> _borrarTokens() async {
    for (final clave in [_claveAcceso, _claveRenovacion]) {
      try {
        await _almacen.borrar(clave);
      } catch (_) {
        // se sigue con la otra clave
      }
    }
  }

  // --- ciclo de la sesión ----------------------------------------------------------------------

  /// Cierra la sesión local. `aviso` = lo que muestra el login (null = sin mensaje).
  Future<void> cerrarSesion(Aviso? aviso) async {
    if (_desechado) return;
    _generacion += 1;
    _cancelarTemporizador();
    _sesion = null;
    _renovando = false;
    _perfil = null;
    _aviso = aviso;
    _pantalla = Pantalla.login;
    _generacionLogin += 1;
    _avisoMlkitVisto = false; // el aviso vuelve a aparecer en la sesión siguiente
    _avisar();
    await _borrarTokens();
  }

  /// "Salir": cierra sin mensaje y avisa a la API (CONTRATO-HU-02 §3).
  Future<void> salir() async {
    final token = _sesion?.tokenAcceso;
    await cerrarSesion(null);
    if (token != null) {
      try {
        await _api.llamar('/v1/auth/logout', metodo: 'POST', token: token);
      } catch (_) {
        // la sesión local ya está cerrada; el servidor la vencerá por inactividad
      }
    }
  }

  /// GET /v1/me tras abrir la sesión. Si falla, `vencida` dice si fue un 401 SESION_VENCIDA: ese
  /// 401 muestra AUTH-03 venga de la solicitud que venga (CONTRATO-HU-01 §4).
  Future<({Perfil? perfil, bool vencida})> _cargarPerfil(int actual) async {
    final sesion = _sesion;
    if (sesion == null) return (perfil: null, vencida: false);
    final respuesta = await _api.llamar('/v1/me', token: sesion.tokenAcceso);
    if (actual != _generacion) return (perfil: null, vencida: false);
    if (respuesta.estado == 200) {
      final perfil = Perfil.desde(respuesta.cuerpo);
      if (perfil != null) return (perfil: perfil, vencida: false);
    }
    final vencida = respuesta.estado == 401 && respuesta.codigo == 'SESION_VENCIDA';
    return (perfil: null, vencida: vencida);
  }

  /// Login completo: POST /v1/auth/login y luego GET /v1/me (el menú sale de /v1/me).
  Future<void> ingresar(String usuario, String clave) async {
    final actual = _generacion;
    try {
      final respuesta = await _api.llamar(
        '/v1/auth/login',
        metodo: 'POST',
        cuerpo: {'usuario': usuario, 'clave': clave},
      );
      if (actual != _generacion) return;
      final datos = respuesta.estado == 200 ? RespuestaSesion.desde(respuesta.cuerpo) : null;
      if (datos != null) {
        _abrir(datos);
        await _guardarTokens(datos.tokenAcceso, datos.tokenRenovacion);
        if (actual != _generacion) return;
        final r = await _cargarPerfil(actual);
        if (actual != _generacion) return;
        if (r.perfil != null) {
          _entrar(r.perfil!);
          return;
        }
        await cerrarSesion(Aviso(r.vencida ? TipoAviso.inactividad : TipoAviso.error));
        return;
      }
      final codigo = respuesta.codigo;
      final hasta = respuesta.objeto?['bloqueado_hasta'];
      if (respuesta.estado == 401 && codigo == 'CREDENCIALES_INVALIDAS') {
        avisar(const Aviso(TipoAviso.credenciales));
      } else if (respuesta.estado == 423 && codigo == 'CUENTA_BLOQUEADA' && hasta is String) {
        avisar(Aviso(TipoAviso.bloqueo, hasta: hasta));
      } else {
        avisar(const Aviso(TipoAviso.error));
      }
    } catch (_) {
      if (actual != _generacion) return;
      if (_sesion != null) {
        await cerrarSesion(const Aviso(TipoAviso.error));
      } else {
        avisar(const Aviso(TipoAviso.error));
      }
    }
  }

  /// Al abrir la app (CONTRATO-MIGRACION-FLUTTER §1.2, v1.1): con un token de renovación guardado,
  /// primero POST /v1/auth/refresh y después GET /v1/me con el token nuevo; sin token, AUTH-01 sin
  /// ninguna solicitud.
  Future<void> restaurar() async {
    final actual = _generacion;
    String? tokenRenovacion;
    try {
      tokenRenovacion = await _almacen.leer(_claveRenovacion);
    } catch (_) {
      tokenRenovacion = null;
    }
    if (actual != _generacion) return;
    if (tokenRenovacion == null || tokenRenovacion.isEmpty) {
      mostrar(Pantalla.login);
      return;
    }
    try {
      final respuesta = await _api.llamar(
        '/v1/auth/refresh',
        metodo: 'POST',
        cuerpo: {'token_renovacion': tokenRenovacion},
      );
      if (actual != _generacion) return;
      final datos = respuesta.estado == 200 ? RespuestaSesion.desde(respuesta.cuerpo) : null;
      if (datos != null) {
        _abrir(datos);
        await _guardarTokens(datos.tokenAcceso, datos.tokenRenovacion);
        if (actual != _generacion) return;
        final r = await _cargarPerfil(actual);
        if (actual != _generacion) return;
        if (r.perfil != null) {
          _entrar(r.perfil!);
          return;
        }
        await cerrarSesion(r.vencida ? const Aviso(TipoAviso.inactividad) : null);
        return;
      }
      final vencida = respuesta.estado == 401 && respuesta.codigo == 'SESION_VENCIDA';
      await cerrarSesion(vencida ? const Aviso(TipoAviso.inactividad) : null);
    } catch (_) {
      if (actual == _generacion) await cerrarSesion(null);
    }
  }

  Future<void> _renovar() async {
    final sesion = _sesion;
    if (sesion == null || _renovando) return;
    _renovando = true;
    final actual = _generacion;
    try {
      final respuesta = await _api.llamar(
        '/v1/auth/refresh',
        metodo: 'POST',
        cuerpo: {'token_renovacion': sesion.tokenRenovacion},
      );
      final vigente = _sesion;
      if (actual != _generacion || vigente == null) return;
      final datos = respuesta.estado == 200 ? RespuestaSesion.desde(respuesta.cuerpo) : null;
      if (datos != null) {
        final ahora = _ahora;
        vigente
          ..tokenAcceso = datos.tokenAcceso
          ..tokenRenovacion = datos.tokenRenovacion
          ..venceAcceso = ahora + datos.expiraEn * 1000
          ..inactividadMs = datos.inactividadS * 1000
          ..ultimoContacto = ahora;
        await _guardarTokens(datos.tokenAcceso, datos.tokenRenovacion);
        if (actual == _generacion) _programarInactividad();
      } else if (respuesta.estado == 401) {
        final vencida = respuesta.codigo == 'SESION_VENCIDA';
        await cerrarSesion(vencida ? const Aviso(TipoAviso.inactividad) : null);
      }
    } catch (_) {
      // sin red: se reintenta con la siguiente interacción
    } finally {
      if (actual == _generacion) _renovando = false;
    }
  }

  /// Cada toque dentro de la vista raíz (`Key('app-raiz')`) cuenta como interacción.
  void registrarInteraccion() {
    final sesion = _sesion;
    if (sesion == null) return;
    final ahora = _ahora;
    if (ahora - sesion.ultimaInteraccion >= sesion.inactividadMs) {
      // El temporizador pudo no correr (app en segundo plano): la sesión ya venció.
      unawaited(cerrarSesion(const Aviso(TipoAviso.inactividad)));
      return;
    }
    sesion.ultimaInteraccion = ahora;
    _programarInactividad();
    final margenServidor = math.min(60000, sesion.inactividadMs / 3);
    final margenToken = math.min(60000, (sesion.venceAcceso - sesion.ultimoContacto) / 3);
    if (ahora - sesion.ultimoContacto >= margenServidor ||
        sesion.venceAcceso - ahora <= margenToken) {
      unawaited(_renovar());
    }
  }

  /// Al volver del segundo plano: si pasó el tiempo de inactividad, se cierra la sesión.
  void revisarAlVolver() {
    final sesion = _sesion;
    if (sesion != null && _ahora - sesion.ultimaInteraccion >= sesion.inactividadMs) {
      unawaited(cerrarSesion(const Aviso(TipoAviso.inactividad)));
    }
  }

  /// Llamada autenticada para las pantallas. Maneja 401 (sesión vencida o no autenticada) y
  /// 403 SIN_PERMISO (ERR-01): en esos casos devuelve null. El resto lo decide quien llama.
  /// Un error de red lanza: nunca se convierte en un resultado (regla 7).
  Future<RespuestaApi?> llamarAutenticado(String ruta, {String metodo = 'GET', Object? cuerpo}) async {
    if (_sesion == null) return null;
    final actual = _generacion;
    if (_sesion!.venceAcceso - _ahora < 30000) await _renovar();
    final sesion = _sesion;
    if (sesion == null || actual != _generacion) return null;
    final respuesta = await _api.llamar(ruta, metodo: metodo, cuerpo: cuerpo, token: sesion.tokenAcceso);
    if (actual != _generacion) return null;
    _sesion?.ultimoContacto = _ahora;
    if (respuesta.estado == 401) {
      final vencida = respuesta.codigo == 'SESION_VENCIDA';
      await cerrarSesion(vencida ? const Aviso(TipoAviso.inactividad) : null);
      return null;
    }
    if (respuesta.estado == 403 && respuesta.codigo == 'SIN_PERMISO') {
      mostrar(Pantalla.sinPermiso);
      return null;
    }
    return respuesta;
  }
}
