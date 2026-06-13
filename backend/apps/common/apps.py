"""Configuración de la app common."""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """App transversal: base abstracta reutilizable por el dominio (F006+)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
