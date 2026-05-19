# Eval Failure Modes — Pickle Playbook

> This file is the contamination guard. We write down what the eval must catch
> *before* writing scenarios or the judge prompt. Every scenario in
> `golden_scenarios.jsonl` and every dimension in `lib/llm_judge.py` should
> trace back to one of the modes below. If a future change can't cite a mode
> here, the eval is drifting.

**Status:** Round 2 reviewed by Brian on 2026-05-13.
Changes from round 1:
- Old M2 (skill-level overreach) **removed**. The binary advanced-shot gate
  was too narrow to be load-bearing (caught "Erne to a 3.5", missed strategic
  mismatches), and dropping it leaves room to reintroduce a sharper skill
  check later if production traces demand it.
- Old M3 (state-blind reasoning) **removed**. It was doing two jobs — grading
  generic *language* and grading position-*reasoning* — and one Likert can't
  cleanly grade both. Future replacement, if any, should be split into narrow
  binary judges driven by real traces.
- Numbering preserved: surviving modes are still **M1, M4, M5** so archived
  result JSON and historical commits keep referring to the same concepts.

**Detection summary after round 2:** M1 and M5 are **deterministic**;
M4 uses the LLM judge. The judge prompt only has to grade one dimension.

**Last updated:** 2026-05-13

---

## How to read each mode

Each entry has four parts:

1. **Description** — one sentence on what the failure looks like
2. **Concrete example** — a real or plausible case where the model fails this way
3. **Why it matters** — what bad thing happens if the eval misses this mode
4. **Detection mechanism** — which layer catches it (deterministic check, LLM judge dimension, scenario design)

---

## M1 — Wrong shot family

**Description:** Model recommends a shot from a different tactical family than what the situation calls for (e.g. drive when a drop is correct, attack when a reset is correct).

**Concrete example:** Ball is at your baseline (y=40), opponents at the kitchen line. Model recommends "Cross-court drive" — but at the baseline against a kitchen-line wall, the canonical answer is third-shot drop, because a drive feeds a wall of paddles you can't get past. Drop family ≠ drive family.

**Why it matters:** This is the most basic test of pickleball strategy. If the model can't distinguish drop from drive in textbook situations, no amount of nice prose hides that.

**Detection mechanism:** Deterministic — `shot_match` via `lib/shot_taxonomy.py`. Predicted shot text is mapped to a family; family must equal `expected_primary` family or be in `acceptable_alternatives`.

---

## M4 — Misreads ball state

**Description:** Model treats a defensive ball as attackable, or treats an attackable ball as defensive. Specifically: ball height (low / mid / high) and ball speed (slow / fast) are read incorrectly. This is distinct from M5 (offense vs defense pick) — M4 is about reading the *ball*, M5 is about the *strategic call*.

**Concrete example:** State has `ball_height: high` at the kitchen line. The right answer is a put-away volley — high ball at the kitchen is a textbook attack opportunity. Model recommends a "soft dink reset" because it's pattern-matching on "kitchen = dink" without checking the height. Defensive shot on an offensive ball.

**Why it matters:** This is the failure mode that exposes the model not actually parsing the state, just pattern-matching on superficial cues like court zone.

**Detection mechanism:** LLM judge Likert dimension — `ball_state_reading` (1–5). Anchor at 5: reasoning explicitly mentions ball height/speed and recommendation matches that posture. Anchor at 1: reasoning contradicts the ball state (e.g. "soft block this slow high ball" when the ball is sitting up).

---

## M5 — Wrong tactical mode (offense vs defense)

**Description:** Model picks the wrong tactical *posture* for the situation. Should attack but plays defense, or should defend but plays offense. This is a layer above M1 (wrong family within a posture) — you can pick the wrong family while still picking the right posture, and vice versa.

**Concrete examples:**
- *Should attack but didn't:* High ball at the kitchen, opponents at the kitchen, you and partner at the kitchen. Right call = offense (put-away). Model picks a soft dink reset — defense when offense is correct.
- *Should defend but didn't:* Low fast ball at your transition zone with opponents at the kitchen. Right call = defense (reset / block). Model picks a drive at the body — offense when defense is correct.

**Why it matters:** This is the most strategic failure — a model that can't tell offense from defense is missing the central judgment of the sport. Often correlates with M4 (if you misread the ball, you'll often pick the wrong mode), but they're separable: a model can read the ball correctly and still pick the wrong posture for it.

**Detection mechanism: fully deterministic, no judge.**

The expected tactical mode is *derivable from the state* — given me's court zone, ball height, ball speed, and opponent positions, the right posture is determined. Two functions, both in `lib/shot_taxonomy.py`:

1. **`expected_tactical_mode(state) → "offensive" | "defensive" | "neutral"`** — applies a decision rule. First cut:

   | me_zone | ball_height | ball_speed | expected mode |
   |---|---|---|---|
   | kitchen | high | any | offensive (attack) |
   | kitchen | mid | slow | offensive (roll/attack) |
   | kitchen | mid | fast | neutral (controlled volley) |
   | kitchen | low | any | neutral (dink rally) |
   | transition | high | any | offensive |
   | transition | low | fast | defensive (reset) |
   | transition | low | slow | neutral |
   | transition | mid | any | neutral |
   | baseline | any | any | neutral (setup — drop or drive) |

   Edges that don't fit cleanly should not be in the golden set; if they're tactically ambiguous, they're not good eval cases anyway.

2. **`shot_posture(shot_text) → "offensive" | "defensive" | "neutral"`** — classifies what posture the recommended shot represents. Similar to `classify()` for families:
   - `attack_volley`, `speedup`, `overhead`, `roll`, `specialty` → offensive
   - `reset`, `block`, `lob` (defensive) → defensive
   - `dink`, `drop` (neutral/setup), `serve_return` → neutral
   - `drive` → offensive in third-shot context, but neutral/setup mostly. Lean offensive.

**M5 check:** if `expected_tactical_mode(state) != shot_posture(predicted_shot)` → M5 fail.

This means M5 (along with M1) is fully deterministic. Only M4 (ball-state reading) needs the LLM judge.

---

## Coverage matrix (to fill out during Phase 3)

| Failure mode | # scenarios | Difficulty mix |
|---|---|---|
| M1 wrong shot family | TBD | TBD |
| M4 misreads ball state | TBD | TBD |
| M5 wrong tactical mode | TBD | TBD |

Target: 4–5 scenarios per mode, ~15 total. Scenarios may probe multiple
modes; the `failure_modes` field on each scenario lists every mode it
primarily probes.

After the round-2 trim the golden set is intentionally thin (2 scenarios:
one M1, one M4, zero M5). Filling these out is the next priority — new
cases come from production traces, not imagination.

---

## Open questions still to resolve

1. **Priority weighting** — are all 3 modes equal, or is one the primary
   thing to catch? (Influences scenario distribution and judge pass criterion.)
2. **First M5 golden case.** M5 has zero scenarios. Pick a state where
   `expected_tactical_mode(state)` returns "offensive" or "defensive" cleanly,
   and the expected answer's posture matches. Avoid `neutral` baselines.
3. **Replacements for old M2 / M3.** If production traces show recurring
   skill-level mismatches or generic reasoning, design narrow binary judges
   for those rather than reinstating the old Likerts.

---

## Definition of done for this file

- [x] Each mode has a description, example, why-it-matters, and detection mechanism
- [x] Brian has reviewed and made round-2 revisions (drop M2, drop M3, preserve numbering)
- [x] No mode is decorative — each one has a concrete detection layer attached
- [ ] Final priority/weighting decision (open question 1)
- [ ] At least one golden case per surviving mode (open question 2)
