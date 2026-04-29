"""shot_taxonomy.py — Pickleball shot classification for eval matching.

Maps canonical golden-set labels OR LLM free-form output to one of 12 families.
`classify(name)` is the public entrypoint. Returns a family name or None if
no rule matches (None = unmatchable, surfaced in eval output as golden-set bug
or LLM vocabulary we don't yet cover).

Design notes:
  - Compound terms are NOT compositional. "drop_volley" is an aggressive
    offensive shot (attack_volley family), NOT a drop. Priority ordering
    resolves this — specific compounds checked before single-word keywords.
  - "Reset" takes precedence over shot *form* ("reset dink" → reset, not dink)
    because reset describes intent, which is what matters for matching.
"""

from __future__ import annotations

import re

# ── canonical labels per family (exact-match vocabulary from golden set) ──

SHOT_FAMILIES: dict[str, list[str]] = {
    "drop": [
        "third_shot_drop", "drop", "let_bounce_and_drop",
    ],
    "drive": [
        "third_shot_drive", "drive", "drive_to_middle", "drive_down_middle",
        "drive_to_opp_right", "drive_to_server_feet",
        "third_shot_drive_to_opp_right",
        "forehand_slap_to_feet", "forehand_roll_to_feet",
        "drive_return_down_line",
    ],
    "reset": [
        "reset", "reset_crosscourt", "reset_from_baseline",
        "backhand_reset_crosscourt", "block_and_reset",
    ],
    "block": [
        "block", "block_volley",
    ],
    "dink": [
        "dink", "dink_crosscourt", "dink_down_line", "dink_down_the_line",
        "crosscourt_dink", "angle_dink", "middle_dink", "angle_dink_sideline",
        "dink_to_middle_T", "sharp_crosscourt_kitchen", "dink_back",
        "dink_crosscourt_for_partner_poach",
    ],
    "speedup": [
        "speedup", "direct_speedup", "speedup_to_body",
        "follow_up_speedup", "bounce_and_speedup",
    ],
    "attack_volley": [
        "attack_volley", "put_away_volley", "roll_volley", "roll_volley_body",
        "cut_angle_volley", "backhand_volley_attack", "volley_before_bounce",
        "drop_volley",
    ],
    "roll": [
        "roll", "backhand_roll",
    ],
    "lob": [
        "lob", "defensive_lob", "lob_over_net_rusher",
    ],
    "overhead": [
        "overhead", "overhead_smash", "let_bounce_then_smash",
    ],
    "serve_return": [
        "serve_deep", "serve_wide", "serve_to_body",
        "deep_return", "topspin_return", "deep_topspin_return",
    ],
    "specialty": [
        "around_the_post", "inside_out_behind_opponent",
    ],
}

# All 12 family names (for validation / iteration elsewhere).
FAMILY_NAMES: frozenset[str] = frozenset(SHOT_FAMILIES.keys())


def _norm(s: str) -> str:
    """Lowercase, collapse non-alphanum to single space, strip.

    Lets 'forehand_roll_to_feet' match 'Forehand Roll to Feet' on exact lookup.
    """
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# Normalized canonical → family, built from SHOT_FAMILIES
_CANONICAL_TO_FAMILY: dict[str, str] = {
    _norm(label): family
    for family, labels in SHOT_FAMILIES.items()
    for label in labels
}


