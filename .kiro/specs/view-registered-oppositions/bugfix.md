# Bugfix Requirements Document

## Introduction

En el panel de derechos ARCO de la página de configuración (`/settings`), el usuario puede
registrar oposiciones al tratamiento de sus datos personales mediante el formulario
`OppositionForm`. Sin embargo, una vez enviada la oposición no existe ninguna vista que
liste las oposiciones ya registradas: el usuario no puede saber cuántas oposiciones tiene
activas ni cuáles son sus motivos.

El problema tiene dos capas:

1. **Backend**: no existe ningún endpoint `GET /users/me/oppositions` (ni equivalente) que
   exponga la lista de propósitos opuestos almacenados en `user.privacy_settings["opposed_purposes"]`.
2. **Frontend**: el componente `OppositionForm` solo muestra el formulario de alta; no hay
   ningún componente que consulte ni renderice las oposiciones existentes.

El impacto es que el derecho de oposición garantizado por la Ley 21.719 queda incompleto:
el usuario puede ejercerlo pero no puede verificar su estado.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN el usuario navega al panel ARCO en `/settings` THEN el sistema muestra únicamente el
    formulario para registrar una nueva oposición, sin ninguna sección que liste las oposiciones
    previamente guardadas.

1.2 WHEN el usuario registra una oposición con éxito THEN el sistema muestra un mensaje de
    confirmación y restablece el formulario, pero no actualiza ni muestra un listado de oposiciones
    activas en ninguna parte de la página.

1.3 WHEN el frontend intenta obtener la lista de oposiciones del usuario THEN el sistema no tiene
    ningún endpoint disponible (`GET /users/me/oppositions` devuelve 404), por lo que la lista
    nunca puede ser recuperada.

### Expected Behavior (Correct)

2.1 WHEN el usuario navega al panel ARCO en `/settings` THEN el sistema SHALL mostrar la lista de
    oposiciones activas registradas por el usuario (vacía si no hay ninguna), junto al formulario
    para registrar una nueva.

2.2 WHEN el usuario registra una oposición con éxito THEN el sistema SHALL actualizar la lista
    visible de oposiciones para incluir la nueva entrada, sin requerir recarga de página.

2.3 WHEN el frontend solicita `GET /users/me/oppositions` THEN el sistema SHALL responder con la
    lista de propósitos opuestos almacenados en `privacy_settings["opposed_purposes"]` para el
    usuario autenticado.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN el usuario envía el formulario de oposición con un propósito válido THEN el sistema SHALL
    CONTINUE TO registrar la oposición correctamente via `POST /users/me/oppose` y devolver la
    respuesta `OpposeResponse` con `opposed: true`.

3.2 WHEN el usuario accede a la página de configuración THEN el sistema SHALL CONTINUE TO mostrar
    el formulario `OppositionForm` con los chips de propósitos predefinidos y el campo de texto
    libre.

3.3 WHEN los demás derechos ARCO (Acceso, Rectificación, Cancelación) están en uso THEN el sistema
    SHALL CONTINUE TO funcionar correctamente sin verse afectados por los cambios introducidos.

3.4 WHEN un usuario no autenticado intenta acceder al nuevo endpoint THEN el sistema SHALL CONTINUE
    TO devolver `401 Unauthorized`, respetando la protección existente sobre todos los endpoints
    `/users/me/*`.
