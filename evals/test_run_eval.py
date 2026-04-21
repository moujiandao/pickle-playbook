"""Tests for eval runner scoring logic.

These tests cover score_scenario, _normalize_shot, and eval_state_to_game_state.
The recommend() function is NOT called — tests are purely about the scoring layer.
"""

import sys
from pathlib import Path

import pytest

# Ensure evals/ and backend/ are on path before importing run_eval
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
for _p in (_HERE, _REPO / "backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from run_eval import _normalize_shot, eval_state_to_game_state, score_scenario


# ── helpers ────────────────────────────────────────────────────────────────

class _Rec:
    """Minimal stand-in for ShotRecommendation."""
    def __init__(self, name: str, why: str = ""):
        self.name = name
        self.why = why


def _scenario(primary: str, alternatives=None, must_mention=None, sid="t001"):
    return {
        "id": sid,
        "difficulty": "obvious",
        "expert_answer": {
            "primary_shot": primary,
            "acceptable_alternatives": alternatives or [],
            "reasoning_must_mention": must_mention or [],
            "expected_sequence": [],
        },
    }


def _base_state(**overrides) -> dict:
    state = {
        "skill_level": 4.0,
        "me_position": "right_kitchen",
        "partner_position": "left_kitchen",
        "opp_left_position": "left_kitchen",
        "opp_right_position": "right_kitchen",
        "ball_position": {"x": 10.0, "y": 27.0},
        "ball_height": "low",
        "ball_speed": "slow",
        "zone": "kitchen",
    }
    state.update(overrides)
    return state


# ── _normalize_shot ────────────────────────────────────────────────────────

class TestNormalizeShotName:
    def test_strips_hyphens_spaces(self):
        assert _normalize_shot("Cross-Court Dink") == "crosscourtdink"

    def test_strips_underscores(self):
        assert _normalize_shot("crosscourt_dink") == "crosscourtdink"

    def test_case_insensitive(self):
        assert _normalize_shot("Third-Shot Drop") == _normalize_shot("third_shot_drop")

    def test_numeric_preserved(self):
        assert "3" in _normalize_shot("third-shot-3")

    def test_empty_string(self):
        assert _normalize_shot("") == ""


# ── score_scenario — shot match ────────────────────────────────────────────

class TestShotMatch:
    def test_exact_match_normalized(self):
        recs = [_Rec("Third-Shot Drop from the Baseline")]
        result = score_scenario(_scenario("third_shot_drop"), recs)
        assert result["shot_match"] is True

    def test_acceptable_alternative_match(self):
        # "Third-Shot Drive" normalizes to "thirdshotdrive" == normalize("third_shot_drive")
        recs = [_Rec("Third-Shot Drive")]
        result = score_scenario(_scenario("third_shot_drop", alternatives=["third_shot_drive"]), recs)
        assert result["shot_match"] is True

    def test_no_match(self):
        recs = [_Rec("Speed-Up Attack")]
        result = score_scenario(_scenario("third_shot_drop"), recs)
        assert result["shot_match"] is False

    def test_substring_match_primary_contains_pred(self):
        # "speedup" is contained in "speedupattack" normalized
        recs = [_Rec("Speedup Attack")]
        result = score_scenario(_scenario("speedup"), recs)
        assert result["shot_match"] is True

    def test_empty_recs_no_crash(self):
        result = score_scenario(_scenario("third_shot_drop"), [])
        assert result["shot_match"] is False

    def test_predicted_shot_recorded(self):
        recs = [_Rec("Cross-Court Dink")]
        result = score_scenario(_scenario("crosscourt_dink"), recs)
        assert result["predicted_shot"] == "Cross-Court Dink"
        assert result["expected_shot"] == "crosscourt_dink"

    def test_no_recs_predicted_shot_is_none(self):
        result = score_scenario(_scenario("drop"), [])
        assert result["predicted_shot"] is None


# ── score_scenario — reasoning coverage ───────────────────────────────────

class TestReasoningCoverage:
    def test_full_coverage(self):
        recs = [_Rec("Drop", "drop into the kitchen then advance")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance"]), recs)
        assert result["reasoning_coverage"] == 1.0

    def test_partial_coverage(self):
        recs = [_Rec("Drop", "drop into the kitchen")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance", "time"]), recs)
        assert result["reasoning_coverage"] == 0.333  # round(1/3, 3)

    def test_zero_coverage(self):
        recs = [_Rec("Drop", "hit the ball softly over the net")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance"]), recs)
        assert result["reasoning_coverage"] == 0.0

    def test_no_must_mention_is_zero(self):
        recs = [_Rec("Drop", "some reasoning")]
        result = score_scenario(_scenario("drop", must_mention=[]), recs)
        assert result["reasoning_coverage"] == 0.0

    def test_checks_all_rec_why_fields(self):
        recs = [
            _Rec("Drop", "drop to kitchen"),
            _Rec("Drive", "buy time to advance"),
        ]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "time"]), recs)
        assert result["reasoning_coverage"] == 1.0

    def test_case_insensitive_keyword_match(self):
        recs = [_Rec("Drop", "KITCHEN reset and ADVANCE")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance"]), recs)
        assert result["reasoning_coverage"] == 1.0

    def test_mentions_dict_populated(self):
        recs = [_Rec("Drop", "kitchen play")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance"]), recs)
        assert result["mentions"] == {"kitchen": True, "advance": False}


# ── eval_state_to_game_state ───────────────────────────────────────────────

class TestEvalStateToGameState:
    def test_basic_right_kitchen(self):
        gs = eval_state_to_game_state(_base_state())
        assert gs.my_side == "right"
        assert gs.skill_level == "4.0"
        assert gs.players.my_left.x < gs.players.my_right.x
        assert gs.ball.height == "low"
        assert gs.ball.speed == "slow"

    def test_left_side_me(self):
        gs = eval_state_to_game_state(_base_state(
            me_position="left_kitchen",
            partner_position="right_kitchen",
        ))
        assert gs.my_side == "left"
        assert gs.players.my_left.x < gs.players.my_right.x

    def test_baseline_positions(self):
        gs = eval_state_to_game_state(_base_state(
            me_position="right_baseline",
            partner_position="left_baseline",
            opp_left_position="left_baseline",
            opp_right_position="right_baseline",
            ball_position={"x": 10.0, "y": 40.0},
        ))
        assert gs.players.my_right.y == 40.0
        assert gs.players.opp_left.y == 4.0

    def test_stacking_no_validator_error(self):
        # Both players same side — stacking scenario
        gs = eval_state_to_game_state(_base_state(
            me_position="right_transition",
            partner_position="right_transition",
            opp_left_position="left_baseline",
            opp_right_position="right_baseline",
            ball_position={"x": 4.0, "y": 38.0},
            ball_height="mid",
        ))
        assert gs.players.my_left.x < gs.players.my_right.x

    def test_skill_level_float_to_string(self):
        gs = eval_state_to_game_state(_base_state(skill_level=3.5))
        assert gs.skill_level == "3.5"

    def test_opp_left_x_less_than_opp_right_x(self):
        gs = eval_state_to_game_state(_base_state())
        assert gs.players.opp_left.x < gs.players.opp_right.x

    def test_transition_y_values(self):
        gs = eval_state_to_game_state(_base_state(
            me_position="right_transition",
            partner_position="left_transition",
        ))
        assert gs.players.my_right.y == 35.0
        assert gs.players.my_left.y == 35.0

    def test_ball_position_passthrough(self):
        gs = eval_state_to_game_state(_base_state(
            ball_position={"x": 7.5, "y": 29.0},
        ))
        assert gs.ball.x == 7.5
        assert gs.ball.y == 29.0
