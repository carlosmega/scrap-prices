"""Lógica de orquestación de corridas de scraping (F024). Sin HTTP, sin routers.

Helpers para abrir/cerrar una corrida (`ScrapeRun`) reutilizando el modelo de
F008 (`apps.prices.models.ScrapeRun`) — NO se crea un modelo nuevo. La política
de cortesía/reintentos/stop-if-blocked vive en `apps.scraping.client`; aquí solo
se registra la auditoría de la corrida (D2 del PRD).
"""

from __future__ import annotations

from django.utils import timezone

from apps.geo.models import Retailer, Zone
from apps.prices.models import ScrapeRun


def abrir_corrida(retailer: Retailer, zone: Zone | None = None) -> ScrapeRun:
    """Abre una corrida de scraping: registra el inicio en `ScrapeRun`.

    Devuelve el `ScrapeRun` con `started_at` fijado y `status` provisional
    `failed`: si la corrida muere a mitad sin cerrarse, queda registrada como
    fallida (default seguro). `cerrar_corrida` la lleva a su estado final.
    """
    return ScrapeRun.objects.create(
        retailer=retailer,
        zone=zone,
        started_at=timezone.now(),
        status=ScrapeRun.Status.FAILED,
    )


def cerrar_corrida(
    run: ScrapeRun,
    *,
    items_found: int = 0,
    errors: list | None = None,
) -> ScrapeRun:
    """Cierra una corrida y deriva su `status` de los resultados.

    Regla de estado:
    - `ok`: hubo items y ningún error.
    - `partial`: hubo items y también errores.
    - `failed`: no hubo items (con o sin errores).
    """
    errors = errors or []
    if items_found <= 0:
        status = ScrapeRun.Status.FAILED
    elif errors:
        status = ScrapeRun.Status.PARTIAL
    else:
        status = ScrapeRun.Status.OK

    run.finished_at = timezone.now()
    run.status = status
    run.items_found = items_found
    run.errors = errors
    run.save(update_fields=["finished_at", "status", "items_found", "errors", "updated_at"])
    return run
