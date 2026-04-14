-- Pickle Playbook: Initial Schema
-- Migration: 001_initial_schema.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- scenarios
-- Saved court setups users can replay or share
-- ============================================================
CREATE TABLE IF NOT EXISTS scenarios (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text        NOT NULL,
    game_state  jsonb       NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Auto-update updated_at on row changes
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scenarios_updated_at
    BEFORE UPDATE ON scenarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- corrections
-- Human-in-the-loop feedback on AI recommendations
-- ============================================================
CREATE TABLE IF NOT EXISTS corrections (
    id                       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    game_state               jsonb       NOT NULL,
    original_recommendation  jsonb       NOT NULL,
    corrected_recommendation jsonb,
    feedback_type            text        NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down', 'rewrite')),
    created_at               timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- corpus_chunks
-- Chunked pickleball strategy content with embeddings for RAG
-- ============================================================
CREATE TABLE IF NOT EXISTS corpus_chunks (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    content     text        NOT NULL,
    source      text        NOT NULL,
    metadata    jsonb       NOT NULL DEFAULT '{}',
    embedding   vector(1536),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- IVFFlat index for cosine similarity search
-- lists=10 is appropriate for a small corpus (< 10k chunks)
-- Increase lists as corpus grows: ~sqrt(row_count) is a good heuristic
CREATE INDEX IF NOT EXISTS corpus_chunks_embedding_idx
    ON corpus_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- ============================================================
-- match_corpus
-- Similarity search: returns chunks above a cosine similarity
-- threshold, ordered by relevance
-- ============================================================
CREATE OR REPLACE FUNCTION match_corpus(
    query_embedding  vector(1536),
    match_threshold  float,
    match_count      int
)
RETURNS TABLE (
    id          uuid,
    content     text,
    source      text,
    similarity  float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        c.id,
        c.content,
        c.source,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM corpus_chunks c
    WHERE c.embedding IS NOT NULL
      AND 1 - (c.embedding <=> query_embedding) >= match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;
