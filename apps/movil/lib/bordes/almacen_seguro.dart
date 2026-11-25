/// Almacenamiento seguro del dispositivo (ADR-0013). Real: flutter_secure_storage.
///
/// La app guarda aquí solo los tokens de la sesión. Nada más se guarda en el dispositivo.
abstract class AlmacenSeguro {
  Future<String?> leer(String clave);
  Future<void> escribir(String clave, String valor);
  Future<void> borrar(String clave);

  /// Todo lo guardado. Las pruebas lo usan para comprobar que queda vacío.
  Future<Map<String, String>> leerTodo();
}
