"""Retrieve strategy chunks from Supabase/pgvector for a query string."""

from db.repository import CorpusRepo
from db.supabase_client import get_client
from rag.embeddings import embed


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Embed query, then search corpus_chunks via pgvector cosine similarity.

    Returns list of {content, source, similarity}.
    """
    query_embedding = embed([query])[0]
    repo = CorpusRepo(get_client())
    results = repo.search_similar(query_embedding, top_k=k)
    return [
        {"content": r["content"], "source": r["source"], "similarity": r["similarity"]}
        for r in results
    ]
