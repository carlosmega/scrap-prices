"""Lógica de orquestación de corridas de scraping (F024/F025/F033). Sin HTTP, sin routers.

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

F033 añade la **búsqueda en vivo bajo demanda** (`correr_busqueda_en_vivo`):
ambos retailers concurrentes con presupuesto total, cada uno con su `ScrapeRun`
(`search_term` + `triggered_by="search"`); el fallo/bloqueo/omisión de uno NO
impide al otro. Los guardrails §2.3 no cambian: el vivo usa los MISMOS adapters
y el MISMO `PoliteClient` (UA honesto, rate-limit, stop-if-blocked sin evasión).
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import connections
from django.utils import timezone

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices.models import PriceObservation, ScrapeRun
from apps.scraping.base import BaseRetailerAdapter
from apps.scraping.construrama import ConstruramaAdapter
from apps.scraping.exceptions import RetailerBlockedError, ScrapeError
from apps.scraping.homedepot import HOMEDEPOT_BASE_URL, HomeDepotAdapter
from apps.scraping.parsers import (
    construrama_brand,
    construrama_sale_unit,
    construrama_unit_raw,
    construrama_url,
    homedepot_href,
    homedepot_sale_unit,
    homedepot_unit,
)


def abrir_corrida(
    retailer: Retailer,
    zone: Zone | None = None,
    *,
    search_term: str | None = None,
    triggered_by: str = ScrapeRun.TriggeredBy.COMMAND,
) -> ScrapeRun:
    """Abre una corrida de scraping: registra el inicio en `ScrapeRun`.

    Devuelve el `ScrapeRun` con `started_at` fijado y `status` provisional
    `failed`: si la corrida muere a mitad sin cerrarse, queda registrada como
    fallida (default seguro). `cerrar_corrida` la lleva a su estado final.

    F033: `search_term`/`triggered_by` auditan el ORIGEN de la corrida. El
    comando `scrape` usa los defaults (sin término, `triggered_by="command"`);
    la búsqueda en vivo pasa el término normalizado y `triggered_by="search"`
    (el cooldown del gatillo se calcula sobre estos campos).
    """
    return ScrapeRun.objects.create(
        retailer=retailer,
        zone=zone,
        started_at=timezone.now(),
        status=ScrapeRun.Status.FAILED,
        search_term=search_term,
        triggered_by=triggered_by,
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


def _homedepot_product_url(raw_price) -> str:
    """URL ABSOLUTA de la ficha (PDP) de Home Depot para un `RawPrice` (F034).

    HD trae el slug REAL del PDP en `content["seo"]["href"]` (relativo); se le
    antepone el host → URL absoluta que responde 200. Si falta/mal formado, se
    cae al buscador `HOMEDEPOT_BASE_URL/search?q={sku}` (verificado 200 y el
    buscador halla el producto por su SKU). NUNCA se usa `/p/{sku}`: ese patrón
    no existe en HD y devuelve 404 (el bug que corrige F034).
    """
    href = homedepot_href(raw_price.raw_payload)
    if href:
        return f"{HOMEDEPOT_BASE_URL}{href}"
    return f"{HOMEDEPOT_BASE_URL}/search?q={raw_price.sku}"


def _get_or_create_retailer_product(retailer: Retailer, raw_price) -> RetailerProduct:
    """`get_or_create` de `RetailerProduct` por (retailer, external_sku).

    El matching al `CanonicalProduct` NO se hace aquí: queda `unmatched` (default
    del modelo) para curarse a mano en Admin (PRD D1). Idempotente: dos corridas
    sobre el mismo SKU no duplican la fila (clave única retailer+external_sku).

    F034: la url se deriva del `seo.href` real de HD (fallback a `/search?q={sku}`),
    nunca del `/p/{sku}` roto. En re-ingestión se REFRESCA la url de una fila ya
    existente (get_or_create solo aplica `defaults` al crear): así una búsqueda o
    scrape posterior corrige en sitio las filas viejas con la URL mala (404), sin
    necesitar una data-migration one-off.
    """
    unit_raw = homedepot_unit(raw_price.raw_payload)
    url = _homedepot_product_url(raw_price)
    rp, created = RetailerProduct.objects.get_or_create(
        retailer=retailer,
        external_sku=raw_price.sku,
        defaults={
            "raw_name": raw_price.raw_name,
            "url": url,
            "unit_raw": unit_raw,
            # F031: unidad estructurada derivada del código UN/ECE de HD; "" si
            # desconocida (se cura en Admin, como el matching a canónico).
            "sale_unit": homedepot_sale_unit(unit_raw),
        },
    )
    if not created and rp.url != url:
        # Refresh de la url en re-ingestión: corrige la fila vieja con `/p/{sku}`.
        rp.url = url
        rp.save(update_fields=["url", "updated_at"])
    return rp


def _run_ingestion(
    zone: Zone,
    location: RetailerLocation,
    category: str,
    adapter,
    get_or_create_rp,
    *,
    captured_at: datetime | None = None,
    search_term: str | None = None,
    triggered_by: str = ScrapeRun.TriggeredBy.COMMAND,
) -> ScrapeRun:
    """Núcleo común de una corrida (F025/F026): precios → `PriceObservation`.

    Flujo (idéntico para cualquier retailer; solo cambia el `get_or_create_rp`):
    1. Abre un `ScrapeRun` (queda `failed` hasta cerrarse: default seguro).
    2. Obtiene los `RawPrice` de la categoría en UNA llamada (cortesía).
    3. Por cada SKU: `get_or_create` de `RetailerProduct` (matching manual en
       Admin) + una `PriceObservation` (source=xhr, captured_at, raw_payload).
    4. Cierra el `ScrapeRun` (ok/partial/failed, items_found, errors).

    F033: `search_term`/`triggered_by` viajan al `ScrapeRun` para auditar si la
    corrida nació del comando (defaults) o de la búsqueda en vivo.

    Guardrail §2.3: si el retailer bloquea (403/429/challenge), el adapter
    propaga `RetailerBlockedError`; aquí NO se reintenta para evadir: se audita,
    la corrida cierra `failed` y se relanza la excepción.
    """
    retailer = location.retailer
    captured_at = captured_at or timezone.now()

    run = abrir_corrida(retailer, zone, search_term=search_term, triggered_by=triggered_by)
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
    search_term: str | None = None,
    triggered_by: str = ScrapeRun.TriggeredBy.COMMAND,
) -> ScrapeRun:
    """Corrida de scraping de Home Depot: precios → `PriceObservation` (F025).

    Delega el flujo común en `_run_ingestion` con el `get_or_create_rp` de HD
    (url del `seo.href` real con fallback a `/search?q={sku}` — F034; unidad
    UN/ECE). Ver `_run_ingestion` para el detalle y el guardrail stop-if-blocked.
    `search_term`/`triggered_by` auditan el origen de la corrida (F033); los
    defaults preservan el comportamiento del comando.
    """
    adapter = adapter or HomeDepotAdapter()
    return _run_ingestion(
        zone,
        location,
        category,
        adapter,
        _get_or_create_retailer_product,
        captured_at=captured_at,
        search_term=search_term,
        triggered_by=triggered_by,
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
    search_term: str | None = None,
    triggered_by: str = ScrapeRun.TriggeredBy.COMMAND,
) -> ScrapeRun:
    """Corrida de scraping de Construrama: precios Algolia → `PriceObservation`.

    Delega el flujo común en `_run_ingestion` con el `get_or_create_rp` de
    Construrama (url/brand/sale_unit del hit). Ver `_run_ingestion` para el
    detalle y el guardrail stop-if-blocked. `search_term`/`triggered_by`
    auditan el origen de la corrida (F033); defaults = comando.
    """
    adapter = adapter or ConstruramaAdapter()
    return _run_ingestion(
        zone,
        location,
        category,
        adapter,
        _get_or_create_retailer_product_construrama,
        captured_at=captured_at,
        search_term=search_term,
        triggered_by=triggered_by,
    )


# --- Resolución de tienda primaria (extraído del comando `scrape`, F033) ----


def resolver_primary_location(retailer: Retailer, zone: Zone) -> RetailerLocation | None:
    """La `RetailerLocation` primaria del retailer que sirve la zona, o None.

    La sirve el `ZoneLocationMap` con `is_primary=True` cuya ubicación es del
    retailer pedido. Extraído del comando `scrape` (F027) para que comando y
    búsqueda en vivo (F033) compartan la resolución; el llamador decide qué
    hacer con None (el comando lo traduce a `CommandError`, la búsqueda a
    `skipped`).
    """
    mapping = (
        ZoneLocationMap.objects.select_related("retailer_location__retailer")
        .filter(
            zone=zone,
            is_primary=True,
            retailer_location__retailer=retailer,
        )
        .first()
    )
    return mapping.retailer_location if mapping is not None else None


# --- Búsqueda en vivo bajo demanda (F033) -----------------------------------
# Orquesta la corrida en vivo de la búsqueda (live-on-miss): ambos retailers
# concurrentes con presupuesto total; el fallo/bloqueo/omisión de uno NO impide
# al otro. La decisión de CUÁNDO disparar (TTL/cooldown/live=never) vive en
# `apps.catalog.services` (dominio de la búsqueda); aquí vive el CÓMO correr.

# Retailers con adapter de búsqueda en vivo, en el orden de reporte estable.
LIVE_RETAILER_SLUGS: tuple[str, ...] = ("home-depot", "construrama")

# Statuses del reporte por retailer (contrato F033: LiveRetailerStatusOut).
LIVE_STATUS_OK = "ok"
LIVE_STATUS_FAILED = "failed"
LIVE_STATUS_BLOCKED = "blocked"
LIVE_STATUS_SKIPPED = "skipped"

# Tope de longitud del `detail` reportado: motivo breve, jamás un stacktrace.
_DETAIL_MAX = 200


@dataclass(frozen=True, slots=True)
class LiveRetailerOutcome:
    """Resultado de UN retailer en la corrida en vivo (dominio, no schema)."""

    retailer_slug: str
    status: str
    items_found: int = 0
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class LiveRunReport:
    """Reporte agregado de la corrida en vivo: duración + un outcome por retailer."""

    duration_ms: int
    outcomes: list[LiveRetailerOutcome]


def build_live_adapter(slug: str) -> BaseRetailerAdapter:
    """Crea el adapter real de un retailer para la búsqueda en vivo.

    Seam de testeo (mismo patrón que `build_adapter` del comando `scrape`): los
    tests lo parchean para inyectar adapters sobre `httpx.MockTransport` — el
    conftest raíz lo parchea a "explota" para que NINGÚN test pegue a la red
    por accidente. Solo se llama para slugs de `LIVE_RETAILER_SLUGS`.
    """
    if slug == "home-depot":
        return HomeDepotAdapter()
    if slug == "construrama":
        return ConstruramaAdapter()
    raise ScrapeError(f"No hay adapter de búsqueda en vivo para el retailer '{slug}'.")


# Función de ingestión por slug (reusa las corridas F025/F026 tal cual).
_LIVE_INGEST = {
    "home-depot": ingest_homedepot,
    "construrama": ingest_construrama,
}


def _skip_para(retailer: Retailer, zone: Zone) -> tuple[RetailerLocation | None, str | None]:
    """Decide si un retailer se OMITE de la corrida en vivo (y por qué).

    Devuelve `(location, None)` si es ejecutable, o `(None, motivo)` si se
    omite: scraper no activo, sin credencial (Construrama sin search key) o sin
    tienda primaria que sirva la zona. Omitir NUNCA rompe al resto.
    """
    if retailer.scraper_status != Retailer.ScraperStatus.ACTIVE:
        return None, f"scraper del retailer en estado '{retailer.scraper_status}' (no activo)"
    if retailer.slug == "construrama" and not settings.CONSTRURAMA_ALGOLIA_SEARCH_KEY:
        return None, (
            "falta CONSTRURAMA_ALGOLIA_SEARCH_KEY en el entorno: "
            "sin search key no se consulta Algolia"
        )
    location = resolver_primary_location(retailer, zone)
    if location is None:
        return None, "sin tienda primaria del retailer que sirva la zona"
    return location, None


def _correr_retailer(
    retailer: Retailer,
    location: RetailerLocation,
    zone: Zone,
    termino: str,
) -> LiveRetailerOutcome:
    """Corre la ingestión en vivo de UN retailer y traduce el resultado.

    NUNCA lanza: cualquier excepción se traduce a un outcome (`blocked`/`failed`)
    con motivo breve (sin stacktrace) para que un retailer caído no tumbe al
    otro. Corre en un hilo del pool: cierra sus conexiones de DB al terminar.
    """
    adapter: BaseRetailerAdapter | None = None
    try:
        adapter = build_live_adapter(retailer.slug)
        ingest = _LIVE_INGEST[retailer.slug]
        run = ingest(
            zone,
            location,
            termino,
            adapter=adapter,
            search_term=termino,
            triggered_by=ScrapeRun.TriggeredBy.SEARCH,
        )
        # Corrida sin excepción = consulta exitosa; con 0 hallazgos sigue siendo
        # "ok" para el usuario (el ScrapeRun interno queda failed por la regla
        # de F024: sin items no hay corrida útil — auditoría, no UX).
        return LiveRetailerOutcome(
            retailer_slug=retailer.slug,
            status=LIVE_STATUS_OK,
            items_found=run.items_found,
        )
    except RetailerBlockedError as exc:
        # stop-if-blocked (§2.3): se reporta y NO se reintenta ni se evade.
        status_http = f" (HTTP {exc.status_code})" if exc.status_code else ""
        return LiveRetailerOutcome(
            retailer_slug=retailer.slug,
            status=LIVE_STATUS_BLOCKED,
            detail=f"el retailer bloqueó la corrida{status_http}; stop-if-blocked, sin evasión",
        )
    except ScrapeError as exc:
        return LiveRetailerOutcome(
            retailer_slug=retailer.slug,
            status=LIVE_STATUS_FAILED,
            detail=str(exc)[:_DETAIL_MAX],
        )
    except Exception as exc:  # noqa: BLE001 — un retailer caído no tumba al otro
        return LiveRetailerOutcome(
            retailer_slug=retailer.slug,
            status=LIVE_STATUS_FAILED,
            detail=f"{type(exc).__name__}: {exc}"[:_DETAIL_MAX],
        )
    finally:
        if adapter is not None:
            cerrar = getattr(adapter, "close", None)
            if callable(cerrar):
                try:
                    cerrar()
                except Exception:  # noqa: BLE001 — cerrar no debe romper el reporte
                    pass
        # Este hilo abrió su propia conexión de DB: se cierra aquí (higiene;
        # `connections` es thread-local, no toca la conexión del request).
        connections.close_all()


def correr_busqueda_en_vivo(
    termino: str,
    zone: Zone,
    retailers: list[Retailer],
    *,
    timeout_seconds: float | None = None,
) -> LiveRunReport:
    """Corre la búsqueda EN VIVO en los retailers dados, concurrente y acotada.

    - Cada retailer ejecutable corre en un hilo propio (`ThreadPoolExecutor`);
      el resultado de uno no depende del otro (`ok`/`failed`/`blocked`).
    - Los no ejecutables (scraper no activo, sin credencial, sin tienda en la
      zona) se reportan `skipped` con motivo, sin gastar red ni `ScrapeRun`.
    - Presupuesto TOTAL `SEARCH_LIVE_TIMEOUT_SECONDS`: al vencer se responde
      con lo que haya y el retailer lento se reporta `failed: timeout`. Nota:
      se usa `concurrent.futures.wait(timeout=...)` (no `asyncio.run(gather)`)
      porque `asyncio.run` espera a los hilos abandonados al cerrar el loop y
      el presupuesto no se cumpliría; el hilo rezagado termina solo y su
      ingestión igual queda en la DB (cache-through).

    Los guardrails §2.3 viven intactos en `PoliteClient`/adapters (UA honesto,
    rate-limit, stop-if-blocked): el vivo no los relaja.
    """
    presupuesto = (
        settings.SEARCH_LIVE_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    )
    inicio = time.monotonic()

    outcomes_por_slug: dict[str, LiveRetailerOutcome] = {}
    ejecutables: list[tuple[Retailer, RetailerLocation]] = []
    for retailer in retailers:
        location, motivo_skip = _skip_para(retailer, zone)
        if motivo_skip is not None:
            outcomes_por_slug[retailer.slug] = LiveRetailerOutcome(
                retailer_slug=retailer.slug,
                status=LIVE_STATUS_SKIPPED,
                detail=motivo_skip,
            )
        else:
            ejecutables.append((retailer, location))

    if ejecutables:
        pool = ThreadPoolExecutor(max_workers=len(ejecutables), thread_name_prefix="live-search")
        try:
            futuros = [
                (retailer, pool.submit(_correr_retailer, retailer, location, zone, termino))
                for retailer, location in ejecutables
            ]
            done, _pendientes = futures_wait([f for _, f in futuros], timeout=presupuesto)
            for retailer, futuro in futuros:
                if futuro in done:
                    outcomes_por_slug[retailer.slug] = futuro.result()
                else:
                    outcomes_por_slug[retailer.slug] = LiveRetailerOutcome(
                        retailer_slug=retailer.slug,
                        status=LIVE_STATUS_FAILED,
                        detail=f"timeout: superó el presupuesto de {presupuesto:g}s",
                    )
        finally:
            # No se espera a los rezagados: terminan solos y su ingestión queda
            # en la DB (cache-through). cancel_futures=False a propósito.
            pool.shutdown(wait=False, cancel_futures=False)

    duration_ms = int((time.monotonic() - inicio) * 1000)
    return LiveRunReport(
        duration_ms=duration_ms,
        outcomes=[outcomes_por_slug[r.slug] for r in retailers],
    )
