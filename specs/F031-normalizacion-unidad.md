# F031 — M5 Normalización de unidad (comparación cross-retailer real)

> SDD: la spec es el contrato. Si no está aquí, no existe. Si es ambiguo,
> se pregunta al humano ANTES de implementar, no después.

## Contexto y objetivo

Hoy `PriceObservation.price` es un `Decimal` **sin unidad**: la búsqueda
(`apps/catalog/services.py`) y la UI ordenan/comparan ese número crudo. Eso es
matemáticamente inválido cross-retailer: **Home Depot lista varilla por tonelada**
(~$20,000), **Construrama por kilogramo** (~$21), y el seed la tenía por pieza.
El "menor precio" actual elegiría siempre a Construrama solo porque su número es
más chico (21 < 20000), aunque por kg sea más caro.

Esta feature normaliza el precio a una **base comparable** para que la
comparación entre retailers sea real, sin perder el dato nativo (transparencia).

**Decisiones de producto cerradas con el humano (2026-06-16):**
1. **Unidad:** titular **por pieza** (intuitivo para obra) + **orden/menor-precio por $/kg** (justo y agnóstico a la longitud).
2. **Factores de conversión:** **tabla estándar NMX** de peso de varilla por calibre, **sembrada** y **editable en Django Admin** (campo `mass_kg` por canónico).
3. **Display:** mostrar **normalizado + precio nativo** del retailer (transparencia: "listado a $20,085/ton").

## Alcance

**Incluye:**
- **Modelo:** `CanonicalProduct.mass_kg` (kg de una pieza/unidad canónica, nullable) y `RetailerProduct.sale_unit` (unidad estructurada del precio listado). Migración commiteada.
- **Servicio de normalización puro:** `apps/catalog/normalization.py` con `normaliza_precio(price, sale_unit, mass_kg) -> (price_per_piece, price_per_kg)`. Sin ORM, testeable 1:1.
- **API/contrato:** `PriceByRetailerOut` gana `sale_unit`, `price_per_piece`, `price_per_kg`; `CanonicalProductRefOut`/`CanonicalProductDetailOut` ganan `mass_kg`; `PriceHistoryPointOut` gana `sale_unit`. La búsqueda ordena y elige "menor precio" por **`price_per_kg`**. Regenerar `backend/openapi.json`.
- **Ingestión:** mapear el código UN/ECE de HD (`homedepot_unit`) a `sale_unit` al hacer `get_or_create` del `RetailerProduct`.
- **Admin:** `mass_kg` editable en `CanonicalProductAdmin`; `sale_unit` editable/visible en `RetailerProductAdmin`.
- **Seed (F013):** sembrar `mass_kg` (tabla NMX × longitud) y `sale_unit` por retailer (HD→tonelada, CR→kg), con precios nativos verosímiles que exhiban la normalización. Actualizar los tests afectados.
- **Frontend:** búsqueda (`result-card.tsx`) y detalle (`product-prices.tsx`) muestran titular **$/pieza**, secundario nativo ("listado a $X/ton") y **$/kg**; ordenan por `price_per_kg`; marcan el **mejor precio** (menor $/kg). Fallback "sin normalizar" cuando falten datos. `pnpm gen:api` antes de consumir.
- **E2E:** la varilla #4 muestra a **Home Depot como más barato** (por $/kg) aunque su número nativo sea mayor; el precio nativo es visible.

**No incluye (explícitamente fuera):**
- Normalizar el **historial** de precios (cada punto solo gana `sale_unit` para etiquetar; los puntos siguen en valor nativo).
- Normalizar la **cotización** (`apps/lists`, F017/F022): sigue con precio nativo. ⚠️ Queda un follow-up conocido: "agregar 1" de un SKU listado por tonelada significa 1 tonelada en el carrito. Se anota como deuda, no se resuelve aquí.
- Auto-match (rapidfuzz), Postgres FTS, Celery beat, CI, export CSV (otros ítems M5).
- Unidades `saco`/`metro`: el modelo las admite en el enum, pero `normaliza_precio` solo computa para `pieza`/`kg`/`tonelada`; el resto cae a "sin normalizar" (None). No es objetivo de esta feature cerrarlas.

## Modelo

### `CanonicalProduct.mass_kg` (apps/catalog/models.py)
```python
mass_kg = models.DecimalField(
    max_digits=8, decimal_places=3, null=True, blank=True,
    help_text="Peso de UNA pieza/unidad canónica en kg (NMX masa nominal × longitud). "
              "Null = no normalizable: la UI cae a solo-precio-nativo.",
)
```

