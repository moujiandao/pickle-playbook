"""Tests for eval runner scoring logic.

Covers score_scenario (family-based shot_match + reasoning_coverage),
_quadrant, and eval_state_to_game_state. The recommend() function is NOT
called — tests are purely about the scoring layer.
"""

import sys
from pathlib import Path

import pytest  # noqa: F401

# Ensure evals/ and backend/ are on path before importing run_eval
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
for _p in (_HERE, _REPO / "backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from run_eval import _quadrant, eval_state_to_game_state, score_scenario


# ── helpers ────────────────────────────────────────────────────────────────

class _Rec:
    """Minimal stand-in for ShotRecommendation."""
    def __init__(self, name: str, why: str = ""):
        self.name = name
        self.why = why


def _scenario(primary: str, alternatives=None, must_mention=None, sid="t001", state=None):
    return {
        "id": sid,
        "difficulty": "obvious",
        "state": state or _base_state(),
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


# ── score_scenario — family-based shot match ───────────────────────────────

class TestShotMatch:
    def test_same_family_matches(self):
        recs = [_Rec("Third-Shot Drop from the Baseline")]
        result = score_scenario(_scenario("third_shot_drop"), recs)
        assert result["shot_match"] is True
        assert result["predicted_family"] == "drop"
        assert result["expected_families"] == ["drop"]

    def test_acceptable_alternative_family_matches(self):
        recs = [_Rec("Drive down the middle")]
        result = score_scenario(
            _scenario("third_shot_drop", alternatives=["third_shot_drive"]), recs
        )
        assert result["shot_match"] is True
        assert result["predicted_family"] == "drive"
        assert set(result["expected_families"]) == {"drop", "drive"}

    def test_different_family_no_match(self):
        recs = [_Rec("Speed-Up Attack")]
        result = score_scenario(_scenario("third_shot_drop"), recs)
        assert result["shot_match"] is False
        assert result["predicted_family"] == "speedup"

    def test_unmappable_prediction_is_miss(self):
        recs = [_Rec("Some Nonsense Shot")]
        result = score_scenario(_scenario("drop"), recs)
        assert result["shot_match"] is False
        assert result["predicted_family"] is None

    def test_empty_recs_no_crash(self):
        result = score_scenario(_scenario("third_shot_drop"), [])
        assert result["shot_match"] is False
        assert result["predicted_shot"] is None
        assert result["predicted_family"] is None

    def test_predicted_and_expected_recorded(self):
        recs = [_Rec("Cross-Court Dink")]
        result = score_scenario(_scenario("crosscourt_dink"), recs)
        assert result["predicted_shot"] == "Cross-Court Dink"
        assert result["expected_primary"] == "crosscourt_dink"

    def test_compound_drop_volley_is_attack_volley_not_drop(self):
        # drop_volley ≠ drop. If golden says drop, a drop_volley prediction must miss.
        recs = [_Rec("Drop Volley")]
        result = score_scenario(_scenario("third_shot_drop"), recs)
        assert result["shot_match"] is False
        assert result["predicted_family"] == "attack_volley"

    def test_unmapped_expected_labels_surfaced(self):
        # Alt label that classify() can't map should appear in unmapped_expected_labels
        recs = [_Rec("Drive")]
        result = score_scenario(
            _scenario("third_shot_drive", alternatives=["bogus_label"]), recs
        )
        assert "bogus_label" in result["unmapped_expected_labels"]


# ── score_scenario — reasoning coverage (diagnostic only, not a gate) ─────

class TestReasoningCoverage:
    def test_full_coverage(self):
        recs = [_Rec("Drop", "drop into the kitchen then advance")]
        result = score_scenario(_scenario("drop", must_mention=["kitchen", "advance"]), recs)
        assert result["reasoning_coverage"] == 1.0

    def test_partial_coverage(self):
        recs = [_Rec("Drop", "drop into the kitchen")]
        result = score_scenario(
            _scenario("drop", must_mention=["kitchen", "advance", "time"]), recs
        )
        assert result["reasoning_coverage"] == 0.333

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


# ── quadrant math ──────────────────────────────────────────────────────────

class TestQuadrant:
    def test_right_shot_good_reasoning(self):
        assert _quadrant(True, True) == "right_shot_good_reasoning"

    def test_right_shot_bad_reasoning(self):
        assert _quadrant(True, False) == "right_shot_bad_reasoning"

    def test_wrong_shot_good_reasoning_is_dangerous(self):
        # Judge rationalizing a wrong pick — most dangerous quadrant
        assert _quadrant(False, True) == "wrong_shot_good_reasoning"

    def test_wrong_shot_bad_reasoning(self):
        assert _quadrant(False, False) == "wrong_shot_bad_reasoning"


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


# ── M2 — advanced shot for sub-4.0 player (deterministic) ─────────────────

class TestM2AdvancedShotViolation:
    def test_advanced_shot_at_3_5_is_violation(self):
        # 3.5 player + Erne recommendation = M2 fail
        recs = [_Rec("Erne to the line")]
        scen = _scenario(
            "crosscourt_dink",
            state=_base_state(skill_level=3.5),
        )
        result = score_scenario(scen, recs)
        assert result["m2_advanced_shot_violation"] is True

    def test_advanced_shot_at_4_0_is_not_violation(self):
        # 4.0 player + Erne = no M2 violation (player is capable)
        recs = [_Rec("Erne winner")]
        scen = _scenario(
            "crosscourt_dink",
            state=_base_state(skill_level=4.0),
        )
        result = score_scenario(scen, recs)
        assert result["m2_advanced_shot_violation"] is False

    def test_basic_shot_at_3_0_is_not_violation(self):
        recs = [_Rec("Cross-court Dink")]
        scen = _scenario(
            "crosscourt_dink",
            state=_base_state(skill_level=3.0),
        )
        result = score_scenario(scen, recs)
        assert result["m2_advanced_shot_violation"] is False

    def test_topspin_at_3_5_is_violation(self):
        recs = [_Rec("Topspin Roll Volley")]
        scen = _scenario("dink", state=_base_state(skill_level=3.5))
        result = score_scenario(scen, recs)
        assert result["m2_advanced_shot_violation"] is True

    def test_no_recs_no_violation(self):
        scen = _scenario("dink", state=_base_state(skill_level=3.0))
        result = score_scenario(scen, [])
        assert result["m2_advanced_shot_violation"] is False


# ── M5 — tactical mode (posture) match (deterministic) ────────────────────

class TestM5TacticalModeMatch:
    def test_offensive_predicted_when_offensive_expected(self):
        # State: high ball at kitchen → offensive expected.
        # Predicted: put_away_volley → offensive. Match.
        recs = [_Rec("Put Away Volley")]
        scen = _scenario(
            "put_away_volley",
            state=_base_state(ball_height="high", ball_speed="slow"),
        )
        result = score_scenario(scen, recs)
        assert result["m5_tactical_mode_match"] is True
        assert result["expected_tactical_mode"] == "offensive"
        assert result["predicted_posture"] == "offensive"

    def test_defensive_predicted_when_defensive_expected(self):
        # State: low fast ball at transition → defensive expected.
        recs = [_Rec("Reset to kitchen")]
        scen = _scenario(
            "reset",
            state=_base_state(
                me_position="right_transition",
                ball_height="low", ball_speed="fast",
            ),
        )
        result = score_scenario(scen, recs)
        assert result["m5_tactical_mode_match"] is True
        assert result["expected_tactical_mode"] == "defensive"

    def test_offensive_predicted_when_defensive_expected_is_mismatch(self):
        # State: low fast at transition → defensive. Model picks drive (offensive). Fail.
        recs = [_Rec("Drive at the body")]
        scen = _scenario(
            "reset",
            state=_base_state(
                me_position="right_transition",
                ball_height="low", ball_speed="fast",
            ),
        )
        result = score_scenario(scen, recs)
        assert result["m5_tactical_mode_match"] is False
        assert result["predicted_posture"] == "offensive"

    def test_alternatives_widen_acceptable_postures(self):
        # v2_001 case: primary=drop (neutral), alt=drive (offensive).
        # Model picks drive — should pass M5 because offensive is in expected_postures.
        recs = [_Rec("Third-shot drive")]
        scen = _scenario(
            "third_shot_drop",
            alternatives=["third_shot_drive"],
            state=_base_state(
                me_position="right_baseline",
                ball_position={"x": 15.0, "y": 40.0},
                ball_height="mid", ball_speed="slow",
            ),
        )
        result = score_scenario(scen, recs)
        assert result["m5_tactical_mode_match"] is True
        assert "offensive" in result["expected_postures"]
        assert "neutral" in result["expected_postures"]

    def test_unmappable_predicted_returns_false_match(self):
        recs = [_Rec("Garbage non-shot")]
        scen = _scenario("dink", state=_base_state())
        result = score_scenario(scen, recs)
        assert result["m5_tactical_mode_match"] is False
        assert result["predicted_posture"] is None

    def test_no_recs_match_is_false(self):
        scen = _scenario("dink", state=_base_state())
        result = score_scenario(scen, [])
        # No prediction → can't match
        assert result["m5_tactical_mode_match"] is False
