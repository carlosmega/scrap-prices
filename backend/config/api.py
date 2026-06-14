"""Instancia raíz de la API de Django Ninja.

Monta los routers de cada dominio. La instancia se llama `api` para que el
comando de contrato funcione tal cual:
    uv run python manage.py export_openapi_schema --api config.api.api
"""

from ninja import NinjaAPI

from apps.catalog.api import router as catalog_router
from apps.core.api import router as core_router
from apps.geo.api import router as geo_router
from apps.lists.api import router as lists_router

api = NinjaAPI(
    title="ConstruScan API",
    version="0.1.0",
    description="API de ConstruScan (Django Ninja).",
)

api.add_router("", core_router)
api.add_router("", geo_router)
api.add_router("", catalog_router)
api.add_router("", lists_router)
