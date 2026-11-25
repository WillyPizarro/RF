import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';

import 'api/cliente_api.dart';
import 'bordes/bordes.dart';
import 'pantallas/comunes.dart';
import 'pantallas/pantalla_bitacora.dart';
import 'pantallas/pantalla_inicio.dart';
import 'pantallas/pantalla_login.dart';
import 'pantallas/pantalla_placa.dart';
import 'pantallas/pantalla_sin_permiso.dart';
import 'sesion/ambito.dart';
import 'sesion/controlador_sesion.dart';

/// App completa (CONTRATO-MIGRACION-FLUTTER §2): una pantalla a la vez según la sesión, sin pila
/// de navegación, así que al cerrar la sesión "atrás" no puede volver a la pantalla anterior.
///
/// Todo el estado vive en este montaje y en memoria (ADR-0013), salvo los tokens, que van al
/// [AlmacenSeguro]. Desmontar la app no borra el almacenamiento: al volver a montarla con el mismo
/// almacenamiento, retoma la sesión (§1.2).
class MovilBuscadorApp extends StatefulWidget {
  const MovilBuscadorApp({super.key, required this.dependencias});

  final Dependencias dependencias;

  @override
  State<MovilBuscadorApp> createState() => _EstadoMovilBuscadorApp();
}

class _EstadoMovilBuscadorApp extends State<MovilBuscadorApp> with WidgetsBindingObserver {
  late final ControladorSesion _sesion;

  @override
  void initState() {
    super.initState();
    final d = widget.dependencias;
    _sesion = ControladorSesion(
      ClienteApi(urlApi: d.urlApi, clienteHttp: d.clienteHttp),
      d.almacen,
    );
    // Se registra antes que el Navigator de MaterialApp: recibe primero el "atrás" del sistema.
    WidgetsBinding.instance.addObserver(this);
    unawaited(_sesion.restaurar());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _sesion.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState estado) {
    if (estado == AppLifecycleState.resumed) _sesion.revisarAlVolver();
  }

  @override
  Future<bool> didPopRoute() async => _sesion.atras();

  @override
  Widget build(BuildContext context) {
    return AmbitoSesion(
      controlador: _sesion,
      lectorPlaca: widget.dependencias.lectorPlaca,
      child: MaterialApp(
        title: 'Movil Buscador',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colores.primario),
          scaffoldBackgroundColor: Colores.fondo,
        ),
        builder: (context, contenido) => _ZonaSegura(
          sesion: _sesion,
          child: contenido ?? const SizedBox.shrink(),
        ),
        home: const _Pantallas(),
      ),
    );
  }
}

/// Safe area de todas las pantallas, resuelta una sola vez (CONTRATO-MIGRACION-FLUTTER §4;
/// revisión UX HU-04, obs. 2): la zona de la barra de estado lleva el fondo oscuro de la franja
/// "DATOS SINTÉTICOS · PROTOTIPO" con íconos claros, así la franja empieza debajo de la barra; abajo,
/// la zona de navegación queda en blanco y ningún botón queda bajo ella.
///
/// Envuelve también la vista raíz (`Key('app-raiz')`): cualquier toque que empiece dentro de ella
/// cuenta como interacción (CONTRATO-HU-01 §4, sesión activa).
class _ZonaSegura extends StatelessWidget {
  const _ZonaSegura({required this.sesion, required this.child});

  final ControladorSesion sesion;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
        systemNavigationBarColor: Colors.transparent,
        systemNavigationBarIconBrightness: Brightness.dark,
        systemNavigationBarContrastEnforced: false,
      ),
      child: ColoredBox(
        color: Colores.franja,
        child: SafeArea(
          bottom: false,
          left: false,
          right: false,
          child: ColoredBox(
            color: Colores.fondo,
            child: SafeArea(
              top: false,
              child: Listener(
                key: const Key('app-raiz'),
                behavior: HitTestBehavior.translucent,
                onPointerDown: (_) => sesion.registrarInteraccion(),
                child: child,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Pantallas extends StatelessWidget {
  const _Pantallas();

  @override
  Widget build(BuildContext context) {
    final sesion = AmbitoSesion.de(context);
    final perfil = sesion.perfil;
    switch (sesion.pantalla) {
      case Pantalla.inicio when perfil != null:
        return PantallaInicio(perfil: perfil);
      case Pantalla.placa when perfil != null:
        return const PantallaPlaca();
      case Pantalla.bitacora when perfil != null:
        return const PantallaBitacora();
      case Pantalla.sinPermiso when perfil != null:
        return PantallaSinPermiso(alVolver: () => sesion.mostrar(Pantalla.inicio));
      case Pantalla.cargando:
        return const Scaffold(backgroundColor: Colores.fondo, body: Espera());
      default:
        return PantallaLogin(key: ValueKey(sesion.generacionLogin));
    }
  }
}
