# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** 🎉 **Bootstrap (F001–F004) + Modelo M0 (F006–F009) COMPLETOS.** Todas APROBADO 1er ciclo,
`./init.sh` verde. El modelo de datos completo de ConstruScan existe: geografía/retailers, catálogo
(+ matching SKU manual), precios/scraping (PriceObservation + ScrapeRun), listas de cotización anónimas.
37 tests backend. Sin features `pending` en `feature_list.json`.

**Siguiente milestone (PRD §13):** M1 (reconocimiento de retailers) / M2 (scrapers + adapters + Celery)
/ M3 (API Ninja + matching) / M4 (UI) / M5 (hardening). Aún sin specs — se generan al arrancar cada uno.
Recordar la estrategia de tests de scrapers (golden fixtures) y Celery eager de `docs/testing-strategy.md`.
