"""Tareas Celery del subsistema de scraping (F025).

`scrape_retailer_zone` dispara una corrida de ingestión para una zona/tienda y
categoría. La lógica vive en `services.ingest_homedepot` (testeable sin Celery);
la tarea es un wrapper delgado que resuelve las entidades por id y delega.

En MVP no hay broker corriendo: la tarea se ejercita en tests con
`CELERY_TASK_ALWAYS_EAGER=True` (corre síncrona, sin worker ni red real).
"""

from __future__ import annotations

from celery import shared_task

from apps.geo.models import RetailerLocation, Zone
from apps.scraping import services


@shared_task(name="scraping.scrape_retailer_zone")
def scrape_retailer_zone(zone_id: str, location_id: str, category: str) -> dict:
    """Corre la ingestión de Home Depot para una zona/tienda y categoría.

    Resuelve `Zone`/`RetailerLocation` por id y delega en `ingest_homedepot`.
    Devuelve un resumen serializable (id y status de la corrida) para el result
    backend. El stop-if-blocked y el cierre del `ScrapeRun` los maneja el service.
    """
    zone = Zone.objects.get(pk=zone_id)
    location = RetailerLocation.objects.select_related("retailer").get(pk=location_id)
    run = services.ingest_homedepot(zone, location, category)
    return {
        "scrape_run_id": str(run.pk),
        "status": run.status,
        "items_found": run.items_found,
    }
