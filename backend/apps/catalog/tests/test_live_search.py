"""Tests de la búsqueda en vivo bajo demanda (F033): GET /search live-on-miss.

100% OFFLINE: los adapters reales (HD y Construrama) corren sobre
`httpx.MockTransport` sirviendo los golden fixtures; la fábrica
`apps.scraping.services.build_live_adapter` se parchea por test (el conftest
raíz la parchea a "explota" por default: ningún test pega a la red). Cubre los
criterios backend de la spec F033:

- término sin datos → dispara la corrida en vivo de AMBOS retailers, ingesta
  (RetailerProduct + PriceObservation + ScrapeRun con search_term y
  triggered_by="search") y responde raw_results poblado + live.triggered;
- NO dispara: con datos frescos (seed), con live=never, con len(q)<3 y dentro
  del cooldown (aunque la corrida previa hallara 0); el cooldown es por retailer;
- un retailer bloqueado (429 → stop-if-blocked, sin reintento) no impide
  ingerir/responder el otro;
- Construrama sin search key → skipped con motivo y HD sigue;
- el presupuesto total: el retailer lento se reporta failed: timeout.

Los tests que SÍ corren el vivo usan `django_db(transaction=True)`: la
orquestación corre cada retailer en un hilo con su propia conexión, y esas
conexiones solo ven datos COMMITEADOS (con el django_db normal, la transacción
del test es invisible para los hilos).
"""

from __future__ import annotations

import threading
import time
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from ninja.testing import TestClient

from apps.catalog.api import router
from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, Zone
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping import services as scraping_services
from apps.scraping.client import PoliteClient
from apps.scraping.construrama import ConstruramaAdapter
from apps.scraping.homedepot import HomeDepotAdapter

FIXTURES = Path(__file__).parents[2] / "scraping" / "tests" / "fixtures"

# La clave NO es real: el transporte está mockeado; solo evita el skip por
# credencial y el fail-claro del adapter (que exige que exista una key).
KEY_DE_PRUEBA = "test-search-key"


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


