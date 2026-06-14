# Reconocimiento — <Retailer>

> Entregable de la Fase 0 del subsistema de scraping (PRD §9.2). Documenta
> CÓMO sirve precios este retailer por zona, para que M2 (adapters) se escriba
> sobre hechos confirmados, no supuestos. **Lo llena un humano** (Carlos) a partir
> de una sesión de DevTools en el sitio real, o entregando un export **HAR** que
> un agente analiza y transcribe aquí. Nada de "TBD" en las secciones obligatorias.

- **Retailer:** <nombre> (`<dominio>`)
- **Fecha de reconocimiento:** <YYYY-MM-DD>
- **Autor:** <quién>
- **Zona piloto reconocida:** Monterrey Metro

## 0. Gate legal / ToS (obligatorio antes de cualquier request automatizado)
- [ ] Revisado `robots.txt` (`<dominio>/robots.txt`). Rutas relevantes: ¿permitidas? <sí/no, citar>
- [ ] Revisados Términos de Servicio respecto a scraping/uso automatizado. Veredicto: <ok / restringido / no viable>
- [ ] Sin login ni evasión de anti-bot (guardrail §2.3.1/2.3.2).
- [ ] User-Agent honesto definido; delay mínimo por dominio definido.
- **Decisión de viabilidad:** `active` | `paused` | `non_viable` (mapea a `Retailer.scraper_status`).

## 1. Mecanismo de zona/precio
- ¿Cómo se fija la zona? (selector de tienda + cookie / subpath de distribuidor + selector de ciudad / otro)
- Nombre(s) de cookie y/o parámetro que fija la zona. Cómo se obtiene/renueva.
- ¿El precio viene en HTML crudo, vía XHR/JSON, o requiere render JS (Playwright)? → `source` esperado: `xhr` | `html` | `playwright`.

## 2. Endpoints de precio (XHR) confirmados
Por cada endpoint relevante:
- **URL** (con plantilla de params): `<...>`
- **Método** y headers clave (sin secretos): `<...>`
- **Params / body** que seleccionan producto + zona: `<...>`
- **Forma del payload de respuesta** (campos de precio, disponibilidad, SKU, moneda, unidad): pegar un ejemplo recortado.
- **Paginación / listado** (cómo se listan productos de una categoría): `<...>`

## 3. Ubicaciones que sirven la zona piloto (Monterrey Metro)
- Tienda(s) Home Depot / distribuidor(es) Construrama que sirven la zona: `external_id`, nombre, subpath/store_id.
- → estos alimentan `RetailerLocation` + `ZoneLocationMap` (curación en Admin).

## 4. Categoría piloto: varilla
- Cómo se navega/busca "varilla" en este retailer; IDs de categoría si aplica.
- Campos disponibles para matching de SKU (`raw_name`, marca, calibre/diámetro/longitud, unidad).

## 5. Riesgos / anti-bot observados
- Captchas, rate limits, bloqueos, fingerprinting detectados. Si bloquea → `non_viable`, se omite (no se fuerza).

## 6. Insumos crudos
- Ruta del HAR / capturas usadas como evidencia (no versionar payloads con PII).
