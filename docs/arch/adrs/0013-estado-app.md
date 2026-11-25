# ADR 0013: Estado de la app en memoria con TanStack Query y sesión en SecureStore

## Estado

Aceptado (2026-11-18). **Precisado por el [ADR-0017](0017-app-movil-flutter-mlkit.md) (2026-11-24):** con la app en Flutter, el estado en memoria se lleva con Riverpod o `ChangeNotifier` y el token con `flutter_secure_storage`. Las reglas (nada en disco salvo el token, limpieza al cerrar sesión) no cambian.

## Contexto

- ADR-0010: la app no guarda consultas, capturas ni resultados en el dispositivo. HU-01 E3: al vencer la sesión, "ninguna consulta previa queda visible en pantalla".
- HU-06 E3: el agente ve "Pendiente de revisión" hasta que el revisor decide, así que la app tiene que enterarse del cambio de estado.
- ADR-0007: los tipos de la app se generan desde el OpenAPI.

## Decisión

- **Estado del servidor** (consultas, revisiones, bitácora): **TanStack Query** con la caché **solo en memoria**, sin ningún persistor.
- **Sesión:** el token de acceso y el de renovación se guardan en `expo-secure-store`. El perfil y el rol viven en un store mínimo en memoria (Zustand).
- **Cierre de sesión, sesión vencida o paso a segundo plano por inactividad:** se limpian la caché de TanStack Query, el store y SecureStore, y la app vuelve a la pantalla de login.
- **Estado de la revisión:** la app sondea `GET /v1/consultas/{id}` cada 10 s mientras la pantalla de una consulta pendiente esté abierta. No hay notificaciones push en el MVP.

## Alternativas consideradas

- **Solo estado de React (useState, Context, fetch).** No agregaba dependencias. Se descartó porque obliga a reescribir la caché, los estados de carga y el sondeo, y es más fácil olvidar limpiar algo al cerrar sesión.

## Consecuencias

- Al cerrar o vencer la sesión no queda ningún resultado en el dispositivo, lo que se puede verificar en las pruebas de seguridad (MobSF y una revisión del almacenamiento).
- **Costo:** sondear cada 10 s genera tráfico y carga en la API mientras haya consultas pendientes abiertas, y el agente no se entera de la decisión si sale de esa pantalla. Las notificaciones push quedan para producción.
- **Costo:** se agregan dos dependencias (TanStack Query y Zustand) que hay que mantener.
