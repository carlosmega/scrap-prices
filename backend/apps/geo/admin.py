"""Registro en Django Admin de las entidades de geografía y retailers (F006).

Las 4 entidades son navegables y editables en /admin/ con list_display y
list_filter razonables (incluido scraper_status filtrable en Retailer).
"""

from django.contrib import admin

from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "pricing_model", "scraper_status", "is_active")
    list_filter = ("scraper_status", "pricing_model", "is_active")
    search_fields = ("name", "slug", "base_url")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(RetailerLocation)
class RetailerLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "retailer", "external_id", "city", "state", "is_active")
    list_filter = ("retailer", "state", "city", "is_active")
    search_fields = ("name", "external_id", "address", "city")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "state", "is_active")
    list_filter = ("state", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ZoneLocationMap)
class ZoneLocationMapAdmin(admin.ModelAdmin):
    list_display = ("zone", "retailer_location", "is_primary", "is_active")
    list_filter = ("is_primary", "is_active", "zone")
    search_fields = ("zone__name", "retailer_location__name")