### `RetailerProduct.sale_unit` (apps/catalog/models.py)
```python
class SaleUnit(models.TextChoices):
    PIEZA = "pieza", "Pieza"
    KG = "kg", "Kilogramo"
    TONELADA = "tonelada", "Tonelada"
    SACO = "saco", "Saco"
    METRO = "m", "Metro"

sale_unit = models.CharField(
    max_length=16, choices=SaleUnit.choices, blank=True,
    help_text="Unidad en que el retailer LISTA el precio. Blank = desconocida "
              "(no normalizable). Se cura en Admin / la fija el adapter.",
)
```
`unit_raw` se conserva tal cual (auditoría del texto/código crudo del retailer).

Migración commiteada junto al modelo (`apps/catalog/migrations/`).

## Servicio de normalización (apps/catalog/normalization.py — nuevo, puro)

```python
def normaliza_precio(
    price: Decimal | None,
    sale_unit: str,
    mass_kg: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    """(price_per_piece, price_per_kg). None donde no se pueda computar."""
```

Reglas (cuantizar cada resultado no-None a **2 decimales, ROUND_HALF_UP**):
- `price is None` → `(None, None)`.
- `sale_unit == "kg"`: `per_kg = price`; `per_piece = price * mass_kg` si `mass_kg` (>0) si no `None`.
- `sale_unit == "tonelada"`: `per_kg = price / 1000`; `per_piece = per_kg * mass_kg` si `mass_kg` si no `None`.
- `sale_unit == "pieza"`: `per_piece = price`; `per_kg = price / mass_kg` si `mass_kg` (>0) si no `None`.
- cualquier otro (`saco`/`m`/`""`): `(None, None)`.

Es decir: se admite resultado **parcial** (un lado `None` cuando falta `mass_kg`).
Función pura (sin ORM, sin HTTP) → test 1:1 con casos tabla.

`apps/catalog/services.py`:
- `_ensamblar_precio(rp, zona, mass_kg)` calcula `price_per_piece`/`price_per_kg` con `normaliza_precio(obs.price, rp.sale_unit, mass_kg)` y los pone en el schema; añade `sale_unit=rp.sale_unit`.
- La elección de "menor precio" y el `sort="price"` usan **`price_per_kg`** (no `price`): menor `price_per_kg` disponible primero; los sin `price_per_kg` al final. Renombrar/ajustar `_menor_precio_disponible` → base `price_per_kg`.

## Ingestión (apps/scraping)

- Añadir en `apps/scraping/parsers.py`:
```python
def homedepot_sale_unit(code: str) -> str:
    """Mapea el código UN/ECE de x_measurements.quantityMeasure a SaleUnit.
    C62->pieza, TN/TNE->tonelada, KGM->kg, MTR->m; desconocido->''."""
```
- En `apps/scraping/services.py::_get_or_create_retailer_product`, setear
  `"sale_unit": homedepot_sale_unit(homedepot_unit(raw_price.raw_payload))` en `defaults`.
  (Sigue dejando el matching a canónico `unmatched` para curar en Admin.)

## Seed (apps/core/services.py)

- `mass_kg` por canónico = **masa nominal NMX (kg/m) × longitud_m**. Tabla:
  | calibre | kg/m  | longitud | mass_kg |
  | ------- | ----- | -------- | ------- |
  | #3 (3/8") | 0.557 | 12 m | 6.684 |
  | #4 (1/2") | 0.996 | 12 m | 11.952 |
  | #2 (1/4") | 0.248 | 6 m  | 1.488 |
- `sale_unit`: **home-depot → `tonelada`**, **construrama → `kg`** (para ejercer la normalización end-to-end sin red).
- Precios nativos base recomendados (deterministas para los tests; el historial se vuelve **multiplicativo** para ser agnóstico a la unidad: factores `[1.000, 1.015, 1.030]` aplicados al base, cuantizado 2dp — la última captura sigue siendo inequívocamente la más alta):
  | canónico | HD ($/ton) base | CR ($/kg) base |
  | -------- | --------------- | -------------- |
  | #3 | 19500.00 | 20.90 |
  | #4 | 19500.00 | 20.90 |
  | #2 | 20500.00 | 19.80 |
  Con esto (última captura ×1.030): HD es más barato por $/kg en **#3 y #4**; Construrama lo es en **#2** → la comparación normalizada varía y NO coincide con "el número crudo más chico".
