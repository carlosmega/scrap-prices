# Review F031 — M5 Normalización de unidad

**Veredicto: APROBADO**

Revisor: reviewer del arnés. Verificación re-ejecutada de forma determinista
(no se confió en los informes de los implementers). Gate `./init.sh --e2e`
corrido por el revisor: **VERDE** a la primera, sin parches ni PIDs huérfanos.

## Tabla criterio (spec §"Criterios de aceptación") → estado → evidencia

| # | Criterio (spec) | Estado | Evidencia (comando/archivo) |
|---|-----------------|--------|------------------------------|
| 1 | **Modelo:** `mass_kg` y `sale_unit` existen; migración commiteada; `makemigrations --check` limpio | CUMPLE | `backend/apps/catalog/models.py:59-68` (`mass_kg` DecimalField nullable), `:89-117` (`SaleUnit` TextChoices + `sale_unit`); migración `backend/apps/catalog/migrations/0002_canonicalproduct_mass_kg_retailerproduct_sale_unit.py`; init.sh Fase 3 "migraciones al día (makemigrations --check)" ✔ |
| 2 | **Normalización pura:** reglas kg/tonelada/pieza, parcial sin `mass_kg`, cuantización 2dp ROUND_HALF_UP, unidad desconocida → None; tests tabla verdes | CUMPLE | `backend/apps/catalog/normalization.py` (sin ORM/HTTP; `_cuantiza` con `ROUND_HALF_UP`; `tiene_masa = mass_kg>0` evita div/0; `else → (None,None)`). Tests: `backend/apps/catalog/tests/test_normalization.py` (tabla de 12 casos + `test_cuantiza_round_half_up` con 1.005→1.01 + `test_resultado_es_decimal`). Corrida aislada: 30 tests verdes |
| 3 | **Búsqueda por `price_per_kg`:** orden y "menor precio" sobre `$/kg`; #4 → HD menor `$/kg` aunque `price` nativo mayor | CUMPLE | `backend/apps/catalog/services.py:77-89` `_menor_precio_por_kg` (filtra `price_per_kg is not None and is_available`); `:143-146` sort por `r[1]` (=menor `$/kg`), sin-precio al final. Test clave `test_para_varilla_4_home_depot_es_menor_por_kg_aunque_nativo_mayor` (test_search.py:135): asserta `Decimal(hd.price) > Decimal(cr.price)` Y `hd.price_per_kg=="20.09" < cr.price_per_kg=="21.53"`. Verificado: HD #4 nativo 20085.00/ton (19500×1.030) → /1000 = 20.085 → 20.09 HALF_UP; CR 20.90×1.030=21.527→21.53 |
| 4 | **Contrato:** `openapi.json` regenerado sin drift; campos nuevos presentes; frontend solo desde `schema.d.ts` | CUMPLE | Regenerado por el revisor → `diff` idéntico ("NO DRIFT: deterministic"). Campos en `backend/openapi.json` (`mass_kg`, `sale_unit`, `price_per_piece`, `price_per_kg`) y en `frontend/src/lib/api/schema.d.ts` (líneas 303,344,346,348,386,424...). init.sh Fase 5 "tipos TS sincronizados" ✔. `frontend/src/features/search/types.ts` deriva todo de `Awaited<ReturnType<typeof fetchSearch>>` (cero tipos a mano) |
| 5 | **Frontend:** titular `$/pieza` + nativo `$/ton`·`$/kg` + badge mejor precio + fallback "sin normalizar"; orden por `$/kg` | CUMPLE | `frontend/src/features/search/format.ts` (`sortPricesAsc` por `price_per_kg`, sin-él-al-final; `bestPriceIndex`; `formatPricePerPiece/Kg`, `formatNativePrice`). `result-card.tsx` y `product-prices.tsx` con paridad: titular `headline`, `retailer-native-price`, `retailer-price-per-kg`, `best-price-badge`, `retailer-unnormalized`, y "sin precio en tu zona". `format.test.ts` 18 casos verdes (vitest 41 total ✔) |
| 6 | **E2E:** varilla 1/2" Monterrey Metro: HD marcado mejor precio (menor `$/kg`), nativo `$/ton` visible | CUMPLE | `e2e/tests/normalization.spec.ts`: asserta badge en fila HD (count 1) y ausente en CR; `retailer-native-price` HD contiene `/ ton`; `hdNativeValue > crNativeValue` (nativo) Y `hdPerKg < crPerKg` (normalizado). init.sh Fase 6 "suite Playwright" ✔ |
| 7 | **Arquitectura/capas:** sin ORM en routers, fetch solo vía client.ts, cero `any` | CUMPLE | Greps deterministas del revisor: ORM en `api.py` = VACÍO (los 2 hits de `.delete(` son decoradores `@router.delete(...)`, no ORM; grep refinado `\.delete\(\s*\)` = vacío); `fetch(` fuera de client.ts = VACÍO; `: any`/`as any` = VACÍO. init.sh Fases 3 y 4 de arquitectura ✔ |

