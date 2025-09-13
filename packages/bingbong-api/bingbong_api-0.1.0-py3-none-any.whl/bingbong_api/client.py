from __future__ import annotations
import os
from typing import Any, Optional
from .exceptions import MissingAPIKeyError

DEFAULT_BASE_URL = "https://api.bingbong.com"  # placeholder


class MockResponse:
    """Minimal stand-in for requests.Response so examples don't error."""

    def __init__(self, method: str, url: str, *, params=None, json=None, headers=None):
        self.method = method
        self.url = url
        self.params = params or {}
        self.json_payload = json
        self.headers = headers or {}
        self.status_code = 200
        self._text = (
            f"[MOCK RESPONSE]\\n"
            f"method={method} url={url}\\n"
            f"params={self.params}\\n"
            f"json={self.json_payload}\\n"
            f"headers={self.headers}\\n"
        )

    def json(self) -> dict[str, Any]:
        return {
            "mock": True,
            "method": self.method,
            "url": self.url,
            "params": self.params,
            "json": self.json_payload,
        }

    @property
    def text(self) -> str:
        return self._text

    def __repr__(self) -> str:
        return f"<MockResponse [{self.status_code}] {self.method} {self.url}>"


class BingBongClient:
    """A tiny client for the BingBong API scaffold."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._api_key = api_key or os.getenv("BINGBONG_API_KEY")
        if not self._api_key:
            raise MissingAPIKeyError()

        self.base_url = base_url.rstrip("/")

    # --- internal ---
    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "bingbong-api-python/0.1.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> MockResponse:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = self._auth_headers()
        # Instead of a real HTTP request, just return a mock
        resp = MockResponse(method, url, params=params, json=json, headers=headers)
        print(resp.text)  # print what would have been sent
        return resp

    # --- placeholder endpoints ---
    def get_placeholder(self, resource: str = "status", *, params=None) -> MockResponse:
        path = f"v1/{resource}"
        return self._request("GET", path, params=params)

    def post_placeholder(self, resource: str = "echo", *, json=None, params=None) -> MockResponse:
        path = f"v1/{resource}"
        return self._request("POST", path, params=params, json=json)

    # --- context management (no network session needed) ---
    def close(self) -> None:
        pass

    def __enter__(self) -> "BingBongClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
