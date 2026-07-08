"""Lógica de negocio de la app core. Sin HTTP, sin routers.

Incluye:
- el estado de salud (estático, no toca la DB);
- el `seed` de datos demo (F013): siembra el grafo mínimo del PRD para la zona
  piloto (Monterrey Metro · varilla) de forma **idempotente**. La lógica de
  armado vive aquí (services); el management command solo la invoca.
"""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from apps.catalog.models import CanonicalProduct, Category, RetailerProduct
from apps.core.schemas import HealthOut
from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices.models import PriceObservation


def get_health() -> HealthOut:
    """Devuelve el estado del servicio. Estático: no consulta la DB."""
    return HealthOut(status="ok")


# --- Seed de datos demo (F013) ---------------------------------------------
# Grafo curado a mano (no datos reales de los retailers): zona piloto Monterrey
# Metro, categoría piloto varilla. Precios ficticios pero verosímiles. Todo el
# grafo se siembra con get_or_create/update_or_create -> idempotente.

# Unidad de venta nativa por retailer (F031): HD lista por TONELADA, Construrama
# por KILOGRAMO. Sembrarlas distintas ejerce la normalización end-to-end sin red.
_SALE_UNIT_POR_RETAILER = {
    "home-depot": RetailerProduct.SaleUnit.TONELADA,
    "construrama": RetailerProduct.SaleUnit.KG,
}

# 3 varillas corrugadas (CanonicalProduct). slug-like key vía specs+name.
# F031: `mass_kg` = masa nominal NMX (kg/m) × longitud (m). Es el factor de
# conversión que habilita la comparación cross-retailer. `precios` son los
# NATIVOS base de cada retailer EN SU UNIDAD (HD $/ton, CR $/kg).
_VARILLAS = [
    {
        "name": 'Varilla corrugada 3/8" (#3) 12m',
        "specs": {"calibre": "#3", "diametro": '3/8"', "longitud_m": 12},
        "mass_kg": Decimal("6.684"),  # 0.557 kg/m × 12 m
        "skus": {
            "home-depot": {
                "external_sku": "HD-VAR-38-12",
                "raw_name": "Varilla 3/8 12 m grado 42",
            },
            "construrama": {
                "external_sku": "CR-VAR-38-12",
                "raw_name": "Varilla corrugada 3/8 12m",
            },
        },
        # precios base NATIVOS por retailer (HD $/ton, CR $/kg). El historial crece
        # multiplicativamente (factor sobre el base) para ser agnostico a la unidad.
        "precios": {"home-depot": "19500.00", "construrama": "20.90"},
    },
    {
        "name": 'Varilla corrugada 1/2" (#4) 12m',
        "specs": {"calibre": "#4", "diametro": '1/2"', "longitud_m": 12},
        "mass_kg": Decimal("11.952"),  # 0.996 kg/m × 12 m
        "skus": {
            "home-depot": {
                "external_sku": "HD-VAR-12-12",
                "raw_name": "Varilla 1/2 12 m grado 42",
            },
            "construrama": {
                "external_sku": "CR-VAR-12-12",
                "raw_name": "Varilla corrugada 1/2 12m",
            },
        },
        "precios": {"home-depot": "19500.00", "construrama": "20.90"},
    },
    {
        "name": 'Varilla corrugada 1/4" (#2) 6m',
        "specs": {"calibre": "#2", "diametro": '1/4"', "longitud_m": 6},
        "mass_kg": Decimal("1.488"),  # 0.248 kg/m × 6 m
        "skus": {
            "home-depot": {"external_sku": "HD-VAR-14-6", "raw_name": "Varilla 1/4 6 m"},
            "construrama": {
                "external_sku": "CR-VAR-14-6",
                "raw_name": "Varilla corrugada 1/4 6m",
            },
        },
        "precios": {"home-depot": "20500.00", "construrama": "19.80"},
    },
]

