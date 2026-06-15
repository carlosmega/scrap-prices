# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** **M2 — Home Depot completo** (F024 infra + F025 adapter/ingestión/Celery). Scraper
respetuoso (UA honesto, rate-limit, stop-if-blocked), parser probado offline con golden fixtures
del HAR; ingestión a `PriceObservation` + `ScrapeRun`. `./init.sh` verde (110 tests backend).

## Pendiente
- **F026 ConstruramaAdapter (Algolia): BLOQUEADA** por hueco técnico — el HAR no guardó el body
  de la respuesta de Algolia (`njvy3eu5dw-dsn.algolia.net`), así que falta la forma real de `hits[]`
  para escribir/probar el parser. Necesita: 2ª captura que guarde esa respuesta, o un ejemplo de la
  1ª corrida en vivo en el entorno del humano.
- **Corrida real HD:** se ejecuta en el entorno del humano (red), con delay ≥7s; el arnés solo
  construye/prueba offline. (Comando de ingestión vía shell/management.)
- Otras pendientes: F012 (script recon, opcional), M5 (Celery beat, CI, logging, fuzzy matching).
