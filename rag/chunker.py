"""
Token-aware text chunker.

Splits markdown/plain-text documents into overlapping chunks of 300-500 tokens.
Uses tiktoken (cl100k_base) for accurate token counting.
Supports .md, .txt, and .srt (subtitle) inputs.
"""

import re
from pathlib import Path
from typing import Generator

import tiktoken

TARGET_MIN = 300
TARGET_MAX = 500
OVERLAP = 50

_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def decode_tokens(token_ids: list[int]) -> str:
    return _ENCODER.decode(token_ids)


# ---------------------------------------------------------------------------
# SRT cleaning
# ---------------------------------------------------------------------------

_SRT_BLOCK = re.compile(
    r"^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n",
    re.MULTILINE,
)


def _strip_srt(text: str) -> str:
    """Remove SRT index/timestamp lines, keep caption text."""
    # Remove blocks: index line + timestamp line, leave caption text
    text = _SRT_BLOCK.sub("", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Paragraph splitter
# ---------------------------------------------------------------------------


def _split_paragraphs(text: str) -> list[str]:
    """Split on blank lines. Returns non-empty paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# ---------------------------------------------------------------------------
# Core chunker
# ---------------------------------------------------------------------------


def chunk_text(
    text: str,
    source: str = "",
    target_min: int = TARGET_MIN,
    target_max: int = TARGET_MAX,
    overlap: int = OVERLAP,
) -> list[dict]:
    """
    Chunk *text* into segments of target_min..target_max tokens with *overlap*
    token overlap between consecutive chunks.

    Returns a list of dicts:
      {
        "text": str,
        "source": str,
        "chunk_index": int,
        "token_count": int,
      }
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[dict] = []
    current_tokens: list[int] = []
    chunk_index = 0

    def _flush(tokens: list[int]) -> None:
        nonlocal chunk_index
        chunk_text_str = decode_tokens(tokens)
        chunks.append(
            {
                "text": chunk_text_str.strip(),
                "source": source,
                "chunk_index": chunk_index,
                "token_count": len(tokens),
            }
        )
        chunk_index += 1

    for para in paragraphs:
        para_tokens = _ENCODER.encode(para)

        # If adding this paragraph would exceed target_max, flush first
        if current_tokens and len(current_tokens) + len(para_tokens) > target_max:
            _flush(current_tokens)
            # Carry over tail for overlap
            current_tokens = current_tokens[-overlap:] if overlap else []

        current_tokens.extend(para_tokens)
        # Add a paragraph separator token (newline)
        current_tokens.extend(_ENCODER.encode("\n\n"))

        # If we've hit the minimum, flush and start a new chunk with overlap
        if len(current_tokens) >= target_min:
            _flush(current_tokens)
            current_tokens = current_tokens[-overlap:] if overlap else []

    # Flush any remainder
    if current_tokens:
        text_remainder = decode_tokens(current_tokens).strip()
        if text_remainder:
            _flush(current_tokens)

    return chunks


# ---------------------------------------------------------------------------
# File reader
# ---------------------------------------------------------------------------


def load_file(path: Path) -> str:
    """Read a .md, .txt, or .srt file and return clean plain text."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".srt":
        return _strip_srt(raw)
    return raw


def chunk_file(path: Path, **kwargs) -> list[dict]:
    """Load a file and chunk it. Source is set to the filename stem."""
    text = load_file(path)
    return chunk_text(text, source=path.name, **kwargs)
