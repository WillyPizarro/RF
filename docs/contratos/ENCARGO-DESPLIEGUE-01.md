# ENCARGO LEAD → DEV y TESTER — DESPLIEGUE-01

**Documento de trabajo:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v1**, aprobado por el humano (vía PM) el 2026-11-19. Es la única spec.
**Rama:** `despliegue-01`, desde `main` `fa75945`. **Se trabaja en un worktree aparte**, `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`, para no pisar `hu-04` en la carpeta principal. Ahí no está `infra/.env` (no se versiona): si lo necesitas, cópialo desde la carpeta principal y **no lo agregues a git**. Tampoco están las dependencias: corre `npm ci` en `apps/movil` si te hacen falta.
**Bloqueo:** el humano contrata el VPS, el dominio y Supabase **a más tardar el 2-dic**. La ventana de despliegue es del 3 al 7-dic. **Fase A (ahora):** todo lo que no necesita el VPS. **Fase B (3 al 7-dic):** el despliegue real, con una M-n.
**Prioridad:** HU-04 va primero. Esto avanza en los huecos y **no la frena**.

## Reglas

1. Solo tus rutas (`AGENTS.md`; el DEV ahora también es dueño de `docs/despliegue/`). Commits con `[DEV]` o `[TESTER]`, **sin** `Co-Authored-By`, sin push y sin merge.
2. **Ningún secreto en el repositorio:**
   - nada de claves de Supabase, `CLAVE_USUARIOS_PRUEBA`, llaves SSH, *deploy keys*, tokens de EAS ni el `.env` del VPS;
   - en los documentos van solo los **nombres** de las variables;
   - la clave de los usuarios nunca va en la guía.
3. Solo datos sintéticos. Sin fotos.
4. No toques `Empezar.txt`. Las dudas van al LEAD con `PREGUNTA <ROL>`.
5. No compres ni contrates nada, y no crees cuentas: eso lo hace el humano.

## Fase A — qué entrega cada uno

- **DEV:**
  - **Compose del VPS:** `infra/docker-compose.vps.yml`, que quita `db` y `auth` y deja `api`, `simuladores` y `proxy` con los puertos 80 y 443. **Sin** el compose de fotos.
  - **Variables:** `infra/.env.example` documenta las del VPS. La credencial de administración de Auth va **solo** para `cargar_usuarios` (decisión 1), con el nombre que elijas.
  - **La credencial fuera de la API en marcha:** que el contenedor `api` no la reciba, y que `cargar_usuarios` la acepte al correrlo, también con las "secret keys" nuevas de Supabase si el proyecto no tiene el JWT secret heredado. **El login no cambia.**
  - **Script de despliegue:** `scripts/desplegar.ps1 <rama o commit>`, que entra por SSH (decisión 4), hace `git fetch` y `checkout` desde `origin`, levanta los servicios con `up -d --build`, migra y espera a que `/v1/salud` responda `200`. No copia secretos y se puede correr dos veces seguidas.
  - **Perfil de EAS:** `preview` en `apps/movil/eas.json`. APK interno, sin `developmentClient` y con `EXPO_PUBLIC_API_URL` del dominio. Mientras no haya dominio, usa un marcador documentado.
  - **En `docs/despliegue/`, en español simple:**
    - `GUIA-PROBADORES.md` (§7 del contrato);
    - `DOMINIO.md`: comprar el dominio y crear el registro DNS `A`;
    - `MANUAL-DESPLIEGUE.md`: el VPS, el `.env` (solo nombres), Supabase (*Session pooler*), migrar, cargar usuarios, los comandos del §6, los logs y el borrado (§8);
    - cómo generar la llave SSH dedicada, autorizarla y revocarla al cierre.
  - **Verificaciones en local:**
    - `docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml config` arma solo `api`, `simuladores` y `proxy`;
    - la API en marcha no tiene la credencial de administración.
  - **Al terminar:** `ENTREGA DEV` con el informe en `informes/DEV-DESPLIEGUE-01.md`.
- **TESTER** (cuando termine la suite de la etapa 1 de HU-04):
  - **Prueba contra el VPS:** `services/api/tests/test_despliegue_vps.py`, que se omite si no está `URL_VPS`. Cubre los casos del contrato que se ven desde afuera:
    - los puertos 22, 80 y 443, y que 8000, 8001 y 5432 están cerrados;
    - el certificado validado con las CA del sistema;
    - `/v1/salud` responde `200`, y `/openapi.json` y `/` responden `404`;
    - login, las 3 placas, la bitácora del supervisor y el `403` por rol.

    La clave se lee del entorno y nunca se escribe.
  - **Comandos para dentro del VPS**, que corre quien tenga SSH: `pg_stat_activity` con `api_app`, el trigger, `printenv` sin la credencial de administración, la clave fuera de los logs del proxy y de `api`, y que el APK no es depurable (`aapt` o `apkanalyzer`).
  - **En local:** comprueba que la prueba nueva se omite sin `URL_VPS` y que la configuración del compose del VPS es la correcta.
  - **Informe:** `informes/TESTER-DESPLIEGUE-01.md`.

## Fase B (3 al 7-dic)

Se abre con una M-n cuando el humano tenga el VPS, el dominio y Supabase. La verificación del humano en su S23 Ultra, por el enlace y sin cable, cierra el veredicto antes del 8-dic.

## Aviso de vuelta

`herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-DESPLIEGUE-01.md"`.

## Instrucciones del ciclo (M-n)

### M-1 (2026-11-19) — Entrega del DEV de la fase A; regresión local

**No reemplaza nada.** El DEV entregó la fase A (`8402ef2`). Cambió también el compose base (`infra/docker-compose.yml`): las variables de `db` y `auth` ahora tienen valores por defecto vacíos (`:-`), para que el VPS no necesite valores falsos.

- **TESTER**, en la fase A y **después** de terminar la suite de HU-04, en el worktree de `despliegue-01`:
  1. Lo que ya pedía el encargo.
  2. Una **regresión local completa**: pytest de la API con el proxy en el puerto alterno y `PROXY_DISPONIBLE=1`, los simuladores y Jest. Así se comprueba que el cambio del compose base no rompió el entorno local.
  3. Que `infra/docker-compose.vps.yml` no le pasa a `api` ni `AUTH_ADMIN_CLAVE` ni `AUTH_JWT_SECRETO`, revisando `docker compose … config`.

  Al terminar: `ENTREGA TESTER`, con el informe en `informes/TESTER-DESPLIEGUE-01.md`.
- **DEV:** sin cambios. Los pasos del §8 para el acta ya están en `PENDIENTES.md` (los agregó el LEAD).

### M-2 (2026-11-20) — Aviso de telemetría en la guía para probadores

**No reemplaza nada.** El humano aprobó el anexo del BA, `docs/hus/anexos/HU-04-aviso-telemetria-mlkit.md` (commit `6eafcd1`, rama `hu-04`). Ese anexo no está en esta rama: léelo con `git show 6eafcd1:docs/hus/anexos/HU-04-aviso-telemetria-mlkit.md`.

- **DEV:** **después** de entregar la M-9 a la M-12 de HU-04, que tienen prioridad, copia **tal cual** el §2 del anexo en `docs/despliegue/GUIA-PROBADORES.md`. Ponlo como una sección sobre la lectura de la placa con la cámara y aclara que **se aplica desde el despliegue que incluya HU-04**: el APK de la Iteración 1 no tiene cámara. No cambies el texto. Commit `[DEV]` en `despliegue-01` y avisa con `ENTREGA DEV`.
