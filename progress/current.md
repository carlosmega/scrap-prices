# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F010** — Reconocimiento Home Depot MX (Fase 0)
**Spec:** `specs/F010-recon-homedepot.md`

## Plan F010 (capa docs)
El humano ya capturó el HAR: `docs/recon/har/www.homedepot.com.mx.har` (8 MB, 188 JSON responses).
- Un subagente analiza el HAR **offline** (scripts, sin leer el HAR crudo en contexto ni pegar a la red)
  y transcribe a `docs/recon/homedepot.md` (desde `docs/recon/TEMPLATE.md`): endpoint XHR de precio +
  forma del payload, mecanismo tienda/cookie, paginación, tienda(s) de Monterrey.
- **Sin cookies/tokens/PII en el doc** (el HAR es gitignored; el .md sí se commitea).
- Sección 0 (ToS): el subagente documenta lo observable (robots, mecanismo); el **veredicto ToS lo
  confirma el humano** (gate §2.3/§14).
- Reviewer verifica completitud (sin TBD en 1–4). Cierre.

**Estado:** F010 `in_progress`. Lanzando análisis del HAR.
