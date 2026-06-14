# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F013** — Seed de datos demo (Monterrey Metro · varilla)
**Spec:** `specs/F013-seed-datos-demo.md`

## Camino elegido por el humano: M3/M4 con seed data (autónomo)
M1/M2 (scraping) diferidos al recon humano + ToS. Construyo la app contra los modelos M0
con datos sembrados. Roadmap en `feature_list.json`: M3 API (F013–F018) → M4 UI (F019–F022),
luego M1 recon (F010–F012, gated) al final.

## Plan F013 (capa única backend → implementer-backend)
Management command `seed` idempotente que crea el grafo PRD para Monterrey Metro/varilla
(retailers, locations, zona, map, categoría, canónicos, retailer products matcheados, price
observations con historial). Sin endpoints. SQLite.

**Estado:** F013 `in_progress`. Lanzando `implementer-backend`.
