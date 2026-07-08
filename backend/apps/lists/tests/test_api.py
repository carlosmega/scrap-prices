"""Tests de la API de listas de cotización (F017): CRUD de /api/lists.

Cubre los criterios de aceptación de la spec, todos con el header `X-Session-Key`:
- flujo completo: crear lista, agregar 2 ítems (snapshot capturado), editar
  cantidad, quitar ítem, ver detalle con subtotal/total correctos, borrar;
- snapshot inmutable: una nueva `PriceObservation` tras agregar NO cambia el
  `captured_price` del ítem (CA2 de C1);
- scoping por sesión: la sesión B NO ve ni modifica la lista de la sesión A (404);
- 400 cuando falta el header donde se requiere;
- 422 cuando la cantidad es inválida (0/negativa) y cuando no hay precio para snapshot.

Datos del `seed` (idempotente) + ORM para casos deterministas. SQLite, sin Docker.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.management import call_command
from ninja.testing import TestClient

from apps.catalog.models import CanonicalProduct, RetailerProduct
from apps.geo.models import Retailer, Zone
from apps.lists.api import router
from apps.prices.models import PriceObservation

SESION_A = "sess-aaaaaaaa"
SESION_B = "sess-bbbbbbbb"
HDR_A = {"X-Session-Key": SESION_A}
HDR_B = {"X-Session-Key": SESION_B}


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def seeded(db):
    """Aplica el seed demo y devuelve la zona piloto y dos SKUs de varilla."""
    call_command("seed")
    zona = Zone.objects.get(slug="monterrey-metro")
    hd = Retailer.objects.get(slug="home-depot")
    cr = Retailer.objects.get(slug="construrama")
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 3/8")
    sku_hd = RetailerProduct.objects.get(retailer=hd, canonical_product=canonico)
    sku_cr = RetailerProduct.objects.get(retailer=cr, canonical_product=canonico)
    return {"zona": zona, "sku_hd": sku_hd, "sku_cr": sku_cr}


def _crear_lista(client, headers=HDR_A, zone_id=None):
    body = {"name": "Mi obra"}
    if zone_id is not None:
        body["zone_id"] = str(zone_id)
    return client.post("/lists", json=body, headers=headers)


# --- Flujo completo ---------------------------------------------------------


@pytest.mark.django_db
def test_flujo_completo_crear_items_editar_quitar_detalle_borrar(client, seeded):
    """Crear lista, 2 ítems con snapshot, editar cantidad, quitar uno, detalle, borrar."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    sku_cr = seeded["sku_cr"]

    # Crear lista (201) con zona.
    r = _crear_lista(client, zone_id=zona.id)
    assert r.status_code == 201
    lista = r.json()
    assert set(lista.keys()) == {"id", "name", "zone_id", "created_at", "item_count"}
    assert lista["name"] == "Mi obra"
    assert lista["zone_id"] == str(zona.id)
    assert lista["item_count"] == 0
    list_id = lista["id"]

    # Aparece en GET /lists de la sesión.
    r = client.get("/lists", headers=HDR_A)
    assert r.status_code == 200
    assert [item["id"] for item in r.json()] == [list_id]

    # Agregar ítem 1 (HD, 10 piezas). Snapshot = última observación NATIVA seed
    # 3/8 HD (×1.030) = 20085.00 (la cotización usa precio nativo, F031 no la
    # normaliza). 10 × 20085.00 = 200850.00.
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 10},
        headers=HDR_A,
    )
    assert r.status_code == 201
    item1 = r.json()
    assert set(item1.keys()) == {
        "id",
        "retailer_product_id",
        "retailer",
        "product_name",
        "quantity",
        "captured_price",
        "captured_at",
        "line_total",
    }
    assert item1["retailer"]["slug"] == "home-depot"
    assert item1["captured_price"] == "20085.00"
    # F033: la última observación del seed es la FRESCA (captured_at ≈ ahora),
    # no la fija de 2026-06-13; el snapshot debe tomarla.
    assert item1["captured_at"] > "2026-06-13"
    assert item1["line_total"] == "200850.00"

    # Agregar ítem 2 (CR, 2 piezas). Snapshot = última observación NATIVA seed
    # 3/8 CR (×1.030) = 21.53. 2 × 21.53 = 43.06.
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_cr.id), "quantity": 2},
        headers=HDR_A,
    )
    assert r.status_code == 201
    item2 = r.json()
    assert item2["captured_price"] == "21.53"
    assert item2["line_total"] == "43.06"
    item2_id = item2["id"]

    # Editar cantidad del ítem 1: 10 -> 5.
    r = client.patch(
        f"/lists/{list_id}/items/{item1['id']}",
        json={"quantity": 5},
        headers=HDR_A,
    )
    assert r.status_code == 200
    assert r.json()["quantity"] == 5
    assert r.json()["line_total"] == "100425.00"  # 5 * 20085.00

    # Detalle con subtotal/total: 5*20085.00 + 2*21.53 = 100425.00 + 43.06 = 100468.06.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    assert r.status_code == 200
    detalle = r.json()
    assert set(detalle.keys()) == {
        "id",
        "name",
        "zone_id",
        "created_at",
        "item_count",
        "items",
        "subtotal",
        "total",
    }
    assert detalle["item_count"] == 2
    assert len(detalle["items"]) == 2
    assert detalle["subtotal"] == "100468.06"
    assert detalle["total"] == "100468.06"

    # Quitar el ítem 2 (204 sin body).
    r = client.delete(f"/lists/{list_id}/items/{item2_id}", headers=HDR_A)
    assert r.status_code == 204
    assert r.content in (b"", b"null")

    # Detalle de nuevo: solo queda el ítem 1, subtotal = 100425.00.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    assert r.status_code == 200
    detalle = r.json()
    assert detalle["item_count"] == 1
    assert detalle["subtotal"] == "100425.00"

    # Borrar la lista (204).
    r = client.delete(f"/lists/{list_id}", headers=HDR_A)
    assert r.status_code == 204

    # Ya no aparece.
    r = client.get("/lists", headers=HDR_A)
    assert r.json() == []
    # Y su detalle ahora es 404.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    assert r.status_code == 404


