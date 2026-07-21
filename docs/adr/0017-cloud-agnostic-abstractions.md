# ADR-0017: Cloud Agnostic — All Dependencies Behind Abstractions

## Estado
Aceptado

## Contexto
Complementa y formaliza el principio 7 del producto ("Cloud-agnostic y costo cero por defecto") y ADR-0002 (prioridad de infraestructura) como restricción arquitectónica explícita.

## Decisión
- El proyecto completo debe permanecer **cloud agnostic**.
- Toda dependencia de infraestructura debe ser **reemplazable** sin modificar el domain ni el application layer.
- Todo servicio externo debe accederse a través de **abstracciones** (interfaces/protocolos definidos en la capa de aplicación, implementados en infraestructura).

## Consecuencias
- Storage de archivos: interfaz `FileStorage` → implementaciones: local filesystem, MinIO, S3, GCS, Supabase Storage.
- Base de datos: SQLAlchemy como abstracción sobre PostgreSQL (portable a otros motores SQL si fuera necesario).
- Envío de emails/notificaciones: interfaz `NotificationService` → implementaciones intercambiables.
- No se usa ningún SDK propietario de cloud directamente en application/domain layers.
- El docker-compose de desarrollo local es la implementación de referencia — cualquier deploy a cloud es solo otra implementación de las mismas interfaces.
