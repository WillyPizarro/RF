import 'dart:math' as math;

import 'package:clock/clock.dart';
import 'package:material_ui/material_ui.dart';

import '../sesion/ambito.dart';
import '../sesion/controlador_sesion.dart';
import 'comunes.dart';

const _mensajeError = 'No se pudo completar la operación; intente nuevamente';

String _dos(int n) => n.toString().padLeft(2, '0');

/// "Podrá volver a intentar a las HH:MM (en N min)", en hora local, desde `bloqueado_hasta`.
String textoBloqueo(String hastaIso) {
  final hasta = DateTime.parse(hastaIso).toLocal();
  final ms = hasta.millisecondsSinceEpoch - clock.now().millisecondsSinceEpoch;
  final minutos = math.max(1, (ms / 60000).ceil());
  final hora = '${_dos(hasta.hour)}:${_dos(hasta.minute)}';
  return 'Cuenta bloqueada temporalmente. Podrá volver a intentar a las $hora (en $minutos min).';
}

/// AUTH-01 a AUTH-04 (CONTRATO-HU-01 §4).
class PantallaLogin extends StatefulWidget {
  const PantallaLogin({super.key});

  @override
  State<PantallaLogin> createState() => _EstadoPantallaLogin();
}

class _EstadoPantallaLogin extends State<PantallaLogin> {
  final _usuario = TextEditingController();
  final _clave = TextEditingController();
  bool _enviando = false;

  @override
  void dispose() {
    _usuario.dispose();
    _clave.dispose();
    super.dispose();
  }

  Future<void> _alIngresar() async {
    if (_enviando) return;
    final sesion = AmbitoSesion.leer(context);
    final usuario = _usuario.text;
    final clave = _clave.text;
    if (usuario.trim().isEmpty || clave.trim().isEmpty) {
      sesion.avisar(const Aviso(TipoAviso.vacios)); // CONTRATO-HU-01 v4: no se envía la solicitud
      return;
    }
    setState(() => _enviando = true);
    _clave.clear(); // la clave se vacía en cualquier resultado (AUTH-02, AUTH-04)
    try {
      await sesion.ingresar(usuario, clave);
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final aviso = AmbitoSesion.de(context).aviso;
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        children: [
          const FranjaPrototipo(),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 48, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Movil Buscador',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: Colores.texto),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Acceso solo para personal autorizado',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 15, color: Colores.tenue),
                  ),
                  const SizedBox(height: 24),
                  if (aviso != null) _Mensaje(aviso: aviso),
                  const SizedBox(height: 12),
                  const EtiquetaCampo('Usuario'),
                  const SizedBox(height: 4),
                  CampoTexto(
                    etiqueta: 'Usuario',
                    controlador: _usuario,
                    soloLectura: _enviando,
                  ),
                  const SizedBox(height: 12),
                  const EtiquetaCampo('Clave'),
                  const SizedBox(height: 4),
                  CampoTexto(
                    etiqueta: 'Clave',
                    controlador: _clave,
                    ocultar: true,
                    soloLectura: _enviando,
                    alEnviar: _alIngresar,
                  ),
                  const SizedBox(height: 24),
                  Boton(texto: 'Ingresar', alTocar: _alIngresar),
                  if (_enviando) ...[
                    const SizedBox(height: 16),
                    const Espera(etiqueta: 'Ingresando'),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Mensaje del login. El ícono distingue el tipo sin depender del color (revisión UX #1) y queda
/// oculto para el lector de pantalla, que lee solo el texto.
class _Mensaje extends StatelessWidget {
  const _Mensaje({required this.aviso});

  final Aviso aviso;

  @override
  Widget build(BuildContext context) {
    final String texto;
    final Color fondo;
    final Color borde;
    String? icono;
    switch (aviso.tipo) {
      case TipoAviso.vacios:
        texto = 'Ingrese su usuario y su clave';
        fondo = Colores.advertencia;
        borde = Colores.advertenciaBorde;
      case TipoAviso.inactividad:
        texto = 'Su sesión se cerró por inactividad. Ingrese de nuevo.';
        fondo = Colores.info;
        borde = Colores.infoBorde;
        icono = 'ⓘ';
      case TipoAviso.credenciales:
        texto = 'Usuario o clave incorrectos';
        fondo = Colores.error;
        borde = Colores.errorBorde;
        icono = '⚠';
      case TipoAviso.bloqueo:
        texto = textoBloqueo(aviso.hasta!);
        fondo = Colores.advertencia;
        borde = Colores.advertenciaBorde;
        icono = '🔒';
      case TipoAviso.error:
        // Falla de red o del servidor: tono neutro, no es un error del usuario (revisión UX #4).
        texto = _mensajeError;
        fondo = Colores.neutro;
        borde = Colores.neutroBorde;
    }
    return Semantics(
      liveRegion: true,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: fondo,
          border: Border.all(color: borde),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (icono != null)
              ExcludeSemantics(
                child: Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Text(icono, style: const TextStyle(fontSize: 16, color: Colores.texto)),
                ),
              ),
            Expanded(
              child: Text(texto, style: const TextStyle(fontSize: 15, color: Colores.texto)),
            ),
          ],
        ),
      ),
    );
  }
}
