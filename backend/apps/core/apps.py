"""Configuración de la app core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """App transversal: salud del servicio y utilidades base."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
