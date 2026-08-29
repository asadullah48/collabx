"""Ollama provider: free, local, offline, no API key.

This is the recommended way to run CollabX with a real model. Inference happens
on the user's own machine, so there is no key to leak, no quota to exhaust, and
no per-token cost -- which matters for a project meant to be cloned and run by
strangers.

Setup:  install Ollama, then `ollama pull llama3.2`
Use:    COLLABX_PROVIDER=ollama
"""
from __future__ import annotations

import os
from typing import List, Optional

from collabx.providers.base import ProviderUnavailable, get_json, post_json

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"


class OllamaProvider:
    """Text completion against a local Ollama server."""

    name = "ollama"

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = (host or os.getenv("OLLAMA_HOST") or DEFAULT_HOST).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or DEFAULT_MODEL

    def available(self) -> bool:
        """True when the local server responds and has at least one model."""
        try:
            tags = get_json(f"{self.host}/api/tags", timeout=3)
        except ProviderUnavailable:
            return False
        return bool(tags.get("models"))

    def installed_models(self) -> List[str]:
        """Model names the local server can serve, for diagnostics."""
        try:
            tags = get_json(f"{self.host}/api/tags", timeout=3)
        except ProviderUnavailable:
            return []
        return [m.get("name", "") for m in tags.get("models", []) if m.get("name")]

    def resolve_model(self) -> str:
        """Pick a model that is actually installed.

        A configured name that has not been pulled would fail every request with
        a 404 the user has to decode. Falling back to an installed model keeps
        the happy path working, and `available()` already proved one exists.
        """
        installed = self.installed_models()
        if not installed:
            raise ProviderUnavailable(
                f"No models installed on {self.host}. Run: ollama pull {self.model}"
            )
        if self.model in installed:
            return self.model
        # Ollama names are "family:tag"; accept a bare family name too.
        for name in installed:
            if name.split(":", 1)[0] == self.model.split(":", 1)[0]:
                return name
        return installed[0]

    def complete(
        self, prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> str:
        payload = {
            "model": self.resolve_model(),
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = post_json(f"{self.host}/api/generate", payload)
        text = (data.get("response") or "").strip()
        if not text:
            raise ProviderUnavailable("Ollama returned an empty completion.")
        return text
