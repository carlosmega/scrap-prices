# impl F023 backend — Puertos fijos locales (CORS default → :3300)

## Spec aplicada y decisiones
Spec: `specs/F023-puertos-fijos.md`, capa backend.
- Cambié SOLO el **default** de `CORS_ALLOWED_ORIGINS` en `config/settings.py` de
  `http://localhost:3000` a `http://localhost:3300`; sigue leyéndose de env.
- NO toqué `CORS_ALLOW_HEADERS` (el `x-session-key` de F022 se conserva).
- Única referencia residual a `:3000` en `backend/` estaba en esas dos líneas
  (default + comentario); ambas actualizadas. No hay más `:3000` en `backend/config` ni `backend/apps`.
- No cambian endpoints/schemas → contrato OpenAPI sin cambios, no se regeneró `openapi.json`.

## Archivos modificados
- `backend/config/settings.py` (default de `CORS_ALLOWED_ORIGINS` y comentario asociado).

## ¿Cambió el contrato OpenAPI?
NO. Sin cambios en rutas, schemas ni params. `openapi.json` intacto.

## Output real de verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest -q`
```
77 passed in 2.28s
```

### Preflight CORS desde el nuevo origen
Server: `uv run python manage.py runserver 127.0.0.1:8800 --noreload` (background, luego matado).
Comando:
`curl -i -X OPTIONS http://127.0.0.1:8800/api/lists -H "Origin: http://localhost:3300" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: x-session-key,content-type"`

```
HTTP/1.1 200 OK
Date: Sun, 14 Jun 2026 16:53:46 GMT
Server: WSGIServer/0.2 CPython/3.12.10
content-length: 0
Content-Type: text/html; charset=utf-8
Vary: origin
access-control-allow-origin: http://localhost:3300
access-control-allow-headers: accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with, x-session-key
access-control-allow-methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
access-control-max-age: 86400
```
Confirmado: `access-control-allow-origin: http://localhost:3300` y `access-control-allow-headers` incluye `x-session-key`.

## Deuda / seguimientos
- Las capas frontend y e2e aún apuntan a `:3000`/`:8000`; el siguiente implementer
  (frontend/e2e) debe completar puertos `3300`/`8800` antes de correr `./init.sh --e2e`.
- No corrí `./init.sh --e2e` por indicación (capa frontend/e2e pendiente).
