import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../api/modelos.dart';
import '../sesion/ambito.dart';
import '../sesion/controlador_sesion.dart';
import 'comunes.dart';

const _nombreRol = {'agente': 'Agente', 'revisor': 'Revisor', 'supervisor': 'Supervisor'};

class _Opcion {
  const _Opcion(this.texto, {this.abre, this.icono});
  final String texto;

  /// Pantalla que abre; sin pantalla, la opción se muestra deshabilitada (CONTRATO-HU-02 dec. 4).
  final Pantalla? abre;
  final String? icono;
}

class _Opciones {
  const _Opciones(this.principales, [this.enlace]);
  final List<_Opcion> principales;
  final _Opcion? enlace;
}

/// Opciones de cada rol (CONTRATO-HU-02 §3). Habilitadas las que ya tienen pantalla: placa
/// (HU-03, HU-04) y bitácora (HU-07). Rostro y "Mis verificaciones" llegan con HU-05 y HU-06.
const _opciones = {
  'agente': _Opciones(
    [_Opcion('Consultar placa', abre: Pantalla.placa, icono: '🚗'), _Opcion('Verificar rostro')],
    _Opcion('Mis verificaciones'),
  ),
  'revisor': _Opciones([_Opcion('Pendientes de revisión')]),
  'supervisor': _Opciones([_Opcion('Bitácora', abre: Pantalla.bitacora)]),
};

/// HOME-01 (agente) y los inicios del revisor y del supervisor. El rol sale de GET /v1/me.
class PantallaInicio extends StatelessWidget {
  const PantallaInicio({super.key, required this.perfil});

  final Perfil perfil;

  @override
  Widget build(BuildContext context) {
    final sesion = AmbitoSesion.leer(context);
    final opciones = _opciones[perfil.rol];
    final enlace = opciones?.enlace;
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colores.borde)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Hola, ${perfil.nombre}',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: Colores.texto,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Rol: ${_nombreRol[perfil.rol] ?? perfil.rol}',
                        style: const TextStyle(fontSize: 15, color: Colores.tenue),
                      ),
                    ],
                  ),
                ),
                SizedBox(
                  width: 96,
                  child: Boton(
                    texto: 'Salir',
                    variante: VarianteBoton.secundario,
                    alTocar: () => unawaited(sesion.salir()),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final o in opciones?.principales ?? const <_Opcion>[])
                    Boton(
                      texto: o.texto,
                      icono: o.icono,
                      variante: VarianteBoton.opcion,
                      deshabilitado: o.abre == null,
                      alTocar: o.abre == null ? null : () => sesion.mostrar(o.abre!),
                    ),
                  if (enlace != null)
                    Boton(
                      texto: enlace.texto,
                      variante: VarianteBoton.secundario,
                      deshabilitado: enlace.abre == null,
                      alTocar: enlace.abre == null ? null : () => sesion.mostrar(enlace.abre!),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
