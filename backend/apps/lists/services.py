"""Lógica de negocio de listas de cotización (F009). Sin HTTP, sin routers.

El cálculo del subtotal de una lista vive aquí (no en el modelo ni en un router):
es lógica de dominio. En M4 los endpoints de listas delegarán en estos helpers.
"""

from decimal import Decimal

from apps.lists.models import UserList


def subtotal_lista(user_list: UserList) -> Decimal:
    """Suma `quantity * captured_price` de todos los ítems de la lista.

    Usa el `captured_price` (snapshot) de cada ítem, nunca el precio en vivo del
    catálogo. Devuelve Decimal("0.00") si la lista no tiene ítems.
    """
    total = Decimal("0.00")
    for item in user_list.items.all():
        total += item.captured_price * item.quantity
    return total
