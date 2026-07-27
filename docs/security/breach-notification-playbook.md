# Breach Notification Playbook — EntreLíneas

| Metadata         | Valor                                              |
|------------------|----------------------------------------------------|
| Referencia legal | Ley 21.719, Art. 14 bis                            |
| Requisito        | `privacy/requirements.md` Req 1.3                  |
| Fecha creación   | 2026-07-27                                         |
| Responsable      | DPO + Equipo de Ingeniería                         |

---

## 1. Definición / Definition

Una **vulneración de datos personales** (brecha) se define como cualquier incidente de seguridad que provoque:

- Acceso no autorizado a datos personales almacenados en el sistema.
- Destrucción, pérdida o alteración accidental o ilícita de datos personales.
- Comunicación o cesión no autorizada de datos personales a terceros.
- Cualquier evento que comprometa la confidencialidad, integridad o disponibilidad de datos personales de los usuarios.

Incluye, pero no se limita a:
- Exfiltración de base de datos.
- Acceso indebido mediante credenciales comprometidas.
- Exposición accidental de datos en logs, backups o APIs.
- Ransomware que afecte datos personales.

---

## 2. Detección / Detection

### Mecanismos automáticos
- **Audit logs**: Patrones anómalos de acceso (volumen inusual de lecturas, acceso fuera de horario, accesos desde IPs no reconocidas).
- **Monitoreo de infraestructura**: Alertas de WAF, IDS/IPS, y servicios de detección de anomalías.
- **Integridad de tokens**: Detección de uso de tokens revocados o expirados.
- **Alertas de dependencias**: Notificaciones de vulnerabilidades en paquetes (Dependabot, Snyk).

### Mecanismos manuales
- **Reportes de usuarios**: Canal de reporte en la plataforma y email de contacto.
- **Revisión periódica**: Auditorías de seguridad programadas.
- **Equipo de desarrollo**: Detección durante revisión de código o debugging.

---

## 3. Evaluación / Assessment (dentro de 4 horas)

Una vez detectado un posible incidente, se debe evaluar dentro de las primeras **4 horas**:

### Clasificación de severidad

| Severidad | Criterio                                                                                  | Ejemplo                                           |
|-----------|-------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Alta**  | PII expuesto a terceros no autorizados; afecta >100 usuarios o incluye credenciales      | Exfiltración de tabla `users`, leak de emails      |
| **Media** | Datos personales accedidos internamente sin autorización; <100 usuarios afectados         | Empleado accede a datos sin permiso               |
| **Baja**  | Datos operacionales expuestos sin PII; sin evidencia de acceso externo                    | Logs con IDs internos expuestos en endpoint debug |

### Información a determinar
- Tipo de datos afectados (PII, credenciales, contenido personal).
- Número estimado de usuarios afectados.
- Vector de ataque utilizado.
- Si la brecha sigue activa o fue contenida.
- Evidencia disponible (logs, timestamps, IPs).

---

## 4. Contención / Containment (dentro de 8 horas)

Acciones técnicas inmediatas una vez confirmada la brecha:

### Acciones obligatorias
1. **Revocar todos los refresh tokens** de usuarios afectados (`RefreshToken.revoked_at = now()`).
2. **Deshabilitar endpoints comprometidos** si el vector fue una API vulnerable.
3. **Aislar datos afectados** — restringir acceso a tablas/storage involucrado.
4. **Rotar secretos** — claves JWT, API keys, credenciales de servicio que pudieran estar comprometidas.
5. **Bloquear IPs/cuentas sospechosas** identificadas en el análisis.
6. **Preservar evidencia** — snapshot de logs, estado de BD, y configuraciones antes de aplicar fixes.

### Acciones condicionales (según severidad alta)
- Poner la plataforma en modo mantenimiento si la brecha sigue activa.
- Notificar al proveedor cloud si involucra infraestructura compartida.
- Activar canal de comunicación de emergencia del equipo.

---

## 5. Notificación — APDP / Notification — Data Protection Agency (dentro de 72 horas)

Conforme al Art. 14 bis de la Ley 21.719, se debe notificar a la Agencia de Protección de Datos Personales (APDP) dentro de **72 horas** desde que se toma conocimiento de la brecha.

### Información requerida en la notificación

1. Naturaleza de la vulneración (qué ocurrió).
2. Categorías y número aproximado de titulares afectados.
3. Categorías y número aproximado de registros afectados.
4. Consecuencias probables de la vulneración.
5. Medidas adoptadas o propuestas para remediar la brecha.
6. Medidas adoptadas para mitigar efectos adversos en los titulares.
7. Datos de contacto del DPO o responsable.

### Canal de notificación
- Portal web de la APDP (cuando esté disponible).
- Correo electrónico oficial de la APDP.
- Documento formal con firma del responsable de tratamiento.

### Plantilla de notificación

```
ASUNTO: Notificación de vulneración de datos personales — EntreLíneas

Fecha de detección: [FECHA]
Fecha de notificación: [FECHA]

1. Descripción del incidente:
   [Descripción clara y concisa]

2. Datos afectados:
   - Tipo: [PII / Credenciales / Contenido personal]
   - Categorías: [email, nombre, contraseña hash, etc.]
   - Titulares afectados (estimado): [N]

3. Consecuencias probables:
   [Evaluación de riesgo para los titulares]

4. Medidas de contención adoptadas:
   [Lista de acciones tomadas]

5. Medidas de remediación planificadas:
   [Plan de acción]

6. Contacto:
   - DPO: [NOMBRE] — [EMAIL]
   - Tel: [TELÉFONO]

Firma: ________________________
Responsable del tratamiento
```

