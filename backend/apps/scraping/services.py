"""Lógica de orquestación de corridas de scraping (F024/F025). Sin HTTP, sin routers.

Helpers para abrir/cerrar una corrida (`ScrapeRun`) reutilizando el modelo de
F008 (`apps.prices.models.ScrapeRun`) — NO se crea un modelo nuevo. La política
de cortesía/reintentos/stop-if-blocked vive en `apps.scraping.client`; aquí solo
se registra la auditoría de la corrida (D2 del PRD).

`ingest_homedepot` (F025) orquesta una corrida real: abre el `ScrapeRun`, obtiene
los precios vía el `HomeDepotAdapter`, hace `get_or_create` de `RetailerProduct`
(matching a canónico queda **unmatched/manual** en Admin) e inserta una
`PriceObservation` por SKU en la zona. Ante un bloqueo (403/429/challenge) el
adapter lanza `RetailerBlockedError`: NO se reintenta para evadir; la corrida
cierra `failed`/`partial` y se propaga el bloqueo.
"""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping.construrama import ConstruramaAdapter
from apps.scraping.exceptions import RetailerBlockedError, ScrapeError
from apps.scraping.homedepot import HOMEDEPOT_BASE_URL, HomeDepotAdapter
from apps.scraping.parsers import (
    construrama_brand,
    construrama_sale_unit,
    construrama_unit_raw,
    construrama_url,
    homedepot_sale_unit,
    homedepot_unit,
)


def abrir_corrida(retailer: Retailer, zone: Zone | None = None) -> ScrapeRun:
    """Abre una corrida de scraping: registra el inicio en `ScrapeRun`.

    Devuelve el `ScrapeRun` con `started_at` fijado y `status` provisional
    `failed`: si la corrida muere a mitad sin cerrarse, queda registrada como
    fallida (default seguro). `cerrar_corrida` la lleva a su estado final.
    """
    return ScrapeRun.objects.create(
        retailer=retailer,
        zone=zone,
        started_at=timezone.now(),
        status=ScrapeRun.Status.FAILED,
    )


def cerrar_corrida(
    run: ScrapeRun,
    *,
    items_found: int = 0,
    errors: list | None = None,
) -> ScrapeRun:
    """Cierra una corrida y deriva su `status` de los resultados.

    Regla de estado:
    - `ok`: hubo items y ningún error.
    - `partial`: hubo items y también errores.
    - `failed`: no hubo items (con o sin errores).
    """
    errors = errors or []
    if items_found <= 0:
        status = ScrapeRun.Status.FAILED
    elif errors:
        status = ScrapeRun.Status.PARTIAL
    else:
        status = ScrapeRun.Status.OK

    run.finished_at = timezone.now()
    run.status = status
    run.items_found = items_found
    run.errors = errors
    run.save(update_fields=["finished_at", "status", "items_found", "errors", "updated_at"])
    return run


# --- Ingestión Home Depot (F025) -------------------------------------------


def _get_or_create_retailer_product(retailer: Retailer, raw_price) -> RetailerProduct:
    """`get_or_create` de `RetailerProduct` por (retailer, external_sku).

    El matching al `CanonicalProduct` NO se hace aquí: queda `unmatched` (default
    del modelo) para curarse a mano en Admin (PRD D1). Idempotente: dos corridas
    sobre el mismo SKU no duplican la fila (clave única retailer+external_sku).
    """
    unit_raw = homedepot_unit(raw_price.raw_payload)
    rp, _created = RetailerProduct.objects.get_or_create(
        retailer=retailer,
        external_sku=raw_price.sku,
        defaults={
            "raw_name": raw_price.raw_name,
            "url": f"{HOMEDEPOT_BASE_URL}/p/{raw_price.sku}",
            "unit_raw": unit_raw,
            # F031: unidad estructurada derivada del código UN/ECE de HD; "" si
            # desconocida (se cura en Admin, como el matching a canónico).
            "sale_unit": homedepot_sale_unit(unit_raw),
        },
    )
    return rp


