# PRD — ConstruScan (nombre de trabajo)
### Comparador de precios de materiales de construcción por zona — México

> **Estado:** Borrador v0.1 · Documento vivo
> **Autor:** Carlos
> **Objetivo de ejecución:** este PRD está redactado para alimentarse a **Claude Code** como guía de construcción.
> **Nota sobre el nombre:** `ConstruScan` es un nombre de trabajo (placeholder). Reemplazable.

---

## 1. Resumen ejecutivo

ConstruScan es una **aplicación independiente** (módulo aparte; integración con ConstruPro/ConstruBase queda fuera de alcance por ahora) cuyo objetivo es permitir a un usuario consultar y comparar **precios reales de materiales de construcción por zona geográfica**, obtenidos de los e-commerce más grandes de México:

- **The Home Depot México** (`homedepot.com.mx`)
- **Construrama** (`construrama.com` — red CEMEX, plataforma unificada con subpaths por distribuidor)

El usuario selecciona su ubicación, busca un producto (p. ej. *"varilla"*), y obtiene los precios de ese producto en su zona en **ambos** retailers. Puede seleccionar productos y agregarlos a una **lista de cotización propia** (no es un carrito de compra), para construir sus propias cotizaciones con costos reales y verificables.

### Principio arquitectónico no negociable
**El scraping NO ocurre en vivo durante la búsqueda del usuario.** Los scrapers corren de forma programada y asíncrona, escriben a PostgreSQL con `zona + timestamp`, y la búsqueda del usuario consulta **siempre la base de datos propia**, nunca a los retailers en tiempo real. La UI muestra la antigüedad del dato ("actualizado hace X").

---

## 2. Alcance

### 2.1 Dentro de alcance (MVP)
- Selección de ubicación / zona por parte del usuario.
- Búsqueda de productos por texto en el catálogo normalizado.
- Visualización de precios por producto en Home Depot y Construrama para la zona seleccionada.
- Lista de cotización del usuario (agregar/quitar productos, cantidades, snapshot de precio).
- Subsistema de scraping programado para los dos retailers, en zona(s) piloto.
- Normalización interna de zonas (mapeo tienda HD ↔ distribuidor Construrama).
- Matching de SKU entre retailers (curación **manual** vía Django Admin en MVP).
- Indicador de frescura del dato.

### 2.2 Fuera de alcance (por ahora)
- Integración con ConstruPro / ConstruBase.
- Compra real / checkout / pasarela de pago.
- Sitios de distribuidores Construrama **independientes** fuera de `construrama.com` (`materialesjerez.com.mx`, `construramaonline.com.mx`, etc.) — distintos CMS, se evalúan después como adapters separados.
- Retailers adicionales (Sodimac, ConstruCity, MN del Golfo, etc.) — backlog.
- Matching automático por fuzzy/ML (llega en fase posterior; MVP es manual).
- Multi-tenant / organizaciones.

### 2.3 Restricciones duras (guardrails) — heredadas y obligatorias
1. **Nunca evadir defensas anti-bot.** Si un sitio bloquea, se marca como no viable y se salta. No se circunvala.
2. **Sin autenticación.** No se hace login en ningún retailer ni se scrapean zonas tras credenciales.
3. **Rate limiting mínimo obligatorio** entre requests por dominio (delay configurable, nunca cero).
4. Respetar `robots.txt` y términos de servicio; User-Agent honesto.
5. Almacenar `raw_payload` de cada lectura para auditabilidad y depuración.
6. No recolectar PII.
7. Fuentes no viables → se marcan (`scraper_status`) y se omiten, no se fuerzan.

---

## 3. Usuarios / Personas

| Persona | Descripción | Necesidad principal |
|---|---|---|
| **Cotizador / contratista** | PyME de construcción que arma cotizaciones para clientes. | Costos reales por zona para cotizar con margen sobre datos verídicos. |
| **Comprador de obra** | Encargado de compras de una obra. | Comparar precio del mismo material entre HD y Construrama en su zona. |
| **Administrador (interno)** | Carlos / operador. | Curar matching de SKU, monitorear scrapers, gestionar zonas y retailers (vía Django Admin). |

---

## 4. Historias de usuario

> Formato: *Como [rol] quiero [acción] para [beneficio]*. Cada historia incluye criterios de aceptación (CA).