## Verificaciones extra (no listadas pero exigidas por CHECKPOINTS.md)

- **Ingestión:** `homedepot_sale_unit` (parsers.py:198, C62→pieza/TN·TNE→tonelada/KGM→kg/MTR→m/otro→"") y se aplica en `scraping/services.py:96` dentro de `defaults` de `_get_or_create_retailer_product`. Test parametrizado en `test_parsers_homedepot.py` verde.
- **Seed:** `mass_kg` NMX×longitud (#3=6.684, #4=11.952, #2=1.488), `sale_unit` HD→tonelada/CR→kg, historial multiplicativo `[1.000,1.015,1.030]`, precios base de la spec. `test_seed.py` asserta `mass_kg>0` y `sale_unit` por retailer.
- **Admin:** `mass_kg` `list_editable` en `CanonicalProductAdmin`; `sale_unit` en `list_display`/`list_filter`/`list_editable` de `RetailerProductAdmin` (admin.py:27,29,41,46,50).
- **Tests significativos ("git stash mental"):** sin la implementación los tests fallarían — antes de F031 no existían los campos `price_per_kg`/`price_per_piece`/`sale_unit`/`mass_kg`, así que las aserciones de igualdad exacta (`=="20.09"`, tuplas Decimal) y de `set(keys)` darían KeyError/AssertionError. No son no-ops.
- **Higiene del arnés:** `feature_list.json` JSON válido, F031 única `in_progress`; 27 features `done` con review APROBADO (init.sh Fase 1 ✔); repo git inicializado (Fase 0 ✔).
- **`git status`:** todos los archivos modificados/nuevos caen dentro de la capa permitida (backend/, frontend/, e2e/, specs/, progress/, feature_list.json). Sin archivos fuera de alcance.

## Output REAL de `./init.sh --e2e` (corrida del revisor)

Estado de puertos antes de correr: `:3300`/`:8800` sin listeners (sin PID huérfano; no se necesitó terminar nada). Suite estable a la primera (incl. `quote.spec.ts`, sin reintentos manuales).

```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ◌ jq no encontrado (opcional / al bootstrapear su capa)
  ✔ uv disponible
  ◌ docker no encontrado (opcional / al bootstrapear su capa)
  ✔ pnpm disponible
  ✔ repositorio git inicializado

── Fase 1 · Invariantes del arnés ──
  ✔ existe CLAUDE.md
  ✔ existe AGENTS.md
  ✔ existe CHECKPOINTS.md
  ✔ existe feature_list.json
  ✔ existe specs/TEMPLATE.md
  ✔ existe progress/current.md
  ✔ existe progress/history.md
  ✔ existe docs/architecture.md
  ✔ existe docs/verification.md
  ✔ feature_list.json es JSON válido (array)
  ✔ features in_progress: 1 (máximo 1)
  ✔ todos los status son válidos
  ✔ hook guard-feature.sh ejecutable
  ✔ las 27 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en MVP (backend corre con SQLite); infra Postgres/Redis diferida

── Fase 3 · Backend (Django + Ninja) ──
  ✔ uv sync (dependencias)
  ✔ ruff check
  ✔ migraciones al día (makemigrations --check)
  ✔ pytest
  ✔ arquitectura: routers (api.py) sin llamadas al ORM

── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ✔ pnpm install
  ✔ suite Playwright

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

## Greps de arquitectura (corrida del revisor, deterministas)

```
$ grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py
backend/apps/lists/api.py:92:@router.delete("/lists/{list_id}", response={204: None})
backend/apps/lists/api.py:149:@router.delete("/lists/{list_id}/items/{item_id}", response={204: None})
# ↑ falsos positivos: son decoradores HTTP de Ninja, NO llamadas al ORM.
# grep refinado a llamada-ORM real (.delete() con parens vacíos / .objects.):
$ grep -nE "\.objects\.|\.delete\(\s*\)|\.save\(\)|\.filter\(|\.create\(" backend/apps/*/api.py
# (vacío) → routers sin ORM.

$ grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"
# (vacío)

$ grep -rn ": any\b\|as any" frontend/src
# (vacío)
```

## Notas / deuda (fuera de alcance, ya documentadas en spec e informes; NO bloquean)

- Cotización (`apps/lists`) sigue en precio nativo: "Agregar 1" de un SKU listado por tonelada = 1 tonelada en el carrito. Spec §"No incluye" lo declara follow-up conocido.
- Historial NO se normaliza (cada punto solo gana `sale_unit` como etiqueta). Por diseño de la spec.
- `saco`/`m` admitidas en el enum pero caen a "sin normalizar" (None). Por diseño de la spec.
- `_PRECIO_INFINITO` en services.py:33 es código muerto **preexistente** (no introducido por F031). Candidato a limpieza aparte.

Todos los criterios CUMPLEN, el gate `./init.sh --e2e` termina VERDE de forma
estable y la arquitectura limpia se sostiene en los greps deterministas.
**Veredicto: APROBADO.**
