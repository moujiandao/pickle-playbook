"""
OpenAI embedding wrapper.

Uses text-embedding-3-small for cost-efficiency.
Batches requests to stay within the API's per-request token limit.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "text-embedding-3-small"
BATCH_SIZE = 100  # texts per API call — well under the 2048-input limit


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def embed(texts: list[str], client: Optional[OpenAI] = None) -> list[list[float]]:
    """
    Return embeddings for *texts*.

    Each embedding is a list of floats (1536 dimensions for text-embedding-3-small).
    Texts are batched into groups of BATCH_SIZE to avoid oversized requests.
    """
    if not texts:
        return []

    c = client or _client()
    results: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = c.embeddings.create(model=MODEL, input=batch)
        # response.data is ordered to match the input
        results.extend(item.embedding for item in response.data)

    return results