### Épica A — Ubicación y zona
**A1.** Como usuario quiero seleccionar mi ubicación para que los precios mostrados correspondan a mi zona.
- CA1: Puedo elegir ciudad/zona de una lista de zonas activas.
- CA2: Opcionalmente puedo dar mi ubicación (lat/lng o dirección) y el sistema resuelve la zona más cercana.
- CA3: La zona seleccionada persiste durante la sesión.
- CA4: Si no hay cobertura en mi zona, recibo un mensaje claro ("aún sin cobertura").

### Épica B — Búsqueda y comparación
**B1.** Como usuario quiero buscar un producto por texto (p. ej. "varilla 3/8") para encontrar opciones en mi zona.
- CA1: La búsqueda consulta el catálogo normalizado (DB propia), no los retailers en vivo.
- CA2: Los resultados muestran productos canónicos con sus precios por retailer en la zona.
- CA3: Cada precio muestra retailer, precio, unidad, disponibilidad y antigüedad ("actualizado hace X").
- CA4: Puedo ordenar por precio.
- CA5: Si un retailer no tiene el producto en la zona, se indica explícitamente.

**B2.** Como usuario quiero ver el detalle de un producto para comparar presentaciones y ver historial de precio.
- CA1: Veo precios actuales por retailer en mi zona.
- CA2: Veo historial de precio (al menos las últimas lecturas).
- CA3: Veo enlace a la ficha original del retailer.

### Épica C — Lista de cotización ("carrito propio")
**C1.** Como usuario quiero agregar productos a una lista propia para construir mi cotización.
- CA1: Puedo agregar un producto (de un retailer específico) con cantidad.
- CA2: Al agregar, se guarda un **snapshot** del precio y fecha (no cambia si el precio luego cambia).
- CA3: Puedo editar cantidades y quitar ítems.
- CA4: Veo subtotal y total de la lista.
- CA5: Puedo tener la lista asociada a una zona.

**C2.** Como usuario quiero exportar/visualizar mi lista para usarla en mi propia cotización.
- CA1: Veo la lista consolidada con costos.
- CA2 (deseable): exportar a CSV/Excel. *(Backlog si no entra en MVP.)*

### Épica D — Administración (interno)
**D1.** Como admin quiero mapear SKUs equivalentes entre retailers a un producto canónico.
- CA1: Desde Django Admin puedo asignar `RetailerProduct` → `CanonicalProduct`.
- CA2: Puedo ver SKUs sin matchear (`unmatched`) y resolverlos.
- CA3: Puedo rechazar/marcar un match.

**D2.** Como admin quiero monitorear las corridas de scraping para detectar fallas.
- CA1: Veo cada `ScrapeRun` con estado, ítems encontrados y errores.
- CA2: Puedo marcar un retailer/fuente como no viable.

**D3.** Como admin quiero gestionar zonas y el mapeo zona↔tienda/distribuidor.

---

## 5. Requerimientos funcionales

- **RF1.** Resolución de zona a partir de selección manual o ubicación (lat/lng/dirección).
- **RF2.** Catálogo normalizado de productos canónicos con categorías y unidades.
- **RF3.** Búsqueda full-text en español sobre el catálogo (tolerante a acentos).
- **RF4.** Lectura de precios por zona y retailer desde DB, con frescura visible.
- **RF5.** Lista de cotización con snapshots de precio y totales.
- **RF6.** Pipeline de scraping programado por retailer y zona, con ingestión a `PriceObservation`.
- **RF7.** Mapeo de zona interna ↔ tienda HD / distribuidor Construrama.
- **RF8.** Curación manual de matching de SKU en Admin.
- **RF9.** Auditoría de corridas de scraping.

---

## 6. Requerimientos no funcionales

- **RNF1 (Legal/Ético).** Cumplimiento de los guardrails de la sección 2.3 en todo el pipeline.
- **RNF2 (Rendimiento).** Búsqueda del usuario < 500 ms (consulta a DB, no a retailers).
- **RNF3 (Frescura).** Cada `PriceObservation` tiene `captured_at`; la UI nunca oculta la antigüedad.
- **RNF4 (Resiliencia de scraping).** Reintentos con backoff (`tenacity`); una falla de un retailer no tumba al otro.
- **RNF5 (Rate limiting).** Delay mínimo configurable por dominio; concurrencia limitada por retailer.
- **RNF6 (Observabilidad).** Logs estructurados y registro de `ScrapeRun`.
- **RNF7 (Mantenibilidad).** Adapters de retailer detrás de una interfaz común; agregar un retailer = nuevo adapter.

