"""
Retrieval service.

Given a GameState dict, generates a natural-language query using
position_describer, queries ChromaDB for the top-k most relevant chunks,
and returns them with source attribution.
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from dotenv import load_dotenv

from embeddings import embed
from ingest import COLLECTION_NAME
from position_describer import make_retrieval_query

load_dotenv()

DEFAULT_DB_DIR = str(Path(__file__).parent / "chroma_db")

_ADJACENT = {
    "3.0": ["3.0", "3.5"],
    "3.5": ["3.0", "3.5", "4.0"],
    "4.0": ["3.5", "4.0", "4.5"],
    "4.5": ["4.0", "4.5", "5.0"],
    "5.0": ["4.5", "5.0"],
}


def _get_collection(db_dir: str, client: Optional[chromadb.Client] = None):
    c = client or chromadb.PersistentClient(path=db_dir)
    return c.get_or_create_collection(name=COLLECTION_NAME)


def _query_collection(collection, query_embedding, k, where=None):
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)

    chunks = []
    if not results["ids"] or not results["ids"][0]:
        return chunks

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "distance": dist,
            }
        )
    return chunks


def retrieve(
    game_state: dict,
    k: int = 5,
    db_dir: str = DEFAULT_DB_DIR,
    client: Optional[chromadb.Client] = None,
    level: Optional[str] = None,
) -> tuple[list[dict], bool]:
    """Retrieve the *k* most relevant strategy chunks for a given game state.

    Returns (chunks, fallback_used) where fallback_used is True when
    level-filtered retrieval found nothing and we fell back to unfiltered.
    """
    query = make_retrieval_query(game_state)
    query_embedding = embed([query])[0]
    collection = _get_collection(db_dir, client)

    if level and level in _ADJACENT:
        where = {"level": {"$in": _ADJACENT[level]}}
        chunks = _query_collection(collection, query_embedding, k, where=where)
        if chunks:
            return chunks, False
        # Fallback: no level-specific content, try unfiltered
        return _query_collection(collection, query_embedding, k), True

    return _query_collection(collection, query_embedding, k), False
