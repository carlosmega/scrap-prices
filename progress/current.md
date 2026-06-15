# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F024** — Infraestructura de scraping (M2)
**Spec:** `specs/F024-scraping-infra.md`

## Decisión (2026-06-15): scraping RESPETUOSO de HD y Construrama
El humano revisó el ToS de **ambos** retailers y determinó que no prohíben la extracción
(su decisión de dueño, como en HD). Se procede con M2, pero **solo de forma respetuosa**:
UA honesto, rate-limit (≥ crawl-delay), backoff, y **stop-if-blocked** (si bloquea → `non_viable`,
no se evade). **NO** se construye disimulo/evasión/anti-captcha/anti-WAF (se mantiene el rechazo previo).
- HD: vía endpoint XHR (payload en el HAR → fixtures listas).
- Construrama: vía **endpoint público de Algolia** (caveat: key de CEMEX; riesgo que asume el humano).
  Hueco técnico: el HAR no guardó el body de Algolia → falta 2ª captura (o ejemplo de corrida en vivo)
  para el parser de F026.
- La corrida REAL (red) corre en el entorno del humano, no en el arnés/CI; los tests son offline.

## Plan M2
F024 infra (base adapter + cliente respetuoso) → F025 HomeDepotAdapter (completo) → F026 Construrama (tras captura Algolia).

**Estado:** F024 `in_progress`. Lanzando implementer-backend (infra, offline).