@pytest.mark.django_db
def test_patch_lista_actualiza_nombre_y_zona(client, seeded):
    """PATCH /lists/{id} actualiza nombre y zona de la lista de la sesión."""
    zona = seeded["zona"]
    list_id = _crear_lista(client).json()["id"]  # sin zona inicial

    r = client.patch(
        f"/lists/{list_id}",
        json={"name": "Obra renombrada", "zone_id": str(zona.id)},
        headers=HDR_A,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Obra renombrada"
    assert data["zone_id"] == str(zona.id)


# --- Snapshot inmutable -----------------------------------------------------


@pytest.mark.django_db
def test_snapshot_inmutable_ante_nueva_observacion(client, seeded):
    """Una nueva PriceObservation tras agregar NO cambia el captured_price del ítem."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]

    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
        headers=HDR_A,
    )
    assert r.status_code == 201
    item_id = r.json()["id"]
    precio_capturado = r.json()["captured_price"]
    # Snapshot NATIVO de la última observación seed 3/8 HD (×1.030) = 20085.00.
    assert precio_capturado == "20085.00"

    # Llega una observación MÁS reciente y mucho más cara.
    PriceObservation.objects.create(
        retailer_product=sku_hd,
        zone=zona,
        price=Decimal("99999.99"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    )

    # El detalle sigue mostrando el snapshot original, no el nuevo precio.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    item = next(i for i in r.json()["items"] if i["id"] == item_id)
    assert item["captured_price"] == "20085.00"
    assert r.json()["subtotal"] == "20085.00"


# --- Scoping por sesión -----------------------------------------------------


@pytest.mark.django_db
def test_scoping_sesion_b_no_ve_lista_de_a(client, seeded):
    """GET /lists de la sesión B no incluye listas de la sesión A."""
    _crear_lista(client, headers=HDR_A)
    r = client.get("/lists", headers=HDR_B)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.django_db
def test_scoping_sesion_b_no_accede_detalle_de_a(client, seeded):
    """La sesión B no puede ver el detalle de una lista de la sesión A → 404."""
    list_id = _crear_lista(client, headers=HDR_A).json()["id"]
    r = client.get(f"/lists/{list_id}", headers=HDR_B)
    assert r.status_code == 404


@pytest.mark.django_db
def test_scoping_sesion_b_no_modifica_lista_de_a(client, seeded):
    """La sesión B no puede PATCH/DELETE una lista de la sesión A → 404."""
    list_id = _crear_lista(client, headers=HDR_A).json()["id"]

    r = client.patch(f"/lists/{list_id}", json={"name": "hack"}, headers=HDR_B)
    assert r.status_code == 404
    r = client.delete(f"/lists/{list_id}", headers=HDR_B)
    assert r.status_code == 404
    # La lista de A sigue intacta.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    assert r.status_code == 200
    assert r.json()["name"] == "Mi obra"


@pytest.mark.django_db
def test_scoping_sesion_b_no_modifica_item_de_a(client, seeded):
    """La sesión B no puede tocar un ítem de la lista de la sesión A → 404."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, headers=HDR_A, zone_id=zona.id).json()["id"]
    item_id = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
        headers=HDR_A,
    ).json()["id"]

    r = client.patch(f"/lists/{list_id}/items/{item_id}", json={"quantity": 99}, headers=HDR_B)
    assert r.status_code == 404
    r = client.delete(f"/lists/{list_id}/items/{item_id}", headers=HDR_B)
    assert r.status_code == 404
    # El ítem de A sigue con su cantidad original.
    r = client.get(f"/lists/{list_id}", headers=HDR_A)
    assert r.json()["items"][0]["quantity"] == 1


