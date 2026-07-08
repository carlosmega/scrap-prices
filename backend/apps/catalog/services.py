"""Lógica de negocio del catálogo (F015/F033): búsqueda y ensamblado de precios.

Sin HTTP, sin routers. La búsqueda consulta PRIMERO la DB propia: por cada
`CanonicalProduct` que matchea `q`, ensambla un `PriceByRetailerOut` por cada
`RetailerProduct` enlazado, con el precio más fresco en la zona (reutiliza
`apps.prices.services.ultima_observacion`). Tolera acentos en SQLite
normalizando (NFKD + strip de diacríticos) en memoria; Postgres FTS llega en M5.
El orden (`price`|`name`) también vive aquí.

F033 (pivote de producto 2026-07-07, reemplaza el §1 del PRD): si para `q`+zona
no hay datos frescos (TTL) y no aplica el cooldown, la búsqueda dispara la
corrida EN VIVO de ambos retailers (`apps.scraping.services`), ingesta lo
hallado (cache-through) y responde canónicos + crudos + info de la corrida.
El GATILLO (cuándo) vive aquí; el CÓMO correr vive en scraping.
"""

import unicodedata
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.catalog.models import CanonicalProduct, RetailerProduct
from apps.catalog.normalization import normaliza_precio
from apps.catalog.schemas import (
    CanonicalProductDetailOut,
    CanonicalProductRefOut,
    LiveRetailerStatusOut,
    LiveSearchInfoOut,
    PriceByRetailerOut,
    PriceHistoryPointOut,
    ProductDetailOut,
    RawRetailerResultOut,
    RetailerRefOut,
    SearchOut,
    SearchResultOut,
)
from apps.geo.models import Retailer, Zone
from apps.prices.models import PriceObservation, ScrapeRun
from apps.prices.services import ultima_observacion
from apps.scraping import services as scraping_services

# Tamaño por defecto del historial de precios en el detalle (PRD/F016: N=20).
_HISTORIAL_DEFAULT = 20

# Ordena los retailers-sin-precio al final cuando se ordena por precio.
_PRECIO_INFINITO = None  # marcador semántico; se traduce a +inf en la key

# F033: tope de resultados crudos por búsqueda (spec).
_RAW_RESULTS_MAX = 50

# F033: largo mínimo del término normalizado para considerar el vivo.
_TERMINO_MIN_VIVO = 3

# F033: el término que se persiste/consulta en ScrapeRun.search_term se trunca
# al max_length del campo para que cooldown y auditoría sean consistentes.
_TERMINO_MAX_CORRIDA = 200


def _normalizar(texto: str) -> str:
    """Minúsculas sin diacríticos (NFKD) para comparar tolerando acentos.

    'Varilla' y 'várilla' colapsan al mismo token; suficiente para el MVP en
    SQLite (Postgres adoptará unaccent/SearchVector en M5).
    """
    descompuesto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(ch for ch in descompuesto if not unicodedata.combining(ch))


def _ensamblar_precio(retailer_product, zone: Zone, mass_kg: Decimal | None) -> PriceByRetailerOut:
    """Arma el PriceByRetailerOut de un RetailerProduct con su precio más fresco.

    Sin observación en la zona → price/captured_at None, is_available False.

    F031: además del precio NATIVO, expone la unidad estructurada (`sale_unit`)
    y el precio NORMALIZADO (`price_per_piece`/`price_per_kg`), calculado con
    `normaliza_precio(precio_nativo, sale_unit, mass_kg)`. Cualquiera de los
    normalizados es None cuando no se puede convertir (sin precio, sin `mass_kg`
    o unidad desconocida).
    """
    obs = ultima_observacion(retailer_product, zone=zone)
    retailer = retailer_product.retailer
    precio = obs.price if obs is not None else None
    per_piece, per_kg = normaliza_precio(precio, retailer_product.sale_unit, mass_kg)
    return PriceByRetailerOut(
        retailer=RetailerRefOut(slug=retailer.slug, name=retailer.name),
        retailer_product_id=str(retailer_product.id),
        price=precio,
        currency=(obs.currency if obs is not None else "MXN"),
        is_available=(obs.is_available if obs is not None else False),
        captured_at=(obs.captured_at if obs is not None else None),
        url=retailer_product.url,
        sale_unit=retailer_product.sale_unit,
        price_per_piece=per_piece,
        price_per_kg=per_kg,
    )


