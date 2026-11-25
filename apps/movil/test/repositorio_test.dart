// Comprobaciones del repositorio que se pueden automatizar (CONTRATO-MIGRACION-FLUTTER v1.1 §2,
// §5 y §6; CONTRATO-HU-04 v6 §1, §6 y §8). Leen los archivos de apps/movil/ (flutter test corre
// con el directorio del paquete como directorio actual); no miran cómo funciona el código, solo
// qué importa, qué declara y qué existe. Reemplaza al bloque "HU-04 §1 — módulo de borde" de
// `HU04_ocr.test.tsx`. Lo que necesita git, flutter analyze o aapt va como comando en el informe.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'soporte/pantalla.dart' show raizProhibida;

String _ruta(FileSystemEntity f) => f.path.replaceAll(r'\', '/');

List<File> _dart(String dir) => Directory(dir)
    .listSync(recursive: true)
    .whereType<File>()
    .where((f) => f.path.endsWith('.dart'))
    .toList();

bool _enBordes(File f) => _ruta(f).startsWith('lib/bordes/');

/// Líneas `import`/`export` de un archivo.
List<String> _imports(File f) => f
    .readAsLinesSync()
    .where((l) => RegExp(r'''^\s*(import|export)\s+['"]''').hasMatch(l))
    .toList();

/// Secciones `dependencies:` y `dev_dependencies:` de pubspec.yaml: nombre → versión (o null si
/// es una dependencia del SDK, de ruta o de git).
Map<String, String?> _dependencias(List<String> pubspec) {
  final deps = <String, String?>{};
  var enSeccion = false;
  String? actual;
  for (final l in pubspec) {
    if (RegExp(r'^\S').hasMatch(l)) {
      enSeccion = RegExp(r'^(dependencies|dev_dependencies|dependency_overrides):').hasMatch(l);
      actual = null;
      continue;
    }
    if (!enSeccion || l.trim().isEmpty || l.trim().startsWith('#')) continue;
    final m = RegExp(r'^  ([A-Za-z0-9_]+):\s*(.*)$').firstMatch(l);
    if (m != null) {
      actual = m.group(1);
      final v = m.group(2)!.replaceAll(RegExp(r'\s+#.*$'), '').trim();
      deps[actual!] = v.isEmpty ? null : v.replaceAll(RegExp('''^['"]|['"]\$'''), '');
    } else if (actual != null && RegExp(r'^\s{4,}version:\s*').hasMatch(l)) {
      deps[actual] = l.split(':').last.trim().replaceAll(RegExp('''['"]'''), '');
    }
  }
  return deps;
}

void main() {
  final pubspecArchivo = File('pubspec.yaml');
  final pubspec = pubspecArchivo.existsSync() ? pubspecArchivo.readAsLinesSync() : <String>[];

  group('§2 Interfaz', () {
    test('existen lib/app.dart, lib/main.dart y lib/bordes/bordes.dart; el paquete es movil_buscador', () {
      expect(File('lib/app.dart').existsSync(), isTrue);
      expect(File('lib/main.dart').existsSync(), isTrue);
      expect(File('lib/bordes/bordes.dart').existsSync(), isTrue);
      expect(pubspec, contains('name: movil_buscador'));
    });

    test('la cámara, ML Kit, los permisos y el almacenamiento seguro solo se importan en lib/bordes/', () {
      final prohibidos = RegExp(
          r'''['"]package:(camera|google_mlkit_[a-z_]+|permission_handler|flutter_secure_storage)/''');
      final fuera = <String>[];
      for (final f in _dart('lib').where((f) => !_enBordes(f))) {
        for (final l in _imports(f)) {
          if (prohibidos.hasMatch(l)) fuera.add('${_ruta(f)}: ${l.trim()}');
        }
      }
      expect(fuera, isEmpty);
    });

    test('otros clientes HTTP (HttpClient de dart:io, dio, …) solo en lib/main.dart o lib/bordes/', () {
      final clientes = RegExp(r'''\bHttpClient\s*\(|package:(dio|chopper|retrofit|graphql)[/_]|\bIOClient\b''');
      final fuera = <String>[];
      for (final f in _dart('lib').where((f) => !_enBordes(f) && _ruta(f) != 'lib/main.dart')) {
        final lineas = f.readAsLinesSync();
        for (var i = 0; i < lineas.length; i++) {
          if (clientes.hasMatch(lineas[i])) fuera.add('${_ruta(f)}:${i + 1}: ${lineas[i].trim()}');
        }
      }
      expect(fuera, isEmpty);
    });

    test('la hora sale de clock.now(): ningún DateTime.now() en lib/', () {
      final fuera = <String>[];
      for (final f in _dart('lib')) {
        final lineas = f.readAsLinesSync();
        for (var i = 0; i < lineas.length; i++) {
          if (lineas[i].contains('DateTime.now()')) fuera.add('${_ruta(f)}:${i + 1}');
        }
      }
      expect(fuera, isEmpty);
    });
  });

  group('§5 El repositorio sin Expo', () {
    test('ningún archivo Expo ni TypeScript en apps/movil (fuera de build/ y .dart_tool/)', () {
      const expo = ['App.tsx', 'index.ts', 'package.json', 'package-lock.json', 'tsconfig.json', 'app.json', 'eas.json'];
      final restos = <String>[];
      for (final n in expo) {
        if (File(n).existsSync()) restos.add(n);
      }
      if (Directory('src').existsSync()) restos.add('src/');
      if (Directory('plugins').existsSync()) restos.add('plugins/');
      for (final f in Directory('.').listSync(recursive: true).whereType<File>()) {
        final r = _ruta(f);
        if (RegExp(r'(^|/)(build|\.dart_tool|node_modules|\.gradle)/').hasMatch(r)) continue;
        if (RegExp(r'\.tsx?$').hasMatch(r)) restos.add(r);
      }
      expect(restos, isEmpty);
    });

    test('pubspec.yaml y android/ no mencionan expo ni react-native', () {
      final archivos = <File>[
        if (pubspecArchivo.existsSync()) pubspecArchivo,
        if (Directory('android').existsSync())
          ...Directory('android').listSync(recursive: true).whereType<File>().where((f) {
            final r = _ruta(f);
            return !RegExp(r'/(build|\.gradle)/').hasMatch(r) &&
                RegExp(r'\.(gradle|kts|xml|yaml|properties)$').hasMatch(r);
          }),
      ];
      final menciones = <String>[];
      for (final f in archivos) {
        final lineas = f.readAsLinesSync();
        for (var i = 0; i < lineas.length; i++) {
          // Palabra completa, como `grep -riw` (CONTRATO-MIGRACION-FLUTTER v1.3 §5): así
          // `android:exported` no cuenta, pero `expo`, `expo-camera` o `react-native` sí.
          if (RegExp(r'(?<![A-Za-z0-9_])(expo|react-native)(?![A-Za-z0-9_])', caseSensitive: false)
              .hasMatch(lineas[i])) {
            menciones.add('${_ruta(f)}:${i + 1}');
          }
        }
      }
      expect(menciones, isEmpty);
    });
  });

  group('§6 Build y versiones', () {
    test('environment fija flutter 3.50.1 exacto (M-2)', () {
      final env = pubspec.skipWhile((l) => !l.startsWith('environment:')).skip(1).takeWhile((l) => l.startsWith(' '));
      final flutter = env.where((l) => RegExp(r'^\s+flutter:').hasMatch(l)).toList();
      expect(flutter, hasLength(1), reason: 'environment.flutter');
      expect(flutter.single.split(':').last.trim().replaceAll(RegExp('''['"]'''), ''), '3.50.1');
    });

    test('cada dependencia lleva versión exacta (sin ^ ni rangos) y pubspec.lock existe', () {
      final deps = _dependencias(pubspec);
      expect(deps, isNotEmpty);
      final conRango = deps.entries
          .where((d) => d.value != null && !RegExp(r'^\d+\.\d+\.\d+([+-][0-9A-Za-z.\-+]+)?$').hasMatch(d.value!))
          .map((d) => '${d.key}: ${d.value}')
          .toList();
      expect(conRango, isEmpty);
      expect(File('pubspec.lock').existsSync(), isTrue);
    });

    test('paquetes: camera, google_mlkit_text_recognition, flutter_secure_storage, http y clock; sin los de HU-05 ni HU-09', () {
      final deps = _dependencias(pubspec);
      for (final p in ['camera', 'google_mlkit_text_recognition', 'flutter_secure_storage', 'http', 'clock']) {
        expect(deps.keys, contains(p));
      }
      expect(deps.keys, isNot(contains('google_mlkit_face_detection')));
      expect(deps.keys, isNot(contains('geolocator')));
    });

    test('ningún paquete de caché HTTP (HU-04 v6 §6)', () {
      final deps = _dependencias(pubspec).keys;
      final cache = deps.where((d) =>
          d == 'dio_cache_interceptor' || d == 'flutter_cache_manager' || d.startsWith('http_cache') || d == 'cached_network_image');
      expect(cache, isEmpty);
    });

    test('sin flujo continuo: startImageStream no aparece en lib/ (regla 6)', () {
      final usos = _dart('lib').where((f) => f.readAsStringSync().contains('startImageStream')).map(_ruta).toList();
      expect(usos, isEmpty);
    });

    test('applicationId pe.prototipo.movilbuscador y nombre visible "Movil Buscador"', () {
      final gradle = ['android/app/build.gradle.kts', 'android/app/build.gradle'].map(File.new).where((f) => f.existsSync());
      expect(gradle, isNotEmpty);
      expect(gradle.first.readAsStringSync(), matches(RegExp(r'''applicationId\s*=?\s*["']pe\.prototipo\.movilbuscador["']''')));
      final manifiesto = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
      expect(manifiesto, contains('android:label="Movil Buscador"'));
    });

    test('android:allowBackup="false" en el manifiesto', () {
      final manifiesto = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
      expect(manifiesto, contains('android:allowBackup="false"'));
    });

    test('network_security_config.xml: base solo con certificados del sistema y sin texto plano; los del usuario solo en debug-overrides',
        () {
      final f = File('android/app/src/main/res/xml/network_security_config.xml');
      expect(f.existsSync(), isTrue);
      final xml = f.readAsStringSync().replaceAll(RegExp(r'<!--.*?-->', dotAll: true), '');
      final base = RegExp(r'<base-config\b[^>]*>(.*?)</base-config>', dotAll: true).firstMatch(xml);
      expect(base, isNotNull, reason: 'falta <base-config>');
      expect(RegExp(r'<base-config\b[^>]*cleartextTrafficPermitted="false"').hasMatch(xml), isTrue);
      expect(base!.group(1), contains('src="system"'));
      expect(base.group(1), isNot(contains('src="user"')));
      final sinDebug = xml.replaceAll(RegExp(r'<debug-overrides\b.*?</debug-overrides>', dotAll: true), '');
      expect(sinDebug, isNot(contains('src="user"')), reason: 'certificados del usuario fuera de <debug-overrides>');
      expect(sinDebug, isNot(contains('cleartextTrafficPermitted="true"')));
      final manifiesto = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
      expect(manifiesto, contains('android:networkSecurityConfig="@xml/network_security_config"'));
    });

    test('.gitignore excluye key.properties, *.jks y *.keystore', () {
      final reglas = [File('.gitignore'), File('../../.gitignore'), File('android/.gitignore')]
          .where((f) => f.existsSync())
          .expand((f) => f.readAsLinesSync())
          .map((l) => l.trim())
          .toSet();
      expect(reglas.any((r) => r.endsWith('key.properties')), isTrue, reason: 'key.properties');
      expect(reglas.any((r) => r.endsWith('*.jks')), isTrue, reason: '*.jks');
      expect(reglas.any((r) => r.endsWith('*.keystore')), isTrue, reason: '*.keystore');
    });
  });

  group('Reglas de AGENTS.md', () {
    test('regla 1: la palabra prohibida no aparece en lib/ ni en android/ (textos, nombres ni comentarios)', () {
      final archivos = [
        ..._dart('lib'),
        if (Directory('android').existsSync())
          ...Directory('android').listSync(recursive: true).whereType<File>().where((f) =>
              !RegExp(r'/(build|\.gradle)/').hasMatch(_ruta(f)) && RegExp(r'\.(xml|kts|gradle|kt|java)$').hasMatch(_ruta(f))),
      ];
      final con = archivos.where((f) => f.readAsStringSync().toLowerCase().contains(raizProhibida)).map(_ruta).toList();
      expect(con, isEmpty);
    });

    test('regla 8: ninguna imagen fuera de los íconos de la app, ni certificados ni llaves en apps/movil', () {
      final malos = <String>[];
      for (final f in Directory('.').listSync(recursive: true).whereType<File>()) {
        final r = _ruta(f);
        if (RegExp(r'(^|/)(build|\.dart_tool|\.gradle|node_modules)/').hasMatch(r)) continue;
        if (RegExp(r'\.(crt|pem|key|der|jks|keystore|p12)$', caseSensitive: false).hasMatch(r)) malos.add(r);
        if (RegExp(r'\.(jpe?g|png|webp|gif|bmp|heic)$', caseSensitive: false).hasMatch(r)) {
          // Íconos: los recursos de lanzador de Android o un archivo con "icon" en el nombre.
          final icono = RegExp(r'android/app/src/main/res/(mipmap|drawable)[^/]*/').hasMatch(r) ||
              RegExp('icon', caseSensitive: false).hasMatch(r.split('/').last);
          if (!icono) malos.add(r);
        }
      }
      expect(malos, isEmpty);
    });
  });
}
