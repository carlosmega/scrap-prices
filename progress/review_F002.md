# Veredicto: APROBADO

**Feature:** F002 — Bootstrap frontend (Next.js 15 + Tailwind v4 + shadcn/ui + Vitest)
**Spec:** `specs/F002-bootstrap-frontend.md`
**Capa:** única `frontend` (no toca e2e). Re-ejecuté `./init.sh` en modo full (sin `--e2e`).
**Revisor:** verificación ejecutable propia, no parafraseo del implementer.

---

## Criterios de aceptación de la spec (uno por uno)

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `pnpm exec tsc --noEmit` limpio | CUMPLE | `./init.sh` Fase 4 `✔ tsc --noEmit` (exit 0) |
| 2 | `pnpm lint` limpio | CUMPLE | `./init.sh` Fase 4 `✔ lint` (exit 0); además mi corrida directa salió 0 sin la sonda |
| 3 | `pnpm build` limpio | CUMPLE | `./init.sh` Fase 4 `✔ build de producción`; reporta `▲ Next.js 15.5.19` |
| 4 | `src/components/ui/` contiene componentes shadcn instalados por CLI/MCP | CUMPLE | `ls frontend/src/components/ui/` → `button.tsx`, `card.tsx`, `input.tsx`; existe `frontend/components.json` (`$schema` ui.shadcn.com) que genera el CLI `shadcn init`. No copiados a mano |
| 5 | La home renderiza con Tailwind + componente shadcn visible | CUMPLE | `frontend/src/app/page.tsx` usa `Card`/`Input`/`Button` de `@/components/ui/*` y clases Tailwind con tokens del theme (`bg-background`, `text-foreground`, `text-muted-foreground`). Test de humo confirma render del heading y del botón |
| 6 | Reglas ESLint de arquitectura activas: un `fetch` fuera de `client.ts` o un `any` hacen fallar `pnpm lint` | CUMPLE | Sonda temporal `src/__lint_probe.ts` (con `any` y `fetch`) → `pnpm lint` exit 1 con `@typescript-eslint/no-explicit-any` y `no-restricted-syntax`. `fetch` dentro de `src/lib/api/client.ts` sonda → SIN error (excepción correcta). Sondas borradas tras la prueba |
| 7 | `pnpm test:unit` (vitest run) pasa con ≥1 test de humo; el script existe en package.json | CUMPLE | `frontend/package.json` define `"test:unit": "vitest run"`; `./init.sh` Fase 4 `✔ tests unitarios (vitest)`. `src/app/page.test.tsx` = 2 casos de humo |

## Sección Frontend de CHECKPOINTS.md (punto por punto)

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `pnpm exec tsc --noEmit` limpio | CUMPLE | Fase 4 `✔ tsc --noEmit` |
| `pnpm lint` limpio | CUMPLE | Fase 4 `✔ lint` |
| `pnpm build` pasa | CUMPLE | Fase 4 `✔ build de producción` |
| shadcn instalado vía CLI/MCP en `src/components/ui/`, no a mano | CUMPLE | `components.json` + 3 componentes; ver criterio 4 |
| Todo fetch maneja estados de carga y error | NO VERIFICABLE / N/A | F002 no consume API (sin `fetch` en `src/`); el cliente y los estados son F003. La regla ESLint ya reserva `client.ts` como único punto de salida |
| Arquitectura: ningún `fetch(` fuera de `src/lib/api/client.ts`; cero `any` | CUMPLE | Greps deterministas: `grep -rn "fetch(" frontend/src ... | grep -v client.ts` → VACÍO; `grep -rn ": any\|as any" frontend/src` → VACÍO. `./init.sh` Fase 4 `✔ arquitectura: fetch solo en src/lib/api/client.ts` |

## Sección Global de CHECKPOINTS.md

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | Resumen: `✔ 30 ok ✘ 0 fallos ◌ 5 pendientes` → VERDE, exit 0 |
| Solo la feature actual cambió de estado | CUMPLE | `feature_list.json`: F002 `in_progress`; F001 `done` (previa); resto `pending`. Ninguna otra mutada |
| Existe `progress/impl_<id>_<capa>.md` por capa tocada con output real | CUMPLE | `progress/impl_F002_frontend.md` con outputs de tsc/lint/build/test:unit |
| La implementación cumple su spec, criterio por criterio | CUMPLE | Tabla de criterios arriba: 6/6 CUMPLE, 1 N/A justificado (estados de carga = F003) |

## Sección Contrato (¿cambió la API?)

NO APLICA a F002. `backend/openapi.json` no existe (lo crea F003) y `frontend/src/lib/api/`
está vacía por diseño (solo `.gitkeep`). `./init.sh` Fase 5 reporta PENDIENTE (no rojo),
que es el estado esperado. El consumo real de la API es F003.

