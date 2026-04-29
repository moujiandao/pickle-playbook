"""Tests for shot_taxonomy.classify() and expected_families().

Covers:
  - canonical labels per family
  - priority ordering: compound terms win over single-word keywords
  - case / whitespace / punctuation insensitivity
  - unmappable inputs return None
  - expected_families() aggregates across primary + alternatives
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure evals/ is on path
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shot_taxonomy import FAMILY_NAMES, classify, expected_families


class TestFamilyNames:
    def test_twelve_families(self):
        assert len(FAMILY_NAMES) == 12

    def test_all_core_families_present(self):
        expected = {
            "drop", "drive", "reset", "block", "dink", "speedup",
            "attack_volley", "roll", "lob", "overhead", "serve_return", "specialty",
        }
        assert FAMILY_NAMES == expected


class TestCanonicalLabels:
    """Each canonical label in SHOT_FAMILIES must classify to its family."""

    def test_drop(self):
        assert classify("third_shot_drop") == "drop"
        assert classify("drop") == "drop"
        assert classify("let_bounce_and_drop") == "drop"

    def test_drive(self):
        assert classify("third_shot_drive") == "drive"
        assert classify("drive_to_middle") == "drive"
        assert classify("drive_down_middle") == "drive"
        assert classify("drive_return_down_line") == "drive"
        assert classify("forehand_slap_to_feet") == "drive"

    def test_reset(self):
        assert classify("reset") == "reset"
        assert classify("reset_crosscourt") == "reset"
        assert classify("backhand_reset_crosscourt") == "reset"

    def test_dink(self):
        assert classify("dink") == "dink"
        assert classify("crosscourt_dink") == "dink"
        assert classify("dink_down_the_line") == "dink"
        assert classify("angle_dink_sideline") == "dink"

    def test_speedup(self):
        assert classify("speedup") == "speedup"
        assert classify("speedup_to_body") == "speedup"
        assert classify("bounce_and_speedup") == "speedup"

    def test_attack_volley(self):
        assert classify("attack_volley") == "attack_volley"
        assert classify("put_away_volley") == "attack_volley"
        assert classify("roll_volley_body") == "attack_volley"

    def test_lob_overhead_serve(self):
        assert classify("lob") == "lob"
        assert classify("defensive_lob") == "lob"
        assert classify("overhead") == "overhead"
        assert classify("overhead_smash") == "overhead"
        assert classify("serve_wide") == "serve_return"
        assert classify("deep_topspin_return") == "serve_return"

    def test_block_roll_specialty(self):
        assert classify("block") == "block"
        assert classify("block_volley") == "block"
        assert classify("roll") == "roll"
        assert classify("backhand_roll") == "roll"
        assert classify("around_the_post") == "specialty"
        assert classify("inside_out_behind_opponent") == "specialty"


class TestCompoundPriority:
    """Compound terms must beat single-word keywords."""

    def test_drop_volley_is_attack_volley_not_drop(self):
        # drop_volley is an offensive volley, NOT a drop
        assert classify("drop_volley") == "attack_volley"
        assert classify("Drop Volley") == "attack_volley"
        assert classify("drop-volley") == "attack_volley"

    def test_block_and_reset_is_reset_not_block(self):
        assert classify("block_and_reset") == "reset"
        assert classify("Block and Reset") == "reset"

    def test_block_volley_is_block(self):
        assert classify("block_volley") == "block"

    def test_put_away_is_attack_volley(self):
        assert classify("put away") == "attack_volley"
        assert classify("put_away_volley") == "attack_volley"

    def test_third_shot_drop_is_drop_not_drive(self):
        assert classify("third_shot_drop") == "drop"

    def test_third_shot_drive_is_drive_not_drop(self):
        assert classify("third_shot_drive") == "drive"

    def test_reset_beats_shot_form(self):
        # "reset dink" describes intent → reset, not dink
        assert classify("reset dink") == "reset"
        assert classify("reset drop") == "reset"


class TestFreeFormLLM:
    """Classify LLM free-form prose into a family."""

    def test_capitalized_and_spaced(self):
        assert classify("Cross-court dink with topspin") == "dink"
        assert classify("Deep Drop Shot to Reset") == "reset"  # reset wins
        assert classify("Overhead Smash") == "overhead"

    def test_atp_abbrev_is_specialty(self):
        assert classify("ATP") == "specialty"
        assert classify("Around The Post") == "specialty"

    def test_serve_and_return(self):
        assert classify("deep serve to body") == "serve_return"
        assert classify("topspin return") == "serve_return"


class TestUnmappableInputs:
    def test_none_returns_none(self):
        assert classify(None) is None

    def test_empty_string_returns_none(self):
        assert classify("") is None

    def test_whitespace_only_returns_none(self):
        assert classify("   ") is None

    def test_nonsense_returns_none(self):
        assert classify("xyzzy foo bar") is None


class TestExpectedFamilies:
    def test_single_primary(self):
        fams, unmapped = expected_families("third_shot_drive", [])
        assert fams == {"drive"}
        assert unmapped == []

    def test_primary_plus_alternatives(self):
        fams, unmapped = expected_families(
            "third_shot_drop", ["third_shot_drive", "drive_to_middle"]
        )
        assert fams == {"drop", "drive"}
        assert unmapped == []

    def test_unmapped_labels_surfaced(self):
        fams, unmapped = expected_families("third_shot_drive", ["nonsense", "bogus"])
        assert fams == {"drive"}
        assert unmapped == ["nonsense", "bogus"]

    def test_all_unmapped(self):
        fams, unmapped = expected_families("xyzzy", ["foobar"])
        assert fams == set()
        assert unmapped == ["xyzzy", "foobar"]
