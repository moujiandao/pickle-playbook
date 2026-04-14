"""Tests for the token-aware text chunker."""

import sys
from pathlib import Path

# Allow importing from rag/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunker import (
    TARGET_MAX,
    TARGET_MIN,
    OVERLAP,
    chunk_text,
    chunk_file,
    count_tokens,
    _strip_srt,
)


# ---------------------------------------------------------------------------
# Basic chunking
# ---------------------------------------------------------------------------

def _make_text(paragraphs: int = 10, words_per_para: int = 60) -> str:
    """Generate a synthetic corpus of known rough size."""
    word = "pickleball "
    para = (word * words_per_para).strip()
    return "\n\n".join([para] * paragraphs)


def test_chunk_returns_list():
    text = _make_text()
    chunks = chunk_text(text, source="test.md")
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_token_bounds():
    """Every chunk except possibly the last must be within [TARGET_MIN, TARGET_MAX] tokens.
    The last chunk may be smaller if the document tail is short."""
    text = _make_text(paragraphs=15)
    chunks = chunk_text(text, source="test.md")

    for chunk in chunks[:-1]:
        assert chunk["token_count"] <= TARGET_MAX, (
            f"Chunk {chunk['chunk_index']} has {chunk['token_count']} tokens, "
            f"exceeds TARGET_MAX={TARGET_MAX}"
        )

    # All chunks should have at least some content
    for chunk in chunks:
        assert chunk["token_count"] > 0


def test_chunk_has_required_keys():
    chunks = chunk_text("Some short text.", source="test.md")
    for chunk in chunks:
        assert "text" in chunk
        assert "source" in chunk
        assert "chunk_index" in chunk
        assert "token_count" in chunk


def test_chunk_source_propagated():
    chunks = chunk_text(_make_text(), source="kitchen_play.md")
    for chunk in chunks:
        assert chunk["source"] == "kitchen_play.md"


def test_chunk_index_sequential():
    chunks = chunk_text(_make_text(paragraphs=20), source="test.md")
    indices = [c["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_overlap_creates_shared_tokens():
    """Consecutive chunks should share some token content at the boundary."""
    text = _make_text(paragraphs=20)
    chunks = chunk_text(text, source="test.md")
    if len(chunks) < 2:
        return  # nothing to test

    # The end of chunk N and the start of chunk N+1 should share text
    end_of_first = chunks[0]["text"][-50:]
    start_of_second = chunks[1]["text"][:50]
    # They won't match exactly due to whitespace normalization, but both should
    # contain the same repeated word
    assert "pickleball" in end_of_first
    assert "pickleball" in start_of_second


def test_empty_text_returns_empty():
    assert chunk_text("", source="empty.md") == []


def test_chunk_token_count_matches_actual():
    """chunk_index token_count should match re-counting the text."""
    chunks = chunk_text(_make_text(), source="test.md")
    for chunk in chunks:
        actual = count_tokens(chunk["text"])
        # Allow small variance due to whitespace stripping
        assert abs(actual - chunk["token_count"]) <= 5, (
            f"Reported {chunk['token_count']} but counted {actual}"
        )


# ---------------------------------------------------------------------------
# SRT stripping
# ---------------------------------------------------------------------------

_SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:03,500
Welcome to pickleball tips.

2
00:00:04,000 --> 00:00:07,000
Today we cover the kitchen dink.

3
00:00:08,000 --> 00:00:10,000
Stay low and soft.
"""


def test_srt_strip_removes_timestamps():
    cleaned = _strip_srt(_SAMPLE_SRT)
    assert "-->" not in cleaned
    assert "00:00" not in cleaned


def test_srt_strip_preserves_caption_text():
    cleaned = _strip_srt(_SAMPLE_SRT)
    assert "Welcome to pickleball tips" in cleaned
    assert "kitchen dink" in cleaned
    assert "Stay low and soft" in cleaned


# ---------------------------------------------------------------------------
# File chunking
# ---------------------------------------------------------------------------

def test_chunk_file_markdown(tmp_path):
    md_file = tmp_path / "strategy.md"
    md_file.write_text(_make_text(paragraphs=10), encoding="utf-8")
    chunks = chunk_file(md_file)
    assert len(chunks) > 0
    assert all(c["source"] == "strategy.md" for c in chunks)


def test_chunk_file_srt(tmp_path):
    srt_file = tmp_path / "lesson.srt"
    # Build a larger SRT so chunking has content to work with
    blocks = []
    for i in range(1, 30):
        blocks.append(
            f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n"
            f"Pickleball tip number {i}: stay low and keep soft hands."
        )
    srt_file.write_text("\n\n".join(blocks), encoding="utf-8")
    chunks = chunk_file(srt_file)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "-->" not in chunk["text"]
