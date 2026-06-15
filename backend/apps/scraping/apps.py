"""Configuración de la app scraping."""

from django.apps import AppConfig


class ScrapingConfig(AppConfig):
    """Infraestructura común de scraping: adapters, cliente HTTP respetuoso.

    No define modelos propios: reusa `ScrapeRun`/`PriceObservation` de
    `apps.prices` (F008). Aquí viven la interfaz de adapters y los guardrails
    éticos cableados en código (PRD §2.3).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scraping"
