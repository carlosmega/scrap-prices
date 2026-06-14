# F014 — API de zonas (Django Ninja)

> Milestone M3. Deriva del PRD §12 (endpoints) y Épica A (ubicación/zona).
> Primera feature que añade endpoints Ninja → activa el flujo contract-first.

## Contexto y objetivo
La UI (M4) necesita listar zonas activas y resolver la zona del usuario por
ubicación. Esta feature expone esos dos endpoints sobre los modelos de F006,
con los datos sembrados por F013.

## Contrato API
| Método | Ruta | Request | Response | Errores |
| ------ | ---- | ------- | -------- | ------- |
| GET | /api/zones | — | `ZoneOut[]` (solo `is_active`, orden por `name`) | — |
| POST | /api/zones/resolve | `{"lat": float, "lng": float}` | `ZoneOut` (zona activa más cercana al centroide) | 404 `{detail}` si no hay cobertura |

`ZoneOut = {"id": uuid(str), "name": str, "slug": str, "state": str}`

- `resolve` calcula la zona activa más cercana por distancia al `centroid_lat/lng`
  (haversine o euclídea simple sobre lat/lng; MVP no requiere PostGIS). Si no hay
  zonas activas con centroide, responde 404 "aún sin cobertura" (Épica A · CA4).
- Resolución por **dirección** (geocoding) se difiere (nota); MVP usa lat/lng.

## Alcance
**Incluye:** `apps/geo/api.py` (router, SIN ORM), `apps/geo/schemas.py` (`ZoneOut`,
`ResolveIn`), lógica de resolución en `apps/geo/services.py`, montaje del router en
`config/api.py`. Regeneración de `backend/openapi.json`. En frontend: `pnpm gen:api`
para sincronizar `schema.d.ts` (sin UI todavía; la UI es F019).
**No incluye:** UI; geocoding de direcciones; PostGIS.

## Criterios de aceptación
- [ ] **Backend:** GET /api/zones devuelve las zonas activas (con F013 sembrado, ≥1)
      como `ZoneOut[]`; lógica de orden/filtrado vía services, router delgado sin ORM.
- [ ] **Backend:** POST /api/zones/resolve con coords de Monterrey (~25.68,-100.31)
      devuelve "Monterrey Metro"; con coords lejanas sin cobertura → 404.
- [ ] **Backend:** tests de ambos endpoints (incl. el 404) usando datos del `seed`
      o factories; `response=` con schema explícito; fallan sin la implementación.
- [ ] **Backend:** `backend/openapi.json` regenerado con los nuevos paths/schemas.
- [ ] **Contrato:** `pnpm gen:api` corrido; `schema.d.ts` incluye `ZoneOut` y las
      rutas; Fase 5 de `init.sh` sin drift.
- [ ] `./init.sh` verde; ruff/pytest/tsc/lint/build limpios.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps/geo -q
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
cd ../frontend && pnpm gen:api
cd .. && ./init.sh   # Fase 5 sin drift, verde
```

## Notas y decisiones abiertas
- Formato de error: Ninja devuelve `{"detail": ...}` por defecto; el 404 de
  "sin cobertura" usa ese formato (ver `docs/testing-strategy.md`).
- `resolve` por dirección/geocoding: feature posterior (M5 o cuando se requiera).
