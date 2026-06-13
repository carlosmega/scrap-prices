# F006 — Base + modelo de geografía y retailers

> SDD: la spec es el contrato. Deriva del PRD §8 (modelo de datos) y §10
> (normalización de zonas). Primera feature de dominio: establece la base
> abstracta que reutilizan F007–F009.

## Contexto y objetivo

ConstruScan compara precios por **zona**. La zona del usuario no es comparable
directamente entre retailers (HD usa tienda+cookie; Construrama usa
distribuidor+ciudad), así que se normaliza con una `Zone` interna mapeada a las
ubicaciones físicas de cada retailer. Esta feature crea esa fundación de datos
y la base abstracta común a todo el dominio.

## Alcance

**Incluye:**
- App Django `apps/geo/` (o `apps/catalog/` según convención del repo; ver Notas).
- **Modelo base abstracto** reutilizable: PK `UUID`, `created_at`/`updated_at`
  (auto), `is_active` (bool, default true, soft-delete). Convención del equipo
  estilo CDS/Dynamics (PRD §8).
- Modelos `Retailer`, `RetailerLocation`, `Zone`, `ZoneLocationMap`.
- Migraciones.
- Registro en **Django Admin** de las 4 entidades, navegable y editable.
- Tests de modelo (creación, relaciones, soft-delete).

**No incluye (explícitamente fuera):**
- Cualquier endpoint Ninja (la API de zonas es M3 / F-posteriores).
- Resolución de zona por lat/lng (eso es lógica de servicio en M3).
- Datos seed de Monterrey Metro (carga de datos es tarea aparte / Admin manual).

## Modelo (campos exactos, PRD §8)

**Base abstracta `TimeStampedUUIDModel`** (`abstract = True`):
`id` (UUIDField, PK, default uuid4, editable=False), `created_at`
(auto_now_add), `updated_at` (auto_now), `is_active` (Bool, default True).

**`Retailer`** (hereda base):
`name` (str), `slug` (slug, unique), `base_url` (URL), `pricing_model`
(choices: `zone_cookie` | `distributor_subpath`), `scraper_status`
(choices: `active` | `paused` | `non_viable`, default `active`).

**`RetailerLocation`** (hereda base) — tienda HD o distribuidor Construrama:
`retailer` (FK→Retailer, related_name `locations`), `external_id` (str;
store_id HD / slug distribuidor), `name` (str), `subpath` (str, blank;
ej. `/materialesmonterrey`), `address` (str, blank), `city` (str), `state`
(str), `lat` (Decimal/Float, null), `lng` (Decimal/Float, null).

**`Zone`** (hereda base) — zona interna normalizada:
`name` (str), `slug` (slug, unique), `state` (str), `centroid_lat`
(null), `centroid_lng` (null).

**`ZoneLocationMap`** (hereda base) — resuelve qué ubicación sirve a una zona:
`zone` (FK→Zone, related_name `location_maps`), `retailer_location`
(FK→RetailerLocation, related_name `zone_maps`), `is_primary` (bool, default
false). `unique_together = (zone, retailer_location)`.

### Relaciones clave
- `Zone` *N↔N* `RetailerLocation` vía `ZoneLocationMap`.
- `Retailer` *1↔N* `RetailerLocation`.

## Criterios de aceptación

- [ ] **Backend:** las 4 entidades + base abstracta en `apps/<app>/models.py`;
      `makemigrations` genera migración y `migrate` corre limpio contra
      SQLite (default del MVP; sin Docker).
- [ ] **Backend:** las 4 entidades registradas en `admin.py` y visibles/editables
      en `/admin/` (con `list_display` y `list_filter` razonables; al menos
      `scraper_status` filtrable en Retailer).
- [ ] **Backend:** tests en `apps/<app>/tests/` que crean un `Retailer` con
      `RetailerLocation`, una `Zone`, y un `ZoneLocationMap` que los une;
      verifican `is_primary` y el `unique_together`.
- [ ] **Backend:** `uv run pytest` pasa, `uv run ruff check .` limpio,
      `makemigrations --check --dry-run` limpio.
- [ ] **Backend:** no se añade ningún router/endpoint; el contrato OpenAPI no
      cambia (esta feature no toca la capa de contrato).

## Plan de verificación

```bash
cd backend && uv run python manage.py migrate   # SQLite por defecto, sin Docker
uv run pytest apps -q
uv run ruff check . && uv run python manage.py makemigrations --check --dry-run
# Crear superuser y verificar Admin navegable manualmente en /admin/
./init.sh   # verde
```

## Notas y decisiones abiertas

- **Nombre de la app:** el implementer elige `apps/geo/` o agrupa en
  `apps/catalog/`; debe ser coherente con `backend/CLAUDE.md` y dejar espacio a
  que F007 (catálogo) y F008 (precios) vivan en apps propias o compartidas.
- El **modelo base abstracto** creado aquí es el contrato para F007–F009: todas
  las entidades de dominio heredan de él. Si el implementer lo ubica en un
  módulo común (`apps/common/models.py`), documentarlo en el informe.
- Auth: por decisión de producto el MVP es **anónimo/sesión**; `Zone` no
  referencia usuarios.
