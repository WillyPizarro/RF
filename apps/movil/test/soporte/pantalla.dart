// Ayudas de pantalla para las pruebas de caja negra de la app (CONTRATO-MIGRACION-FLUTTER v1.1
// §2): se monta `MovilBuscadorApp` con dobles, los campos se encuentran por su etiqueta de
// accesibilidad, los textos con `find.text`, la vista raíz con `Key('app-raiz')` y el "atrás"
// del sistema con `handlePopRoute`.
import 'package:clock/clock.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:movil_buscador/app.dart';

import 'dobles.dart';

const Key llaveRaiz = Key('app-raiz');

/// Raíz de la palabra que la app nunca muestra (AGENTS.md regla 1). Se arma por partes para que
/// tampoco aparezca escrita en las pruebas.
final String raizProhibida = ['identi', 'ficad'].join();

/// Textos que no se negocian (CONTRATO-HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6).
abstract final class T {
  // HU-01
  static const usuario = 'Usuario';
  static const clave = 'Clave';
  static const ingresar = 'Ingresar';
  static const franja = 'DATOS SINTÉTICOS · PROTOTIPO';
  static const credenciales = 'Usuario o clave incorrectos';
  static const inactividad = 'Su sesión se cerró por inactividad. Ingrese de nuevo.';
  static const otroError = 'No se pudo completar la operación; intente nuevamente';
  static const camposVacios = 'Ingrese su usuario y su clave';
  // HU-02
  static const salir = 'Salir';
  static const rolAgente = 'Rol: Agente';
  static const rolRevisor = 'Rol: Revisor';
  static const rolSupervisor = 'Rol: Supervisor';
  static const consultarPlaca = 'Consultar placa';
  static const rostro = 'Verificar rostro';
  static const misVerif = 'Mis verificaciones';
  static const pendientes = 'Pendientes de revisión';
  static const bitacora = 'Bitácora';
  static const sinPermiso = 'No tiene permiso para usar esta función.';
  static const registrado = 'El intento quedó registrado.';
  static const volverInicio = 'Volver al inicio';
  // HU-03
  static const placa = 'Placa';
  static const motivo = 'Motivo de consulta *';
  static const describa = 'Describa el motivo *';
  static const consultar = 'Consultar';
  static const sinMotivo = 'Indique el motivo de la consulta.';
  static const otroCorto = 'Describa el motivo (mínimo 10 caracteres).';
  static const formato = 'El formato de placa no es válido. Formato esperado: ';
  static const consultando = 'Consultando…';
  static const tiene = 'TIENE REQUISITORIA';
  static const sinReq = 'Sin requisitoria registrada en la fuente consultada';
  static const noReg = 'Placa no registrada en la fuente consultada. Verifique la placa.';
  static const errorConsulta = 'No se pudo completar la consulta; intente nuevamente';
  static const reintentar = 'Reintentar';
  static const volver = 'Volver';
  static const nueva = 'Nueva consulta';
  // HU-07
  static const sintetico = 'SINTÉTICO';
  static const pa24 = 'PA 24';
  static const sistema = 'sistema';
  static const cargarMas = 'Cargar más';
  static const soloLectura = 'Registro de solo lectura';
  static const origen = 'Origen: datos sintéticos';
  static const errorBitacora = 'No se pudo cargar la bitácora; intente nuevamente';
  static const vacia = 'No hay registros para estos filtros.';
  static const aplicar = 'Aplicar filtros';
  static const ayudaFecha = 'dd/mm/aaaa';
  static const fechaInvalida = 'Use fechas con el formato dd/mm/aaaa.';
  // HU-04
  static const camara = 'Leer con cámara';
  static const cerrar = 'Cerrar';
  static const leerPlaca = 'Leer placa';
  static const encuadre = 'Encuadre la placa y toque Capturar';
  static const capturar = 'Capturar';
  static const manual = 'Ingresar manualmente';
  static const placaLeida = 'Placa leída';
  static const confirme = 'Confirme o corrija la placa antes de consultar.';
  static const usar = 'Usar esta placa';
  static const recapturar = 'Volver a capturar';
  static const noLeida = 'No se pudo leer la placa. Pruebe de frente y con más luz.';
  static const volverIntentar = 'Volver a intentar';
  static const sinPermisoCamara = 'La app no tiene permiso para usar la cámara.';
  static const comoDar = 'Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara.';
  static const ajustes = 'Abrir ajustes';
  static const avisoTitulo = 'Antes de leer la placa';
  static const avisoTexto =
      'Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. '
      'Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de uso '
      'y un código de esta instalación.';
  static const entendido = 'Entendido';
  // Indicadores de espera (§1.2)
  static const ingresando = 'Ingresando';
  static const cargando = 'Cargando';
}

// --- Plataforma ----------------------------------------------------------------------------

/// Cuántas veces la app pidió al sistema salir (el "atrás" no tenía a dónde volver).
int salidasAlSistema = 0;

