# Diagramas de arquitectura

| Carpeta o archivo | Qué es | Cómo se genera |
|---|---|---|
| `fuentes/*.json` | Fuentes de los diagramas interactivos | Se editan a mano |
| `*.html` y `*.delivery.json` | Diagramas interactivos (C4 y secuencias) y su recibo de entrega | `archify finalize` desde la fuente |
| `osigp/*.svg` | Diagramas de los formatos OSIGP-FR-03 y FR-04 | SVG editados a mano; los PNG de los `.docx` (`entregables/osigp/`) se renderizan desde estos SVG con Chrome sin interfaz, a escala 2 |

Última regeneración: 2026-11-24, con el stack aceptado (ADR-0017 a 0019: Flutter, NGINX y el servicio `motor`).

## Verificación en el navegador

**Hecha el 2026-11-24 (20:36 y 20:37):** los cinco HTML pasaron `browser-check` con `"ok": true`, y `seq-verificacion-facial` pasó además un `finalize` completo (los cuatro gates). Los recibos están en `evidencia-2026-11-24/`; cada uno apunta al `receiptId` del `.delivery.json` de su diagrama. La primera corrida falló porque se hizo desde una PowerShell de administrador.

Los cinco HTML pasaron `validate`, `deliver` y `check` de `archify` el 2026-11-24. El `browser-check` no se pudo correr desde la sesión del agente, porque Chrome no abre su canal de depuración ahí. Hay que correrlo desde una **PowerShell abierta de forma normal** (sin "Ejecutar como administrador"), en la carpeta del worktree:

```powershell
cd C:\Willy\Trabajo\MININTER\Movil_Buscador-entregables
$archify = "C:\Users\Willy\.claude\skills\archify\bin\archify.mjs"
foreach ($d in "c4-contexto","c4-contenedores","seq-consulta-placa","seq-verificacion-facial","seq-vencimiento-24h") {
  node $archify browser-check "docs\arch\diagramas\$d.html" --out-dir "docs\arch\diagramas\evidencia-2026-11-24" --json
}
```

Cada corrida deja su recibo en `docs\arch\diagramas\evidencia-2026-11-24\`. Si los cinco terminan con `"ok": true`, se pueden commitear esos recibos con el prefijo `[ARCH]`. Si alguno falla, se lo pasa al ARCH con el texto del error.

## Regenerar un diagrama interactivo

Desde la misma carpeta, después de editar su fuente:

```powershell
node $archify finalize sequence docs\arch\diagramas\fuentes\seq-verificacion-facial.json docs\arch\diagramas\seq-verificacion-facial.html --quality showcase --out-dir docs\arch\diagramas\evidencia-<fecha> --json
```

Para los C4 se usa `architecture` en lugar de `sequence`.
