# F018 — API de retailers (interno)

> Milestone M3. PRD §12 (`GET /api/retailers` interno), Épica D2 (monitoreo de
> scrapers). Último endpoint de M3.

## Contexto y objetivo
Endpoint de soporte/diagnóstico que lista los retailers y el estado de su scraper,
para que la UI/operador vea de un vistazo qué fuentes están activas/pausadas/no
viables (complementa el Django Admin de `ScrapeRun`).

## Contrato API
| Método | Ruta | Request | Response | Errores |
| ------ | ---- | ------- | -------- | ------- |
| GET | /api/retailers | — | `RetailerOut[]` (orden por `name`) | — |

```
RetailerOut = {
  "id": str, "name": str, "slug": str,
  "pricing_model": str,        # zone_cookie | distributor_subpath
  "scraper_status": str,       # active | paused | non_viable
  "is_active": bool
}
```

- Lista todos los retailers (incluye `is_active=false` para diagnóstico), orden por `name`.
- Endpoint de lectura simple; sin filtros en MVP.

## Alcance
**Incluye:** endpoint en `apps/geo/api.py` (los retailers viven en `apps/geo`),
schema `RetailerOut` en `schemas.py`, lógica en `services.py`. Regenera
`openapi.json`; frontend `pnpm gen:api`.
**No incluye:** UI; autenticación/permiso de "interno" (MVP sin auth; se endurece
cuando exista login, RNF/§14); endpoints de escritura de retailers (eso es Admin).

## Criterios de aceptación
- [ ] **Backend:** `GET /api/retailers` (con `seed`) devuelve Home Depot y Construrama
      como `RetailerOut[]` con su `scraper_status` y `pricing_model`, orden por `name`.
- [ ] **Backend:** router sin ORM, lógica en `services.py`, `response=` explícito.
- [ ] **Backend:** test del endpoint (≥2 retailers, campos correctos, orden); falla sin la implementación.
- [ ] **Backend:** `openapi.json` regenerado. **Contrato:** `pnpm gen:api`, Fase 5 sin drift.
- [ ] `./init.sh` verde; ruff/pytest/tsc/lint/build limpios.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps/geo -q
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
cd ../frontend && pnpm gen:api && cd .. && ./init.sh
```

## Notas y decisiones abiertas
- "Interno": en MVP sin auth, el endpoint es público; cuando exista login/roles, se
  protege (admin/staff). Anotarlo como deuda hasta entonces.
