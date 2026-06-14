"""Lógica de negocio de la app core. Sin HTTP, sin routers.

Incluye:
- el estado de salud (estático, no toca la DB);
- el `seed` de datos demo (F013): siembra el grafo mínimo del PRD para la zona
  piloto (Monterrey Metro · varilla) de forma **idempotente**. La lógica de
  armado vive aquí (services); el management command solo la invoca.
"""

from datetime import UTC, datetime
from decimal import Decimal

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

# 3 varillas corrugadas (CanonicalProduct). slug-like key vía specs+name.
_VARILLAS = [
    {
        "name": 'Varilla corrugada 3/8" (#3) 12m',
        "specs": {"calibre": "#3", "diametro": '3/8"', "longitud_m": 12},
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
        # precios base por retailer (mas reciente arranca aqui y crece en el historial)
        "precios": {"home-depot": "189.50", "construrama": "182.00"},
    },
    {
        "name": 'Varilla corrugada 1/2" (#4) 12m',
        "specs": {"calibre": "#4", "diametro": '1/2"', "longitud_m": 12},
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
        "precios": {"home-depot": "329.00", "construrama": "315.50"},
    },
    {
        "name": 'Varilla corrugada 1/4" (#2) 6m',
        "specs": {"calibre": "#2", "diametro": '1/4"', "longitud_m": 6},
        "skus": {
            "home-depot": {"external_sku": "HD-VAR-14-6", "raw_name": "Varilla 1/4 6 m"},
            "construrama": {
                "external_sku": "CR-VAR-14-6",
                "raw_name": "Varilla corrugada 1/4 6m",
            },
        },
        "precios": {"home-depot": "64.90", "construrama": "59.50"},
    },
]

# Tres capturas historicas (de mas antigua a mas reciente). El precio sube en
# cada captura para que "ultima observacion" sea inequivoca.
_CAPTURAS = [
    {"captured_at": datetime(2026, 5, 30, 9, 0, tzinfo=UTC), "delta": Decimal("0")},
    {"captured_at": datetime(2026, 6, 6, 9, 0, tzinfo=UTC), "delta": Decimal("4.50")},
    {"captured_at": datetime(2026, 6, 13, 9, 0, tzinfo=UTC), "delta": Decimal("9.00")},
]


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
    hd_loc, _ = RetailerLocation.objects.update_or_create(
        retailer=hd,
        external_id="store-2034",
        defaults={
            "name": "Home Depot Valle Oriente",
            "subpath": "",
            "address": "Av. Lázaro Cárdenas 1000, Valle Oriente",
            "city": "Monterrey",
            "state": "NL",
            "lat": Decimal("25.648900"),
            "lng": Decimal("-100.310600"),
        },
    )
    cr_loc, _ = RetailerLocation.objects.update_or_create(
        retailer=cr,
        external_id="distribuidor-mty-centro",
        defaults={
            "name": "Construrama Materiales del Norte",
            "subpath": "/distribuidores/mty-centro",
            "address": "Av. Colón 500, Centro",
            "city": "Monterrey",
            "state": "NL",
            "lat": Decimal("25.686600"),
            "lng": Decimal("-100.316100"),
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
    ZoneLocationMap.objects.update_or_create(
        zone=zona, retailer_location=hd_loc, defaults={"is_primary": True}
    )
    ZoneLocationMap.objects.update_or_create(
        zone=zona, retailer_location=cr_loc, defaults={"is_primary": False}
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
                    "url": f"{retailer.base_url}/p/{sku_info['external_sku']}",
                    "canonical_product": canonico,
                    "match_status": RetailerProduct.MatchStatus.MANUAL,
                    "match_confidence": 1.0,
                },
            )
            base = Decimal(varilla["precios"][slug])
            for captura in _CAPTURAS:
                # Clave natural: (retailer_product, zona, captured_at) -> sin duplicar.
                _, creada = PriceObservation.objects.update_or_create(
                    retailer_product=rp,
                    zone=zona,
                    captured_at=captura["captured_at"],
                    defaults={
                        "retailer_location": (hd_loc if slug == "home-depot" else cr_loc),
                        "price": base + captura["delta"],
                        "currency": "MXN",
                        "is_available": True,
                        "source": PriceObservation.Source.XHR,
                        "raw_payload": {"seed": True},
                    },
                )
                if creada:
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
