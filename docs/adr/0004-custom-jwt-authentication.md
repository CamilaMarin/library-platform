# ADR-0004: Custom JWT Authentication

## Estado
Aceptado

## Contexto
El proyecto necesita un mecanismo de autenticación. Las opciones evaluadas fueron: Supabase Auth (servicio gestionado), AWS Cognito (cloud-específico), sesiones server-side (requieren estado compartido/Redis), y JWT personalizado (stateless, portable).

## Decisión
- Implementar autenticación propia basada en **JWT Access Tokens + Refresh Tokens**.
- Se rechazan explícitamente: Supabase Auth, AWS Cognito y sesiones server-side.

## Justificación
- **Cloud agnostic:** no ata el proyecto a ningún proveedor de identidad externo.
- **Vendor neutral:** el mecanismo es estándar (RFC 7519) y portable entre cualquier infraestructura.
- **Portable:** se puede desplegar en Docker local, Render, Vercel, GCP o AWS sin cambiar el sistema de auth.
- **Fácil de testear:** no requiere mocks de servicios externos para tests de integración del flujo de autenticación.
- **Experiencia de aprendizaje:** implementar auth desde cero aporta valor como pieza de portafolio.

## Consecuencias
- Se elimina la dependencia de Supabase Auth mencionada en `adr/0002-tech-stack.md` — Supabase queda solo como opción de Postgres + Storage gestionado.
- No se necesita Redis para sesiones en el MVP (ver ADR-0012).
- Requiere implementar rotación de Refresh Tokens, revocación, y almacenamiento seguro del token en el cliente.
- El domain layer sigue sin conocer JWT — la lógica vive en infrastructure/interface layer.
