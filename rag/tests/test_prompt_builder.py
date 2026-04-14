"""Tests for prompt_builder — assembles Claude API prompts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_builder import build_prompt, SYSTEM_PROMPT, OUTPUT_FORMAT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state(my_side="left") -> dict:
    return {
        "my_side": my_side,
        "players": {
            "my_left":  {"x": 5.0,  "y": 37.0},
            "my_right": {"x": 15.0, "y": 37.0},
            "opp_left": {"x": 5.0,  "y": 7.0},
            "opp_right": {"x": 15.0, "y": 7.0},
        },
        "ball": {"x": 10.0, "y": 33.0, "height": "mid", "speed": "slow", "spin": None},
    }


def _chunks(n=2) -> list[dict]:
    return [
        {
            "text": f"Strategy tip {i}: Always dink cross-court when at the kitchen.",
            "source": "kitchen_play.md",
            "chunk_index": i,
            "distance": 0.2 + i * 0.05,
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# build_prompt structure
# ---------------------------------------------------------------------------

def test_returns_system_and_user_keys():
    prompt = build_prompt(_state(), _chunks())
    assert "system" in prompt
    assert "user" in prompt


def test_system_prompt_is_string():
    prompt = build_prompt(_state(), _chunks())
    assert isinstance(prompt["system"], str)
    assert len(prompt["system"]) > 50


def test_system_contains_persona():
    prompt = build_prompt(_state(), _chunks())
    assert "pickleball" in prompt["system"].lower()


def test_user_message_is_string():
    prompt = build_prompt(_state(), _chunks())
    assert isinstance(prompt["user"], str)


# ---------------------------------------------------------------------------
# Situation section
# ---------------------------------------------------------------------------

def test_user_contains_situation():
    prompt = build_prompt(_state(), _chunks())
    assert "Tactical Situation" in prompt["user"]


def test_user_contains_ball_description():
    prompt = build_prompt(_state(), _chunks())
    assert "Ball" in prompt["user"]


def test_user_contains_player_descriptions():
    prompt = build_prompt(_state(), _chunks())
    # At least one player label should be present
    assert any(label in prompt["user"] for label in ["You", "partner", "Opponent"])


# ---------------------------------------------------------------------------
# Context chunks section
# ---------------------------------------------------------------------------

def test_user_contains_retrieved_chunks():
    chunks = _chunks(n=3)
    prompt = build_prompt(_state(), chunks)
    assert "Strategy tip" in prompt["user"]


def test_user_contains_source_attribution():
    prompt = build_prompt(_state(), _chunks(n=2))
    assert "kitchen_play.md" in prompt["user"]


def test_empty_chunks_handled_gracefully():
    prompt = build_prompt(_state(), [])
    assert "No additional strategy context" in prompt["user"]


# ---------------------------------------------------------------------------
# Output format section
# ---------------------------------------------------------------------------

def test_user_contains_output_format_instruction():
    prompt = build_prompt(_state(), _chunks())
    assert "JSON" in prompt["user"]
    assert "rally" in prompt["user"].lower()


def test_user_specifies_3_shots():
    prompt = build_prompt(_state(), _chunks())
    assert "3" in prompt["user"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_spin_none_no_spin_in_prompt():
    """Spin=None should not produce 'spin: None' noise in the prompt."""
    prompt = build_prompt(_state(), _chunks())
    assert "spin: None" not in prompt["user"].lower()
    assert "spin: null" not in prompt["user"].lower()


def test_my_side_right_uses_correct_me_label():
    state = _state(my_side="right")
    prompt = build_prompt(state, _chunks())
    # "You (ME)" should appear somewhere in the user message
    assert "ME" in prompt["user"] or "You" in prompt["user"]
