# Review F011 — Reconocimiento Construrama (Fase 0)

Veredicto: APROBADO

> Feature de **capa docs** (no toca código). La verificación es de **completitud
> del entregable** y de **higiene/privacidad** (el `.md` se commitea), NO de
> `./init.sh` por capas. Aun así se corrió `./init.sh --quick` para confirmar la
> higiene del arnés (VERDE). Revisor: reviewer del arnés. Fecha: 2026-06-14.
> Precedente análogo: F010 (Home Depot), también capa docs sin `impl_<id>`.

Insumos revisados:
- `specs/F011-recon-construrama.md`
- `docs/recon/TEMPLATE.md`
- `docs/recon/construrama.md` (entregable)
- `CHECKPOINTS.md` (sección "Higiene del arnés")

Nota de proceso: igual que F010, esta feature de capa docs **no tiene
`progress/impl_F011_docs.md`** (el HAR lo analiza un subagente y transcribe el
`.md` directamente). Es consistente con el precedente F010 y no es defecto.

---

## 1. Criterios de aceptación de la spec F011

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Existe `docs/recon/construrama.md` siguiendo el TEMPLATE, sin "TBD" en 0–4 (marcas `[indirecto]`/`pendiente 2ª captura` son honestidad válida, NO TBD vacío) | **CUMPLE** | `grep -in "TBD" docs/recon/construrama.md` → **VACÍO** (exit 1). Estructura idéntica al `TEMPLATE.md` vía `grep -nE "^#{1,3} "`: secciones 0–6 + subsecciones 2.1–2.4. Donde la evidencia es limitada el doc usa marcas explícitas `[indirecto]` / `Pendiente 2ª captura` (p.ej. líneas 76, 92, 142–147, 192–198), que es honestidad, no un TBD. |
| 2 | Gate ToS/robots (sección 0) con veredicto explícito + `scraper_status` propuesta (`paused`) | **CUMPLE** | §0 líneas 37–39: ToS = `` `PENDIENTE — requiere confirmación humana` `` (válido por spec). Líneas 34–36: robots.txt no quedó en el HAR → pendiente leerlo antes de M2 (justificado). Línea 48: **Decisión de viabilidad: `paused`** (mapea a `Retailer.scraper_status='paused'`), con doble bloqueo razonado: gate ToS humano + riesgo técnico Imperva (§5). |
| 3 | Mecanismo de zona confirmado: subpath de estado (`nuevo-leon`) + cómo se fija la ciudad (`setStoresByCity`) + si los precios son XHR o requieren render (`source` con evidencia) | **CUMPLE** | §1 líneas 56–66: subpath de **estado** `/nuevo-leon/` (matiza el supuesto del PRD §9.1 de slug-por-distribuidor, honestamente). Líneas 67–79: ciudad fijada vía `GET /nuevo-leon/store-finder/setStoresByCity?cityId={GOOGLE_PLACE_ID}&withStores=1&city=...` (verbo "set" → sesión). Líneas 86–101: **`source=xhr`** (precio servido por Algolia, índice `construrama_mx`, campo `OSS7_priceValue_mxn_double` presente en el filtro de la query capturada) con plan B `playwright` si Imperva bloquea. Concluye `source` con evidencia. |
| 4 | Lista distribuidor(es)/zona de Monterrey como insumo para `RetailerLocation` (store-id pendiente de 2ª captura debe decirse explícitamente + dar lo accionable hoy) | **CUMPLE** | §3 líneas 184–201: insumo accionable hoy = estado `nuevo-leon` (subpath) + ciudad Monterrey (Google place_id `ChIJ9fg3tDGVYoYRlJjIasrT06M`). El store-id del distribuidor concreto se declara **explícitamente pendiente de 2ª captura** (líneas 191–198: el body de `setStoresByCity` no se guardó) y se difiere a curación en Admin. La limitación está dicha, no escondida. |

