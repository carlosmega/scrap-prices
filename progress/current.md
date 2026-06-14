# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** Reconocimiento M1 (Fase 0) **completo**: F010 Home Depot ✅ + F011 Construrama ✅
(docs en `docs/recon/`). `./init.sh` verde.

## Gate humano antes de M2 (scraping real)
1. **Revisión de ToS/robots** de ambos sitios (decisión legal de Carlos) — hoy `scraper_status=paused`.
2. **Home Depot:** técnicamente listo (XHR JSON, sin anti-bot). Endpoint y tienda Monterrey documentados.
3. **Construrama:** precio vía Algolia (`source=xhr`), pero **WAF Imperva** → validar plan A (Algolia
   directo) vs plan B (Playwright); además falta **2ª captura** (store-id del distribuidor + bodies de
   Algolia/setStoresByCity/get-algolia). Ver `docs/recon/construrama.md` §6.

Siguiente `pending`: **F012** (script read-only Fase 1) — BLOQUEADA hasta ToS + (Construrama) 2ª captura.
Luego **M2** (adapters + ingestión + Celery + golden fixtures) reemplaza el `seed`.
