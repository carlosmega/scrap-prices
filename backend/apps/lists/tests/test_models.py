"""Tests de modelo de listas de cotización anónimas (F009).

Cubre los criterios de aceptación de la spec:
- crear una `UserList` anónima con `session_key` y `zone` (sin login/User);
- agregar dos `UserListItem` con `captured_price`/`captured_at` y cantidades;
- snapshot inmutable: cambiar el precio del `RetailerProduct` o crear nuevas
  `PriceObservation` NO altera el `captured_price` del ítem (CA2 de C1);
- subtotal de la lista (suma `quantity * captured_price`) vía `services.py`;
- defaults (`quantity`, `status`, `name`) y herencia de la base abstracta.
SQLite, sin Docker.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, Zone
from apps.lists import services
from apps.lists.models import UserList, UserListItem
from apps.prices.models import PriceObservation


@pytest.fixture
def home_depot():
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def zona():
    return Zone.objects.create(
        name="Monterrey Metro",
        slug="monterrey-metro",
        state="Nuevo León",
    )


@pytest.fixture
def sku(home_depot):
    return RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-001",
        raw_name="Varilla corrugada 3/8 12m",
    )


@pytest.fixture
def otro_sku(home_depot):
    return RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-002",
        raw_name="Cemento gris 50kg",
    )


@pytest.mark.django_db
def test_crear_lista_anonima_con_session_key_y_zona(zona):
    """Una UserList se crea anónima (solo session_key) y opcionalmente con zona."""
    lista = UserList.objects.create(session_key="sess-abc123", zone=zona)
    assert isinstance(lista.id, uuid.UUID)
    assert lista.created_at is not None
    assert lista.updated_at is not None
    assert lista.is_active is True
    # Anónima: no existe campo user_fk/user en el modelo (decisión de producto).
    field_names = {f.name for f in UserList._meta.get_fields()}
    assert "user" not in field_names
    assert "user_fk" not in field_names
    # Defaults de producto.
    assert lista.name == "Mi cotización"
    assert lista.status == UserList.Status.OPEN
    assert lista.zone == zona


@pytest.mark.django_db
def test_session_key_indexado():
    """session_key está indexado (consulta caliente: 'mis listas por sesión')."""
    field = UserList._meta.get_field("session_key")
    assert field.db_index is True


@pytest.mark.django_db
def test_agregar_y_quitar_items_con_cantidades(zona, sku, otro_sku):
    """Se agregan dos ítems con cantidades y luego se quita uno."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    captura = datetime(2026, 6, 13, 10, 0, tzinfo=UTC)
    item1 = UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        quantity=10,
        captured_price=Decimal("190.25"),
        captured_at=captura,
    )
    item2 = UserListItem.objects.create(
        user_list=lista,
        retailer_product=otro_sku,
        quantity=3,
        captured_price=Decimal("250.00"),
        captured_at=captura,
    )
    # related_name 'items' en la lista; 'list_items' en el SKU.
    assert lista.items.count() == 2
    assert {item1, item2} == set(lista.items.all())
    assert list(sku.list_items.all()) == [item1]

    # Quitar un ítem: la lista queda con uno.
    item1.delete()
    assert lista.items.count() == 1
    assert list(lista.items.all()) == [item2]


@pytest.mark.django_db
def test_quantity_default_uno(zona, sku):
    """quantity por defecto es 1 si no se especifica."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    item = UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        captured_price=Decimal("100.00"),
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )
    assert item.quantity == 1


@pytest.mark.django_db
def test_captured_price_es_snapshot_inmutable_ante_observaciones(zona, sku):
    """Crear nuevas PriceObservation del SKU NO altera el captured_price del ítem."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    precio_al_agregar = Decimal("190.25")
    item = UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        quantity=2,
        captured_price=precio_al_agregar,
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )

    # Más tarde el precio del SKU cambia (nuevas observaciones más caras).
    PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("999.99"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
    )

    item.refresh_from_db()
    # El snapshot del ítem es inmutable: sigue siendo el precio al agregar.
    assert item.captured_price == precio_al_agregar
    assert isinstance(item.captured_price, Decimal)


@pytest.mark.django_db
def test_captured_price_no_cambia_si_cambia_el_sku(zona, sku):
    """Editar el SKU (raw_name/brand) no toca el captured_price del ítem."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    item = UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        captured_price=Decimal("190.25"),
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )
    sku.raw_name = "Varilla corrugada 3/8 12m (rebrand)"
    sku.brand = "Acme"
    sku.save()

    item.refresh_from_db()
    assert item.captured_price == Decimal("190.25")


@pytest.mark.django_db
def test_subtotal_lista_suma_cantidad_por_precio(zona, sku, otro_sku):
    """services.subtotal_lista suma quantity * captured_price de cada ítem."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    captura = datetime(2026, 6, 13, 10, 0, tzinfo=UTC)
    UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        quantity=10,
        captured_price=Decimal("190.25"),
        captured_at=captura,
    )
    UserListItem.objects.create(
        user_list=lista,
        retailer_product=otro_sku,
        quantity=3,
        captured_price=Decimal("250.00"),
        captured_at=captura,
    )
    # 10 * 190.25 + 3 * 250.00 = 1902.50 + 750.00 = 2652.50
    assert services.subtotal_lista(lista) == Decimal("2652.50")


@pytest.mark.django_db
def test_subtotal_lista_vacia_es_cero(zona):
    """Una lista sin ítems tiene subtotal 0.00 (no lanza)."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    assert services.subtotal_lista(lista) == Decimal("0.00")


@pytest.mark.django_db
def test_subtotal_usa_snapshot_no_precio_en_vivo(zona, sku):
    """El subtotal usa el captured_price, aunque el precio en vivo del SKU cambie."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        quantity=2,
        captured_price=Decimal("100.00"),
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )
    # Una observación posterior mucho más cara no afecta el subtotal de la lista.
    PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("5000.00"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
    )
    assert services.subtotal_lista(lista) == Decimal("200.00")


@pytest.mark.django_db
def test_borrar_lista_borra_sus_items_en_cascada(zona, sku):
    """Al borrar la UserList, sus UserListItem se borran en cascada."""
    lista = UserList.objects.create(session_key="sess-1", zone=zona)
    UserListItem.objects.create(
        user_list=lista,
        retailer_product=sku,
        captured_price=Decimal("100.00"),
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )
    lista_id = lista.id
    lista.delete()
    assert UserListItem.objects.filter(user_list_id=lista_id).count() == 0


@pytest.mark.django_db
def test_lista_zona_nula_permitida():
    """La zona es opcional: una lista anónima puede no tener zona aún."""
    lista = UserList.objects.create(session_key="sess-sin-zona")
    assert lista.zone is None
