"""Tests del adapter Construrama + ingestión a PriceObservation (F026).

100% OFFLINE: el HTTP (POST a la Query API de Algolia) se mockea con
`httpx.MockTransport` sirviendo el golden fixture Algolia; ningún test pega a una
URL real ni requiere la search key real. Un reloj falso hace el rate-limit
instantáneo. Cubre:

- el adapter hace POST al host Algolia con headers x-algolia-* y cuerpo con el
  índice + filtro de precio de la zona (OSS7);
- `set_zone` lee `current_store`/app_id/índice de `RetailerLocation.extra`;
- la search key faltante ⇒ ScrapeError ANTES de pegar a la red (0 peticiones);
- `ingest_construrama` crea PriceObservation (source=xhr) + RetailerProduct
  (url/brand/sale_unit del hit) + ScrapeRun ok; 2 corridas no duplican SKU;
- la tarea Celery eager ingiere;
- stop-if-blocked: un 429 ⇒ RetailerBlockedError, run failed, 1 sola petición;
- el management command `scrape --retailer construrama` (dry-run y real).
"""

from __future__ import annotations

import json
from decimal import Decimal
from io import StringIO
from pathlib import Path

import httpx
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping import services
from apps.scraping.client import PoliteClient
from apps.scraping.construrama import ConstruramaAdapter
from apps.scraping.exceptions import RetailerBlockedError, ScrapeError
from apps.scraping.management.commands import scrape as scrape_cmd

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


def _make_client(handler) -> PoliteClient:
    clock = FakeClock()
    return PoliteClient(
        user_agent="ConstruScan/test (+contacto)",
        min_delay_seconds=7.0,
        timeout_seconds=5.0,
        max_concurrency_per_domain=1,
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )


def _make_adapter(handler, *, search_key: str = "test-search-key") -> ConstruramaAdapter:
    """ConstruramaAdapter con PoliteClient sobre MockTransport (sin red).

    La search key se inyecta (dummy): el transporte mockeado no la valida, pero
    el adapter exige que exista antes de armar la petición.
    """
    return ConstruramaAdapter(client=_make_client(handler), search_key=search_key)


