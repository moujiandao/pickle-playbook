"""OpenAI embedding wrapper using text-embedding-3-small (1536 dims)."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client: OpenAI | None = None

MODEL = "text-embedding-3-small"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input string."""
    if not texts:
        return []
    response = _get_client().embeddings.create(model=MODEL, input=texts)
    # API returns embeddings sorted by index, so ordering is preserved
    return [item.embedding for item in sorted(response.data, key=lambda e: e.index)]
