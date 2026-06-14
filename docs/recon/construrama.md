# Reconocimiento — Construrama (red CEMEX)

> Entregable de la Fase 0 del subsistema de scraping (PRD §9.2). Documenta
> CÓMO sirve precios este retailer por zona, para que M2 (adapters) se escriba
> sobre hechos confirmados, no supuestos. Transcrito por un agente a partir de un
> export **HAR** de una sesión de DevTools real (no se pegó a la red).

- **Retailer:** Construrama (`www.construrama.com`, red de distribuidores CEMEX)
- **Fecha de reconocimiento:** 2026-06-14
- **Autor:** Carlos (captura HAR) + agente Fase 0 (análisis offline)
- **Zona piloto reconocida:** Monterrey Metro (estado Nuevo León; se eligió/usó
  Monterrey y Guadalupe, N.L.)
- **Plataforma detectada:** **SAP Commerce Cloud (Hybris) accelerator storefront**
  (`_ui/responsive/...`, addons `construrama*addon`, `theme-construrama`, `acc.*.js`,
  URLs `/c/{categoryCode}` y `/p/{productCode}`, versión `?ver=V6.54.12`). El sitio
  es una **SPA con búsqueda servida por Algolia** (InstantSearch): `acc.algolia.js`,
  `instantsearch.js (4.65.0)`, índice `construrama_mx`. Monitoreo Dynatrace
  (`x-dt-tracestate`, `x-oneagent-js-injection`). Detrás de **CDN/WAF Imperva**
  (`x-cdn: Imperva`, `x-iinfo`). Dominios hermanos vistos en `x-frame-options`:
  `*.construrama.com`, `*.construramapro.com`, `*.construenvio.com`.

> **Nota de alcance de la evidencia (LÉASE PRIMERO).** El HAR de Construrama es
> **más pequeño y ruidoso** que el de Home Depot: 178 entries totales, de las que
> **solo ~35 son del host `construrama.com` + Algolia** (el resto es Google /
> Pinterest / DoubleClick / analytics, ignorado). Además, **muchos cuerpos de
> respuesta NO quedaron guardados** en el export (la página HTML inicial, el body de
> la búsqueda Algolia, `get/algolia`, `setStoresByCity`, `googleApiAutocomplete`).
> Por eso varias afirmaciones se apoyan en: (a) URLs y params de request (sí
> capturados), (b) el **rastro de navegación** que filtraron los beacons de Imperva
> (`rb_*`), que contienen el historial de URLs visitadas. Donde la evidencia es
> indirecta se marca **[indirecto]** y se indica qué confirmar en una 2ª captura.

## 0. Gate legal / ToS (obligatorio antes de cualquier request automatizado)
- [ ] Revisado `robots.txt` (`www.construrama.com/robots.txt`). **No se observó en el
  HAR** (el navegador no solicitó `robots.txt` en la sesión; su contenido NO está en
  la evidencia). Pendiente leerlo antes de M2.
- [ ] Revisados Términos de Servicio respecto a scraping/uso automatizado. Veredicto:
  **`PENDIENTE — requiere confirmación humana`** (decisión legal de Carlos, fuera del
  alcance del agente). No hay evidencia de ToS en el HAR.
- [x] Sin login ni evasión de anti-bot: la sesión analizada fue de **usuario invitado**
  (Algolia con `userToken=cma-anonymous-...`; el rastro muestra páginas públicas de
  catálogo `/c/` y `/p/`). Todas las llamadas observadas respondieron `200`; no se
  observó captcha resuelto ni flujo de login. **Pero ver §5: hay WAF/anti-bot Imperva
  activo** — esto sí pesa en la viabilidad técnica.
- [ ] User-Agent honesto definido; delay mínimo por dominio definido. Pendiente fijar
  en M2 (la captura usó UA real de iPhone/Safari; M2 debe usar un UA honesto de
  ConstruScan).
- **Decisión de viabilidad:** **`paused`** (mapea a `Retailer.scraper_status='paused'`).
  Doble bloqueo: (1) gate ToS/robots humano (§0), (2) **riesgo técnico real por Imperva**
  (§5). NO se habilita `active` hasta veredicto ToS explícito Y validar que un cliente
  server-side honesto no es bloqueado por el WAF. La capa de precio en sí (Algolia) es
  técnicamente accesible (§1–§2), pero el primer paso —cargar la página/abrir sesión—
  pasa por Imperva.

