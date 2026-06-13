"""Configuración de la app geo."""

from django.apps import AppConfig


class GeoConfig(AppConfig):
    """Dominio de geografía y retailers: zonas normalizadas y ubicaciones."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.geo"
