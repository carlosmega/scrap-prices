"""Tests del management command `scrape` (F027). 100% OFFLINE (sin red real).

El HTTP se mockea con `httpx.MockTransport` devolviendo el golden fixture de HD
(F025); ningún test pega a una URL real. Un reloj falso hace el rate-limit
instantáneo. El adapter sobre el transporte mockeado se inyecta parcheando
`build_adapter` del módulo del comando (el mismo seam que usa la corrida real).

Cubre los criterios de aceptación de F027:
- `--dry-run`: imprime productos y NO cambia conteos de PriceObservation/RetailerProduct.
- sin `--dry-run`: crea PriceObservation + ScrapeRun ok.
- retailer/zona inexistente o sin RetailerLocation primaria => CommandError.
- slug sin adapter (construrama) => mensaje "no disponible aún", sin stacktrace.
- MockTransport 429 => reporta bloqueo y sale con error (CommandError), sin evadir.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import httpx
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping.client import PoliteClient
from apps.scraping.homedepot import HomeDepotAdapter
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


def _make_adapter(handler) -> HomeDepotAdapter:
    """HomeDepotAdapter con PoliteClient sobre MockTransport (sin red)."""
    clock = FakeClock()
    client = PoliteClient(
        user_agent="ConstruScan/test (+contacto)",
        min_delay_seconds=7.0,
        timeout_seconds=5.0,
        max_concurrency_per_domain=1,
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    return HomeDepotAdapter(client=client)


def _ok_handler(fixture: str, calls: dict | None = None):
    """Sirve un fixture con status 200 y (opcional) registra cuántas peticiones."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls["n"] = calls.get("n", 0) + 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            text=_fixture_text(fixture),
        )

    return handler


def _patch_adapter(monkeypatch, handler) -> dict:
    """Parchea `build_adapter` para devolver el adapter mockeado (sin red).

    Devuelve el dict `calls` que el handler va llenando, para asertar el conteo
    de peticiones (guardrail stop-if-blocked).
    """
    calls: dict = {}
    adapter = _make_adapter(_handler_con_calls(handler, calls))
    monkeypatch.setattr(scrape_cmd, "build_adapter", lambda slug: adapter)
    return calls


def _handler_con_calls(handler, calls: dict):
    def wrapped(request: httpx.Request) -> httpx.Response:
        calls["n"] = calls.get("n", 0) + 1
        return handler(request)

    return wrapped


# --- Fixtures de dominio ----------------------------------------------------
@pytest.fixture
def hd_setup(db):
    """Retailer HD + tienda primaria + zona + ZoneLocationMap(is_primary)."""
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
    zone = Zone.objects.create(name="Monterrey Metro", slug="monterrey-metro", state="NL")
    ZoneLocationMap.objects.create(zone=zone, retailer_location=location, is_primary=True)
    return {"retailer": retailer, "location": location, "zone": zone}


# --- (1) --dry-run: imprime y NO escribe ------------------------------------
@pytest.mark.django_db
def test_dry_run_imprime_y_no_escribe(hd_setup, monkeypatch):
    """--dry-run hace fetch real e imprime los productos sin crear filas."""
    _patch_adapter(monkeypatch, _ok_handler("homedepot_varilla_batch.json"))
    out = StringIO()

    obs_antes = PriceObservation.objects.count()
    rp_antes = RetailerProduct.objects.count()
    runs_antes = ScrapeRun.objects.count()

    call_command(
        "scrape",
        retailer="home-depot",
        zone="monterrey-metro",
        category="varilla",
        dry_run=True,
        stdout=out,
    )

    salida = out.getvalue()
    assert "DRY-RUN" in salida
    assert "Productos que se traerían: 4" in salida
    # Se imprime al menos un SKU/precio del fixture.
    assert "462843" in salida
    assert "MXN" in salida

    # NINGUNA escritura: conteos sin cambios (0 nuevas).
    assert PriceObservation.objects.count() == obs_antes
    assert RetailerProduct.objects.count() == rp_antes
    assert ScrapeRun.objects.count() == runs_antes


# --- (2) sin --dry-run: ingiere (PriceObservation + ScrapeRun ok) -----------
@pytest.mark.django_db
def test_corrida_real_crea_observations_y_run_ok(hd_setup, monkeypatch):
    """Sin --dry-run crea PriceObservation + RetailerProduct y ScrapeRun ok."""
    _patch_adapter(monkeypatch, _ok_handler("homedepot_varilla_batch.json"))
    out = StringIO()

    call_command(
        "scrape",
        retailer="home-depot",
        zone="monterrey-metro",
        category="varilla",
        stdout=out,
    )

    salida = out.getvalue()
    assert "Corrida ok" in salida
    assert "4 items" in salida

    assert PriceObservation.objects.filter(zone=hd_setup["zone"]).count() == 4
    assert RetailerProduct.objects.filter(retailer=hd_setup["retailer"]).count() == 4
    run = ScrapeRun.objects.get(retailer=hd_setup["retailer"])
    assert run.status == ScrapeRun.Status.OK
    assert run.items_found == 4


