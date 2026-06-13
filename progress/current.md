# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna (endurecimiento del arnés, no una feature de `feature_list.json`)
**Plan:** Auditoría 2026-06-13 → `progress/auditoria-arnes-2026-06-13.md`. Lote aprobado: arquitectura limpia (3 capas) + fixes de corrección urgentes. **COMPLETADO.**

## Resultado de esta tanda

Fixes de corrección urgentes:
- [x] `git init` + identidad + commit base.
- [x] `init.sh` Fase 0: verifica repo git real (`git rev-parse`). ✔ verde.
- [x] `init.sh` Fase 1: gate `done ← review-aprobado` (jq-gated).
- [x] F001: `django-cors-headers`+`CORS_ALLOWED_ORIGINS`, `'ninja'` en INSTALLED_APPS, `[tool.pytest.ini_options]` con `DJANGO_SETTINGS_MODULE`.
- [x] F002: procedimiento real de `create-next-app` en dir no vacío.
- [x] F003: criterio de drift apoyado en Fase 5 de init.sh, no en `git diff --exit-code`.
- [x] `.env.example` con DATABASE_URL, REDIS_URL, CORS_ALLOWED_ORIGINS, NEXT_PUBLIC_API_URL.
- [x] `guard-feature.sh`: fail-closed sin jq, detección de capa por segmento (insensible a forma de ruta, cierra hueco `backend/docs/x.py`), validación de capa vs feature in_progress (jq-gated).
- [x] `settings.json`: hooks invocados vía `bash` explícito + permisos git init/add/commit.
- [x] README: prerrequisitos (git init, jq/docker/uv/node/pnpm en Windows).

Arquitectura limpia (3 capas):
- [x] Conocimiento: sección de reglas de capas + ejemplo en `docs/conventions-backend.md` y `conventions-frontend.md`.
- [x] Gate: checkpoints de arquitectura en `CHECKPOINTS.md` + paso 6 del `reviewer` con greps; F001/F002 exigen lint de capas (import-linter/ruff, ESLint).
- [x] Mecánico: greps en `init.sh` Fase 3 (ORM en `api.py`) y Fase 4 (`fetch` fuera de `client.ts`).

## Estado de verificación
`./init.sh --quick` → 14 ok, 2 fallos, 7 pendientes. Los 2 fallos son **`jq` ausente**
en este entorno (check obligatorio + validación JSON que usa jq). `feature_list.json`
verificado válido con node. Instalar `jq` deja Fase 0–1 en verde.

**Estado:** completado. Listo para `claude` → «implementa la siguiente feature pendiente» (F001).
