# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F027** — Comando `manage.py scrape` (M2 operabilidad)
**Spec:** `specs/F027-cmd-scrape.md`

## Plan F027 (capa backend → implementer-backend)
Comando `scrape --retailer --zone --category --dry-run` que envuelve la ingestión de F025:
resuelve Retailer/Zone/RetailerLocation, registro de adapters (home-depot→ingest_homedepot;
construrama→"no disponible aún"), `--dry-run` hace fetch real e imprime sin escribir, respeta
stop-if-blocked. Tests offline (MockTransport + golden fixture): dry-run no escribe, real ingiere,
errores claros, 429→reporta sin evadir.

Objetivo: dar al humano un comando seguro para la **corrida real de Home Depot** en su entorno.

**Estado:** F027 `in_progress`. M2: F024 ✅ F025 ✅ → **F027** (comando). F026 Construrama pendiente de captura Algolia.
