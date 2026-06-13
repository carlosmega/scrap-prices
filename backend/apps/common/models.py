"""Modelos base reutilizables por todo el dominio (F006+).

La base abstracta `TimeStampedUUIDModel` es el contrato común que heredan
todas las entidades de dominio: PK UUID, timestamps automáticos y soft-delete
(`is_active`). Convención del equipo estilo CDS/Dynamics (PRD §8).
"""

import uuid

from django.db import models


class TimeStampedUUIDModel(models.Model):
    """Base abstracta: PK UUID + timestamps automáticos + soft-delete.

    Heredan de aquí todas las entidades de dominio (F007–F009). No crea tabla
    propia (`abstract = True`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
