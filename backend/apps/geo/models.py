"""Modelos de geografía y retailers (F006, PRD §8 y §10).

ConstruScan compara precios por **zona**. La zona del usuario no es comparable
directamente entre retailers (HD usa tienda+cookie; Construrama usa
distribuidor+ciudad), así que se normaliza con una `Zone` interna mapeada a las
ubicaciones físicas de cada retailer vía `ZoneLocationMap`.

Todas las entidades heredan de `TimeStampedUUIDModel` (apps.common.models).
"""

from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Retailer(TimeStampedUUIDModel):
    """Cadena minorista (Home Depot, Construrama, ...)."""

    class PricingModel(models.TextChoices):
        ZONE_COOKIE = "zone_cookie", "Zona por cookie"
        DISTRIBUTOR_SUBPATH = "distributor_subpath", "Distribuidor por subpath"

    class ScraperStatus(models.TextChoices):
        ACTIVE = "active", "Activo"
        PAUSED = "paused", "Pausado"
        NON_VIABLE = "non_viable", "No viable"

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    base_url = models.URLField()
    pricing_model = models.CharField(max_length=32, choices=PricingModel.choices)
    scraper_status = models.CharField(
        max_length=16,
        choices=ScraperStatus.choices,
        default=ScraperStatus.ACTIVE,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RetailerLocation(TimeStampedUUIDModel):
    """Ubicación física de un retailer: tienda HD o distribuidor Construrama."""

    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    external_id = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    subpath = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Params de routing específicos del retailer que no caben en los campos base
    # (HD: market_id/st_loc_id; Construrama: distribuidor/ciudad, F026). Genérico.
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["retailer", "name"]

    def __str__(self) -> str:
        return f"{self.retailer.name} — {self.name}"


class Zone(TimeStampedUUIDModel):
    """Zona interna normalizada (unidad de comparación de precios)."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    state = models.CharField(max_length=120)
    centroid_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    centroid_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ZoneLocationMap(TimeStampedUUIDModel):
    """Resuelve qué ubicación física sirve a una zona (N↔N Zone–Location)."""

    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name="location_maps",
    )
    retailer_location = models.ForeignKey(
        RetailerLocation,
        on_delete=models.CASCADE,
        related_name="zone_maps",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = (("zone", "retailer_location"),)
        ordering = ["zone", "-is_primary"]

    def __str__(self) -> str:
        return f"{self.zone.name} ↔ {self.retailer_location.name}"
