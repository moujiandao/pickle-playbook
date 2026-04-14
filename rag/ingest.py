"""
Corpus ingestion pipeline.

Walks rag/corpus/ for .md, .txt, .srt files, chunks them into 300-500 token
segments with 50-token overlap, generates OpenAI embeddings, and upserts into
a local ChromaDB collection named "pickleball_strategy".

Usage:
    python ingest.py                  # uses default corpus/ and chroma_db/
    python ingest.py --corpus ./my_corpus --db ./my_db
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Optional

import chromadb

from chunker import chunk_file
from embeddings import embed

COLLECTION_NAME = "pickleball_strategy"
SUPPORTED_EXTENSIONS = {".md", ".txt", ".srt"}


def _chunk_id(source: str, chunk_index: int) -> str:
    """Stable, deterministic ID for a chunk (source file + index)."""
    raw = f"{source}::{chunk_index}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def ingest_corpus(
    corpus_dir: str = "corpus",
    db_dir: str = "chroma_db",
    client: Optional[chromadb.Client] = None,
) -> int:
    """
    Ingest all supported files in *corpus_dir* into ChromaDB.

    Returns the total number of chunks upserted.
    """
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        print(f"ERROR: corpus directory not found: {corpus_path.resolve()}")
        return 0

    files = [
        f for f in corpus_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        print(f"No supported files found in {corpus_path.resolve()}")
        return 0

    # --- ChromaDB setup ---
    if client is None:
        chroma_client = chromadb.PersistentClient(path=str(db_dir))
    else:
        chroma_client = client

    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    total_upserted = 0

    for file_path in sorted(files):
        print(f"  Processing: {file_path.name}")
        chunks = chunk_file(file_path)
        if not chunks:
            print(f"    -> no chunks produced, skipping")
            continue

        texts = [c["text"] for c in chunks]
        ids = [_chunk_id(c["source"], c["chunk_index"]) for c in chunks]
        metadatas = [
            {
                "source": c["source"],
                "chunk_index": c["chunk_index"],
                "token_count": c["token_count"],
            }
            for c in chunks
        ]

        print(f"    -> {len(chunks)} chunks, embedding...")
        embeddings = embed(texts)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"    -> upserted {len(chunks)} chunks")
        total_upserted += len(chunks)

    print(f"\nDone. Total chunks in collection: {total_upserted}")
    return total_upserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest pickleball corpus into ChromaDB")
    parser.add_argument("--corpus", default="corpus", help="Path to corpus directory")
    parser.add_argument("--db", default="chroma_db", help="Path to ChromaDB storage directory")
    args = parser.parse_args()

    count = ingest_corpus(corpus_dir=args.corpus, db_dir=args.db)
    sys.exit(0 if count > 0 else 1)
