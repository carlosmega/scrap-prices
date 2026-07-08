"""Management command `scrape` (F027): corre la ingestión de F025 a mano.

Envuelve la corrida de scraping respetuoso (F024/F025) en un comando cómodo y
seguro para lanzarla desde el entorno del humano. Comando delgado por diseño: la
lógica de ingestión vive en `apps.scraping.services` y la cortesía/stop-if-blocked
en `apps.scraping.client`; aquí solo se resuelven entidades por slug, se elige el
adapter del retailer y se reporta el resultado de forma legible.

Modos:
- `--dry-run`: hace el fetch REAL vía el adapter (PoliteClient) e IMPRIME los
  productos/precios que traería (sku, nombre, precio, disponibilidad) SIN escribir
  en la BD: no crea `PriceObservation`/`RetailerProduct` ni un `ScrapeRun`. Para
  no escribir, llama a `adapter.fetch_products_with_prices` (solo lectura), nunca
  a `services.ingest_homedepot`.
- sin `--dry-run`: ejecuta `services.ingest_homedepot` (crea `PriceObservation` +
  `ScrapeRun`) y reporta el resumen.

Guardrail §2.3 (stop-if-blocked): si el fetch lanza `RetailerBlockedError`
(403/429/challenge), el comando imprime el motivo y termina con código de error
(`CommandError`), SIN reintentar para evadir. El registro de adapters deja listo
el enganche de Construrama (F026) sin tocar el comando.
"""

from __future__ import annotations

from collections.abc import Callable

from django.core.management.base import BaseCommand, CommandError

from apps.geo.models import Retailer, RetailerLocation, Zone
from apps.scraping import services
from apps.scraping.base import BaseRetailerAdapter, RawPrice
from apps.scraping.construrama import ConstruramaAdapter
from apps.scraping.exceptions import RetailerBlockedError, ScrapeError
from apps.scraping.homedepot import HomeDepotAdapter

# Cuántos productos se listan en la salida legible (resumen, no volcado completo).
PREVIEW_LIMIT = 10

# Registro de adapters: retailer-slug -> función de ingestión (F025/F026). Añadir
# un retailer es agregar una entrada aquí (y su rama en `build_adapter`), sin tocar
# el flujo del comando. Un slug ausente => "adapter no disponible aún" (sin reventar).
INGEST_REGISTRY: dict[str, Callable[..., object]] = {
    "home-depot": services.ingest_homedepot,
    "construrama": services.ingest_construrama,
}


def build_adapter(slug: str) -> BaseRetailerAdapter:
    """Crea el adapter de retailer para un slug con su `PoliteClient` honesto.

    Seam de testeo: los tests parchean esta función para inyectar un adapter
    sobre `httpx.MockTransport` (sin red real). Solo se llama para slugs que sí
    tienen adapter (los del `INGEST_REGISTRY`).
    """
    if slug == "home-depot":
        return HomeDepotAdapter()
    if slug == "construrama":
        return ConstruramaAdapter()
    raise CommandError(f"No hay adapter construible para el retailer '{slug}'.")


