# Technical Design Document: Movil Buscador (MININTER)

**Tipo de proyecto:** Greenfield. No existe código previo; el MININTER "no tiene nada hecho" (`Empezar.txt`).
**Design.md disponible:** No. El modelo de datos se derivó del `PRD.md` y de las HU-01 a HU-08 (`docs/hus/`). Cuando UX entregue el prototipo navegable, hay que revisar si sus pantallas revelan campos que falten.
**Insumos:** `PRD.md`, `docs/hus/README.md`, HU-01 a HU-08, el análisis de factibilidad (doc "Movil Buscador — Análisis de factibilidad") y las skills `especialista-biometria` y `datos-personales-peru`.
**Rol / fecha:** ARCH, 2026-11-18. Cada decisión fue respondida por el usuario.
**Estado:** aprobado por el usuario el 2026-11-18. Los diagramas C4 y de secuencia se agregaron el 2026-11-18 (sección Diagramas).

## Resumen

Prototipo funcional móvil para que el personal autorizado del MININTER verifique si un vehículo (por su placa) o una persona (por su rostro) tiene requisitoria, usando **solo datos sintéticos y simuladores** (PRD › Enfoque MVP). Se construyen en versión mínima los cinco módulos del encargo:

- seguridad y acceso;
- consulta de placas (manual y por OCR);
- verificación facial contra una lista acotada, con revisión humana obligatoria;
- bitácora inalterable con motivo;
- servicios con contrato respaldados por simuladores reemplazables.

Las políticas de seguridad avanzadas se documentan, pero no se construyen. El plazo total es de 30 a 40 días.

## Arquitectura de componentes

```
┌──────────────────────────┐
│ App móvil (Expo dev build│   OCR + calidad facial en el dispositivo (ML Kit)
│ Android, TypeScript)     │   Nada en disco salvo el token (SecureStore)
└────────────┬─────────────┘
             │ HTTPS + JWT  (REST /v1, contrato OpenAPI)
┌────────────▼─────────────────────────────── VPS (docker compose) ─┐
│ proxy (Caddy, TLS)                                                 │
│   └─► api (FastAPI) ─────────────────────────────┐                 │
│        ├─ auth: login/refresh/logout → Supabase Auth                │
│        ├─ control de rol en cada request                           │
│        ├─ MotorBiometrico (YuNet + SFace, OpenCV)                  │
│        ├─ adaptadores de fuente ──► simuladores (FastAPI, red      │
│        │                            interna, sin puerto público)   │
│        └─ bitácora (fail-closed)                                   │
└────────────┬───────────────────────────────────────────────────────┘
             │ SQL (rol api_app) / Auth API
┌────────────▼─────────────┐
│ Supabase (nube): Auth +  │
│ Postgres                 │
└──────────────────────────┘
```

| Componente | Responsabilidad | ADR |
|---|---|---|
| App móvil | Captura, OCR, calidad facial, pantallas por rol (agente, revisor, supervisor). Solo habla con la API. | 0001, 0002, 0010, 0013 |
| API (FastAPI) | Único punto de entrada: sesión, roles, consultas, motor biométrico, adaptadores de fuente, bitácora, borrado de capturas. | 0001, 0003, 0004, 0005, 0007, 0012, 0014 |
| Simuladores (FastAPI) | Placas, requisitorias de personas y galería, con contrato OpenAPI y modos de falla. | 0006 |
| Supabase | Auth (emisión de JWT) y Postgres (datos de la API y bitácora). | 0001, 0009, 0012 |
| Proxy (Caddy) | Terminación TLS; único servicio expuesto. | 0009 |

### Diagramas

Diagramas HTML interactivos generados con `archify`. Sus fuentes JSON están en `diagramas/fuentes/`.

| Diagrama | Qué muestra |
|---|---|
| [C4 — Contexto](diagramas/c4-contexto.html) | Los tres roles, el sistema, Supabase, las fuentes simuladas y las fuentes reales (fuera del MVP) |
| [C4 — Contenedores](diagramas/c4-contenedores.html) | App, Caddy, API con el motor biométrico, simuladores en la red interna, y Supabase Auth y Postgres |
| [Secuencia — Consulta de placa](diagramas/seq-consulta-placa.html) | HU-03 y HU-04: OCR, validación, fuente con timeout, registro fail-closed y camino de error |
| [Secuencia — Verificación facial con revisión humana](diagramas/seq-verificacion-facial.html) | HU-05 y HU-06: calidad, comparación, retención cifrada del candidato, decisión con motivo y borrado |
| [Secuencia — Vencimiento a 24 h](diagramas/seq-vencimiento-24h.html) | ADR-0008 / PA #23: borrado periódico, revisión vencida y "No concluyente" para el agente |

