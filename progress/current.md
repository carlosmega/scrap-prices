# Sesión activa — HANDOFF

> El líder mantiene este archivo. Punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 30 `done`, pendientes
`F012` (opcional).

**Estado del arnés:** VERDE. `init.sh --quick` local + **CI en GitHub Actions** en
verde. Backend 171 tests, lint-imports 1/0, contrato sin drift.

## Novedad de esta sesión
- **F026 · ConstruramaAdapter** cerrada (APROBADO 2º ciclo). **Segundo retailer en
  vivo → la comparación cross-retailer real del PRD ya es posible** (Home Depot +
  Construrama). Adapter Algolia respetuoso, parser con golden fixtures de 7 hits
  reales, ingestión `source=xhr`, seed Construrama Monterrey (`scraper_status=active`).
  - **ToS Construrama APROBADO por el humano 2026-07-07.**
  - Fixtures obtenidos con UNA consulta respetuosa en vivo a Algolia (el HAR de
    Chrome no guardó el body de la respuesta — limitación conocida).
  - RECHAZO #1 del reviewer atrapó un bug real (seed `is_primary=False` rompía
    `manage.py scrape`, oculto por los tests); corregido + tests de regresión.
- (Antes en la sesión) 2 hotfixes de arnés (`+x`, docker Fase 2) y **F032 CI**.

## Pendiente operativo (IMPORTANTE)
- **Cambios de F026 SIN commitear** (código backend + seed + fixtures + spec +
  bitácora + feature_list). Listos para `feat(F026): ...`.
- **3 commits de líder locales SIN pushear** (git-push→ask, abre F026, +settings):
  `0d55d9d`, `acc6c9c` y el de ask. Con la regla `ask`, el push pide tu aprobación.
- Committer de la sesión: `M081899@…local` (no enlaza a GitHub `carlosmega`).

## Próximos pasos sugeridos
1. **Corrida real de Construrama (red)** con la search key real en
   `CONSTRURAMA_ALGOLIA_SEARCH_KEY`: `manage.py scrape --retailer construrama
   --zone monterrey-metro --category varilla`. Valida empíricamente que Algolia
   responde a un cliente server-side sin Imperva (recon §5). Si 403 por Referer →
   Plan B Playwright (feature aparte) o `non_viable`.
2. **Matching manual en Admin:** mapear los SKUs reales de Construrama a los
   `CanonicalProduct` y curar `sale_unit`/`mass_kg` (F031) para que la comparación
   **$/kg vs Home Depot** sea real.
3. **Auto-match (rapidfuzz)** para no curar a mano (M5, sin spec).
4. **Deuda F031:** normalizar la cotización (`apps/lists`).
5. `F012` (script recon read-only) opcional.

## Cómo levantar (local)
```bash
./dev-backend.sh    # :8800   ./dev-frontend.sh   # :3300
# corrida real Construrama:
cd backend && CONSTRURAMA_ALGOLIA_SEARCH_KEY=<key> uv run python manage.py scrape \
  --retailer construrama --zone monterrey-metro --category varilla
```
