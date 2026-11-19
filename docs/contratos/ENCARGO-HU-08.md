# ENCARGO LEAD → TESTER y DEV — HU-08

**Documento de trabajo:** `docs/contratos/CONTRATO-HU-08.md`, **v1 (aprobado el 2026-11-19)**. Es la única spec: lo que no dice, no se supone; se pregunta.
**Rama:** `hu-08` (desde `main` 2ef0829). TESTER y DEV trabajan en la misma rama, cada uno en sus rutas.
**Plazo:** construcción del 28-nov al 8-dic-2026, veredicto antes del 10-dic. Si terminan antes, mejor.
**Pasa por UX:** no (el contrato lo dice: no cambia nada visible).

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (y que repite el contrato en "Rutas de cada rol").
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]`, **sin** la línea `Co-Authored-By`. Sin push a `main`; sin merge.
3. No mires ni preguntes por el trabajo del otro rol. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`. La respuesta sale del contrato o se escala al humano; si cambia algo, llega como contrato v2.
4. No toques `Empezar.txt` (cambios del humano) ni lo incluyas en commits.
5. Ningún archivo de imagen en el repositorio, ni siquiera de prueba (AGENTS.md regla 8; contrato, decisión 6). Si necesitas una imagen, se genera en tiempo de ejecución.
6. Reglas de negocio de `AGENTS.md`, en especial la 1 (la palabra prohibida) y la 7 (ningún error se convierte en negativo).
7. Comandos de referencia (SPRINT0 §5): arranque `docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build`; pruebas `docker compose -f infra/docker-compose.yml run --rm simuladores pytest` y `... run --rm api pytest`.

## Qué entrega cada uno

- **TESTER:** pruebas automatizadas de cada caso del contrato (secciones 1 a 8) en `services/simuladores/tests/` (y `pruebas/datos/` si hace falta), escritas contra el contrato, no contra el código. Informe `informes/TESTER-HU-08.md` con cada caso en verde, rojo o `NO VERIFICADO`, con evidencia.
- **DEV:** implementación que cumple el contrato en sus rutas, con los tres yaml en `contratos/fuentes/` e `infra/.env.example` al día. Informe `informes/DEV-HU-08.md` con qué hizo, dónde y cómo se arranca.

## Aviso de vuelta

Al terminar: `herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-HU-08.md"`.

## Instrucciones del ciclo (M-n)

Aquí se agregan las aclaraciones durante el ciclo (M-1, M-2, …). Cada una dice qué reemplaza. Si recibes "lee M-n del encargo", es esta sección.

### M-1 (2026-11-19) — Contrato v2

**Reemplaza** la referencia a la v1 del encabezado: el documento de trabajo ahora es `docs/contratos/CONTRATO-HU-08.md` **v2**, aprobado por el humano. Los cambios C1 a C5 están en el changelog del contrato. Cada rol revisa su parte contra la v2:

- **DEV:** C5 (dependencias de prueba en el grupo `dev` del simulador) es trabajo nuevo. Confirma que lo ya construido cumple C1 a C4. Al terminar: `ENTREGA DEV` con el informe actualizado.
- **TESTER:** ajusta las pruebas a C1 a C5 (incluidos H1 y H2) y haz la corrida definitiva cuando Docker esté disponible. Al terminar: `ENTREGA TESTER` con el informe final.

### M-2 (2026-11-19) — Contrato v3

**Reemplaza** a M-1 en la versión: el documento de trabajo ahora es el contrato **v3**. Agrega C6: `infra/docker-compose.yml` monta `../contratos/fuentes` en solo lectura en `/app/contratos/fuentes` del contenedor `simuladores`, con `CONTRATOS_FUENTES_DIR=/app/contratos/fuentes`.

- **DEV:** C6 es trabajo nuevo, junto con C5.
- **TESTER:** usa `CONTRATOS_FUENTES_DIR`.
