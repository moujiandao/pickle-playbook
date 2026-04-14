"""Chunk and embed corpus markdown files into corpus_chunks in Supabase.

Run from the project root:
    python -m backend.scripts.migrate_corpus
"""

import os
import sys
from pathlib import Path

# Ensure project root and backend are on the path when run as a module
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # .../pickle-deploy
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
for _p in [str(_PROJECT_ROOT), str(_BACKEND_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db.repository import CorpusRepo  # noqa: E402
from db.supabase_client import get_client  # noqa: E402
from rag.embeddings import embed  # noqa: E402

CORPUS_DIR = _PROJECT_ROOT / "rag" / "corpus"
MIN_CHUNK_CHARS = 50


def chunk_file(path: Path) -> list[str]:
    """Split a markdown file on blank lines, skipping short chunks."""
    text = path.read_text(encoding="utf-8")
    raw_chunks = text.split("\n\n")
    return [c.strip() for c in raw_chunks if len(c.strip()) >= MIN_CHUNK_CHARS]


def main() -> None:
    repo = CorpusRepo(get_client())
    total = 0

    for md_file in sorted(CORPUS_DIR.glob("*.md")):
        source = md_file.name
        chunks = chunk_file(md_file)
        print(f"{source}: {len(chunks)} chunks found")

        if not chunks:
            continue

        embeddings = embed(chunks)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            repo.insert_chunk(
                content=chunk,
                source=source,
                metadata={"chunk_index": i, "file": source},
                embedding=embedding,
            )
            total += 1
            print(f"  [{i + 1}/{len(chunks)}] inserted chunk ({len(chunk)} chars)")

    print(f"\nDone. Inserted {total} chunks total.")


if __name__ == "__main__":
    main()
