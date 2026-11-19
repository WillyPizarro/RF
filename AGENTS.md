# AGENTS.md — Movil Buscador (MININTER)

Prototipo móvil (MVP, 30 a 40 días) para que personal autorizado verifique si un vehículo (por placa) o una persona (por rostro) tiene requisitoria. **Solo datos sintéticos y simuladores.**

## Documentos de referencia

| Qué | Dónde |
|---|---|
| PRD y puntos abiertos | `PRD.md` |
| Historias de Usuario | `docs/hus/` |
| Diseño de interfaz | `docs/ux/` |
| Diseño técnico y ADRs | `docs/arch/TECH-DESIGN.md`, `docs/arch/adrs/` |
| Sprint 0 | `SPRINT0.md` |

## Reglas de negocio que nadie rompe

1. La palabra "identificado" no existe en la app, la API, la bitácora ni los mensajes. Solo: "Posible coincidencia — requiere revisión", "No concluyente — verifique por otros medios", "Sin coincidencia en la lista consultada".
2. Motivo de consulta obligatorio antes de consultar una placa o un rostro.
3. Una captura de mala calidad se rechaza con su motivo y no se compara.
4. Nada automático antes de la revisión humana. Un agente nunca revisa su propia consulta (ADR-0003).
5. La captura facial se borra tras la comparación, o tras la revisión si hay candidato (máximo 24 h, ADR-0008).
6. Sin identificación masiva, video continuo ni lectura automática de placas.
7. Ningún error se convierte en un resultado negativo ("sin requisitoria" o "sin coincidencia").
8. Ningún dato real de ciudadanos, ninguna foto en el repositorio, ningún secreto versionado.

## Propiedad de rutas

| Rol | Rutas |
|---|---|
| TESTER | `services/api/tests/`, `services/simuladores/tests/`, `apps/movil/__tests__/`, `apps/movil/.maestro/`, `pruebas/carga/`, `pruebas/datos/` |
| DEV | `apps/movil/` (salvo `__tests__/` y `.maestro/`), `services/api/` (salvo `tests/`), `services/simuladores/` (salvo `tests/`), `infra/`, `contratos/api/`, `contratos/fuentes/`, `scripts/` |
| ARCH | `docs/arch/` |
| UX | `docs/ux/` |
| BA / PM | `docs/hus/`, `PRD.md` |
| Solo LEAD / humano | `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/`, `skills-lock.json`, `settings.json`, `SPRINT0.md`, `docs/contratos/` |

Cada rol toca solo sus rutas. Los commits llevan el prefijo del rol (`[DEV]`, `[TESTER]`, …) e incluyen solo archivos de sus rutas. Nadie hace push a `main` ni mergea: eso lo decide el humano.
