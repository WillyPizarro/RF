/// Del texto que lee el OCR a la placa propuesta (CONTRATO-HU-04 §4, decisión 2). Mismo algoritmo
/// que `src/camara/placaLeida.ts` de la referencia Expo (CONTRATO-MIGRACION-FLUTTER §9).
///
/// El texto se pasa a mayúsculas y se separa en líneas. En cada línea se buscan candidatos que
/// cumplan `formato_placa.regex` (de GET /v1/motivos): primero el texto tal cual (la línea entera y
/// cada palabra) y después con el espacio o el punto entre dos grupos cambiado por un guion. Se
/// propone el primer candidato que cumpla. La app no adivina caracteres (O/0): si nada cumple, null.
String? proponerPlaca(String? texto, String regex) {
  if (texto == null || texto.isEmpty) return null;
  final RegExp patron;
  try {
    patron = RegExp(regex);
  } on FormatException {
    return null;
  }
  bool cumple(String candidato) => candidato.isNotEmpty && patron.hasMatch(candidato);

  for (final linea in texto.toUpperCase().split(RegExp(r'\r?\n'))) {
    final limpia = linea.trim();
    if (limpia.isEmpty) continue;
    final palabras = limpia.split(RegExp(r'\s+'));

    // 1. Tal cual: la línea entera y cada palabra, en orden.
    for (final candidato in [limpia, ...palabras]) {
      if (cumple(candidato)) return candidato;
    }

    // 2. Con el espacio o el punto entre dos grupos cambiado por un guion.
    final cambiados = <String>[];
    for (var i = 0; i < palabras.length; i += 1) {
      cambiados.add(palabras[i].replaceAll('.', '-'));
      if (i + 1 < palabras.length) cambiados.add('${palabras[i]}-${palabras[i + 1]}');
    }
    for (final candidato in cambiados) {
      if (cumple(candidato)) return candidato;
    }
  }
  return null;
}

/// La placa cumple `formato_placa.regex`. Una regex que Dart no entiende no bloquea: la API valida
/// igual (CONTRATO-HU-03 §2).
bool cumpleFormato(String placa, String regex) {
  try {
    return RegExp(regex).hasMatch(placa);
  } on FormatException {
    return true;
  }
}
