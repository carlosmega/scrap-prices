"""Modelos de catálogo (F007, PRD §8 y §11).

El catálogo normaliza "el mismo producto" entre retailers: un `CanonicalProduct`
agrupa los `RetailerProduct` (SKUs reales de cada tienda) que le corresponden.
El matching en MVP es **manual vía Django Admin** (PRD D1); el matching
automático con rapidfuzz es fase posterior. La categoría piloto es **varilla**,
pero los datos se curan a mano en Admin (no se hardcodean aquí).

Todas las entidades heredan de `TimeStampedUUIDModel` (apps.common.models).
"""

from django.db import models

from apps.common.models import TimeStampedUUIDModel
from apps.geo.models import Retailer


class Category(TimeStampedUUIDModel):
    """Categoría del catálogo, jerárquica (self-FK). Piloto MVP: varilla."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class CanonicalProduct(TimeStampedUUIDModel):
    """Producto normalizado entre retailers (agrupa SKUs equivalentes)."""

    class Unit(models.TextChoices):
        PIEZA = "pieza", "Pieza"
        SACO = "saco", "Saco"
        METRO = "m", "Metro"
        KILOGRAMO = "kg", "Kilogramo"

    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    unit = models.CharField(max_length=16, choices=Unit.choices)
    # specs libres por producto: p.ej. {calibre, diametro, longitud, marca,
    # presentacion}. JSON para no rigidizar el esquema en MVP.
    specs = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RetailerProduct(TimeStampedUUIDModel):
    """Un SKU tal como existe en UN retailer; se cura al canónico en Admin."""

    class MatchStatus(models.TextChoices):
        UNMATCHED = "unmatched", "Sin asignar"
        AUTO = "auto", "Automático"
        MANUAL = "manual", "Manual"
        REJECTED = "rejected", "Rechazado"

    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name="products",
    )
    external_sku = models.CharField(max_length=200)
    raw_name = models.CharField(max_length=300)
    url = models.URLField(blank=True)
    unit_raw = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=200, blank=True)
    canonical_product = models.ForeignKey(
        CanonicalProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retailer_products",
    )
    match_status = models.CharField(
        max_length=16,
        choices=MatchStatus.choices,
        default=MatchStatus.UNMATCHED,
    )
    match_confidence = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["retailer", "raw_name"]
        unique_together = (("retailer", "external_sku"),)

    def __str__(self) -> str:
        return f"{self.retailer.name} — {self.raw_name}"
