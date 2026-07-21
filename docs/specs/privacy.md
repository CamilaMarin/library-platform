# Spec — Privacy & Ley 21.719 Compliance

## Requirement: Cumplimiento Ley 21.719

**User Story:** Como usuario, quiero certeza de que mis datos y los de mi familia se tratan de forma segura y transparente.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ mantener un registro de actividades de tratamiento (qué dato, finalidad, retención) auditable.
2. EL SISTEMA DEBERÁ implementar los 4 derechos ARCO + portabilidad, ejecutables por el usuario sin fricción.
3. SI ocurre una brecha de seguridad, ENTONCES EL SISTEMA DEBERÁ notificar a la APDP y a los titulares dentro de 72 horas, según un playbook documentado.
4. EL SISTEMA DEBERÁ aplicar minimización de datos: nunca solicitar ni almacenar un dato no estrictamente necesario.
5. EL SISTEMA DEBERÁ mantener logs de auditoría de accesos y modificaciones a datos personales.
6. EL SISTEMA DEBERÁ cifrar datos personales sensibles y archivos digitales en tránsito y en reposo.
7. EL SISTEMA DEBERÁ definir y aplicar una política de retención configurable (no hardcodeada), eliminando datos de cuentas inactivas o cerradas según la política vigente. Los usuarios deben ser informados antes de cualquier eliminación (ver `adr/0016-configurable-data-retention.md`).
8. ANTES de compartir cualquier dato de un usuario con otro miembro del grupo, EL SISTEMA DEBERÁ requerir visibilidad configurada explícitamente por el dueño del dato.
