"""Fixtures globales de la suite (F033): candado anti-red del scrape en vivo.

La búsqueda puede disparar un scrape EN VIVO (live-on-miss). En tests eso JAMÁS
debe pegar a la red: este autouse parchea la fábrica de adapters en vivo para
que reviente con un mensaje claro si algún test dispara el vivo sin haber
inyectado su propio adapter mockeado (los tests de F033 la re-parchean con
adapters sobre `httpx.MockTransport`). El resto del scraping ya es offline por
diseño (adapters/clients inyectados explícitamente en sus tests).
"""

import pytest


@pytest.fixture(autouse=True)
def _candado_scrape_en_vivo(monkeypatch):
    """Ningún test construye un adapter en vivo REAL (candado estructural)."""
    from apps.scraping import services as scraping_services

    def _explota(slug: str):
        raise AssertionError(
            f"Un test disparó la búsqueda EN VIVO del retailer '{slug}' sin adapter "
            "mockeado. Usa live=never, siembra datos frescos o parchea "
            "apps.scraping.services.build_live_adapter con un adapter sobre "
            "httpx.MockTransport."
        )

    monkeypatch.setattr(scraping_services, "build_live_adapter", _explota)
