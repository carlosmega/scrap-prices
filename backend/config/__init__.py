"""Paquete de configuración del proyecto ConstruScan.

Importa la app de Celery para que el decorador @shared_task quede disponible
en todo el proyecto al arrancar Django.
"""

from config.celery import app as celery_app

__all__ = ("celery_app",)
