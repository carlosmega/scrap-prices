# Review F010 — Reconocimiento Home Depot MX (Fase 0)

Veredicto: APROBADO

> Feature de **capa docs** (no toca código). La verificación es de **completitud
> del entregable** y de **higiene/seguridad**, NO de `./init.sh` por capas. Aun así
> se corrió `./init.sh --quick` para confirmar la higiene del arnés (VERDE).
> Revisor: reviewer del arnés. Fecha: 2026-06-14.

Insumos revisados:
- `specs/F010-recon-homedepot.md`
- `docs/recon/TEMPLATE.md`
- `docs/recon/homedepot.md` (entregable)
- `CHECKPOINTS.md` (sección "Higiene del arnés")

---

## 1. Criterios de aceptación de la spec F010

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Existe `docs/recon/homedepot.md` siguiendo el TEMPLATE, sin "TBD" en secciones 0–4 | **CUMPLE** | `grep -ni "TBD" docs/recon/homedepot.md` → sin coincidencias. Headers del doc (secciones 0–6 + subsecciones 2.1–2.4) coinciden con `TEMPLATE.md` vía `grep -nE "^#{1,3} "`. Lo único "pendiente" es el gate ToS (permitido) y robots.txt (justificado: no quedó en el HAR). |
| 2 | Gate ToS/robots (sección 0) con veredicto explícito + `scraper_status` propuesta | **CUMPLE** | Línea 21: ToS = `` `PENDIENTE — requiere confirmación humana` `` (válido por spec). Línea 28: **Decisión de viabilidad: `paused`** (mapea a `Retailer.scraper_status`). Líneas 29–30 justifican por qué no es `active` aún (gate humano), y línea 208 contempla `non_viable` si aparece challenge. |
| 3 | ≥1 endpoint XHR de precio con forma de payload (ejemplo recortado) + cómo se fija tienda/zona | **CUMPLE** | §2.1 (líneas 55–104): `GET /search/resources/api/v2/products?...&physicalStoreId={STORE_ID}&currency=MXN` con ejemplo JSON recortado (`price[]` usage Offer/Display, `x_prices.<id>.mxn`, `partNumber`, `inventories`). Zona = query param `physicalStoreId`/`stLocId`/`marketId` (§1, líneas 38–45); selector vía `POST .../setDefault` `{"defaultStore":"1333"}`. |
| 4 | Lista la(s) tienda(s) de Monterrey (store id) como insumo para `RetailerLocation` | **CUMPLE** | §3 (líneas 152–171): `external_id`/`physicalStoreName` = **`1333`**, `physicalStoreId` interno HCL = **`18503`**, `marketId` = **`10`**. Recomendación explícita: `RetailerLocation` usa `external_id=1333` + id interno y marketId como metadatos. Documenta honestamente la limitación (el HAR no trae el nombre de ciudad; la asociación a Monterrey es insumo humano de Carlos). |

**Extras del entregable (no exigidos, suman valor):** §2.2 paginación (`limit`/`offset`/`total`),
§2.3 endpoint auxiliar de inventario, §2.4 endpoints de soporte, §4 campos de matching de SKU
para varilla (`CALIBRE`/`LARGO`/`MODELO`/`UPC`...), §5 ausencia de anti-bot observada.

---

## 2. Verificación de seguridad / privacidad (CRÍTICA — el .md SÍ se commitea)

### 2.1 Grep de patrones sensibles

Comando:
```
grep -inE "set-cookie|cookie:|authorization|bearer|password|_abck|sessionid|token=" docs/recon/homedepot.md
```
Salida (4 líneas, **todas descriptivas — sin valores reales**):
```
42:  y `Set-Cookie` removidos — no hay nombres de cookie en la evidencia). Para M2 esto
64:  `Authorization` para precio público. (Cookie de sesión removida del HAR; ver §1.)
197:  Akamai bot-manager / DataDome / PerimeterX / reCAPTCHA / `_abck`. Todas las llamadas de
210:- **Nota de privacidad:** el export ya venía **sin** headers `Cookie`/`Set-Cookie`/`Authorization`
```
Veredicto privacidad: **OK**. Las 4 coincidencias son menciones descriptivas del tipo
"la cookie/Authorization fue removida del HAR" y "no se vio `_abck`", expresamente permitidas
por la spec. No hay valores reales de cookie/token/auth.

