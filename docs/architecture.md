# Arquitectura

## Vista general

```
┌─────────────────────────── monorepo (el arnés) ───────────────────────────┐
│                                                                            │
│   specs/  feature_list.json  CHECKPOINTS.md  progress/   ← capa de control │
│                                                                            │
│  ┌────────────────┐   openapi.json    ┌──────────────────┐                 │
│  │   backend/     │ ───────────────►  │    frontend/     │                 │
│  │ Django + Ninja │   (contrato,      │ Next 15 + shadcn │                 │
│  │ Celery worker  │    commiteado)    │ tipos generados  │                 │
│  └───────┬────────┘                   └────────┬─────────┘                 │
│          │ SQL / cache                         │ HTTP /api/*               │
│   ┌──────┴───────┐                             │                           │
│   │ Postgres 16  │◄──── docker compose ────────┘                           │
│   │ Redis 7      │                                                         │
│   └──────────────┘            e2e/ (Playwright) cruza ambos                │
└────────────────────────────────────────────────────────────────────────────┘
```

## Por qué monorepo

Las tres razones, en orden de importancia para el arnés:

1. **El repositorio ES el sistema.** Un solo `feature_list.json`, un solo
   `progress/`, una sola verificación. Casi toda feature es un vertical
   slice (endpoint + UI): el líder no puede orquestar un slice repartido en
   dos checkouts.
2. **La verificación es atómica.** `./init.sh` demuestra el sistema completo
   en una corrida: invariantes, backend, frontend, contrato y E2E.
3. **El contrato no puede romperse en silencio.** Cambiar un schema, regenerar
   `openapi.json`, regenerar `schema.d.ts` y adaptar la UI es UN commit que
   el reviewer audita junto.

## Flujo contract-first

1. La spec (`specs/<id>-*.md`) define el contrato en su tabla de API.
2. `implementer-backend` lo implementa y regenera `backend/openapi.json`
   (comando: `manage.py export_openapi_schema --api config.api.api`).
3. `pnpm gen:api` en frontend regenera `src/lib/api/schema.d.ts` con
   `openapi-typescript`.
4. `implementer-frontend` consume SOLO tipos generados vía
   `src/lib/api/client.ts`.
5. La Fase 5 de `init.sh` regenera los tipos a un tmp y hace `diff`: si hay
   drift, rojo. El contrato queda mecánicamente garantizado.

## Límites de escritura por rol

| Rol                  | Escribe en                                  |
| -------------------- | ------------------------------------------- |
| Líder (hilo principal)| `feature_list.json`, `progress/`, `specs/` |
| implementer-backend  | `backend/`                                  |
| implementer-frontend | `frontend/`, `e2e/`                         |
| reviewer             | `progress/review_*.md`                      |

El hook `guard-feature.sh` añade la garantía mecánica de que nadie toca
código sin una feature `in_progress`.

## Cuándo reconsiderar el monorepo

Si este proyecto evoluciona a un backend que sirve a múltiples clientes
(web + mobile) con equipos y cadencias de release independientes, el split
tiene sentido — y en ese momento `backend/openapi.json` se convierte en un
paquete versionado del contrato. Hasta entonces, el monorepo es lo que hace
posible el arnés.