---

## 7. Arquitectura técnica

### 7.1 Stack (confirmado)
- **Backend:** Django 5.0 + **Django Ninja** (schemas Pydantic, endpoints async, OpenAPI automático sobre el ORM/Admin/migraciones de Django).
- **Frontend:** **Next.js 15.5** (React).
- **Base de datos:** PostgreSQL.
- **Async / scheduling:** **Celery + Redis** (Celery Beat para programación; Redis como broker y cache).
- **Scraping:** `httpx` (async), `selectolax` (parsing rápido), `tenacity` (retries), `asyncio`. `requests`/`beautifulsoup4` como utilitarios puntuales. **Playwright solo como último recurso** (fallback para JS pesado / contenido no obtenible vía XHR).
- **Matching (fase posterior):** `rapidfuzz` para fuzzy matching.

> **Por qué Django Ninja y no FastAPI:** se aprovecha ORM, migraciones, auth y especialmente **Django Admin** para la curación manual de SKUs en MVP, sin perder lo bueno de FastAPI (Pydantic, async, type hints, docs). FastAPI obligaría a reconstruir todo eso sin ventaja.

### 7.2 Componentes
```
┌─────────────────────┐      HTTP/JSON       ┌──────────────────────────┐
│  Next.js 15.5 (UI)  │ ───────────────────► │  Django + Django Ninja   │
│  - Selección zona   │ ◄─────────────────── │  API (lectura desde DB)  │
│  - Búsqueda         │                       └────────────┬─────────────┘
│  - Lista cotización │                                    │ ORM
└─────────────────────┘                       ┌────────────▼─────────────┐
                                               │       PostgreSQL          │
                                               │  Canonical, RetailerProd, │
                                               │  PriceObservation, Zones  │
                                               └────────────▲─────────────┘
                                                            │ ingestión
┌─────────────────────┐   tasks programadas   ┌────────────┴─────────────┐
│   Celery Beat       │ ───────────────────►  │  Celery Workers (scrapers)│
│   (scheduling)      │                        │  - HomeDepotAdapter       │
└─────────────────────┘                        │  - ConstruramaAdapter     │
         ▲ Redis (broker+cache)                │  (BaseRetailerAdapter)    │
         └──────────────────────────────       └────────────┬─────────────┘
                                                            │ HTTP (rate-limited)
                                                  ┌─────────▼──────────┐
                                                  │ Home Depot MX /    │
                                                  │ Construrama        │
                                                  └────────────────────┘
```

---

## 8. Modelo de datos

> Convención (estilo CDS/Dynamics, preferencia del equipo): **PK UUID**, `created_at`/`updated_at`, soft-delete (`is_active`) donde aplique, campos de auditoría en entidades clave.

### Entidades núcleo

**`Retailer`**
`id (UUID)`, `name`, `slug`, `base_url`, `pricing_model` (`zone_cookie` | `distributor_subpath`), `scraper_status` (`active` | `paused` | `non_viable`), `is_active`, timestamps.

**`RetailerLocation`** — tienda física (HD) o distribuidor (Construrama)
`id`, `retailer_fk`, `external_id` (store_id HD / slug distribuidor Construrama), `name`, `subpath` (para Construrama: `/materialesmonterrey`), `address`, `city`, `state`, `lat`, `lng`, `is_active`, timestamps.

**`Zone`** — zona interna normalizada (p. ej. "Monterrey Metro")
`id`, `name`, `slug`, `state`, `centroid_lat`, `centroid_lng`, `is_active`, timestamps.

**`ZoneLocationMap`** — resuelve qué tienda/distribuidor sirve a una zona
`id`, `zone_fk`, `retailer_location_fk`, `is_primary`. (Une `Zone` ↔ `RetailerLocation`.)

**`Category`** — categoría interna normalizada (varilla, cemento, block…)
`id`, `name`, `slug`, `parent_fk (nullable)`, `is_active`.

**`CanonicalProduct`** — el "mismo producto" normalizado entre retailers
`id`, `name`, `category_fk`, `unit` (`pieza` | `saco` | `m` | `kg` | …), `specs (JSONB: calibre, diámetro, longitud, marca, presentación)`, `is_active`, timestamps.

**`RetailerProduct`** — un SKU tal como existe en UN retailer
`id`, `retailer_fk`, `external_sku`, `raw_name`, `url`, `unit_raw`, `brand`, `canonical_product_fk (nullable)`, `match_status` (`unmatched` | `auto` | `manual` | `rejected`), `match_confidence (nullable)`, `is_active`, timestamps.

