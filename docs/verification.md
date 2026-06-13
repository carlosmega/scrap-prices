# Verificación: cómo se demuestra que algo funciona

La palabra del agente no es evidencia. Evidencia = output de un comando,
copiado tal cual en el informe de progress/.

## Niveles
| Nivel  | Comando            | Cuándo                                        |
| ------ | ------------------ | --------------------------------------------- |
| Rápido | `./init.sh --quick`| Durante el desarrollo, iteración corta         |
| Full   | `./init.sh`        | Antes de reportar done; lo corre el reviewer   |
| E2E    | `./init.sh --e2e`  | Features con capa e2e; antes de cerrar slice   |

## Por capa
| Capa     | Prueba                          | Comando                                          |
| -------- | ------------------------------- | ------------------------------------------------ |
| Arnés    | Invariantes (1 feature, JSON ok)| Fase 1 de init.sh                                 |
| Backend  | Unit + endpoint                 | `cd backend && uv run pytest -q`                  |
| Backend  | Estilo y migraciones            | `uv run ruff check .` / `makemigrations --check`  |
| Contrato | Sin drift de tipos              | Fase 5 de init.sh (diff de regeneración)          |
| Frontend | Tipos / lint / build            | `pnpm exec tsc --noEmit && pnpm lint && pnpm build` |
| E2E      | Flujo real usuario              | `cd e2e && pnpm test:e2e`                         |

## Reglas
1. Un test nuevo debe FALLAR sin la implementación. Si nace verde, no
   prueba nada (el reviewer puede pedir el `git stash` mental: ¿qué rompería
   este test?).
2. El output se pega completo en `progress/impl_<id>_<capa>.md`. Output
   parafraseado = no verificado.
3. Rojo en init.sh = nada está terminado, sin excepciones ni "es un flaky".
   Si de verdad es flaky, arreglar el test ES la tarea.
