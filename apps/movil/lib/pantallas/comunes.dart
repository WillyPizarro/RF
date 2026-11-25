import 'package:material_ui/material_ui.dart';

/// Colores del prototipo (los mismos de la app Expo).
abstract final class Colores {
  static const fondo = Color(0xFFFFFFFF);

  /// Fondo de la franja "DATOS SINTÉTICOS · PROTOTIPO" y de la zona de la barra de estado.
  static const franja = Color(0xFF1B1F24);
  static const texto = Color(0xFF1B1F24);
  static const tenue = Color(0xFF5B6470);
  static const primario = Color(0xFF0B4F8A);
  static const borde = Color(0xFFC9D1DB);
  static const info = Color(0xFFE7F1FB);
  static const infoBorde = Color(0xFF7AA7D6);
  static const error = Color(0xFFFDECEC);
  static const errorBorde = Color(0xFFD9534F);
  static const advertencia = Color(0xFFFFF4DC);
  static const advertenciaBorde = Color(0xFFE0A526);
  static const neutro = Color(0xFFF1F3F5);
  static const neutroBorde = Color(0xFF9AA4AF);

  /// Gris azulado de PLA-08 (placa no registrada): neutro, distinto del gris de PLA-06.
  static const neutroAzul = Color(0xFFE8EEF4);
  static const neutroAzulBorde = Color(0xFF7D93AB);

  /// Rojo de PLA-05 (tiene requisitoria).
  static const alerta = Color(0xFFB42318);
  static const deshabilitado = Color(0xFFE3E7EC);
  static const textoDeshabilitado = Color(0xFF8A939E);
}

/// Franja fija de todas las pantallas (elemento aprobado por UX, 2026-11-18).
class FranjaPrototipo extends StatelessWidget {
  const FranjaPrototipo({super.key});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      header: true,
      child: Container(
        width: double.infinity,
        color: Colores.franja,
        padding: const EdgeInsets.symmetric(vertical: 6),
        alignment: Alignment.center,
        child: const Text(
          'DATOS SINTÉTICOS · PROTOTIPO',
          style: TextStyle(
            color: Color(0xFFFFD54F),
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }
}

enum VarianteBoton { primario, opcion, secundario }

/// Botón grande a todo el ancho, pensado para uso en la calle (HOME-01).
class Boton extends StatelessWidget {
  const Boton({
    super.key,
    required this.texto,
    this.alTocar,
    this.deshabilitado = false,
    this.variante = VarianteBoton.primario,
    this.icono,
  });

  final String texto;
  final VoidCallback? alTocar;
  final bool deshabilitado;
  final VarianteBoton variante;

  /// Ícono delante del texto, oculto para el lector de pantalla (que lee solo el texto).
  final String? icono;

  @override
  Widget build(BuildContext context) {
    final secundario = variante == VarianteBoton.secundario;
    final accion = deshabilitado ? null : alTocar;
    final colorTexto = deshabilitado
        ? Colores.textoDeshabilitado
        : (secundario ? Colores.primario : Colors.white);
    final contenido = Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icono != null)
          ExcludeSemantics(
            child: Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Text(icono!, style: const TextStyle(fontSize: 22)),
            ),
          ),
        Flexible(
          child: Text(
            texto,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: colorTexto,
              fontSize: secundario ? 14 : 18,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
    final forma = RoundedRectangleBorder(borderRadius: BorderRadius.circular(8));
    final boton = secundario
        ? OutlinedButton(
            onPressed: accion,
            style: OutlinedButton.styleFrom(
              minimumSize: const Size.fromHeight(48),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              shape: forma,
              side: BorderSide(color: deshabilitado ? Colores.deshabilitado : Colores.primario),
              backgroundColor: deshabilitado ? Colores.deshabilitado : Colors.transparent,
              disabledBackgroundColor: Colores.deshabilitado,
            ),
            child: contenido,
          )
        : ElevatedButton(
            onPressed: accion,
            style: ElevatedButton.styleFrom(
              minimumSize: const Size.fromHeight(56),
              padding: EdgeInsets.symmetric(
                horizontal: 16,
                vertical: variante == VarianteBoton.opcion ? 24 : 16,
              ),
              shape: forma,
              elevation: 0,
              backgroundColor: Colores.primario,
              disabledBackgroundColor: Colores.deshabilitado,
            ),
            child: contenido,
          );
    if (variante == VarianteBoton.opcion) {
      return Padding(padding: const EdgeInsets.only(bottom: 16), child: boton);
    }
    return boton;
  }
}

/// Botón de solo un símbolo (← ✕ 📷) con su etiqueta de accesibilidad.
class BotonIcono extends StatelessWidget {
  const BotonIcono({
    super.key,
    required this.etiqueta,
    required this.simbolo,
    required this.alTocar,
    this.estilo,
    this.decoracion,
    this.deshabilitado = false,
    this.tamano = 48,
  });

  final String etiqueta;
  final String simbolo;
  final VoidCallback alTocar;
  final TextStyle? estilo;
  final BoxDecoration? decoracion;
  final bool deshabilitado;
  final double tamano;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: etiqueta,
      button: true,
      enabled: !deshabilitado,
      excludeSemantics: true,
      onTap: deshabilitado ? null : alTocar,
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: deshabilitado ? null : alTocar,
          borderRadius: BorderRadius.circular(6),
          child: Container(
            constraints: BoxConstraints(minWidth: tamano, minHeight: tamano),
            alignment: Alignment.center,
            decoration: decoracion,
            child: Text(simbolo, style: estilo),
          ),
        ),
      ),
    );
  }
}