Comando de refuerzo (busca asignaciones de valor real):
```
grep -inE "(token=|sessionid=|_abck=)[A-Za-z0-9%._-]{6,}|bearer [A-Za-z0-9._-]{10,}|authorization: [A-Za-z0-9._-]{10,}" docs/recon/homedepot.md
```
Salida: **VACÍO** (ningún valor real de token/cookie/auth en el doc).

### 2.2 HAR gitignored y no trackeado

| Comprobación | Comando | Resultado |
|--------------|---------|-----------|
| HAR ignorado por git | `git check-ignore docs/recon/har/www.homedepot.com.mx.har` | Matchea → `docs/recon/har/www.homedepot.com.mx.har` ✔ |
| Reglas de .gitignore | `grep -niE "har\|recon" .gitignore` | Líneas 24–25: `docs/recon/har/` y `*.har` ✔ |
| HAR NO trackeado | `git ls-files docs/recon/har/` | VACÍO ✔ (toda la carpeta `har/` está fuera del índice, incl. `LEEME.txt` y `construrama.har`) |
| HAR existe en disco | `ls -la docs/recon/har/` | `www.homedepot.com.mx.har` ~8.1 MB (coincide con §6 del doc: ~8 MB) ✔ |

---

## 3. Higiene del arnés (CHECKPOINTS.md)

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `git status` muestra solo el deliverable de la capa docs | **CUMPLE** | `git status --porcelain` → única línea: `?? docs/recon/homedepot.md`. Filtrado fuera de `docs/recon\|progress\|feature_list.json` → VACÍO. (feature_list/progress ya estaban commiteados; sin código de capas tocado.) |
| Sin cambios en capas de código | **CUMPLE** | `git status --porcelain backend/ frontend/ e2e/` → VACÍO. |
| `feature_list.json` JSON válido, ≤1 `in_progress` | **CUMPLE** | `init.sh` Fase 1: "feature_list.json es JSON válido (array)" + "features in_progress: 1 (máximo 1)" (es F010). |
| `progress/current.md` refleja la sesión | **CUMPLE** | `progress/current.md` → "Feature en curso: F010" con plan de capa docs coherente. |
| Toda feature `done` tiene review APROBADO | **CUMPLE** | `init.sh` Fase 1: "las 19 feature(s) 'done' tienen review APROBADO". |
| Repo git inicializado | **CUMPLE** | `git rev-parse --is-inside-work-tree` → `true`; `init.sh` Fase 0: "repositorio git inicializado". |

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
  ✔ las 19 feature(s) 'done' tienen review APROBADO

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

Todos los criterios de aceptación de `specs/F010` **CUMPLEN**. El entregable
`docs/recon/homedepot.md` sigue el TEMPLATE, está libre de "TBD" en secciones 0–4,
registra el gate ToS con veredicto explícito (`PENDIENTE — requiere confirmación humana`)
y `scraper_status=paused`, documenta el endpoint XHR de precio con payload de ejemplo
sanitizado y el mecanismo de zona/tienda, y lista la tienda de Monterrey
(`external_id=1333`, interno `18503`, `marketId=10`). La verificación de seguridad es
limpia: ningún valor real de cookie/token/auth en el `.md`, HAR gitignored y no trackeado.
La higiene del arnés está VERDE (`./init.sh --quick`), con solo el deliverable de la capa
docs como cambio y sin código de capas tocado.

**Nota para el líder (no bloqueante):** antes de F012/M2 quedan dos cierres humanos ya
señalados en el propio doc — (a) veredicto legal ToS de Carlos, (b) lectura de `robots.txt`
real. Son precondiciones de M2, no defectos de esta Fase 0.

Veredicto: **APROBADO**.
