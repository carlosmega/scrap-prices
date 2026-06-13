"""Registro en Django Admin de listas de cotización (F009).

Inspección interna del carrito anónimo: en el detalle de `UserList` se ven sus
`UserListItem` como inline (cantidad + snapshot de precio). El listado filtra por
estado/zona y busca por `session_key`/`name`.
"""

from django.contrib import admin

from apps.lists.models import UserList, UserListItem


class UserListItemInline(admin.TabularInline):
    model = UserListItem
    extra = 0
    autocomplete_fields = ("retailer_product",)
    fields = ("retailer_product", "quantity", "captured_price", "captured_at", "notes")


@admin.register(UserList)
class UserListAdmin(admin.ModelAdmin):
    list_display = ("name", "session_key", "zone", "status", "is_active", "created_at")
    list_filter = ("status", "zone", "is_active")
    search_fields = ("session_key", "name")
    ordering = ("-created_at",)
    inlines = (UserListItemInline,)


@admin.register(UserListItem)
class UserListItemAdmin(admin.ModelAdmin):
    list_display = (
        "user_list",
        "retailer_product",
        "quantity",
        "captured_price",
        "captured_at",
    )
    list_filter = ("retailer_product__retailer",)
    search_fields = (
        "user_list__session_key",
        "user_list__name",
        "retailer_product__raw_name",
    )
    autocomplete_fields = ("retailer_product",)
    ordering = ("-created_at",)