**Extras del entregable (no exigidos, suman valor):** §2.1 body multi-query
InstantSearch sanitizado + paginación Algolia (`page`/`hitsPerPage`); §2.2 PLP/PDP
(categoryCode `005057`, productCodes `6000111693`/`6000111692`); §2.3 endpoint
auxiliar `get/algolia`; §4 campos de matching de varilla (diámetro/grado/longitud/
unidad `kilogramos`); §5 análisis del anti-bot **Imperva** y la ruta directa a
Algolia para esquivar el WAF.

---

## 2. Verificación de privacidad (CRÍTICA — el `.md` SÍ se commitea)

### 2.1 Grep de patrones sensibles
Comando:
```
grep -inE "set-cookie|cookie:|authorization|bearer|x-algolia-api-key|password|sessionid|jsessionid=" docs/recon/construrama.md
```
Salida (7 líneas, **todas descriptivas — sin valores reales**):
```
80:- **Cookie de zona:** **NO se puede nombrar** — el export trae los `Set-Cookie`
84:  `Set-Cookie` tras `setStoresByCity`; típicamente Hybris usa `JSESSIONID` +
110:    `x-algolia-api-key` → **redactada en este doc** (es una search-only key pública del
115:  `Accept: */*`. Headers de credencial Algolia (`x-algolia-api-key`,
286:- **Nota de privacidad:** el export venía **sin** `Cookie`/`Set-Cookie`/`Authorization`
288:  (`x-algolia-api-key`) y el **App ID** existen en el HAR pero se **redactaron** aquí
302:  (3) ver `Set-Cookie` de la sesión, (4) probar si Algolia responde a un cliente
```
Veredicto privacidad: **OK**. Las 7 coincidencias son menciones descriptivas
("`Set-Cookie` removidos", "key redactada", "`JSESSIONID`" citado como el nombre
que Hybris *típicamente* usa — no un valor real). Expresamente permitidas por la spec.

### 2.2 Confirmación de que la search API key de Algolia NO aparece
Comando:
```
grep -inE "x-algolia-api-key: *[A-Za-z0-9]{16,}|[a-f0-9]{32}" docs/recon/construrama.md
```
Salida: **VACÍO** (exit 1). No hay ningún valor real de search key ni hash de 32 hex.

Solo aparece el **App ID público** `njvy3eu5dw` (líneas 88, 108, 283, 289, 306),
que es aceptable por la spec (viaja en el host público y en `x-algolia-application-id`).

### 2.3 userToken y tokens largos
- `grep -in "userToken"` → 4 hits, todos **truncados a `cma-anonymous-...`** (sesión
  anónima de invitado, sin PII; líneas 41, 123, 127, 307).
- Strings de ≥24 chars restantes: Google Place ID `ChIJ9fg3tDGVYoYRlJjIasrT06M`
  (identificador público de Monterrey, no secreto), slugs de producto y la ruta
  ofuscada de Imperva (patrón de URL público). **Ningún secreto.**
- El propio doc (líneas 290–292) aclara que los códigos `67615451`/`67554194` son
  **códigos postales** de geocoding (Monterrey/Guadalupe), no PII.

### 2.4 HAR gitignored y no trackeado

| Comprobación | Comando | Resultado |
|--------------|---------|-----------|
| HAR ignorado por git | `git check-ignore docs/recon/har/www.construrama.com.har` | Matchea → `docs/recon/har/www.construrama.com.har` ✔ (exit 0) |
| Reglas de `.gitignore` | `grep -niE "har\|recon" .gitignore` | Líneas 23–25: comentario + `docs/recon/har/` + `*.har` ✔ |
| HAR (y toda la carpeta) NO trackeado | `git ls-files docs/recon/har/` | **VACÍO** ✔ (incl. `LEEME.txt`, `check-ignore` exit 0) |
| HAR existe en disco | `ls -la docs/recon/har/` | `www.construrama.com.har` ~6.35 MB (coincide con §6 del doc: ~6.3 MB) ✔ |

---

## 3. Higiene del arnés (CHECKPOINTS.md)

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `git status` solo el deliverable docs + progress/feature_list | **CUMPLE** | `git status --porcelain` → única línea: `?? docs/recon/construrama.md`. Filtrado fuera de `docs/recon\|progress\|feature_list.json` → **VACÍO** (exit 1). `progress/` y `feature_list.json` ya estaban commiteados (sin cambios pendientes). |
| Sin cambios en capas de código | **CUMPLE** | `git status --porcelain backend/ frontend/ e2e/` → **VACÍO**. |
| `feature_list.json` JSON válido, ≤1 `in_progress` | **CUMPLE** | `init.sh` Fase 1: "feature_list.json es JSON válido (array)" + "features in_progress: 1 (máximo 1)" (es F011, confirmado en `feature_list.json` línea 147). |
| `progress/current.md` refleja la sesión | **CUMPLE** | `progress/current.md` → "Feature en curso: F011" con plan de capa docs coherente (HAR offline, source xhr/render, ToS pendiente, privacidad). |
| Toda feature `done` tiene review APROBADO | **CUMPLE** | `init.sh` Fase 1: "las 20 feature(s) 'done' tienen review APROBADO". |
| Repo git inicializado | **CUMPLE** | `git rev-parse` responde; `init.sh` Fase 0: "repositorio git inicializado". |

---

## 4. Output real de `./init.sh --quick`

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
  ✔ las 20 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ saltada en modo --quick

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
  ◌ build saltado en modo --quick
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ◌ saltada (usa ./init.sh --e2e para correrla)

════════ Resumen ════════
  ✔ 30 ok   ✘ 0 fallos   ◌ 5 pendientes
  VERDE — el arnés está en estado consistente.
```

(Los 5 `◌` pendientes son esperables en `--quick`: jq/docker opcionales, infra/build/e2e saltados.)

---

## 5. Conclusión

Los 4 criterios de aceptación de `specs/F011` **CUMPLEN**. El entregable
`docs/recon/construrama.md` sigue el TEMPLATE (secciones 0–6 + 2.1–2.4), está
libre de "TBD", y donde la evidencia es indirecta lo marca con honestidad
(`[indirecto]` / `Pendiente 2ª captura`) en vez de inventar. Registra el gate ToS
con veredicto explícito (`PENDIENTE — requiere confirmación humana`) y
`scraper_status=paused`; confirma el mecanismo de zona (subpath de **estado**
`nuevo-leon` + ciudad vía `setStoresByCity`) y concluye **`source=xhr`** (precio
en Algolia `OSS7_priceValue_mxn_double`, con plan B `playwright` por el WAF
Imperva); y aporta el insumo accionable de Monterrey (estado `nuevo-leon` +
place_id Monterrey), declarando el store-id del distribuidor como pendiente de 2ª
captura.

La verificación de privacidad es limpia: ningún valor real de cookie/token/auth/
search-key en el `.md` (solo el App ID público `njvy3eu5dw`); HAR gitignored y no
trackeado. La higiene del arnés está **VERDE** (`./init.sh --quick`), con solo el
deliverable de la capa docs como cambio y sin código de capas tocado.

**Nota para el líder (no bloqueante, ya señalada en el propio doc):** antes de
F012/M2 quedan cierres pendientes que son precondiciones de M2, no defectos de
esta Fase 0 — (a) veredicto legal ToS de Carlos; (b) lectura de `robots.txt`
real; (c) una **2ª captura dirigida** para: body de Algolia (campos de `hits[]`),
`setStoresByCity`/`get/algolia` (store-id del distribuidor + prefijo de zona
`OSS7`), `Set-Cookie` de sesión, y validar si Algolia responde a un cliente
server-side sin pasar por Imperva.

Veredicto: **APROBADO**.
