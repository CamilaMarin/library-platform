# ADR-0003: Cumplimiento de la Ley 21.719 desde el diseño

## Estado
Aceptado

## Contexto
La Ley 21.719 (Chile) entra en plena vigencia el 1 de diciembre de 2026, alineada con el estándar GDPR: crea la Agencia de Protección de Datos Personales (APDP), exige derechos ARCO + portabilidad, notificación de brechas en 72 horas, y multas de hasta 20.000 UTM o 4% de ingresos anuales en reincidencia. Aplica a cualquier organización que trate datos de personas en Chile, sin excepción de tamaño.

## Decisión
- Privacy by Design desde el primer sprint, no como ajuste posterior al MVP.
- Cada entidad que almacene datos personales queda vinculada a un registro de tratamiento (`RegistroTratamientoDatos`) y a logs de auditoría.
- El panel de privacidad del usuario (`/privacy`) implementa los 4 derechos ARCO + portabilidad como autoservicio, sin pasar por soporte.
- Existe un playbook documentado de notificación de brechas dentro de 72 horas.
- Minimización de datos: ningún campo se agrega al modelo sin justificar su necesidad funcional explícita (ej. no se pide RUT).

## Consecuencias
- Overhead de diseño y desarrollo mayor al de un MVP típico, pero evita rediseñar el modelo de datos bajo presión antes de diciembre de 2026.
- Sirve como diferenciador de portafolio: pocos proyectos personales documentan cumplimiento normativo real desde el ADR.
- Requiere revisión legal externa antes de cualquier lanzamiento con datos reales (fuera del alcance de este documento, que es orientación general y no asesoría legal).
