# F003 — Pipeline de contrato: OpenAPI de Ninja → tipos TypeScript

## Contexto y objetivo
Convertir el contrato en algo mecánicamente verificable: el schema OpenAPI
que genera Django Ninja es la única fuente de verdad de los tipos de API
del frontend. La Fase 5 de `./init.sh` detecta drift.

## Alcance
**Incluye:** export del schema commiteado, generación de tipos, cliente
fetch tipado, script `gen:api`.
**No incluye:** endpoints nuevos.

## Pasos esperados
1. Backend: commitear `backend/openapi.json` generado con
   `uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json`.
2. Frontend: dev-dependency `openapi-typescript`; script
   `"gen:api": "openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts"`.
3. Frontend: `src/lib/api/client.ts` — wrapper fetch tipado con
   `NEXT_PUBLIC_API_URL`, manejo de errores y tipos de `schema.d.ts`.
4. Frontend: la home consume GET /api/health con el cliente y muestra el estado.

## Criterios de aceptación
- [ ] Contrato: `pnpm gen:api` regenera `schema.d.ts` idéntico al commiteado (sin drift).
- [ ] Frontend: cero tipos de respuesta API declarados a mano (grep lo demuestra).
- [ ] Frontend: la home muestra "ok" cuando el backend está arriba y un estado de error amable cuando no.

## Plan de verificación
```bash
cd frontend && pnpm gen:api
# El control de drift NO depende de git: la Fase 5 de init.sh regenera los tipos
# a un tmp y los compara con el archivo en disco (diff -q). Esto evita el falso
# verde de 'git diff --exit-code' sobre un archivo aún no trackeado.
./init.sh   # Fase 5 debe pasar de PENDIENTE a verde (rojo si hay drift)
```

> `src/lib/api/schema.d.ts` debe quedar commiteado, pero la prueba de drift es
> la Fase 5 de `init.sh`, no `git diff`.