- Actualizar los tests que asumían precios por pieza / orden crudo: `apps/core/tests/test_seed.py`, `apps/catalog/tests/test_search.py`, `apps/catalog/tests/test_detalle.py`.

## Frontend (Next.js)

Primero `pnpm gen:api` para que `src/lib/api/schema.d.ts` traiga los campos nuevos
(jamás declarar tipos a mano). Luego:
- `src/features/search/format.ts`: `sortPricesAsc` ordena por **`price_per_kg`** (base de comparación); los sin `price_per_kg` al final. Añadir helper de formato para el titular `$/pieza` y la línea nativa `$X / <unidad>`.
- `src/features/search/components/result-card.tsx` y `src/features/products/components/product-prices.tsx`:
  - **Titular** por fila de retailer: `price_per_piece` → "$236.65 / pieza".
  - **Secundario** (texto chico): nativo → "listado a $20,085.00 / ton" usando `price` + `sale_unit`; y `price_per_kg` → "$20.09 / kg".
  - **Mejor precio:** marcar la fila con menor `price_per_kg` (badge/etiqueta), `data-testid` para E2E.
  - **Fallback:** si `price_per_piece`/`price_per_kg` son `null`, mostrar solo el nativo con nota "sin normalizar".
  - Conservar disponibilidad/frescura y "sin precio en tu zona".

## Contrato API (cambios)

| Schema | Campo nuevo | Tipo |
| ------ | ----------- | ---- |
| `PriceByRetailerOut` | `sale_unit` | `str` (`""` si desconocida) |
| `PriceByRetailerOut` | `price_per_piece` | `Decimal \| None` |
| `PriceByRetailerOut` | `price_per_kg` | `Decimal \| None` |
| `CanonicalProductRefOut` | `mass_kg` | `Decimal \| None` |
| `CanonicalProductDetailOut` | `mass_kg` | `Decimal \| None` |
| `PriceHistoryPointOut` | `sale_unit` | `str` |

`Decimal` se serializa como string (exactitud monetaria, igual que `price` hoy).
Regenerar: `uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json` y `pnpm gen:api`.

## Criterios de aceptación

- [ ] **Backend (modelo):** `mass_kg` y `sale_unit` existen con migración commiteada; `makemigrations --check` limpio.
- [ ] **Backend (normalización):** `normaliza_precio` cubierta por tests tabla: tonelada/kg/pieza con y sin `mass_kg`, `price=None`, unidad desconocida, y la cuantización a 2dp (ROUND_HALF_UP).
- [ ] **Backend (búsqueda):** `GET /api/search?q=varilla&zone_id=<mty>` devuelve cada precio con `sale_unit`, `price_per_piece`, `price_per_kg`; el orden y el "menor precio" usan `price_per_kg`. Para #4, Home Depot (nativo por tonelada) sale como menor `price_per_kg` aunque su `price` nativo sea mayor que el de Construrama.
- [ ] **Backend (contrato):** `openapi.json` regenerado; `init.sh` Fase 5 (drift) verde.
- [ ] **Frontend:** la tarjeta de búsqueda y el detalle muestran titular `$/pieza`, nativo (`$X/ton`/`$X/kg`) y `$/kg`; ordenan por `$/kg`; marcan el mejor precio; caen a "sin normalizar" cuando falta dato. `tsc`+`lint`+`build` verdes; sin tipos de API a mano.
- [ ] **E2E:** en Monterrey Metro, para "varilla 1/2" Home Depot aparece marcado como mejor precio (menor $/kg) y su precio nativo "$.../ton" es visible.

## Plan de verificación

```bash
# Backend
cd backend
uv run ruff check .
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q                       # incl. normalization, search, detalle, seed
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
# Frontend
cd ../frontend
pnpm gen:api
pnpm exec tsc --noEmit && pnpm lint && pnpm build
pnpm exec vitest run
# Todo junto (gate del arnés)
cd .. && ./init.sh --e2e               # debe terminar VERDE
```

## Notas y decisiones abiertas

- Resueltas con el humano (ver arriba). **Sin dudas abiertas** que bloqueen implementar.
- Follow-up conocido (fuera de alcance): normalizar la cotización para que "cantidad" sea en piezas y no en la unidad nativa del retailer.
