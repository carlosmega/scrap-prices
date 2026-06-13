# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F007** — Modelo M0: catálogo (Category, CanonicalProduct, RetailerProduct)
**Spec:** `specs/F007-modelo-catalogo.md`

## Plan F007 (capa única backend → implementer-backend)

- Modelos `Category`, `CanonicalProduct`, `RetailerProduct` heredando `apps.common.models.TimeStampedUUIDModel`.
- Curación manual de SKU en Django Admin (matching CanonicalProduct ↔ RetailerProduct).
- Migraciones commiteadas; tests de relaciones/constraints. Sin endpoints (contrato sin cambios). SQLite.

Cierre: `./init.sh` verde + pytest/ruff/makemigrations --check limpios + review APROBADO.

**Estado:** F007 `in_progress`. Cadena M0: F006 ✅ → **F007** → F008 → F009.
