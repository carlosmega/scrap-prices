# Sesión activa — F032 CI (GitHub Actions)

> El líder mantiene este archivo. Punto de retomada de la sesión.

**Feature en curso:** `F032` (in_progress) — CI con GitHub Actions que corre
`./init.sh --e2e` en cada push a `main` y en cada PR.

## Por qué
En esta sesión un checkout nuevo se rompió en 3 formas invisibles en local
(faltaba `+x` en `init.sh`/hooks, faltaba el navegador de Playwright, y Docker
daba falso-rojo). CI es la red que convierte "verde en mi máquina" en "verde en
cada push" y blinda las 28+ features `done`. Es la tesis del repo (verificable
y auditable) hecha automática.

## Plan
1. [hecho] `specs/F032-ci-github-actions.md` (contrato de la feature).
2. [hecho] `.github/workflows/ci.yml`: job `verify` (ubuntu) → instala uv +
   Node 24 + pnpm 11 + Chromium de Playwright → `bash init.sh --e2e`; sube
   `playwright-report` como artefacto si falla.
3. [hecho] `F032` abierta `in_progress` en `feature_list.json`.
4. [pendiente] Validación local: YAML parseable + `init.sh --quick` verde.
5. [pendiente] **`git push origin main`** — dispara la corrida (el push directo
   del agente se bloqueó antes; lo autoriza el humano).
6. [pendiente] Observar la corrida en Actions (o vía MCP de GitHub) → verde.
7. [pendiente] Al ver verde: `review_F032.md` APROBADO → marcar `done` →
   línea en `progress/history.md`.

## Estado del repo (arrastre de esta sesión)
- 2 commits locales adelante de `origin/main`, listos para push:
  - `d951a03` fix(harness): restaura bit +x en init.sh y hooks.
  - `435d25c` fix(harness): Fase 2 no exige Docker (MVP en SQLite).
- Deuda conocida: committer de esos commits es `M081899@…local`, no el correo
  de GitHub (no se enlazan a la cuenta `carlosmega`). Fácil de reautorar antes
  del push si se decide.

## Gate de "done" para F032
La feature NO es `done` hasta ver la corrida **verde** en GitHub Actions contra
el commit del workflow. Los criterios locales (YAML válido, init.sh verde) son
necesarios pero no suficientes.
