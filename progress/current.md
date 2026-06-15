# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F028** — Seed con tienda real de HD Monterrey (external_id 1333)
**Spec:** `specs/F028-seed-store-real-hd.md`

## Plan F028 (capa backend → implementer-backend)
Cambiar en `apps/core/services.py::seed_demo` el `external_id` de la RetailerLocation de Home Depot
en Monterrey de `store-2034` (placeholder) → **`1333`** (real, del recon F010). Idempotente. Ajustar test.
Objetivo: que `manage.py scrape --retailer home-depot ...` pegue a la tienda correcta en la corrida real.

**Estado:** F028 `in_progress`. (Tras esto, el humano corre el `--dry-run` de HD.)
