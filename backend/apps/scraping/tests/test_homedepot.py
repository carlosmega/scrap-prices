"""Tests del adapter HD + ingestión a PriceObservation (F025).

100% OFFLINE: el HTTP se mockea con `httpx.MockTransport` devolviendo los golden
fixtures; ningún test pega a una URL real. Un reloj falso hace el rate-limit/
reintentos instantáneos. Cubre:

- `ingest_homedepot` crea las PriceObservation esperadas + ScrapeRun ok con
  items_found correcto; correr 2 veces NO duplica RetailerProduct (idempotencia);
- el adapter envía `physicalStoreId` (de la RetailerLocation) en la URL;
- la tarea Celery (`CELERY_TASK_ALWAYS_EAGER`) produce la ingestión;
- stop-if-blocked: un 429 ⇒ RetailerBlockedError, ScrapeRun failed, sin reintento.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from django.test import override_settings

from apps.catalog.models import RetailerProduct
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping import services
from apps.scraping.client import PoliteClient
from apps.scraping.exceptions import RetailerBlockedError
from apps.scraping.homedepot import HomeDepotAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeClock:
    """Reloj/sleep falsos: el rate-limit no espera en tiempo real en tests."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _make_adapter(handler) -> HomeDepotAdapter:
    """HomeDepotAdapter con PoliteClient sobre MockTransport (sin red)."""
    clock = FakeClock()
    transport = httpx.MockTransport(handler)
    client = PoliteClient(
        user_agent="ConstruScan/test (+contacto)",
        min_delay_seconds=7.0,
        timeout_seconds=5.0,
        max_concurrency_per_domain=1,
        max_retries=3,
        transport=transport,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    return HomeDepotAdapter(client=client)


def _ok_handler(fixture: str, calls: dict | None = None):
    """Handler que sirve un fixture con status 200 y registra las URLs pedidas."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.setdefault("urls", []).append(str(request.url))
            calls["n"] = calls.get("n", 0) + 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            text=_fixture_text(fixture),
        )

    return handler


# --- Fixtures de dominio ----------------------------------------------------
@pytest.fixture
def hd_setup(db):
    """Retailer HD + tienda Monterrey (external_id=18503) + zona + categoría."""
    from apps.geo.models import Retailer, RetailerLocation, Zone

    retailer = Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )
    location = RetailerLocation.objects.create(
        retailer=retailer,
        external_id="18503",
        name="Home Depot Monterrey",
        city="Monterrey",
        state="NL",
    )
    zone = Zone.objects.create(name="Monterrey Metro", slug="mty-metro", state="NL")
    return {"retailer": retailer, "location": location, "zone": zone}


# --- (1) physicalStoreId en la URL -----------------------------------------
@pytest.mark.django_db
def test_adapter_envia_physical_store_id_en_la_url(hd_setup):
    """`set_zone` fija el physicalStoreId desde RetailerLocation.external_id."""
    calls: dict = {}
    adapter = _make_adapter(_ok_handler("homedepot_varilla_batch.json", calls))

    adapter.fetch_products_with_prices("varilla", hd_setup["location"])

    assert calls["n"] == 1
    url = calls["urls"][0]
    assert "physicalStoreId=18503" in url
    assert "searchTerm=varilla" in url
    assert url.startswith("https://www.homedepot.com.mx/search/resources/api/v2/products")


# --- (2) ingestión crea PriceObservation + ScrapeRun ok ---------------------
@pytest.mark.django_db
def test_ingest_homedepot_crea_observations_y_run_ok(hd_setup):
    """La ingestión inserta una PriceObservation por SKU y cierra el run ok."""
    adapter = _make_adapter(_ok_handler("homedepot_varilla_batch.json"))

    run = services.ingest_homedepot(
        hd_setup["zone"], hd_setup["location"], "varilla", adapter=adapter
    )

    assert run.status == ScrapeRun.Status.OK
    assert run.items_found == 4
    assert run.errors == []
    # 4 observaciones, todas en la zona/ubicación, source xhr, precio Decimal.
    observations = PriceObservation.objects.filter(zone=hd_setup["zone"])
    assert observations.count() == 4
    for obs in observations:
        assert obs.source == PriceObservation.Source.XHR
        assert obs.retailer_location == hd_setup["location"]
        assert isinstance(obs.price, Decimal)
        assert obs.price > 0
        assert obs.raw_payload  # raw_payload guardado para auditoría
    # RetailerProduct creado por cada SKU, unmatched (matching manual en Admin).
    rps = RetailerProduct.objects.filter(retailer=hd_setup["retailer"])
    assert rps.count() == 4
    assert all(rp.match_status == RetailerProduct.MatchStatus.UNMATCHED for rp in rps)


# --- (3) idempotencia: 2 corridas no duplican RetailerProduct ---------------
@pytest.mark.django_db
def test_ingest_dos_veces_no_duplica_retailer_product(hd_setup):
    """Correr 2 veces: 8 PriceObservation (histórico) pero solo 4 RetailerProduct."""
    adapter1 = _make_adapter(_ok_handler("homedepot_varilla_batch.json"))
    adapter2 = _make_adapter(_ok_handler("homedepot_varilla_batch.json"))

    services.ingest_homedepot(
        hd_setup["zone"], hd_setup["location"], "varilla", adapter=adapter1
    )
    services.ingest_homedepot(
        hd_setup["zone"], hd_setup["location"], "varilla", adapter=adapter2
    )

    # PriceObservation es histórico: NO se deduplica (cada corrida añade lecturas).
    assert PriceObservation.objects.filter(zone=hd_setup["zone"]).count() == 8
    # RetailerProduct sí es idempotente (clave única retailer+external_sku).
    assert RetailerProduct.objects.filter(retailer=hd_setup["retailer"]).count() == 4


# --- (4) tarea Celery eager produce la ingestión ----------------------------
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
@pytest.mark.django_db
def test_tarea_celery_eager_produce_ingestion(hd_setup, monkeypatch):
    """La tarea `scrape_retailer_zone` corre eager e ingiere precios."""
    from apps.scraping import tasks

    # Inyecta un adapter mockeado: la tarea construye su propio adapter, así que
    # parcheamos ingest_homedepot para que use el transporte fixture (sin red).
    # Capturamos la función ORIGINAL antes de parchear para no recursar.
    adapter = _make_adapter(_ok_handler("homedepot_varilla_batch.json"))
    ingest_original = services.ingest_homedepot

    def _ingest_con_adapter(zone, location, category, **kwargs):
        kwargs.setdefault("adapter", adapter)
        return ingest_original(zone, location, category, **kwargs)

    monkeypatch.setattr(tasks.services, "ingest_homedepot", _ingest_con_adapter)

    result = tasks.scrape_retailer_zone.apply(
        args=(str(hd_setup["zone"].pk), str(hd_setup["location"].pk), "varilla")
    ).get()

    assert result["status"] == ScrapeRun.Status.OK
    assert result["items_found"] == 4
    assert PriceObservation.objects.filter(zone=hd_setup["zone"]).count() == 4


# --- (5) stop-if-blocked: 429 ⇒ RetailerBlockedError, run failed, sin evasión -
@pytest.mark.django_db
def test_ingest_429_lanza_blocked_y_run_failed_sin_reintento(hd_setup):
    """Un 429 detiene la corrida: RetailerBlockedError, run failed, 1 sola request."""
    calls: dict = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text="too many requests")

    adapter = _make_adapter(handler)

    with pytest.raises(RetailerBlockedError):
        services.ingest_homedepot(
            hd_setup["zone"], hd_setup["location"], "varilla", adapter=adapter
        )

    # Guardrail: NO se reintenta para evadir (una sola petición).
    assert calls["n"] == 1
    # Sin items ⇒ el run cierra failed; no se crearon observaciones.
    run = ScrapeRun.objects.get(retailer=hd_setup["retailer"])
    assert run.status == ScrapeRun.Status.FAILED
    assert run.items_found == 0
    assert run.errors and run.errors[0]["type"] == "blocked"
    assert PriceObservation.objects.count() == 0


# --- valor monetario exacto (sanity de Decimal sobre fixture real) ----------
@pytest.mark.django_db
def test_ingest_precio_decimal_exacto_de_fixture_real(hd_setup):
    """El precio ingerido es el Decimal exacto del fixture (sin float)."""
    adapter = _make_adapter(_ok_handler("homedepot_varilla_482588.json"))

    services.ingest_homedepot(
        hd_setup["zone"], hd_setup["location"], "varilla", adapter=adapter
    )

    obs = PriceObservation.objects.get(retailer_product__external_sku="482588")
    assert obs.price == Decimal("20068.00")
    # inventories.18503.quantity == 0.0 ⇒ no disponible en la tienda piloto.
    assert obs.is_available is False
