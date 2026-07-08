"""Registro en Django Admin de precios y auditoría de scraping (F008).

D2 del PRD: el operador monitorea las corridas (`ScrapeRun`) y audita las
lecturas de precio (`PriceObservation`) desde /admin/.
"""

from django.contrib import admin

from apps.prices.models import PriceObservation, ScrapeRun


@admin.register(PriceObservation)
class PriceObservationAdmin(admin.ModelAdmin):
    list_display = (
        "retailer_product",
        "zone",
        "price",
        "currency",
        "is_available",
        "source",
        "captured_at",
    )
    list_filter = ("retailer_product", "zone", "source", "is_available")
    search_fields = ("retailer_product__raw_name", "retailer_product__external_sku")
    ordering = ("-captured_at",)
    autocomplete_fields = ("retailer_product",)


@admin.register(ScrapeRun)
class ScrapeRunAdmin(admin.ModelAdmin):
    # F033: `triggered_by`/`search_term` distinguen las corridas del comando de
    # las disparadas por la búsqueda en vivo (auditoría del gatillo y cooldown).
    list_display = (
        "retailer",
        "zone",
        "status",
        "items_found",
        "triggered_by",
        "search_term",
        "started_at",
    )
    list_filter = ("status", "retailer", "triggered_by")
    search_fields = ("retailer__name", "search_term")
    ordering = ("-started_at",)
