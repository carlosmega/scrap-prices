# Reconocimiento — Home Depot México

> Entregable de la Fase 0 del subsistema de scraping (PRD §9.2). Documenta
> CÓMO sirve precios este retailer por zona, para que M2 (adapters) se escriba
> sobre hechos confirmados, no supuestos. Transcrito por un agente a partir de un
> export **HAR** de una sesión de DevTools real (no se pegó a la red).

- **Retailer:** The Home Depot México (`www.homedepot.com.mx`)
- **Fecha de reconocimiento:** 2026-06-14
- **Autor:** Carlos (captura HAR) + agente Fase 0 (análisis offline)
- **Zona piloto reconocida:** Monterrey Metro
- **Plataforma detectada:** HCL Commerce ("WebSphere Commerce") Cloud — `ec-version: 24d`,
  backend `*.prd.hdmx.now.hclsoftware.cloud`. `storeId=10351`, `catalogId=10101`,
  `langId=-5` (es_MX), `currency=MXN`, `contractId=4000000000000000003`, `marketId=10`.

## 0. Gate legal / ToS (obligatorio antes de cualquier request automatizado)
- [ ] Revisado `robots.txt` (`www.homedepot.com.mx/robots.txt`). **No se observó en el HAR**
  (el navegador no solicitó `robots.txt` durante la sesión, por lo que su contenido NO
  está en la evidencia). Pendiente leerlo antes de M2.
- [ ] Revisados Términos de Servicio respecto a scraping/uso automatizado. Veredicto:
  **`PENDIENTE — requiere confirmación humana`** (decisión legal de Carlos, fuera del
  alcance del agente). No hay evidencia de ToS en el HAR.
- [x] Sin login ni evasión de anti-bot: la sesión analizada fue de usuario invitado
  (`isPartiallyAuthenticated:false`, `registerType:"G"` en `usercontext/@self/contextdata`);
  los endpoints de precio respondieron `200` sin autenticación ni captcha (ver §5).
- [ ] User-Agent honesto definido; delay mínimo por dominio definido. Pendiente fijar
  en M2 (la captura usó UA de Safari iOS real; M2 debe usar un UA honesto de ConstruScan).
- **Decisión de viabilidad:** **`paused`** hasta cerrar el gate ToS/robots humano.
  Técnicamente es `active`-able (endpoint XHR público, JSON limpio, sin anti-bot observado),
  pero NO se habilita `Retailer.scraper_status=active` hasta veredicto ToS explícito.

## 1. Mecanismo de zona/precio
- **Cómo se fija la zona:** selector de tienda física. Al elegir tienda se hace
  `POST /wcs/resources/store/10351/hdm/store/setDefault` con body
  `{"defaultStore":"1333","fromPageName":"2"}` (respuesta vacía, status `200`).
  Aquí `1333` es el **código/nombre de tienda** (`physicalStoreName`); internamente
  el sistema lo mapea a un **`physicalStoreId`** numérico distinto (ver §3).
- **Cómo viaja la tienda en las llamadas de precio:** NO por header custom. Va como
  **query params** en cada request a `/search/resources/api/v2/products`:
  `physicalStoreId`, `stLocId`, `marketId`. La persistencia entre páginas la da una
  **cookie de sesión** que el HAR **no capturó** (el export trae los headers `Cookie`
  y `Set-Cookie` removidos — no hay nombres de cookie en la evidencia). Para M2 esto
  **no es bloqueante**: el precio se puede pedir pasando los params de tienda
  explícitamente, sin depender de la cookie. Confirmar nombre de cookie de tienda en
  DevTools si M2 prefiere el flujo basado en cookie.
- **¿El precio depende de la tienda?** Sí. El payload de producto incluye un campo de
  precio por tienda física: `x_prices.<physicalStoreId>.mxn` (p.ej. `x_prices.1333.mxn`),
  además del array `price` global. La disponibilidad/inventario también es por tienda
  (`inventories.<storeCode>.quantity`, `inventories.total.quantity`).
- **¿HTML, XHR o Playwright?** El precio viene por **XHR/JSON** limpio (HCL Commerce
  REST), no requiere render JS. → **`source` esperado del adapter M2: `xhr`.**

