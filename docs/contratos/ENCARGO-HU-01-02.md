# ENCARGO LEAD → TESTER y DEV — HU-01 + HU-02

**Documentos de trabajo:** `docs/contratos/CONTRATO-HU-01.md` **v1** y `docs/contratos/CONTRATO-HU-02.md` **v1**, aprobados por el humano el 2026-11-19. Son la única spec: lo que no dicen no se supone, se pregunta.
**Rama:** `hu-01`, creada desde `main` en `befd3d7`. El TESTER y el DEV trabajan en la misma rama, cada uno en sus rutas. Las dos HUs se construyen juntas y tienen un solo veredicto (CONTRATO-HU-02, decisión 1).
**Plazo:** construcción del 28-nov al 8-dic-2026, con veredicto antes del 10-dic. Si terminan antes, mejor.
**Pasa por UX:** sí. Pantallas AUTH-01 a AUTH-04, HOME-01, los inicios del revisor y del supervisor, y ERR-01. El UX revisa con capturas de Jest y del emulador, contra los wireframes.

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (las repiten los contratos en "Rutas de cada rol").
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]` y **sin** la línea `Co-Authored-By`. Sin push y sin merge.
3. No mires ni preguntes por el trabajo del otro rol. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`. La respuesta sale del contrato o se escala al humano; si cambia algo, llega como una versión nueva del contrato.
4. No toques `Empezar.txt` ni lo incluyas en commits.
5. Ninguna clave en el repositorio: las de los usuarios de prueba viven en `CLAVE_USUARIOS_PRUEBA`, en `infra/.env` (local, no versionado). Ninguna foto en el repositorio.
6. Reglas de negocio de `AGENTS.md`, en especial la 1 (la palabra prohibida) y la 7 (ningún error se convierte en un resultado negativo).
7. Arranque de referencia: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`. Usa siempre los dos archivos, para no recrear `simuladores` sin su montaje (lección del veredicto de HU-08).
8. El puerto 80 de esta máquina lo ocupa `http.sys` de Windows, así que lo que pase por el proxy puede quedar `NO VERIFICADO`. Lo que se pueda probar dentro de la red interna (`http://api:8000`) se prueba ahí.

## Qué entrega cada uno

- **TESTER:** pruebas automatizadas de cada caso de los dos contratos: pytest para la API y la tabla `bitacora`, y Jest con RNTL para las pantallas. Incluye la prueba del `422 SOLICITUD_INVALIDA` que quedó pendiente del Sprint 0 (`docs/contratos/PENDIENTES.md`). Informe en `informes/TESTER-HU-01-02.md`, con cada caso en verde, rojo o `NO VERIFICADO`, con evidencia.
- **DEV:** la implementación que cumple los dos contratos, con el OpenAPI y los tipos de la app regenerados e `infra/.env.example` al día. Informe en `informes/DEV-HU-01-02.md`: qué hizo, dónde, cómo se arranca y cómo se cargan los usuarios. Además, **capturas para el UX** de cada pantalla (de Jest o del emulador), guardadas fuera del repositorio. En el informe indica la ruta local donde quedaron.

## Orden del cierre

1. `ENTREGA DEV` con el informe y las capturas.
2. El LEAD le pasa las capturas al UX para su revisión. Si hay correcciones, vuelven al DEV como una M-n.
3. Con la aprobación del UX, el LEAD da la orden (en una M-n) de la **suite completa, una sola vez**, sobre el commit definitivo.
4. `ENTREGA TESTER` con el informe final.

Mientras tanto, el TESTER puede escribir y correr sus pruebas contra lo que haya; la corrida que cuenta es la del punto 3.

## Aviso de vuelta

Al terminar: `herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-HU-01-02.md"`.

## Instrucciones del ciclo (M-n)

Aquí se agregan las aclaraciones durante el ciclo (M-1, M-2, …). Cada una dice qué reemplaza. Si recibes "lee M-n del encargo", es esta sección.

### M-1 (2026-11-19) — Contratos v2

**Reemplaza** la versión del encabezado: los documentos de trabajo ahora son CONTRATO-HU-01 **v2** y CONTRATO-HU-02 **v2**, aprobados por el humano. Los cambios están en sus changelogs: la nueva §4 bis de HU-01 (montaje en `apps/movil/App.tsx` sin expo-router, `fetch` global con `EXPO_PUBLIC_API_URL`, `testID="app-raiz"`, `BackHandler`), AUTH-03 observable desde afuera y qué cuenta como interacción.

- **DEV:** cumple la §4 bis.
- **TESTER:** monta `App.tsx` y verifica AUTH-03 como dice la v2.
