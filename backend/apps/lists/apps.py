"""Configuración de la app lists."""

from django.apps import AppConfig


class ListsConfig(AppConfig):
    """Dominio de listas de cotización anónimas (carrito propio por sesión)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lists"