## 1. Mecanismo de zona/precio
- **Subpath de zona = ESTADO, no distribuidor individual.** El subpath observado es
  **`/nuevo-leon/`** (el estado Nuevo León), no `construrama.com/{slug-de-distribuidor}/`.
  Las URLs de catálogo aparecen en dos formas en el rastro:
  - con subpath de estado: `https://www.construrama.com/nuevo-leon/catalogo/aceros/varilla/c/005057`
  - sin subpath (raíz): `https://www.construrama.com/catalogo/aceros/varilla/c/005057`
  Es decir, **el subpath fija el estado/región**; la tienda/distribuidor concreto se
  selecciona aparte (selector de ciudad → store-finder) y se persiste en la **sesión**
  (cookie). El supuesto del PRD §9.1 de "`construrama.com/{distribuidor}/`" se matiza:
  lo que se vio es `construrama.com/{estado}/` (`nuevo-leon`), no un slug por sucursal.
  **Falta confirmar en 2ª captura** si existe además un nivel de slug por distribuidor
  cuando hay varias sucursales en la misma ciudad.
- **Cómo se fija la ciudad/zona:** flujo de **store-finder** vía dos XHR (host
  `construrama.com`, bajo el subpath de estado):
  1. `GET /nuevo-leon/store-finder/googleApiAutocomplete?input=monterrey`
     → autocompletado de ciudades (proxy a Google Places).
  2. `GET /nuevo-leon/store-finder/setStoresByCity?cityId={GOOGLE_PLACE_ID}&withStores=1&city={Ciudad}`
     → **verbo "set"**: fija la ciudad elegida en la **sesión** y devuelve las tiendas
     que la sirven. En la captura: `cityId=ChIJ9fg3tDGVYoYRlJjIasrT06M`
     (place_id de Monterrey), `city=Monterrey, N.L., México`.
  - **El cuerpo de `setStoresByCity` NO se guardó** (size 1024 B, sin texto) → no
    tenemos el JSON con la lista de tiendas/distribuidores ni sus IDs. **[indirecto]**
    El rastro de Imperva muestra que la zona efectiva quedó en Monterrey/Guadalupe N.L.
    (`$a=...|Monterrey^c N.L.^c México|...|67615451...` y `...|Guadalupe^c N.L.^c México|...`;
    `67xxxx` = código postal usado en geocoding, NO PII). → Ver §3.
- **Cookie de zona:** **NO se puede nombrar** — el export trae los `Set-Cookie`
  **removidos** (count 0 en todas las respuestas, igual que en el HAR de Home Depot).
  El mecanismo (sesión Hybris fijada por `setStoresByCity`) es claro; el nombre de la
  cookie de tienda/zona queda **pendiente de una 2ª captura con DevTools** (mirar
  `Set-Cookie` tras `setStoresByCity`; típicamente Hybris usa `JSESSIONID` +
  cookie/atributo de `currentStore`/`activeStore`).
- **¿HTML, XHR o Playwright? → el precio viene por XHR/JSON (Algolia).** Evidencia:
  - La búsqueda de "varilla" se resuelve contra **Algolia**
    (`POST https://njvy3eu5dw-dsn.algolia.net/1/indexes/*/queries`, índice
    `construrama_mx`), y el **filtro de la query incluye el precio**:
    `filters = allCategories_string_mv:OSS7Category AND (OSS7_priceValue_mxn_double > 0)`.
    → el **precio es un atributo del registro Algolia** (`OSS7_priceValue_mxn_double`),
    por lo que la respuesta JSON de Algolia trae el precio sin render. **[indirecto:**
    el body de respuesta de Algolia NO se guardó (276 KB, `hasText:false`), así que no
    pudimos listar los nombres exactos de campos de la respuesta; el nombre del campo
    de precio se infiere del filtro de la request, que sí se capturó].
  - El sitio es una SPA (SAP Commerce + InstantSearch); el HTML inicial **no** se
    capturó, así que no se puede afirmar que el precio venga server-rendered en el DOM.
  - **`source` esperado del adapter M2: `xhr`** (consultar Algolia directamente), con
    **plan B `playwright`** si el WAF Imperva bloquea el cliente httpx (ver §5). NO se
    necesita render JS para *leer* el precio una vez que se obtiene la respuesta Algolia;
    el riesgo no es el render sino el **gate Imperva** previo.

