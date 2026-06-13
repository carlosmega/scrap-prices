"""Schemas de entrada/salida de la app core. El contrato vive aquí."""

from ninja import Schema


class HealthOut(Schema):
    """Respuesta del endpoint de salud."""

    status: str
