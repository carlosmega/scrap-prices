# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F006** — Modelo M0: base abstracta + geografía y retailers
**Spec:** `specs/F006-modelo-geografia-retailers.md`

## Plan F006 (capa única backend → implementer-backend)

- Base abstracta `TimeStampedUUIDModel` (UUID PK, created_at/updated_at, is_active soft-delete) — contrato para F007–F009.
- Modelos `Retailer`, `RetailerLocation`, `Zone`, `ZoneLocationMap` (N↔N Zone↔RetailerLocation vía el map; `unique_together`).
- Migraciones commiteadas; Django Admin de las 4 entidades; tests de relaciones + `unique_together` + `is_primary`.
- Sin endpoints Ninja (el contrato OpenAPI NO cambia). SQLite/sin-Docker.

Cierre: `./init.sh` verde (Fase 3) + pytest/ruff/makemigrations --check limpios + review APROBADO.

**Estado:** F006 `in_progress`. Lanzando `implementer-backend`. (Cadena M0: F006→F007→F008→F009.)
