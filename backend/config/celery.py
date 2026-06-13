"""Esqueleto de Celery para ConstruScan.

MVP: solo importable. No hay broker corriendo ni workers; las tareas reales de
scraping llegan en milestones posteriores. Este módulo existe para que el
wiring (@shared_task, autodiscover) quede listo desde el bootstrap.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("construscan")

# Toma la configuración de Django (claves con prefijo CELERY_).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubre tasks.py en cada app instalada.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    """Tarea de diagnóstico mínima (no se ejercita en MVP)."""
    print(f"Request: {self.request!r}")
