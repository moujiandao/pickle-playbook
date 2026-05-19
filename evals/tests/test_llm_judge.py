"""Tests for llm_judge.py — focuses on parse + prompt construction.

The actual API call to score_response() is not exercised here (it would
require an ANTHROPIC_API_KEY and produce non-deterministic costs). Tests
cover:
  - parse_judge_output: valid JSON, missing field, out-of-range scores,
    fenced output, embedded notes
  - JudgeResult.passed reflects the M4 threshold
  - build_judge_prompt: state cues + recommendation appear; expected_answer
    fields do NOT leak in
"""

from __future__ import annotations

import pytest

from llm_judge import (
    JudgeResult,
    build_judge_prompt,
    parse_judge_output,
)


def _state(**overrides) -> dict:
    base = {
        "skill_level": 4.0,
        "me_position": "right_kitchen",
        "partner_position": "left_kitchen",
        "opp_left_position": "left_kitchen",
        "opp_right_position": "right_kitchen",
        "ball_position": {"x": 15.0, "y": 27.0},
        "ball_height": "high",
        "ball_speed": "slow",
    }
    base.update(overrides)
    return base


# ── parse ──────────────────────────────────────────────────────────────────

class TestParseJudgeOutput:
    def test_valid_5_passes(self):
        raw = '{"ball_state_reading": 5, "notes": "tight"}'
        r = parse_judge_output(raw, model="test-model")
        assert r.ball_state_reading == 5
        assert r.m4_passed is True
        assert r.passed is True
        assert r.score == 1.0
        assert r.notes == "tight"
        assert r.model == "test-model"

    def test_valid_3_just_passes(self):
        raw = '{"ball_state_reading": 3, "notes": "ok"}'
        r = parse_judge_output(raw)
        assert r.passed is True
        assert r.m4_passed is True

    def test_below_threshold_fails(self):
        raw = '{"ball_state_reading": 2, "notes": "missed ball read"}'
        r = parse_judge_output(raw)
        assert r.m4_passed is False
        assert r.passed is False

    def test_score_normalized_to_unit_interval(self):
        # bsr=1 → score=0; bsr=5 → score=1; bsr=3 → score=0.5
        assert parse_judge_output('{"ball_state_reading":1,"notes":""}').score == 0.0
        assert parse_judge_output('{"ball_state_reading":5,"notes":""}').score == 1.0
        assert parse_judge_output('{"ball_state_reading":3,"notes":""}').score == 0.5

    def test_fenced_json_parses(self):
        raw = '```json\n{"ball_state_reading": 3, "notes": "ok"}\n```'
        r = parse_judge_output(raw)
        assert r.ball_state_reading == 3
        assert r.passed is True

    def test_extra_text_around_json_parses(self):
        raw = 'Here is my evaluation:\n{"ball_state_reading": 4, "notes": "good"}\nDone.'
        r = parse_judge_output(raw)
        assert r.ball_state_reading == 4

    def test_missing_ball_state_reading_raises(self):
        with pytest.raises(ValueError, match="missing field: ball_state_reading"):
            parse_judge_output('{"notes": "x"}')

    def test_score_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_judge_output('{"ball_state_reading": 6, "notes": ""}')
        with pytest.raises(ValueError, match="out of range"):
            parse_judge_output('{"ball_state_reading": 0, "notes": ""}')

    def test_no_json_object_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_judge_output("the model refused to respond")

    def test_notes_optional(self):
        r = parse_judge_output('{"ball_state_reading": 4}')
        assert r.notes == ""


# ── prompt construction ────────────────────────────────────────────────────

class TestBuildJudgePrompt:
    def test_state_cues_appear_in_prompt(self):
        recs = [{"name": "Put-Away Volley", "why": "high ball at kitchen"}]
        prompt = build_judge_prompt(recs, _state())
        assert "right_kitchen" in prompt
        assert "high" in prompt          # ball_height
        assert "slow" in prompt          # ball_speed
        assert "Put-Away Volley" in prompt
        assert "high ball at kitchen" in prompt

    def test_no_expert_answer_leaks(self):
        # The state dict and recs are the only inputs; even if a state dict
        # accidentally carries an 'expert_answer' key, build_judge_prompt
        # should not render it. This is the blind-judging guarantee.
        state = _state()
        state["expert_answer"] = {"primary_shot": "put_away_volley"}  # accidentally added
        prompt = build_judge_prompt([{"name": "X", "why": "Y"}], state)
        assert "put_away_volley" not in prompt
        assert "expert_answer" not in prompt

    def test_dimension_named_in_prompt(self):
        prompt = build_judge_prompt([{"name": "X", "why": "Y"}], _state())
        assert "ball_state_reading" in prompt
        # And the failure mode anchors should be visible
        assert "Wrong" in prompt
        assert "Correct" in prompt
        assert "ANCHORS" in prompt

    def test_dropped_dimensions_not_in_prompt(self):
        # M3 (state_use) was retired round 2; v1 dimensions removed earlier.
        prompt = build_judge_prompt([{"name": "X", "why": "Y"}], _state())
        assert "state_use" not in prompt
        assert "strategic_soundness" not in prompt
        assert "reasoning_quality" not in prompt
        assert "specificity" not in prompt
        assert "skill_level_feasible" not in prompt
