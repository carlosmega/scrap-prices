# F011 — Reconocimiento Construrama (Fase 0)

> Deriva del PRD §9.1 (hallazgos Construrama), §9.2 (Fase 0), §10, §14.
> Milestone M1. **Feature con gate humano** — ver Bloqueo. Análoga a F010.

## Contexto y objetivo
Documentar cómo Construrama (`construrama.com`, red CEMEX) sirve precios por zona.
Plataforma unificada con **subpath por distribuidor** (`construrama.com/{distribuidor}/`)
y selector de ciudad/zona por cookie de sesión (§9.1). Falta confirmar (§14) el
mecanismo exacto (XHR vs render JS) y qué distribuidor(es) sirven Monterrey Metro.

## Alcance
**Incluye:** `docs/recon/construrama.md` (desde el TEMPLATE) con secciones
obligatorias llenas: gate ToS/robots, mecanismo subpath-distribuidor + selector
ciudad/cookie, **XHR vs render** confirmado, endpoint(s)/forma de payload o, si es
render, marcar `source=playwright`; categoría "varilla"; distribuidor(es) que
sirven Monterrey Metro.
**No incluye:** sitios de distribuidores **independientes** fuera de
`construrama.com` (§2.4 — distinto CMS, backlog); ingesta; adapters.

## Bloqueo / precondición humana (LÉASE PRIMERO)
Igual que F010: DevTools/HAR humano + gate ToS. El agente analiza el HAR y
transcribe; NO pega a `construrama.com`. Punto extra a confirmar: si el precio
solo aparece tras render JS, el adapter de M2 usará Playwright (último recurso,
§9.3) y se documenta como tal.

## Criterios de aceptación
- [ ] Existe `docs/recon/construrama.md` siguiendo el TEMPLATE, sin "TBD" en 0–4.
- [ ] Gate ToS/robots (sección 0) resuelto + `scraper_status` propuesta.
- [ ] Mecanismo de zona confirmado: subpath de distribuidor + cómo se fija la
      ciudad/zona; y si los precios son XHR o requieren render (`source`).
- [ ] Lista el/los distribuidor(es) Construrama (slug/subpath) que sirven
      Monterrey Metro → insumo para `RetailerLocation`/`ZoneLocationMap`.

## Plan de verificación
Completitud del entregable (no `./init.sh`):
```bash
test -f docs/recon/construrama.md && ! grep -qi "TBD" docs/recon/construrama.md
```

## Notas y decisiones abiertas
- Confirmar el supuesto del §14 (XHR vs render). De eso depende si el adapter de
  Construrama es httpx+selectolax o Playwright.
- Si bloquea o ToS lo prohíbe → `non_viable`, se omite.