def _ok_handler(fixture: str, calls: dict | None = None):
    """Sirve un fixture Algolia con 200 y registra request (método/headers/body/url)."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls["n"] = calls.get("n", 0) + 1
            calls["method"] = request.method
            calls["url"] = str(request.url)
            calls["headers"] = dict(request.headers)
            calls["body"] = json.loads(request.content) if request.content else None
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            text=_fixture_text(fixture),
        )

    return handler


# --- Fixtures de dominio ----------------------------------------------------
@pytest.fixture
def cr_setup(db):
    """Retailer Construrama + distribuidor Monterrey (extra OSS7) + zona + mapa."""
    retailer = Retailer.objects.create(
        name="Construrama",
        slug="construrama",
        base_url="https://www.construrama.com",
        pricing_model=Retailer.PricingModel.DISTRIBUTOR_SUBPATH,
    )
    location = RetailerLocation.objects.create(
        retailer=retailer,
        external_id="distribuidor-mty-centro",
        name="Construrama Materiales del Norte",
        subpath="/nuevo-leon",
        city="Monterrey",
        state="NL",
        extra={
            "subpath": "nuevo-leon",
            "current_store": "OSS7",
            "algolia_app_id": "NJVY3EU5DW",
            "algolia_index": "construrama_mx",
        },
    )
    zone = Zone.objects.create(name="Monterrey Metro", slug="monterrey-metro", state="NL")
    ZoneLocationMap.objects.create(zone=zone, retailer_location=location, is_primary=True)
    return {"retailer": retailer, "location": location, "zone": zone}


# --- (1) POST a Algolia con headers + cuerpo correctos ----------------------
@pytest.mark.django_db
def test_adapter_hace_post_a_algolia_con_headers_y_filtro_de_zona(cr_setup):
    """El adapter hace POST al host Algolia con x-algolia-* y filtro de precio OSS7."""
    calls: dict = {}
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json", calls))

    adapter.fetch_products_with_prices("varilla", cr_setup["location"])

    assert calls["n"] == 1
    assert calls["method"] == "POST"
    assert calls["url"].startswith("https://njvy3eu5dw-dsn.algolia.net/1/indexes/*/queries")
    # Credenciales Algolia en headers (app id público + search key inyectada).
    assert calls["headers"]["x-algolia-application-id"] == "NJVY3EU5DW"
    assert calls["headers"]["x-algolia-api-key"] == "test-search-key"
    # Cuerpo multi-query con el índice y el filtro de precio de la zona OSS7.
    req = calls["body"]["requests"][0]
    assert req["indexName"] == "construrama_mx"
    assert "query=varilla" in req["params"]
    assert "OSS7_priceValue_mxn_double" in req["params"]


# --- (1b) set_zone lee el store/índice de extra -----------------------------
@pytest.mark.django_db
def test_set_zone_usa_current_store_de_extra_para_el_prefijo(cr_setup):
    """`current_store` de extra fija el prefijo del filtro/precio (recon §2.1)."""
    location = cr_setup["location"]
    location.extra = {**location.extra, "current_store": "OSS9"}
    location.save(update_fields=["extra"])

    calls: dict = {}
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json", calls))
    adapter.fetch_products_with_prices("varilla", location)

    params = calls["body"]["requests"][0]["params"]
    assert "OSS9_priceValue_mxn_double" in params
    assert "OSS9Category" in params


@pytest.mark.django_db
def test_set_zone_exige_retailer_location(cr_setup):
    """Una Zone (sin store/índice) no posiciona el adapter: TypeError claro."""
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json"))
    with pytest.raises(TypeError, match="RetailerLocation"):
        adapter.set_zone(cr_setup["zone"])


# --- (1c) search key faltante ⇒ ScrapeError sin pegar a la red --------------
@pytest.mark.django_db
def test_sin_search_key_falla_claro_sin_peticion(cr_setup):
    """Sin search key el adapter falla ANTES de la red (0 peticiones): no se inventa."""
    calls: dict = {"n": 0}
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json", calls), search_key="")

    with pytest.raises(ScrapeError, match="search key"):
        adapter.fetch_products_with_prices("varilla", cr_setup["location"])

    assert calls["n"] == 0  # nunca se pegó a la red


# --- (2) ingestión crea PriceObservation + ScrapeRun ok ---------------------
@pytest.mark.django_db
def test_ingest_construrama_crea_observations_y_run_ok(cr_setup):
    """La ingestión inserta una PriceObservation por hit y cierra el run ok."""
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json"))

    run = services.ingest_construrama(
        cr_setup["zone"], cr_setup["location"], "varilla", adapter=adapter
    )

    assert run.status == ScrapeRun.Status.OK
    assert run.items_found == 7
    assert run.errors == []
    observations = PriceObservation.objects.filter(zone=cr_setup["zone"])
    assert observations.count() == 7
    for obs in observations:
        assert obs.source == PriceObservation.Source.XHR
        assert obs.retailer_location == cr_setup["location"]
        assert isinstance(obs.price, Decimal)
        assert obs.price > 0
        assert obs.currency == "MXN"
        assert obs.raw_payload  # hit crudo guardado (auditoría §2.3)
    # RetailerProduct por SKU, unmatched (matching manual en Admin).
    rps = RetailerProduct.objects.filter(retailer=cr_setup["retailer"])
    assert rps.count() == 7
    assert all(rp.match_status == RetailerProduct.MatchStatus.UNMATCHED for rp in rps)


@pytest.mark.django_db
def test_ingest_construrama_deriva_url_marca_y_sale_unit(cr_setup):
    """El RetailerProduct trae url absoluta, marca (sin 'brands') y sale_unit (F031)."""
    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json"))
    services.ingest_construrama(cr_setup["zone"], cr_setup["location"], "varilla", adapter=adapter)

    # Varilla grado 42 por Kilogramos ⇒ sale_unit kg; marca genérica.
    rp_kg = RetailerProduct.objects.get(external_sku="6000111693")
    assert rp_kg.sale_unit == RetailerProduct.SaleUnit.KG
    assert rp_kg.brand == "GENÉRICO"
    assert rp_kg.url.startswith("https://www.construrama.com/catalogo/")
    assert rp_kg.url.endswith("/p/6000111693")

    # Varilla lisa por Pieza ⇒ sale_unit pieza; el amarrador Truper conserva marca.
    rp_pieza = RetailerProduct.objects.get(external_sku="0204000061")
    assert rp_pieza.sale_unit == RetailerProduct.SaleUnit.PIEZA
    rp_truper = RetailerProduct.objects.get(external_sku="0204000086")
    assert rp_truper.brand == "TRUPER"


# --- (3) idempotencia: 2 corridas no duplican RetailerProduct ---------------
@pytest.mark.django_db
def test_ingest_dos_veces_no_duplica_retailer_product(cr_setup):
    """2 corridas: 14 PriceObservation (histórico) pero solo 7 RetailerProduct."""
    services.ingest_construrama(
        cr_setup["zone"],
        cr_setup["location"],
        "varilla",
        adapter=_make_adapter(_ok_handler("construrama_varilla_algolia.json")),
    )
    services.ingest_construrama(
        cr_setup["zone"],
        cr_setup["location"],
        "varilla",
        adapter=_make_adapter(_ok_handler("construrama_varilla_algolia.json")),
    )

    assert PriceObservation.objects.filter(zone=cr_setup["zone"]).count() == 14
    assert RetailerProduct.objects.filter(retailer=cr_setup["retailer"]).count() == 7


# --- (4) tarea Celery eager produce la ingestión ----------------------------
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
@pytest.mark.django_db
def test_tarea_celery_eager_produce_ingestion(cr_setup, monkeypatch):
    """La tarea `scrape_construrama_zone` corre eager e ingiere precios."""
    from apps.scraping import tasks

    adapter = _make_adapter(_ok_handler("construrama_varilla_algolia.json"))
    ingest_original = services.ingest_construrama

    def _ingest_con_adapter(zone, location, category, **kwargs):
        kwargs.setdefault("adapter", adapter)
        return ingest_original(zone, location, category, **kwargs)

    monkeypatch.setattr(tasks.services, "ingest_construrama", _ingest_con_adapter)

    result = tasks.scrape_construrama_zone.apply(
        args=(str(cr_setup["zone"].pk), str(cr_setup["location"].pk), "varilla")
    ).get()

    assert result["status"] == ScrapeRun.Status.OK
    assert result["items_found"] == 7
    assert PriceObservation.objects.filter(zone=cr_setup["zone"]).count() == 7


# --- (5) stop-if-blocked: 429 ⇒ RetailerBlockedError, run failed, sin evasión -
@pytest.mark.django_db
def test_ingest_429_lanza_blocked_y_run_failed_sin_reintento(cr_setup):
    """Un 429 detiene la corrida: RetailerBlockedError, run failed, 1 sola request."""
    calls: dict = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text="too many requests")

    adapter = _make_adapter(handler)

    with pytest.raises(RetailerBlockedError):
        services.ingest_construrama(
            cr_setup["zone"], cr_setup["location"], "varilla", adapter=adapter
        )

    # Guardrail: NO se reintenta para evadir (una sola petición).
    assert calls["n"] == 1
    run = ScrapeRun.objects.get(retailer=cr_setup["retailer"])
    assert run.status == ScrapeRun.Status.FAILED
    assert run.items_found == 0
    assert run.errors and run.errors[0]["type"] == "blocked"
    assert PriceObservation.objects.count() == 0


# --- (6) management command: dry-run y corrida real -------------------------
def _patch_build_adapter(monkeypatch, handler) -> None:
    adapter = _make_adapter(handler)
    monkeypatch.setattr(scrape_cmd, "build_adapter", lambda slug: adapter)


@pytest.mark.django_db
def test_command_dry_run_construrama_imprime_y_no_escribe(cr_setup, monkeypatch):
    """`scrape --retailer construrama --dry-run` imprime y NO escribe filas."""
    _patch_build_adapter(monkeypatch, _ok_handler("construrama_varilla_algolia.json"))
    out = StringIO()

    call_command(
        "scrape",
        retailer="construrama",
        zone="monterrey-metro",
        category="varilla",
        dry_run=True,
        stdout=out,
    )

    salida = out.getvalue()
    assert "DRY-RUN" in salida
    assert "Productos que se traerían: 7" in salida
    assert PriceObservation.objects.count() == 0
    assert RetailerProduct.objects.count() == 0
    assert ScrapeRun.objects.count() == 0


@pytest.mark.django_db
def test_command_corrida_real_construrama_crea_observations(cr_setup, monkeypatch):
    """`scrape --retailer construrama` (sin dry-run) crea PriceObservation + run ok."""
    _patch_build_adapter(monkeypatch, _ok_handler("construrama_varilla_algolia.json"))
    out = StringIO()

    call_command(
        "scrape",
        retailer="construrama",
        zone="monterrey-metro",
        category="varilla",
        stdout=out,
    )

    assert "Corrida ok" in out.getvalue()
    assert PriceObservation.objects.filter(zone=cr_setup["zone"]).count() == 7
    run = ScrapeRun.objects.get(retailer=cr_setup["retailer"])
    assert run.status == ScrapeRun.Status.OK
    assert run.items_found == 7
    # F033: el comando sigue auditando su origen como 'command' (default),
    # sin término de búsqueda (search_term null; eso es del vivo).
    assert run.triggered_by == ScrapeRun.TriggeredBy.COMMAND
    assert run.search_term is None


# --- (7) integración seed↔comando real (regresión del review F026) ----------
@pytest.mark.django_db
def test_seed_y_scrape_construrama_dry_run_resuelve_el_mapeo(monkeypatch):
    """El seed REAL + `scrape --retailer construrama --dry-run` resuelve la tienda.

    Regresión: el seed siembra el `ZoneLocationMap` de Construrama con
    `is_primary=True`, así que `_resolver_primary_location` (que filtra por
    retailer) encuentra la tienda y NO lanza el `CommandError` de mapeo. Con el
    adapter mockeado el dry-run imprime los 7 productos. Sin el fix del seed
    (is_primary=False) este test falla con el CommandError de mapeo.
    """
    call_command("seed")
    _patch_build_adapter(monkeypatch, _ok_handler("construrama_varilla_algolia.json"))
    out = StringIO()

    call_command(
        "scrape",
        retailer="construrama",
        zone="monterrey-metro",
        category="varilla",
        dry_run=True,
        stdout=out,
    )

    salida = out.getvalue()
    # Prueba que la tienda se resolvió (se imprime la línea de contexto) y corre.
    assert "construrama" in salida
    assert "Productos que se traerían: 7" in salida


@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY="")
@pytest.mark.django_db
def test_seed_y_scrape_construrama_sin_key_para_en_guardrail_no_en_mapeo():
    """Con el seed REAL y sin search key, el comando para en el GUARDRAIL, no en el mapeo.

    El mapeo de zona↔tienda se resuelve (gracias al fix del seed); el único fallo
    restante es la falta de `CONSTRURAMA_ALGOLIA_SEARCH_KEY` → `ScrapeError` que el
    comando surface como CommandError del guardrail (menciona la search key), NUNCA
    el CommandError de 'RetailerLocation primaria'. No hay petición de red (el
    adapter falla antes de pegar).
    """
    call_command("seed")

    with pytest.raises(CommandError) as exc_info:
        call_command(
            "scrape",
            retailer="construrama",
            zone="monterrey-metro",
            category="varilla",
            dry_run=True,
        )

    mensaje = str(exc_info.value)
    assert "search key" in mensaje  # guardrail esperado (falta la key)
    assert "primaria" not in mensaje  # NO es el CommandError de mapeo
