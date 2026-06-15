"""Tests del helper de corridas de scraping (F024).

Verifica que `abrir_corrida`/`cerrar_corrida` reusan el modelo `ScrapeRun` de
F008 (no hay modelo nuevo) y derivan el `status` correcto. SQLite, sin red.
"""

from __future__ import annotations

import pytest

from apps.geo.models import Retailer, Zone
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
