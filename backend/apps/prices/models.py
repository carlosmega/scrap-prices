"""Modelos de precios y auditoría de scraping (F008, PRD §8 y §9).

Principio arquitectónico no negociable: el scraping NO ocurre en vivo. Los
scrapers escriben `PriceObservation` (lecturas históricas con zona + timestamp,
nunca se sobrescriben) y registran cada corrida en `ScrapeRun` (auditoría). La
búsqueda del usuario consulta siempre la DB propia, jamás la web del retailer.

Esta feature solo crea el destino de los datos: no implementa scrapers (M2) ni
endpoints de precios (M3).

Todas las entidades heredan de `TimeStampedUUIDModel` (apps.common.models).
"""

from django.db import models

from apps.catalog.models import RetailerProduct
from apps.common.models import TimeStampedUUIDModel
from apps.geo.models import Retailer, RetailerLocation, Zone


class PriceObservation(TimeStampedUUIDModel):
    """Una lectura de precio de un SKU en una zona/ubicación (histórica).

    Nunca se sobrescribe: cada captura es una fila nueva. El precio más fresco
    por (producto, zona) se obtiene ordenando por `-captured_at`, soportado por
    el índice compuesto. `price` es Decimal (nunca float) por exactitud
    monetaria (PRD §8).
    """

    class Source(models.TextChoices):
        XHR = "xhr", "XHR / API"
        HTML = "html", "HTML"
        PLAYWRIGHT = "playwright", "Playwright"

    retailer_product = models.ForeignKey(
        RetailerProduct,
        on_delete=models.CASCADE,
        related_name="observations",
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    retailer_location = models.ForeignKey(
        RetailerLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="MXN")
    is_available = models.BooleanField(default=True)
    source = models.CharField(max_length=16, choices=Source.choices)
    # Momento de la lectura (lo fija el scraper); distinto de created_at, que es
    # cuándo se insertó la fila. Indexado para consultas por recencia.
    captured_at = models.DateTimeField(db_index=True)
    # Payload crudo de la captura para auditabilidad (guardrail §2.3 punto 5).
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            # Soporta "último precio por producto y zona" (consulta caliente M3).
            models.Index(
                fields=["retailer_product", "zone", "-captured_at"],
                name="price_obs_rp_zone_capt_idx",
            ),
        ]

    def __str__(self) -> str:
        cuando = self.captured_at.strftime("%Y-%m-%d %H:%M")
        return f"{self.retailer_product} — {self.price} {self.currency} @ {cuando}"


class ScrapeRun(TimeStampedUUIDModel):
    """Auditoría de una corrida de scraping (D2 del PRD: monitorear corridas)."""

    class Status(models.TextChoices):
        OK = "ok", "Correcta"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallida"

    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name="scrape_runs",
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scrape_runs",
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    items_found = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.retailer.name} — {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"
