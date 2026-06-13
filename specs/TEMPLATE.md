# <ID> — <Título corto>

> SDD: la spec es el contrato. Si no está aquí, no existe. Si es ambiguo,
> se pregunta al humano ANTES de implementar, no después.

## Contexto y objetivo

2–4 líneas: qué problema resuelve esta feature y para quién.

## Alcance

**Incluye:**
- ...

**No incluye (explícitamente fuera):**
- ...

## Contrato API (si aplica)

| Método | Ruta | Request | Response | Errores |
| ------ | ---- | ------- | -------- | ------- |
| GET    | /api/... | — | `{ ... }` | 404 |

Schemas con campos y tipos exactos. Este bloque es lo que el backend
implementa y lo que el frontend consume vía tipos generados.

## Criterios de aceptación

- [ ] **Backend:** ...
- [ ] **Frontend:** ...
- [ ] **E2E:** ...

Cada criterio debe ser verificable con un comando o una acción concreta.
"Funciona bien" no es un criterio.

## Plan de verificación

Comandos exactos que deben pasar para considerar la feature terminada
(además de `./init.sh` verde):

```bash
# ...
```

## Notas y decisiones abiertas

Dudas que el líder debe resolver con el humano antes de marcar in_progress.
