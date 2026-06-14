"""Schemas de entrada/salida de las listas de cotización (F017). El contrato vive aquí.

La frontera de datos de los 8 endpoints CRUD de `/api/lists`:
- salidas (`UserListOut`, `UserListItemOut`, `UserListDetailOut`) con shapes EXACTAS
  de la spec (PRD §12); los `Decimal` monetarios se serializan como string para no
  perder exactitud (PRD §8);
- entradas (`UserListCreateIn`, `UserListPatchIn`, `UserListItemCreateIn`,
  `UserListItemPatchIn`) con validación de `quantity >= 1` (422 si 0/negativo).

El router (`api.py`) no inventa dicts: todo lo que entra/sale pasa por estos schemas.
"""

from datetime import datetime
from decimal import Decimal

from ninja import Schema
from pydantic import Field

from apps.catalog.schemas import RetailerRefOut


class UserListOut(Schema):
    """Lista de cotización (resumen): metadatos + conteo de ítems.

    `zone_id` es None cuando la lista aún no tiene zona asignada. `item_count`
    es la cantidad de ítems (filas), no la suma de cantidades.
    """

    id: str
    name: str
    zone_id: str | None = None
    created_at: datetime
    item_count: int


class UserListItemOut(Schema):
    """Ítem de una lista: SKU, cantidad y snapshot inmutable del precio.

    `captured_price`/`captured_at` son el snapshot que se fijó al agregar el ítem
    y NUNCA cambian después (CA2 de C1). `line_total = quantity * captured_price`.
    Los `Decimal` se serializan como string por exactitud monetaria (PRD §8).
    """

    id: str
    retailer_product_id: str
    retailer: RetailerRefOut
    product_name: str
    quantity: int
    captured_price: Decimal
    captured_at: datetime
    line_total: Decimal


class UserListDetailOut(UserListOut):
    """Detalle de una lista: el resumen + sus ítems y los totales calculados.

    `subtotal`/`total` reutilizan `services.subtotal_lista` (F009); en el MVP no
    hay impuestos ni envío, así que `total == subtotal`. Decimales como string.
    """

    items: list[UserListItemOut]
    subtotal: Decimal
    total: Decimal


class UserListCreateIn(Schema):
    """Cuerpo de POST /lists: nombre obligatorio y zona opcional."""

    name: str
    zone_id: str | None = None


class UserListPatchIn(Schema):
    """Cuerpo de PATCH /lists/{id}: campos opcionales (parcial).

    `zone_id` admite tres estados: ausente (no tocar), una zona, o None explícito
    (desasignar la zona).
    """

    name: str | None = None
    zone_id: str | None = None


class UserListItemCreateIn(Schema):
    """Cuerpo de POST /lists/{id}/items: SKU + cantidad (>= 1)."""

    retailer_product_id: str
    quantity: int = Field(default=1, ge=1)


class UserListItemPatchIn(Schema):
    """Cuerpo de PATCH /lists/{id}/items/{item_id}: nueva cantidad (>= 1)."""

    quantity: int = Field(ge=1)