**`PriceObservation`** — una lectura de precio
`id`, `retailer_product_fk`, `zone_fk` (y/o `retailer_location_fk`), `price (Decimal)`, `currency` (`MXN`), `is_available (bool)`, `source` (`xhr` | `html` | `playwright`), `captured_at`, `raw_payload (JSONB)`.

**`ScrapeRun`** — auditoría de corrida
`id`, `retailer_fk`, `zone_fk`, `started_at`, `finished_at`, `status` (`ok` | `partial` | `failed`), `items_found`, `errors (JSONB)`.

### Entidades de usuario

**`UserList`** — lista de cotización (el "carrito propio")
`id`, `user_fk`, `name`, `zone_fk`, `status`, `created_at`, `updated_at`.

**`UserListItem`**
`id`, `user_list_fk`, `retailer_product_fk` (o `canonical_product_fk`), `quantity`, `captured_price (Decimal, snapshot)`, `captured_at (snapshot)`, `notes`.

### Relaciones clave
- `Zone` *N↔N* `RetailerLocation` vía `ZoneLocationMap`.
- `CanonicalProduct` *1↔N* `RetailerProduct` (matching).
- `RetailerProduct` *1↔N* `PriceObservation`.
- `UserList` *1↔N* `UserListItem`.

---

## 9. Subsistema de scraping

### 9.1 Hallazgos confirmados por retailer

**Home Depot México**
- Precios servidos vía **XHR/JavaScript**, no en HTML crudo.
- **Precio por zona** dependiente de selector de tienda + cookie.
- Estrategia: reproducir la llamada XHR fijando la tienda/zona; parsear JSON. `selectolax` solo si hace falta leer HTML.

**Construrama** (`construrama.com`, red CEMEX)
- Plataforma unificada con **subpath por distribuidor** (`construrama.com/{distribuidor}/`, categorías tipo `/c/006`).
- **Precio y disponibilidad por ciudad/zona** mediante selector de dirección + cookie de sesión ("la selección será vigente en la sesión actual").
- 700+ concesionarios; no todos sirven todas las zonas.
- Estrategia: identificar distribuidor(es) que sirven la zona piloto; fijar ciudad/zona; capturar precios. Confirmar mecanismo exacto (XHR vs render) en reconocimiento.

### 9.2 Enfoque por fases (heredado)
1. **Fase 0 — Reconocimiento manual (DevTools).** Por retailer: documentar endpoints XHR, mecanismo de cookie/selector de zona, forma de los payloads, paginación. Entregable: doc de reconocimiento por retailer.
2. **Fase 1 — Script de reconocimiento (read-only).** Confirma endpoints y el cambio de zona de forma reproducible. No ingesta aún.
3. **Fase 2 — Extracción acotada.** 2 zonas geográficas × 1–2 categorías (cemento / varilla). Ingesta a `PriceObservation`.

### 9.3 Interfaz de adapters
```python
class BaseRetailerAdapter(Protocol):
    retailer_slug: str

    async def list_products(self, category: str, location: RetailerLocation) -> list[RawProduct]: ...
    async def get_price(self, product: RawProduct, location: RetailerLocation) -> RawPrice: ...
    def set_zone(self, location: RetailerLocation) -> None: ...   # fija cookie/selector
```
- `HomeDepotAdapter` y `ConstruramaAdapter` implementan la interfaz.
- `httpx.AsyncClient` con headers honestos; `tenacity` para reintentos con backoff; rate limiter por dominio (delay mínimo configurable + semáforo de concurrencia).
- **Playwright** solo si el contenido es inalcanzable vía XHR; marcado como `source=playwright`.

### 9.4 Programación
- Celery Beat dispara `scrape_retailer_zone(retailer, zone, category)` por combinación.
- Frecuencia configurable (p. ej. diaria) respetando rate limiting.
- Cada corrida crea un `ScrapeRun`; los precios entran como nuevas `PriceObservation` (histórico, no se sobrescribe).

---

## 10. Normalización de zonas

Problema: "zona" no es comparable directamente entre retailers (HD usa tienda+cookie; Construrama usa distribuidor+ciudad).

Solución: `Zone` interna normalizada. Cada zona se mapea (`ZoneLocationMap`) a:
- la(s) tienda(s) Home Depot que la sirven, y
- el/los distribuidor(es) Construrama que la sirven.

