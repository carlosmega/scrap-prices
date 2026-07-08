"""Tests del helper de corridas de scraping (F024/F033).

Verifica que `abrir_corrida`/`cerrar_corrida` reusan el modelo `ScrapeRun` de
F008 (no hay modelo nuevo) y derivan el `status` correcto; F033: los campos de
auditoría del origen (`search_term`/`triggered_by`) y la resolución de tienda
primaria extraída del comando (`resolver_primary_location`). SQLite, sin red.
"""

from __future__ import annotations

import pytest

from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices.models import ScrapeRun
from apps.scraping import services


@pytest.fixture
def home_depot():
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def zona():
    return Zone.objects.create(name="Monterrey", slug="monterrey", state="Nuevo León")


@pytest.mark.django_db
def test_abrir_corrida_arranca_como_failed(home_depot, zona):
    """Una corrida recién abierta queda 'failed' hasta cerrarse (default seguro)."""
    run = services.abrir_corrida(home_depot, zona)
    assert isinstance(run, ScrapeRun)
    assert run.status == ScrapeRun.Status.FAILED
    assert run.started_at is not None
    assert run.finished_at is None
    assert run.retailer == home_depot
    assert run.zone == zona


@pytest.mark.django_db
def test_cerrar_corrida_ok_sin_errores(home_depot):
    """Items y sin errores ⇒ status ok."""
    run = services.abrir_corrida(home_depot)
    cerrada = services.cerrar_corrida(run, items_found=42, errors=[])
    cerrada.refresh_from_db()
    assert cerrada.status == ScrapeRun.Status.OK
    assert cerrada.items_found == 42
    assert cerrada.errors == []
    assert cerrada.finished_at is not None


@pytest.mark.django_db
def test_cerrar_corrida_partial_con_errores(home_depot):
    """Items y errores ⇒ status partial; los errores se guardan como JSON."""
    run = services.abrir_corrida(home_depot)
    errores = [{"sku": "HD-002", "error": "precio no encontrado"}]
    cerrada = services.cerrar_corrida(run, items_found=10, errors=errores)
    cerrada.refresh_from_db()
    assert cerrada.status == ScrapeRun.Status.PARTIAL
    assert cerrada.items_found == 10
    assert cerrada.errors == errores


@pytest.mark.django_db
def test_cerrar_corrida_sin_items_es_failed(home_depot):
    """Sin items ⇒ failed, aunque no haya errores."""
    run = services.abrir_corrida(home_depot)
    cerrada = services.cerrar_corrida(run, items_found=0)
    cerrada.refresh_from_db()
    assert cerrada.status == ScrapeRun.Status.FAILED


@pytest.mark.django_db
def test_helper_no_crea_modelo_nuevo(home_depot):
    """El helper persiste sobre el ScrapeRun de F008 (apps.prices), no uno nuevo."""
    run = services.abrir_corrida(home_depot)
    assert ScrapeRun.objects.filter(pk=run.pk).exists()
    assert run._meta.app_label == "prices"


# --- F033: auditoría del origen de la corrida --------------------------------


@pytest.mark.django_db
def test_abrir_corrida_default_es_comando_sin_termino(home_depot):
    """Sin kwargs, la corrida audita triggered_by='command' y search_term null.

    Es lo que usa el comando `scrape` existente: su comportamiento no cambia
    con F033 (el default del campo es 'command').
    """
    run = services.abrir_corrida(home_depot)
    assert run.triggered_by == ScrapeRun.TriggeredBy.COMMAND
    assert run.search_term is None


@pytest.mark.django_db
def test_abrir_corrida_de_busqueda_estampa_termino_y_origen(home_depot, zona):
    """La búsqueda en vivo estampa search_term + triggered_by='search'."""
    run = services.abrir_corrida(
        home_depot,
        zona,
        search_term="cemento",
        triggered_by=ScrapeRun.TriggeredBy.SEARCH,
    )
    run.refresh_from_db()
    assert run.search_term == "cemento"
    assert run.triggered_by == ScrapeRun.TriggeredBy.SEARCH


# --- F033: resolución de tienda primaria (extraída del comando) ---------------


@pytest.mark.django_db
def test_resolver_primary_location_encuentra_la_primaria_del_retailer(home_depot, zona):
    """Devuelve la RetailerLocation del ZoneLocationMap is_primary del retailer."""
    location = RetailerLocation.objects.create(
        retailer=home_depot,
        external_id="1333",
        name="HD Valle Oriente",
        city="Monterrey",
        state="NL",
    )
    ZoneLocationMap.objects.create(zone=zona, retailer_location=location, is_primary=True)

    assert services.resolver_primary_location(home_depot, zona) == location


@pytest.mark.django_db
def test_resolver_primary_location_none_si_no_hay_primaria(home_depot, zona):
    """Sin mapeo primario (o solo is_primary=False) devuelve None, sin reventar."""
    assert services.resolver_primary_location(home_depot, zona) is None

    location = RetailerLocation.objects.create(
        retailer=home_depot,
        external_id="1333",
        name="HD Valle Oriente",
        city="Monterrey",
        state="NL",
    )
    ZoneLocationMap.objects.create(zone=zona, retailer_location=location, is_primary=False)
    assert services.resolver_primary_location(home_depot, zona) is None
