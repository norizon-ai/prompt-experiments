"""
LLM API client — supports multiple providers (OpenAI, Mistral, etc.)

All providers use OpenAI-compatible APIs. The client picks the right
base_url and api_key based on the model name.

Configurable via .env file or direct parameters.
"""

import os
from typing import Optional

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root (works whether called from notebooks/ or root)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")
# Also try current directory as fallback
load_dotenv()

# Model → provider mapping
# Add new models here as needed
MODEL_PROVIDERS = {
    "gpt-4o": {
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "gpt-4o-mini": {
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "mistral-small-latest": {
        "base_url": "https://api.mistral.ai/v1",
        "env_key": "MISTRAL_API_KEY",
    },
}

# Alias: intern can use "mistral-25b" as shorthand
MODEL_PROVIDERS["mistral-25b"] = MODEL_PROVIDERS["mistral-small-latest"]


def get_client(model: Optional[str] = None) -> OpenAI:
    """
    Get an OpenAI-compatible client for the given model.

    Automatically picks the right base_url and API key based on model name.
    Falls back to OPENAI_API_KEY and default OpenAI endpoint for unknown models.
    """
    model = model or os.getenv("MODEL_NAME", "gpt-4o")
    provider = MODEL_PROVIDERS.get(model, MODEL_PROVIDERS.get("gpt-4o"))

    api_key = os.getenv(provider["env_key"], "")
    if not api_key:
        raise ValueError(
            f"API key not set for model '{model}'. "
            f"Set {provider['env_key']} in your .env file."
        )

    return OpenAI(
        api_key=api_key,
        base_url=provider["base_url"],
    )


def call_model(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call the LLM with a system + user prompt and return the response.

    The model name determines which API endpoint and key to use:
    - "gpt-4o" → OpenAI API (OPENAI_API_KEY)
    - "mistral-25b" / "mistral-small-latest" → Mistral API (MISTRAL_API_KEY)

    Args:
        system_prompt: The system instruction.
        user_prompt: The user message.
        model: Model name. Determines both the API endpoint and the model ID.
        temperature: Sampling temperature (default: from env or 0.2).
        max_tokens: Max response tokens (default: from env or 4000).

    Returns:
        The model's response text.
    """
    model = model or os.getenv("MODEL_NAME", "gpt-4o")
    client = get_client(model)

    # Resolve aliases to actual model IDs for the API call
    actual_model = model
    if model == "mistral-25b":
        actual_model = "mistral-small-latest"

    temperature = temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0.2"))
    max_tokens = max_tokens or int(os.getenv("MAX_TOKENS", "4000"))

    response = client.chat.completions.create(
        model=actual_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()
