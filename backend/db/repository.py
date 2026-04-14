"""Repository classes wrapping Supabase tables."""

from supabase import Client


class ScenarioRepo:
    def __init__(self, supabase: Client) -> None:
        self._db = supabase

    def save(self, name: str, game_state: dict) -> dict:
        response = (
            self._db.table("scenarios")
            .insert({"name": name, "game_state": game_state})
            .execute()
        )
        return response.data[0]

    def get(self, scenario_id: str) -> dict | None:
        response = (
            self._db.table("scenarios")
            .select("*")
            .eq("id", scenario_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def list_all(self) -> list[dict]:
        response = (
            self._db.table("scenarios")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def delete(self, scenario_id: str) -> bool:
        response = (
            self._db.table("scenarios")
            .delete()
            .eq("id", scenario_id)
            .execute()
        )
        return len(response.data) > 0


class CorrectionRepo:
    def __init__(self, supabase: Client) -> None:
        self._db = supabase

    def save(
        self,
        game_state: dict,
        original: dict,
        corrected: dict | None,
        feedback_type: str,
    ) -> dict:
        response = (
            self._db.table("corrections")
            .insert(
                {
                    "game_state": game_state,
                    "original_recommendation": original,
                    "corrected_recommendation": corrected,
                    "feedback_type": feedback_type,
                }
            )
            .execute()
        )
        return response.data[0]

    def list_by_game_state(self, game_state: dict) -> list[dict]:
        # Filter by exact jsonb match using the @> containment operator
        response = (
            self._db.table("corrections")
            .select("*")
            .contains("game_state", game_state)
            .execute()
        )
        return response.data


class CorpusRepo:
    def __init__(self, supabase: Client) -> None:
        self._db = supabase

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[dict]:
        response = self._db.rpc(
            "match_corpus",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k,
            },
        ).execute()
        return response.data  # [{id, content, source, similarity}, ...]

    def insert_chunk(
        self,
        content: str,
        source: str,
        metadata: dict,
        embedding: list[float],
    ) -> dict:
        response = (
            self._db.table("corpus_chunks")
            .insert(
                {
                    "content": content,
                    "source": source,
                    "metadata": metadata,
                    "embedding": embedding,
                }
            )
            .execute()
        )
        return response.data[0]
