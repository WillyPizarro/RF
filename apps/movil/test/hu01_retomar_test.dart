// CONTRATO-MIGRACION-FLUTTER v1.1 §1.2 (retomar la sesión al abrir la app) y CONTRATO-HU-01 v6
// §4 (AUTH-03 "venga de la solicitud que venga"). Porta `HU01_retomar_me_vencida.test.tsx` y
// `HU01_retomar_todo_vencido.test.tsx` de la referencia Expo, más el retomar correcto con la
// secuencia de la M-1 (refresh y después /v1/me) y el arranque sin token.
//
// "Con token guardado" se arma como en Jest: login, cerrar la app y volver a montarla con el
// mismo `AlmacenSeguro` (el nombre de la clave del token es libre, HU-01 v6 §4 bis).
import 'package:flutter_test/flutter_test.dart';

import 'soporte/dobles.dart';
import 'soporte/pantalla.dart';
import 'soporte/servidor_falso.dart';

void main() {
  late Entorno e;

  setUp(() => e = Entorno());

  Resp vencida(Llamada _) => errorApi(401, 'SESION_VENCIDA', 'Su sesión se cerró por inactividad');

  /// Login del agente y cierre de la app: queda un token guardado.
  Future<void> dejarSesionGuardada(WidgetTester t) async {
    prepararPlataforma(t);
    e.servidor.sesionValida('agente');
    await montar(t, e);
    await ingresar(t, 'agente1', 'clave');
    await esperarTexto(t, T.rolAgente);
    expect(await e.almacen.leerTodo(), isNotEmpty);
    await desmontar(t);
  }

  testWidgets('sin token guardado: AUTH-01, sin ninguna solicitud de sesión (M-1)', (t) async {
    prepararPlataforma(t);
    e.servidor.sesionValida('agente');
    await montar(t, e);
    await esperarTexto(t, T.ingresar);
    await asentar(t);
    final sesion = e.servidor.llamadas.where((l) => l.ruta.startsWith('/v1/auth/') || l.ruta == '/v1/me').toList();
    expect(sesion, isEmpty);
    expect(find.text(T.inactividad), findsNothing);
  });

  testWidgets(
      'con token guardado: POST /v1/auth/refresh con ese token, después GET /v1/me con el acceso nuevo, y al inicio sin pasar por AUTH-01 (M-1)',
      (t) async {
    await dejarSesionGuardada(t);
    final renovacionGuardada = e.servidor.tokensRenovacion.last;
    final accesoDelLogin = e.servidor.ultimoAcceso;
    String? accesoDelRefresh;
    e.servidor.rutas['POST /v1/auth/refresh'] = (_) {
      final s = e.servidor.darSesion('agente');
      accesoDelRefresh = s['token_acceso'] as String;
      return Resp(200, s);
    };
    final desde = e.servidor.llamadas.length;

    await montar(t, e);
    var vioLogin = false;
    await esperarQue(t, () {
      if (find.text(T.ingresar).evaluate().isNotEmpty) vioLogin = true;
      return find.text(T.rolAgente).evaluate().isNotEmpty;
    }, razon: 'debería retomar al inicio del agente');
    expect(vioLogin, isFalse, reason: 'no debería pasar por AUTH-01');

    final nuevas = e.servidor.llamadas.skip(desde).toList();
    final iRefresh = nuevas.indexWhere((l) => '${l.metodo} ${l.ruta}' == 'POST /v1/auth/refresh');
    final iMe = nuevas.indexWhere((l) => '${l.metodo} ${l.ruta}' == 'GET /v1/me');
    expect(iRefresh, greaterThanOrEqualTo(0), reason: 'falta POST /v1/auth/refresh: $nuevas');
    expect(iMe, greaterThan(iRefresh), reason: 'GET /v1/me tiene que ir después del refresh: $nuevas');
    expect(nuevas[iRefresh].cuerpoMapa['token_renovacion'], renovacionGuardada);
    // /v1/me va con el token de acceso nuevo, el que entregó el refresh.
    expect(nuevas[iMe].token, isNot(accesoDelLogin));
    expect(nuevas[iMe].token, accesoDelRefresh);
    expect(nuevas.where((l) => l.ruta == '/v1/auth/login'), isEmpty);
  });

  testWidgets('al volver a abrir: la renovación responde 200 y /v1/me 401 SESION_VENCIDA → AUTH-03, almacenamiento vacío',
      (t) async {
    await dejarSesionGuardada(t);
    e.servidor.rutas['GET /v1/me'] = vencida;
    await montar(t, e);
    await esperarTexto(t, T.inactividad);
    expect(find.text(T.rolAgente), findsNothing);
    await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
  });

  testWidgets(
      'retomar con todo vencido: la renovación y /v1/me responden 401 SESION_VENCIDA → AUTH-03 (lo que hace la referencia), almacenamiento vacío',
      (t) async {
    await dejarSesionGuardada(t);
    e.servidor.rutas['GET /v1/me'] = vencida;
    e.servidor.rutas['POST /v1/auth/refresh'] = vencida;
    await montar(t, e);
    await esperarTexto(t, T.inactividad);
    expect(find.text(T.rolAgente), findsNothing);
    await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
  });

  testWidgets('después de retomar con la sesión vencida, un login nuevo funciona (§1.2, segundo login)', (t) async {
    await dejarSesionGuardada(t);
    e.servidor.rutas['GET /v1/me'] = vencida;
    e.servidor.rutas['POST /v1/auth/refresh'] = vencida;
    await montar(t, e);
    await esperarTexto(t, T.inactividad);
    await asentar(t);
    e.servidor.sesionValida('supervisor');
    await ingresar(t, 'supervisor1', 'clave');
    await esperarTexto(t, T.rolSupervisor);
    expect(find.textContaining(personas['agente']!.nombre), findsNothing);
  });
}
