// CONTRATO-HU-01 v6 §4 y CONTRATO-HU-02 v4 §3, de caja negra contra la interfaz de
// CONTRATO-MIGRACION-FLUTTER v1.1 §2. Porta `__tests__/HU01_HU02.test.tsx` de la referencia
// `hu-04-expo-referencia` (matriz en informes/TESTER-MIGRACION-FLUTTER.md), más los casos de la
// §1.2 que no tenían prueba en Jest (segundo login tras "Salir", indicador "Ingresando").
import 'dart:async';

import 'package:clock/clock.dart';
import 'package:flutter_test/flutter_test.dart';

import 'soporte/dobles.dart';
import 'soporte/pantalla.dart';
import 'soporte/servidor_falso.dart';

void main() {
  late Entorno e;

  setUp(() => e = Entorno());

  Future<void> abrir(WidgetTester t) async {
    prepararPlataforma(t);
    await montar(t, e);
  }

  group('HU-01 AUTH-01 — login', () {
    testWidgets('sin sesión muestra Usuario, Clave, Ingresar y la franja de datos sintéticos', (t) async {
      await abrir(t);
      await esperarTexto(t, T.ingresar);
      expect(find.text(T.usuario), findsWidgets);
      expect(find.text(T.clave), findsWidgets);
      expect(campo(T.usuario), findsOneWidget);
      expect(campo(T.clave), findsOneWidget);
      expect(find.text(T.franja), findsOneWidget);
      expect(find.byKey(llaveRaiz), findsOneWidget);
      expect(arbol(t).toLowerCase(), isNot(contains(raizProhibida)));
    });

    testWidgets('la clave se escribe oculta', (t) async {
      await abrir(t);
      await esperarTexto(t, T.ingresar);
      expect(editable(t, T.clave).obscureText, isTrue);
      expect(editable(t, T.usuario).obscureText, isFalse);
    });

    testWidgets('envía usuario y clave a urlApi + /v1/auth/login por clienteHttp', (t) async {
      e.servidor.sesionValida('agente');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave-buena');
      await esperarQue(t, () => e.servidor.a('POST /v1/auth/login').isNotEmpty);
      final l = e.servidor.a('POST /v1/auth/login').first;
      expect(l.cuerpo, {'usuario': 'agente1', 'clave': 'clave-buena'});
      expect(e.servidor.llamadas.every((x) => x.url.toString().startsWith(urlApi)), isTrue);
    });

    testWidgets('login correcto lleva al inicio de su rol y guarda el token en el AlmacenSeguro', (t) async {
      e.servidor.sesionValida('agente');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave-buena');
      await esperarTexto(t, T.rolAgente);
      expect(await e.almacen.leerTodo(), isNotEmpty);
    });

    testWidgets('mientras espera el login se ve el indicador "Ingresando" (§1.2)', (t) async {
      final respuesta = Completer<Resp>();
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/auth/login'] = (_) => respuesta.future;
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperar(t, find.bySemanticsLabel(T.ingresando));
      respuesta.complete(Resp(200, e.servidor.darSesion('agente')));
      await esperarTexto(t, T.rolAgente);
    });
  });

  group('HU-01 AUTH-01 vacío (v4)', () {
    const casos = <(String, String, String)>[
      ('usuario y clave vacíos', '', ''),
      ('usuario vacío', '', 'clave'),
      ('clave vacía', 'agente1', ''),
      ('solo espacios', '   ', '  '),
      ('usuario con espacios', '   ', 'clave'),
      ('clave con espacios', 'agente1', '   '),
    ];
    for (final (nombre, usuario, clave) in casos) {
      testWidgets('$nombre → "Ingrese su usuario y su clave" y no envía la solicitud', (t) async {
        e.servidor.sesionValida('agente');
        await abrir(t);
        await ingresar(t, usuario, clave);
        await esperarTexto(t, T.camposVacios);
        expect(e.servidor.a('POST /v1/auth/login'), isEmpty);
        expect(find.text(T.rolAgente), findsNothing);
        expect(find.text(T.credenciales), findsNothing);
      });
    }
  });

  group('HU-01 AUTH-02 — usuario o clave incorrectos', () {
    testWidgets('mensaje único, el usuario queda escrito, la clave se vacía, sin intentos restantes', (t) async {
      e.servidor.rutas['POST /v1/auth/login'] =
          (_) => errorApi(401, 'CREDENCIALES_INVALIDAS', 'Usuario o clave incorrectos');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave-mala');
      await esperarTexto(t, T.credenciales);
      expect(find.text(T.credenciales), findsOneWidget);
      expect(valor(t, T.usuario), 'agente1');
      expect(valor(t, T.clave), '');
      expect(arbol(t).toLowerCase(), isNot(contains('intento')));
      expect(find.text(T.rolAgente), findsNothing);
    });
  });

  group('HU-01 AUTH-04 — cuenta bloqueada', () {
    testWidgets('muestra la hora local (HH:MM) y los minutos, vacía la clave e Ingresar sigue activo', (t) async {
      // M-17 (vuelta 1): la hora se fija con withClock (CONTRATO-MIGRACION-FLUTTER §2, "Hora y
      // temporizadores"). Con el reloj real, la prueba calculaba los minutos después que la app y
      // en el borde de 900 s exactos esperaba "15" cuando la app ya había mostrado "16". Con la
      // hora fija y el bloqueo a 15 min justos, el texto esperado es uno solo.
      final ahora = DateTime(2026, 11, 25, 17, 9);
      final hasta = ahora.add(const Duration(minutes: 15));
      await withClock(Clock.fixed(ahora), () async {
        e.servidor.rutas['POST /v1/auth/login'] = (_) => errorApi(423, 'CUENTA_BLOQUEADA', 'Cuenta bloqueada temporalmente', {
              'bloqueado_hasta': hasta.toUtc().toIso8601String(),
            });
        await abrir(t);
        await ingresar(t, 'agente1', 'cualquiera');
        await esperarTexto(t, 'Cuenta bloqueada temporalmente. Podrá volver a intentar a las 17:24 (en 15 min).');
        expect(valor(t, T.clave), '');
        habilitado(t, T.ingresar);
        expect(find.text(T.credenciales), findsNothing);
      });
    });
  });

  group('HU-01 — otro error (regla 7)', () {
    final casos = <(String, Resp)>[
      ('error de red', red),
      ('500', errorApi(500, 'ERROR_INTERNO', 'Error interno')),
      ('503', errorApi(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')),
    ];
    for (final (nombre, r) in casos) {
      testWidgets('$nombre en el login → mensaje genérico, nunca el de credenciales', (t) async {
        e.servidor.rutas['POST /v1/auth/login'] = (_) => r;
        await abrir(t);
        await ingresar(t, 'agente1', 'clave');
        await esperarTexto(t, T.otroError);
        expect(find.text(T.credenciales), findsNothing);
        expect(find.text(T.rolAgente), findsNothing);
      });
    }
  });

  group('HU-01 AUTH-03 — sesión cerrada por inactividad', () {
    testWidgets('sin tocar la pantalla durante inactividad_s (del login): vuelve al login con el aviso', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 2);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      await dormir(t, const Duration(milliseconds: 3500));
      await esperarTexto(t, T.inactividad);
      expect(find.text(T.rolAgente), findsNothing);
    });

    testWidgets('inactividad_s sale del login, no está fijo: con 600 s la sesión sigue a los 30 s', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 600);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      await dormir(t, const Duration(seconds: 30));
      expect(find.text(T.rolAgente), findsOneWidget);
      expect(find.text(T.inactividad), findsNothing);
    });

    testWidgets(
        'tras el cierre: almacenamiento vacío, atrás no vuelve, otro usuario no ve datos del anterior ni se reenvía el token viejo',
        (t) async {
      e.servidor.sesionValida('agente', inactividadS: 2);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperar(t, find.textContaining(personas['agente']!.nombre));
      await dormir(t, const Duration(milliseconds: 3500));
      await esperarTexto(t, T.inactividad);

      await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
      expect(await e.almacen.leerTodo(), isEmpty);

      await atras(t);
      expect(find.text(T.rolAgente), findsNothing);
      expect(find.textContaining(personas['agente']!.nombre), findsNothing);

      final viejos = Set.of(e.servidor.tokensAcceso)..addAll(e.servidor.tokensRenovacion);
      final desde = e.servidor.llamadas.length;
      e.servidor.sesionValida('revisor');
      await ingresar(t, 'revisor1', 'clave');
      await esperarTexto(t, T.rolRevisor);
      expect(find.textContaining(personas['agente']!.nombre), findsNothing);
      expect(find.text(T.rolAgente), findsNothing);
      expect(find.text(T.consultarPlaca), findsNothing);
      final reenviados = e.servidor.llamadas
          .skip(desde)
          .where((l) => (l.token != null && viejos.contains(l.token)) || viejos.any(l.cuerpoTexto.contains))
          .toList();
      expect(reenviados, isEmpty);
    });

    testWidgets('un 401 SESION_VENCIDA de la API también cierra la sesión con el aviso', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['GET /v1/me'] = (_) => errorApi(401, 'SESION_VENCIDA', 'Su sesión se cerró por inactividad');
      e.servidor.rutas['POST /v1/auth/refresh'] =
          (_) => errorApi(401, 'SESION_VENCIDA', 'Su sesión se cerró por inactividad');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.inactividad);
      expect(find.text(T.rolAgente), findsNothing);
      await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
    });

    testWidgets('sesión activa: con toques dentro de app-raiz la sesión no vence', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 2);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      for (var i = 0; i < 10; i++) {
        // Un toque sobre un texto no interactivo de la pantalla, dentro de Key('app-raiz').
        await t.tap(find.text(T.rolAgente), warnIfMissed: false);
        await dormir(t, const Duration(milliseconds: 500));
      }
      expect(find.descendant(of: find.byKey(llaveRaiz), matching: find.text(T.rolAgente)), findsOneWidget);
      expect(find.text(T.inactividad), findsNothing);
    });

    testWidgets('sesión activa: un gesto que empieza en la vista raíz (startGesture) también cuenta', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 2);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      for (var i = 0; i < 10; i++) {
        final g = await t.startGesture(t.getCenter(find.textContaining('Hola, ')));
        await g.up();
        await dormir(t, const Duration(milliseconds: 500));
      }
      expect(find.text(T.rolAgente), findsOneWidget);
      expect(find.text(T.inactividad), findsNothing);
    });
  });

  group('HU-01 §1.2 — volver del segundo plano', () {
    testWidgets('vuelve después de más de inactividad_s sin interacción → AUTH-03', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 600);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      await segundoPlanoYVolver(t, const Duration(seconds: 601));
      await esperar(t, find.text(T.inactividad), pasos: 10);
      expect(find.text(T.rolAgente), findsNothing);
      await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío', pasos: 10);
    });

    testWidgets('vuelve antes de inactividad_s → la sesión sigue', (t) async {
      e.servidor.sesionValida('agente', inactividadS: 600);
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      await segundoPlanoYVolver(t, const Duration(seconds: 30));
      await asentar(t, pasos: 10);
      expect(find.text(T.rolAgente), findsOneWidget);
      expect(find.text(T.inactividad), findsNothing);
    });
  });

  group('HU-02 — inicio por rol', () {
    testWidgets(
        'agente (HOME-01): saludo, rol, Salir; "Consultar placa" habilitada, las otras dos deshabilitadas; nada de otros roles',
        (t) async {
      e.servidor.sesionValida('agente');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      expect(find.textContaining('Hola, ${personas['agente']!.nombre}'), findsWidgets);
      expect(find.text(T.salir), findsOneWidget);
      habilitado(t, T.consultarPlaca);
      deshabilitado(t, T.rostro);
      deshabilitado(t, T.misVerif);
      expect(find.text(T.pendientes), findsNothing);
      expect(find.text(T.bitacora), findsNothing);
    });

    testWidgets('revisor: "Pendientes de revisión" (deshabilitada), nada de consulta ni bitácora', (t) async {
      e.servidor.sesionValida('revisor');
      await abrir(t);
      await ingresar(t, 'revisor1', 'clave');
      await esperarTexto(t, T.rolRevisor);
      expect(find.textContaining('Hola, ${personas['revisor']!.nombre}'), findsWidgets);
      expect(find.text(T.salir), findsOneWidget);
      deshabilitado(t, T.pendientes);
      for (final x in [T.consultarPlaca, T.rostro, T.misVerif, T.bitacora]) {
        expect(find.text(x), findsNothing, reason: x);
      }
    });

    testWidgets('supervisor: "Bitácora" habilitada, nada de consulta ni revisión', (t) async {
      e.servidor.sesionValida('supervisor');
      await abrir(t);
      await ingresar(t, 'supervisor1', 'clave');
      await esperarTexto(t, T.rolSupervisor);
      expect(find.textContaining('Hola, ${personas['supervisor']!.nombre}'), findsWidgets);
      expect(find.text(T.salir), findsOneWidget);
      habilitado(t, T.bitacora);
      for (final x in [T.consultarPlaca, T.rostro, T.misVerif, T.pendientes]) {
        expect(find.text(x), findsNothing, reason: x);
      }
    });

    testWidgets('el menú sale de GET /v1/me (con el token), no de un valor guardado', (t) async {
      e.servidor.sesionValida('agente', rolMe: 'revisor');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolRevisor);
      expect(find.text(T.consultarPlaca), findsNothing);
      final me = e.servidor.a('GET /v1/me');
      expect(me, isNotEmpty);
      expect(me.first.auth, matches(RegExp(r'^Bearer acceso-agente-')));
    });

    testWidgets('Salir: POST /v1/auth/logout con el token, almacenamiento vacío y AUTH-01 sin mensaje', (t) async {
      e.servidor.sesionValida('supervisor');
      await abrir(t);
      await ingresar(t, 'supervisor1', 'clave');
      await esperarTexto(t, T.rolSupervisor);
      await tocar(t, T.salir);
      await esperarTexto(t, T.ingresar);
      await esperarQue(t, () => e.servidor.a('POST /v1/auth/logout').isNotEmpty);
      expect(e.servidor.a('POST /v1/auth/logout').first.auth, matches(RegExp(r'^Bearer acceso-supervisor-')));
      await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
      for (final x in [T.inactividad, T.credenciales, T.otroError]) {
        expect(find.text(x), findsNothing, reason: x);
      }
      await atras(t);
      expect(find.text(T.rolSupervisor), findsNothing);
    });

    testWidgets('segundo login tras "Salir" (§1.2): funciona igual y no muestra nada del anterior', (t) async {
      e.servidor.sesionValida('agente');
      await abrir(t);
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      await tocar(t, T.salir);
      await esperarTexto(t, T.ingresar);
      await asentar(t);
      // Mismo usuario.
      await ingresar(t, 'agente1', 'clave');
      await esperarTexto(t, T.rolAgente);
      expect(e.servidor.a('POST /v1/auth/login'), hasLength(2));
      expect(e.servidor.a('POST /v1/auth/login').last.cuerpo, {'usuario': 'agente1', 'clave': 'clave'});
      await tocar(t, T.salir);
      await esperarTexto(t, T.ingresar);
      await asentar(t);
      // Otro usuario.
      e.servidor.sesionValida('supervisor');
      await ingresar(t, 'supervisor1', 'clave');
      await esperarTexto(t, T.rolSupervisor);
      expect(find.textContaining(personas['agente']!.nombre), findsNothing);
      expect(find.text(T.consultarPlaca), findsNothing);
    });
  });
}
