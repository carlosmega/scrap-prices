# Convenciones de backend (Django + Ninja + Celery)

## Gestión y herramientas
- `uv` para todo: `uv sync`, `uv run <cmd>`. No existe requirements.txt.
- `ruff` es lint Y formato (lo aplica el hook PostToolUse automáticamente).
- Tests con `pytest` + `pytest-django`. Un test mínimo por endpoint y por
  regla de negocio. Los tests viven junto a su app: `apps/<dominio>/tests/`.

## Estructura por dominio
```
backend/apps/<dominio>/
├── models.py
├── schemas.py      # schemas Ninja (entrada/salida) — el contrato en código
├── api.py          # Router de Ninja: SOLO parseo, validación y delegación
├── services.py     # TODA la lógica de negocio vive aquí
├── tasks.py        # tareas Celery del dominio
└── tests/
```

## Reglas duras
1. Los routers no contienen lógica de negocio: reciben, delegan a
   `services.py`, responden. Si un endpoint tiene más de ~15 líneas,
   probablemente está mal.
2. Todo endpoint declara `response=` con un schema explícito. Nada de
   devolver dicts sueltos: el contrato OpenAPI sale de los schemas.
3. Migraciones SIEMPRE commiteadas en el mismo cambio que el modelo.
   `makemigrations --check` en init.sh lo vigila.
4. Settings leen de variables de entorno con defaults locales que apuntan
   al docker-compose del repo (`DATABASE_URL`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS`).
5. Si cambias schemas o rutas: regenera `backend/openapi.json` antes de
   reportar (ver `docs/architecture.md`, flujo contract-first).

## Arquitectura limpia (regla de capas)
El flujo de una request es **una sola dirección**:

```
api.py (router)  →  services.py (lógica)  →  models.py (ORM)
   parseo/validación    reglas de negocio       persistencia
   y delegación         y transacciones
```

- **`api.py` NUNCA toca el ORM.** Prohibido `Model.objects`, `.save(`,
  `.filter(`, `.create(`, `.delete(` dentro de un router. Si lo necesitas,
  es señal de que esa lógica va en `services.py`.
- **`services.py` no conoce HTTP.** No recibe `request`, no devuelve
  `HttpResponse`; recibe/devuelve tipos del dominio o schemas. Esto lo hace
  testeable sin cliente HTTP.
- **`schemas.py` es la frontera de datos.** Todo lo que entra/sale de la API
  se valida con un schema; el router no inventa shapes.
- Esta regla se hace cumplir **mecánicamente**, no por buena voluntad:
  `import-linter` (contrato de capas en `pyproject.toml`) o `ruff` con
  `flake8-tidy-imports`. Además la Fase 3 de `init.sh` corre un grep heurístico
  que falla si aparece una llamada al ORM en `api.py`.

Ejemplo correcto (router delgado):
```python
# apps/tareas/api.py
@router.post("/tareas", response=TareaOut)
def crear_tarea(request, data: TareaIn):
    return services.crear_tarea(titulo=data.titulo)   # delega; sin ORM aquí
```

## Nombres
Apps en español del dominio (`tareas`, `pagos`), código y schemas en el
idioma del dominio, comentarios en español.