# --- 400: falta el header ---------------------------------------------------


@pytest.mark.django_db
def test_sin_header_session_key_400_en_get(client, seeded):
    """GET /lists sin X-Session-Key → 400."""
    r = client.get("/lists")
    assert r.status_code == 400


@pytest.mark.django_db
def test_sin_header_session_key_400_en_post(client, seeded):
    """POST /lists sin X-Session-Key → 400."""
    r = client.post("/lists", json={"name": "x"})
    assert r.status_code == 400


@pytest.mark.django_db
def test_sin_header_session_key_400_en_items(client, seeded):
    """POST /lists/{id}/items sin X-Session-Key → 400 (no se crea nada)."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
    )
    assert r.status_code == 400


# --- 422: cantidad inválida / sin precio ------------------------------------


@pytest.mark.django_db
def test_quantity_cero_es_422(client, seeded):
    """POST item con quantity=0 → 422 (schema ge=1)."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 0},
        headers=HDR_A,
    )
    assert r.status_code == 422


@pytest.mark.django_db
def test_quantity_negativa_es_422(client, seeded):
    """POST item con quantity negativa → 422."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": -3},
        headers=HDR_A,
    )
    assert r.status_code == 422


@pytest.mark.django_db
def test_patch_item_quantity_invalida_es_422(client, seeded):
    """PATCH item con quantity=0 → 422."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]
    item_id = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
        headers=HDR_A,
    ).json()["id"]
    r = client.patch(f"/lists/{list_id}/items/{item_id}", json={"quantity": 0}, headers=HDR_A)
    assert r.status_code == 422


@pytest.mark.django_db
def test_agregar_item_sin_observacion_es_422(client, seeded):
    """Si el SKU no tiene ninguna observación → 422 'sin precio para snapshot'."""
    zona = seeded["zona"]
    sku_hd = seeded["sku_hd"]
    # Lista CON zona, pero el SKU no tiene observaciones en esa zona ni en ninguna.
    PriceObservation.objects.filter(retailer_product=sku_hd).delete()
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]

    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
        headers=HDR_A,
    )
    assert r.status_code == 422


# --- 404: recursos inexistentes ---------------------------------------------


@pytest.mark.django_db
def test_agregar_item_sku_inexistente_es_404(client, seeded):
    """POST item con retailer_product_id inexistente → 404."""
    zona = seeded["zona"]
    list_id = _crear_lista(client, zone_id=zona.id).json()["id"]
    fantasma = "00000000-0000-0000-0000-000000000000"
    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": fantasma, "quantity": 1},
        headers=HDR_A,
    )
    assert r.status_code == 404


@pytest.mark.django_db
def test_detalle_lista_inexistente_es_404(client, seeded):
    """GET /lists/{id} de una lista inexistente → 404."""
    fantasma = "00000000-0000-0000-0000-000000000000"
    r = client.get(f"/lists/{fantasma}", headers=HDR_A)
    assert r.status_code == 404


# --- Snapshot sin zona: usa la última observación disponible ----------------


@pytest.mark.django_db
def test_snapshot_sin_zona_usa_ultima_observacion_disponible(client, seeded):
    """Lista SIN zona: el snapshot usa la última observación sin zona del producto."""
    sku_hd = seeded["sku_hd"]
    # El seed asocia todas las observaciones a la zona; crea una sin zona, la más
    # reciente, para verificar que la rama "sin zona" la captura.
    PriceObservation.objects.create(
        retailer_product=sku_hd,
        zone=None,
        price=Decimal("123.45"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 30, 9, 0, tzinfo=UTC),
    )
    list_id = _crear_lista(client).json()["id"]  # sin zona

    r = client.post(
        f"/lists/{list_id}/items",
        json={"retailer_product_id": str(sku_hd.id), "quantity": 1},
        headers=HDR_A,
    )
    assert r.status_code == 201
    assert r.json()["captured_price"] == "123.45"