# Tres capturas historicas (de mas antigua a mas reciente). F031: el precio crece
# MULTIPLICATIVAMENTE (factor sobre el base, cuantizado 2dp) para ser agnostico a
# la unidad nativa.
_CAPTURAS = [
    {"captured_at": datetime(2026, 5, 30, 9, 0, tzinfo=UTC), "factor": Decimal("1.000")},
    {"captured_at": datetime(2026, 6, 6, 9, 0, tzinfo=UTC), "factor": Decimal("1.015")},
    {"captured_at": datetime(2026, 6, 13, 9, 0, tzinfo=UTC), "factor": Decimal("1.030")},
]

# F033: factor de la captura FRESCA (captured_at = ahora). Igual al de la última
# captura fija (×1.030): el precio "vigente" no cambia respecto a F031, solo su
# frescura. Con datos frescos la búsqueda NO dispara el scrape en vivo (TTL 24h)
# — clave para que la demo sembrada y el E2E sigan siendo 100% OFFLINE.
_FACTOR_FRESCO = Decimal("1.030")

# Cuantizacion monetaria del historial multiplicativo: 2 decimales, ROUND_HALF_UP.
_CENTAVOS = Decimal("0.01")

# --- Producto crudo SIN matchear (F033) --------------------------------------
# Hallazgo REAL de Construrama (hit del golden fixture Algolia): el amarrador de
# varillas Truper. Se siembra SIN canónico (match_status unmatched) para que la
# sección "resultados de las tiendas (sin comparar)" de la búsqueda sea visible
# con datos sembrados (su raw_name matchea "varilla"). El matching manual en
# Admin (PRD D1) es lo que lo promovería a la comparación canónica.
_CRUDO_CONSTRURAMA = {
    "external_sku": "0204000086",
    "raw_name": "Truper, Amarrador De Varillas Con Grip, Pieza",
    "url": (
        "https://www.construrama.com/catalogo/aceros/varilla/varilla/"
        "truper-amarrador-de-varillas-con-grip-pieza/p/0204000086"
    ),
    "brand": "TRUPER",
    "unit_raw": "Pieza",
    "sale_unit": RetailerProduct.SaleUnit.PIEZA,
    "precio": Decimal("125.00"),
}


def _seed_pdp_url(slug: str, base_url: str, external_sku: str) -> str:
    """URL de ficha demo por retailer para el seed (F034).

    Home Depot NO expone `/p/{sku}` (responde 404: patrón inexistente); su
    buscador sí halla el producto por SKU, así que la demo usa el fallback
    `/search?q={sku}` (verificado 200) en vez de una ficha rota. Construrama sí
    lista por `/...p/{code}` (su patrón real): se conserva su URL.
    """
    if slug == "home-depot":
        return f"{base_url}/search?q={external_sku}"
    return f"{base_url}/p/{external_sku}"


def _sembrar_observacion_fresca(rp, zona, location, precio) -> bool:
    """Siembra/refresca la observación FRESCA (captured_at=ahora) de un RP.

    Idempotente sin duplicar: la fila se identifica por el marker
    `raw_payload.fresh` (la clave natural (rp, zona, captured_at) no sirve
    porque captured_at es "ahora" y cambia por corrida). Re-sembrar ACTUALIZA
    esa misma fila (refresca captured_at/price) en vez de crear otra. Devuelve
    True si la creó. Es un artificio de LA DEMO: las corridas reales de
    scraping siguen siendo append-only (nunca sobrescriben).
    """
    ahora = timezone.now()
    existente = PriceObservation.objects.filter(
        retailer_product=rp, zone=zona, raw_payload__fresh=True
    ).first()
    if existente is None:
        PriceObservation.objects.create(
            retailer_product=rp,
            zone=zona,
            retailer_location=location,
            price=precio,
            currency="MXN",
            is_available=True,
            source=PriceObservation.Source.XHR,
            captured_at=ahora,
            raw_payload={"seed": True, "fresh": True},
        )
        return True
    existente.retailer_location = location
    existente.price = precio
    existente.captured_at = ahora
    existente.save(update_fields=["retailer_location", "price", "captured_at", "updated_at"])
    return False