## 2. Endpoints de precio (XHR) confirmados

### 2.1 Búsqueda/listado de productos con precio — Algolia (fuente principal de M2)
- **URL (plantilla):**
  `POST https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=...`
  - App ID observado: `njvy3eu5dw` (es público — viaja en el host y en header
    `x-algolia-application-id`). La **Search API key** viaja en header
    `x-algolia-api-key` → **redactada en este doc** (es una search-only key pública del
    front, pero no se commitea por higiene; M2 debe re-obtenerla del bundle del front o
    del endpoint `get/algolia`, ver §2.3).
- **Método y headers clave (sin secretos):** `POST`,
  `content-type: application/x-www-form-urlencoded`, `Origin: https://www.construrama.com`,
  `Accept: */*`. Headers de credencial Algolia (`x-algolia-api-key`,
  `x-algolia-application-id`) **redactados**.
- **Body (multi-query InstantSearch, sanitizado):**
  ```json
  {
    "requests": [
      {
        "indexName": "construrama_mx",
        "params": "query=varilla&hitsPerPage=5&clickAnalytics=true&facets=%5B%5D&filters=allCategories_string_mv%3AOSS7Category%20AND%20(OSS7_priceValue_mxn_double%20%3E%200)&userToken=cma-anonymous-..."
      },
      {
        "indexName": "construrama_mx_query_suggestions",
        "params": "query=varilla&hitsPerPage=4&filters=&userToken=cma-anonymous-..."
      }
    ]
  }
  ```
  - **Índice de productos:** `construrama_mx`. Índice de sugerencias:
    `construrama_mx_query_suggestions`.
  - **Campo de precio:** `OSS7_priceValue_mxn_double` (precio en MXN, tipo double).
    El prefijo **`OSS7`** (también en `OSS7Category` y el filtro de categoría) parece
    ser un **código de catálogo/zona/lista de precios** del distribuidor o región
    activa — es decir, **el precio sí es por zona** y vive en un atributo namespaced.
    **[Pendiente confirmar]** si `OSS7` cambia al elegir otra ciudad/distribuidor (de
    ser así, M2 debe leer ese prefijo de `get/algolia` o del contexto de sesión, no
    hardcodearlo). Esto es lo más importante a verificar en una 2ª captura: cambiar de
    zona y volver a buscar "varilla" para ver si el filtro pasa a `OSS<otro>_priceValue`.
  - **Forma de la respuesta (estructura estándar Algolia, NO capturada — inferida):**
    `{ "results": [ { "index":"construrama_mx", "hits":[ {...} ], "nbHits":N,
    "page":0, "nbPages":M, "hitsPerPage":5 } , {...suggestions...} ] }`. Cada `hit`
    incluye `objectID`, nombre, `OSS7_priceValue_mxn_double`, atributos de categoría
    y la URL del PDP. **[indirecto: el body real (276 KB) no quedó en el export;
    confirmar los nombres exactos de campos de `hits[]` en una 2ª captura].**
- **Paginación:** parámetros Algolia `page` (0-based) + `hitsPerPage`. En la captura
  `hitsPerPage=5` porque es la **búsqueda-as-you-type del header** (autocomplete);
  la página de resultados completa (PLP) usa el mismo índice con `hitsPerPage` mayor y
  `page` incremental, hasta `nbPages`. **[Pendiente confirmar `hitsPerPage` real del PLP
  en 2ª captura].** Además existe la paginación de Hybris en la URL de la PLP
  (sufijo `,2`, `,3`… → `.../c/005057,2`), que el front mapea a `page` de Algolia.

### 2.2 Páginas de catálogo (PLP / PDP) — solo URLs, sin precio embebido confirmado
> Estas URLs salieron del **rastro de navegación de los beacons Imperva** (no se
> capturó su HTML). Sirven para mapear la estructura, no como fuente de precio.
- **PLP (listado de categoría "varilla"):**
  `GET /nuevo-leon/catalogo/aceros/varilla/c/005057`  (categoryCode = `005057`).
  Paginación: `/c/005057,2`, `/c/005057,3`, …
