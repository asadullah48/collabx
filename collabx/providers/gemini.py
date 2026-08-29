"""Google Gemini provider, via the free-tier REST API.

Uses the REST endpoint directly rather than the `google-generativeai` SDK so
that installing CollabX pulls in no vendor client libraries. The whole provider
is one HTTPS POST.

Setup:  get a free key at https://aistudio.google.com/apikey
        export GEMINI_API_KEY=...
Use:    COLLABX_PROVIDER=gemini

The free tier is rate limited. A quota rejection surfaces as
`ProviderUnavailable`, which the agents treat like any other outage: fall back
to deterministic output rather than failing the request.
"""
from __future__ import annotations

import os
from typing import Optional

from collabx.providers.base import ProviderUnavailable, post_json

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

# A floating alias, not a pinned version. Google retires specific model ids --
# `gemini-2.0-flash` now returns 404 with "no longer available" -- and a
# portfolio project that 404s six months after it is written is worse than one
# that never called a model at all. Pin deliberately via GEMINI_MODEL.
#
# The *lite* alias is the default because the full flash models spend thinking
# tokens out of the same maxOutputTokens budget: measured here, a 24-token
# request to gemini-flash-latest returned MAX_TOKENS with no visible text at
# all, after 42 seconds. Lite answers the same prompt in 1.4s.
DEFAULT_MODEL = "gemini-flash-lite-latest"


class GeminiProvider:
    """Text completion against the Gemini REST API."""

    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL

    def available(self) -> bool:
        """True when a key is configured.

        Deliberately does not call the network. Availability is checked on every
        request to choose a provider, and spending a quota unit -- plus a round
        trip -- just to ask "do I have a key" is the wrong trade. A key that
        turns out to be invalid raises `ProviderUnavailable` at call time and
        falls back like any other failure.
        """
        return bool(self.api_key)

    def complete(
        self, prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> str:
        if not self.api_key:
            raise ProviderUnavailable(
                "GEMINI_API_KEY is not set. Free key: https://aistudio.google.com/apikey"
            )

        url = f"{API_ROOT}/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        # The key travels as a header, never in the URL: query strings are
        # logged by proxies and land in shell history.
        data = post_json(url, payload, headers={"x-goog-api-key": self.api_key})

        finish_reason = None
        try:
            finish_reason = data["candidates"][0].get("finishReason")
        except (KeyError, IndexError, TypeError):
            pass

        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            if finish_reason == "MAX_TOKENS":
                # Not a malformed response. Thinking-capable models spend the
                # maxOutputTokens budget on reasoning before emitting any text,
                # so a small budget yields a candidate with no parts at all.
                raise ProviderUnavailable(
                    f"Model '{self.model}' consumed the whole {max_tokens}-token budget "
                    f"on reasoning and returned no text. Raise max_tokens, or use a "
                    f"lite model such as '{DEFAULT_MODEL}'."
                ) from exc
            if finish_reason == "SAFETY":
                raise ProviderUnavailable(
                    f"Gemini blocked this request for safety (finishReason=SAFETY)."
                ) from exc
            raise ProviderUnavailable(
                f"Unexpected Gemini response shape (finishReason={finish_reason}): {exc}"
            ) from exc

        if not text:
            raise ProviderUnavailable("Gemini returned an empty completion.")
        return text
