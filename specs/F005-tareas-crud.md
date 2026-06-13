# F005 — CRUD de tareas (vertical slice de ejemplo)

> Esta spec existe para demostrar el flujo completo del arnés sobre una
> feature de verdad: backend → contrato → frontend → e2e, con review.

## Contexto y objetivo

Una lista de tareas mínima: crear, listar y marcar como completada. Es el
"hello world" vertical del arnés — suficientemente simple para auditar el
proceso, suficientemente real para ejercitar todas las capas.

## Alcance

**Incluye:** modelo, endpoints CRUD parcial (crear, listar, toggle), UI con
shadcn, test E2E del flujo feliz.
**No incluye:** edición de título, borrado, autenticación, paginación.

## Modelo

`Tarea`: `id` (auto), `titulo` (str, máx 200, requerido), `completada`
(bool, default false), `created_at` (auto).

## Contrato API

| Método | Ruta                     | Request                  | Response                       | Errores |
| ------ | ------------------------ | ------------------------ | ------------------------------ | ------- |
| GET    | /api/tareas              | —                        | `TareaOut[]` (orden: -created) | —       |
| POST   | /api/tareas              | `{"titulo": str}`        | `TareaOut` (201)               | 422 si titulo vacío |
| PATCH  | /api/tareas/{id}/toggle  | —                        | `TareaOut`                     | 404     |

`TareaOut = {"id": int, "titulo": str, "completada": bool, "created_at": datetime}`

## Criterios de aceptación

- [ ] **Backend:** los 3 endpoints implementados en `apps/tareas/` con lógica
      en `services.py`; tests de los 3 casos + el 422 y el 404.
- [ ] **Backend:** `backend/openapi.json` regenerado con los nuevos schemas.
- [ ] **Contrato:** `pnpm gen:api` corrido; el frontend usa `TareaOut` generado.
- [ ] **Frontend:** ruta `/tareas` en `src/features/tareas/`: lista las tareas,
      input + botón para crear, checkbox para toggle. Componentes shadcn:
      Card, Input, Button, Checkbox. Estados de carga y error visibles.
- [ ] **E2E:** test en `e2e/`: crear una tarea con título único, verla en la
      lista, marcarla completada, verificar el estado visual.

## Plan de verificación

```bash
./init.sh --e2e          # todo verde, incluida la suite nueva
cd backend && uv run pytest apps/tareas -q
grep -rn "completada" frontend/src/lib/api/schema.d.ts   # el tipo viene del contrato
```

## Notas y decisiones abiertas

- Sin usuarios: las tareas son globales (es un ejemplo de arnés, no un producto).
