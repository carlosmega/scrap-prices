"""Configuración de la app catalog."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Dominio de catálogo: categorías, productos canónicos y SKUs por retailer."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
