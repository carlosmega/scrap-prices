# F032 — CI: GitHub Actions corriendo `./init.sh --e2e`

> SDD: la spec es el contrato. Si no está aquí, no existe. Si es ambiguo,
> se pregunta al humano ANTES de implementar, no después.

## Contexto y objetivo

El valor del repo es que sea **verificable y auditable**, pero hoy la única
prueba de que el arnés está verde vive en la laptop de un humano. En esta misma
sesión un checkout nuevo se rompió de tres formas invisibles en local (faltaba
el bit `+x` de `init.sh`/hooks, faltaba el navegador de Playwright, y Docker daba
falso-rojo). CI convierte *"verde en mi máquina"* en *"verde en cada push"*: una
red de regresión automática para las 28+ features `done`.

## Alcance

**Incluye:**
- Un workflow `.github/workflows/ci.yml` que corre en `push` a `main`, en
  `pull_request` y bajo `workflow_dispatch`.
- Un job `verify` (ubuntu-latest) que instala el toolchain (uv, Node 24, pnpm 11,
  navegador Chromium de Playwright) y ejecuta **`bash init.sh --e2e`** — el gate
  canónico completo (backend, frontend, contrato, arquitectura, E2E).
- Subida del `playwright-report` como artefacto cuando el job falla, para
  diagnóstico.

**No incluye (explícitamente fuera):**
- Deploy / release / publicación de imágenes.
- Matriz multi-OS o multi-versión (un solo runner ubuntu + Node 24, que replica
  el entorno local).
- Postgres/Redis vía Docker: el MVP corre en SQLite; Fase 2 de `init.sh` ya es
  `pendiente` (F: fix de esta misma sesión) y no se ejercita en CI.
- Caché agresiva de dependencias (se puede afinar después; la corrección va
  primero).

## Contrato API (si aplica)

No aplica: es infraestructura del arnés, sin capa de código de app ni endpoints.

## Criterios de aceptación

- [ ] **CI:** existe `.github/workflows/ci.yml` válido (YAML parseable) con
      triggers `push`(main) + `pull_request` + `workflow_dispatch`.
- [ ] **CI:** el job instala uv, Node 24, pnpm 11 y el Chromium de Playwright, y
      ejecuta `bash init.sh --e2e`.
- [ ] **CI:** la corrida en GitHub Actions termina **verde** contra el commit que
      introduce el workflow (esta es la prueba real; requiere `git push`).
- [ ] **CI:** ante fallo, se sube `e2e/playwright-report/` como artefacto.
- [ ] **Higiene:** `init.sh --quick` local sigue verde con `F032 in_progress`
      (exactamente 1 `in_progress`, JSON válido).

## Plan de verificación

Local (antes del push):
```bash
# YAML válido
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
# el arnés sigue consistente con la feature abierta
bash init.sh --quick    # VERDE, F032 in_progress
```

Remoto (la prueba que cierra la feature):
```bash
git push origin main
# observar la corrida:  Actions -> CI -> job "verify" en verde
# (o vía el MCP de GitHub: listar runs del workflow y confirmar conclusion=success)
```

La feature NO se marca `done` hasta ver la corrida **verde** en GitHub Actions.

## Notas y decisiones abiertas

- **Gate = `--e2e` completo.** Se elige el gate máximo (incluye Playwright) para
  blindar los vertical slices. Si el E2E resulta flaky en CI, el follow-up es
  separarlo en un job aparte (no bloquea esta feature).
- **uv vía instalador oficial** (`astral.sh/uv/install.sh`) + PATH explícito, para
  no depender de la versión de una action de terceros.
- **Node 24 / pnpm 11** para replicar el entorno local (24.18.0 / 11.9.0) y así
  reproducir exactamente el verde local — que es el propósito del CI.
- Backend corre en SQLite con defaults (no requiere `.env`); se copia
  `.env.example`→`.env` de forma defensiva por si CI toma otra rama de settings.