---

## 6. Notificación — Usuarios afectados / Notification — Affected Users (dentro de 72 horas)

Cuando la brecha sea susceptible de generar un riesgo alto para los derechos y libertades de los titulares, se debe notificar directamente a los usuarios afectados.

### Canal de comunicación
- **Email** al correo registrado del usuario.
- Notificación in-app al siguiente inicio de sesión (complementaria).

### Contenido obligatorio de la notificación al usuario

1. Descripción en lenguaje claro de lo ocurrido.
2. Tipo de datos personales afectados.
3. Posibles consecuencias para el usuario.
4. Medidas que el usuario puede tomar para protegerse.
5. Medidas que la plataforma ha tomado.
6. Datos de contacto del DPO.

### Plantilla de comunicación al usuario

```
Asunto: Aviso importante sobre la seguridad de tu cuenta — EntreLíneas

Estimado/a [NOMBRE],

Te informamos que hemos detectado un incidente de seguridad que podría
haber afectado algunos de tus datos personales en nuestra plataforma.

¿Qué ocurrió?
[Descripción clara y sin tecnicismos]

¿Qué datos fueron afectados?
[Lista de tipos de datos: email, nombre, etc.]

¿Qué hemos hecho?
- Revocamos todas las sesiones activas de tu cuenta.
- [Otras medidas tomadas]

¿Qué puedes hacer tú?
- Cambiar tu contraseña en tu próximo inicio de sesión.
- Revisar la actividad reciente de tu cuenta.
- Contactarnos si notas algo inusual.

Lamentamos esta situación y estamos trabajando para que no se repita.

Contacto DPO: [EMAIL]

Atentamente,
Equipo EntreLíneas
```

---

## 7. Remediación / Remediation

### Análisis de causa raíz
- Determinar el vector de ataque exacto.
- Identificar la vulnerabilidad explotada.
- Revisar si existían controles que fallaron.

### Despliegue de corrección
- Desarrollar y desplegar fix de la vulnerabilidad.
- Verificar que el fix cierra efectivamente el vector.
- Ejecutar pruebas de penetración focalizadas post-fix.

### Medidas de prevención
- Actualizar dependencias vulnerables.
- Reforzar controles de acceso si aplica.
- Agregar monitoreo específico para el vector descubierto.
- Actualizar la política de retención si la brecha reveló datos retenidos innecesariamente.

---

## 8. Revisión Post-Incidente / Post-Incident Review

Dentro de los **7 días** posteriores al cierre del incidente:

1. **Reunión de lecciones aprendidas** — todo el equipo involucrado.
2. **Documentar**:
   - Línea de tiempo completa del incidente.
   - Qué funcionó bien en la respuesta.
   - Qué se puede mejorar.
   - Acciones pendientes.
3. **Actualizar políticas** — modificar este playbook si se identifican gaps.
4. **Actualizar controles técnicos** — implementar nuevas alertas o validaciones.
5. **Reportar internamente** — informe ejecutivo para stakeholders.

---

## 9. Pasos Automatizados / Automated Steps

El sistema ejecuta automáticamente las siguientes acciones cuando se activa el protocolo de brecha:

| Acción                                    | Trigger                        | Descripción                                                      |
|-------------------------------------------|--------------------------------|------------------------------------------------------------------|
| Revocar todos los refresh tokens          | Activación del playbook        | `UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id IN (afectados)` |
| Exportar audit logs                       | Activación del playbook        | Snapshot completo de `AuditLog` para preservar evidencia.        |
| Marcar cuentas afectadas                  | Activación del playbook        | Flag `requires_password_change = true` en usuarios afectados.    |
| Notificación al equipo                    | Detección de anomalía          | Alerta inmediata vía canal de emergencia (Slack/email).          |
| Forzar re-autenticación                   | Revocación de tokens           | Usuarios afectados deben autenticarse nuevamente.                |
| Registrar evento en AuditLog              | Cualquier acción del playbook  | Todas las acciones de respuesta quedan auditadas.                |

---

## 10. Información de Contacto / Contact Information

| Rol                    | Nombre        | Email                    | Teléfono       |
|------------------------|---------------|--------------------------|----------------|
| DPO (Data Protection Officer) | [POR DEFINIR] | dpo@entrelineas.cl       | [POR DEFINIR]  |
| Lead Técnico de Seguridad     | [POR DEFINIR] | security@entrelineas.cl  | [POR DEFINIR]  |
| Asesor Legal                  | [POR DEFINIR] | legal@entrelineas.cl     | [POR DEFINIR]  |
| Contacto APDP                 | —             | [Canal oficial APDP]     | —              |

---

## Historial de Revisiones

| Fecha      | Versión | Cambio                        |
|------------|---------|-------------------------------|
| 2026-07-27 | 1.0     | Creación inicial del playbook |

---

*Este documento debe revisarse y actualizarse al menos una vez al año o después de cada incidente de seguridad.*
