# Bitácora (append-only)

> Una línea por feature cerrada: fecha, id, resumen de 1-2 frases, ciclos de review.

- 2026-06-13 · **F002** Bootstrap frontend (Next.js 15.5.19 + Tailwind v4 + shadcn button/card/input + Vitest) · APROBADO 1er ciclo · `./init.sh` verde (30 ok). ESLint de arquitectura muerde (no `fetch` fuera de client.ts, cero `any`). Resuelto pnpm 11 `allowBuilds`. Informe `impl_F002_frontend.md`, review `review_F002.md`.
- 2026-06-13 · **F001** Bootstrap backend (Django 6 + Ninja 1.6 + Celery esqueleto, SQLite/sin-Docker) · APROBADO 1er ciclo · `./init.sh` verde (23 ok). Regla de capas mecánica (ruff TID251 + import-linter). `export_openapi_schema` OK. Informe `impl_F001_backend.md`, review `review_F001.md`.
- 2026-06-13 · Endurecimiento del arnés (no-feature) · Auditoría multidimensional (42 agentes, verificación adversarial): 30 hallazgos confirmados, 0 sobrevivieron como "alta". Aplicado: git init + check de repo, gate done←review, CORS + config de bootstrap en F001/F002, drift de F003 sin git diff, guard hook fail-closed con detección de capa, hooks vía bash, .env.example, y arquitectura limpia en 3 capas (conventions + reviewer/CHECKPOINTS + greps en init.sh). Detalle: `progress/auditoria-arnes-2026-06-13.md`.
