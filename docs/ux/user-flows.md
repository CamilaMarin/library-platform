# User Flows — EntreLíneas

## 1. Alta de libro digital
1. Usuario sube archivo (epub/pdf) desde `/library/add`.
2. Sistema cifra y almacena en espacio aislado de su cuenta.
3. Se crean/reutilizan registros de Libro + Ejemplar (tipo=digital).
4. Se registra la entrada correspondiente en el registro de tratamiento si aplica.

## 2. Turno de lectura digital dentro de un club
1. Miembro intenta unirse a un turno de lectura de un libro del club.
2. Sistema valida que tenga su propio ejemplar (físico o digital); si no, lo dirige a agregarlo — nunca ofrece acceso al archivo de otro miembro.
3. Se activa el turno; los comentarios quedan asociados al turno, no al archivo.

## 3. Ejercicio de derechos ARCO
1. Usuario entra a `/privacy`.
2. Elige: exportar datos (portable JSON/CSV), rectificar, cancelar cuenta, u oponerse a un tratamiento puntual (ej. salir de los sorteos del grupo).
3. Cancelación dispara job de borrado que purga archivos y anonimiza logs más allá del mínimo legal de retención.

## 4. Notificación de brecha (flujo interno/admin)
1. Monitoreo detecta acceso anómalo.
2. Playbook: contención → evaluación de alcance → notificación a la APDP y a titulares afectados dentro de 72h → registro del incidente.

## 5. Sorteo de lectura
1. Usuario entra a `/draw`, define filtros (género, páginas máx., disponibilidad, no leído).
2. Sistema cruza ejemplares de todos los miembros del grupo que cumplen el filtro.
3. Resultado muestra el libro sorteado y de qué biblioteca personal proviene, sin exponer el archivo.
