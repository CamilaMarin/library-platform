# ADR-0007: Review Visibility Model

## Estado
Aceptado

## Contexto
El modelo anterior de visibilidad de reseñas (`private | group | club`) era ambiguo: un usuario puede pertenecer a múltiples grupos y clubes, y no quedaba claro a cuál se refería cada opción.

## Decisión
Reemplazar el modelo de visibilidad por dos campos:

- **visibility**: `private` | `shared`
- **shared_with**: referencia explícita a un Grupo específico o un Club específico (solo cuando `visibility = shared`)

## Consecuencias
- Se elimina la ambigüedad: cada reseña compartida indica exactamente con quién se comparte.
- El schema de base de datos cambia: `resenas.visibilidad` se reemplaza por `resenas.visibility` + `resenas.shared_with_type` + `resenas.shared_with_id`.
- El principio de "visibilidad siempre decidida explícitamente por el autor" (regla de negocio 7) se refuerza con este modelo.
- Un usuario puede crear múltiples reseñas del mismo libro con visibilidades distintas, o una sola reseña compartida con un destino específico.
