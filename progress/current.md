# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F011** — Reconocimiento Construrama (Fase 0)
**Spec:** `specs/F011-recon-construrama.md`

## Plan F011 (capa docs)
HAR humano: `docs/recon/har/www.construrama.com.har` (6 MB, 178 entries, 42 JSON; mucho ruido de
analytics). Un subagente lo analiza **offline** y transcribe a `docs/recon/construrama.md`.
Punto clave del PRD §14: **confirmar si el precio es XHR o requiere render JS** (→ source xhr/html/playwright).
ToS = veredicto humano (PENDIENTE). Sin cookies/PII en el .md. Reviewer verifica completitud + privacidad.

**Estado:** F011 `in_progress`. (F010 Home Depot ✅.) Lanzando análisis del HAR.
