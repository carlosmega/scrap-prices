# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F009** — Modelo M0: listas de cotización anónimas
**Spec:** `specs/F009-modelo-listas-cotizacion.md`

## Plan F009 (capa única backend → implementer-backend)

- `UserList` (lista de cotización; **anónima/sesión** — `user_fk` NO obligatorio en MVP, decisión de producto) y `UserListItem` (item con cantidad + snapshot de precio).
- Heredan `apps.common.models.TimeStampedUUIDModel`. Migraciones commiteadas; Admin; tests.
- Sin endpoints (contrato sin cambios). SQLite.

Cierre: `./init.sh` verde + pytest/ruff/makemigrations --check limpios + review APROBADO.

**Estado:** F009 `in_progress`. Cadena M0: F006 ✅ F007 ✅ F008 ✅ → **F009** (última de M0).