def _ok_handler(fixture: str, calls: dict | None = None):
    """Sirve un golden fixture con 200 y cuenta las peticiones."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls["n"] = calls.get("n", 0) + 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            text=_fixture_text(fixture),
        )

    return handler


def _bloqueo_handler(calls: dict):
    """Responde 429 (bloqueo deliberado del retailer) y cuenta peticiones."""

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] = calls.get("n", 0) + 1
        return httpx.Response(429, text="too many requests")

    return handler


def _patch_adapters(monkeypatch, *, hd_handler=None, cr_handler=None) -> None:
    """Parchea la fábrica de adapters en vivo con MockTransport (sin red).

    Un handler None significa "este test NO espera que ese retailer corra":
    si el orquestador lo intenta, el AssertionError sale como outcome failed
    y el test lo detecta en el status esperado.
    """

    def build(slug: str):
        if slug == "home-depot":
            assert hd_handler is not None, "el test no esperaba correr Home Depot en vivo"
            return HomeDepotAdapter(client=_make_client(hd_handler))
        if slug == "construrama":
            assert cr_handler is not None, "el test no esperaba correr Construrama en vivo"
            return ConstruramaAdapter(client=_make_client(cr_handler), search_key=KEY_DE_PRUEBA)
        raise AssertionError(f"slug de retailer inesperado: {slug}")

    monkeypatch.setattr(scraping_services, "build_live_adapter", build)


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def seeded(db):
    """Seed demo (con observaciones FRESCAS + el crudo Truper) y atajos."""
    call_command("seed")
    return {
        "zona": Zone.objects.get(slug="monterrey-metro"),
        "hd": Retailer.objects.get(slug="home-depot"),
        "cr": Retailer.objects.get(slug="construrama"),
    }


def _get_search(client, zona, q: str, extra: str = "") -> dict:
    response = client.get(f"/search?q={q}&zone_id={zona.id}{extra}")
    assert response.status_code == 200
    return response.json()


def _statuses(body: dict) -> dict[str, dict]:
    return {r["retailer_slug"]: r for r in body["live"]["retailers"]}


# --- (1) término sin datos → dispara AMBOS, ingesta y responde ---------------
@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY=KEY_DE_PRUEBA)
@pytest.mark.django_db(transaction=True)
def test_termino_sin_datos_dispara_vivo_de_ambos_e_ingesta(client, seeded, monkeypatch):
    """ "alambre" no tiene datos → corrida en vivo de HD+CR, cache-through y crudos."""
    hd_calls: dict = {}
    cr_calls: dict = {}
    _patch_adapters(
        monkeypatch,
        hd_handler=_ok_handler("homedepot_varilla_batch.json", hd_calls),
        cr_handler=_ok_handler("construrama_varilla_algolia.json", cr_calls),
    )

    body = _get_search(client, seeded["zona"], "alambre")

    # Corrida en vivo reportada: ambos retailers ok, en orden estable.
    assert body["live"] is not None
    assert body["live"]["triggered"] is True
    assert body["live"]["duration_ms"] >= 0
    assert [r["retailer_slug"] for r in body["live"]["retailers"]] == [
        "home-depot",
        "construrama",
    ]
    por_slug = _statuses(body)
    assert por_slug["home-depot"]["status"] == "ok"
    assert por_slug["home-depot"]["items_found"] == 4  # golden fixture HD
    assert por_slug["construrama"]["status"] == "ok"
    assert por_slug["construrama"]["items_found"] == 7  # golden fixture Algolia
    assert hd_calls["n"] == 1 and cr_calls["n"] == 1  # una petición por retailer

    # Cache-through: ScrapeRun por retailer con search_term y triggered_by=search.
    runs = ScrapeRun.objects.filter(triggered_by=ScrapeRun.TriggeredBy.SEARCH)
    assert runs.count() == 2
    for run in runs:
        assert run.search_term == "alambre"
        assert run.zone == seeded["zona"]
        assert run.status == ScrapeRun.Status.OK

    # RetailerProduct nuevos quedan unmatched (matching manual en Admin)...
    alambre_hd = RetailerProduct.objects.get(retailer=seeded["hd"], external_sku="462843")
    assert alambre_hd.match_status == RetailerProduct.MatchStatus.UNMATCHED
    assert alambre_hd.canonical_product is None
    # ...con su PriceObservation en la zona (histórico + frescura).
    assert PriceObservation.objects.filter(
        retailer_product=alambre_hd, zone=seeded["zona"]
    ).exists()
    # El amarrador ya sembrado NO se duplica (clave retailer+external_sku).
    assert RetailerProduct.objects.filter(external_sku="0204000086").count() == 1

    # Y la MISMA respuesta ya sirve lo hallado. F035: los crudos se seleccionan
    # por término scrapeado ∪ nombre, así que el vivo bajo "alambre" expone TODO
    # lo ingestado bajo ese término (no solo los nombres que contienen "alambre").
    assert body["results"] == []  # ningún canónico se llama "alambre"
    crudos = body["raw_results"]
    por_sku = {c["external_sku"]: c for c in crudos}
    # El crudo de HD cuyo nombre además contiene "alambre" está, con sus datos.
    assert "462843" in por_sku
    crudo = por_sku["462843"]
    assert crudo["retailer_slug"] == "home-depot"
    assert crudo["raw_name"].startswith("ALAMBRE DE ACERO RECOCIDO")
    assert crudo["price"] == 27.7
    assert crudo["currency"] == "MXN"
    assert crudo["captured_at"] is not None
    # F035: el resto de lo scrapeado bajo "alambre" también se sirve como crudo
    # (aunque su nombre no diga "alambre"): la respuesta ya no queda en 1 solo.
    assert len(crudos) > 1


# --- (2) con datos frescos (seed) NO dispara ---------------------------------
@pytest.mark.django_db
def test_con_datos_frescos_no_dispara_y_expone_crudos_sembrados(client, seeded):
    """El seed deja "varilla" fresco → live=null; la sección cruda trae al Truper."""
    body = _get_search(client, seeded["zona"], "varilla")

    assert set(body.keys()) == {"results", "raw_results", "live"}
    assert body["live"] is None  # no se disparó: hay observaciones < TTL
    assert ScrapeRun.objects.count() == 0
    assert len(body["results"]) == 3  # canónicos comparados, igual que antes

    # El crudo sembrado (amarrador Truper, real del fixture) es visible.
    crudos = body["raw_results"]
    assert len(crudos) == 1
    crudo = crudos[0]
    assert crudo["retailer_slug"] == "construrama"
    assert crudo["retailer_name"] == "Construrama"
    assert crudo["external_sku"] == "0204000086"
    assert crudo["raw_name"] == "Truper, Amarrador De Varillas Con Grip, Pieza"
    assert crudo["brand"] == "TRUPER"
    assert crudo["sale_unit"] == "pieza"
    assert crudo["price"] == 125.0
    assert crudo["is_available"] is True
    assert crudo["url"].endswith("/p/0204000086")
    assert crudo["retailer_product_id"]
    assert crudo["captured_at"] is not None


# --- (3) live=never NO dispara ------------------------------------------------
@pytest.mark.django_db
def test_live_never_no_dispara_aunque_no_haya_datos(client, seeded):
    """ "cemento" no tiene datos, pero live=never lo apaga: live=null y sin corridas."""
    body = _get_search(client, seeded["zona"], "cemento", extra="&live=never")

    assert body["live"] is None
    assert body["results"] == []
    assert body["raw_results"] == []
    assert ScrapeRun.objects.count() == 0


# --- (4) término corto NO dispara ---------------------------------------------
@pytest.mark.django_db
def test_termino_corto_no_dispara(client, seeded):
    """len(q normalizado) < 3 nunca dispara (ni con cero datos)."""
    body = _get_search(client, seeded["zona"], "va")

    assert body["live"] is None
    assert ScrapeRun.objects.count() == 0


# --- (5) cooldown NO dispara (aunque la corrida previa hallara 0) -------------
@pytest.mark.django_db
def test_dentro_del_cooldown_no_dispara_aunque_hallara_cero(client, seeded):
    """Corrida previa del término (0 items, failed) hace 5 min → no se martilla."""
    hace_5_min = timezone.now() - timedelta(minutes=5)
    for retailer in (seeded["hd"], seeded["cr"]):
        ScrapeRun.objects.create(
            retailer=retailer,
            zone=seeded["zona"],
            started_at=hace_5_min,
            finished_at=hace_5_min,
            status=ScrapeRun.Status.FAILED,
            items_found=0,
            search_term="cemento",
            triggered_by=ScrapeRun.TriggeredBy.SEARCH,
        )

    body = _get_search(client, seeded["zona"], "cemento")

    assert body["live"] is None  # dentro del cooldown: no se re-dispara
    assert ScrapeRun.objects.count() == 2  # no hay corridas nuevas


@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY=KEY_DE_PRUEBA)
@pytest.mark.django_db(transaction=True)
def test_cooldown_es_por_retailer(client, seeded, monkeypatch):
    """HD en cooldown queda fuera; Construrama (sin corrida previa) SÍ corre."""
    ScrapeRun.objects.create(
        retailer=seeded["hd"],
        zone=seeded["zona"],
        started_at=timezone.now() - timedelta(minutes=5),
        status=ScrapeRun.Status.FAILED,
        items_found=0,
        search_term="cemento",
        triggered_by=ScrapeRun.TriggeredBy.SEARCH,
    )
    cr_calls: dict = {}
    _patch_adapters(
        monkeypatch, cr_handler=_ok_handler("construrama_varilla_algolia.json", cr_calls)
    )

    body = _get_search(client, seeded["zona"], "cemento")

    assert body["live"]["triggered"] is True
    assert [r["retailer_slug"] for r in body["live"]["retailers"]] == ["construrama"]
    assert _statuses(body)["construrama"]["status"] == "ok"
    assert cr_calls["n"] == 1
    # Solo Construrama abrió corrida nueva; HD sigue con la del cooldown.
    assert ScrapeRun.objects.filter(retailer=seeded["cr"]).count() == 1
    assert ScrapeRun.objects.filter(retailer=seeded["hd"]).count() == 1


# --- (6) un retailer bloqueado no impide al otro -------------------------------
@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY=KEY_DE_PRUEBA)
@pytest.mark.django_db(transaction=True)
def test_retailer_bloqueado_no_impide_al_otro(client, seeded, monkeypatch):
    """HD responde 429 (blocked, stop-if-blocked) y Construrama ingesta igual."""
    hd_calls: dict = {}
    _patch_adapters(
        monkeypatch,
        hd_handler=_bloqueo_handler(hd_calls),
        cr_handler=_ok_handler("construrama_varilla_algolia.json"),
    )

    body = _get_search(client, seeded["zona"], "cemento")

    por_slug = _statuses(body)
    assert por_slug["home-depot"]["status"] == "blocked"
    assert por_slug["home-depot"]["items_found"] == 0
    detail = por_slug["home-depot"]["detail"]
    assert "429" in detail
    assert "Traceback" not in detail  # motivo breve, sin stacktrace
    assert por_slug["construrama"]["status"] == "ok"
    assert por_slug["construrama"]["items_found"] == 7

    # stop-if-blocked: UNA sola petición a HD (sin reintento ni evasión).
    assert hd_calls["n"] == 1

    # Construrama ingirió sus 7 hits pese al bloqueo de HD.
    assert PriceObservation.objects.filter(
        retailer_product__external_sku="6000111693", zone=seeded["zona"]
    ).exists()
    run_hd = ScrapeRun.objects.get(retailer=seeded["hd"])
    assert run_hd.status == ScrapeRun.Status.FAILED
    assert run_hd.search_term == "cemento"
    assert run_hd.errors and run_hd.errors[0]["type"] == "blocked"
    run_cr = ScrapeRun.objects.get(retailer=seeded["cr"])
    assert run_cr.status == ScrapeRun.Status.OK
    assert run_cr.triggered_by == ScrapeRun.TriggeredBy.SEARCH


# --- (7) Construrama sin search key → skipped y HD sigue -----------------------
@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY="")
@pytest.mark.django_db(transaction=True)
def test_construrama_sin_key_queda_skipped_y_hd_sigue(client, seeded, monkeypatch):
    """Sin CONSTRURAMA_ALGOLIA_SEARCH_KEY: skipped con motivo, sin romper a HD."""
    _patch_adapters(monkeypatch, hd_handler=_ok_handler("homedepot_varilla_batch.json"))

    body = _get_search(client, seeded["zona"], "cemento")

    por_slug = _statuses(body)
    assert por_slug["home-depot"]["status"] == "ok"
    assert por_slug["home-depot"]["items_found"] == 4
    assert por_slug["construrama"]["status"] == "skipped"
    assert "CONSTRURAMA_ALGOLIA_SEARCH_KEY" in por_slug["construrama"]["detail"]

    # El skip NO abre corrida (ni gasta red): solo HD tiene ScrapeRun.
    assert ScrapeRun.objects.filter(retailer=seeded["cr"]).count() == 0
    run_hd = ScrapeRun.objects.get(retailer=seeded["hd"])
    assert run_hd.triggered_by == ScrapeRun.TriggeredBy.SEARCH
    assert run_hd.search_term == "cemento"


# --- (7b) scraper no activo → skipped (sin romper el resto) --------------------
@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY="")
@pytest.mark.django_db
def test_retailer_no_activo_queda_skipped(client, seeded):
    """HD pausado + CR sin key: ambos skipped con motivo; sin corridas ni hilos.

    Documenta la decisión de diseño: el gatillo SÍ se disparó (triggered=true)
    pero cada retailer reporta por qué no corrió; no se abre ningún ScrapeRun
    (y por eso el cooldown no aplica a los skips: no gastan red).
    """
    hd = seeded["hd"]
    hd.scraper_status = Retailer.ScraperStatus.PAUSED
    hd.save(update_fields=["scraper_status"])

    body = _get_search(client, seeded["zona"], "cemento")

    assert body["live"]["triggered"] is True
    por_slug = _statuses(body)
    assert por_slug["home-depot"]["status"] == "skipped"
    assert "paused" in por_slug["home-depot"]["detail"]
    assert por_slug["construrama"]["status"] == "skipped"
    assert ScrapeRun.objects.count() == 0


# --- (9) F035: las observaciones del vivo se ligan a su ScrapeRun --------------
@override_settings(CONSTRURAMA_ALGOLIA_SEARCH_KEY="")
@pytest.mark.django_db(transaction=True)
def test_observaciones_del_vivo_se_ligan_a_su_scrape_run(client, seeded, monkeypatch):
    """F035: cada PriceObservation ingestada por la corrida en vivo queda ligada a
    su ScrapeRun (triggered_by=search, search_term=q). CR sin key → solo HD corre."""
    _patch_adapters(monkeypatch, hd_handler=_ok_handler("homedepot_varilla_batch.json"))

    body = _get_search(client, seeded["zona"], "alambre")

    assert _statuses(body)["home-depot"]["status"] == "ok"
    run_hd = ScrapeRun.objects.get(retailer=seeded["hd"], triggered_by=ScrapeRun.TriggeredBy.SEARCH)
    assert run_hd.search_term == "alambre"
    # Las 4 observaciones del fixture quedaron ligadas a ESA corrida (ninguna suelta).
    observaciones = PriceObservation.objects.filter(scrape_run=run_hd)
    assert observaciones.count() == 4
    assert all(o.zone_id == seeded["zona"].id for o in observaciones)


# --- (8) presupuesto total: el retailer lento se reporta failed: timeout -------
@pytest.mark.django_db(transaction=True)
def test_presupuesto_agotado_reporta_timeout_sin_colgar(seeded, monkeypatch):
    """`correr_busqueda_en_vivo` responde al vencer el presupuesto (retailer lento)."""
    termino_evento = threading.Event()

    class AdapterLento:
        """Adapter falso cuyo fetch tarda más que el presupuesto (sin red)."""

        def fetch_products_with_prices(self, category, location, *, captured_at=None):
            termino_evento.wait(1.0)  # más que el presupuesto de 0.05 s
            return []

        def close(self) -> None:  # pragma: no cover - higiene
            pass

    monkeypatch.setattr(scraping_services, "build_live_adapter", lambda slug: AdapterLento())

    reporte = scraping_services.correr_busqueda_en_vivo(
        "cemento", seeded["zona"], [seeded["hd"]], timeout_seconds=0.05
    )

    assert len(reporte.outcomes) == 1
    outcome = reporte.outcomes[0]
    assert outcome.retailer_slug == "home-depot"
    assert outcome.status == "failed"
    assert "timeout" in outcome.detail
    # Libera al hilo rezagado y espera a que CIERRE su corrida ANTES del
    # teardown (el flush de transaction=True no debe cruzarse con escrituras).
    # Que la corrida quede en la DB pese al timeout ES el cache-through.
    termino_evento.set()
    cerradas = ScrapeRun.objects.filter(retailer=seeded["hd"], finished_at__isnull=False)
    limite = time.monotonic() + 2.0
    while time.monotonic() < limite and not cerradas.exists():
        time.sleep(0.01)
    assert cerradas.exists()