## 2. Endpoints de precio (XHR) confirmados

### 2.1 Detalle de producto con precio (PDP) — endpoint principal de M2
- **URL (plantilla):**
  `GET https://www.homedepot.com.mx/search/resources/api/v2/products`
  `?storeId=10351&partNumber={PN}&catalogId=10101&langId=-5`
  `&physicalStoreId={STORE_ID}&contractId=4000000000000000003&currency=MXN`
  - Acepta múltiples `partNumber={PN}` repetidos para batch (varios SKUs en una llamada).
  - Variante por id interno: `&id={CATENTRY_ID}` en lugar de `partNumber`.
- **Método y headers clave (sin secretos):** `GET`. Headers observados: `Accept: application/json`,
  `Origin`/`Referer: https://www.homedepot.com.mx`, `User-Agent`. No requiere
  `Authorization` para precio público. (Cookie de sesión removida del HAR; ver §1.)
- **Params que seleccionan producto + zona:** producto = `partNumber` (o `id`);
  zona = `physicalStoreId` (+ `marketId`/`stLocId` en variantes de listado). `currency=MXN`.
- **Forma del payload de respuesta** (recortado y sanitizado; solo campos de precio/sku/unidad):
  ```json
  {
    "metaData": { "price": "1" },
    "total": 1,
    "contents": [
      {
        "partNumber": "482588",
        "id": "79197",
        "name": "VARILLA CORRUGADA RECTA R-42 1'' 12 METROS 1 TONELADA",
        "buyable": "true",
        "storeID": "10351",
        "currency-implicit": "MXN",
        "x_measurements.quantityMeasure": "C62",
        "price": [
          { "usage": "Offer",   "value": "20068.0", "currency": "MXN", "description": "I" },
          { "usage": "Display", "value": "20068.0", "currency": "MXN", "description": "L" }
        ],
        "x_prices.1333.mxn": "20068.0",
        "inventories.total.quantity": "7937.29"
      }
    ]
  }
  ```
  - **Campos de precio:** array `price[]` con dos entradas:
    `usage:"Offer"` (description `"I"`) = precio de venta/oferta vigente;
    `usage:"Display"` (description `"L"`) = precio de lista. `value` es **string**, `currency:"MXN"`.
    Cuando coinciden, no hay descuento. Además `x_prices.<physicalStoreId>.mxn` = precio
    de esa tienda (string).
  - **SKU / identificadores:** `partNumber` (SKU del retailer), `id` (catentry id interno).
  - **Disponibilidad:** `inventories.total.quantity` (string) e `inventories.<storeCode>.quantity`
    por tienda (p.ej. `inventories.M350.quantity`, `inventories.18503.quantity`).
  - **Unidad:** `x_measurements.quantityMeasure` (código UN/CEFACT; `C62` = pieza/unidad,
    `TN` = tonelada en `x_measurements.weightMeasure`).
  - **Nota sobre `value:""` / `"0.0"`:** el perfil `HDM_V2_findProductByIds_IncludeZeroPrices`
    devuelve productos SuperSKU "padre" con precio vacío; el precio real está en los SKU hijos
    (`items[]`) o se obtiene pidiendo el `partNumber`/`id` del SKU concreto. Para precio fiable,
    M2 debe pedir el SKU comprable (`buyable:"true"`) con `physicalStoreId` de la tienda.

### 2.2 Búsqueda/listado con precio (categoría/búsqueda "varilla")
- **URL (plantilla):**
  `GET /search/resources/api/v2/products`
  `?storeId=10351&searchTerm=varilla&limit=28&offset=0`
  `&profileName=HCL_V2_findProductsBySearchTermWithPrice`
  `&contractId=4000000000000000003&currency=MXN&langId=-5&marketId=10`
  `&physicalStoreId=1333&stLocId=18503&extendedCatalog=false&marketOnly=true`
  `&selectedFacets=...&minPrice=-1&maxPrice=-1&selectedPageOffset=0&orderBy=0`
