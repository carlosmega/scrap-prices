# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F008** — Modelo M0: precios y auditoría de scraping
**Spec:** `specs/F008-modelo-precios-scraping.md`

## Plan F008 (capa única backend → implementer-backend)

- `PriceObservation` (histórico de precios, `price` Decimal, `source` xhr/html/playwright, `captured_at`, `raw_payload` JSON) e índice compuesto `(retailer_product, zone, -captured_at)`.
- `ScrapeRun` (auditoría de corrida: status ok/partial/failed, items_found, errors). Depende de F006 (Zone, Retailer, RetailerLocation) y F007 (RetailerProduct).
- Admin de ambos; tests incluyendo la consulta "última observación por producto+zona" y un ScrapeRun partial con errors. Sin endpoints (contrato sin cambios). SQLite.

Cierre: `./init.sh` verde + pytest/ruff/makemigrations --check limpios + review APROBADO.

**Estado:** F008 `in_progress`. Cadena M0: F006 ✅ F007 ✅ → **F008** → F009.
