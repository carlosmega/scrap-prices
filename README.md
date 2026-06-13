# harness-fullstack — Arnés Django Ninja + Next.js

Arnés de ingeniería para desarrollo multi-agente con Claude Code, basado en
los patrones de `betta-tech/ejemplo-harness-subagentes` y extendido a un
stack fullstack con un cuarto pilar: **Spec-Driven Development**.

> El valor no está en el código de la app: está en cómo el repo obliga a los
> agentes a trabajar de forma autónoma, verificable y auditable.

## Los cuatro pilares y dónde viven

| Pilar | Manifestación |
| --- | --- |
| 1. El repositorio ES el sistema | `AGENTS.md`, `init.sh`, `feature_list.json`, `progress/`, `docs/`, `.mcp.json` |
| 2. Orquestación multi-agente | `CLAUDE.md` (líder = hilo principal), `.claude/agents/` (2 implementers + reviewer) |
| 3. Supervisión y mejora | `CHECKPOINTS.md`, hooks en `.claude/settings.json` + `.claude/hooks/`, fases de `init.sh` |
| 4. Spec-Driven Development | `specs/` (TEMPLATE + una spec por feature; la spec es el contrato) |

## Para empezar

Prerrequisitos (el arnés los exige; `./init.sh` Fase 0 los verifica):
- **Herramientas:** `git`, `jq` (obligatorias) y, al bootstrapear cada capa,
  `docker`, `uv`, `node`, `pnpm`. En Windows instálalas con winget/scoop/choco
  (`jq`), Docker Desktop, y `corepack enable` para `pnpm`.
- **Repositorio git:** el arnés asume un repo vivo (el reviewer hace `git diff`
  y el contrato se "commitea"). Si clonaste, ya lo tienes; si partiste de un
  zip, inicialízalo:

```bash
git init && git add -A && git commit -m "chore: bootstrap del arnés"   # solo la primera vez
chmod +x init.sh .claude/hooks/*.sh                                    # solo la primera vez
./init.sh
```

Verás las Fases 3–6 en PENDIENTE: es correcto. El propio bootstrap del stack
son las features F001–F004 — **el arnés se construye a sí mismo**.

## Probarlo con Claude Code

1. `./init.sh` — Fases 0–2 verdes, resto pendiente.
2. Abre Claude Code en la raíz: `claude`. Aprueba los MCP del proyecto si
   te lo pide (o ya están pre-aprobados vía settings).
3. Pídele literalmente: **«implementa la siguiente feature pendiente»**.
4. Observa `progress/` mientras trabaja: ahí queda la traza de cada subagente.

| Archivo | Quién lo escribe | Qué contiene |
| --- | --- | --- |
| `progress/current.md` | líder | Plan vivo de la sesión |
| `progress/impl_<id>_<capa>.md` | implementers | Archivos tocados + output real de verificación |
| `progress/review_<id>.md` | reviewer | Veredicto criterio por criterio |
| `feature_list.json` | líder | `pending` → `in_progress` → `done` |
| `progress/history.md` | líder | Bitácora append-only |

Por chat no circula código: solo referencias `done -> progress/...`
(regla anti-teléfono-descompuesto).

## MCP

Los servers del proyecto (shadcn, playwright, context7) viven versionados en
`.mcp.json`. Quién puede usar cada uno y por qué: `docs/mcp.md`.

## Nota para Windows

`init.sh` y los hooks son bash: ejecútalos desde **Git Bash o WSL**. Docker
Desktop debe estar corriendo para la Fase 2.