La búsqueda del usuario opera sobre `Zone`; el scraping opera sobre `RetailerLocation`. El mapeo se cura en Admin.

**Zona piloto:** Monterrey Metro.

---

## 11. Matching de SKU

- **MVP:** curación **manual** en Django Admin. Vista de `RetailerProduct` con filtro por `match_status=unmatched`; acción para asignar `CanonicalProduct`.
- **Fase posterior:** sugerencia automática con `rapidfuzz` sobre `raw_name` + comparación de `specs` (calibre/diámetro/longitud/marca), con umbral de confianza y revisión humana del `auto`-match.

---

## 12. API (Django Ninja) — endpoints MVP

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/zones` | Lista zonas activas. |
| POST | `/api/zones/resolve` | Resuelve zona desde lat/lng o dirección. |
| GET | `/api/search?q=&zone_id=&sort=price` | Productos canónicos + precios por retailer en zona. |
| GET | `/api/products/{id}?zone_id=` | Detalle: precios por retailer + historial. |
| GET | `/api/lists` / POST `/api/lists` | Listar / crear lista de cotización. |
| GET/PATCH/DELETE | `/api/lists/{id}` | Gestionar lista. |
| POST/PATCH/DELETE | `/api/lists/{id}/items` | Gestionar ítems (con snapshot de precio). |
| GET | `/api/retailers` (interno) | Retailers y estado de scraper. |

Respuestas incluyen `captured_at` y `is_available` en cada precio para reflejar frescura.

---

## 13. Roadmap por fases (para Claude Code)

| Hito | Contenido | Entregable |
|---|---|---|
| **M0 — Scaffold** | Monorepo: Django+Ninja+Postgres+Celery/Redis y Next.js 15.5. Modelo de datos completo, migraciones, Admin configurado. | Proyecto corriendo local + Admin navegable. |
| **M1 — Reconocimiento** | Fase 0 (manual DevTools) + Fase 1 (script de reconocimiento) para HD y Construrama, zona Monterrey. | Docs de reconocimiento + script read-only que confirma zona. |
| **M2 — Extracción** | Adapters + pipeline de ingestión a `PriceObservation`. 2 zonas × 1–2 categorías. `ScrapeRun` + rate limiting + retries. | Precios reales en DB con histórico. |
| **M3 — API + Matching** | Resolución de zona, búsqueda full-text, endpoints de productos/precios. Curación manual de SKU en Admin. | API funcional + catálogo matcheado. |
| **M4 — UI** | Next.js: selección de ubicación, búsqueda, resultados comparados por retailer, lista de cotización con snapshots. | App end-to-end usable. |
| **M5 — Hardening** | Programación Celery Beat, indicadores de frescura, observabilidad, fuzzy matching (`rapidfuzz`), export CSV/Excel. | MVP endurecido. |

---

## 14. Supuestos y pendientes abiertos

- **(Confirmado)** Construrama unificado = `construrama.com` con subpaths por distribuidor y selector de ciudad/zona; sitios de distribuidor independientes quedan fuera.
- **(Pendiente)** Confirmar en reconocimiento el mecanismo exacto de precios de Construrama (XHR vs render) y de Home Depot México.
- **(Pendiente)** Identificar qué tiendas HD y qué distribuidores Construrama sirven la zona Monterrey Metro.
- **(Decisión pendiente)** Categoría piloto: **cemento vs. varilla**. *Recomendación: iniciar con **varilla** (es el caso de ejemplo del usuario y tiene specs claras —calibre/diámetro/longitud— que facilitan el matching).*
- **(Pendiente)** Revisión de Términos de Servicio de ambos sitios antes de M2.
- **(Pendiente)** Modelo de autenticación de usuarios de ConstruScan (¿login propio? ¿anónimo con lista en sesión?) — definir antes de M3/M4.

---

## 15. Stack tecnológico (resumen)

| Capa | Tecnología |
|---|---|
| Backend / API | Django 5.0 + Django Ninja |
| Frontend | Next.js 15.5 (React) |
| Base de datos | PostgreSQL |
| Async / scheduling / cache | Celery + Celery Beat + Redis |
| Scraping | httpx, selectolax, tenacity, asyncio (requests/beautifulsoup4 puntual; Playwright último recurso) |
| Matching (fase posterior) | rapidfuzz |
| Admin / curación | Django Admin |
