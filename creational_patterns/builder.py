"""
Builder — Creational Design Pattern

Separates the construction of a complex object from its final representation.
The builder assembles the product step by step; an optional Director encodes
canned construction recipes by calling steps in a specific order.

Key characteristics:
  - Construction is incremental — each step configures one aspect of the product
  - The same builder interface can produce different representations
  - The product is only retrieved at the end via build(); calling it earlier
    would yield an incomplete object
  - Step methods return self for a fluent (chaining) interface

Contrast with Factory Method / Abstract Factory: those decide *which class*
to instantiate and create the object in a single step. Builder hides *how*
a single complex object is assembled step by step — used when a constructor
with many optional parameters would become unwieldy (telescoping constructors).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class HttpMethod(str, Enum):
    GET    = "GET"
    POST   = "POST"
    PUT    = "PUT"
    PATCH  = "PATCH"
    DELETE = "DELETE"


@dataclass
class HttpRequest:
    """The complex object produced by the builder."""
    method:  HttpMethod
    url:     str
    headers: dict[str, str]  = field(default_factory=dict)
    params:  dict[str, str]  = field(default_factory=dict)
    body:    Any             = None
    timeout: int             = 30   # seconds
    retries: int             = 0

    def __str__(self) -> str:
        lines = [f"{self.method.value} {self.url}"]
        if self.params:
            query = "&".join(f"{k}={v}" for k, v in self.params.items())
            lines[0] += f"?{query}"
        for k, v in self.headers.items():
            lines.append(f"  {k}: {v}")
        if self.body is not None:
            lines.append(f"  Body: {self.body}")
        lines.append(f"  timeout={self.timeout}s  retries={self.retries}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class HttpRequestBuilder:
    """
    Fluent builder for HttpRequest. Each step method returns self so calls
    can be chained. Call build() once all desired steps are complete.
    """

    def __init__(self, method: HttpMethod, url: str) -> None:
        self._method:  HttpMethod       = method
        self._url:     str              = url
        self._headers: dict[str, str]  = {}
        self._params:  dict[str, str]  = {}
        self._body:    Any             = None
        self._timeout: int             = 30
        self._retries: int             = 0

    # --- step methods ---

    def header(self, key: str, value: str) -> HttpRequestBuilder:
        self._headers[key] = value
        return self

    def param(self, key: str, value: str) -> HttpRequestBuilder:
        self._params[key] = value
        return self

    def body(self, payload: Any) -> HttpRequestBuilder:
        self._body = payload
        return self

    def bearer_auth(self, token: str) -> HttpRequestBuilder:
        return self.header("Authorization", f"Bearer {token}")

    def json_content(self) -> HttpRequestBuilder:
        return self.header("Content-Type", "application/json")

    def timeout(self, seconds: int) -> HttpRequestBuilder:
        if seconds <= 0:
            raise ValueError("Timeout must be positive")
        self._timeout = seconds
        return self

    def retries(self, count: int) -> HttpRequestBuilder:
        if count < 0:
            raise ValueError("Retry count cannot be negative")
        self._retries = count
        return self

    def build(self) -> HttpRequest:
        """Materialise the product. The builder can be reused after calling this."""
        return HttpRequest(
            method=self._method,
            url=self._url,
            headers=dict(self._headers),
            params=dict(self._params),
            body=self._body,
            timeout=self._timeout,
            retries=self._retries,
        )


# Convenience factory functions so callers read like plain English
def GET(url: str)   -> HttpRequestBuilder: return HttpRequestBuilder(HttpMethod.GET,    url)
def POST(url: str)  -> HttpRequestBuilder: return HttpRequestBuilder(HttpMethod.POST,   url)
def PUT(url: str)   -> HttpRequestBuilder: return HttpRequestBuilder(HttpMethod.PUT,    url)
def PATCH(url: str) -> HttpRequestBuilder: return HttpRequestBuilder(HttpMethod.PATCH,  url)
def DELETE(url: str)-> HttpRequestBuilder: return HttpRequestBuilder(HttpMethod.DELETE, url)


# ---------------------------------------------------------------------------
# Director — encodes canned construction recipes
# ---------------------------------------------------------------------------

class ApiClientDirector:
    """
    Optional. Knows how to drive the builder to produce standard request
    shapes used repeatedly across the codebase. Client code can use the
    director for convenience, or drive the builder directly for custom shapes.
    """

    def __init__(self, base_url: str, token: str) -> None:
        self._base  = base_url.rstrip("/")
        self._token = token

    def _authenticated(self, method: HttpMethod, path: str) -> HttpRequestBuilder:
        return (
            HttpRequestBuilder(method, f"{self._base}/{path.lstrip('/')}")
            .bearer_auth(self._token)
            .json_content()
            .timeout(10)
            .retries(2)
        )

    def list_resource(self, path: str, **filters: str) -> HttpRequest:
        builder = self._authenticated(HttpMethod.GET, path)
        for k, v in filters.items():
            builder.param(k, v)
        return builder.build()

    def create_resource(self, path: str, payload: Any) -> HttpRequest:
        return self._authenticated(HttpMethod.POST, path).body(payload).build()

    def update_resource(self, path: str, payload: Any) -> HttpRequest:
        return self._authenticated(HttpMethod.PUT, path).body(payload).build()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Direct builder use — caller controls every step
    search = (
        GET("https://api.example.com/products")
        .param("q", "widget")
        .param("page", "1")
        .header("Accept", "application/json")
        .timeout(5)
        .build()
    )
    print("=== Search request ===")
    print(search)

    create_order = (
        POST("https://api.example.com/orders")
        .bearer_auth("tok_abc123")
        .json_content()
        .body({"sku": "WGT-001", "qty": 3})
        .timeout(15)
        .retries(1)
        .build()
    )
    print("\n=== Create order ===")
    print(create_order)

    # Director use — consistent shape without repeating boilerplate
    client = ApiClientDirector("https://api.example.com", "tok_abc123")

    list_users   = client.list_resource("/users", role="admin", active="true")
    create_user  = client.create_resource("/users", {"name": "Alice", "role": "admin"})

    print("\n=== Director: list users ===")
    print(list_users)
    print("\n=== Director: create user ===")
    print(create_user)
