# MCP en el arnés

## Dónde viven

Los MCP del proyecto se declaran en **`.mcp.json` en la raíz del repo**
(scope *project* de Claude Code). Ese archivo **se versiona en git**: es
coherente con el pilar "el repositorio ES el sistema" — quien clona el repo
hereda exactamente las mismas capacidades de agente que tú.

Claude Code tiene tres scopes y solo uno pertenece al arnés:

| Scope   | Archivo                       | ¿Va al repo? | Uso                                  |
| ------- | ----------------------------- | ------------ | ------------------------------------ |
| project | `.mcp.json` (raíz)            | **Sí**       | Capacidades del arnés, compartidas   |
| local   | `~/.claude.json` (por proyecto)| No          | Experimentos personales              |
| user    | `~/.claude.json` (global)     | No           | Utilidades tuyas en todos los repos  |

La primera vez, Claude Code pide aprobar los servers de proyecto; este arnés
los pre-aprueba para todo el equipo con `"enableAllProjectMcpServers": true`
en `.claude/settings.json`.

Para añadir uno: `claude mcp add --scope project <nombre> -- <comando>` o
editar `.mcp.json` directamente.

## Qué servers hay y quién los usa

| Server     | Para qué                                                | Quién lo usa            |
| ---------- | ------------------------------------------------------- | ----------------------- |
| shadcn     | Buscar e instalar componentes del registry sin copy-paste| implementer-frontend    |
| playwright | Verificación visual interactiva durante el desarrollo    | implementer-frontend    |
| context7   | Documentación fresca (Next 15, Tailwind 4, Ninja)        | implementers            |

El **reviewer no tiene MCP a propósito**: su verificación debe ser
determinista (comandos, exit codes), no impresiones de un browser.

## Cómo se asigna el acceso por subagente

El campo `tools` del frontmatter de cada agente controla el acceso:

- **Si se omite `tools`** → el subagente hereda TODAS las herramientas del
  hilo principal, **incluidos los MCP**. Así está configurado
  `implementer-frontend` (a propósito, con un comentario en el archivo).
- **Si se lista `tools` explícitamente** → solo esas. Así están
  `implementer-backend` (no necesita MCP) y `reviewer` (no debe tenerlos).

## Criterio del arnés: script > MCP

Regla de decisión antes de añadir un server:

1. ¿Un script o comando determinista puede hacerlo? → **script** (va a
   `init.sh` o a un script de package.json, corre igual en CI).
2. ¿Requiere capacidad interactiva imposible de scriptear (navegar un
   browser, consultar un registry vivo, docs actualizadas)? → MCP.

Dos razones: la verificación del arnés debe ser reproducible sin agente, y
**cada server suma definiciones de tools al contexto** de cada sesión — el
contexto es el recurso escaso del arnés, así que se añade con avaricia.

Por eso el E2E formal es `pnpm test:e2e` (script, Fase 6 de init.sh) y el
MCP de playwright es solo una lupa de desarrollo.