- **Paginación:** `limit` (tamaño de página, observado `28`) + `offset` (0-based).
  La respuesta sigue la forma `{ metaData, contents:[...], total }`; `total` da el conteo
  para iterar `offset += limit`. (El **body** de esta llamada concreta NO quedó guardado en
  el HAR —content vacío— pero el mismo perfil y forma de respuesta están confirmados por las
  llamadas `findProductsByPartNumber`/`findProductByIds`, que sí traen `contents[].price`.)
- **Filtros de precio:** `minPrice`/`maxPrice` (`-1` = sin filtro); `selectedFacets` para
  facetas; `orderBy` para ordenamiento.

### 2.3 Inventario por tienda (endpoint auxiliar, confirma stock real)
- **URL:** `GET /wcs/resources/store/10351/inventoryavailability/{PN}[,{PN}...]`
- **Payload (sanitizado):**
  ```json
  {
    "InventoryAvailability": [
      {
        "partNumber": "482588",
        "productId": "79197",
        "physicalStoreName": "1333",
        "physicalStoreId": "18503",
        "availableQuantity": "0.0",
        "x_AvailableQuantityInMarket": "61.12",
        "unitOfMeasure": "TN",
        "inventoryStatus": "Available",
        "x_itemFulFillmentType": "Online Only"
      }
    ]
  }
  ```
- Útil para confirmar `inventoryStatus` y stock; **confirma el mapeo tienda**:
  `physicalStoreName:"1333"` ↔ `physicalStoreId:"18503"`.

### 2.4 Endpoints de soporte observados (no de precio, contexto)
- `GET /search/resources/api/v2/categories?storeId=10351&depthAndLimit=*&...` — árbol de categorías.
- `GET /search/resources/store/10351/sitecontent/suggestions` — autocompletado de búsqueda.
- `GET /wcs/resources/store/10351/hdm/physicalStore/ids` — catálogo de tiendas (ver §3).
- `GET /wcs/resources/store/10351/usercontext/@self/contextdata` — confirma `storeId`,
  `currency:MXN`, `languageId:-5`, sesión de invitado.

## 3. Ubicaciones que sirven la zona piloto (Monterrey Metro)
- **Tienda seleccionada en la captura (zona Monterrey):**
  - `external_id` (código/nombre de tienda, `physicalStoreName`): **`1333`** — es el valor
    enviado en `setDefault` (`defaultStore:"1333"`) y usado como `physicalStoreId=1333`/`stLocId=1333`
    en las llamadas de precio.
  - `physicalStoreId` interno (HCL): **`18503`** — aparece como `physicalStoreId` en
    `inventoryavailability` y como `stLocId=18503` en la búsqueda "varilla".
  - `marketId`: **`10`**.
  - → Para `RetailerLocation`: usar `external_id = 1333` (el código que el sitio acepta en
    `setDefault` y en `physicalStoreId`/`stLocId` para precio). Guardar también el id interno
    `18503` y `marketId 10` como metadatos de apoyo.
- **Limitación de la evidencia:** el HAR **no contiene el nombre humano ni la dirección** de la
  tienda 1333 (ningún body menciona "Monterrey"; el catálogo `physicalStore/ids` solo expone
  `storeName` numérico, `uniqueID` y `marketId`, sin ciudad). El catálogo `physicalStore/ids`
  lista ~muchas tiendas con `uniqueID` 12501+ y códigos `M###`/numéricos, pero **no** trae
  texto de ciudad. La confirmación de que `1333`/`18503` es físicamente una tienda de Monterrey
  proviene de que **Carlos la seleccionó manualmente** durante la captura (insumo humano).
  → Antes de poblar `ZoneLocationMap`, validar en Admin que `external_id=1333` corresponde a la
  tienda de Monterrey deseada (y, si se requieren más tiendas del área metro, repetir captura
  por tienda o consultar `physicalStore/ids` cruzando `marketId`/geolocalización).

## 4. Categoría piloto: varilla
- **Cómo se busca/navega:** búsqueda libre `searchTerm=varilla` contra
  `GET /search/resources/api/v2/products` con `profileName=HCL_V2_findProductsBySearchTermWithPrice`
  (ver §2.2). También hay árbol de categorías vía `/search/resources/api/v2/categories`
  (no se identificó un categoryId fijo de "varilla" en el HAR; la sesión usó búsqueda por término).
