# AGENTS.md — Mapa del arnés (divulgación progresiva)

No leas todo de golpe. Busca lo que necesitas cuando lo necesitas:

| Necesitas...                          | Ve a                                              |
| ------------------------------------- | ------------------------------------------------- |
| Saber qué hacer ahora                  | `feature_list.json` (primera `pending`)            |
| El contrato de la feature              | `specs/<id>-*.md`                                  |
| Criterios de "terminado"               | `CHECKPOINTS.md`                                   |
| Cómo se hablan backend y frontend      | `docs/architecture.md`                             |
| Convenciones Django/Ninja              | `docs/conventions-backend.md` + `backend/CLAUDE.md`|
| Convenciones Next/Tailwind/shadcn      | `docs/conventions-frontend.md` + `frontend/CLAUDE.md` |
| Cómo demostrar que algo funciona       | `docs/verification.md`                             |
| Qué MCP hay y quién puede usarlos      | `docs/mcp.md`                                      |
| Estado de la sesión actual             | `progress/current.md`                              |
| Qué pasó en sesiones anteriores        | `progress/history.md`                              |

## Comandos canónicos

| Acción                                  | Comando                          |
| ---------------------------------------- | -------------------------------- |
| Verificar todo el sistema                 | `./init.sh`                      |
| Verificación rápida (sin build ni infra)  | `./init.sh --quick`              |
| Verificación completa + E2E               | `./init.sh --e2e`                |
| Levantar infraestructura (Postgres/Redis) | `docker compose up -d`           |
| Tests del backend                         | `cd backend && uv run pytest`    |
| Regenerar tipos desde el contrato         | `cd frontend && pnpm gen:api`    |

Si un comando canónico no existe todavía, es porque su feature de bootstrap
(F001–F004) sigue `pending`. `./init.sh` reporta esas capas como PENDIENTE
sin fallar.

## Roles

| Rol                   | Quién                                  | Puede editar              |
| --------------------- | -------------------------------------- | ------------------------- |
| Líder                 | Hilo principal (ver `CLAUDE.md` raíz)  | `feature_list.json`, `progress/`, `specs/` |
| implementer-backend   | `.claude/agents/implementer-backend.md`| `backend/`                |
| implementer-frontend  | `.claude/agents/implementer-frontend.md`| `frontend/`, `e2e/`      |
| reviewer              | `.claude/agents/reviewer.md`           | `progress/review_*.md`    |

## Estados de feature

`pending` → `in_progress` (solo una a la vez) → `done`.
El líder administra los estados; los implementers nunca marcan `done`.
