"""Tests de modelo del catálogo (F007).

Cubre los criterios de aceptación de la spec: las 3 entidades heredan la base
abstracta (UUID/timestamps/is_active); la jerarquía de `Category`; el flujo de
matching manual (dos `RetailerProduct` `unmatched` se asignan a un
`CanonicalProduct` y pasan a `manual`); y el `unique_together
(retailer, external_sku)`. SQLite, sin Docker.
"""

import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.catalog.models import CanonicalProduct, Category, RetailerProduct
from apps.geo.models import Retailer


@pytest.fixture
def categoria_varilla():
    return Category.objects.create(name="Varilla", slug="varilla")


@pytest.fixture
def canonico(categoria_varilla):
    return CanonicalProduct.objects.create(
        name="Varilla corrugada 3/8 12m",
        category=categoria_varilla,
        unit=CanonicalProduct.Unit.PIEZA,
        specs={"calibre": "3/8", "longitud": "12m"},
    )


@pytest.fixture
def home_depot():
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def construrama():
    return Retailer.objects.create(
        name="Construrama",
        slug="construrama",
        base_url="https://www.construrama.com",
        pricing_model=Retailer.PricingModel.DISTRIBUTOR_SUBPATH,
    )


@pytest.mark.django_db
def test_category_hereda_base_abstracta(categoria_varilla):
    """Category hereda la base: id UUID, timestamps e is_active por defecto."""
    assert isinstance(categoria_varilla.id, uuid.UUID)
    assert categoria_varilla.created_at is not None
    assert categoria_varilla.updated_at is not None
    assert categoria_varilla.is_active is True


@pytest.mark.django_db
def test_category_jerarquia_self_fk(categoria_varilla):
    """Category es jerárquica: el self-FK 'parent' expone related_name 'children'."""
    hija = Category.objects.create(
        name="Varilla corrugada",
        slug="varilla-corrugada",
        parent=categoria_varilla,
    )
    assert hija.parent == categoria_varilla
    assert list(categoria_varilla.children.all()) == [hija]


@pytest.mark.django_db
def test_canonical_product_pertenece_a_categoria(canonico, categoria_varilla):
    """CanonicalProduct→Category expone related_name 'products' y specs JSON."""
    assert canonico.category == categoria_varilla
    assert list(categoria_varilla.products.all()) == [canonico]
    assert canonico.specs == {"calibre": "3/8", "longitud": "12m"}


@pytest.mark.django_db
def test_canonical_product_specs_default_dict(categoria_varilla):
    """specs tiene default dict vacío si no se especifica."""
    producto = CanonicalProduct.objects.create(
        name="Varilla lisa 1/4",
        category=categoria_varilla,
        unit=CanonicalProduct.Unit.PIEZA,
    )
    assert producto.specs == {}


@pytest.mark.django_db
def test_retailer_product_default_match_status_unmatched(home_depot):
    """Un RetailerProduct recién creado nace 'unmatched' y sin canónico."""
    sku = RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-001",
        raw_name="Varilla 3/8 12m corrugada",
    )
    assert sku.match_status == RetailerProduct.MatchStatus.UNMATCHED
    assert sku.canonical_product is None
    assert sku.match_confidence is None


@pytest.mark.django_db
def test_matching_manual_dos_retailers_a_un_canonico(home_depot, construrama, canonico):
    """Dos SKUs (uno por retailer) unmatched se asignan al canónico → manual."""
    sku_hd = RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-001",
        raw_name="Varilla 3/8 12m corrugada",
    )
    sku_cr = RetailerProduct.objects.create(
        retailer=construrama,
        external_sku="CR-777",
        raw_name="Varilla corrugada 3/8 x 12 metros",
    )
    assert sku_hd.match_status == RetailerProduct.MatchStatus.UNMATCHED
    assert sku_cr.match_status == RetailerProduct.MatchStatus.UNMATCHED

    # Curación manual: enlazar al canónico y marcar como manual.
    for sku in (sku_hd, sku_cr):
        sku.canonical_product = canonico
        sku.match_status = RetailerProduct.MatchStatus.MANUAL
        sku.save(update_fields=["canonical_product", "match_status"])

    # El canónico agrupa ambos SKUs vía related_name 'retailer_products'.
    assert set(canonico.retailer_products.all()) == {sku_hd, sku_cr}
    for sku in canonico.retailer_products.all():
        assert sku.match_status == RetailerProduct.MatchStatus.MANUAL


@pytest.mark.django_db
def test_retailer_product_unique_together(home_depot):
    """El par (retailer, external_sku) es único: el duplicado lanza IntegrityError."""
    RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-001",
        raw_name="Varilla 3/8 12m",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        RetailerProduct.objects.create(
            retailer=home_depot,
            external_sku="HD-001",
            raw_name="Otro nombre crudo mismo SKU",
        )


@pytest.mark.django_db
def test_mismo_sku_en_distintos_retailers_es_valido(home_depot, construrama):
    """El mismo external_sku en retailers distintos NO colisiona."""
    RetailerProduct.objects.create(
        retailer=home_depot, external_sku="X-1", raw_name="Varilla HD"
    )
    # No debe lanzar: la unicidad es por (retailer, external_sku).
    RetailerProduct.objects.create(
        retailer=construrama, external_sku="X-1", raw_name="Varilla CR"
    )
    assert RetailerProduct.objects.filter(external_sku="X-1").count() == 2


@pytest.mark.django_db
def test_borrar_canonico_no_borra_el_sku(home_depot, canonico):
    """Al borrar el canónico, el SKU sobrevive con canonical_product=None (SET_NULL)."""
    sku = RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-002",
        raw_name="Varilla 1/2",
        canonical_product=canonico,
        match_status=RetailerProduct.MatchStatus.MANUAL,
    )
    canonico.delete()
    sku.refresh_from_db()
    assert sku.canonical_product is None