- **PDP (detalle de producto):**
  `GET /nuevo-leon/catalogo/aceros/varilla/varilla/{slug}/p/{productCode}`
  - Ej.: `.../varilla-corrugada-grado-42-de-12-915-m-kilogramos/p/6000111693`
  - Ej.: `.../varilla-corrugada-grado-42-de-38-915-m-kilogramos/p/6000111692`
  - `productCode` numérico de 10 dígitos (`6000111693`, `6000111692`).
- **No confirmado:** si el HTML del PDP trae el precio server-rendered en el DOM. El
  precio sí está en Algolia (§2.1), que es la ruta preferida para M2. Si M2 necesitara
  el PDP, **falta una 2ª captura** que guarde el HTML para localizar el selector.

### 2.3 Endpoint de configuración Algolia (auxiliar)
- **URL:** `GET /nuevo-leon/get/algolia` (respuesta `application/json`, ~168–215 B
  gzip). **Body NO capturado.** **[indirecto]** Por nombre y tamaño, devuelve la
  config Algolia del contexto activo (probablemente `appId`, search key pública y/o el
  nombre de índice / prefijo de zona `OSS7`). → **Útil para M2**: en lugar de
  hardcodear credenciales/índice, M2 podría leerlas de aquí por estado/zona. Confirmar
  el JSON exacto en 2ª captura.

### 2.4 Store-finder (selección de zona, no de precio) — ver §1 y §3
- `GET /nuevo-leon/store-finder/googleApiAutocomplete?input={texto}` → autocompletar ciudad.
- `GET /nuevo-leon/store-finder/setStoresByCity?cityId={GOOGLE_PLACE_ID}&withStores=1&city={Ciudad}`
  → fija ciudad en sesión + devuelve tiendas (body no capturado).

## 3. Ubicaciones que sirven la zona piloto (Monterrey Metro)
- **Estado/región (subpath):** `nuevo-leon` → este es el valor que ancla la zona en
  la URL del catálogo. Para `RetailerLocation`/`ZoneLocationMap`, el subpath de estado
  `nuevo-leon` es un insumo seguro.
- **Ciudad seleccionada en la captura:** **Monterrey, N.L.** (también se tocó
  **Guadalupe, N.L.**, municipio del área metropolitana de Monterrey). La ciudad se
  fija con `setStoresByCity` usando el **Google Place ID** `ChIJ9fg3tDGVYoYRlJjIasrT06M`
  (= Monterrey) y `city=Monterrey, N.L., México`.
- **Distribuidor/sucursal concreta: NO determinada por la evidencia.** El body de
  `setStoresByCity` (que listaría las tiendas con sus IDs/`external_id`) **no se guardó
  en el export**. Tampoco se capturó un endpoint de "set default store" con un store-id
  (a diferencia de Home Depot, que sí tenía `setDefault` con `defaultStore:"1333"`).
  → **Pendiente de 2ª captura:** elegir explícitamente una sucursal en el store-finder
  y capturar el JSON de `setStoresByCity`/respuesta del selector para extraer el
  `external_id`/store code del distribuidor de Monterrey, e identificar si el prefijo
  `OSS7` del precio (§2.1) corresponde a esa tienda/lista de precios.
- **Insumo accionable para M2 hoy:** zona = `nuevo-leon` (subpath) + ciudad Monterrey
  (place_id `ChIJ9fg3tDGVYoYRlJjIasrT06M`). El store-id del distribuidor concreto se
  curará en Admin tras la 2ª captura.

## 4. Categoría piloto: varilla
- **Cómo se busca/navega:**
  - **Búsqueda libre:** `query=varilla` contra Algolia índice `construrama_mx`
    (§2.1). Es la ruta más directa y la que M2 debería usar.
  - **Navegación por categoría:** árbol `aceros → varilla`, categoryCode **`005057`**,
    URL `/nuevo-leon/catalogo/aceros/varilla/c/005057` (la PLP también consume Algolia
    vía InstantSearch, filtrando por la categoría).
