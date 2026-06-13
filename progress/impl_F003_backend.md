# Informe implementer-backend — F003 (paso 1: contrato)

## Spec aplicada y decisiones
Spec: `specs/F003-contrato-tipos.md`, paso 1 (Backend). Tarea mínima: generar y
dejar commiteable `backend/openapi.json` desde la API existente (`/api/health`,
schema `HealthOut` de F001). NO se añadieron endpoints ni se tocaron schemas/rutas.
El export incluye el prefijo `/api` en las rutas (la instancia se monta bajo
`/api/` en `config/urls.py`), por lo que el contrato refleja la ruta real
`/api/health`. El contrato pasa de inexistente a existente.

## Archivos creados/modificados
- `backend/openapi.json` (CREADO)

## ¿Cambió el contrato OpenAPI?
**SÍ.** De inexistente a existente. El líder debe disparar la capa frontend
(paso 2 de la spec: `pnpm gen:api`) para regenerar `frontend/src/lib/api/schema.d.ts`
antes del implementer-frontend. La Fase 5 de `init.sh` estará ROJA a propósito
hasta que ese paso corra; por eso NO se ejecutó `./init.sh` completo aquí.

## Verificaciones (output real)

### `uv run ruff check .`
```
All checks passed!
```

### `uv run pytest -q`
```
..                                                                       [100%]
```

### Export del contrato
```
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
EXIT: 0
```

### Validación de `backend/openapi.json` (JSON válido + contenido)
```
JSON VALIDO
paths: ['/api/health']
schemas: ['HealthOut']
```

### Primeras líneas de `backend/openapi.json`
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "ConstruScan API",
    "version": "0.1.0",
    "description": "API de ConstruScan (Django Ninja)."
  },
  "paths": {
    "/api/health": {
      "get": {
        "operationId": "apps_core_api_health",
        "summary": "Health",
        "parameters": [],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HealthOut"
                }
              }
            }
          }
        },
        "description": "Estado del servicio. Estático, no toca la DB.",
        "tags": [
          "core"
        ]
      }
    }
  },
  "components": {
    "schemas": {
      "HealthOut": {
        "description": "Respuesta del endpoint de salud.",
        "properties": {
          "status": {
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "status"
        ],
        "title": "HealthOut",
        "type": "object"
      }
    }
  },
  "servers": []
}
```

## Nota sobre `makemigrations --check`
No se ejecutó porque esta tarea no toca modelos ni migraciones (solo genera el
contrato a partir de schemas existentes). Sin cambios de modelo, el check no es
parte del alcance del paso 1. ruff y pytest cubren la verificación relevante.

## Deuda / seguimientos detectados
- Ninguna en backend. El cierre del contrato (sin drift) depende del paso 2
  frontend (`pnpm gen:api`) y de la Fase 5 de `init.sh`, fuera de esta capa.