def _menor_precio_por_kg(prices: list[PriceByRetailerOut]):
    """Menor `price_per_kg` entre los retailers disponibles; None si ninguno tiene.

    F031: la base de comparación cross-retailer es **$/kg** (agnóstica a la
    longitud), NO el precio nativo crudo. Solo cuentan los retailers disponibles
    con `price_per_kg` computado.
    """
    disponibles = [p.price_per_kg for p in prices if p.price_per_kg is not None and p.is_available]
    return min(disponibles) if disponibles else None


def buscar(
    q: str,
    zone_id: str,
    sort: str = "price",
    live: str = "auto",
) -> SearchOut | None:
    """Busca `q` en la zona: canónicos comparados + crudos + vivo si falta (F033).

    Devuelve None si la zona no existe o está inactiva (el router lo traduce a
    404). En caso contrario devuelve `SearchOut`:

    1. Gatillo live-on-miss: si `live=auto`, el término es utilizable y NO hay
       datos frescos ni cooldown, corre el scrape EN VIVO de ambos retailers
       (ingesta primero, así la misma respuesta ya sirve lo recién hallado).
    2. `results`: canónicos que matchean, ordenados por `sort` (`price`: menor
       `price_per_kg` disponible primero — F031; `name`: alfabético).
    3. `raw_results`: `RetailerProduct` SIN canónico, por UNIÓN de (a) los
       hallados bajo una corrida cuyo `search_term` == `q` normalizado (F035) y
       (b) los cuyo `raw_name` matchea, con su observación más fresca en la zona
       (retailer → precio asc, tope 50).
    """
    zona = Zone.objects.filter(id=zone_id, is_active=True).first()
    if zona is None:
        return None

    termino = _normalizar(q.strip())
    live_info = _buscar_en_vivo_si_falta(termino, zona, live)

    return SearchOut(
        results=_buscar_canonicos(termino, zona, sort),
        raw_results=_buscar_crudos(termino, zona),
        live=live_info,
    )


def _buscar_canonicos(termino: str, zona: Zone, sort: str) -> list[SearchResultOut]:
    """Canónicos que matchean `termino` con sus precios en la zona (F015/F031)."""
    resultados: list[tuple[SearchResultOut, object, str]] = []
    canonicos = (
        CanonicalProduct.objects.filter(is_active=True).select_related("category").order_by("name")
    )
    for canonico in canonicos:
        if termino and termino not in _normalizar(canonico.name):
            continue

        retailer_products = (
            canonico.retailer_products.filter(is_active=True)
            .select_related("retailer")
            .order_by("retailer__name")
        )
        prices = [_ensamblar_precio(rp, zona, canonico.mass_kg) for rp in retailer_products]

        item = SearchResultOut(
            canonical_product=CanonicalProductRefOut(
                id=str(canonico.id),
                name=canonico.name,
                category=canonico.category.name,
                unit=canonico.unit,
                mass_kg=canonico.mass_kg,
            ),
            prices=prices,
        )
        resultados.append((item, _menor_precio_por_kg(prices), canonico.name))

    if sort == "name":
        resultados.sort(key=lambda r: _normalizar(r[2]))
    else:  # sort == "price": menor price_per_kg disponible primero; sin él al final.
        resultados.sort(
            key=lambda r: (r[1] is None, r[1] if r[1] is not None else 0, _normalizar(r[2]))
        )

    return [item for item, _, _ in resultados]


# --- Resultados crudos por tienda (F033/F035) --------------------------------


def _rp_ids_por_termino_scrapeado(termino: str, zona: Zone) -> set:
    """IDs de RetailerProduct (sin canónico) hallados en la zona bajo una corrida
    cuyo `search_term` normalizado == `termino` (el fix F035).

    Es el puente que hace visibles los crudos que el retailer devolvió por un
    typo/fuzzy: sus nombres NO contienen el texto tecleado, pero la corrida que
    los ingestó sí registró el término. La normalización REUSA `_normalizar`
    (acento/case, + el `.strip()` que ya aplica la query) sobre AMBOS lados: el
    término del vivo ya viene normalizado (F033), el del comando es el
    `--category` crudo (F035). `termino` vacío no aporta (la unión la cubre el
    filtro por nombre).
    """
    if not termino:
        return set()
    run_ids = [
        run_id
        for run_id, term in ScrapeRun.objects.filter(search_term__isnull=False).values_list(
            "id", "search_term"
        )
        if _normalizar(term.strip()) == termino
    ]
    if not run_ids:
        return set()
    return set(
        PriceObservation.objects.filter(
            zone=zona,
            scrape_run_id__in=run_ids,
            retailer_product__is_active=True,
            retailer_product__canonical_product__isnull=True,
        ).values_list("retailer_product_id", flat=True)
    )


