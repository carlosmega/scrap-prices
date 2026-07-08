# Review F032 — CI: GitHub Actions corriendo `./init.sh --e2e`

Veredicto: APROBADO

Revisor: reviewer del arnés. Metodología: re-ejecuté todas las verificaciones
yo mismo (no acepto output pegado). Todos los comandos y su salida real están
abajo.

## Criterios de aceptación de la spec

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | `ci.yml` YAML válido con triggers `push`(main) + `pull_request` + `workflow_dispatch` | **CUMPLE** | `uv run --with pyyaml --no-project python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → `YAML OK`; `ci.yml` líneas 5-9: `push.branches:[main]`, `pull_request:`, `workflow_dispatch:` |
| 2 | Job instala uv, Node 24, pnpm 11 y Chromium de Playwright, y ejecuta `bash init.sh --e2e` | **CUMPLE** | `ci.yml`: uv installer (L26-30), `pnpm/action-setup@v4` `version: 11` (L33-36), `setup-node@v4` `node-version: 24` (L38-41), `playwright install --with-deps chromium` (L52-56), `run: bash init.sh --e2e` (L61-62) |
| 3 | La corrida en GitHub Actions termina **verde** contra el commit del workflow | **CUMPLE** | `gh run view 28907565411 --json conclusion,headSha,event,headBranch` → `conclusion=success`, `event=push`, `headBranch=main`, `headSha=8e67b103…`. `git show -s --oneline 8e67b10` → `ci(F032): GitHub Actions corriendo ./init.sh --e2e en push/PR` (== HEAD y == commit que introduce `ci.yml`) |
| 4 | Ante fallo se sube `e2e/playwright-report/` como artefacto | **CUMPLE** | `ci.yml` L64-71: step con `if: failure()`, `actions/upload-artifact@v4`, `path: e2e/playwright-report/` |
| 5 | Higiene: `feature_list.json` JSON válido con exactamente 1 `in_progress` (F032); `init.sh --quick` VERDE | **CUMPLE** | `json.load` OK, `in_progress count: 1`, `ids: ['F032']`; `bash init.sh --quick` → `VERDE — 32 ok, 0 fallos` (output completo abajo) |

## CHECKPOINTS.md — puntos aplicables

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | **CUMPLE** | `--quick` VERDE localmente + CI `--e2e` `conclusion=success` (Fases 0-6 en el runner) |
| Exactamente la feature actual en revisión; ninguna otra cambió de estado | **CUMPLE** | `feature_list.json`: solo F032 `in_progress`; `git show --stat 8e67b10` toca únicamente `feature_list.json`, `progress/current.md`, `specs/F032-…md`, `.github/workflows/ci.yml` |
| Implementación cumple cada criterio de la spec | **CUMPLE** | tabla anterior |
| Higiene: `feature_list.json` JSON válido con ≤1 `in_progress` | **CUMPLE** | Fase 1: `features in_progress: 1 (máximo 1)`, `feature_list.json es JSON válido (array)` |
| `progress/current.md` refleja la sesión | **CUMPLE** | describe F032, plan y gate de "done" (corrida verde en Actions) |
| Toda feature `done` tiene `review_<id>.md` APROBADO | **CUMPLE** | Fase 1: `las 28 feature(s) 'done' tienen review APROBADO` |
| Repo inicializado como git (Fase 0) | **CUMPLE** | Fase 0: `repositorio git inicializado`; `git status` responde (working tree clean) |
| Arquitectura backend: `api.py` sin ORM | **CUMPLE (no aplica a F032)** | Fase 3: `arquitectura: routers (api.py) sin llamadas al ORM`. Ver nota sobre falso positivo del grep manual abajo |
| Arquitectura frontend: `fetch` solo en `client.ts`; cero `any` | **CUMPLE (no aplica a F032)** | Fase 4: `arquitectura: fetch solo en src/lib/api/client.ts`; grep manual `fetch(` fuera del cliente → VACÍO; grep `: any\|as any` → VACÍO |

## Diff / capa tocada

`git show --stat 8e67b10` — la feature toca solo capa CI/arnés (permitida):

```
 .github/workflows/ci.yml        | 71 ++++++++++
 feature_list.json               |  7 ++++
 progress/current.md             | 78 +++++------
 specs/F032-ci-github-actions.md | 80 ++++++++++++
 4 files changed, 191 insertions(+), 45 deletions(-)
```

No se tocó `backend/`, `frontend/` ni `e2e/`. `git status` → working tree clean,
`up to date with origin/main`.

## Greps deterministas de arquitectura (protocolo del revisor)

```
$ grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py
backend/apps/lists/api.py:92:@router.delete("/lists/{list_id}", response={204: None})
backend/apps/lists/api.py:149:@router.delete("/lists/{list_id}/items/{item_id}", response={204: None})
```

**Falso positivo, no violación:** ambos hits son el **decorador de ruta de Ninja**
`@router.delete(...)` (verbo HTTP), no una llamada al ORM `.delete()`. Es código
preexistente, no tocado por F032. La Fase 3 de `init.sh` (grep más preciso) lo
confirma: `arquitectura: routers (api.py) sin llamadas al ORM` en VERDE.

```
$ grep -rn "fetch(" frontend/src --include="*.ts" --include="*.tsx" | grep -v "lib/api/client.ts"
(vacío — exit 1)
$ grep -rn ": any\b\|as any" frontend/src
(vacío — exit 1)
```

## Confirmación de la corrida en GitHub Actions

```
$ gh run view 28907565411 --json status,conclusion,headSha,headBranch,workflowName,event
{"conclusion":"success","event":"push","headBranch":"main","headSha":"8e67b103d884d5276ab5a879d43ff67b0cbedbb8","status":"completed","workflowName":"CI"}

$ gh run view 28907565411
✓ main CI · 28907565411
Triggered via push about 3 minutes ago
JOBS
✓ init.sh --e2e (arnés completo) in 2m4s (ID 85757805971)
ANNOTATIONS
! Node.js 20 is deprecated. The following actions target Node.js 20 but are
  being forced to run on Node.js 24: actions/checkout@v4, actions/setup-node@v4,
  pnpm/action-setup@v4. (advertencia informativa, no falla el job)
```

`headSha 8e67b103…` == commit `8e67b10` (`ci(F032): …`) == HEAD == el commit que
introduce el workflow. Job único `verify` verde en 2m4s.

## Output real de `bash init.sh --quick`

```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ✔ jq disponible
  ✔ uv disponible
  ✔ docker disponible
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
  ✔ las 28 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en el MVP (backend corre con SQLite); infra Postgres/Redis diferida a una migración futura

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
  ✔ 32 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

(Los 3 `◌` son esperados en `--quick`: infra Docker diferida al MVP SQLite,
`build` y `E2E` se corren en `--e2e` — y esa capa E2E fue ejercitada en verde
por la corrida de CI `28907565411`.)

## Observaciones no bloqueantes

1. **Sin `progress/impl_F032_ci.md`.** La capa de F032 es `ci` (`.github/`), que
   no es `backend/`/`frontend/`/`e2e/`; el líder puede autorar el workflow
   directamente, por lo que no hubo handoff de un implementer. No es un criterio
   de aceptación de la spec y toda la verificación real quedó capturada aquí y en
   la corrida de CI. No bloquea.
2. **Advertencia de deprecación de Node 20** en las actions de terceros
   (`checkout@v4`, `setup-node@v4`, `pnpm/action-setup@v4`). Es una *annotation*
   informativa de GitHub, no falla el job (`conclusion=success`). Follow-up
   opcional a futuro; fuera del alcance de F032.

## Conclusión

Los 5 criterios de aceptación CUMPLEN con evidencia ejecutable, la corrida de CI
`28907565411` está `conclusion=success` contra el commit del workflow (`8e67b10`),
`init.sh --quick` local está VERDE y la higiene del arnés se mantiene (1
`in_progress` = F032, JSON válido). **APROBADO.**
