# F027 — Comando `manage.py scrape` (operación del scraping)

> Milestone M2 (operabilidad). Envuelve la ingestión de F025 en un comando cómodo
> y seguro para lanzar la **corrida real** desde el entorno del humano, con `--dry-run`.

## Contexto y objetivo
Dar un único comando para correr el scraping respetuoso por retailer/zona/categoría,
con un modo de prueba (`--dry-run`) que hace el fetch real e imprime lo que traería
**sin escribir** en la BD. Es el enabler para validar Home Depot en vivo.

## Alcance
**Incluye (`apps/scraping/management/commands/scrape.py`):**
- Args: `--retailer <slug>` (req), `--zone <slug>` (req), `--category <txt>` (default `varilla`),
  `--dry-run` (flag).
- Resuelve `Retailer` por slug, `Zone` por slug, y la `RetailerLocation` que sirve esa zona
  (vía `ZoneLocationMap`, la `is_primary`); errores claros si falta algo (`CommandError`).
- **Registro de adapters** retailer-slug → ingestión: `home-depot` → `ingest_homedepot` (F025).
  Slugs sin adapter (p.ej. `construrama` hoy) → mensaje claro "adapter no disponible aún".
- **`--dry-run`:** hace el fetch real vía el adapter (PoliteClient, respetuoso) y **imprime**
  los productos/precios que traería (sku, nombre, precio, disponibilidad), **sin** crear
  `PriceObservation`/`RetailerProduct` ni cerrar un `ScrapeRun` con escritura.
- **Sin `--dry-run`:** ejecuta la ingestión real (PriceObservation + ScrapeRun) y reporta
  el resumen (items, status, errores).
- Respeta los guardrails de F024 (UA honesto, rate-limit, **stop-if-blocked**): si el sitio
  bloquea, imprime el motivo y termina con código de error, **sin evadir**.
- Salida legible (conteos, status del ScrapeRun, primeros N productos).

**No incluye:** programación (Celery beat = M5); adapter de Construrama (F026); endpoints.

## Criterios de aceptación
- [ ] **Backend:** `manage.py scrape --retailer home-depot --zone monterrey-metro --dry-run`
      (con el HTTP **mockeado** en test devolviendo el golden fixture) **imprime** los productos
      y **NO** crea `PriceObservation` ni `RetailerProduct` (test verifica conteos sin cambios).
- [ ] **Backend:** sin `--dry-run` ingiere (crea `PriceObservation` + `ScrapeRun` ok) — test con MockTransport.
- [ ] **Backend:** retailer/zona inexistentes o sin `RetailerLocation` → `CommandError` claro (test).
- [ ] **Backend:** slug sin adapter (`construrama`) → mensaje "no disponible aún", sin reventar.
- [ ] **Backend:** si el fetch devuelve 429/bloqueo → el comando reporta el bloqueo y sale con
      error, **sin reintentar para evadir** (test con MockTransport 429).
- [ ] **Backend:** `ruff`/`pytest` verdes; `makemigrations --check` limpio; contrato sin cambios.

## Plan de verificación
```bash
cd backend && uv run ruff check . && uv run pytest apps/scraping -q
uv run python manage.py makemigrations --check --dry-run
./init.sh   # verde
# Corrida REAL (SOLO entorno del humano, red):
# uv run python manage.py seed
# uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla --dry-run
# (si se ve bien) uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla
```

## Notas y decisiones abiertas
- Los tests son **offline** (HTTP mockeado); la corrida con red real la hace el humano.
- El registro de adapters deja listo el enganche de Construrama (F026) sin tocar el comando.
- En M5, este comando se invoca desde Celery beat para programación periódica.
