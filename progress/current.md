# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F019** — UI selección de zona (persistente)
**Spec:** `specs/F019-ui-seleccion-zona.md`

## Plan F019 (capas frontend + e2e → implementer-frontend)
- Shell de la home + selector de zona (Client Component) con `fetchZones()`; estados carga/error/datos.
- `useSelectedZone()` persistente en localStorage (sobrevive recarga). Limpia placeholder de F003.
- Opcional: "usar mi ubicación" → POST /api/zones/resolve, 404 → "sin cobertura".
- E2E: webServer backend corre migrate+seed; test elige "Monterrey Metro" y verifica persistencia.

Cierre: `./init.sh --e2e` verde (Fase 6) + tsc/lint/build/test:unit + review APROBADO.

**Estado:** F019 `in_progress`. Inicio de M4 (UI). Cadena: F019 → F020 → F021 → F022.
