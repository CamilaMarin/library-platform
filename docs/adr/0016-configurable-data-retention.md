# ADR-0016: Configurable Data Retention

## Estado
Aceptado

## Contexto
La Ley 21.719 exige políticas de retención de datos pero no prescribe periodos específicos para todos los casos. Hardcodear periodos de retención hace difícil adaptarse a cambios regulatorios o a interpretaciones legales futuras.

## Decisión
- **No hardcodear periodos de retención** en el código.
- Las políticas de retención deben ser **configurables** (vía configuración de aplicación, no constantes en código).
- Toda política debe estar **documentada** y ser comprensible para el usuario.
- Los usuarios deben ser **informados antes de cualquier eliminación** de datos por expiración de retención.

## Consecuencias
- Se necesita una tabla o configuración de `PoliticaRetencion` que defina periodos por tipo de dato.
- El flujo de cancelación de cuenta no purga inmediatamente — informa al usuario del plazo y luego ejecuta la purga según la política configurada.
- Facilita adaptarse si la APDP emite guías específicas sobre periodos de retención.
- Requiere un job periódico que evalúe datos expirados contra la política vigente.
