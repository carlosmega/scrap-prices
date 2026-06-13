# CHECKPOINTS.md — Criterios de "estado final correcto"

Una feature está terminada cuando TODO lo aplicable es cierto. El reviewer
verifica cada punto **ejecutando comandos**, no leyendo resúmenes.

## Global

- [ ] `./init.sh` termina verde de punta a punta.
- [ ] Exactamente la feature actual pasó de `in_progress` a revisión; ninguna
      otra cambió de estado.
- [ ] Existen `progress/impl_<id>_<capa>.md` por cada capa tocada, con output
      real de las verificaciones (no parafraseado).
- [ ] La implementación cumple su `specs/<id>-*.md`: cada criterio de
      aceptación, uno por uno.

## Backend (si la feature toca esta capa)

- [ ] `uv run pytest` pasa. La feature trae tests nuevos que fallarían sin
      la implementación.
- [ ] `uv run python manage.py makemigrations --check --dry-run` limpio
      (no hay migraciones pendientes de generar).
- [ ] `uv run ruff check .` limpio.
- [ ] La lógica de negocio vive en `services.py`, no en los routers de Ninja.
- [ ] **Arquitectura:** `api.py` no contiene llamadas al ORM
      (`.objects`/`.save(`/`.filter(`/`.create(`); la regla de capas
      (import-linter o ruff banned-api) pasa. La Fase 3 de `init.sh` lo grepea.
- [ ] `corsheaders` configurado con `CORS_ALLOWED_ORIGINS` desde env.
- [ ] Si cambió el contrato: `backend/openapi.json` regenerado y commiteado.

## Contrato (si cambió la API)

- [ ] `frontend/src/lib/api/schema.d.ts` regenerado con `pnpm gen:api` y sin
      drift contra `backend/openapi.json` (la fase de contrato de `init.sh`
      lo verifica).
- [ ] El frontend NO declara a mano tipos de respuestas de la API: todo sale
      de los tipos generados.

## Frontend (si la feature toca esta capa)

- [ ] `pnpm exec tsc --noEmit` limpio.
- [ ] `pnpm lint` limpio.
- [ ] `pnpm build` pasa.
- [ ] Componentes shadcn instalados vía CLI o MCP en `src/components/ui/`,
      no copiados a mano de internet.
- [ ] Todo fetch maneja estados de carga y error.
- [ ] **Arquitectura:** ningún `fetch(` fuera de `src/lib/api/client.ts`;
      cero `any`; las reglas ESLint de arquitectura pasan. La Fase 4 de
      `init.sh` grepea `fetch(` fuera del cliente.

## E2E (si la feature es un vertical slice)

- [ ] El smoke de `e2e/` pasa con `./init.sh --e2e`.
- [ ] La feature tiene al menos un test E2E propio cubriendo el flujo feliz.

## Higiene del arnés

- [ ] `feature_list.json` sigue siendo JSON válido con ≤ 1 `in_progress`.
- [ ] `progress/current.md` refleja la realidad de la sesión.
- [ ] Toda feature `done` tiene su `progress/review_<id>.md` con
      `Veredicto: APROBADO` en la primera línea (la Fase 1 de `init.sh` lo verifica).
- [ ] El repositorio está inicializado como git (la Fase 0 de `init.sh` lo
      verifica con `git rev-parse`), para que el diff del reviewer sea ejecutable.
