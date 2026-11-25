// CONTRATO-HU-03 v5 §6 y §7 (PLA-01 a PLA-08, ERR-01, PLA-01 sin catálogo) y CONTRATO-HU-07 v5
// §5 (BIT-01 con sus filtros, BIT-02), de caja negra contra CONTRATO-MIGRACION-FLUTTER v1.1 §2.
// Porta `__tests__/HU03_HU07.test.tsx` de la referencia `hu-04-expo-referencia`, más el
// indicador "Cargando" de la §1.2.
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'soporte/dobles.dart';
import 'soporte/pantalla.dart';
import 'soporte/servidor_falso.dart';

void main() {
  late Entorno e;

  setUp(() => e = Entorno());

  Future<void> entrar(WidgetTester t, String rol) async {
    prepararPlataforma(t);
    await montar(t, e);
    await ingresar(t, personas[rol]!.usuario, 'clave');
  }

  Future<void> abrirPla01(WidgetTester t) async {
    await entrar(t, 'agente');
    await esperarTexto(t, T.rolAgente);
    await tocar(t, T.consultarPlaca);
    await esperarTexto(t, T.motivo);
    await asentar(t);
  }

  Future<void> consultar(WidgetTester t) async {
    await tocar(t, T.consultar);
    await t.pump();
  }

  // ===========================================================================================
  // HU-03 §6
  // ===========================================================================================

  group('HU-03 — acceso y PLA-01', () {
    testWidgets('HOME-01: "Consultar placa" habilitada; "Verificar rostro" sigue deshabilitada', (t) async {
      e.servidor.sesionValida('agente');
      await entrar(t, 'agente');
      await esperarTexto(t, T.rolAgente);
      habilitado(t, T.consultarPlaca);
      deshabilitado(t, T.rostro);
    });

    testWidgets('PLA-01: campo Placa, selector con el catálogo de /v1/motivos, Consultar; "Describa el motivo *" solo con Otro',
        (t) async {
      e.servidor.sesionValida('agente');
      await abrirPla01(t);
      expect(campo(T.placa), findsOneWidget);
      expect(find.text(T.consultar), findsOneWidget);
      expect(e.servidor.a('GET /v1/motivos'), isNotEmpty);
      expect(campo(T.describa), findsNothing);
      for (final m in motivos.take(4)) {
        await elegirMotivo(t, m['descripcion']!);
        expect(campo(T.describa), findsNothing, reason: m['descripcion']);
      }
      await elegirMotivo(t, 'Otro');
      await esperar(t, campo(T.describa));
    });

    testWidgets('PLA-01: el campo Placa va en mayúsculas y con fuente monoespaciada', (t) async {
      e.servidor.sesionValida('agente');
      await abrirPla01(t);
      await escribir(t, T.placa, 'zza-101');
      final c = editable(t, T.placa);
      final mayus = c.textCapitalization == TextCapitalization.characters || c.controller.text == 'ZZA-101';
      expect(mayus, isTrue, reason: 'mayúsculas');
      final fuente = [c.style.fontFamily ?? '', ...?c.style.fontFamilyFallback].join(' ');
      expect(fuente, matches(RegExp('mono|courier', caseSensitive: false)));
    });

    testWidgets('mientras carga el catálogo se ve el indicador "Cargando" (§1.2)', (t) async {
      final respuesta = Completer<Resp>();
      e.servidor.sesionValida('agente');
      e.servidor.rutas['GET /v1/motivos'] = (_) => respuesta.future;
      await entrar(t, 'agente');
      await esperarTexto(t, T.rolAgente);
      await tocar(t, T.consultarPlaca);
      await esperar(t, find.bySemanticsLabel(T.cargando));
      respuesta.complete(Resp(200, {'motivos': motivos, 'formato_placa': formatoPorDefecto}));
      await esperarTexto(t, T.motivo);
    });
  });

  group('HU-03 v4 — PLA-01 sin catálogo', () {
    final casos = <(String, Resp)>[
      ('503', errorApi(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')),
      ('error de red', red),
      ('respuesta inesperada', const Resp(200, {'otra': 'cosa'})),
    ];
    for (final (nombre, falla) in casos) {
      testWidgets('GET /v1/motivos con $nombre → error de PLA-07, no se puede consultar; "Reintentar" vuelve a pedir el catálogo',
          (t) async {
        e.servidor.sesionValida('agente');
        var veces = 0;
        e.servidor.rutas['GET /v1/motivos'] = (_) =>
            ++veces == 1 ? falla : Resp(200, {'motivos': motivos, 'formato_placa': formatoPorDefecto});
        await entrar(t, 'agente');
        await esperarTexto(t, T.rolAgente);
        await tocar(t, T.consultarPlaca);
        await esperarTexto(t, T.errorConsulta);
        expect(find.text(T.reintentar), findsOneWidget);
        expect(find.text(T.volver), findsOneWidget);
        if (find.text(T.consultar).evaluate().isNotEmpty) {
          deshabilitado(t, T.consultar);
          await t.tap(find.text(T.consultar), warnIfMissed: false);
          await asentar(t);
        }
        expect(e.servidor.postsPlaca, isEmpty);
        expect(arbol(t).toLowerCase(), isNot(contains('sin requisitoria')));
        await tocar(t, T.reintentar);
        await esperarTexto(t, T.motivo);
        expect(veces, 2);
        expect(find.text(T.errorConsulta), findsNothing);
      });
    }
  });

  group('HU-03 — validación local (no se envía nada)', () {
    testWidgets('PLA-02: sin motivo → "Indique el motivo de la consulta." y ningún POST', (t) async {
      e.servidor.sesionValida('agente');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await consultar(t);
      await esperarTexto(t, T.sinMotivo);
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('PLA-02: "Otro" con menos de 10 caracteres → aviso y ningún POST', (t) async {
      e.servidor.sesionValida('agente');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Otro');
      await esperar(t, campo(T.describa));
      await escribir(t, T.describa, 'corto');
      await consultar(t);
      await esperarTexto(t, T.otroCorto);
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('PLA-03: formato inválido → mensaje con la descripción de /v1/motivos, sin enviar', (t) async {
      e.servidor.sesionValida('agente', formato: {'regex': formatoPorDefecto['regex']!, 'descripcion': 'DESCRIPCION-QUE-MANDA-LA-API'});
      await abrirPla01(t);
      await escribir(t, T.placa, 'HOLA MUNDO');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, '${T.formato}DESCRIPCION-QUE-MANDA-LA-API');
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('PLA-03: la app valida con formato_placa.regex de la API, no con uno fijo', (t) async {
      e.servidor.sesionValida('agente', formato: {'regex': r'^ZZ[A-Z]-[0-9]{3}$', 'descripcion': 'ZZX-999'});
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZ1-101'); // vale con el formato por defecto, no con el de la API
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, '${T.formato}ZZX-999');
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('PLA-03: sin motivo y con formato inválido se muestran los dos mensajes', (t) async {
      e.servidor.sesionValida('agente');
      await abrirPla01(t);
      await escribir(t, T.placa, 'HOLA');
      await consultar(t);
      await esperarTexto(t, T.sinMotivo);
      expect(find.text('${T.formato}${formatoPorDefecto['descripcion']}'), findsOneWidget);
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('PLA-03: si la API rechaza el formato (422), se muestra su mensaje', (t) async {
      e.servidor.sesionValida('agente', formato: {'regex': r'^.+$', 'descripcion': 'cualquiera'});
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) =>
          errorApi(422, 'PLACA_FORMATO_INVALIDO', 'El formato de placa no es válido. Formato esperado: DESDE-EL-422');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperar(t, find.textContaining('${T.formato}DESDE-EL-422'));
      expect(find.textContaining(T.sinReq), findsNothing);
    });
  });

  group('HU-03 — consulta y resultados', () {
    testWidgets('envía placa, motivo_codigo y motivo_texto a POST /v1/consultas/placa con el token', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZA-101', 'con_requisitoria');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarQue(t, () => e.servidor.postsPlaca.length == 1);
      final p = e.servidor.postsPlaca.first;
      expect(p.auth, matches(RegExp(r'^Bearer acceso-agente-')));
      expect(p.cuerpoMapa['placa'], 'ZZA-101');
      expect(p.cuerpoMapa['motivo_codigo'], 'control_vehicular');
      expect(p.cuerpoMapa['motivo_texto'], isNull);
    });

    testWidgets('PLA-04: "Consultando…" con la placa y el botón desactivado (no se envía dos veces)', (t) async {
      e.servidor.sesionValida('agente');
      final soltar = Completer<Resp>();
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => soltar.future;
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperar(t, find.textContaining(T.consultando));
      expect(arbol(t), contains('ZZA-101'));
      if (find.text(T.consultar).hitTestable().evaluate().isNotEmpty) {
        deshabilitado(t, T.consultar);
        await t.tap(find.text(T.consultar).hitTestable().last, warnIfMissed: false);
        await t.pump();
      }
      expect(e.servidor.postsPlaca, hasLength(1));
      soltar.complete(resultadoPlaca('ZZA-101', 'con_requisitoria'));
      await esperarTexto(t, T.tiene);
    });

    testWidgets('PLA-05: con_requisitoria → TIENE REQUISITORIA, placa, Motivo:, Consultado: dd/mm/aaaa hh:mm local, Nueva consulta',
        (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZA-101', 'con_requisitoria');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, T.tiene);
      final d = DateTime.parse(consultadoEn).toLocal();
      final fecha = '${dosDigitos(d.day)}/${dosDigitos(d.month)}/${d.year} ${dosDigitos(d.hour)}:${dosDigitos(d.minute)}';
      expect(arbol(t), contains('ZZA-101'));
      expect(find.textContaining(RegExp('^Motivo:')), findsWidgets);
      expect(find.textContaining('Consultado: $fecha'), findsWidgets);
      expect(find.text(T.nueva), findsOneWidget);
      expect(find.textContaining(T.sinReq), findsNothing);
      final todo = arbol(t).toLowerCase();
      for (final dato in ['marca', 'modelo', 'autoridad', raizProhibida]) {
        expect(todo, isNot(contains(dato)), reason: dato);
      }
    });

    testWidgets('PLA-06: sin_requisitoria → texto neutro, sin ✓', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZB-201', 'sin_requisitoria');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZB-201');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperar(t, find.textContaining(T.sinReq));
      expect(arbol(t), contains('ZZB-201'));
      expect(hayVistoBueno(t), isFalse);
      expect(find.text(T.tiene), findsNothing);
    });

    testWidgets('PLA-08: placa_no_registrada → su texto, distinto de PLA-06, sin ✓', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZZ-999', 'placa_no_registrada');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZZ-999');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperar(t, find.textContaining(T.noReg));
      expect(find.textContaining(T.sinReq), findsNothing);
      expect(hayVistoBueno(t), isFalse);
    });

    final errores = <(String, Resp)>[
      ('503 FUENTE_NO_DISPONIBLE', errorApi(503, 'FUENTE_NO_DISPONIBLE', 'No se pudo completar la consulta; intente nuevamente')),
      ('502 FUENTE_RESPUESTA_INVALIDA', errorApi(502, 'FUENTE_RESPUESTA_INVALIDA', 'No se pudo completar la consulta; intente nuevamente')),
      ('503 SERVICIO_NO_DISPONIBLE', errorApi(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')),
      ('error de red', red),
      ('500 inesperado', errorApi(500, 'ERROR_INTERNO', 'x')),
      ('200 con resultado desconocido', resultadoPlaca('ZZA-101', 'otra_cosa')),
    ];
    for (final (nombre, r) in errores) {
      testWidgets('PLA-07: $nombre → mensaje de error, Reintentar y Volver; nunca "sin requisitoria"', (t) async {
        e.servidor.sesionValida('agente');
        e.servidor.rutas['POST /v1/consultas/placa'] = (_) => r;
        await abrirPla01(t);
        await escribir(t, T.placa, 'ZZA-101');
        await elegirMotivo(t, 'Control vehicular');
        await consultar(t);
        await esperarTexto(t, T.errorConsulta);
        expect(find.text(T.reintentar), findsOneWidget);
        expect(find.text(T.volver), findsOneWidget);
        expect(arbol(t).toLowerCase(), isNot(contains('sin requisitoria')));
        expect(find.textContaining(T.noReg), findsNothing);
        expect(find.text(T.tiene), findsNothing);
      });
    }

    testWidgets('PLA-07: "Reintentar" vuelve a enviar la misma placa y el mismo motivo', (t) async {
      e.servidor.sesionValida('agente');
      var n = 0;
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => ++n == 1
          ? errorApi(503, 'FUENTE_NO_DISPONIBLE', 'No se pudo completar la consulta; intente nuevamente')
          : resultadoPlaca('ZZA-101', 'con_requisitoria');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, T.reintentar);
      await tocar(t, T.reintentar);
      await esperarQue(t, () => e.servidor.postsPlaca.length == 2);
      expect(e.servidor.postsPlaca[1].cuerpoMapa['placa'], 'ZZA-101');
      expect(e.servidor.postsPlaca[1].cuerpoMapa['motivo_codigo'], 'control_vehicular');
    });

    testWidgets('403 SIN_PERMISO → ERR-01; "Volver al inicio" lleva al inicio del rol', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] =
          (_) => errorApi(403, 'SIN_PERMISO', 'No tiene permiso para usar esta función');
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, T.sinPermiso);
      expect(find.text(T.registrado), findsOneWidget);
      await tocar(t, T.volverInicio);
      await esperarTexto(t, T.rolAgente);
    });

    testWidgets('nada en el dispositivo: el resultado no queda en el AlmacenSeguro', (t) async {
      e.servidor.sesionValida('agente');
      e.servidor.rutas['POST /v1/consultas/placa'] = (_) => resultadoPlaca('ZZA-101', 'con_requisitoria');
      await abrirPla01(t);
      final antes = (await e.almacen.leerTodo()).keys.toSet();
      await escribir(t, T.placa, 'ZZA-101');
      await elegirMotivo(t, 'Control vehicular');
      await consultar(t);
      await esperarTexto(t, T.tiene);
      final ahora = await e.almacen.leerTodo();
      expect(ahora.keys.toSet(), antes, reason: 'ninguna clave nueva');
      final guardado = ahora.entries.map((x) => '${x.key}=${x.value}').join('\n');
      expect(guardado, isNot(matches(RegExp('ZZA-101|con_requisitoria|c-1'))));
    });
  });

  // ===========================================================================================
  // HU-07 §5
  // ===========================================================================================

  String uuid(int n) {
    final h = n.toRadixString(16).padLeft(8, '0');
    return '$h-0000-4000-8000-${h.padLeft(12, '0')}';
  }

  Map<String, Object?> registro(int n, String tipo, [Map<String, Object?> extra = const {}]) => {
        'id': uuid(n),
        'ocurrido_en': '2026-11-19T15:04:00Z',
        'usuario': 'agente1',
        'rol': 'agente',
        'tipo_evento': tipo,
        'motivo': null,
        'parametros': <String, Object?>{},
        'resultado': null,
        'score': null,
        'captura_id': null,
        'consulta_id': null,
        'codigo_error': null,
        'es_sintetico': true,
        ...extra,
      };

  const etiquetasTipo = {
    'LOGIN_OK': 'Inicio de sesión',
    'LOGIN_FALLIDO': 'Intento fallido',
    'CUENTA_BLOQUEADA': 'Cuenta bloqueada',
    'LOGOUT': 'Cierre de sesión',
    'SESION_VENCIDA': 'Sesión vencida',
    'ACCESO_DENEGADO': 'Acceso denegado',
    'CONSULTA_PLACA': 'Consulta de placa',
    'ERROR_FUENTE': 'Error de fuente',
    'CONSULTA_BITACORA': 'Consulta de bitácora',
  };
  const etiquetasResultado = {
    'con_requisitoria': 'Tiene requisitoria',
    'sin_requisitoria': 'Sin requisitoria registrada',
    'placa_no_registrada': 'Placa no registrada',
    'error': 'Error',
  };

  Resp pagina(List<Map<String, Object?>> regs, [String? cursor]) =>
      Resp(200, {'registros': regs, 'siguiente_cursor': cursor});

  List<Llamada> pedidosBitacora() => e.servidor.a('GET /v1/bitacora');

  Future<void> abrirBitacora(WidgetTester t, Manejador manejador) async {
    e.servidor.sesionValida('supervisor');
    e.servidor.rutas['GET /v1/bitacora'] = manejador;
    await entrar(t, 'supervisor');
    await esperarTexto(t, T.rolSupervisor);
    habilitado(t, T.bitacora);
    await tocar(t, T.bitacora);
  }

  /// HU-07 v4: los filtros pueden ir plegados bajo "Filtros ▾"; se despliegan con un toque.
  Future<void> desplegarFiltros(WidgetTester t) async {
    final titulo = find.textContaining(RegExp('^Filtros'));
    await esperar(t, titulo);
    if (find.text(T.aplicar).evaluate().isEmpty) {
      await t.tap(titulo.first, warnIfMissed: false);
      await asentar(t, pasos: 10);
    }
    await esperarTexto(t, T.aplicar);
  }

  /// "Desde" y "Hasta": por etiqueta de accesibilidad (CONTRATO-MIGRACION-FLUTTER §2).
  Future<void> escribirFecha(WidgetTester t, String etiqueta, String texto) => escribir(t, etiqueta, texto);

  Future<void> aplicarFiltros(WidgetTester t) async {
    final f = find.text(T.aplicar);
    await t.ensureVisible(f);
    await t.pump();
    await tocar(t, T.aplicar);
  }

  group('HU-07 — BIT-01 y BIT-02', () {
    testWidgets(
        'BIT-01: una tarjeta por registro con fecha dd/mm hh:mm, usuario o "sistema", etiqueta, resultado y SINTÉTICO; PA 24; sin editar/borrar/exportar',
        (t) async {
      final tipos = etiquetasTipo.keys.toList();
      final regs = [
        for (var i = 0; i < tipos.length; i++)
          registro(100 - i, tipos[i], {
            'usuario': tipos[i] == 'LOGIN_FALLIDO' ? null : 'agente1',
            'resultado': tipos[i] == 'CONSULTA_PLACA'
                ? 'con_requisitoria'
                : tipos[i] == 'ERROR_FUENTE'
                    ? 'error'
                    : null,
            if (tipos[i] == 'CONSULTA_PLACA' || tipos[i] == 'ERROR_FUENTE') ...{
              'motivo': 'control_vehicular',
              'parametros': tipos[i] == 'ERROR_FUENTE' ? {'placa': 'ZZA-101', 'fuente': 'placas'} : {'placa': 'ZZA-101'},
              'consulta_id': 'c-$i',
              'codigo_error': tipos[i] == 'ERROR_FUENTE' ? 'FUENTE_NO_DISPONIBLE' : null,
            },
          }),
      ];
      // Pantalla alta: las nueve tarjetas a la vista a la vez (la lista puede ser perezosa).
      t.view.physicalSize = const Size(1080, 8000);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.reset);
      await abrirBitacora(t, (_) => pagina(regs));
      await esperarTexto(t, etiquetasTipo['LOGIN_OK']!);
      for (final etiqueta in etiquetasTipo.values) {
        expect(find.text(etiqueta), findsWidgets, reason: etiqueta);
      }
      expect(find.text(etiquetasResultado['con_requisitoria']!), findsWidgets);
      expect(find.text(T.sintetico), findsNWidgets(regs.length));
      expect(find.textContaining(T.sistema), findsWidgets);
      final d = DateTime.parse('2026-11-19T15:04:00Z').toLocal();
      expect(find.textContaining('${dosDigitos(d.day)}/${dosDigitos(d.month)} ${dosDigitos(d.hour)}:${dosDigitos(d.minute)}'),
          findsWidgets);
      expect(find.textContaining(T.pa24), findsWidgets);
      expect(arbol(t), isNot(matches(RegExp('editar|borrar|eliminar|exportar', caseSensitive: false))));
      expect(find.text(T.cargarMas), findsNothing);
    });

    testWidgets('BIT-01: etiquetas de resultado', (t) async {
      final claves = etiquetasResultado.keys.toList();
      final regs = [
        for (var i = 0; i < claves.length; i++)
          registro(50 - i, claves[i] == 'error' ? 'ERROR_FUENTE' : 'CONSULTA_PLACA', {'resultado': claves[i]}),
      ];
      await abrirBitacora(t, (_) => pagina(regs));
      await esperarTexto(t, etiquetasResultado['con_requisitoria']!);
      for (final x in etiquetasResultado.values) {
        expect(find.text(x), findsWidgets, reason: x);
      }
    });

    testWidgets('BIT-01: "Cargar más" pide la página siguiente con el cursor y la agrega', (t) async {
      await abrirBitacora(t, (ll) => ll.consulta['cursor'] == 'CUR-2'
          ? pagina([registro(1, 'LOGOUT')])
          : pagina([registro(2, 'LOGIN_OK')], 'CUR-2'));
      await esperarTexto(t, T.cargarMas);
      await t.ensureVisible(find.text(T.cargarMas));
      await tocar(t, T.cargarMas);
      await esperarTexto(t, etiquetasTipo['LOGOUT']!);
      expect(find.text(etiquetasTipo['LOGIN_OK']!), findsOneWidget);
      expect(find.text(T.cargarMas), findsNothing);
      expect(pedidosBitacora().last.consulta['cursor'], 'CUR-2');
    });

    testWidgets('BIT-02 (v3): "Registro #<8 primeros del id>", "ID" con el id completo, solo lectura; sin "ID de captura" ni "Score"',
        (t) async {
      final r = registro(0x77abcdef, 'ERROR_FUENTE', {
        'motivo': 'control_vehicular',
        'resultado': 'error',
        'codigo_error': 'FUENTE_NO_DISPONIBLE',
        'parametros': {'placa': 'ZZA-101', 'fuente': 'placas'},
        'consulta_id': 'c-77',
      });
      final id = r['id'] as String;
      await abrirBitacora(t, (_) => pagina([r]));
      await esperarTexto(t, etiquetasTipo['ERROR_FUENTE']!);
      await tocar(t, etiquetasTipo['ERROR_FUENTE']!);
      await esperar(t, find.textContaining('Registro #${id.substring(0, 8)}'));
      expect(find.textContaining('Registro #$id'), findsNothing);
      expect(find.textContaining(RegExp(r'^ID\b(?! de captura)')), findsWidgets);
      expect(find.textContaining(id), findsWidgets);
      expect(find.text(T.soloLectura), findsOneWidget);
      expect(find.textContaining(T.origen), findsWidgets);
      final todo = arbol(t);
      expect(todo, contains('FUENTE_NO_DISPONIBLE'));
      expect(todo, contains('agente1'));
      expect(todo, isNot(matches(RegExp('ID de captura|Score'))));
    });

    testWidgets('BIT-01 (v3): filtros con "Filtros", "Usuario", "Desde", "Hasta", "Tipo", "Resultado", ayuda dd/mm/aaaa y "Aplicar filtros"',
        (t) async {
      await abrirBitacora(t, (_) => pagina([registro(1, 'LOGIN_OK')]));
      await desplegarFiltros(t);
      for (final x in ['Usuario', 'Desde', 'Hasta', 'Tipo', 'Resultado']) {
        expect(find.text(x), findsWidgets, reason: x);
      }
      expect(find.textContaining(RegExp('^Filtros')), findsWidgets);
      expect(campo('Usuario'), findsOneWidget);
      expect(campo('Desde'), findsOneWidget);
      expect(campo('Hasta'), findsOneWidget);
      // La ayuda "dd/mm/aaaa" en "Desde" y en "Hasta" (texto a la vista o ayuda del campo).
      final ayudas = find.textContaining(T.ayudaFecha).evaluate().length;
      expect(ayudas, greaterThanOrEqualTo(2));
    });

    for (final fecha in ['2026-11-19', '19-11-2026', '32/13/2026', 'ayer']) {
      testWidgets('BIT-01 (v3): fecha inválida "$fecha" → "Use fechas con el formato dd/mm/aaaa." y no envía la solicitud',
          (t) async {
        await abrirBitacora(t, (_) => pagina([registro(1, 'LOGIN_OK')]));
        await desplegarFiltros(t);
        final antes = pedidosBitacora().length;
        await escribirFecha(t, 'Desde', fecha);
        await aplicarFiltros(t);
        await esperarTexto(t, T.fechaInvalida);
        expect(pedidosBitacora().length, antes);
      });
    }

    testWidgets('BIT-01: "Aplicar filtros" con usuario y una fecha válida pide la bitácora con usuario y desde', (t) async {
      await abrirBitacora(t, (_) => pagina([registro(1, 'LOGIN_OK')]));
      await desplegarFiltros(t);
      final antes = pedidosBitacora().length;
      await escribir(t, 'Usuario', 'agente1');
      await escribirFecha(t, 'Desde', '19/11/2026');
      await aplicarFiltros(t);
      await esperarQue(t, () => pedidosBitacora().length == antes + 1);
      final q = pedidosBitacora().last.consulta;
      expect(q['usuario'], 'agente1');
      expect(q['desde'], isNotNull);
      expect(q['desde'], isNotEmpty);
      expect(find.text(T.fechaInvalida), findsNothing);
    });

    final fallas = <(String, Resp)>[
      ('503', errorApi(503, 'SERVICIO_NO_DISPONIBLE', 'No se pudo completar la operación; intente nuevamente')),
      ('error de red', red),
      ('respuesta inesperada', const Resp(200, {'otra': 'cosa'})),
    ];
    for (final (nombre, r) in fallas) {
      testWidgets('error al cargar ($nombre) → mensaje y Reintentar; nunca la lista vacía', (t) async {
        await abrirBitacora(t, (_) => r);
        await esperarTexto(t, T.errorBitacora);
        expect(find.text(T.reintentar), findsOneWidget);
        expect(find.text(T.vacia), findsNothing);
      });
    }

    testWidgets('lista vacía real → "No hay registros para estos filtros."', (t) async {
      await abrirBitacora(t, (_) => pagina([]));
      await esperarTexto(t, T.vacia);
      expect(find.text(T.errorBitacora), findsNothing);
    });

    testWidgets('mientras carga la bitácora se ve el indicador "Cargando" (§1.2)', (t) async {
      final respuesta = Completer<Resp>();
      await abrirBitacora(t, (_) => respuesta.future);
      await esperar(t, find.bySemanticsLabel(T.cargando));
      respuesta.complete(pagina([registro(1, 'LOGIN_OK')]));
      await esperarTexto(t, etiquetasTipo['LOGIN_OK']!);
    });
  });
}
