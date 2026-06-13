"""Modelos de listas de cotización anónimas (F009, PRD §8, adaptado a sesión).

La "lista de cotización" es el carrito propio del usuario: agrega productos con
cantidad y guarda un **snapshot** del precio al momento de agregarlos (no cambia
si el precio luego cambia en el catálogo). Por **decisión de producto, el MVP es
anónimo/sesión**: la lista se identifica por un `session_key`, sin login ni
`User` de Django obligatorio (el login propio se difiere a fase posterior; si se
añade, será un FK→User null que no rompe este contrato).

Esta feature solo modela las entidades: no implementa endpoints Ninja de
listas/ítems (M4) ni cálculo de totales como endpoint (el subtotal se deriva en
`services.py`).

Todas las entidades heredan de `TimeStampedUUIDModel` (apps.common.models).
"""

from django.db import models

from apps.catalog.models import RetailerProduct
from apps.common.models import TimeStampedUUIDModel
from apps.geo.models import Zone


class UserList(TimeStampedUUIDModel):
    """Lista de cotización propia de una sesión anónima (carrito del usuario).

    Se identifica por `session_key` (provisto por el frontend/sesión en M4; aquí
    solo se modela e indexa). No hay `user_fk` en MVP: las listas son anónimas.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Abierta"
        CLOSED = "closed", "Cerrada"

    # Identifica la sesión anónima propietaria. Indexado: la consulta caliente
    # de M4 es "mis listas por session_key".
    session_key = models.CharField(max_length=120, db_index=True)
    name = models.CharField(max_length=200, blank=True, default="Mi cotización")
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_lists",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.session_key})"


class UserListItem(TimeStampedUUIDModel):
    """Ítem de una lista: un `RetailerProduct` con cantidad y snapshot de precio.

    `captured_price`/`captured_at` se copian explícitamente al crear el ítem y
    nunca se releen en vivo del `RetailerProduct`: son el corazón de la garantía
    de snapshot (CA2 de C1). Cambiar el precio del SKU o sus observaciones no
    altera el `captured_price` del ítem.
    """

    user_list = models.ForeignKey(
        UserList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    retailer_product = models.ForeignKey(
        RetailerProduct,
        on_delete=models.CASCADE,
        related_name="list_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    # Snapshot del precio al momento de agregar (Decimal, nunca float, por
    # exactitud monetaria — PRD §8). No se relee del catálogo.
    captured_price = models.DecimalField(max_digits=12, decimal_places=2)
    # Snapshot del momento de agregado (lo fija quien crea el ítem); distinto de
    # created_at, que es cuándo se insertó la fila.
    captured_at = models.DateTimeField()
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.quantity} × {self.retailer_product} @ {self.captured_price}"
