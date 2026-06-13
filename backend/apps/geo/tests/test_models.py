"""Tests de modelo de geografía y retailers (F006).

Cubre: creación de Retailer + RetailerLocation, Zone y un ZoneLocationMap que
los une; verifica is_primary, el soft-delete (is_active) y que el
unique_together (zone, retailer_location) se respeta. SQLite, sin Docker.
"""

import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap


@pytest.fixture
def retailer():
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def location(retailer):
    return RetailerLocation.objects.create(
        retailer=retailer,
        external_id="store-1234",
        name="HD Monterrey Centro",
        city="Monterrey",
        state="Nuevo León",
        lat="25.686610",
        lng="-100.316110",
    )


@pytest.fixture
def zone():
    return Zone.objects.create(
        name="Monterrey Metro",
        slug="monterrey-metro",
        state="Nuevo León",
    )


@pytest.mark.django_db
def test_retailer_defaults_y_base_abstracta(retailer):
    """Retailer hereda la base: id es UUID, timestamps e is_active por defecto."""
    assert isinstance(retailer.id, uuid.UUID)
    assert retailer.created_at is not None
    assert retailer.updated_at is not None
    assert retailer.is_active is True
    # scraper_status tiene default 'active'.
    assert retailer.scraper_status == Retailer.ScraperStatus.ACTIVE


@pytest.mark.django_db
def test_retailer_tiene_locations_related_name(retailer, location):
    """La FK RetailerLocation→Retailer expone el related_name 'locations'."""
    assert location.retailer == retailer
    assert list(retailer.locations.all()) == [location]


@pytest.mark.django_db
def test_zone_location_map_une_zona_y_ubicacion(zone, location):
    """Un ZoneLocationMap enlaza Zone↔RetailerLocation y respeta is_primary."""
    mapping = ZoneLocationMap.objects.create(
        zone=zone,
        retailer_location=location,
        is_primary=True,
    )

    assert mapping.is_primary is True
    assert list(zone.location_maps.all()) == [mapping]
    assert list(location.zone_maps.all()) == [mapping]


@pytest.mark.django_db
def test_zone_location_map_default_is_primary_false(zone, location):
    """is_primary es False por defecto si no se especifica."""
    mapping = ZoneLocationMap.objects.create(zone=zone, retailer_location=location)
    assert mapping.is_primary is False


@pytest.mark.django_db
def test_zone_location_map_unique_together(zone, location):
    """El par (zone, retailer_location) es único: el duplicado lanza IntegrityError."""
    ZoneLocationMap.objects.create(zone=zone, retailer_location=location)

    with pytest.raises(IntegrityError), transaction.atomic():
        ZoneLocationMap.objects.create(zone=zone, retailer_location=location)


@pytest.mark.django_db
def test_soft_delete_marca_is_active_false(retailer):
    """El soft-delete de la base se hace marcando is_active=False (no borra fila)."""
    retailer.is_active = False
    retailer.save(update_fields=["is_active"])

    refreshed = Retailer.objects.get(pk=retailer.pk)
    assert refreshed.is_active is False
