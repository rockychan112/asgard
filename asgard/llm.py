"""One tiny seam for the model call, so arms, judge, and the eval harness can
inject their own — a mock for dry-runs, temperature=0 for reproducible eval, or
a different model for the judge than for the arms.
"""
from __future__ import annotations

import os
from typing import Callable

# A Chat takes (system, user) and returns the raw completion string.
# Temperature and json-mode are baked in when the Chat is built.
Chat = Callable[[str, str], str]


def openai_chat(
    *,
    model: str | None = None,
    temperature: float = 0.0,
    json: bool = True,
    base_url_env: str = "OPENAI_BASE_URL",
    key_env: str = "OPENAI_API_KEY",
    model_env: str = "ASGARD_MODEL",
    default_model: str = "gpt-4o-mini",
) -> Chat:
    """Build a Chat against any OpenAI-compatible endpoint (env-configured).

    The *_env names are parameterised so the arms and the judge can point at two
    different providers (e.g. arms=OPENAI_*/DeepSeek, judge=GLM_*).
    """
    from openai import OpenAI

    # A long eval is ~hundreds of sequential calls; one transient blip must not tank
    # the whole run, so lean on the SDK's exponential-backoff retries + a per-call timeout.
    client = OpenAI(
        base_url=os.environ.get(base_url_env, "https://api.openai.com/v1"),
        api_key=os.environ.get(key_env, ""),
        max_retries=5,
        timeout=60.0,
    )
    mdl = model or os.environ.get(model_env, default_model)
    fmt = {"response_format": {"type": "json_object"}} if json else {}

    def _chat(system: str, user: str) -> str:
        content = ""
        for _ in range(3):  # SDK retries HTTP errors; this retries a 200-OK empty body
            resp = client.chat.completions.create(
                model=mdl,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **fmt,
            )
            content = resp.choices[0].message.content or ""
            if content.strip():
                break
        return content

    return _chat
