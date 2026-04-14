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


def _get_collection(db_dir: str, client: Optional[chromadb.Client] = None):
    c = client or chromadb.PersistentClient(path=db_dir)
    return c.get_or_create_collection(name=COLLECTION_NAME)


def retrieve(
    game_state: dict,
    k: int = 5,
    db_dir: str = DEFAULT_DB_DIR,
    client: Optional[chromadb.Client] = None,
) -> list[dict]:
    """
    Retrieve the *k* most relevant strategy chunks for a given game state.

    Returns a list of dicts:
      {
        "text": str,          # chunk content
        "source": str,        # filename (e.g., "kitchen_play.md")
        "chunk_index": int,
        "distance": float,    # lower = more similar
      }
    """
    query = make_retrieval_query(game_state)
    query_embedding = embed([query])[0]

    collection = _get_collection(db_dir, client)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

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
