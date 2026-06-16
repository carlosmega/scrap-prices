# Sesión activa — HANDOFF (pausa 2026-06-16)

> El líder mantiene este archivo. Es el punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 28 `done`, pendientes `F012` (opcional) y `F026` (Construrama, bloqueada).
**Estado del arnés:** `./init.sh --e2e` VERDE (33 ok, 0 fallos, 3 opcionales: jq/docker/infra). Backend 144 tests, vitest 41, E2E 7.

## Qué está hecho (novedad de esta sesión)
- **F031 · M5 Normalización de unidad** (cerrada, APROBADO 1er ciclo). La comparación cross-retailer ya es **real**:
  - Modelo `CanonicalProduct.mass_kg` + `RetailerProduct.sale_unit` (+migración).
  - `apps/catalog/normalization.py::normaliza_precio` puro (kg/tonelada/pieza, parcial sin masa, 2dp ROUND_HALF_UP) con tabla de casos.
  - Búsqueda ordena y elige "menor precio" por **`price_per_kg`** (ya no por el número crudo).
  - Contrato: `PriceByRetailerOut` +`sale_unit`/`price_per_piece`/`price_per_kg`; `CanonicalProduct*Out` +`mass_kg`; `PriceHistoryPointOut` +`sale_unit`.
  - Ingestión HD mapea el código UN/ECE → `sale_unit`. Seed con tabla **NMX** (masa×longitud) + HD→tonelada / CR→kg + historial multiplicativo.
  - UI: titular **$/pieza** + nativo **$/ton** + **$/kg** + badge "mejor precio" + fallback "sin normalizar".
  - Decisiones de producto (unidad pieza+kg, tabla NMX, mostrar nativo) cerradas con el humano el 2026-06-16.
- (Sesiones previas) Bootstrap F001–F004 · Modelo M0 F006–F009 · API M3 F013–F018 · UI M4 F019–F022 · Puertos fijos F023 · Recon M1 F010/F011 · **M2 Home Depot EN VIVO** F024/F025/F027/F028/F029 · F030 fix hydration.

## Próximos pasos (orden sugerido)
1. **Resto de M5** (orden libre, todos features nuevos sin spec aún):
   - **Auto-match (rapidfuzz)** para no curar SKUs a mano.
   - **Celery beat** para programar `scrape` (broker pendiente; hoy Celery no se ejercita en MVP).
   - **CI** (GitHub Actions corriendo `./init.sh`).
   - **Export CSV** de comparación; logging/observabilidad.
2. **Follow-up de F031 (deuda conocida):** normalizar la **cotización** (`apps/lists`). Hoy sigue en precio nativo → "Agregar 1" de un SKU listado por tonelada = 1 tonelada en el carrito. Decidir con el humano si la cantidad va en piezas.
3. **F026 ConstruramaAdapter** — BLOQUEADA: falta que el humano capture el **body de la respuesta de Algolia** (`njvy3eu5dw-dsn.algolia.net`, índice `construrama_mx`) con "Save HAR with content" o un ejemplo en vivo. Sin la forma de `hits[]` no se cierra el parser.
4. `F012` (script recon read-only) opcional.

## Pendiente operativo (esta sesión)
- **Cambios de F031 SIN commitear** (el líder no commitea sin que el humano lo pida). Listo para commit si se desea: migración + modelo/normalización/schema/seed/ingestión/admin (backend), UI + E2E + `schema.d.ts` regenerado (frontend), `openapi.json`, specs/F031, feature_list.json, progress/.

## Cómo levantar (Git Bash)
```bash
./dev-backend.sh    # :8800  (migrate + seed + runserver)
./dev-frontend.sh   # :3300  -> http://localhost:3300
```
Nota: la BD local `db.sqlite3` (gitignored) puede no tener datos reales en sesión nueva. Para precios reales de HD:
```bash
cd backend
uv run python manage.py seed
uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla   # corrida real (red)
# luego matchear los SKUs reales a canónicos y fijar su sale_unit en Admin (curación)
```

## Decisiones / gotchas clave (no perder)
- **Scraping SOLO respetuoso, nunca evasión** (ToS aprobado por el dueño). Ver memoria `scraping-recon-human-gate`.
- **El sandbox del agente SÍ tiene red** → puede correr `scrape`/validar endpoints en vivo (respetuosamente).
- **Matching manual** (MVP); `sale_unit` se cura/confirma en Admin (HD lo autollena desde el código UN/ECE).
- **Comparación = $/kg; titular = $/pieza** (F031). `mass_kg` (tabla NMX) editable en Admin; null ⇒ "sin normalizar".
- SQLite/sin-Docker (MVP); contrato OpenAPI→tipos sin drift; arquitectura limpia con greps en `init.sh` + import-linter/ESLint.
- Traza completa en `progress/history.md`; specs en `specs/`; recon en `docs/recon/`.