/// Responde a los mensajes del canal de plataforma (SystemNavigator, SystemChrome, …) sin
/// fallar, y cuenta las salidas al sistema.
void prepararPlataforma(WidgetTester t) {
  salidasAlSistema = 0;
  t.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
    if (call.method == 'SystemNavigator.pop') salidasAlSistema += 1;
    return null;
  });
  addTearDown(() => t.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
}

// --- Montaje -------------------------------------------------------------------------------

Future<void> montar(WidgetTester t, Entorno e) async {
  await t.pumpWidget(MovilBuscadorApp(key: UniqueKey(), dependencias: e.dependencias));
  await t.pump();
}

/// Cierra la app (equivale a `screen.unmount()` de Jest).
Future<void> desmontar(WidgetTester t) async {
  await t.pumpWidget(const SizedBox());
  await t.pump();
}

// --- Espera --------------------------------------------------------------------------------

const Duration _paso = Duration(milliseconds: 50);

/// Avanza el tiempo de a 50 ms hasta que aparezca `f` (como `waitFor` de Jest). Máximo 10 s.
Future<void> esperar(WidgetTester t, Finder f, {int pasos = 200}) async {
  for (var i = 0; i < pasos; i++) {
    if (f.evaluate().isNotEmpty) return;
    await t.pump(_paso);
  }
  expect(f, findsWidgets, reason: 'no apareció a tiempo');
}

Future<void> esperarTexto(WidgetTester t, String texto) => esperar(t, find.text(texto));

/// Avanza el tiempo hasta que la condición se cumpla. Máximo 10 s.
Future<void> esperarQue(WidgetTester t, bool Function() cond, {String? razon, int pasos = 200}) async {
  for (var i = 0; i < pasos; i++) {
    if (cond()) return;
    await t.pump(_paso);
  }
  expect(cond(), isTrue, reason: razon ?? 'la condición no se cumplió a tiempo');
}

/// Deja terminar animaciones y respuestas pendientes (1 s), sin exigir que todo quede quieto.
Future<void> asentar(WidgetTester t, {int pasos = 20}) async {
  for (var i = 0; i < pasos; i++) {
    await t.pump(_paso);
  }
}

/// Avanza el reloj de la prueba (temporizadores y `clock.now()`) en pasos chicos.
Future<void> dormir(WidgetTester t, Duration d) async {
  var resto = d;
  while (resto > Duration.zero) {
    final p = resto < _paso ? resto : _paso;
    await t.pump(p);
    resto -= p;
  }
}

// --- Campos --------------------------------------------------------------------------------

bool _coincide(String? etiqueta, String buscada) {
  if (etiqueta == null) return false;
  final e = etiqueta.trim();
  return e == buscada || e.startsWith('$buscada\n');
}

/// Las etiquetas que la app le da a un campo: la etiqueta de accesibilidad (`Semantics`) y, en
/// un `TextField`, su `labelText` o `hintText`.
List<String> _etiquetasDe(Element editable) {
  final etiquetas = <String>[];
  var niveles = 0;
  editable.visitAncestorElements((a) {
    niveles += 1;
    final w = a.widget;
    if (w is TextField) {
      final d = w.decoration;
      if (d?.labelText != null) etiquetas.add(d!.labelText!);
      if (d?.hintText != null) etiquetas.add(d!.hintText!);
      if (d?.semanticCounterText != null) etiquetas.add(d!.semanticCounterText!);
    }
    if (w is Semantics && w.properties.label != null) {
      etiquetas.add(w.properties.label!);
      return false; // la etiqueta de accesibilidad más cercana manda
    }
    return niveles < 25;
  });
  return etiquetas;
}

/// El campo de texto con la etiqueta de accesibilidad `etiqueta` (`find.bySemanticsLabel`).
Finder campo(String etiqueta) {
  final porSemantica = find.bySemanticsLabel(RegExp('^${RegExp.escape(etiqueta)}(\n|\$)'));
  return find.byElementPredicate((e) {
    if (e.widget is! EditableText) return false;
    if (_etiquetasDe(e).any((x) => _coincide(x, etiqueta))) return true;
    for (final s in porSemantica.evaluate()) {
      if (identical(s, e)) return true;
      var dentro = false;
      e.visitAncestorElements((a) {
        if (identical(a, s)) dentro = true;
        return !dentro;
      });
      if (dentro) return true;
    }
    return false;
  }, description: 'campo con la etiqueta "$etiqueta"');
}

Future<void> escribir(WidgetTester t, String etiqueta, String texto) async {
  final f = campo(etiqueta);
  expect(f, findsOneWidget, reason: 'campo "$etiqueta"');
  await t.enterText(f, texto);
  await t.pump();
}

String valor(WidgetTester t, String etiqueta) {
  final f = campo(etiqueta);
  expect(f, findsOneWidget, reason: 'campo "$etiqueta"');
  return t.widget<EditableText>(f).controller.text;
}

EditableText editable(WidgetTester t, String etiqueta) {
  final f = campo(etiqueta);
  expect(f, findsOneWidget, reason: 'campo "$etiqueta"');
  return t.widget<EditableText>(f);
}

