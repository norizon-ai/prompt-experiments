"""
LLM API client.

Simple wrapper around OpenAI's API for testing prompts.
Configurable via .env file or direct parameters.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_client() -> OpenAI:
    """Get an OpenAI client using env vars."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Copy .env.example to .env and fill in your key."
        )
    return OpenAI(api_key=api_key)


def call_model(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call the LLM with a system + user prompt and return the response.

    Args:
        system_prompt: The system instruction.
        user_prompt: The user message.
        model: Model name (default: from env or gpt-4o).
        temperature: Sampling temperature (default: from env or 0.2).
        max_tokens: Max response tokens (default: from env or 4000).

    Returns:
        The model's response text.
    """
    client = get_client()

    model = model or os.getenv("MODEL_NAME", "gpt-4o")
    temperature = temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0.2"))
    max_tokens = max_tokens or int(os.getenv("MAX_TOKENS", "4000"))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()
