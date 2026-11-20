/**
 * Del texto que lee el OCR a la placa propuesta (CONTRATO-HU-04 §4, decision 2).
 *
 * El texto se pasa a mayusculas y se separa en lineas. En cada linea se buscan candidatos que
 * cumplan `formato_placa.regex` (de GET /v1/motivos): primero el texto tal cual (la linea entera y
 * cada palabra) y despues con el espacio o el punto entre dos grupos cambiado por un guion. Se
 * propone el primer candidato que cumpla. La app no adivina caracteres (O/0): si nada cumple, null.
 */
export function proponerPlaca(texto: string | null | undefined, regex: string): string | null {
  if (!texto) return null;
  let patron: RegExp;
  try {
    patron = new RegExp(regex);
  } catch {
    return null;
  }
  const cumple = (candidato: string) => candidato.length > 0 && patron.test(candidato);

  for (const linea of texto.toUpperCase().split(/\r?\n/)) {
    const limpia = linea.trim();
    if (!limpia) continue;
    const palabras = limpia.split(/\s+/);

    // 1. Tal cual: la linea entera y cada palabra, en orden.
    const talCual = [limpia, ...palabras];
    const directo = talCual.find(cumple);
    if (directo) return directo;

    // 2. Con el espacio o el punto entre dos grupos cambiado por un guion.
    const cambiados: string[] = [];
    for (let i = 0; i < palabras.length; i += 1) {
      cambiados.push(palabras[i].replace(/\./g, '-'));
      if (i + 1 < palabras.length) cambiados.push(`${palabras[i]}-${palabras[i + 1]}`);
    }
    const cambiado = cambiados.find(cumple);
    if (cambiado) return cambiado;
  }
  return null;
}
