import 'package:material_ui/material_ui.dart';

import 'comunes.dart';

/// ERR-01: respuesta 403 SIN_PERMISO de la API (CONTRATO-HU-02 §3; su prueba es de HU-03).
class PantallaSinPermiso extends StatelessWidget {
  const PantallaSinPermiso({super.key, required this.alVolver});

  final VoidCallback alVolver;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colores.fondo,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FranjaPrototipo(),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const ExcludeSemantics(
                    child: Text('⛔', textAlign: TextAlign.center, style: TextStyle(fontSize: 48)),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No tiene permiso para usar esta función.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colores.texto),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'El intento quedó registrado.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16, color: Colores.tenue),
                  ),
                  const SizedBox(height: 32),
                  Boton(texto: 'Volver al inicio', alTocar: alVolver),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