## Decisiones de arquitectura

| # | Decisión | Estado |
|---|---|---|
| [ADR-0001](adrs/0001-componentes-api-unica.md) | API propia como único punto de entrada de la app | Aceptado |
| [ADR-0002](adrs/0002-stack-movil-expo-mlkit.md) | App con Expo (dev build) y ML Kit en el dispositivo | Aceptado |
| [ADR-0003](adrs/0003-autenticacion-roles.md) | Login vía API, tres roles, usuarios por script de carga | Aceptado |
| [ADR-0004](adrs/0004-verificacion-facial.md) | Lista acotada, motor dentro de la API, umbrales calibrados | Aceptado |
| [ADR-0005](adrs/0005-bitacora.md) | Bitácora de solo inserción, sin resultado sin registro, consultable en la app | Aceptado |
| [ADR-0006](adrs/0006-simuladores-fuentes.md) | Simuladores como servicio HTTP con contrato OpenAPI | Aceptado |
| [ADR-0007](adrs/0007-contrato-app-api.md) | REST versionado con OpenAPI generado | Aceptado |
| [ADR-0008](adrs/0008-retencion-datos-personales.md) | Retención de la captura, galería con consentimiento, retención de la bitácora | Aceptado |
| [ADR-0009](adrs/0009-despliegue.md) | VPS con docker compose y Supabase en la nube | Aceptado |
| [ADR-0010](adrs/0010-conectividad-plataforma.md) | Solo en línea, Android como referencia | Aceptado |
| [ADR-0011](adrs/0011-umbrales-provisionales.md) | Valores provisionales de sesión, desempeño, OCR y motivo | Aceptado (provisional) |
| [ADR-0012](adrs/0012-acceso-datos-migraciones.md) | SQLAlchemy 2 async y Alembic | Aceptado |
| [ADR-0013](adrs/0013-estado-app.md) | Estado en memoria (TanStack Query) y sesión en SecureStore | Aceptado |
| [ADR-0014](adrs/0014-resiliencia-errores.md) | Timeout, un reintento en lecturas, errores controlados | Aceptado |
| [ADR-0015](adrs/0015-foto-varias-personas-rostro-elegido.md) | Foto con varias personas: se compara solo el rostro elegido, recortado en el dispositivo (C6) | **Propuesto** |
| [ADR-0016](adrs/0016-ubicacion-aviso-105-simulado.md) | Ubicación del dispositivo para el aviso simulado al 105 (PA #32 y #34) | **Propuesto** |

## Modelos biométricos fijados

Verificado el 2026-11-18 (encargo del LEAD, Sprint 0). El detalle de la prueba de la API está en el [ADR-0004 › Versiones y modelos fijados](adrs/0004-verificacion-facial.md#versiones-y-modelos-fijados-sprint-0-2026-11-18).

| Pieza | Versión / archivo | Licencia | SHA-256 |
|---|---|---|---|
| OpenCV | `opencv-python-headless==5.1.0.95` | — | — |
| YuNet (detección) | `face_detection_yunet_2026may.onnx` | **MIT** (LICENSE de `models/face_detection_yunet/`) | `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0` |
| SFace (reconocimiento) | `face_recognition_sface_2021dec.onnx` | **Apache 2.0** (LICENSE de `models/face_recognition_sface/`) | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |

Fuente: opencv_zoo, rama `main`, commit `48b10fa505aeb51fbd127fc60a5c660040e823b7`. Las dos licencias permiten el uso en un servicio contratado (regla de negocio 6); ninguno de los modelos es de InsightFace. La API de 5.1 es compatible con lo que asume el ADR-0004, salvo el nombre de la constante en Python: se usa `cv.FaceRecognizerSF_FR_COSINE`.

## Modelo de datos

Base de datos de la API (Postgres en Supabase). El esquema `auth` pertenece a Supabase y no se modifica. Todas las tablas de negocio llevan `es_sintetico boolean not null default true`.

| Entidad | Campos principales | Notas |
|---|---|---|
| `usuario_perfil` | `id` (= `auth.users.id`), `nombre`, `rol` (`agente`·`revisor`·`supervisor`), `activo` | Lo crea el script de carga (ADR-0003). |
| `control_acceso` | `usuario_id`, `intentos_fallidos`, `bloqueado_hasta` | Bloqueo por intentos (ADR-0003, ADR-0011). |
| `motivo_catalogo` | `codigo`, `descripcion`, `activo` | Catálogo más "Otro" (ADR-0011). |
| `consulta` | `id`, `tipo` (`placa`·`rostro`), `agente_id`, `motivo_codigo`, `motivo_texto`, `placa` (nula si es de rostro), `resultado` (placa: `con_requisitoria`·`sin_requisitoria`·`error`; rostro: banda de ADR-0004 o `error`), `estado` (`completada`·`pendiente_revision`·`revisada`·`vencida`·`error`), `version_modelo`, `version_umbral`, `creada_en` | Una fila por consulta. Nunca guarda la imagen. |
| `candidato` | `consulta_id`, `persona_ref_id` (id en el simulador), `score`, `orden` (1–3) | Como máximo 3 por consulta (ADR-0004). El score no se expone al agente. |
| `revision` | `id`, `consulta_id`, `estado` (`pendiente`·`decidida`·`vencida`), `revisor_id`, `decision` (`confirmar`·`descartar`·`no_concluyente`), `motivo_decision`, `decidida_en`, `vence_en` | Una por consulta con resultado `candidato` (HU-06). |
| `captura_pendiente` | `id`, `consulta_id`, `imagen_cifrada` (bytea, AES-GCM), `nonce`, `expira_en` | Solo existe para candidatos y se borra al decidir o a las 24 h (ADR-0008). Se borra físicamente; no es parte de la bitácora. |
| `embedding_galeria` | `persona_ref_id`, `version_galeria`, `version_modelo`, `embedding` | Caché que se recalcula si cambia la versión de la galería o del modelo (ADR-0004, ADR-0006). |
| `config_umbral` | `version`, `umbral_alto`, `umbral_bajo`, `modelo`, `hash_modelo`, `fecha`, `origen` (enlace a la evaluación) | Hace que cada umbral quede trazable (ADR-0004). |
| `bitacora` | `id`, `ocurrido_en` (UTC, del servidor), `usuario_id`, `rol`, `tipo_evento`, `motivo`, `parametros` (placa; nunca imagen), `resultado`, `score`, `version_modelo`, `version_umbral`, `captura_id`, `consulta_id`, `codigo_error`, `id_traza`, `es_sintetico` | Solo inserción: permisos más trigger (ADR-0005). |

Tipos de evento de la bitácora: `LOGIN_OK`, `LOGIN_FALLIDO`, `CUENTA_BLOQUEADA`, `LOGOUT`, `SESION_VENCIDA`, `ACCESO_DENEGADO`, `CONSULTA_PLACA`, `CONSULTA_ROSTRO`, `CAPTURA_RECHAZADA`, `DECISION_REVISION`, `REVISION_VENCIDA`, `CAPTURA_ELIMINADA`, `ERROR_FUENTE`, `CONSULTA_BITACORA`.

Base de datos de los simuladores (esquema propio, ADR-0006): `sim_vehiculo` (placa, marca, modelo, color, requisitoria vigente, tipo), `sim_persona` (id, nombres y documento sintéticos, requisitoria, referencia a la foto cifrada) y `sim_galeria` (versión y lista de personas). Los campos son provisionales hasta conocer las fuentes reales (PA #6).

## Protección de datos personales

> Esta sección organiza el trabajo documental; **no es asesoría legal**. Las citas a la Ley N.º 29733 y su reglamento son **a validar** por el área legal del MININTER; no se consultó la fuente oficial.

**Declaración del MVP:** el prototipo usa solo datos sintéticos, salvo las fotos de integrantes del equipo con consentimiento firmado ampliado (ADR-0008). No hay titulares reales de la población ni conexión a fuentes reales.

### Matriz de tratamiento

| Dato | Categoría | Finalidad | Base legal (a validar) | Origen | Dónde se guarda | Retención (MVP) | Quién accede |
|---|---|---|---|---|---|---|---|
| Captura facial (no candidato) | Sensible (biometría) | Comparar contra la lista acotada | Producción: función de la entidad, que confirma Legal. MVP: consentimiento | Cámara del celular | Solo en la memoria de la API | Se descarta al terminar la solicitud | Nadie |
| Captura facial (candidato) | Sensible | Revisión humana (HU-06) | Ídem | Cámara del celular | `captura_pendiente`, cifrada | Hasta la decisión o 24 h | Revisor |
| Fotos de la galería | Sensible | Referencia de comparación | Consentimiento firmado ampliado | Equipo del proveedor | Almacenamiento del simulador, cifrado | Hasta el cierre y el acta de eliminación | API (motor) y revisor (visualización) |
| Embeddings de la galería | Sensible (derivado biométrico) | Comparación | Ídem | Calculados por la API | `embedding_galeria` | Hasta el cierre | API |
| Placa consultada | Identificativo indirecto | Verificar requisitoria | Función de la entidad | Ingreso manual u OCR | `consulta`, `bitacora` | Todo el proyecto, luego se borra el ambiente | Agente (las propias), supervisor |
| Imagen de la placa | Identificativo indirecto | OCR | — | Cámara | No se guarda: se procesa en el dispositivo | — | Nadie |
| Datos de la persona o vehículo requisitoriado | Personal, vinculado a requisitoria | Mostrar un resultado controlado | Función de la entidad | Simulador (sintético) | Simulador | Todo el proyecto | Agente y revisor (vista mínima, PA #15) |
| Credenciales y perfil del usuario | Identificativo | Autenticación y rol | Relación laboral (a validar) | Script de carga | Supabase Auth, `usuario_perfil` | Todo el proyecto | API |
| Bitácora | Técnico más personal | Trazabilidad y auditoría | Función de la entidad | API | `bitacora` | Todo el proyecto, luego se borra el ambiente; en producción, PA #16 | Supervisor |

### Controles: implementados en el MVP frente a documentados para producción

| Control | MVP (implementado) | Producción (documentado) |
|---|---|---|
| Autenticación y roles | Usuario y clave vía API, 3 roles, bloqueo por intentos, sesión de 10 min | Identidad institucional (OIDC), MFA, administración de usuarios |
| Bitácora | Solo inserción (permisos y trigger), con motivo, fail-closed | Hash encadenado o firma, sellado de tiempo, retención legal |
| Cifrado en tránsito | HTTPS (Caddy) | Certificados gestionados por la entidad, mTLS hacia las fuentes |
| Cifrado en reposo | Captura pendiente y galería con AES-GCM a nivel de aplicación; cifrado del proveedor de nube | Gestión de llaves de la entidad (KMS o HSM) |
| Minimización | Captura de no candidato sin persistencia; placa leída en el dispositivo; score oculto al agente | Ídem más revisión periódica |
| Dispositivo | Nada en disco salvo el token; limpieza al cerrar sesión | MDM y borrado remoto |
| Biometría | Lista acotada, máximo 3 candidatos, revisión humana, bandas con umbral documentado | Prueba de vida, evaluación independiente con datos autorizados |
| Evaluación de impacto | Borrador (pendiente) | Evaluación formal aprobada |
| Registro del banco de datos | No aplica (datos sintéticos) | Inscripción ante la ANPD si corresponde (a validar) |
| Derechos ARCO | No hay titulares reales | Procedimiento de atención definido |

### Brechas para producción (resumen)

1. Base legal del tratamiento biométrico y de la consulta de requisitorias, confirmada por el área legal.
2. Evaluación de impacto formal, con la retención de capturas de candidatos como riesgo principal.
3. Integración con fuentes reales y convenios (PA #6), incluida la galería biométrica real.
4. Identidad institucional y MFA; administración de usuarios.
5. Bitácora firmada y sellada; política de retención legal (PA #16).
6. Prueba de vida y anti-suplantación; evaluación biométrica con datos representativos de la población.
7. MDM; modo sin conexión (si PA #11 lo exige); iOS (si PA #12 lo exige).
8. Residencia de datos (Postgres fuera del Perú en el MVP); llaves gestionadas por la entidad.
9. Circuit breaker y monitoreo para fuentes reales; notificaciones push.

## Criterios de aceptación por flujo

Los valores numéricos vienen de los ADR-0004 y ADR-0011 y son provisionales hasta que se responda el PA #4.

### Sesión y acceso (HU-01, HU-02)

- [ ] `POST /v1/auth/login` con credenciales válidas devuelve un token y registra `LOGIN_OK` en la bitácora.
- [ ] Credenciales inválidas devuelven un mensaje único ("Usuario o clave incorrectos") que no distingue cuál falló, y registran `LOGIN_FALLIDO`.
- [ ] El 5.º intento fallido consecutivo bloquea la cuenta 15 min (`CUENTA_BLOQUEADA`). Durante el bloqueo, incluso la clave correcta es rechazada.
- [ ] Tras 10 min sin actividad, la app vuelve al login y la caché, el store y SecureStore quedan vacíos. Se verifica inspeccionando el almacenamiento.
- [ ] Un token vencido o con una firma inválida recibe 401.
- [ ] Cada endpoint de otro rol responde 403 con cada uno de los tres roles (matriz completa) y registra `ACCESO_DENEGADO`.
- [ ] El menú de la app muestra solo las opciones del rol que devuelve `GET /v1/me`.
- [ ] La clave no aparece en ningún log de la API ni del proxy.

### Consulta de placa (HU-03, HU-04)

- [ ] Una placa sintética con requisitoria devuelve `con_requisitoria`, y una sin requisitoria devuelve `sin_requisitoria`. Ambas quedan en la bitácora con usuario, fecha y hora, motivo y resultado.
- [ ] Sin motivo, o con "Otro" de menos de 10 caracteres, la API responde `MOTIVO_REQUERIDO` y no consulta la fuente (también si se llama a la API directamente).
- [ ] Una placa que no cumple la expresión regular configurada responde `PLACA_FORMATO_INVALIDO` y el mensaje muestra el formato esperado.
- [ ] Si el simulador está en modo timeout o 500, la respuesta es `FUENTE_NO_DISPONIBLE` y nunca `sin_requisitoria`; queda `ERROR_FUENTE` en la bitácora; hay como máximo 1 reintento.
- [ ] El OCR deja el texto en un campo editable y no se envía ninguna consulta sin la confirmación del usuario.
- [ ] Sin permiso de cámara, la app ofrece el ingreso manual.
- [ ] No queda ninguna imagen de placa en el dispositivo ni en el servidor.
- [ ] OCR: ≥ 90 % de lecturas exactas en un set de ≥ 100 imágenes de día con el celular de referencia; la noche se reporta.
- [ ] Desempeño: p95 ≤ 2 s con 20 usuarios concurrentes y error < 1 %.

### Verificación facial (HU-05)

- [ ] Una captura con 0 o ≥ 2 rostros, de perfil, con los ojos cerrados, pequeña o borrosa se rechaza en el dispositivo con su motivo y no se envía.
- [ ] Si la API recibe una imagen que no pasa la calidad del servidor (YuNet distinto de 1 rostro, nitidez), responde `captura_rechazada` con su motivo y no compara.
- [ ] Con un score ≥ umbral alto, la respuesta es `candidato` con como máximo 3 candidatos, y la app muestra "Posible coincidencia — requiere revisión".
- [ ] En la banda intermedia la app muestra "No concluyente — verifique por otros medios", y por debajo del umbral bajo, "Sin coincidencia en la lista consultada".
- [ ] La cadena "identificado" no aparece en el OpenAPI, la app, la bitácora ni los mensajes de error (búsqueda automatizada en el repositorio y prueba de UI).
- [ ] El score no está en la respuesta para el agente, pero sí en la bitácora, con `version_modelo` y `version_umbral`.
- [ ] Con un resultado distinto de candidato no queda ninguna fila en `captura_pendiente`; con candidato queda una fila cifrada.
- [ ] Umbrales: el alto cumple FMR ≤ 0,1 % y el bajo FNMR ≤ 5 % en el set de calibración; la evaluación los reporta con la regla de 3 y por subgrupo.
- [ ] Desempeño: p95 ≤ 5 s con 20 usuarios concurrentes.

### Revisión humana (HU-06)

- [ ] El revisor ve la cola de revisiones `pendiente`, y en cada una la captura y la referencia lado a lado más el motivo original.
- [ ] Decidir sin motivo responde `MOTIVO_REQUERIDO` y la decisión no se guarda.
- [ ] Al decidir, la bitácora registra `DECISION_REVISION` (revisor, fecha y hora, decisión, motivo), la captura se borra y queda `CAPTURA_ELIMINADA`.
- [ ] Mientras la revisión está pendiente, el agente ve "Pendiente de revisión" y no se dispara ninguna alerta ni acción.
- [ ] A las 24 h sin decisión, la revisión pasa a `vencida`, la captura no existe y el agente ve "No concluyente" (provisional, PA #23).
- [ ] Un agente no puede decidir sobre su propia consulta (403).

### Bitácora (HU-07)

- [ ] `UPDATE`, `DELETE` y `TRUNCATE` sobre `bitacora` fallan con `api_app` y con el rol dueño de la tabla (prueba automatizada sobre una base recién migrada).
- [ ] Si se simula un fallo de escritura en la bitácora, la consulta no devuelve su resultado (fail-closed).
- [ ] Cada tipo de evento listado en el modelo de datos se genera en al menos una prueba.
- [ ] El supervisor filtra por usuario, rango de fechas, tipo y resultado, con paginación. Agente y revisor reciben 403.
- [ ] Ningún registro contiene una imagen ni una clave.

### Servicios y simuladores (HU-08)

- [ ] La app no tiene la URL del simulador y el simulador no publica ningún puerto (se verifica en el compose y con un escaneo).
- [ ] Al apuntar la API a una segunda implementación del contrato (por ejemplo, un mock de Prism), las pruebas funcionales de la app pasan sin cambios.
- [ ] Una respuesta fuera de contrato produce `FUENTE_RESPUESTA_INVALIDA`, registrada en la bitácora.
- [ ] Los contratos `contratos/fuentes/*.yaml` y `contratos/api/openapi.json` están versionados y coinciden con lo desplegado.

### Despliegue y entrega

- [ ] `docker compose up` sobre un VPS limpio, más las migraciones y los scripts de carga, deja el sistema operativo siguiendo solo el manual.
- [ ] Solo los puertos 80 y 443 están expuestos; no hay secretos en el repositorio (escaneo de secretos en CI).
- [ ] Al cierre existe un acta de eliminación del ambiente y de las fotos de la galería.

## Riesgos técnicos abiertos

- **Aceptación de la propuesta (PA #8, #17):** todo el diseño asume infraestructura del proveedor, simuladores y stack propio. Si se rechaza, hay que volver a abrir los ADR-0006, ADR-0008 y ADR-0009.
- **Tipo de comparación (PA #7):** si el MININTER exige 1:1, hay que volver a abrir el ADR-0004 y HU-05.
- **Revisor (PA #2):** si es el mismo agente, se pierde la separación de funciones (ADR-0003).
- **Capturas de candidatos en reposo hasta 24 h** en la nube, fuera del Perú: es el riesgo principal de la evaluación de impacto (ADR-0008, ADR-0009).
- **Consentimiento ampliado** para las fotos del equipo: debe estar firmado antes del día 6, o la prueba biométrica temprana se retrasa.
- **Datos biométricos poco representativos** (unas 20 personas del equipo): la evaluación no se puede extrapolar a producción; se reporta por subgrupo y con la regla de 3.
- ~~Licencias de YuNet y SFace sin verificar~~: **verificadas el 2026-11-18** (ver "Modelos biométricos fijados"). La prueba de la API en la imagen Linux del contenedor `api` es un requisito del contrato de HU-05 (LEAD).
- **Expresión regular de placa** no verificada contra la normativa (PA #20).
- **Contratos de las fuentes** diseñados sin conocer las reales (PA #6): pueden requerir reescribir los adaptadores.
- **Planes de terceros:** Supabase gratis puede pausarse en la semana de validación; conviene evaluar un mes del plan Pro.
- **Diagramas:** pasaron todas las verificaciones de `archify`, incluida la revisión automática en el navegador (el usuario la ejecutó desde su PowerShell el 2026-11-18).

### Estado de los conflictos y puntos abiertos encargados al ARCH

| Ítem | Cómo queda en el diseño | ¿Cerrado? |
|---|---|---|
| C1 Administración de roles | Script de carga, 3 roles, sin pantalla (ADR-0003) | Para el MVP sí; falta confirmar el PA #3 |
| C3 Simuladores frente a integración real | Contratos OpenAPI y adaptadores reemplazables (ADR-0006) | Para el MVP sí; falta el PA #17 por escrito |
| C4 Sin umbrales medibles | Valores provisionales (ADR-0004, ADR-0011) | Provisional; falta el PA #4 |
| PA #4 | ADR-0004 y ADR-0011 | Provisional |
| PA #6 | Tres fuentes simuladas con campos provisionales (ADR-0006) | Abierto |
| PA #7 | Lista acotada, máximo 3 candidatos (ADR-0004) | Decisión de diseño; falta confirmar con el MININTER |
| PA #8 | VPS del proveedor y entrega con compose (ADR-0009) | Falta la aceptación |
| PA #11 | Solo en línea (ADR-0010) | Decisión de diseño; falta confirmar |
| PA #12 | Android de referencia (ADR-0010) | Decisión de diseño; falta confirmar |
| PA #16 | MVP: todo el proyecto y luego se borra; producción: Legal (ADR-0008) | Abierto para producción |
| PA #17 | Supuesto de todo el diseño | Abierto (bloqueante) |
