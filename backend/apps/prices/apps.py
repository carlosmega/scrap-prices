"""Configuración de la app prices."""

from django.apps import AppConfig


class PricesConfig(AppConfig):
    """Dominio de precios: observaciones históricas y auditoría de scraping."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.prices"
