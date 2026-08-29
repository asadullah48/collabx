"""Provider registry and selection.

Selection is driven by `COLLABX_PROVIDER`:

    unset / "auto"    deterministic unless a provider is already configured
    "deterministic"   never call a model (the default, and the CI default)
    "ollama"          local, free, no key
    "gemini"          Google free tier, needs GEMINI_API_KEY

**"auto" prefers deterministic when nothing is configured, not when nothing is
available.** A fresh clone must behave identically on every machine; if `auto`
silently picked up a stray Ollama server that happened to be running, two
developers would get different output from the same command and neither would
know why. Opting in to a model is explicit.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from collabx.providers.base import LLMProvider, ProviderUnavailable
from collabx.providers.deterministic import DeterministicProvider
from collabx.providers.gemini import GeminiProvider
from collabx.providers.ollama import OllamaProvider

__all__ = [
    "LLMProvider",
    "ProviderUnavailable",
    "DeterministicProvider",
    "GeminiProvider",
    "OllamaProvider",
    "resolve_provider",
    "provider_status",
    "PROVIDERS",
]

PROVIDERS = {
    "deterministic": DeterministicProvider,
    "ollama": OllamaProvider,
    "gemini": GeminiProvider,
}

ENV_VAR = "COLLABX_PROVIDER"


def resolve_provider(name: Optional[str] = None) -> LLMProvider:
    """Return the provider to use, falling back to deterministic.

    Never raises. An unknown name, an unconfigured key, or an unreachable
    server all resolve to `DeterministicProvider`, because a missing model must
    degrade the *quality* of the output, never the availability of the service.
    """
    requested = (name or os.getenv(ENV_VAR) or "auto").strip().lower()

    if requested in ("", "auto", "deterministic"):
        return DeterministicProvider()

    factory = PROVIDERS.get(requested)
    if factory is None:
        return DeterministicProvider()

    provider = factory()
    try:
        if provider.available():
            return provider
    except Exception:  # availability probes must never break a request
        pass
    return DeterministicProvider()


def provider_status() -> Dict[str, object]:
    """Diagnostics for the health endpoint and the setup docs.

    Reports which providers are configured without ever revealing a key: a
    boolean is enough to debug "why am I getting deterministic output", and a
    prefix or suffix of a credential is still a credential.
    """
    requested = (os.getenv(ENV_VAR) or "auto").strip().lower()
    active = resolve_provider()

    available: List[str] = ["deterministic"]
    ollama = OllamaProvider()
    if ollama.available():
        available.append("ollama")
    if GeminiProvider().available():
        available.append("gemini")

    return {
        "requested": requested,
        "active": active.name,
        "available": available,
        "ollama_models": ollama.installed_models(),
        "llm_backed": active.name != "deterministic",
    }
