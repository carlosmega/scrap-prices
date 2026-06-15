"""Excepciones del subsistema de scraping.

La distinción entre `TransientScrapeError` y `RetailerBlockedError` es la
columna vertebral del guardrail ético del PRD §2.3:

- Un error **transitorio** (timeout, 5xx, fallo de red) es ruido del transporte:
  se puede reintentar con backoff porque NO es una señal de que el retailer nos
  esté rechazando deliberadamente.
- Un **bloqueo** (`403`/`429`/challenge/captcha) es una señal explícita de "no
  queremos que entres". La respuesta correcta y deliberada es DETENERSE
  (`stop-if-blocked`): NO reintentar para forzar, NO rotar identidad/UA, NO
  resolver captchas, NO falsear fingerprint. El llamador marca el retailer
  `non_viable` (guardrail §2.3.1/2.3.7).
"""


class ScrapeError(Exception):
    """Raíz de los errores de scraping."""


class TransientScrapeError(ScrapeError):
    """Error transitorio del transporte: timeout, 5xx o fallo de red.

    Es el ÚNICO tipo de error que el cliente reintenta (con backoff exponencial
    vía tenacity). No implica rechazo deliberado del retailer.
    """


class RetailerBlockedError(ScrapeError):
    """El retailer nos bloqueó (`403`/`429`/challenge/captcha).

    Guardrail §2.3 cableado en código: ante un bloqueo, el cliente DETIENE la
    corrida lanzando esta excepción. Es deliberado que NO se reintente, NO se
    rote identidad/UA, NO se resuelva el captcha y NO se falsee fingerprint.
    Reintentar o evadir aquí sería violar el principio ético del proyecto; por
    eso esta excepción NO hereda de `TransientScrapeError` y queda fuera de la
    política de reintentos de tenacity.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
