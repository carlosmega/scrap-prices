# F010 — Reconocimiento Home Depot México (Fase 0)

> Deriva del PRD §9.1 (hallazgos HD), §9.2 (Fase 0), §10 (zonas), §14 (pendientes).
> Milestone M1. **Feature con gate humano** — ver Bloqueo.

## Contexto y objetivo
Documentar, sobre hechos verificados, cómo Home Depot México sirve precios por
zona, para que el `HomeDepotAdapter` de M2 se escriba sin adivinar. El precio de
HD viene por XHR/JS dependiente de tienda + cookie (§9.1); hay que confirmar el
endpoint exacto, la forma del payload y qué tienda(s) sirven Monterrey Metro.

## Alcance
**Incluye:** un documento de reconocimiento `docs/recon/homedepot.md` (desde
`docs/recon/TEMPLATE.md`) con TODAS sus secciones obligatorias llenas: gate
ToS/robots, mecanismo de zona/cookie, endpoint(s) XHR de precio + forma del
payload, paginación de la categoría "varilla", y la(s) tienda(s) HD que sirven
Monterrey Metro (`external_id`/store_id).
**No incluye:** pegar a HD de forma programada, ingesta de datos, adapters,
endpoints (eso es M2/M3). No se hace login ni se evade anti-bot (§2.3).

## Bloqueo / precondición humana (LÉASE PRIMERO)
Esta feature **no la puede completar un agente de forma autónoma**:
1. **Trabajo de DevTools humano:** la captura del tráfico real la hace Carlos en
   su navegador (sesión normal de usuario). El agente NO pega a `homedepot.com.mx`.
2. **División de trabajo recomendada:** el humano exporta un **HAR** de la sesión
   (DevTools → Network → Save all as HAR) tras buscar "varilla" con una tienda de
   Monterrey seleccionada; el agente analiza ese HAR y transcribe los hallazgos al
   doc. Así el agente aporta valor sin tocar el sitio.
3. **Gate ToS/robots (§14):** la revisión de Términos de Servicio debe hacerse y
   registrarse en la sección 0 del doc antes de pasar a F012/M2.

## Criterios de aceptación
- [ ] Existe `docs/recon/homedepot.md` siguiendo el TEMPLATE, sin "TBD" en las
      secciones 0–4.
- [ ] El gate ToS/robots (sección 0) está resuelto con veredicto explícito y la
      `scraper_status` propuesta (`active`/`paused`/`non_viable`).
- [ ] Documenta al menos un endpoint XHR de precio con su forma de payload
      (ejemplo recortado, sin PII) y cómo se fija la tienda/zona.
- [ ] Lista la(s) tienda(s) HD (store_id) que sirven Monterrey Metro → insumo
      para `RetailerLocation`/`ZoneLocationMap`.

## Plan de verificación
La verificación es de **completitud del entregable**, no de `./init.sh` (esta
feature no toca código). El reviewer comprueba que el doc existe y cubre las
secciones obligatorias sin marcadores TBD, y que el veredicto ToS está registrado.
```bash
test -f docs/recon/homedepot.md && ! grep -qi "TBD" docs/recon/homedepot.md
```

## Notas y decisiones abiertas
- Si HD bloquea o el ToS lo prohíbe → `non_viable`; se documenta y se omite, no se
  fuerza (§2.3.1/2.3.7). En ese caso M2 para HD queda fuera de alcance.
- Sin HAR ni recon humano, esta feature queda `blocked`: el líder NO debe lanzar
  un implementer a "scrapear" el sitio.