def _buscar_crudos(termino: str, zona: Zone) -> list[RawRetailerResultOut]:
    """Hallazgos crudos: `RetailerProduct` SIN canónico, por UNIÓN de dos filtros.

    Un producto entra si (a) tiene una observación en la zona bajo una corrida
    cuyo `search_term` normalizado == `termino` (F035: lo que el retailer devolvió
    para la query, aunque su nombre no contenga el texto tecleado) **O** (b) su
    `raw_name` acento-insensible contiene `termino` (relevancia por nombre, F033).
    Solo los que tienen observación en la zona (precio/frescura son obligatorios
    del contrato); los matcheados a canónico ya salen en `results`. El dedup es
    por construcción: se itera cada producto candidato UNA vez y se incluye si
    (a) O (b), así un producto que cumple ambos no aparece dos veces. Orden:
    retailer → precio asc → nombre; tope 50 (spec F033).
    """
    ids_por_termino = _rp_ids_por_termino_scrapeado(termino, zona)
    crudos: list[RawRetailerResultOut] = []
    candidatos = (
        RetailerProduct.objects.filter(is_active=True, canonical_product__isnull=True)
        .select_related("retailer")
        .order_by("retailer__name", "raw_name")
    )
    for rp in candidatos:
        coincide_nombre = not termino or termino in _normalizar(rp.raw_name)
        if not (coincide_nombre or rp.id in ids_por_termino):
            continue
        obs = ultima_observacion(rp, zone=zona)
        if obs is None:
            # Sin observación en la zona no hay precio/frescura que mostrar.
            continue
        crudos.append(
            RawRetailerResultOut(
                retailer_slug=rp.retailer.slug,
                retailer_name=rp.retailer.name,
                retailer_product_id=rp.id,
                external_sku=rp.external_sku,
                raw_name=rp.raw_name,
                url=rp.url or None,
                brand=rp.brand or None,
                sale_unit=rp.sale_unit or None,
                price=float(obs.price),
                currency=obs.currency,
                is_available=obs.is_available,
                captured_at=obs.captured_at,
            )
        )
    crudos.sort(key=lambda c: (c.retailer_slug, c.price, _normalizar(c.raw_name)))
    return crudos[:_RAW_RESULTS_MAX]


# --- Gatillo de la búsqueda en vivo (F033) -----------------------------------
# CUÁNDO disparar vive aquí (dominio de la búsqueda: frescura del término en la
# zona + cooldown). CÓMO correr vive en apps.scraping.services (adapters,
# concurrencia, presupuesto, guardrails §2.3).


def _matchea_termino(termino: str, rp: RetailerProduct) -> bool:
    """¿El RP (o su canónico) matchea `termino` acento-insensible?"""
    if not termino:
        return True
    if termino in _normalizar(rp.raw_name):
        return True
    canonico = rp.canonical_product
    return canonico is not None and termino in _normalizar(canonico.name)


def _hay_datos_frescos(termino: str, zona: Zone) -> bool:
    """¿Existe ALGUNA observación (canónica o cruda) fresca para término+zona?

    "Fresca" = `captured_at` dentro de `SEARCH_LIVE_TTL_HOURS`. El matcheo es el
    mismo de la búsqueda (acento-insensible, en memoria — SQLite MVP): sobre el
    `raw_name` del RP y el nombre de su canónico si lo tiene.
    """
    limite = timezone.now() - timedelta(hours=settings.SEARCH_LIVE_TTL_HOURS)
    rp_ids = [
        rp.id
        for rp in RetailerProduct.objects.filter(is_active=True).select_related("canonical_product")
        if _matchea_termino(termino, rp)
    ]
    if not rp_ids:
        return False
    return PriceObservation.objects.filter(
        retailer_product_id__in=rp_ids, zone=zona, captured_at__gte=limite
    ).exists()


def _en_cooldown(termino_corrida: str, zona: Zone, retailer: Retailer) -> bool:
    """¿Hay un `ScrapeRun` reciente de este término+zona+retailer?

    Aplica CUALQUIER corrida (aunque hallara 0 items o fallara): el cooldown
    existe para no martillar términos sin resultados ("asdfgh").
    """
    limite = timezone.now() - timedelta(minutes=settings.SEARCH_LIVE_COOLDOWN_MINUTES)
    return ScrapeRun.objects.filter(
        retailer=retailer,
        zone=zona,
        search_term=termino_corrida,
        started_at__gte=limite,
    ).exists()


