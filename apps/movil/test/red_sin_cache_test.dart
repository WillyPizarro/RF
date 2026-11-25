// CONTRATO-MIGRACION-FLUTTER v1.1 §2 ("toda la red pasa por clienteHttp") y §3 (lo que en Expo
// era `cache: 'no-store'`, CONTRATO-HU-04 v6 §6). Reemplaza a `HU04_sin_cache.test.tsx` de la
// referencia: un recorrido por todas las solicitudes de la app (login, me, motivos, consulta,
// retomar, logout y bitácora) en el que (1) cada solicitud llega al MockClient con urlApi y
// (2) la app no abre ningún HttpClient de dart:io por su cuenta. La parte de la caché que se ve
// en el repositorio (ningún paquete de caché en pubspec.yaml) está en repositorio_test.dart.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'soporte/dobles.dart';
import 'soporte/pantalla.dart';
import 'soporte/servidor_falso.dart';

/// Cuenta los HttpClient de dart:io que se crean mientras corre la prueba.
class _EspiaHttp extends HttpOverrides {
  int creados = 0;

  @override
  HttpClient createHttpClient(SecurityContext? context) {
    creados += 1;
    return super.createHttpClient(context);
  }
}

void main() {
  testWidgets('toda la red de la app pasa por clienteHttp (login, me, motivos, consulta, retomar, logout, bitácora)', (t) async {
    final anterior = HttpOverrides.current;
    final espia = _EspiaHttp();
    HttpOverrides.global = espia;
    addTearDown(() => HttpOverrides.global = anterior);
    prepararPlataforma(t);

    final e = Entorno();
    e.servidor.sesionValida('agente');
    e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZA-101', 'con_requisitoria');

    // Agente: login, /v1/me, /v1/motivos y consulta de placa.
    await montar(t, e);
    await ingresar(t, 'agente1', 'clave');
    await esperarTexto(t, T.rolAgente);
    await tocar(t, T.consultarPlaca);
    await esperarTexto(t, T.motivo);
    await asentar(t);
    await escribir(t, T.placa, 'ZZA-101');
    await elegirMotivo(t, 'Control vehicular');
    await tocar(t, T.consultar);
    await esperarTexto(t, T.tiene);

    // Retomar la sesión al volver a abrir la app (refresh y /v1/me), y "Salir".
    await desmontar(t);
    await montar(t, e);
    await esperarTexto(t, T.rolAgente);
    await tocar(t, T.salir);
    await esperarTexto(t, T.ingresar);
    await asentar(t);

    // Supervisor: bitácora.
    e.servidor.sesionValida('supervisor');
    e.servidor.rutas['GET /v1/bitacora'] = (_) => const Resp(200, {'registros': [], 'siguiente_cursor': null});
    await ingresar(t, 'supervisor1', 'clave');
    await esperarTexto(t, T.rolSupervisor);
    await tocar(t, T.bitacora);
    await esperarQue(t, () => e.servidor.a('GET /v1/bitacora').isNotEmpty);
    await asentar(t);

    final rutas = e.servidor.llamadas.map((l) => '${l.metodo} ${l.ruta}').toSet();
    for (final r in [
      'POST /v1/auth/login',
      'POST /v1/auth/refresh',
      'GET /v1/me',
      'GET /v1/motivos',
      'POST /v1/consultas/placa',
      'POST /v1/auth/logout',
      'GET /v1/bitacora',
    ]) {
      expect(rutas, contains(r));
    }
    final fuera = e.servidor.llamadas.where((l) => !l.url.toString().startsWith('$urlApi/v1/')).toList();
    expect(fuera, isEmpty, reason: 'solicitudes fuera de urlApi + /v1/');
    expect(espia.creados, 0, reason: 'la app abrió un HttpClient de dart:io por fuera de clienteHttp');
  });
}