- **Producto de ejemplo confirmado:** `partNumber 482588` / id `79197` —
  *"VARILLA CORRUGADA RECTA R-42 1'' 12 METROS 1 TONELADA"*. Es un SuperSKU con `numberOfSKUs`
  variantes (distintos calibres/diámetros), `buyable:"true"`.
- **Campos disponibles para matching de SKU** (en `contents[].attributes[]`, cada uno
  `identifier`/`name`/`values[].value`):
  - `CALIBRE` → diámetro nominal, p.ej. `1"` (clave para varilla).
  - `LARGO` → longitud, p.ej. `12 m`.
  - `MATERIAL` → p.ej. `Acero`.
  - `MODELO` → p.ej. `R42`.
  - `TIPO` → p.ej. `Varilla corrugada recta`.
  - `PESO` → p.ej. `1 tonelada kg`.
  - `UPC` → código de barras, p.ej. `0099004825887` (excelente para matching exacto cross-retailer).
  - `raw_name` = campo `name`. Unidad de venta = `x_measurements.quantityMeasure`
    (`C62`=pieza, o `TN`=tonelada según producto).
  - Otros flags presentes: `FULFILLMENT_TYPE`, `STORE_ONLY_AVAILABLE`, `ONLINE_ONLY_SELLING_STORE`,
    `PRO_ONLINE_ONLY_SELLING_STORE`.

## 5. Riesgos / anti-bot observados
- **No se observó anti-bot** en el HAR: ningún challenge/captcha; sin headers ni cuerpos de
  Akamai bot-manager / DataDome / PerimeterX / reCAPTCHA / `_abck`. Todas las llamadas de
  precio respondieron `200` (los únicos `404` fueron `cart/@self` esperables en sesión invitada).
- **Stack:** HCL Commerce Cloud (`ec-version: 24d`, backend `*.prd.hdmx.now.hclsoftware.cloud`).
  Headers de seguridad estándar: `strict-transport-security` (max-age 86400),
  `x-frame-options: SAMEORIGIN`, `x-content-type-options`, `content-security-policy-report-only`
  (solo report). `cached_response: true` y `server-timing` sugieren CDN/caché de borde delante
  del API (favorable: respuestas cacheables, menor riesgo de rate-limit agresivo).
- **CORS:** `access-control-allow-origin: https://www.homedepot.com.mx` (mismo origen);
  un cliente server-side no usa CORS, pero conviene replicar `Origin`/`Referer` honestos.
- **Recomendaciones M2:** UA honesto de ConstruScan, delay mínimo por dominio, respetar
  caché (`cached_response`), batch de `partNumber` para reducir nº de requests, y **NO** forzar
  si en el futuro aparece challenge → entonces `non_viable`. Riesgo residual: el sitio podría
  introducir bot-manager más adelante (no garantizado por una sola captura).
- **Bloqueo real para `active`:** únicamente el gate ToS/robots humano (§0), no lo técnico.

## 6. Insumos crudos
- **HAR:** `docs/recon/har/www.homedepot.com.mx.har` (~8 MB, 265 entries; host principal
  `www.homedepot.com.mx`, 143 entries). **Gitignored** — no se versiona (contiene posible PII
  de sesión). Este documento solo transcribe extractos sanitizados.
- **Nota de privacidad:** el export ya venía **sin** headers `Cookie`/`Set-Cookie`/`Authorization`
  (removidos por el navegador/exportador); por eso §1 no puede nombrar la cookie de tienda.
  Ningún valor sensible, token ni PII se copió a este `.md`.
- **Endpoint estrella para M2 (`HomeDepotAdapter`, `source=xhr`):**
  `GET /search/resources/api/v2/products?storeId=10351&partNumber={PN}&catalogId=10101&langId=-5&physicalStoreId={STORE_ID}&contractId=4000000000000000003&currency=MXN`
  → leer `contents[0].price[]` (usage `Offer`/`Display`) y `x_prices.{STORE_ID}.mxn`;
  tienda piloto Monterrey: `external_id=1333` (internal `18503`, `marketId 10`).