def _buscar_en_vivo_si_falta(termino: str, zona: Zone, live: str) -> LiveSearchInfoOut | None:
    """Dispara la corrida en vivo si procede; None si no se disparó.

    Reglas del gatillo (spec F033):
    - `live=never` → nunca. Término normalizado con menos de 3 chars → nunca.
    - Solo si NO hay ninguna observación del término+zona más fresca que el TTL.
    - Por retailer: si tiene un `ScrapeRun` del término+zona dentro del
      cooldown queda fuera; si NINGÚN retailer queda, no se dispara.
    """
    if live == "never" or len(termino) < _TERMINO_MIN_VIVO:
        return None
    if _hay_datos_frescos(termino, zona):
        return None

    termino_corrida = termino[:_TERMINO_MAX_CORRIDA]
    retailers = sorted(
        Retailer.objects.filter(slug__in=scraping_services.LIVE_RETAILER_SLUGS),
        key=lambda r: scraping_services.LIVE_RETAILER_SLUGS.index(r.slug),
    )
    retailers = [r for r in retailers if not _en_cooldown(termino_corrida, zona, r)]
    if not retailers:
        return None

    reporte = scraping_services.correr_busqueda_en_vivo(termino_corrida, zona, retailers)
    return LiveSearchInfoOut(
        triggered=True,
        duration_ms=reporte.duration_ms,
        retailers=[
            LiveRetailerStatusOut(
                retailer_slug=outcome.retailer_slug,
                status=outcome.status,
                items_found=outcome.items_found,
                detail=outcome.detail,
            )
            for outcome in reporte.outcomes
        ],
    )


def _historial(canonico: CanonicalProduct, zona: Zone, n: int) -> list[PriceHistoryPointOut]:
    """Últimas `n` observaciones del canónico en la zona, orden `-captured_at`.

    Combina todos los `RetailerProduct` activos enlazados al canónico; cada punto
    lleva su retailer. La consulta se apoya en el índice (retailer_product, zone,
    -captured_at) y el orden por `-captured_at` del modelo.

    F031: cada punto gana `sale_unit` (etiqueta de unidad nativa); el `price` NO
    se normaliza (el historial queda en valor nativo, fuera de alcance).
    """
    observaciones = (
        PriceObservation.objects.filter(
            retailer_product__canonical_product=canonico,
            retailer_product__is_active=True,
            zone=zona,
        )
        .select_related("retailer_product__retailer")
        .order_by("-captured_at")[:n]
    )
    return [
        PriceHistoryPointOut(
            retailer=RetailerRefOut(
                slug=obs.retailer_product.retailer.slug,
                name=obs.retailer_product.retailer.name,
            ),
            price=obs.price,
            currency=obs.currency,
            is_available=obs.is_available,
            captured_at=obs.captured_at,
            sale_unit=obs.retailer_product.sale_unit,
        )
        for obs in observaciones
    ]


def detalle_producto(
    product_id: str,
    zone_id: str,
    historial_n: int = _HISTORIAL_DEFAULT,
) -> ProductDetailOut | None:
    """Detalle de un canónico en una zona: producto, precios actuales e historial.

    Devuelve None si el canónico no existe/inactivo o si la zona no existe/inactiva
    (el router lo traduce a 404). `prices` reutiliza el ensamblado "precio más
    fresco por retailer/zona" de F015; `history` son las últimas `historial_n`
    observaciones en la zona, orden `-captured_at`.
    """
    zona = Zone.objects.filter(id=zone_id, is_active=True).first()
    if zona is None:
        return None

    canonico = (
        CanonicalProduct.objects.filter(id=product_id, is_active=True)
        .select_related("category")
        .first()
    )
    if canonico is None:
        return None

    retailer_products = (
        canonico.retailer_products.filter(is_active=True)
        .select_related("retailer")
        .order_by("retailer__name")
    )
    prices = [_ensamblar_precio(rp, zona, canonico.mass_kg) for rp in retailer_products]

    return ProductDetailOut(
        canonical_product=CanonicalProductDetailOut(
            id=str(canonico.id),
            name=canonico.name,
            category=canonico.category.name,
            unit=canonico.unit,
            mass_kg=canonico.mass_kg,
            specs=canonico.specs,
        ),
        prices=prices,
        history=_historial(canonico, zona, historial_n),
    )
