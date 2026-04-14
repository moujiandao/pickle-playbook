"""Heuristic strategy engine.

Mock stand-in for the eventual RAG+Claude pipeline. Branches on ball zone,
height, speed, and spin to emit 2-3 shot recommendations, each with a
3-step rally (you -> opponent -> you).
"""

from app.schemas.game_state import GameState, RallyStep, ShotRecommendation
from app.services.position_describer import (
    ball_zone,
    describe_position,
    lateral_label,
    zone_of,
)


def _opponent_pressure(state: GameState) -> str:
    opp_left_zone = zone_of(state.players.opp_left.y, "far")
    opp_right_zone = zone_of(state.players.opp_right.y, "far")
    if opp_left_zone == "kitchen" and opp_right_zone == "kitchen":
        return "both_kitchen"
    if opp_left_zone == "baseline" or opp_right_zone == "baseline":
        return "one_back"
    return "mixed"


def _middle_gap(state: GameState) -> float:
    return abs(state.players.opp_right.x - state.players.opp_left.x)


def recommend(state: GameState) -> list[ShotRecommendation]:
    b = state.ball
    zone = ball_zone(b.y)
    ball_where = describe_position(b.x, b.y, "near")
    opp_pressure = _opponent_pressure(state)
    gap = _middle_gap(state)
    ball_side = lateral_label(b.x)

    me_label = "You"
    partner_label = "Partner"

    recs: list[ShotRecommendation] = []

    if zone == "kitchen" and b.height == "low":
        why_parts = [f"Ball is low in the kitchen ({ball_where})."]
        if opp_pressure == "both_kitchen":
            why_parts.append("Both opponents are at the kitchen line, so attacks are low-percentage.")
        cross_target = "right" if ball_side == "left sideline" else "left"
        recs.append(
            ShotRecommendation(
                name="Cross-Court Dink",
                why=" ".join(why_parts) + " A cross-court dink has the longest available landing zone and pulls them wide.",
                rally=[
                    RallyStep(
                        shot=1, who=me_label,
                        action=f"Soft cross-court dink to the {cross_target} side of their kitchen.",
                        result="Lands just over the net, forcing a stretched reply.",
                    ),
                    RallyStep(
                        shot=2, who="Opponent",
                        action=f"Opponent on the {cross_target} dinks back, likely to your middle.",
                        result="Ball pops up slightly as they reach wide.",
                    ),
                    RallyStep(
                        shot=3, who=partner_label,
                        action="Partner steps in and redirects the dink to the open middle seam.",
                        result="Splits the defenders and forces a defensive reset.",
                    ),
                ],
            )
        )
        if gap >= 8:
            recs.append(
                ShotRecommendation(
                    name="Middle Dink Probe",
                    why=f"Opponents are spread ({gap:.0f}ft apart). A dink up the middle creates confusion over who takes it.",
                    rally=[
                        RallyStep(shot=1, who=me_label, action="Controlled dink into the middle of their kitchen.", result="Lands between both opponents, causing hesitation."),
                        RallyStep(shot=2, who="Opponent", action="One opponent reaches across and pops the ball up.", result="Weak reply floats above net height."),
                        RallyStep(shot=3, who=me_label, action="Step in and put the ball away with a controlled roll.", result="Point won on the attack."),
                    ],
                )
            )
        recs.append(
            ShotRecommendation(
                name="Reset and Reload",
                why="If the angle is tight, a soft reset into the kitchen keeps you in the point without overcommitting.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Cushioned reset into the center of their kitchen.", result="Neutralizes pace, buys time to reset your feet."),
                    RallyStep(shot=2, who="Opponent", action="Opponent dinks back to continue the exchange.", result="Neutral kitchen rally."),
                    RallyStep(shot=3, who=partner_label, action="Partner takes over the dink battle from a balanced stance.", result="Maintains neutral rally position."),
                ],
            )
        )
        return recs[:3]

    if zone == "kitchen" and b.height in ("mid", "high"):
        recs.append(
            ShotRecommendation(
                name="Speed-Up Attack",
                why=f"Ball is at {b.height} height in the kitchen ({ball_where}). That's attackable before it drops.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Short backswing speed-up at the opponent's hip.", result="Forces a reactive, high reply."),
                    RallyStep(shot=2, who="Opponent", action="Opponent blocks upward, ball floats.", result="Ball sits up in the kitchen zone."),
                    RallyStep(shot=3, who=partner_label, action="Partner crashes in and puts the floater away.", result="Point ends on the put-away."),
                ],
            )
        )
        recs.append(
            ShotRecommendation(
                name="Topspin Roll",
                why="Rolling topspin keeps the ball low over the net while still carrying bite.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Low-to-high topspin roll aimed at the far shoulder.", result="Dips fast into the kitchen, hard to read."),
                    RallyStep(shot=2, who="Opponent", action="Opponent pops the roll up off the paddle face.", result="Short, floaty return."),
                    RallyStep(shot=3, who=me_label, action="Finish overhead into the open court.", result="Unanswered winner."),
                ],
            )
        )
        return recs

    if zone == "transition":
        recs.append(
            ShotRecommendation(
                name="Third-Shot Drop",
                why=f"Ball is in the transition zone ({ball_where}). A drop buys time to get to the kitchen.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Soft third-shot drop landing in the middle of their kitchen.", result="Forces them to hit up; you advance."),
                    RallyStep(shot=2, who="Opponent", action="Opponent dinks back crosscourt.", result="Neutral kitchen exchange begins."),
                    RallyStep(shot=3, who=partner_label, action="Partner and you reach the kitchen line together.", result="Even kitchen battle established."),
                ],
            )
        )
        if opp_pressure == "one_back":
            recs.append(
                ShotRecommendation(
                    name="Drive at the Deep Opponent",
                    why="One opponent is still back. Drive at their feet before they establish position.",
                    rally=[
                        RallyStep(shot=1, who=me_label, action="Flat drive at the feet of the deeper opponent.", result="Forces a tough half-volley."),
                        RallyStep(shot=2, who="Opponent", action="Deep opponent blocks the drive short and high.", result="Ball sits up in the transition zone."),
                        RallyStep(shot=3, who=partner_label, action="Partner steps in and attacks the floater.", result="Put-away into open court."),
                    ],
                )
            )
        return recs

    # zone == "baseline"
    recs.append(
        ShotRecommendation(
            name="Third-Shot Drop from the Baseline",
            why=f"Ball is near your baseline ({ball_where}). A controlled drop is the highest-percentage advance.",
            rally=[
                RallyStep(shot=1, who=me_label, action="Compact third-shot drop to the middle of their kitchen.", result="Gives you time to advance to the transition zone."),
                RallyStep(shot=2, who="Opponent", action="Opponent dinks the drop back to your partner's side.", result="Neutral kitchen dink begins."),
                RallyStep(shot=3, who=partner_label, action="Partner resets into the kitchen and holds position.", result="Both teams at the kitchen line."),
            ],
        )
    )
    if b.speed == "fast":
        recs.append(
            ShotRecommendation(
                name="Topspin Drive",
                why="A fast ball from the baseline can be converted into a heavy topspin drive that dips at their feet.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Topspin drive at the weaker opponent's hip.", result="Forces a defensive block."),
                    RallyStep(shot=2, who="Opponent", action="Opponent blocks the drive short.", result="Ball lands mid-court."),
                    RallyStep(shot=3, who=me_label, action="Follow the drive in and put away the short block.", result="Aggressive advance to the kitchen."),
                ],
            )
        )
    return recs
