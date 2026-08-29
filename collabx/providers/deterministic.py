"""The null provider: no model, no key, no network.

This is the default, and it is what makes CollabX runnable on a fresh clone
with nothing installed. It is always "available" and never completes anything:
callers ask `is_model_backed` and take the template path instead.

Modelling "no model" as a provider rather than as `None` keeps the branch in
one place. Every caller handles a provider object, so there is no scattered
`if provider is not None` to forget.
"""
from __future__ import annotations

from collabx.providers.base import ProviderUnavailable


class DeterministicProvider:
    """Always available, never generates. Signals the template path."""

    name = "deterministic"

    def available(self) -> bool:
        return True

    def complete(
        self, prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> str:
        raise ProviderUnavailable(
            "The deterministic provider does not call a model. "
            "Set COLLABX_PROVIDER=ollama or COLLABX_PROVIDER=gemini to enable one."
        )


def is_model_backed(provider) -> bool:
    """True when `provider` actually calls a model.

    A single predicate so agents never compare provider names inline; adding a
    provider must not mean hunting down string comparisons.
    """
    return getattr(provider, "name", "deterministic") != "deterministic"