// --- Botones y textos ----------------------------------------------------------------------

/// Toca el texto visible `texto` (el último a la vista, como en Jest). Si está en la pantalla
/// pero fuera de la vista (la de `flutter_test` mide 800 × 600), primero se desplaza hasta él,
/// como haría el usuario.
Future<void> tocar(WidgetTester t, String texto) async {
  final f = find.text(texto).hitTestable();
  if (f.evaluate().isEmpty && find.text(texto).evaluate().isNotEmpty) {
    await t.ensureVisible(find.text(texto).last);
    await t.pump();
  }
  expect(f, findsWidgets, reason: 'texto tocable "$texto"');
  await t.tap(f.last, warnIfMissed: false);
  await t.pump();
}

/// Toca el elemento con la etiqueta de accesibilidad `etiqueta` ("Leer con cámara", "Cerrar", …).
Future<void> tocarEtiqueta(WidgetTester t, String etiqueta) async {
  final f = find.bySemanticsLabel(etiqueta);
  expect(f, findsWidgets, reason: 'etiqueta de accesibilidad "$etiqueta"');
  await t.tap(f.first, warnIfMissed: false);
  await t.pump();
}

/// El botón que contiene `f` está habilitado (o deshabilitado), según su semántica.
void esperaHabilitado(WidgetTester t, Finder f, bool habilitado) {
  expect(f, findsWidgets);
  expect(
    t.getSemantics(f.first),
    isSemantics(hasEnabledState: true, isEnabled: habilitado),
    reason: habilitado ? 'debería estar habilitado' : 'debería estar deshabilitado',
  );
}

void habilitado(WidgetTester t, String texto) => esperaHabilitado(t, find.text(texto), true);
void deshabilitado(WidgetTester t, String texto) => esperaHabilitado(t, find.text(texto), false);

/// Todo el texto a la vista (equivale a `JSON.stringify(screen.toJSON())` de Jest): textos,
/// valores de los campos y etiquetas de accesibilidad.
String arbol(WidgetTester t) {
  final b = StringBuffer();
  for (final e in find.byType(RichText).evaluate()) {
    b.writeln((e.widget as RichText).text.toPlainText());
  }
  for (final e in find.byType(EditableText).evaluate()) {
    b.writeln((e.widget as EditableText).controller.text);
  }
  for (final e in find.byType(Semantics).evaluate()) {
    final l = (e.widget as Semantics).properties.label;
    if (l != null) b.writeln(l);
  }
  return b.toString();
}

/// Íconos de "visto bueno" que PLA-06 y PLA-08 no pueden mostrar.
final Set<IconData> iconosVistoBueno = {
  Icons.check,
  Icons.check_circle,
  Icons.check_circle_outline,
  Icons.check_box,
  Icons.done,
  Icons.done_all,
  Icons.task_alt,
  Icons.verified,
};

bool hayVistoBueno(WidgetTester t) {
  if (RegExp('[✓✔☑✅]').hasMatch(arbol(t))) return true;
  return find.byType(Icon).evaluate().any((e) => iconosVistoBueno.contains((e.widget as Icon).icon));
}

// --- Sesión --------------------------------------------------------------------------------

Future<void> ingresar(WidgetTester t, String usuario, String clave) async {
  await esperarTexto(t, T.ingresar);
  await escribir(t, T.usuario, usuario);
  await escribir(t, T.clave, clave);
  await tocar(t, T.ingresar);
}

/// "Atrás" del sistema (`hardwareBackPress` en Expo).
Future<void> atras(WidgetTester t) async {
  await t.binding.handlePopRoute();
  await asentar(t, pasos: 10);
}

/// La app va al segundo plano y vuelve `despues` más tarde según `clock.now()`, sin que corran
/// los temporizadores entre medio (como en el teléfono con la app suspendida).
Future<void> segundoPlanoYVolver(WidgetTester t, Duration despues) async {
  for (final s in [AppLifecycleState.inactive, AppLifecycleState.hidden, AppLifecycleState.paused]) {
    t.binding.handleAppLifecycleStateChanged(s);
  }
  await t.pump();
  final luego = clock.now().add(despues);
  withClock(Clock.fixed(luego), () {
    for (final s in [AppLifecycleState.hidden, AppLifecycleState.inactive, AppLifecycleState.resumed]) {
      t.binding.handleAppLifecycleStateChanged(s);
    }
  });
  await t.pump();
}

// --- PLA-01 --------------------------------------------------------------------------------

/// Abre el selector "Motivo de consulta *" y toca la opción `descripcion`.
Future<void> elegirMotivo(WidgetTester t, String descripcion) async {
  await t.tap(find.text(T.motivo).hitTestable().first, warnIfMissed: false);
  await asentar(t, pasos: 10);
  final opcion = find.text(descripcion).hitTestable();
  await esperar(t, opcion);
  await t.tap(opcion.last, warnIfMissed: false);
  await asentar(t, pasos: 10);
}

String dosDigitos(int n) => n.toString().padLeft(2, '0');
