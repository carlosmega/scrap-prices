# Auditoría del arnés — 2026-06-13

> Auditoría multidimensional (5 dimensiones, 42 agentes) con verificación
> adversarial de cada hallazgo. Resultado: **30 confirmados, 3 fuera-de-alcance,
> 2 refutados**. Tras la verificación adversarial **ningún hallazgo "alta"
> sobrevivió** — todos bajaron a media/baja.

## Veredicto

- **Como andamio de proceso** (su propósito declarado): completo y coherente.
  El flujo contract-first, SDD, roles, anti-teléfono-descompuesto y la
  verificación ejecutable están bien diseñados.
- **Como base para una app de producción**: ~12 hallazgos de severidad media;
  ninguno showstopper de diseño, pero varios conviene cerrar antes de arrancar.

## Refutados (buenas noticias)

1. **`export_openapi_schema` SÍ es nativo de django-ninja** (`ninja/management/commands/export_openapi_schema.py`), con `--api/--output/--indent`. Requiere solo `'ninja'` en `INSTALLED_APPS`. El comando del arnés es correcto.
2. **`./init.sh --e2e` SÍ levanta docker** (la Fase 2 no se salta en `--e2e`). El gate E2E está bien cableado; Playwright `webServer` ya está en F004.

## Confirmados (severidad ajustada tras verificación)

### Tema A — Git asumido pero no inicializado (media)
El repo no era git. `reviewer` paso 5 (`git diff/status`), `CHECKPOINTS "commiteado"` y `F003 git diff --exit-code` dependen de git. `init.sh` exigía el binario pero nunca el repo. **Mitigado:** el drift real (Fase 5) es git-independiente.

### Tema B — El guard hook es más débil de lo que el arnés proclama (media x4)
1. **Falla abierto sin `jq`** (ausente en este entorno) → invariante apagado en silencio.
2. **Nunca valida QUÉ capa** edita el agente; solo cuenta `in_progress`.
3. El matcher `Edit|Write|MultiEdit` **no cubre escrituras vía Bash** (`echo>`, `sed -i`, `tee`); los agentes tienen Bash.
4. La allowlist (`*/docs/*`, `*/CLAUDE.md`, `*/.claude/*`) **no está anclada** a la raíz → rutas de código se cuelan.

### Tema C — Config de bootstrap no documentada (media, autocorregible)
- `pytest-django` necesita `DJANGO_SETTINGS_MODULE` (F001 no lo dice).
- El management command necesita `'ninja'` en `INSTALLED_APPS` (no documentado).
- `create-next-app .` **aborta** en `frontend/` por `CLAUDE.md` + `.gitkeep` presentes.

### Tema D — CORS ausente (media)
F005 hace mutaciones client-side (`:3000`→`:8000`); sin `django-cors-headers` el navegador las bloquea. F001 no lo incluye. El E2E de F005 lo expondría en rojo.

### Tema E — `done ← review-aprobado` sin enforcement (media)
Nada verifica que una feature `done` tenga su `review_<id>.md` con `APROBADO`.

### Baja (deuda menor, no bloqueante)
Script `test:e2e` no enumerado en F004; `init.sh` duplica la línea de `gen:api`; Celery esqueleto no verificado; falta `.env.example`; sin CI; sin convención de formato de error 4xx/5xx; hooks invocados sin `bash` explícito; parseo frágil de `docker compose ps`; healthcheck estático; sin seeds/fixtures; sin logging configurado; deadlock invertido benigno; ambigüedad de dueño de `pnpm gen:api`.

## Fuera de alcance por diseño (no son huecos)
Autenticación, despliegue/Dockerfiles/settings de producción — declarados explícitamente en F001/F005.

## Acciones tomadas (lote aprobado 2026-06-13)
Ver `progress/current.md`. Resumen: git init + check de repo, CORS y config de bootstrap en F001/F002, gate `done←review`, endurecimiento del guard hook (fail-closed, allowlist anclada, validación de capa), y arquitectura limpia en 3 capas (conventions + reviewer/CHECKPOINTS + checks mecánicos en init.sh).
