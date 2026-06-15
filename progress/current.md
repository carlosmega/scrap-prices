# Sesión activa — HANDOFF (pausa 2026-06-15)

> El líder mantiene este archivo. Es el punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 28 `done`, pendientes `F012` (opcional) y `F026` (Construrama).
**Estado del arnés:** `./init.sh --e2e` VERDE. ~58 commits, todo revisado feature por feature.

## Qué está hecho
- **Bootstrap** F001–F004 · **Modelo M0** F006–F009 · **API M3** F013–F018 · **UI M4** F019–F022 · **Puertos fijos** F023 (backend `:8800`, frontend `:3300`).
- **Recon M1** F010 (Home Depot) + F011 (Construrama) desde HARs del humano → `docs/recon/`.
- **M2 Home Depot — funcionando EN VIVO con datos reales:** F024 infra respetuosa (UA honesto, rate-limit, stop-if-blocked, **sin evasión**) + F025 adapter + F027 `manage.py scrape` + F028 tienda real `1333` + F029 params de búsqueda (profileName/marketId/stLocId, hallado en corrida en vivo). El `scrape` real trajo 13 precios reales de HD; 8 varillas matcheadas a mano → visibles en la app.
- **F030** fix de hydration mismatch (hooks de localStorage SSR-safe con `useSyncExternalStore`) + guardia E2E.

## Próximos pasos (orden sugerido)
1. **Normalización de unidad (M5)** — HD vende varilla por **tonelada** ($20,068), Construrama por **kg**, seed por **pieza**. Sin esto, la comparación cross-retailer NO es válida. Feature de mayor valor.
2. **F026 ConstruramaAdapter** — BLOQUEADO: falta que el humano capture el **body de la respuesta de Algolia** (`njvy3eu5dw-dsn.algolia.net`, índice `construrama_mx`) con "Save HAR with content", o un ejemplo de corrida en vivo. El parser de Construrama no se puede cerrar sin esa forma de `hits[]`.
3. **M5 resto:** auto-match (rapidfuzz), Celery beat (programar `scrape`), CI (GitHub Actions con `./init.sh`), logging/observabilidad, export CSV. `F012` (script recon) opcional.

## Cómo levantar (Git Bash)
```bash
./dev-backend.sh    # :8800  (migrate + seed + runserver)
./dev-frontend.sh   # :3300  -> http://localhost:3300
```
Nota: la BD local `db.sqlite3` (gitignored) puede no tener datos reales en sesión nueva.
Para restaurar la vista con precios reales de HD:
```bash
cd backend
uv run python manage.py seed
uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla   # corrida real (red)
# luego matchear los SKUs reales a canónicos (curación; ver progress/history.md F-matching o script ad-hoc)
```
Servidores de dev de esta sesión: pueden seguir corriendo en background; si no, reiniciar con los scripts.

## Decisiones / gotchas clave (no perder)
- **Scraping SOLO respetuoso, nunca evasión** (el dueño aprobó el ToS de ambos; pidió disimulo una vez → rechazado y se mantiene). Ver memoria `scraping-recon-human-gate`.
- **El sandbox del agente SÍ tiene red** → el agente puede correr `scrape`/validar endpoints en vivo (respetuosamente).
- **Matching es manual** (MVP); los SKUs reales matcheados viven solo en `db.sqlite3` local (no commiteado).
- SQLite/sin-Docker (MVP); contrato OpenAPI→tipos sin drift; arquitectura limpia con greps en `init.sh` + import-linter/ESLint.
- Traza completa en `progress/history.md`; specs en `specs/`; recon en `docs/recon/`.
