"""Registro en Django Admin del catálogo (F007).

Flujo de curación (PRD D1): en el listado de `RetailerProduct` se filtra por
`match_status=unmatched` y `retailer`, se busca por `raw_name`/`external_sku`, y
se asigna el `CanonicalProduct` — bien editando la fila (FK editable en el
listado y en el formulario), bien con la acción masiva, que marca el match como
`manual`.
"""

from django.contrib import admin

from apps.catalog.models import CanonicalProduct, Category, RetailerProduct


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CanonicalProduct)
class CanonicalProductAdmin(admin.ModelAdmin):
    # F031: mass_kg visible y editable en el listado para curar el factor de
    # conversión (peso de la pieza canónica) que habilita la normalización.
    list_display = ("name", "category", "unit", "mass_kg", "is_active")
    list_filter = ("category", "unit", "is_active")
    list_editable = ("mass_kg",)
    search_fields = ("name",)
    autocomplete_fields = ("category",)


@admin.register(RetailerProduct)
class RetailerProductAdmin(admin.ModelAdmin):
    list_display = (
        "raw_name",
        "retailer",
        "external_sku",
        "canonical_product",
        "sale_unit",
        "match_status",
        "match_confidence",
        "is_active",
    )
    list_filter = ("match_status", "retailer", "sale_unit", "is_active")
    search_fields = ("raw_name", "external_sku", "brand")
    # FK y sale_unit editables directamente en el listado para curar sin abrir
    # cada fila (F031: la unidad de venta habilita la normalización).
    list_editable = ("canonical_product", "sale_unit")
    autocomplete_fields = ("canonical_product",)
    actions = ("asignar_a_canonico_manual",)

    @admin.action(description="Marcar match como manual (asignación curada)")
    def asignar_a_canonico_manual(self, request, queryset):
        """Marca como `manual` los SKUs ya enlazados a un canónico.

        Pensada para confirmar en bloque tras enlazar varios `RetailerProduct`
        a su `CanonicalProduct`: solo afecta a los que tienen canónico asignado.
        """
        updated = queryset.exclude(canonical_product__isnull=True).update(
            match_status=RetailerProduct.MatchStatus.MANUAL,
        )
        self.message_user(request, f"{updated} producto(s) marcados como match manual.")