# Priority-ordered keyword rules for LLM free-form text.
# First match wins — compound / specific patterns MUST come before single words.
_KEYWORD_RULES: list[tuple[str, str]] = [
    # Compound attack_volley (drop_volley, put_away, etc.) before "drop"/"volley"
    (r"drop[\s_-]*volley", "attack_volley"),
    (r"put[\s_-]*away", "attack_volley"),
    (r"roll[\s_-]*volley", "attack_volley"),
    (r"attack[\s_-]*volley", "attack_volley"),
    (r"cut[\s_-]*angle[\s_-]*volley", "attack_volley"),
    (r"volley[\s_-]*before[\s_-]*bounce", "attack_volley"),
    (r"backhand[\s_-]*volley[\s_-]*attack", "attack_volley"),

    # Block compounds before bare "block"/"reset"
    (r"block[\s_-]*and[\s_-]*reset", "reset"),
    (r"block[\s_-]*volley", "block"),

    # Specialty compounds
    (r"around[\s_-]*the[\s_-]*post|\batp\b", "specialty"),
    (r"inside[\s_-]*out", "specialty"),

    # Third-shot compounds before bare "drive"/"drop"
    (r"third[\s_-]*shot[\s_-]*drop", "drop"),
    (r"third[\s_-]*shot[\s_-]*drive", "drive"),

    # Unambiguous single-family words
    (r"\boverhead\w*|\bsmash\w*", "overhead"),
    (r"\blob\w*", "lob"),
    (r"\bserve\w*", "serve_return"),
    (r"\breturn\w*", "serve_return"),

    # Reset BEFORE dink/drop/block — "reset dink" is a reset, not a dink
    (r"\breset\w*", "reset"),

    # Remaining single-word families
    (r"\bspeed[\s_-]*up\w*|\bspeedup\w*", "speedup"),
    (r"\bblock\w*", "block"),
    (r"\bdink\w*", "dink"),
    (r"\broll\w*", "roll"),
    (r"\bdrive\w*|\bslap\w*", "drive"),
    (r"\bdrop\w*", "drop"),
]

_COMPILED_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), family)
    for pattern, family in _KEYWORD_RULES
]


def classify(shot_name: str | None) -> str | None:
    """Map a shot name (canonical label OR LLM free-form) → family or None.

    Strategy:
      1. Exact normalized-canonical match (handles 'forehand_roll_to_feet'
         and 'Forehand Roll to Feet' identically).
      2. Priority-ordered keyword fallback for free-form text.
      3. Return None if no rule applies (unmatchable).
    """
    if not shot_name or not shot_name.strip():
        return None

    normalized = _norm(shot_name)
    if normalized in _CANONICAL_TO_FAMILY:
        return _CANONICAL_TO_FAMILY[normalized]

    for pattern, family in _COMPILED_RULES:
        if pattern.search(shot_name):
            return family

    return None


def expected_families(primary: str, alternatives: list[str]) -> tuple[set[str], list[str]]:
    """Classify a golden scenario's expected answers.

    Returns (family_set, unmapped_labels). Empty family_set means the scenario
    is fully unmatchable (all labels unmapped) — caller should flag.
    """
    unmapped: list[str] = []
    families: set[str] = set()

    for label in [primary, *alternatives]:
        fam = classify(label)
        if fam is None:
            unmapped.append(label)
        else:
            families.add(fam)

    return families, unmapped


# ── M2: advanced shot detection ────────────────────────────────────────────

# Shots that require 4.0+ skill to execute reliably. A sub-4.0 player choosing
# any of these is M2 fail. Match logic mirrors classify(): exact normalized
# canonical, then keyword fallback for free-form text.
_ADVANCED_RAW: frozenset[str] = frozenset({
    # specialty family — Ernes, ATPs, behind-the-back
    "around_the_post", "inside_out_behind_opponent",
    # offensive-finesse volleys
    "drop_volley", "roll_volley", "roll_volley_body", "cut_angle_volley",
    "backhand_volley_attack",
    # topspin / spin variants
    "topspin_return", "deep_topspin_return",
    # roll family is fundamentally a 4.0+ shape
    "roll", "backhand_roll",
    # backhand reset cross-court is reliable above 4.0; below it tends to float
    "backhand_reset_crosscourt",
})

# Apply _norm() so lookup can use the same normalization as classify().
ADVANCED_CANONICAL: frozenset[str] = frozenset(_norm(s) for s in _ADVANCED_RAW)

_ADVANCED_KEYWORDS = [
    re.compile(r"\bern[ey]?s?\b", re.IGNORECASE),             # erne / erney / ernes
    re.compile(r"around[\s_-]*the[\s_-]*post|\batp\b", re.IGNORECASE),
    re.compile(r"\btopspin\w*", re.IGNORECASE),
    re.compile(r"roll[\s_-]*volley", re.IGNORECASE),
    re.compile(r"drop[\s_-]*volley", re.IGNORECASE),
    re.compile(r"cut[\s_-]*angle", re.IGNORECASE),
    re.compile(r"inside[\s_-]*out", re.IGNORECASE),
]


