# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** Bootstrap (F001–F004) + Modelo M0 (F006–F009) completos y verdes. Specs de **M1
(Reconocimiento)** escritas: F010 (recon HD), F011 (recon Construrama), F012 (script read-only Fase 1).

## ⚠️ M1 tiene GATE HUMANO (no autónomo como M0)
- F010/F011 = **Fase 0 con DevTools humano** (PRD §9.2). El agente NO pega a los retailers;
  el humano captura un **HAR** y el agente lo transcribe a `docs/recon/<retailer>.md` (TEMPLATE listo).
- Gate **ToS/robots** (PRD §2.3 + §14): revisión legal pendiente antes de cualquier request automatizado.
- F012 (script real) **bloqueada** hasta F010+F011 + ToS + acceso de red autorizado.

## Decisión estratégica abierta (preguntada al humano)
M1/M2 (scraping) dependen de recon humano + ToS. **M3 (API) y M4 (UI) SÍ se pueden construir ya**
de forma autónoma contra los modelos M0 usando datos seed/fixtures; el scraping real se enchufa después.
Esperando decisión: (a) humano hace recon M1, o (b) seguir con M3/M4 sobre seed data.
