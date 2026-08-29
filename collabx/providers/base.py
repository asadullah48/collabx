"""Provider interface for optional LLM-backed agents.

CollabX runs with **no model and no API key by default**. That is deliberate:
a portfolio project a reviewer cannot run is a screenshot, and nobody clicking
a repository link will install a runtime or register for a key just to see it
work. The deterministic template engine is the always-available floor; a model
is an opt-in upgrade layered on top.

The contract is intentionally tiny -- text in, text out. Anything richer would
bind the project to one vendor's SDK, and every provider here is reachable over
plain HTTP with the standard library, so installing CollabX pulls in no client
libraries at all.

Failure is never fatal. A provider that is unreachable, unauthorised, rate
limited, or slow raises `ProviderUnavailable`, and the caller falls back to the
deterministic path. The endpoint stays total, which is the same promise the
revision loop makes when it runs out of budget.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional, Protocol, runtime_checkable

# Network calls are bounded so a hung provider cannot hang an HTTP request.
DEFAULT_TIMEOUT_SECONDS = 60


class ProviderUnavailable(RuntimeError):
    """The provider cannot serve this request; fall back to deterministic output.

    Raised for every failure mode a caller should treat identically: no key, no
    server, bad status, rate limit, timeout, or an unparseable response.
    """


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal text-completion interface every provider implements."""

    name: str

    def available(self) -> bool:
        """True when this provider is configured and reachable.

        Must never raise and must never block for long: it is called to choose
        a provider, not to serve a request.
        """
        ...

    def complete(self, prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        """Return the model's text completion, or raise `ProviderUnavailable`."""
        ...


def post_json(
    url: str,
    payload: dict,
    *,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """POST JSON and return the decoded response, or raise `ProviderUnavailable`.

    Shared by every HTTP provider so they fail identically. Uses urllib rather
    than a client library to keep CollabX's runtime dependency list at
    fastapi/uvicorn/pydantic.
    """
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Read the body for the real reason: providers put quota and key errors
        # in the payload, and "HTTP 429" alone does not tell a user what to fix.
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
        except Exception:  # pragma: no cover - best-effort diagnostics
            pass
        raise ProviderUnavailable(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderUnavailable(f"Cannot reach {url}: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderUnavailable(f"Network failure calling {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderUnavailable(f"Non-JSON response from {url}: {exc}") from exc


def get_json(url: str, *, headers: Optional[dict] = None, timeout: int = 5) -> dict:
    """GET JSON with a short timeout, for availability probes."""
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # availability probes must never raise
        raise ProviderUnavailable(f"Probe failed for {url}: {exc}") from exc
