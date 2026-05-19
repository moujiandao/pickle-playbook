"""Schema validation for the live golden_scenarios.jsonl file.

Catches data-level regressions that the pure-logic tests in test_run_eval.py
won't see. Runs against the actual file so a bad scenario edit fails CI even
if the runner code is unchanged.

Validations:
  - Every line is parseable JSON
  - Required fields present (id, state, expert_answer, difficulty)
  - State has all position fields and a ball_position with x/y
  - Skill level in {3.0, 3.5, 4.0, 4.5, 5.0+}
  - Position strings match {left|right}_{kitchen|transition|baseline}
  - Ball x in [0, 20], y in [22, 44] (your side only — game rule)
  - Ball height in {low, mid, high}, speed in {slow, fast}
  - primary_shot + acceptable_alternatives all resolve through shot_taxonomy
  - reasoning_must_mention is a list of strings
  - failure_modes (v2 only) references modes from failure_modes.md
  - IDs are unique
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from shot_taxonomy import classify

_EVALS = Path(__file__).resolve().parents[1]
_SCENARIOS_PATH = _EVALS / "golden_scenarios.jsonl"
_FAILURE_MODES_PATH = _EVALS / "failure_modes.md"

_VALID_SKILLS = {3.0, 3.5, 4.0, 4.5, 5.0, 5.5}
_VALID_SIDES = {"left", "right"}
_VALID_ZONES = {"kitchen", "transition", "baseline"}
_VALID_HEIGHTS = {"low", "mid", "high"}
_VALID_SPEEDS = {"slow", "fast"}
_VALID_DIFFICULTIES = {"obvious", "typical", "tricky", "adversarial"}
_POS_RE = re.compile(r"^(left|right)_(kitchen|transition|baseline)$")


def _load_scenarios() -> list[dict]:
    if not _SCENARIOS_PATH.exists():
        pytest.skip(f"{_SCENARIOS_PATH} not present")
    rows = []
    for i, line in enumerate(_SCENARIOS_PATH.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            pytest.fail(f"line {i}: invalid JSON: {e}")
    return rows


def _declared_failure_modes() -> set[str]:
    """Parse mode IDs (M1, M2, ...) from failure_modes.md headings."""
    if not _FAILURE_MODES_PATH.exists():
        return set()
    text = _FAILURE_MODES_PATH.read_text()
    return set(re.findall(r"^##\s+(M\d+)\b", text, flags=re.MULTILINE))


SCENARIOS = _load_scenarios()
DECLARED_MODES = _declared_failure_modes()


@pytest.fixture(scope="module")
def scenarios() -> list[dict]:
    if not SCENARIOS:
        pytest.skip("golden_scenarios.jsonl is empty")
    return SCENARIOS


def test_at_least_one_scenario(scenarios):
    assert len(scenarios) >= 1


def test_ids_are_unique(scenarios):
    ids = [s["id"] for s in scenarios]
    dupes = [i for i in set(ids) if ids.count(i) > 1]
    assert not dupes, f"duplicate ids: {dupes}"


@pytest.mark.parametrize("s", SCENARIOS, ids=lambda s: s.get("id", "?"))
class TestScenario:
    def test_required_top_level_fields(self, s):
        for field in ("id", "state", "expert_answer", "difficulty"):
            assert field in s, f"missing {field}"

    def test_difficulty_valid(self, s):
        assert s["difficulty"] in _VALID_DIFFICULTIES, (
            f"{s['id']} difficulty={s['difficulty']!r} not in {_VALID_DIFFICULTIES}"
        )

    def test_state_required_fields(self, s):
        state = s["state"]
        for field in (
            "skill_level",
            "me_position",
            "partner_position",
            "opp_left_position",
            "opp_right_position",
            "ball_position",
            "ball_height",
            "ball_speed",
        ):
            assert field in state, f"{s['id']} state missing {field}"

    def test_skill_level_valid(self, s):
        sl = float(s["state"]["skill_level"])
        assert sl in _VALID_SKILLS, f"{s['id']} skill_level={sl} not in {_VALID_SKILLS}"

    def test_position_strings_valid(self, s):
        for field in ("me_position", "partner_position", "opp_left_position", "opp_right_position"):
            val = s["state"][field]
            assert _POS_RE.match(val), f"{s['id']}.{field}={val!r} doesn't match {{side}}_{{zone}}"

    def test_ball_on_your_side(self, s):
        # Per CLAUDE.md: ball can only be dragged on YOUR side (y >= 22).
        ball = s["state"]["ball_position"]
        assert 0 <= ball["x"] <= 20, f"{s['id']} ball.x={ball['x']} out of [0,20]"
        assert 22 <= ball["y"] <= 44, f"{s['id']} ball.y={ball['y']} out of [22,44]"

    def test_ball_height_speed_valid(self, s):
        assert s["state"]["ball_height"] in _VALID_HEIGHTS, f"{s['id']} bad height"
        assert s["state"]["ball_speed"] in _VALID_SPEEDS, f"{s['id']} bad speed"

    def test_expert_answer_required(self, s):
        ea = s["expert_answer"]
        assert "primary_shot" in ea, f"{s['id']} missing primary_shot"
        assert isinstance(ea.get("acceptable_alternatives", []), list)
        assert isinstance(ea.get("reasoning_must_mention", []), list)

    def test_primary_shot_resolves(self, s):
        primary = s["expert_answer"]["primary_shot"]
        assert classify(primary) is not None, (
            f"{s['id']} primary_shot={primary!r} doesn't resolve through shot_taxonomy"
        )

    def test_alternatives_resolve(self, s):
        for alt in s["expert_answer"].get("acceptable_alternatives", []):
            assert classify(alt) is not None, (
                f"{s['id']} alternative={alt!r} doesn't resolve through shot_taxonomy"
            )

    def test_must_mention_keywords_are_strings(self, s):
        for kw in s["expert_answer"].get("reasoning_must_mention", []):
            assert isinstance(kw, str) and kw.strip(), f"{s['id']} bad must_mention entry: {kw!r}"

    def test_failure_modes_valid_if_present(self, s):
        modes = s.get("failure_modes")
        if modes is None:
            return  # v1 schema, optional
        assert isinstance(modes, list) and all(isinstance(m, str) for m in modes)
        if DECLARED_MODES:
            unknown = set(modes) - DECLARED_MODES
            assert not unknown, (
                f"{s['id']} references undeclared modes {unknown}; "
                f"declared in failure_modes.md: {sorted(DECLARED_MODES)}"
            )
