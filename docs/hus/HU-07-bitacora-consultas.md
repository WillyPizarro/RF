# HU-07: Registrar cada consulta en una bitácora

## Historia de usuario
Como responsable del servicio en el MININTER
Quiero que cada consulta, decisión y error quede registrado en una bitácora que nadie pueda modificar
Para poder auditar quién consultó qué, cuándo, por qué y con qué resultado

## Contexto
PRD › Alcance — Incluye › Componente 2 › Trazabilidad: "bitácora de consultas con usuario, fecha, hora, motivo de consulta y resultado; gestión de errores". Componente 1: "bitácoras". Enfoque MVP: "bitácora con motivo de consulta obligatorio" se construye.
Las demás HUs (01, 02, 03, 04, 05, 06) generan los registros; esta HU define cómo se guardan y consultan.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Bitácora de consultas
  Escenario: Una consulta queda registrada
    Dado que un usuario en campo completó una consulta de placa o de rostro
    Cuando la consulta termina, con éxito o con error
    Entonces la bitácora tiene un registro con usuario, fecha, hora, tipo de consulta, motivo y resultado
```

### Escenario 2 — Caso borde: intento de modificación
```gherkin
  Escenario: Alguien intenta modificar o borrar un registro
    Dado que existe un registro en la bitácora
    Cuando cualquier usuario o servicio intenta modificarlo o borrarlo
    Entonces la operación es rechazada
    Y el registro original permanece igual
```

### Escenario 3 — Caso borde: datos sensibles
```gherkin
  Escenario: Registro de una verificación facial
    Dado que se completó una verificación facial
    Cuando se guarda el registro
    Entonces la bitácora guarda el identificador de la captura y el score
    Y no guarda la imagen del rostro
```

## Supuestos
- (MVP) La bitácora solo admite inserciones; la inalterabilidad avanzada (firma, sellado) se documenta para producción.
- Los registros se marcan como datos sintéticos.

## Puntos abiertos
- ¿Quién puede consultar la bitácora, desde dónde (app móvil o web) y con qué filtros? El PRD define qué se registra, no quién lo consulta.
- PRD PA #16: ¿cuánto tiempo se conserva la bitácora y quién autoriza su eliminación?
- PRD PA #9: ¿existe un rol de auditor?

## Fuera de alcance (explícitamente excluido en el PRD)
- Inalterabilidad avanzada de la bitácora (firma, sellado de tiempo): política de seguridad avanzada, se documenta, no se construye.