# --- (3) retailer inexistente => CommandError -------------------------------
@pytest.mark.django_db
def test_retailer_inexistente_command_error(hd_setup):
    """Retailer con slug desconocido => CommandError claro."""
    with pytest.raises(CommandError, match="No existe un Retailer"):
        call_command("scrape", retailer="no-existe", zone="monterrey-metro")


# --- (3b) zona inexistente => CommandError ----------------------------------
@pytest.mark.django_db
def test_zona_inexistente_command_error(hd_setup):
    """Zona con slug desconocido => CommandError claro."""
    with pytest.raises(CommandError, match="No existe una Zone"):
        call_command("scrape", retailer="home-depot", zone="no-existe")


# --- (3c) sin RetailerLocation primaria => CommandError ---------------------
@pytest.mark.django_db
def test_sin_location_primaria_command_error(db):
    """Retailer y zona existen, pero no hay ZoneLocationMap is_primary => error."""
    retailer = Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )
    Zone.objects.create(name="Monterrey Metro", slug="monterrey-metro", state="NL")
    # Ojo: no se crea ningún ZoneLocationMap is_primary para ese retailer.
    with pytest.raises(CommandError, match="RetailerLocation primaria"):
        call_command("scrape", retailer=retailer.slug, zone="monterrey-metro")


# --- (4) slug sin adapter (retailer futuro) => aviso, sin stacktrace ---------
@pytest.mark.django_db
def test_slug_sin_adapter_avisa_sin_reventar(db):
    """Un retailer sembrado pero SIN adapter (aún) => 'no disponible aún', sin reventar.

    Home Depot (F025) y Construrama (F026) ya tienen adapter; este caso usa un
    retailer futuro/hipotético (sin entrada en INGEST_REGISTRY) para ejercer la
    rama de 'adapter no disponible aún' sin stacktrace.
    """
    retailer = Retailer.objects.create(
        name="Ferretería Futura",
        slug="ferre-futura",
        base_url="https://www.ferre-futura.example",
        pricing_model=Retailer.PricingModel.DISTRIBUTOR_SUBPATH,
    )
    location = RetailerLocation.objects.create(
        retailer=retailer,
        external_id="sucursal-mty",
        name="Ferretería Futura MTY",
        city="Monterrey",
        state="NL",
    )
    zone = Zone.objects.create(name="Monterrey Metro", slug="monterrey-metro", state="NL")
    ZoneLocationMap.objects.create(zone=zone, retailer_location=location, is_primary=True)
    out = StringIO()

    # No revienta (no levanta excepción) y avisa.
    call_command("scrape", retailer="ferre-futura", zone="monterrey-metro", stdout=out)

    assert "no disponible aún" in out.getvalue()
    # No ejecutó ninguna corrida.
    assert ScrapeRun.objects.count() == 0
    assert PriceObservation.objects.count() == 0


# --- (5) 429 => reporta bloqueo y sale con error, sin evadir -----------------
@pytest.mark.django_db
def test_429_reporta_bloqueo_y_sale_con_error_sin_evadir(hd_setup, monkeypatch):
    """Un 429 detiene la corrida: CommandError, una sola petición (sin reintento)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="too many requests")

    calls = _patch_adapter(monkeypatch, handler)

    with pytest.raises(CommandError, match="stop-if-blocked"):
        call_command(
            "scrape",
            retailer="home-depot",
            zone="monterrey-metro",
            category="varilla",
        )

    # Guardrail: NO se reintenta para evadir (una sola petición).
    assert calls["n"] == 1


# --- (5b) 429 en --dry-run => también reporta bloqueo y sale con error -------
@pytest.mark.django_db
def test_429_en_dry_run_tambien_reporta_bloqueo(hd_setup, monkeypatch):
    """El stop-if-blocked aplica igual en --dry-run; sin escribir nada."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="too many requests")

    calls = _patch_adapter(monkeypatch, handler)

    with pytest.raises(CommandError, match="stop-if-blocked"):
        call_command(
            "scrape",
            retailer="home-depot",
            zone="monterrey-metro",
            dry_run=True,
        )

    assert calls["n"] == 1
    assert PriceObservation.objects.count() == 0
    assert ScrapeRun.objects.count() == 0
