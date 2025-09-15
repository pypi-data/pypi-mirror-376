from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Conservative defaults: (connect, read)
DEFAULT_TIMEOUT: tuple[float, float] = (3.05, 10.0)


@dataclass(frozen=True)
class HttpConfig:
    timeout: tuple[float, float] = DEFAULT_TIMEOUT
    total_retries: int = 3
    backoff_factor: float = 0.2
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504)


def _build_session(cfg: HttpConfig) -> Session:
    s = requests.Session()
    retry = Retry(
        total=cfg.total_retries,
        backoff_factor=cfg.backoff_factor,
        status_forcelist=cfg.status_forcelist,
        allowed_methods=frozenset({"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


class HttpClient:
    def __init__(self, cfg: HttpConfig | None = None) -> None:
        self.cfg = cfg or HttpConfig()
        self._session = _build_session(self.cfg)

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> Response:
        resp = self._session.get(
            url, params=params, headers=headers, timeout=timeout or self.cfg.timeout
        )
        resp.raise_for_status()
        return resp

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> Response:
        resp = self._session.post(
            url,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout or self.cfg.timeout,
        )
        resp.raise_for_status()
        return resp


# Convenience default client
default_http = HttpClient()