def is_advanced_shot(shot_name: str | None) -> bool:
    """Return True if `shot_name` requires 4.0+ skill to execute reliably.

    Used for M2 (skill-level overreach) deterministic check: if the player is
    sub-4.0 and the recommendation is_advanced_shot → fail M2.
    """
    if not shot_name or not shot_name.strip():
        return False
    if _norm(shot_name) in ADVANCED_CANONICAL:
        return True
    return any(p.search(shot_name) for p in _ADVANCED_KEYWORDS)


# ── M5: tactical mode (offense / defense / neutral) ───────────────────────

# Map shot families → posture. drop and dink are neutral/setup; the deterministic
# rule errs toward neutral when a family supports multiple intents (e.g. drive
# can be a third-shot setup or an attack — caller can't tell from the family
# name alone, so we use the dominant case).
_FAMILY_POSTURE: dict[str, str] = {
    "drop": "neutral",
    "drive": "offensive",
    "reset": "defensive",
    "block": "defensive",
    "dink": "neutral",
    "speedup": "offensive",
    "attack_volley": "offensive",
    "roll": "offensive",
    "lob": "defensive",
    "overhead": "offensive",
    "serve_return": "neutral",
    "specialty": "offensive",
}


def shot_posture(shot_name: str | None) -> str | None:
    """Classify a shot's tactical posture: 'offensive' | 'defensive' | 'neutral'.

    Returns None when the shot doesn't classify (unmapped family). Built on
    top of classify() so anything classify() handles, this handles too.
    """
    fam = classify(shot_name)
    if fam is None:
        return None
    return _FAMILY_POSTURE.get(fam)


# Decision table for expected tactical mode.
# Keyed by (me_zone, ball_height, ball_speed). me_zone is parsed from
# state.me_position (e.g. 'right_baseline' → 'baseline'). Speed is collapsed
# when the cell doesn't depend on it ('any' wildcard handled in lookup).
_MODE_TABLE: dict[tuple[str, str, str], str] = {
    # kitchen
    ("kitchen", "high", "any"):  "offensive",
    ("kitchen", "mid",  "slow"): "offensive",
    ("kitchen", "mid",  "fast"): "neutral",
    ("kitchen", "low",  "any"):  "neutral",
    # transition
    ("transition", "high", "any"):  "offensive",
    ("transition", "mid",  "any"):  "neutral",
    ("transition", "low",  "fast"): "defensive",
    ("transition", "low",  "slow"): "neutral",
    # baseline (third-shot territory — always setup, dominantly neutral)
    ("baseline", "any", "any"): "neutral",
}


def expected_tactical_mode(state: dict) -> str | None:
    """Compute expected tactical mode from game state.

    Inputs read: state['me_position'], state['ball_height'], state['ball_speed'].
    Returns None if state is malformed or zone/height/speed are unrecognized.
    """
    me = state.get("me_position", "")
    height = state.get("ball_height")
    speed = state.get("ball_speed")
    if "_" not in me or height is None or speed is None:
        return None
    zone = me.rsplit("_", 1)[-1]
    if zone not in {"kitchen", "transition", "baseline"}:
        return None

    # Try most specific match first, then progressively wildcard speed/height.
    for h, s in ((height, speed), (height, "any"), ("any", speed), ("any", "any")):
        mode = _MODE_TABLE.get((zone, h, s))
        if mode is not None:
            return mode
    return None


def expected_postures(primary: str, alternatives: list[str]) -> set[str]:
    """Posture set for all acceptable shots in a scenario.

    A model prediction passes M5 if its posture is in this set. Lets a scenario
    with primary=drop (neutral) and alt=drive (offensive) accept either posture.
    """
    postures: set[str] = set()
    for label in [primary, *alternatives]:
        p = shot_posture(label)
        if p is not None:
            postures.add(p)
    return postures
