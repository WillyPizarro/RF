# Contratos de fuentes

Aquí van los contratos OpenAPI 3.1 de cada fuente simulada (ADR-0006), uno por fuente:
`contratos/fuentes/<fuente>.yaml` (`placas`, `requisitorias-personas`, `galeria`).

Cada contrato documenta campos, códigos de error, ejemplos y tiempo de respuesta simulado. El
contenedor `simuladores` los implementa con datos sintéticos, y la API los consume mediante un
adaptador por fuente. Para reemplazar un simulador por la fuente real basta con otra
implementación del mismo contrato, sin cambiar la app.

En el Sprint 0 esta carpeta está vacía a propósito: los contratos llegan con HU-03, HU-05 y HU-08.
