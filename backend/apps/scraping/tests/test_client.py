"""Tests del cliente HTTP respetuoso (F024) — guardrails §2.3 verificables.

100% OFFLINE: ninguna petición pega a una URL real. Se usa `httpx.MockTransport`
para servir respuestas guionizadas y un reloj/sleep FALSOS para verificar el
rate-limit y hacer los reintentos instantáneos. Cada test fallaría sin la
implementación de `PoliteClient`.

Cubre los criterios de aceptación de la spec:
1. el rate-limiter espera el delay mínimo entre peticiones al mismo dominio;
2. tenacity reintenta un 5xx/timeout transitorio y luego tiene éxito;
3. ante 403/429/challenge se lanza RetailerBlockedError y NO se reintenta/evade;
4. el User-Agent por defecto es el honesto.
"""

from __future__ import annotations

import httpx
import pytest

from apps.scraping.client import PoliteClient
from apps.scraping.exceptions import RetailerBlockedError, TransientScrapeError


class FakeClock:
    """Reloj monotónico + sleep falsos: avanzan tiempo sin esperar de verdad."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        # Registrar y avanzar el reloj: ningún test espera en tiempo real.
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(handler, clock: FakeClock | None = None, **overrides) -> PoliteClient:
    """PoliteClient con transporte mockeado y reloj falso (sin red, sin esperas)."""
    clock = clock or FakeClock()
    transport = httpx.MockTransport(handler)
    defaults = dict(
        user_agent="ConstruScan/test (+contacto)",
        min_delay_seconds=7.0,
        timeout_seconds=5.0,
        max_concurrency_per_domain=1,
        max_retries=3,
        transport=transport,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    defaults.update(overrides)
    return PoliteClient(**defaults)


# --- (4) UA honesto ---------------------------------------------------------
def test_user_agent_por_defecto_es_honesto():
    """El UA default identifica a ConstruScan (no imita a un navegador real)."""
    # Sin override: toma el de settings, que es el honesto.
    client = PoliteClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    try:
        ua = client.user_agent
        assert "ConstruScan" in ua
        # Guardrail: jamás un UA que se haga pasar por Chrome/Safari/Firefox.
        lowered = ua.lower()
        for navegador in ("mozilla", "chrome", "safari", "firefox", "applewebkit"):
            assert navegador not in lowered
    finally:
        client.close()


def test_user_agent_se_envia_en_la_peticion():
    """El header User-Agent honesto viaja en cada petición."""
    sent_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent_headers["user-agent"] = request.headers.get("user-agent")
        return httpx.Response(200, text="ok")

    with make_client(handler, user_agent="ConstruScan/0.1 (+contacto)") as client:
        client.get("https://retailer.example/p/1")

    assert sent_headers["user-agent"] == "ConstruScan/0.1 (+contacto)"


# --- (1) rate-limit por dominio --------------------------------------------
def test_rate_limit_espera_el_delay_entre_peticiones_mismo_dominio():
    """Entre 2 peticiones al MISMO dominio se duerme >= delay mínimo."""
    clock = FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    with make_client(handler, clock=clock, min_delay_seconds=7.0) as client:
        client.get("https://retailer.example/a")
        # La primera no espera (no hay petición previa al dominio).
        assert clock.sleeps == []
        client.get("https://retailer.example/b")

    # La segunda esperó exactamente el delay mínimo.
    assert clock.sleeps == [7.0]


def test_rate_limit_no_mezcla_dominios_distintos():
    """Dominios distintos no comparten el rate-limit: pegar a otro no espera."""
    clock = FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    with make_client(handler, clock=clock, min_delay_seconds=7.0) as client:
        client.get("https://uno.example/a")
        client.get("https://dos.example/a")

    # Ninguna esperó: son dominios diferentes.
    assert clock.sleeps == []


# --- (2) reintentos de transitorios ----------------------------------------
def test_reintenta_5xx_y_luego_tiene_exito():
    """Un 5xx transitorio se reintenta con backoff y la 2a vez tiene éxito."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="service unavailable")
        return httpx.Response(200, text="ok")

    with make_client(handler, clock=clock, max_retries=3) as client:
        response = client.get("https://retailer.example/p")

    assert response.status_code == 200
    assert calls["n"] == 2  # falló una vez, reintentó, tuvo éxito


def test_reintenta_timeout_y_luego_tiene_exito():
    """Un timeout (transitorio de red) se reintenta y luego tiene éxito."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectTimeout("boom", request=request)
        return httpx.Response(200, text="ok")

    with make_client(handler, clock=clock, max_retries=3) as client:
        response = client.get("https://retailer.example/p")

    assert response.status_code == 200
    assert calls["n"] == 2


def test_5xx_persistente_agota_reintentos_y_lanza_transient():
    """Si el 5xx no cede, se agotan los reintentos y se lanza TransientScrapeError."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, text="err")

    with make_client(handler, clock=clock, max_retries=3) as client:
        with pytest.raises(TransientScrapeError):
            client.get("https://retailer.example/p")

    # Reintentó exactamente max_retries veces (no infinito).
    assert calls["n"] == 3


# --- (3) stop-if-blocked (NO evasión) --------------------------------------
@pytest.mark.parametrize("status", [403, 429])
def test_403_429_lanza_blocked_y_no_reintenta(status):
    """Ante 403/429 se lanza RetailerBlockedError y NO se reintenta (stop)."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, text="blocked")

    with make_client(handler, clock=clock, max_retries=3) as client:
        with pytest.raises(RetailerBlockedError) as exc:
            client.get("https://retailer.example/p")

    assert exc.value.status_code == status
    # Clave del guardrail: UNA sola petición. No se reintenta para forzar.
    assert calls["n"] == 1


def test_challenge_captcha_lanza_blocked_y_no_reintenta():
    """Un challenge/captcha (cuerpo HTML) se trata como bloqueo: detente."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<html><body>Please complete the CAPTCHA to continue</body></html>",
        )

    with make_client(handler, clock=clock, max_retries=3) as client:
        with pytest.raises(RetailerBlockedError):
            client.get("https://retailer.example/p")

    assert calls["n"] == 1  # no se reintenta ni se intenta resolver el captcha


def test_blocked_no_se_reintenta_aunque_max_retries_sea_alto():
    """Aunque max_retries sea grande, un bloqueo nunca se reintenta (no evasión)."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text="too many requests")

    with make_client(handler, clock=clock, max_retries=10) as client:
        with pytest.raises(RetailerBlockedError):
            client.get("https://retailer.example/p")

    assert calls["n"] == 1


# --- 4xx no-bloqueo: error legítimo, no se reintenta ------------------------
def test_404_no_se_reintenta_y_se_devuelve():
    """Un 404 (no es bloqueo) no se reintenta: se devuelve para que el adapter lo maneje."""
    clock = FakeClock()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, text="not found")

    with make_client(handler, clock=clock, max_retries=3) as client:
        response = client.get("https://retailer.example/p")

    assert response.status_code == 404
    assert calls["n"] == 1
