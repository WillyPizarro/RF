# Contratos de fuentes

Contratos OpenAPI 3.1 de cada fuente simulada (ADR-0006, contrato HU-08 v1), uno por fuente:

| Archivo | Rutas | Usada por |
|---|---|---|
| `placas.yaml` | `GET /placas/{placa}` | HU-03 |
| `requisitorias-personas.yaml` | `GET /personas/{persona_id}`, `GET /personas/{persona_id}/fotos/{foto_id}` | HU-05, HU-06 |
| `galeria.yaml` | `GET /galeria` | HU-05 |

Cada contrato documenta campos, códigos de error, ejemplos y tiempo de respuesta simulado
(`x-tiempo-respuesta-ms`). El contenedor `simuladores` los implementa con datos sintéticos, y la
API los consume con un adaptador por fuente, cuya URL se configura con `FUENTE_PLACAS_URL`,
`FUENTE_REQUISITORIAS_URL` y `FUENTE_GALERIA_URL` (respaldo: `SIMULADORES_URL`). Para reemplazar
un simulador por la fuente real basta con otra implementación del mismo contrato, sin cambiar la
app. Por ejemplo, un mock generado solo desde el contrato:

```bash
npx @stoplight/prism-cli mock contratos/fuentes/placas.yaml
```

La ruta de control de los modos de falla del simulador (`/control/modos`) no es parte de estos
contratos: una fuente real no la tiene.