def seed_demo() -> dict[str, int]:
    """Siembra el grafo demo (Monterrey Metro · varilla). Idempotente.

    Usa get_or_create/update_or_create con claves naturales estables, así que
    correrlo varias veces no duplica filas ni falla. Devuelve un resumen de
    conteos para que el command lo reporte.
    """
    hd, _ = Retailer.objects.update_or_create(
        slug="home-depot",
        defaults={
            "name": "Home Depot",
            "base_url": "https://www.homedepot.com.mx",
            "pricing_model": Retailer.PricingModel.ZONE_COOKIE,
            "scraper_status": Retailer.ScraperStatus.ACTIVE,
        },
    )
    cr, _ = Retailer.objects.update_or_create(
        slug="construrama",
        defaults={
            "name": "Construrama",
            "base_url": "https://www.construrama.com",
            "pricing_model": Retailer.PricingModel.DISTRIBUTOR_SUBPATH,
            "scraper_status": Retailer.ScraperStatus.ACTIVE,
        },
    )
    retailers = {"home-depot": hd, "construrama": cr}

    # RetailerLocation: HD tienda (external_id), Construrama distribuidor (subpath).
    # Clave de lookup estable = (retailer, name), NO el external_id: este último es
    # el código real de la tienda Monterrey del recon F010 ("1333", physicalStoreId
    # que HD acepta para precio) y puede cambiar. Keyear por name -> re-sembrar
    # ACTUALIZA el external_id en sitio en vez de dejar una fila huérfana.
    hd_loc, _ = RetailerLocation.objects.update_or_create(
        retailer=hd,
        name="Home Depot Valle Oriente",
        defaults={
            "external_id": "1333",
            "subpath": "",
            "address": "Av. Lázaro Cárdenas 1000, Valle Oriente",
            "city": "Monterrey",
            "state": "NL",
            "lat": Decimal("25.648900"),
            "lng": Decimal("-100.310600"),
            # Params de routing reales de HCL Commerce para esta tienda (recon
            # F010 §3): marketId 10 y stLocId 18503 (id interno, distinto del
            # external_id/physicalStoreId 1333). Necesarios para que la búsqueda
            # devuelva resultados con precio (F029).
            "extra": {"market_id": "10", "st_loc_id": "18503"},
        },
    )
    cr_loc, _ = RetailerLocation.objects.update_or_create(
        retailer=cr,
        external_id="distribuidor-mty-centro",
        defaults={
            "name": "Construrama Materiales del Norte",
            "subpath": "/nuevo-leon",
            "address": "Av. Colón 500, Centro",
            "city": "Monterrey",
            "state": "NL",
            "lat": Decimal("25.686600"),
            "lng": Decimal("-100.316100"),
            # F026: params de routing/precio de Construrama (recon §1-§2). El
            # subpath de la URL de catálogo es el ESTADO (`nuevo-leon`); el precio
            # de la zona vive en el índice Algolia `construrama_mx` bajo el prefijo
            # del store activo (`currentStore=OSS7` de `get/algolia`). App ID e
            # índice son públicos; la search key NO se siembra (va por env).
            "extra": {
                "subpath": "nuevo-leon",
                "current_store": "OSS7",
                "place_id": "ChIJ9fg3tDGVYoYRlJjIasrT06M",
                "algolia_app_id": "NJVY3EU5DW",
                "algolia_index": "construrama_mx",
            },
        },
    )

    # Zona piloto + mapeo (HD primaria).
    zona, _ = Zone.objects.update_or_create(
        slug="monterrey-metro",
        defaults={
            "name": "Monterrey Metro",
            "state": "NL",
            "centroid_lat": Decimal("25.673200"),
            "centroid_lng": Decimal("-100.297300"),
        },
    )
    # `is_primary` es POR retailer: marca la ubicación primaria de ESE retailer
    # que sirve la zona (lo consume el resolver del comando `scrape`, que filtra
    # por retailer, y el Admin). La búsqueda de precios NO depende de un único
    # primario por zona. Ambos retailers tienen su primaria en Monterrey Metro
    # para que `scrape --retailer {home-depot|construrama}` resuelva su tienda.
    ZoneLocationMap.objects.update_or_create(
        zone=zona, retailer_location=hd_loc, defaults={"is_primary": True}
    )
    ZoneLocationMap.objects.update_or_create(
        zone=zona, retailer_location=cr_loc, defaults={"is_primary": True}
    )

    # Categoría piloto.
    categoria, _ = Category.objects.update_or_create(
        slug="varilla", defaults={"name": "Varilla", "parent": None}
    )

    obs_count = 0
    for varilla in _VARILLAS:
        canonico, _ = CanonicalProduct.objects.update_or_create(
            name=varilla["name"],
            defaults={
                "category": categoria,
                "unit": CanonicalProduct.Unit.PIEZA,
                "mass_kg": varilla["mass_kg"],
                "specs": varilla["specs"],
            },
        )
        for slug, sku_info in varilla["skus"].items():
            retailer = retailers[slug]
            rp, _ = RetailerProduct.objects.update_or_create(
                retailer=retailer,
                external_sku=sku_info["external_sku"],
                defaults={
                    "raw_name": sku_info["raw_name"],
                    "url": _seed_pdp_url(slug, retailer.base_url, sku_info["external_sku"]),
                    "canonical_product": canonico,
                    "sale_unit": _SALE_UNIT_POR_RETAILER[slug],
                    "match_status": RetailerProduct.MatchStatus.MANUAL,
                    "match_confidence": 1.0,
                },
            )
            base = Decimal(varilla["precios"][slug])
            location = hd_loc if slug == "home-depot" else cr_loc
            for captura in _CAPTURAS:
                # Historial multiplicativo: base × factor, cuantizado a 2dp.
                precio = (base * captura["factor"]).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
                # Clave natural: (retailer_product, zona, captured_at) -> sin duplicar.
                _, creada = PriceObservation.objects.update_or_create(
                    retailer_product=rp,
                    zone=zona,
                    captured_at=captura["captured_at"],
                    defaults={
                        "retailer_location": location,
                        "price": precio,
                        "currency": "MXN",
                        "is_available": True,
                        "source": PriceObservation.Source.XHR,
                        "raw_payload": {"seed": True},
                    },
                )
                if creada:
                    obs_count += 1
            # F033: captura FRESCA (captured_at=ahora, mismo precio vigente
            # ×1.030) para que la búsqueda de los términos sembrados NO dispare
            # el scrape en vivo (TTL 24h) — demo y E2E siguen offline.
            precio_fresco = (base * _FACTOR_FRESCO).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
            if _sembrar_observacion_fresca(rp, zona, location, precio_fresco):
                obs_count += 1

    # F033: producto crudo SIN matchear (real, del fixture de Construrama) con
    # historial + observación fresca: hace visible la sección de resultados por
    # tienda ("sin comparar") de la búsqueda con datos sembrados.
    crudo, _ = RetailerProduct.objects.update_or_create(
        retailer=cr,
        external_sku=_CRUDO_CONSTRURAMA["external_sku"],
        defaults={
            "raw_name": _CRUDO_CONSTRURAMA["raw_name"],
            "url": _CRUDO_CONSTRURAMA["url"],
            "brand": _CRUDO_CONSTRURAMA["brand"],
            "unit_raw": _CRUDO_CONSTRURAMA["unit_raw"],
            "sale_unit": _CRUDO_CONSTRURAMA["sale_unit"],
            "canonical_product": None,
            "match_status": RetailerProduct.MatchStatus.UNMATCHED,
            "match_confidence": None,
        },
    )
    _, creada = PriceObservation.objects.update_or_create(
        retailer_product=crudo,
        zone=zona,
        captured_at=_CAPTURAS[-1]["captured_at"],
        defaults={
            "retailer_location": cr_loc,
            "price": _CRUDO_CONSTRURAMA["precio"],
            "currency": "MXN",
            "is_available": True,
            "source": PriceObservation.Source.XHR,
            "raw_payload": {"seed": True},
        },
    )
    if creada:
        obs_count += 1
    if _sembrar_observacion_fresca(crudo, zona, cr_loc, _CRUDO_CONSTRURAMA["precio"]):
        obs_count += 1

    return {
        "retailers": Retailer.objects.count(),
        "locations": RetailerLocation.objects.count(),
        "zones": Zone.objects.count(),
        "zone_maps": ZoneLocationMap.objects.count(),
        "categories": Category.objects.count(),
        "canonical_products": CanonicalProduct.objects.count(),
        "retailer_products": RetailerProduct.objects.count(),
        "observations": PriceObservation.objects.count(),
        "observations_created": obs_count,
    }
