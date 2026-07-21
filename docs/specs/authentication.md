# Spec — Authentication & Groups

## Requirement: Registro y consentimiento

**User Story:** Como nuevo usuario, quiero crear mi cuenta y entender qué se hace con mis datos, para decidir con confianza si uso la plataforma.

### Acceptance Criteria
1. CUANDO un usuario crea una cuenta, EL SISTEMA DEBERÁ pedir consentimiento explícito e informado (finalidad + base legal) antes de habilitar cualquier función.
2. EL SISTEMA DEBERÁ registrar timestamp y versión de política aceptada en `ConsentimientoDatos`.

## Requirement: Autenticación JWT

**User Story:** Como usuario registrado, quiero iniciar sesión de forma segura y mantener mi sesión activa sin re-autenticarme constantemente.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ emitir un Access Token (JWT, corta duración) y un Refresh Token (larga duración) al hacer login exitoso.
2. EL SISTEMA DEBERÁ validar el Access Token en cada request autenticado sin consultar estado server-side.
3. EL SISTEMA DEBERÁ permitir rotar el Refresh Token (emitir uno nuevo e invalidar el anterior) vía `POST /auth/refresh`.
4. EL SISTEMA DEBERÁ permitir revocar un Refresh Token (logout) vía `POST /auth/logout`.
5. EL SISTEMA DEBERÁ almacenar password con hashing seguro (bcrypt o argon2), nunca en texto plano.

> Referencia: `adr/0004-custom-jwt-authentication.md`

## Requirement: Grupo familiar

**User Story:** Como usuario, quiero crear o unirme a un grupo familiar, para compartir la experiencia de lectura con las personas correctas.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ permitir crear un grupo familiar e invitar a otros perfiles.
2. Un perfil invitado NUNCA DEBERÁ integrarse al grupo sin aceptar explícitamente la invitación.

> Nota: La gestión de cuentas de menores (adulto responsable) está diferida a v2 (ver `adr/0005-minor-accounts-deferred.md`). En el MVP todos los usuarios comparten el mismo modelo de permisos.

## Requirement: Cuenta y datos personales

### Acceptance Criteria
1. EL SISTEMA DEBERÁ permitir exportar o eliminar la cuenta y todos los datos asociados desde el propio perfil, sin intervención de soporte.