class Command(BaseCommand):
    help = (
        "Corre la ingestión de scraping respetuoso (F025) para un retailer/zona/"
        "categoría. Con --dry-run hace el fetch real e imprime lo que traería sin "
        "escribir en la BD."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--retailer",
            required=True,
            help="Slug del retailer a scrapear (p.ej. home-depot).",
        )
        parser.add_argument(
            "--zone",
            required=True,
            help="Slug de la zona interna a scrapear (p.ej. monterrey-metro).",
        )
        parser.add_argument(
            "--category",
            default="varilla",
            help="Término/categoría a buscar (default: varilla).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch real e imprime lo que traería, SIN escribir en la BD.",
        )

    def handle(self, *args, **options) -> None:
        retailer_slug: str = options["retailer"]
        zone_slug: str = options["zone"]
        category: str = options["category"]
        dry_run: bool = options["dry_run"]

        retailer = self._resolver_retailer(retailer_slug)
        zone = self._resolver_zone(zone_slug)
        location = self._resolver_primary_location(retailer, zone)

        ingest = INGEST_REGISTRY.get(retailer.slug)
        if ingest is None:
            # Slug conocido pero sin adapter (p.ej. construrama hoy, F026): no es
            # un error de programa ni un stacktrace; es un estado esperado.
            self.stdout.write(
                self.style.WARNING(
                    f"Adapter no disponible aún para el retailer '{retailer.slug}'. "
                    "No se ejecuta ninguna corrida."
                )
            )
            return

        adapter = build_adapter(retailer.slug)

        self.stdout.write(
            f"Retailer: {retailer.name} ({retailer.slug}) · "
            f"Zona: {zone.name} ({zone.slug}) · "
            f"Tienda: {location.name} (external_id={location.external_id}) · "
            f"Categoría: {category}"
        )

        if dry_run:
            self._ejecutar_dry_run(adapter, zone, location, category)
        else:
            self._ejecutar_ingestion(ingest, adapter, zone, location, category)

    # -- resolución de entidades --------------------------------------------
    def _resolver_retailer(self, slug: str) -> Retailer:
        try:
            return Retailer.objects.get(slug=slug)
        except Retailer.DoesNotExist as exc:
            raise CommandError(
                f"No existe un Retailer con slug '{slug}'. "
                "Revisa los slugs sembrados (p.ej. corre `manage.py seed`)."
            ) from exc

    def _resolver_zone(self, slug: str) -> Zone:
        try:
            return Zone.objects.get(slug=slug)
        except Zone.DoesNotExist as exc:
            raise CommandError(
                f"No existe una Zone con slug '{slug}'. "
                "Revisa los slugs sembrados (p.ej. corre `manage.py seed`)."
            ) from exc

    def _resolver_primary_location(self, retailer: Retailer, zone: Zone) -> RetailerLocation:
        """Devuelve la `RetailerLocation` primaria del retailer que sirve la zona.

        La resolución vive en `services.resolver_primary_location` (F033: la
        comparte con la búsqueda en vivo). Si no hay ninguna, es un error de
        datos (no de programa): `CommandError` con mensaje claro, no un
        stacktrace.
        """
        location = services.resolver_primary_location(retailer, zone)
        if location is None:
            raise CommandError(
                f"No hay una RetailerLocation primaria de '{retailer.slug}' que "
                f"sirva la zona '{zone.slug}' (falta un ZoneLocationMap is_primary). "
                "Revisa el mapeo de la zona o corre `manage.py seed`."
            )
        return location

    # -- modos ---------------------------------------------------------------
    def _ejecutar_dry_run(
        self,
        adapter: BaseRetailerAdapter,
        zone: Zone,
        location: RetailerLocation,
        category: str,
    ) -> None:
        """Fetch real + impresión, SIN escribir nada en la BD.

        Usa `fetch_products_with_prices` (solo lectura del adapter): NO llama a
        `ingest_homedepot`, así que es imposible que cree `PriceObservation`/
        `RetailerProduct` ni un `ScrapeRun`. El stop-if-blocked aplica igual.
        """
        self.stdout.write(self.style.WARNING("DRY-RUN: no se escribirá nada en la BD."))
        try:
            precios = adapter.fetch_products_with_prices(category, location)
        except RetailerBlockedError as exc:
            self._reportar_bloqueo(exc)
        except ScrapeError as exc:
            self._reportar_scrape_error(exc)
        finally:
            self._cerrar_adapter(adapter)

        self.stdout.write(f"Productos que se traerían: {len(precios)}")
        self._imprimir_precios(precios)

    def _ejecutar_ingestion(
        self,
        ingest: Callable[..., object],
        adapter: BaseRetailerAdapter,
        zone: Zone,
        location: RetailerLocation,
        category: str,
    ) -> None:
        """Corrida real: delega en la ingestión (PriceObservation + ScrapeRun)."""
        try:
            run = ingest(zone, location, category, adapter=adapter)
        except RetailerBlockedError as exc:
            self._reportar_bloqueo(exc)
        except ScrapeError as exc:
            self._reportar_scrape_error(exc)
        finally:
            self._cerrar_adapter(adapter)

        estilo = self.style.SUCCESS if run.status == "ok" else self.style.WARNING
        self.stdout.write(
            estilo(f"Corrida {run.status}: {run.items_found} items (ScrapeRun {run.pk}).")
        )
        if run.errors:
            self.stdout.write(self.style.WARNING(f"Errores: {len(run.errors)}"))
            for error in run.errors[:PREVIEW_LIMIT]:
                self.stdout.write(f"  - {error}")

    # -- salida legible ------------------------------------------------------
    def _imprimir_precios(self, precios: list[RawPrice]) -> None:
        for precio in precios[:PREVIEW_LIMIT]:
            disponibilidad = "disponible" if precio.is_available else "agotado"
            self.stdout.write(
                f"  [{precio.sku}] {precio.raw_name} — "
                f"{precio.price} {precio.currency} ({disponibilidad})"
            )
        restantes = len(precios) - PREVIEW_LIMIT
        if restantes > 0:
            self.stdout.write(f"  ... y {restantes} más.")

    def _reportar_bloqueo(self, exc: RetailerBlockedError) -> None:
        """stop-if-blocked: reporta el bloqueo y sale con error, SIN evadir."""
        raise CommandError(
            f"Retailer bloqueó la corrida (status {exc.status_code}): {exc}. "
            "stop-if-blocked: nos detenemos sin reintentar ni evadir."
        )

    def _reportar_scrape_error(self, exc: ScrapeError) -> None:
        """Detiene la corrida por un error de fetch (p.ej. falta la search key).

        Es un STOP limpio del guardrail (no un bug de mapeo): el mapeo de la zona
        ya se resolvió antes de llegar aquí. Se surface como `CommandError` con el
        motivo, sin stacktrace.
        """
        raise CommandError(f"No se pudo completar el fetch del retailer (guardrail): {exc}")

    def _cerrar_adapter(self, adapter: BaseRetailerAdapter) -> None:
        cerrar = getattr(adapter, "close", None)
        if callable(cerrar):
            cerrar()
