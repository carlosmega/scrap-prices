"""Management command `seed` (F013): siembra datos demo idempotentes.

Comando delgado por diseño: toda la lógica de armado del grafo (Monterrey
Metro · varilla) vive en `apps.core.services.seed_demo`. Aquí solo se invoca y
se reporta el resumen. Correrlo varias veces no duplica filas (idempotente).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core import services


class Command(BaseCommand):
    help = "Siembra datos demo (Monterrey Metro · varilla). Idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        resumen = services.seed_demo()
        self.stdout.write(self.style.SUCCESS("Seed demo aplicado (idempotente)."))
        for clave, valor in resumen.items():
            self.stdout.write(f"  {clave}: {valor}")
