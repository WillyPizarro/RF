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

_(Sin instrucciones por ahora.)_
