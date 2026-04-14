"""Tests for position_describer — coordinate-to-NL translation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from position_describer import (
    describe_player,
    describe_ball,
    describe_situation,
    make_retrieval_query,
    NET_Y,
    KITCHEN_NEAR,
    KITCHEN_FAR,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state(
    my_left_y=37.0, my_right_y=37.0,
    opp_left_y=7.0, opp_right_y=7.0,
    ball_x=10.0, ball_y=33.0,
    height="mid", speed="slow", spin=None,
    my_side="left",
) -> dict:
    return {
        "my_side": my_side,
        "players": {
            "my_left":  {"x": 5.0, "y": my_left_y},
            "my_right": {"x": 15.0, "y": my_right_y},
            "opp_left": {"x": 5.0, "y": opp_left_y},
            "opp_right": {"x": 15.0, "y": opp_right_y},
        },
        "ball": {"x": ball_x, "y": ball_y, "height": height, "speed": speed, "spin": spin},
    }


# ---------------------------------------------------------------------------
# describe_player
# ---------------------------------------------------------------------------

def test_player_at_kitchen_line():
    desc = describe_player(10.0, KITCHEN_NEAR, "my_left", my_side="left")
    assert "kitchen" in desc.lower()


def test_player_at_baseline():
    desc = describe_player(10.0, 42.0, "my_left", my_side="left")
    assert "baseline" in desc.lower()


def test_player_me_label_left_side():
    desc = describe_player(5.0, 37.0, "my_left", my_side="left")
    assert "ME" in desc or "You" in desc


def test_player_me_label_right_side():
    desc = describe_player(15.0, 37.0, "my_right", my_side="right")
    assert "ME" in desc or "You" in desc


def test_opponent_zone_at_kitchen():
    desc = describe_player(10.0, KITCHEN_FAR, "opp_left", my_side="left")
    assert "kitchen" in desc.lower()


def test_opponent_label_present():
    desc = describe_player(5.0, 7.0, "opp_right", my_side="left")
    assert "Opponent" in desc


# ---------------------------------------------------------------------------
# describe_ball
# ---------------------------------------------------------------------------

def test_ball_in_kitchen():
    desc = describe_ball({"x": 10.0, "y": 25.0, "height": "low", "speed": "slow", "spin": None})
    assert "kitchen" in desc.lower()


def test_ball_height_present():
    desc = describe_ball({"x": 10.0, "y": 33.0, "height": "high", "speed": "fast", "spin": "topspin"})
    assert "high" in desc.lower()
    assert "topspin" in desc.lower()


def test_ball_spin_omitted_when_none():
    desc = describe_ball({"x": 10.0, "y": 33.0, "height": "mid", "speed": "slow", "spin": None})
    assert "spin" not in desc.lower()


# ---------------------------------------------------------------------------
# describe_situation
# ---------------------------------------------------------------------------

def test_situation_contains_all_players():
    state = _state()
    situation = describe_situation(state)
    assert "my_left" in situation.lower() or "partner" in situation.lower() or "You" in situation
    assert "Opponent" in situation


def test_situation_contains_ball():
    situation = describe_situation(_state())
    assert "Ball" in situation


def test_situation_contains_tactical_context():
    situation = describe_situation(_state())
    assert "Phase" in situation or "phase" in situation


# ---------------------------------------------------------------------------
# make_retrieval_query
# ---------------------------------------------------------------------------

def test_query_both_at_kitchen():
    state = _state(my_left_y=KITCHEN_NEAR, my_right_y=KITCHEN_NEAR,
                   opp_left_y=KITCHEN_FAR, opp_right_y=KITCHEN_FAR)
    query = make_retrieval_query(state)
    assert "kitchen" in query.lower()


def test_query_team_at_baseline():
    state = _state(my_left_y=40.0, my_right_y=40.0)
    query = make_retrieval_query(state)
    assert "baseline" in query.lower()


def test_query_ball_in_kitchen():
    state = _state(ball_y=25.0)
    query = make_retrieval_query(state)
    assert "kitchen" in query.lower()


def test_query_includes_ball_height():
    state = _state(height="high")
    query = make_retrieval_query(state)
    assert "high" in query.lower()


def test_query_includes_spin_when_present():
    state = _state(spin="topspin", ball_y=25.0)
    query = make_retrieval_query(state)
    assert "topspin" in query.lower()