/// Barra superior de las pantallas internas: flecha atrás y título.
class Encabezado extends StatelessWidget {
  const Encabezado({super.key, required this.titulo, required this.alVolver});

  final String titulo;
  final VoidCallback alVolver;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Colores.borde)),
      ),
      child: Row(
        children: [
          BotonIcono(
            etiqueta: 'Atrás',
            simbolo: '←',
            alTocar: alVolver,
            estilo: const TextStyle(fontSize: 24, color: Colores.primario),
          ),
          Expanded(
            child: Semantics(
              header: true,
              child: Text(
                titulo,
                style: const TextStyle(
                  fontSize: 19,
                  fontWeight: FontWeight.w700,
                  color: Colores.texto,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Etiqueta visible de un campo. Queda fuera del árbol de accesibilidad: el campo lleva la misma
/// etiqueta (como `accessibilityLabelledBy` en Expo), así el lector no la lee dos veces.
class EtiquetaCampo extends StatelessWidget {
  const EtiquetaCampo(this.texto, {super.key, this.estilo});

  final String texto;
  final TextStyle? estilo;

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: Text(
        texto,
        style: estilo ?? const TextStyle(fontSize: 15, color: Colores.texto),
      ),
    );
  }
}

/// Campo de texto con su etiqueta de accesibilidad (CONTRATO-MIGRACION-FLUTTER §2).
class CampoTexto extends StatelessWidget {
  const CampoTexto({
    super.key,
    required this.etiqueta,
    required this.controlador,
    this.focusNode,
    this.ocultar = false,
    this.mayusculas = false,
    this.soloLectura = false,
    this.conError = false,
    this.pista,
    this.estilo,
    this.teclado,
    this.alEnviar,
    this.alCambiar,
  });

  final String etiqueta;
  final TextEditingController controlador;
  final FocusNode? focusNode;
  final bool ocultar;
  final bool mayusculas;
  final bool soloLectura;
  final bool conError;
  final String? pista;
  final TextStyle? estilo;
  final TextInputType? teclado;
  final VoidCallback? alEnviar;
  final ValueChanged<String>? alCambiar;

  @override
  Widget build(BuildContext context) {
    OutlineInputBorder borde(Color color, double ancho) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: color, width: ancho),
        );
    final normal = conError ? borde(Colores.errorBorde, 2) : borde(Colores.borde, 1);
    return Semantics(
      label: etiqueta,
      child: TextField(
        controller: controlador,
        focusNode: focusNode,
        obscureText: ocultar,
        readOnly: soloLectura,
        autocorrect: false,
        enableSuggestions: !ocultar && !mayusculas,
        textCapitalization: mayusculas ? TextCapitalization.characters : TextCapitalization.none,
        keyboardType: teclado,
        onSubmitted: alEnviar == null ? null : (_) => alEnviar!(),
        onChanged: alCambiar,
        style: estilo ?? const TextStyle(fontSize: 17, color: Colores.texto),
        decoration: InputDecoration(
          isDense: true,
          hintText: pista,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          enabledBorder: normal,
          border: normal,
          focusedBorder: conError ? borde(Colores.errorBorde, 2) : borde(Colores.primario, 2),
        ),
      ),
    );
  }
}

/// Indicador de espera con su etiqueta ("Ingresando" o "Cargando").
class Espera extends StatelessWidget {
  const Espera({super.key, this.etiqueta = 'Cargando', this.color, this.grande = false});

  final String etiqueta;
  final Color? color;
  final bool grande;

  @override
  Widget build(BuildContext context) {
    final indicador = CircularProgressIndicator(
      semanticsLabel: etiqueta,
      color: color ?? Colores.primario,
      strokeWidth: grande ? 4 : 3,
    );
    final lado = grande ? 40.0 : 28.0;
    return Center(child: SizedBox(width: lado, height: lado, child: indicador));
  }
}

String _dos(int n) => n.toString().padLeft(2, '0');

DateTime _local(String iso) => DateTime.parse(iso).toLocal();

/// dd/mm/aaaa hh:mm en hora local.
String fechaHora(String iso) {
  final f = _local(iso);
  return '${_dos(f.day)}/${_dos(f.month)}/${f.year} ${_dos(f.hour)}:${_dos(f.minute)}';
}

/// dd/mm hh:mm en hora local (tarjetas de BIT-01).
String fechaHoraCorta(String iso) {
  final f = _local(iso);
  return '${_dos(f.day)}/${_dos(f.month)} ${_dos(f.hour)}:${_dos(f.minute)}';
}

/// dd/mm/aaaa hh:mm:ss en hora local (BIT-02).
String fechaHoraCompleta(String iso) => '${fechaHora(iso)}:${_dos(_local(iso).second)}';

/// Mensaje de error de un campo (PLA-02, PLA-03).
class MensajeCampo extends StatelessWidget {
  const MensajeCampo(this.texto, {super.key});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const ExcludeSemantics(
              child: Padding(
                padding: EdgeInsets.only(right: 6),
                child: Text('⚠', style: TextStyle(color: Colores.errorBorde, fontSize: 15)),
              ),
            ),
            Expanded(
              child: Text(texto, style: const TextStyle(color: Colores.errorBorde, fontSize: 15)),
            ),
          ],
        ),
      ),
    );
  }
}
