import 'package:flutter/widgets.dart';

import '../bordes/bordes.dart';
import 'controlador_sesion.dart';

/// Da a las pantallas el controlador de la sesión y el lector de placas del montaje actual.
class AmbitoSesion extends InheritedNotifier<ControladorSesion> {
  const AmbitoSesion({
    super.key,
    required ControladorSesion controlador,
    required this.lectorPlaca,
    required super.child,
  }) : super(notifier: controlador);

  final LectorPlaca lectorPlaca;

  /// El controlador; la pantalla se reconstruye cuando cambia.
  static ControladorSesion de(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AmbitoSesion>()!.notifier!;

  /// El controlador, sin reconstruir la pantalla cuando cambia.
  static ControladorSesion leer(BuildContext context) =>
      context.getInheritedWidgetOfExactType<AmbitoSesion>()!.notifier!;

  static LectorPlaca lector(BuildContext context) =>
      context.getInheritedWidgetOfExactType<AmbitoSesion>()!.lectorPlaca;
}