- **Productos de ejemplo confirmados (del rastro):**
  - `productCode 6000111693` — *"varilla corrugada grado 42 de 1/2", 9.15 m, kilogramos"*
    (slug `varilla-corrugada-grado-42-de-12-915-m-kilogramos`; "12" = diámetro 1/2",
    "915" = 9.15 m de largo).
  - `productCode 6000111692` — *"varilla corrugada grado 42 de 3/8", 9.15 m, kilogramos"*
    (slug `...grado-42-de-38-915-m-kilogramos`; "38" = 3/8").
- **Campos disponibles para matching de SKU** (extraídos de slug/estructura; los
  nombres exactos de atributos Algolia faltan por captura de la respuesta):
  - `raw_name` / nombre del producto (en el slug y, se asume, en el `hit` de Algolia).
  - **Marca:** no aparece en el slug del ejemplo (varilla genérica de la red); confirmar
    si Algolia trae atributo de marca.
  - **Calibre/diámetro:** `1/2"`, `3/8"` (clave para varilla; codificado como `12`/`38`
    en el slug).
  - **Grado:** `grado 42` (calidad del acero / `R42`, equivalente al `R-42` visto en
    Home Depot → buen campo cross-retailer).
  - **Longitud:** `9.15 m` (`915` en el slug; varilla comercial de 9.15 m / 12 m).
  - **Unidad de venta:** `kilogramos` (en el slug; difiere de Home Depot que vendía por
    tonelada/pieza → cuidar normalización de unidad en el matching).
  - **`objectID` de Algolia** y **`productCode`** (`6000111693`) como identificadores de
    SKU del retailer.
  - **Precio:** `OSS7_priceValue_mxn_double` (MXN), atributo del `hit` (§2.1).
- **Limitación:** sin el body de Algolia no se listan TODOS los facets/atributos de
  matching disponibles. **[Pendiente 2ª captura]** para enumerar `hits[]` completo
  (marca, UPC/EAN si existe, facetas de diámetro/grado/largo).

## 5. Riesgos / anti-bot observados
- **WAF / anti-bot = Imperva (Incapsula) — ACTIVO y relevante.** Evidencia:
  - Header `x-cdn: Imperva` y `x-iinfo: 61-98904768-... PNNy RT(...) q(...) r(...)`
    (formato de telemetría Incapsula) en **todas** las respuestas de `construrama.com`.
  - Beacon de reputación de cliente: `POST /rb_bf25878uck?type=js3&sn=v_4_srv_8_sn_...`
    (`server: Apache`, `text/plain`) — es el endpoint de **client reputation /
    fingerprinting** de Imperva; el front lo llama repetidamente con telemetría del
    navegador (incluye el rastro de navegación que aquí explotamos).
  - Endpoint con **path ofuscado/aleatorio**
    `POST /t-is-Thought-sharewingdome-timely-Fortall-bals-C?d=www.construrama.com`
    (`server: bon`, `access-control-allow-origin: *`) — patrón típico de **Imperva
    Advanced Bot Protection** (recolección de señales JS). `server: bon` es de la malla
    de bot-mitigation de Imperva.
  - En el rastro aparece `captchaaddon.js` (`addons/captchaaddon/.../captchaaddon.js`)
    → el storefront **tiene capacidad de captcha**, aunque **en esta sesión no se
    disparó ningún challenge** (todo `200`, sin reCAPTCHA/hCaptcha en la red).
  - **Implicación para M2:** Imperva puede exigir ejecución de su JS de fingerprinting
    para no marcar al cliente como bot. Un `httpx`/`selectolax` "pelón" **podría ser
    bloqueado o servido un challenge** en la carga inicial de la página o de la sesión.
    Por eso `source=xhr` (Algolia) es el plan A pero **con riesgo**, y **Playwright**
    (que ejecuta el JS de Imperva y obtiene cookies válidas) es un **plan B realista**
    para esta tienda — más probable que en Home Depot, donde no se vio anti-bot.
- **Otros headers:** `content-security-policy` (con `cxprod-cdn.cemex.com`, confirma
  CEMEX), `strict-transport-security` (max-age 1 año), `x-content-type-options: nosniff`,
  `x-xss-protection`, `referrer-policy: same-origin`, `permissions-policy: geolocation=(self)`.
  Monitoreo **Dynatrace** (`x-dt-tracestate`, `x-oneagent-js-injection`, `server-timing:
  dtSInfo/dtRpid`) — APM, no anti-bot, pero implica observabilidad del lado del retailer.
- **CORS de Algolia:** la búsqueda va a `*.algolia.net` con `Origin:
  https://www.construrama.com` y la search key pública. Un cliente server-side **podría
  consultar Algolia directamente** (sin pasar por Imperva) **si** obtiene App ID + search
  key + nombre de índice + prefijo de zona `OSS7` — todos públicos en el front
  (`get/algolia` / bundle). **Esto es lo más prometedor**: si M2 va directo a Algolia
  para precio, **evita el WAF Imperva** del host construrama.com. **Pendiente confirmar**
  que la search key no está restringida por `Referer`/`allowedSources`.
- **Recomendaciones M2:**
  1. Plan A: consultar **Algolia directamente** (índice `construrama_mx`, campo
     `OSS7_priceValue_mxn_double`), obteniendo credenciales/índice de `get/algolia` por
     zona; UA honesto; delay por dominio. Esto evita Imperva.
  2. Plan B: si la search key está restringida por Referer o si se necesita el contexto
     de sesión/zona, usar **Playwright** para ejecutar el JS de Imperva, fijar la zona
     (`setStoresByCity`) y capturar la respuesta Algolia desde el navegador.
  3. **NO** forzar si aparece challenge/captcha sostenido → entonces `non_viable`.
- **Bloqueo real para `active`:** (a) gate ToS/robots humano (§0), y (b) **validar
  empíricamente** que el camino elegido (Algolia directo o Playwright) no es bloqueado
  por Imperva. A diferencia de Home Depot, aquí lo técnico **sí** es un riesgo abierto.

## 6. Insumos crudos
- **HAR:** `docs/recon/har/www.construrama.com.har` (~6.3 MB, 178 entries; del host
  `www.construrama.com` solo **33** entries + **2** a `njvy3eu5dw-dsn.algolia.net`; el
  resto es ruido de Google/Pinterest/DoubleClick/analytics). **Gitignored** — no se
  versiona (posible PII de sesión). Este documento solo transcribe extractos sanitizados.
- **Nota de privacidad:** el export venía **sin** `Cookie`/`Set-Cookie`/`Authorization`
  (removidos) → §1 no puede nombrar la cookie de zona. La **search API key de Algolia**
  (`x-algolia-api-key`) y el **App ID** existen en el HAR pero se **redactaron** aquí
  (el App ID `njvy3eu5dw` se cita por ser parte del host público, sin la key). Ningún
  token, cookie ni PII se copió a este `.md`. Los códigos `67615451`/`67554194` que
  aparecen en los beacons son **códigos postales** de geocoding (Monterrey/Guadalupe),
  no datos personales.
- **Limitaciones de evidencia (resumen):** NO se capturaron los **bodies** de: HTML de
  página, respuesta de Algolia (`construrama_mx`), `get/algolia`, `setStoresByCity`,
  `googleApiAutocomplete`. Lo que SÍ se confirmó: estructura de URLs (catálogo `/c/`,
  producto `/p/`, subpath de estado `nuevo-leon`), que **el precio se sirve por Algolia**
  (`OSS7_priceValue_mxn_double` en el filtro de la query), el flujo de zona por
  `store-finder/setStoresByCity`, la plataforma (SAP Commerce/Hybris) y el **anti-bot
  Imperva**. → Antes de M2 se requiere una **2ª captura** dirigida a: (1) guardar el
  body de Algolia (nombres de campos de `hits[]`), (2) guardar `setStoresByCity` y
  `get/algolia` (store-id del distribuidor de Monterrey + prefijo de zona `OSS7`),
  (3) ver `Set-Cookie` de la sesión, (4) probar si Algolia responde a un cliente
  server-side sin pasar por Imperva.
- **Endpoint estrella tentativo para M2 (`ConstruramaAdapter`, `source=xhr` con plan B
  `playwright`):**
  `POST https://njvy3eu5dw-dsn.algolia.net/1/indexes/*/queries`
  body `{"requests":[{"indexName":"construrama_mx","params":"query=varilla&hitsPerPage=N&page=0&filters=allCategories_string_mv:OSS7Category AND (OSS7_priceValue_mxn_double > 0)&userToken=cma-anonymous-..."}]}`
  → leer `results[0].hits[].OSS7_priceValue_mxn_double` (MXN) + `objectID`/`productCode`;
  zona piloto: estado `nuevo-leon`, ciudad Monterrey (place_id `ChIJ9fg3tDGVYoYRlJjIasrT06M`),
  distribuidor/store-id **pendiente de 2ª captura**.
