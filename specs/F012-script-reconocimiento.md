# F012 — Script de reconocimiento read-only (Fase 1)

> Deriva del PRD §9.2 (Fase 1). Milestone M1. **Bloqueada** hasta F010+F011 y el
> gate ToS. Confirma de forma reproducible —sin ingesta— lo documentado en Fase 0.

## Contexto y objetivo
Un script read-only que confirma, contra los retailers reales, que (a) los
endpoints documentados en `docs/recon/*.md` responden y (b) el cambio de zona
funciona de forma reproducible. **No ingesta** a `PriceObservation`: solo imprime
lo que ve, para validar la Fase 0 antes de construir los adapters de M2.

## Alcance
**Incluye:** un script (en `backend/`, p.ej. `apps/scraping/recon.py` + un
management command `recon`) que, dada una `RetailerLocation` de Monterrey, fija la
zona y obtiene 1–2 precios de "varilla" por retailer, imprimiéndolos (no guarda).
Respeta TODOS los guardrails: delay mínimo por dominio, User-Agent honesto,
`tenacity` con backoff, sin login, sin evasión anti-bot, honra `robots.txt`.
**No incluye:** ingesta, `ScrapeRun`, Celery, adapters completos, endpoints API
(eso es M2/M3).

## Bloqueo / precondiciones (LÉASE PRIMERO)
1. **F010 y F011 `done`**: el script implementa exactamente los endpoints/mecanismos
   ya documentados; sin Fase 0 no hay qué reproducir.
2. **Gate ToS/robots resuelto** (secciones 0 de los docs de recon) con veredicto
   `active`. Si algún retailer quedó `non_viable`, se excluye del script.
3. **Acceso de red a los retailers** desde donde corra el script. Los agentes del
   arnés normalmente NO tienen (ni deben usar) ese acceso: este script lo corre el
   humano o un entorno autorizado, no el implementer en CI.

## Criterios de aceptación
- [ ] `uv run python manage.py recon --retailer homedepot --location <id>` imprime
      al menos un precio de "varilla" para una tienda de Monterrey (cuando HD es viable).
- [ ] Ídem Construrama (si viable).
- [ ] El script aplica delay configurable (> 0) y User-Agent honesto; código sin
      login ni evasión. Lógica en `services.py`/módulo de scraping, no en `api.py`.
- [ ] NO escribe en la DB (sin `.save()`/`.create()` de `PriceObservation`); es read-only.
- [ ] `uv run ruff check .` y `uv run pytest` limpios (tests con el HTTP **mockeado**,
      sin red real — golden fixtures, ver `docs/testing-strategy.md`).

## Plan de verificación
- Tests unitarios: el parser corre contra **fixtures grabados** (sin red); pasan en `./init.sh`.
- La corrida real contra los retailers la ejecuta el humano/entorno autorizado
  (no el reviewer en el arnés), y se anexa su output a `docs/recon/*.md`.

## Notas y decisiones abiertas
- Este es el puente a M2: cuando el script confirma Fase 0, los adapters
  (`HomeDepotAdapter`/`ConstruramaAdapter`) reutilizan su lógica de fijar-zona +
  parsear, ya con ingesta a `PriceObservation` y `ScrapeRun`.
- La parte testeable en el arnés (parsers + fixtures) SÍ es autónoma; la parte de
  red real NO. Separar ambas en el diseño.