## Sección Higiene del arnés

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido con ≤1 `in_progress` | CUMPLE | Fase 1 `✔ feature_list.json es JSON válido (array)` + `✔ features in_progress: 1 (máximo 1)` |
| `progress/current.md` refleja la sesión | CUMPLE | Describe F002, plan de capa única frontend, estado `in_progress` |
| Toda feature `done` tiene review APROBADO | CUMPLE | Fase 1 `✔ las 1 feature(s) 'done' tienen review APROBADO`; `progress/review_F001.md` línea 1 = `# Veredicto: APROBADO` |
| Repo git inicializado | CUMPLE | `git rev-parse --is-inside-work-tree` → `true` (exit 0); Fase 0 `✔ repositorio git inicializado` |

## Diff / alcance de capa (git status + git diff)

Solo se tocó la capa permitida (`frontend/`) más el archivo de arnés del implementer
(`progress/impl_F002_frontend.md`). No hay archivos fuera de capa.

```
 D frontend/.gitkeep
?? frontend/.env.example
?? frontend/.gitignore
?? frontend/README.md
?? frontend/components.json
?? frontend/eslint.config.mjs
?? frontend/next.config.ts
?? frontend/package.json
?? frontend/pnpm-lock.yaml
?? frontend/pnpm-workspace.yaml
?? frontend/postcss.config.mjs
?? frontend/public/
?? frontend/src/
?? frontend/tsconfig.json
?? frontend/vitest.config.ts
?? frontend/vitest.setup.ts
?? progress/impl_F002_frontend.md
```

Nota sobre `D frontend/.gitkeep`: el implementer movió `frontend/.gitkeep` y
`frontend/CLAUDE.md` fuera durante el scaffold de `create-next-app` (dir no vacío,
procedimiento de la spec). Restauró `frontend/CLAUDE.md` (presente, con su contenido
original) pero no el `.gitkeep` raíz — ya innecesario porque `frontend/` dejó de
estar vacío. No es un defecto: el `.gitkeep` solo existía para versionar la carpeta
vacía, propósito que el scaffold deja obsoleto. Sin impacto en init.sh ni en la spec.

## Hechos de entorno confirmados como NO-defectos

- `jq` y `docker` ausentes → PENDIENTE en Fase 0/2 por diseño del MVP (SQLite, sin Docker). `pnpm 11.6.0` presente.
- Fase 5 (contrato) PENDIENTE (no rojo): `backend/openapi.json` y `frontend/src/lib/api/schema.d.ts` son de F003.
- `frontend/src/lib/api/` vacía (solo `.gitkeep`) = estado esperado de F002.
- Next.js pineado a 15.5.19 (la spec exige "Next.js 15"; `@latest` daría Next 16). Decisión correcta del implementer.

## Verificación de que el test "muerde" (regla del git-stash mental)

- ESLint: sonda con `any` + `fetch` → `pnpm lint` exit 1 (2 errores); sin sonda → exit 0. La regla NO es decorativa.
- Excepción de `client.ts`: `fetch` dentro de `src/lib/api/client.ts` → 0 errores. La whitelist funciona y está alineada con el grep de la Fase 4 de init.sh.
- Test de humo: comprueba `getByRole("heading", {name:/construscan/i})` y el botón Buscar; fallaría si la home no renderizara esos elementos (verificado por el implementer rompiendo el heading → 1 failed).

---

## Output REAL de mi corrida de `./init.sh` (modo full)

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
  ✔ las 1 feature(s) 'done' tienen review APROBADO

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
  ◌ pipeline de contrato sin configurar (feature F003 pending)

── Fase 6 · E2E (Playwright) ──
  ◌ saltada (usa ./init.sh --e2e para correrla)

════════ Resumen ════════
  ✔ 30 ok   ✘ 0 fallos   ◌ 5 pendientes
  VERDE — el arnés está en estado consistente.

INIT_EXIT=0
```

## Prueba de las reglas ESLint (sonda temporal, ya borrada)

```
C:\scrap-prices\frontend\src\__lint_probe.ts
  2:19  error  Unexpected any. Specify a different type                                    @typescript-eslint/no-explicit-any
  3:21  error  Prohibido `fetch` directo. Todo HTTP pasa por src/lib/api/client.ts (F003)  no-restricted-syntax

✖ 2 problems (2 errors, 0 warnings)
[ELIFECYCLE] Command failed with exit code 1.
LINT_EXIT_WITH_PROBE=1
```
(`src/lib/api/client.ts` con `fetch` no generó error: la excepción funciona. Ambas sondas eliminadas; `src/lib/api/` vuelve a contener solo `.gitkeep`.)

## Greps deterministas de arquitectura

```
grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"  → (vacío)
grep -rn ": any\b\|as any" frontend/src --include=*.ts --include=*.tsx                        → (vacío)
```
