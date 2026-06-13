# F009 — Modelo de listas de cotización (anónimo / sesión)

> SDD: la spec es el contrato. Deriva del PRD §8 (entidades de usuario) y
> Épica C. Depende de F006 (`Zone`) y F007 (`RetailerProduct`).

## Contexto y objetivo

La "lista de cotización" es el carrito propio del usuario: agrega productos con
cantidad y guarda un **snapshot** del precio al momento (no cambia si el precio
luego cambia). Por **decisión de producto, el MVP es anónimo/sesión**: la lista
se identifica por un token de sesión, sin login ni `User` de Django obligatorio.

## Alcance

**Incluye:**
- Modelos `UserList`, `UserListItem`.
- Migraciones.
- **Django Admin** de ambos (inspección interna).
- Tests de modelo: snapshot de precio, totales, asociación a zona.

**No incluye (explícitamente fuera):**
- Endpoints Ninja de listas/ítems (M4 / F-posteriores).
- Login propio de usuarios (decisión de producto: diferido a fase posterior).
- Export CSV/Excel (M5, backlog).
- Cálculo de totales como endpoint (en MVP el total se deriva en servicio/UI).

## Modelo (campos exactos, PRD §8, adaptado a auth anónima)

Heredan la base de F006 (UUID/timestamps/`is_active`).

**`UserList`** — la lista de cotización:
`session_key` (str, indexado; identifica la sesión anónima propietaria),
`name` (str, blank; default p. ej. "Mi cotización"), `zone` (FK→Zone, null,
blank, related_name `user_lists`), `status` (str/choices, ej. `open`, default
`open`).
- **Nota auth:** se omite `user_fk` en MVP. Si en fase posterior se añade login,
  se agrega `user` (FK→User, null) sin romper este contrato.

**`UserListItem`**:
`user_list` (FK→UserList, related_name `items`), `retailer_product`
(FK→RetailerProduct, related_name `list_items`), `quantity` (PositiveInteger,
default 1), `captured_price` (Decimal, max_digits 12, decimal_places 2;
**snapshot**), `captured_at` (DateTime; **snapshot** del momento de agregado),
`notes` (str, blank).

### Relaciones clave
- `UserList` *1↔N* `UserListItem`.
- El ítem referencia `RetailerProduct` (precio de un retailer concreto, CA1 de C1).

## Criterios de aceptación

- [ ] **Backend:** ambas entidades en `models.py` heredando la base; `migrate`
      limpio; `session_key` indexado.
- [ ] **Backend:** Admin de `UserList` (inline de `UserListItem`) navegable.
- [ ] **Backend:** tests que: crean una `UserList` con `session_key` y `zone`,
      agregan dos `UserListItem` con `captured_price`/`captured_at`, y verifican
      que cambiar el precio del `RetailerProduct`/sus observaciones **no** altera
      el `captured_price` del ítem (snapshot inmutable, CA2 de C1).
- [ ] **Backend:** test que calcula el subtotal de la lista (suma
      `quantity * captured_price`) en una función de `services.py` (la lógica no
      vive en el modelo ni en un router).
- [ ] **Backend:** `uv run pytest` pasa, `ruff check .` limpio,
      `makemigrations --check --dry-run` limpio.
- [ ] **Backend:** no cambia el contrato OpenAPI (sin endpoints).

## Plan de verificación

```bash
cd backend && uv run python manage.py migrate
uv run pytest apps -q
uv run ruff check . && uv run python manage.py makemigrations --check --dry-run
./init.sh   # verde
```

## Notas y decisiones abiertas

- El `captured_price` se copia explícitamente al crear el ítem; nunca se lee en
  vivo del `RetailerProduct`. Es el corazón de la garantía de snapshot (CA2).
- `session_key` será provisto por el frontend/sesión en M4; aquí solo se modela
  y se indexa. La gestión de cómo se emite el token es de la feature de API.
