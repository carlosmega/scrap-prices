# Estrategia de pruebas — ConstruScan sobre el arnés

> Extiende `docs/verification.md` (los niveles `--quick/--full/--e2e`) con la
> **pirámide concreta** de ConstruScan. Regla madre del arnés intacta: la
> palabra del agente no es evidencia; evidencia = output de un comando, y un
> test que nace verde no prueba nada (debe fallar sin la implementación).

## La pirámide (de más a menos, de rápido a lento)

```
                ╱╲   E2E (Playwright)         pocos, flujo feliz por slice vertical
               ╱──╲  Integración backend      endpoints Ninja + servicios + DB real
              ╱────╲ Unit frontend (Vitest)   componentes/hooks aislados
             ╱──────╲Unit backend (pytest)    modelos, servicios, parsers de scraper
            ╱────────╲Estático                 tsc --noEmit · ruff · ESLint · mypy?
```

Cada capa tiene un **dueño de comando** y una **fase de `init.sh`** que la ejerce.
Nada es "estrategia de papel": si no lo corre `init.sh`, no cuenta.

| Capa | Comando canónico | Fase init.sh | Capa/dir |
| --- | --- | --- | --- |
| Estático backend | `uv run ruff check .` | Fase 3 | `backend/` |
| Unit + integración backend | `uv run pytest -q` | Fase 3 | `backend/apps/<dom>/tests/` |
| Estático frontend | `pnpm exec tsc --noEmit && pnpm lint` | Fase 4 | `frontend/` |
| **Unit frontend (Vitest)** | `pnpm test:unit` | Fase 4 | `frontend/**/__tests__` o `*.test.ts(x)` |
| Build | `pnpm build` | Fase 4 | `frontend/` |
| Contrato | regen + `diff -q` | Fase 5 | — |
| **E2E (Playwright)** | `pnpm test:e2e` | Fase 6 | `e2e/` |

## ⚠️ Los DOS Playwright (no confundir)

ConstruScan usa Playwright en dos sitios que **no se mezclan**:

| | Playwright de **testing** | Playwright de **scraping** |
| --- | --- | --- |
| Para qué | E2E del flujo de usuario | Último recurso para scrapear JS pesado |
| Dónde vive | `e2e/` (capa e2e) | adapters de scraping en `backend/` (M2) |
| Quién lo escribe | implementer-frontend | implementer-backend |
| Origen | F004 + suite por slice | PRD §9; marca `source=playwright` |
| Se ejecuta en | `pnpm test:e2e` (Fase 6) | tareas Celery programadas |

Prohibido meter lógica de scraping en `e2e/` o tests de UI en los adapters.

## Backend — pytest + pytest-django

- Un test por **endpoint** y por **regla de negocio** (PRD ⇒ servicio). Viven en
  `apps/<dominio>/tests/`.
- La lógica está en `services.py` (sin HTTP), así que se testea **sin cliente**:
  test de servicio directo + test de endpoint para el contrato.
- `Decimal` para precios: los tests verifican exactitud monetaria, nunca `float`.
- Base de datos real (Postgres del compose) vía `pytest-django` + marker
  `django_db`. `DJANGO_SETTINGS_MODULE` se fija en `[tool.pytest.ini_options]`
  (ver F001).

## Scrapers — golden fixtures (la capa más crítica)

El eslabón frágil de ConstruScan: el HTML/XHR de Home Depot y Construrama
**cambia sin avisar**. Sin red de seguridad eso entra como **precio basura
silencioso** en la BD. Estrategia obligatoria desde M1/M2:

1. **Grabar** respuestas reales (HTML / JSON XHR) como archivos en
   `apps/<retailer>/tests/fixtures/` (con fecha en el nombre). Una vez, a mano.
2. **Testear el parser contra el fixture, SIN red.** El parser es una función
   pura `bytes → ProductoParseado`; el test la alimenta con el fixture y verifica
   precio, disponibilidad, SKU, moneda.
3. Un cambio del sitio ⇒ **test rojo** (regrabas el fixture y ajustas el parser),
   no un dato malo en producción.
4. El scraper de red (httpx/selectolax/tenacity) se separa del parser: la lógica
   de red se mockea; el parsing se prueba con fixtures. **Nunca** se pega a los
   retailers en un test.

> Esto materializa el principio no negociable del PRD: el scraping no ocurre en
> vivo, y su corrección es verificable offline.

## Celery — tareas verificadas, no esqueleto muerto

El scraping programado son tasks Celery. La auditoría marcó Celery como esqueleto
sin verificar; la estrategia lo cierra:

- En tests: `CELERY_TASK_ALWAYS_EAGER = True` (la task corre inline, sin worker).
- Test de la task de scraping con el adapter **mockeado** (devuelve un fixture):
  verifica que produce un `ScrapeRun` con `status` correcto y N `PriceObservation`.
- Un smoke opcional `celery -A config inspect ping` contra el redis del compose
  para probar el wiring del broker.

## Frontend — Vitest + Testing Library

- **Unit/componente** con `vitest` + `@testing-library/react`: formato de precio
  (`Decimal`/MXN), indicador "actualizado hace X" (frescura), lógica de la lista
  de cotización (agregar/quitar/cantidades), estados carga/error/datos.
- Datos de API **siempre** tipados desde `schema.d.ts` (también en los mocks de
  test): el contrato manda, incluso en pruebas.
- Script `test:unit` = `vitest run` (no watch). `init.sh` Fase 4 lo ejecuta si
  está definido. Setup en F002.
- Lo que cruza red real o varias pantallas **no** es unit: es E2E (Playwright).

## E2E — Playwright

- Cada **slice vertical** (cuando hay UI, desde M4) trae su test E2E del flujo
  feliz en `e2e/`. F004 monta Playwright + `webServer` (levanta backend y
  frontend) y el smoke base.
- Gate formal = `pnpm test:e2e` (Fase 6, `./init.sh --e2e`). El MCP de Playwright
  es solo lupa de desarrollo, nunca el veredicto.
- Flujo mínimo ConstruScan a cubrir en M4: elegir zona → buscar "varilla" → ver
  precios de ambos retailers → agregar a la lista de cotización → verla.

## Qué corre cuándo

| Momento | Comando | Cubre |
| --- | --- | --- |
| Iteración corta | `./init.sh --quick` | estático + unit (pytest, vitest), sin build ni infra |
| Antes de reportar done | `./init.sh` | + infra + build + contrato |
| Cerrar slice con UI | `./init.sh --e2e` | + Playwright E2E |

Regla sin excepción (`docs/verification.md`): rojo en `init.sh` ⇒ nada está
terminado. Un test flaky no se ignora: arreglarlo ES la tarea.