def _run_ingestion(
    zone: Zone,
    location: RetailerLocation,
    category: str,
    adapter,
    get_or_create_rp,
    *,
    captured_at: datetime | None = None,
) -> ScrapeRun:
    """Núcleo común de una corrida (F025/F026): precios → `PriceObservation`.

    Flujo (idéntico para cualquier retailer; solo cambia el `get_or_create_rp`):
    1. Abre un `ScrapeRun` (queda `failed` hasta cerrarse: default seguro).
    2. Obtiene los `RawPrice` de la categoría en UNA llamada (cortesía).
    3. Por cada SKU: `get_or_create` de `RetailerProduct` (matching manual en
       Admin) + una `PriceObservation` (source=xhr, captured_at, raw_payload).
    4. Cierra el `ScrapeRun` (ok/partial/failed, items_found, errors).

    Guardrail §2.3: si el retailer bloquea (403/429/challenge), el adapter
    propaga `RetailerBlockedError`; aquí NO se reintenta para evadir: se audita,
    la corrida cierra `failed` y se relanza la excepción.
    """
    retailer = location.retailer
    captured_at = captured_at or timezone.now()

    run = abrir_corrida(retailer, zone)
    errors: list[dict] = []
    items_found = 0

    try:
        precios = adapter.fetch_products_with_prices(category, location, captured_at=captured_at)
    except RetailerBlockedError as exc:
        # stop-if-blocked: NO se reintenta ni se evade. Se audita y se relanza.
        errors.append({"type": "blocked", "detail": str(exc), "status": exc.status_code})
        cerrar_corrida(run, items_found=0, errors=errors)
        raise
    except ScrapeError as exc:
        errors.append({"type": "scrape_error", "detail": str(exc)})
        cerrar_corrida(run, items_found=0, errors=errors)
        raise

    for precio in precios:
        try:
            rp = get_or_create_rp(retailer, precio)
            PriceObservation.objects.create(
                retailer_product=rp,
                zone=zone,
                retailer_location=location,
                price=precio.price,
                currency=precio.currency,
                is_available=precio.is_available,
                source=PriceObservation.Source.XHR,
                captured_at=precio.captured_at,
                raw_payload=precio.raw_payload,
            )
            items_found += 1
        except Exception as exc:  # noqa: BLE001 — un SKU malo no tumba la corrida
            errors.append({"sku": precio.sku, "error": str(exc)})

    return cerrar_corrida(run, items_found=items_found, errors=errors)


def ingest_homedepot(
    zone: Zone,
    location: RetailerLocation,
    category: str,
    *,
    adapter: HomeDepotAdapter | None = None,
    captured_at: datetime | None = None,
) -> ScrapeRun:
    """Corrida de scraping de Home Depot: precios → `PriceObservation` (F025).

    Delega el flujo común en `_run_ingestion` con el `get_or_create_rp` de HD
    (url `/p/{sku}`, unidad UN/ECE). Ver `_run_ingestion` para el detalle y el
    guardrail stop-if-blocked.
    """
    adapter = adapter or HomeDepotAdapter()
    return _run_ingestion(
        zone,
        location,
        category,
        adapter,
        _get_or_create_retailer_product,
        captured_at=captured_at,
    )


# --- Ingestión Construrama (F026) ------------------------------------------


def _get_or_create_retailer_product_construrama(retailer: Retailer, raw_price) -> RetailerProduct:
    """`get_or_create` de `RetailerProduct` de Construrama por (retailer, sku).

    Deriva del hit crudo (`raw_price.raw_payload`): url absoluta del PDP
    (`url_es_mx_string`), marca (`brand_string_mv` sin el token "brands"),
    unidad cruda y `sale_unit` (F031) inferida del nombre ("Kilogramos"→kg,
    "Pieza"→pieza). El matching al canónico queda `unmatched` (Admin). Idempotente
    por la clave única (retailer, external_sku).
    """
    hit = raw_price.raw_payload
    rp, _created = RetailerProduct.objects.get_or_create(
        retailer=retailer,
        external_sku=raw_price.sku,
        defaults={
            "raw_name": raw_price.raw_name,
            "url": construrama_url(hit),
            "brand": construrama_brand(hit),
            "unit_raw": construrama_unit_raw(raw_price.raw_name),
            "sale_unit": construrama_sale_unit(raw_price.raw_name),
        },
    )
    return rp


def ingest_construrama(
    zone: Zone,
    location: RetailerLocation,
    category: str,
    *,
    adapter: ConstruramaAdapter | None = None,
    captured_at: datetime | None = None,
) -> ScrapeRun:
    """Corrida de scraping de Construrama: precios Algolia → `PriceObservation`.

    Delega el flujo común en `_run_ingestion` con el `get_or_create_rp` de
    Construrama (url/brand/sale_unit del hit). Ver `_run_ingestion` para el
    detalle y el guardrail stop-if-blocked.
    """
    adapter = adapter or ConstruramaAdapter()
    return _run_ingestion(
        zone,
        location,
        category,
        adapter,
        _get_or_create_retailer_product_construrama,
        captured_at=captured_at,
    )
