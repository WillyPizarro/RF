// CONTRATO-HU-04 v6 §2 a §6 (parte de flutter_test), con el aviso de telemetría de OCR-01 (§3,
// v5), de caja negra contra CONTRATO-MIGRACION-FLUTTER v1.1 §2: la cámara y el OCR son un doble
// de `LectorPlaca` en `Dependencias.lectorPlaca`. Porta `__tests__/HU04_ocr.test.tsx` de la
// referencia `hu-04-expo-referencia`. La parte de §1 que en Jest leía archivos (el módulo de
// borde) está en repositorio_test.dart.
import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:movil_buscador/bordes/bordes.dart';

import 'soporte/dobles.dart';
import 'soporte/pantalla.dart';
import 'soporte/servidor_falso.dart';

void main() {
  late Entorno e;

  void servidor({Map<String, String> formato = formatoPorDefecto, int inactividadS = 600}) {
    e.servidor.sesionValida('agente', formato: formato, inactividadS: inactividadS);
    e.servidor.rutas['POST /v1/consultas/placa'] = (ll) => Resp(200, {
          'consulta_id': 'c-1',
          'placa': ll.cuerpoMapa['placa'],
          'resultado': 'con_requisitoria',
          'motivo': {'codigo': 'control_vehicular', 'texto': null},
          'consultado_en': consultadoEn,
        });
  }

  setUp(() {
    e = Entorno();
    servidor();
  });

  Future<void> irAPla01(WidgetTester t) async {
    await ingresar(t, 'agente1', 'clave');
    await esperarTexto(t, T.rolAgente);
    await tocar(t, T.consultarPlaca);
    await esperarTexto(t, T.motivo);
    await asentar(t);
  }

  Future<void> abrirPla01(WidgetTester t) async {
    prepararPlataforma(t);
    await montar(t, e);
    await irAPla01(t);
  }

  Future<void> tocarCamara(WidgetTester t) async {
    await tocarEtiqueta(t, T.camara);
    await asentar(t, pasos: 10);
  }

  /// Abre OCR-01 sin tocar el aviso.
  Future<void> abrirOcr01ConAviso(WidgetTester t) async {
    e.lector.permisos.add(PermisoCamara.concedido);
    await tocarCamara(t);
    await esperarTexto(t, T.encuadre);
  }

  /// Abre OCR-01 y, si aparece el aviso de telemetría (v5), lo cierra.
  Future<void> abrirOcr01(WidgetTester t) async {
    await abrirOcr01ConAviso(t);
    if (find.text(T.entendido).evaluate().isNotEmpty) {
      await tocar(t, T.entendido);
      await esperarQue(t, () => find.text(T.avisoTitulo).evaluate().isEmpty);
    }
  }

  Future<void> capturar(WidgetTester t) async {
    await tocar(t, T.capturar);
    await t.pump();
  }

  Future<void> leerYConfirmar(WidgetTester t, String texto) async {
    e.lector.leeraSiempre(texto);
    await abrirOcr01(t);
    await capturar(t);
    await esperarTexto(t, T.placaLeida);
  }

  Future<void> volverAPla01(WidgetTester t) => esperarTexto(t, T.motivo);

  // ===========================================================================================
  // §2 Entrada desde PLA-01
  // ===========================================================================================

  group('HU-04 §2 — entrada desde PLA-01', () {
    testWidgets('el botón 📷 "Leer con cámara" está habilitado', (t) async {
      await abrirPla01(t);
      esperaHabilitado(t, find.bySemanticsLabel(T.camara), true);
    });

    testWidgets('permiso concedido → OCR-01 con sus textos y el visor activo; capturarYLeer no se llama', (t) async {
      await abrirPla01(t);
      await abrirOcr01(t);
      expect(e.lector.llamadasPermiso, 1);
      for (final x in [T.leerPlaca, T.encuadre, T.capturar, T.manual]) {
        expect(find.text(x), findsWidgets, reason: x);
      }
      expect(find.bySemanticsLabel(T.cerrar), findsWidgets, reason: '"✕" con la etiqueta "Cerrar"');
      expect(find.byKey(llaveVisor), findsOneWidget);
      expect(e.lector.visores.last, isTrue);
      expect(e.lector.llamadasCaptura, 0);
    });

    testWidgets('permiso denegado → OCR-04 con sus textos; capturarYLeer nunca se llama', (t) async {
      e.lector.permisoPorDefecto = PermisoCamara.denegado;
      await abrirPla01(t);
      await tocarCamara(t);
      await esperarTexto(t, T.sinPermisoCamara);
      for (final x in [T.comoDar, T.ajustes, T.manual]) {
        expect(find.text(x), findsWidgets, reason: x);
      }
      expect(e.lector.llamadasCaptura, 0);
      expect(find.byKey(llaveVisor), findsNothing);
    });
  });

  // ===========================================================================================
  // §3 Captura
  // ===========================================================================================

  group('HU-04 §3 — captura', () {
    testWidgets('sin tocar "Capturar" no se lee nada, por más tiempo que pase (regla 6)', (t) async {
      await abrirPla01(t);
      await abrirOcr01(t);
      await dormir(t, const Duration(seconds: 30));
      expect(e.lector.llamadasCaptura, 0);
      expect(find.text(T.placaLeida), findsNothing);
    });

    testWidgets('una sola lectura por toque; mientras espera "Capturar" queda desactivado y un 2.º toque no lee', (t) async {
      final soltar = Completer<LecturaPlaca>();
      e.lector.lecturaPorDefecto = () => soltar.future;
      await abrirPla01(t);
      await abrirOcr01(t);
      await capturar(t);
      expect(e.lector.llamadasCaptura, 1);
      if (find.text(T.capturar).hitTestable().evaluate().isNotEmpty) {
        deshabilitado(t, T.capturar);
        await t.tap(find.text(T.capturar).hitTestable().last, warnIfMissed: false);
        await t.pump();
      }
      expect(e.lector.llamadasCaptura, 1);
      soltar.complete(const LecturaPlaca('ZZA-101'));
      await esperarTexto(t, T.placaLeida);
      expect(e.lector.llamadasCaptura, 1);
    });

    testWidgets('cada toque de "Capturar" es una lectura: volver a capturar y tocar de nuevo → 2 en total', (t) async {
      e.lector.leeraSiempre('ZZA-101');
      await abrirPla01(t);
      await abrirOcr01(t);
      await capturar(t);
      await esperarTexto(t, T.placaLeida);
      await tocar(t, T.recapturar);
      await esperarTexto(t, T.encuadre);
      expect(e.lector.llamadasCaptura, 1);
      await capturar(t);
      await esperarTexto(t, T.placaLeida);
      expect(e.lector.llamadasCaptura, 2);
    });

    testWidgets('falla de la cámara (capturarYLeer lanza) → OCR-03, nunca un resultado', (t) async {
      e.lector.lecturaPorDefecto = () => throw StateError('cámara');
      await abrirPla01(t);
      await abrirOcr01(t);
      await capturar(t);
      await esperarTexto(t, T.noLeida);
      expect(find.text(T.volverIntentar), findsOneWidget);
      expect(find.text(T.manual), findsWidgets);
      expect(find.text(T.placaLeida), findsNothing);
      expect(arbol(t).toLowerCase(), isNot(contains('sin requisitoria')));
    });

    testWidgets('"✕" vuelve a PLA-01 sin cambios (placa y motivo como estaban)', (t) async {
      await abrirPla01(t);
      await escribir(t, T.placa, 'ZZB-201');
      await elegirMotivo(t, 'Operativo');
      await abrirOcr01(t);
      await tocarEtiqueta(t, T.cerrar);
      await volverAPla01(t);
      await asentar(t);
      expect(valor(t, T.placa), 'ZZB-201');
      await tocar(t, T.consultar);
      await esperarQue(t, () => e.servidor.postsPlaca.length == 1);
      expect(e.servidor.postsPlaca.first.cuerpoMapa['placa'], 'ZZB-201');
      expect(e.servidor.postsPlaca.first.cuerpoMapa['motivo_codigo'], 'operativo');
    });

    for (final desde in ['OCR-01', 'OCR-03', 'OCR-04']) {
      testWidgets('"Ingresar manualmente" desde $desde vuelve a PLA-01 sin cambios, con el foco en "Placa"', (t) async {
        await abrirPla01(t);
        await escribir(t, T.placa, 'ZZB-201');
        if (desde == 'OCR-04') {
          e.lector.permisos.add(PermisoCamara.denegado);
          await tocarCamara(t);
          await esperarTexto(t, T.sinPermisoCamara);
        } else {
          await abrirOcr01(t);
          if (desde == 'OCR-03') {
            e.lector.leera(null);
            await capturar(t);
            await esperarTexto(t, T.noLeida);
          }
        }
        await tocar(t, T.manual);
        await volverAPla01(t);
        await asentar(t);
        expect(valor(t, T.placa), 'ZZB-201');
        expect(editable(t, T.placa).focusNode.hasFocus, isTrue, reason: 'foco en el campo "Placa"');
        expect(e.servidor.postsPlaca, isEmpty);
      });
    }
  });

  // ===========================================================================================
  // §4 Del texto leído a la placa propuesta (tabla completa)
  // ===========================================================================================

  group('HU-04 §4 — texto leído → placa propuesta', () {
    const aceptados = <(String, String)>[
      ('ZZA-101', 'ZZA-101'),
      ('zza-101', 'ZZA-101'),
      ('ZZA 101', 'ZZA-101'),
      ('ZZA.101', 'ZZA-101'),
      ('PERU\nZZB-201\nLIMA', 'ZZB-201'),
      ('ZZA-101 ZZB-201', 'ZZA-101'),
    ];
    for (final (texto, esperado) in aceptados) {
      testWidgets('${texto.replaceAll('\n', r'\n')} → OCR-02 con $esperado', (t) async {
        e.lector.leeraSiempre(texto);
        await abrirPla01(t);
        await abrirOcr01(t);
        await capturar(t);
        await esperarTexto(t, T.placaLeida);
        expect(valor(t, T.placaLeida), esperado);
      });
    }

    for (final texto in <String?>['ZZA-1O1', 'PERU', '', null]) {
      testWidgets('${texto == null ? 'null' : '"$texto"'} → OCR-03 (la app no adivina caracteres)', (t) async {
        e.lector.leeraSiempre(texto);
        await abrirPla01(t);
        await abrirOcr01(t);
        await capturar(t);
        await esperarTexto(t, T.noLeida);
        expect(find.text(T.placaLeida), findsNothing);
      });
    }

    testWidgets('si la API cambia formato_placa.regex, cambia lo que se acepta (sin tocar código)', (t) async {
      servidor(formato: {'regex': r'^[A-Z]{2}[0-9]{4}$', 'descripcion': 'AB1234'});
      e.lector
        ..leera('ZZA-101')
        ..leera('ab1234');
      await abrirPla01(t);
      await abrirOcr01(t);
      await capturar(t);
      await esperarTexto(t, T.noLeida); // ZZA-101 no cumple la regex nueva
      await tocar(t, T.volverIntentar);
      await esperarTexto(t, T.encuadre);
      await capturar(t);
      await esperarTexto(t, T.placaLeida);
      expect(valor(t, T.placaLeida), 'AB1234');
    });
  });

  // ===========================================================================================
  // §5 Confirmar y volver a la consulta
  // ===========================================================================================

  group('HU-04 §5 — confirmar y volver', () {
    testWidgets('OCR-02: "Placa leída", campo editable, aviso, "Usar esta placa", "Volver a capturar"; ninguna imagen', (t) async {
      await abrirPla01(t);
      await leerYConfirmar(t, 'ZZA-101');
      for (final x in [T.confirme, T.usar, T.recapturar]) {
        expect(find.text(x), findsWidgets, reason: x);
      }
      final c = editable(t, T.placaLeida);
      expect(c.readOnly, isFalse);
      expect(find.byType(Image), findsNothing);
      expect(find.byType(RawImage), findsNothing);
      expect(arbol(t), isNot(matches(RegExp(r'file://|data:image|\.jpe?g|\.png', caseSensitive: false))));
    });

    testWidgets('corregir: el texto editado vuelve a PLA-01 en "Placa"', (t) async {
      await abrirPla01(t);
      await leerYConfirmar(t, 'ZZA-101');
      await escribir(t, T.placaLeida, 'ZZB-201');
      await tocar(t, T.usar);
      await volverAPla01(t);
      await asentar(t);
      expect(valor(t, T.placa), 'ZZB-201');
    });

    testWidgets('nunca consulta sola: entre 📷 y "Consultar" no hay ninguna solicitud; sin motivo previo, el motivo sigue vacío',
        (t) async {
      await abrirPla01(t);
      final desde = e.servidor.llamadas.length;
      await leerYConfirmar(t, 'ZZA-101');
      await tocar(t, T.usar);
      await volverAPla01(t);
      await asentar(t);
      expect(valor(t, T.placa), 'ZZA-101');
      expect(e.servidor.llamadas.skip(desde), isEmpty);
      await tocar(t, T.consultar);
      await esperarTexto(t, T.sinMotivo);
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('el motivo elegido antes de abrir la cámara se conserva; la consulta es la de HU-03 (sin imagen ni campos nuevos)',
        (t) async {
      await abrirPla01(t);
      await elegirMotivo(t, 'Control vehicular');
      final desde = e.servidor.llamadas.length;
      await leerYConfirmar(t, 'zza 101');
      await tocar(t, T.usar);
      await volverAPla01(t);
      await asentar(t);
      expect(e.servidor.llamadas.skip(desde), isEmpty);
      await tocar(t, T.consultar);
      await esperarTexto(t, T.tiene);
      expect(e.servidor.postsPlaca, hasLength(1));
      final cuerpo = e.servidor.postsPlaca.first.cuerpoMapa;
      expect(cuerpo['placa'], 'ZZA-101');
      expect(cuerpo['motivo_codigo'], 'control_vehicular');
      expect(cuerpo.keys.every({'placa', 'motivo_codigo', 'motivo_texto'}.contains), isTrue, reason: '$cuerpo');
    });

    testWidgets('sigue HU-03: una corrección con formato inválido se rechaza en PLA-03 sin enviar', (t) async {
      await abrirPla01(t);
      await elegirMotivo(t, 'Control vehicular');
      await leerYConfirmar(t, 'ZZA-101');
      await escribir(t, T.placaLeida, 'ZZA-1O1');
      await tocar(t, T.usar);
      await volverAPla01(t);
      await asentar(t);
      await tocar(t, T.consultar);
      await esperarTexto(t, '${T.formato}${formatoPorDefecto['descripcion']}');
      expect(e.servidor.postsPlaca, isEmpty);
    });

    testWidgets('"Volver a capturar" → OCR-01 y el valor leído se descarta', (t) async {
      await abrirPla01(t);
      await leerYConfirmar(t, 'ZZA-101');
      await tocar(t, T.recapturar);
      await esperarTexto(t, T.encuadre);
      expect(find.text(T.placaLeida), findsNothing);
      await tocarEtiqueta(t, T.cerrar);
      await volverAPla01(t);
      await asentar(t);
      expect(valor(t, T.placa), '');
    });

    testWidgets('"Volver a intentar" en OCR-03 → OCR-01', (t) async {
      e.lector.leeraSiempre(null);
      await abrirPla01(t);
      await abrirOcr01(t);
      await capturar(t);
      await esperarTexto(t, T.noLeida);
      await tocar(t, T.volverIntentar);
      await esperarTexto(t, T.encuadre);
    });

    testWidgets('"Abrir ajustes" en OCR-04 llama a abrirAjustes()', (t) async {
      e.lector.permisoPorDefecto = PermisoCamara.denegado;
      await abrirPla01(t);
      await tocarCamara(t);
      await esperarTexto(t, T.ajustes);
      await tocar(t, T.ajustes);
      await esperarQue(t, () => e.lector.llamadasAjustes == 1);
    });

    testWidgets('volver con permiso: tras OCR-04, si ahora está concedido, 📷 abre OCR-01', (t) async {
      e.lector.permisos.addAll([PermisoCamara.denegado, PermisoCamara.concedido]);
      await abrirPla01(t);
      await tocarCamara(t);
      await esperarTexto(t, T.sinPermisoCamara);
      await tocar(t, T.manual);
      await volverAPla01(t);
      await asentar(t);
      await tocarCamara(t);
      await esperarTexto(t, T.encuadre);
      expect(e.lector.llamadasPermiso, 2);
    });
  });

  // ===========================================================================================
  // §6 Nada se guarda ni sale del dispositivo (parte de flutter_test)
  // ===========================================================================================

  group('HU-04 §6 — nada se guarda ni sale', () {
    testWidgets('en todo el flujo OCR-01 → OCR-03 el MockClient no recibe ninguna solicitud', (t) async {
      e.lector
        ..leera(null)
        ..fallara();
      await abrirPla01(t);
      final desde = e.servidor.llamadas.length;
      await abrirOcr01(t);
      await capturar(t);
      await esperarTexto(t, T.noLeida);
      await tocar(t, T.volverIntentar);
      await esperarTexto(t, T.encuadre);
      await capturar(t);
      await esperarTexto(t, T.noLeida);
      expect(e.servidor.llamadas.skip(desde), isEmpty);
    });

    testWidgets('después de leer, el AlmacenSeguro no tiene ninguna clave nueva', (t) async {
      await abrirPla01(t);
      final antes = await e.almacen.leerTodo();
      await leerYConfirmar(t, 'ZZA-101');
      await tocar(t, T.usar);
      await volverAPla01(t);
      final despues = await e.almacen.leerTodo();
      expect(despues.keys.toSet(), antes.keys.toSet());
      expect(despues.values.join('\n'), isNot(contains('ZZA-101')));
    });
  });

  // ===========================================================================================
  // §3 Aviso de telemetría de ML Kit (v5)
  // ===========================================================================================

  group('HU-04 §3 (v5) — aviso de telemetría en OCR-01', () {
    testWidgets('la primera vez por sesión aparece la tarjeta con sus textos; "Capturar" desactivado; "Ingresar manualmente" activo',
        (t) async {
      e.lector.leeraSiempre('ZZA-101');
      await abrirPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
      expect(find.text(T.avisoTexto), findsOneWidget);
      expect(find.text(T.entendido), findsOneWidget);
      deshabilitado(t, T.capturar);
      await t.tap(find.text(T.capturar), warnIfMissed: false);
      await asentar(t);
      expect(e.lector.llamadasCaptura, 0);
      habilitado(t, T.manual);
    });

    testWidgets('tocar fuera de la tarjeta (el visor) no hace nada', (t) async {
      await abrirPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
      await t.tapAt(t.getTopLeft(find.byKey(llaveVisor)) + const Offset(4, 4));
      await asentar(t);
      expect(find.text(T.avisoTitulo), findsOneWidget);
      deshabilitado(t, T.capturar);
      expect(e.lector.llamadasCaptura, 0);
    });

    testWidgets('"Entendido": la tarjeta desaparece, "Capturar" se activa y en esa sesión no vuelve a aparecer', (t) async {
      e.lector.leeraSiempre('ZZA-101');
      await abrirPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
      await tocar(t, T.entendido);
      await esperarQue(t, () => find.text(T.avisoTitulo).evaluate().isEmpty);
      habilitado(t, T.capturar);
      await capturar(t);
      await esperarTexto(t, T.placaLeida);
      expect(e.lector.llamadasCaptura, 1);
      // Salir y volver a OCR-01 en la misma sesión: no aparece.
      await tocar(t, T.recapturar);
      await esperarTexto(t, T.encuadre);
      expect(find.text(T.avisoTitulo), findsNothing);
      await tocarEtiqueta(t, T.cerrar);
      await volverAPla01(t);
      await asentar(t);
      await abrirOcr01ConAviso(t);
      await asentar(t);
      expect(find.text(T.avisoTitulo), findsNothing);
      habilitado(t, T.capturar);
    });

    for (final como in ['✕', 'atrás', 'Ingresar manualmente']) {
      testWidgets('salir con "$como" con la tarjeta a la vista no la da por vista: al volver a OCR-01 aparece de nuevo', (t) async {
        await abrirPla01(t);
        await abrirOcr01ConAviso(t);
        await esperarTexto(t, T.avisoTitulo);
        if (como == '✕') {
          await tocarEtiqueta(t, T.cerrar);
        } else if (como == 'atrás') {
          await atras(t);
        } else {
          await tocar(t, T.manual);
        }
        await volverAPla01(t);
        await asentar(t);
        expect(find.text(T.avisoTitulo), findsNothing);
        await abrirOcr01ConAviso(t);
        await esperarTexto(t, T.avisoTitulo);
        expect(e.lector.llamadasCaptura, 0);
      });
    }

    testWidgets('solo en memoria: tras "Salir" y volver a entrar, aparece otra vez; el AlmacenSeguro sin claves nuevas por el aviso',
        (t) async {
      await abrirPla01(t);
      final antes = (await e.almacen.leerTodo()).keys.toSet();
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
      await tocar(t, T.entendido);
      await esperarQue(t, () => find.text(T.avisoTitulo).evaluate().isEmpty);
      final ahora = await e.almacen.leerTodo();
      expect(ahora.keys.toSet(), antes);
      expect(ahora.values.join('\n'),
          isNot(matches(RegExp('entendido|aviso|telemetr|mlkit|ml kit', caseSensitive: false))));
      // Volver al inicio y salir.
      await tocarEtiqueta(t, T.cerrar);
      await volverAPla01(t);
      for (var i = 0; i < 5 && find.text(T.salir).evaluate().isEmpty; i++) {
        await atras(t);
      }
      await tocar(t, T.salir);
      await esperarTexto(t, T.ingresar);
      await asentar(t);
      // Nueva sesión.
      await irAPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
    });

    testWidgets('solo en memoria: tras el cierre por inactividad, el aviso aparece otra vez y AUTH-03 sigue igual', (t) async {
      servidor(inactividadS: 2);
      await abrirPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
      await tocar(t, T.entendido);
      await esperarQue(t, () => find.text(T.avisoTitulo).evaluate().isEmpty);
      await tocarEtiqueta(t, T.cerrar);
      await volverAPla01(t);
      await dormir(t, const Duration(milliseconds: 3500));
      await esperarTexto(t, T.inactividad);
      await esperarQue(t, () => e.almacen.datos.isEmpty, razon: 'el almacenamiento debería quedar vacío');
      servidor(inactividadS: 600);
      await asentar(t);
      await irAPla01(t);
      await abrirOcr01ConAviso(t);
      await esperarTexto(t, T.avisoTitulo);
    });

    testWidgets('sin permiso: OCR-04 no muestra el aviso', (t) async {
      e.lector.permisoPorDefecto = PermisoCamara.denegado;
      await abrirPla01(t);
      await tocarCamara(t);
      await esperarTexto(t, T.sinPermisoCamara);
      expect(find.text(T.avisoTitulo), findsNothing);
      expect(find.text(T.entendido), findsNothing);
    });
  });
}
