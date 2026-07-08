"""Cliente HTTP respetuoso para scraping (F024) — guardrails §2.3 en código.

Este módulo es donde los principios éticos del PRD §2.3 dejan de ser prosa y se
vuelven comportamiento verificable:

1. **User-Agent honesto** (`SCRAPER_USER_AGENT`): identifica a ConstruScan y deja
   un contacto. NUNCA se imita un navegador real para engañar.
2. **Rate-limit por dominio**: entre dos peticiones al mismo dominio se espera al
   menos `SCRAPER_MIN_DELAY_SECONDS`, y un semáforo limita la concurrencia por
   dominio. La cortesía es el comportamiento por defecto, no una opción.
3. **Reintentos** (tenacity, backoff exponencial) SOLO para errores transitorios
   (timeout / 5xx / fallo de red), que son ruido del transporte.
4. **stop-if-blocked (NO evasión):** ante `403`/`429` o un challenge/captcha se
   lanza `RetailerBlockedError` y la corrida se DETIENE. Es deliberado que aquí
   NO se reintente, NO se rote identidad/UA, NO se resuelva captcha y NO se
   falsee fingerprint. Reintentar o disimular sería violar el guardrail.

El cliente es síncrono a propósito: en MVP las corridas son tasks Celery
secuenciales y un cliente sync es trivial de testear de forma determinista
(reloj y sleep inyectables, transporte mockeado). No pega a ninguna URL real en
tests; recibe un `transport` de httpx que se puede sustituir por
`httpx.MockTransport`.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Callable
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from apps.scraping.exceptions import RetailerBlockedError, TransientScrapeError

# Códigos que significan "el retailer te está rechazando deliberadamente".
# Ante cualquiera de estos se DETIENE (stop-if-blocked), no se reintenta.
BLOCKED_STATUS_CODES = frozenset({403, 429})


def _is_challenge_response(response: httpx.Response) -> bool:
    """Heurística mínima para detectar un challenge/captcha (anti-bot).

    No intenta resolverlo ni esquivarlo: solo lo RECONOCE para poder detenerse.
    Señales típicas: cabeceras de servicios anti-bot o un cuerpo HTML con un
    captcha. Es a propósito conservadora: ante la duda, mejor detenerse.
    """
    server = response.headers.get("server", "").lower()
    if "cloudflare" in server and response.status_code in {403, 503}:
        return True
    if response.headers.get("cf-mitigated", "").lower() == "challenge":
        return True
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" in content_type:
        body = response.text.lower()
        markers = ("captcha", "are you a robot", "verify you are human", "px-captcha")
        if any(marker in body for marker in markers):
            return True
    return False


class PoliteClient:
    """Cliente HTTP cortés y con guardrails para scraping (§2.3).

    Pensado para usarse por composición desde cada adapter. La política es
    inmutable durante la vida del cliente: no expone forma de desactivar el
    rate-limit ni de reintentar un bloqueo.
    """

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        min_delay_seconds: float | None = None,
        timeout_seconds: float | None = None,
        max_concurrency_per_domain: int | None = None,
        max_retries: int | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.user_agent = user_agent or settings.SCRAPER_USER_AGENT
        self.min_delay_seconds = (
            settings.SCRAPER_MIN_DELAY_SECONDS if min_delay_seconds is None else min_delay_seconds
        )
        self.timeout_seconds = (
            settings.SCRAPER_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        concurrency = (
            settings.SCRAPER_MAX_CONCURRENCY_PER_DOMAIN
            if max_concurrency_per_domain is None
            else max_concurrency_per_domain
        )
        self.max_concurrency_per_domain = max(1, concurrency)
        self.max_retries = settings.SCRAPER_MAX_RETRIES if max_retries is None else max_retries
        # `sleep`/`monotonic` inyectables: en tests se sustituyen por un reloj
        # falso para verificar el delay sin esperar en tiempo real.
        self._sleep = sleep
        self._monotonic = monotonic

        self._client = httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout_seconds,
            transport=transport,
            follow_redirects=True,
        )

        # Estado del rate-limiter por dominio.
        self._state_lock = threading.Lock()
        self._domain_locks: dict[str, threading.Semaphore] = {}
        self._domain_next_allowed: dict[str, float] = defaultdict(float)

    # -- ciclo de vida -------------------------------------------------------
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PoliteClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- rate-limit por dominio ---------------------------------------------
    def _semaphore_for(self, domain: str) -> threading.Semaphore:
        with self._state_lock:
            sem = self._domain_locks.get(domain)
            if sem is None:
                sem = threading.Semaphore(self.max_concurrency_per_domain)
                self._domain_locks[domain] = sem
            return sem

    def _wait_for_domain(self, domain: str) -> None:
        """Espera hasta que esté permitido pegarle de nuevo a `domain`.

        Garantiza ≥ `min_delay_seconds` entre el inicio de dos peticiones al
        mismo dominio. Usa el reloj monotónico inyectable; en tests un reloj
        falso demuestra que efectivamente se duerme el delay.
        """
        with self._state_lock:
            now = self._monotonic()
            next_allowed = self._domain_next_allowed[domain]
            wait = next_allowed - now
            # Reserva ya el próximo slot para que peticiones concurrentes se
            # serialicen correctamente respecto del delay.
            start = max(now, next_allowed)
            self._domain_next_allowed[domain] = start + self.min_delay_seconds
        if wait > 0:
            self._sleep(wait)

    # -- política de reintentos ---------------------------------------------
    def _retrying(self) -> Retrying:
        """Política tenacity: backoff exponencial SOLO ante errores transitorios.

        `RetailerBlockedError` NO está en `retry_if_exception_type`, así que un
        bloqueo se propaga al primer intento: no se reintenta para forzar la
        entrada (stop-if-blocked, §2.3).
        """
        return Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception_type(TransientScrapeError),
            sleep=self._sleep,
            reraise=True,
        )

    # -- petición ------------------------------------------------------------
    def get(self, url: str, **kwargs: object) -> httpx.Response:
        """GET cortés a `url` con rate-limit, reintentos y stop-if-blocked.

        - Espera el delay del dominio antes de cada intento (cortesía real,
          también entre reintentos).
        - Reintenta SOLO errores transitorios (timeout/5xx/red) con backoff.
        - Ante 403/429/challenge lanza `RetailerBlockedError` y se detiene: no
          reintenta, no rota UA/identidad, no resuelve captcha, no evade.
        """
        return self._send("GET", url, **kwargs)

    def post(self, url: str, **kwargs: object) -> httpx.Response:
        """POST cortés a `url` con las MISMAS garantías que `get`.

        Necesario para APIs que solo aceptan POST (p.ej. la Query API de Algolia
        de Construrama, F026: el cuerpo de la búsqueda viaja como JSON). Aplica
        idéntica cortesía (rate-limit por dominio), reintentos de transitorios y
        stop-if-blocked; ni el método POST relaja ningún guardrail.
        """
        return self._send("POST", url, **kwargs)

    def _send(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        """Núcleo común de `get`/`post`: rate-limit + reintentos + stop-if-blocked."""
        domain = urlsplit(url).netloc
        semaphore = self._semaphore_for(domain)

        with semaphore:
            for attempt in self._retrying():
                with attempt:
                    self._wait_for_domain(domain)
                    return self._do_request(method, url, **kwargs)
        raise AssertionError("unreachable")  # pragma: no cover

    def _do_request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        try:
            response = self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            # Timeout: transitorio → se reintenta con backoff.
            raise TransientScrapeError(f"Timeout pidiendo {url}: {exc}") from exc
        except httpx.TransportError as exc:
            # Fallo de red (conexión, DNS, etc.): transitorio → se reintenta.
            raise TransientScrapeError(f"Error de red pidiendo {url}: {exc}") from exc

        self._raise_for_block_or_transient(response)
        return response

    @staticmethod
    def _raise_for_block_or_transient(response: httpx.Response) -> None:
        """Traduce el status a la excepción correcta (bloqueo vs. transitorio).

        El orden importa: el BLOQUEO se evalúa primero y se DETIENE. Nunca se
        intenta evadir; reconocer el bloqueo es justamente para parar.
        """
        status = response.status_code
        if status in BLOCKED_STATUS_CODES or _is_challenge_response(response):
            raise RetailerBlockedError(
                f"Retailer bloqueó la petición a {response.request.url} "
                f"(status {status}). stop-if-blocked: nos detenemos sin evadir.",
                status_code=status,
            )
        if status >= 500:
            # 5xx: transitorio del servidor → se reintenta con backoff.
            raise TransientScrapeError(f"Error transitorio {status} en {response.request.url}")
        # 4xx que no sea bloqueo (404, 400, ...) no se reintenta: es un error
        # legítimo de la petición. Se devuelve para que el adapter lo maneje.


def build_polite_client(**overrides: object) -> PoliteClient:
    """Construye un `PoliteClient` con los defaults de settings.

    Punto único de creación para los adapters; los `overrides` permiten a los
    tests inyectar reloj/sleep/transport falsos.
    """
    return PoliteClient(**overrides)  # type: ignore[arg-type]
