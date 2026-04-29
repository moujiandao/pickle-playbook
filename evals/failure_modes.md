# Eval Failure Modes — Pickle Playbook

> This file is the contamination guard. We write down what the eval must catch
> *before* writing scenarios or the judge prompt. Every scenario in
> `golden_scenarios.jsonl` and every dimension in `llm_judge.py` should trace
> back to one of the modes below. If a future change can't cite a mode here,
> the eval is drifting.

**Status:** DRAFT — seeds proposed by Claude, awaiting Brian's review.
Edit freely. Replace, delete, or add modes. When this file is committed,
Phase 1 unblocks and we proceed to the rebuild.

**Last updated:** 2026-04-28

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

**Detection mechanism:** Deterministic — `shot_match` via `shot_taxonomy.py`. Predicted shot text is mapped to a family; family must equal `expected_primary` family or be in `acceptable_alternatives`.

---

## M2 — Skill-level overreach

**Description:** Model recommends a shot that's strategically sound but beyond what a player at the stated skill level can reliably execute.

**Concrete example:** State says `skill_level: 3.5`. Ball is wide on the right side; the strategically optimal shot is an Erne (jumping around the kitchen to volley). A 3.5 player cannot reliably execute an Erne — they'll either miss the line or fault into the kitchen. The right answer for *this player* is a defensive reset, even though the Erne is what a 5.0 would do.

**Why it matters:** A coaching system that ignores skill level is giving advice for the wrong player. Real coaching meets you where you are.

**Detection mechanism:** Binary judge dimension — `skill_level_feasible`. Already exists in `llm_judge.py` v1; keep it but tighten the anchors per skill band.

---

## M3 — Generic advice (would fit any state)

**Description:** Model's reasoning is vague enough that swapping the state for a different scenario wouldn't change the recommendation. The "Why" doesn't reference ball height, ball position, opponent position, or any state-specific fact.

**Concrete example:** State has ball low at the kitchen, opponents both at the kitchen line. Model says: "Keep the ball low and play patient pickleball. Stay aggressive but controlled." That sentence works for ~80% of all kitchen scenarios — it tells you nothing about *this* one.

**Why it matters:** This is the failure that's most expensive to ship. The system *sounds* like coaching but isn't actually using the state. Users get the warm fuzzy of getting an answer without any actual signal.

**Detection mechanism:** LLM judge Likert dimension — `specificity` (1–5 with anchors). Also partially caught deterministically by `reasoning_must_mention` if we put state-specific keywords there per scenario.

---

## M4 — Misreads ball state

**Description:** Model treats a defensive ball as attackable, or treats an attackable ball as defensive. Specifically: ball height (low / mid / high) and ball speed (slow / fast) are read incorrectly.

**Concrete example:** State has `ball_height: high` at the kitchen line. The right answer is a put-away volley — high ball at the kitchen is a textbook attack opportunity. Model recommends a "soft dink reset" because it's pattern-matching on "kitchen = dink" without checking the height. Defensive shot on an offensive ball.

**Why it matters:** This is the failure mode that exposes the model not actually parsing the state, just pattern-matching on superficial cues like court zone.

**Detection mechanism:** LLM judge Likert dimension — `state_reading` (1–5). Replaces v1's `strategic_soundness` which was too vague. This dimension specifically asks: did the recommendation match the offensive/defensive posture implied by ball height + speed?

---

## M5 — Position-blind

**Description:** Model's recommendation and reasoning don't account for where the partner and opponents actually are. Same advice would be given regardless of formation.

**Concrete example:** Opponents are stacked on the left side of the court (both at left_kitchen and left_transition); the right side is open. The right answer is to hit into the open right side. Model says "Cross-court dink to the backhand" without noting that one of the opponents is positioned to easily intercept the cross-court angle. The advice would be identical if both opponents were centered — meaning their actual positions weren't used.

**Why it matters:** Pickleball is 80% positioning. A model that ignores positioning is basically a dink/drive/drop classifier with extra steps.

**Detection mechanism:** LLM judge Likert dimension — `position_awareness` (1–5). Also reinforced via scenarios where positioning is the *only* thing that distinguishes the right answer from a plausible-looking wrong one (adversarial difficulty).

---

## Coverage matrix (to fill out during Phase 3)

| Failure mode | # scenarios | Difficulty mix |
|---|---|---|
| M1 wrong shot family | TBD | TBD |
| M2 skill-level overreach | TBD | TBD |
| M3 generic advice | TBD | TBD |
| M4 misreads ball state | TBD | TBD |
| M5 position-blind | TBD | TBD |

Target: 4–5 scenarios per mode, ~20 total. Each scenario is tagged in its
`source` field with the failure mode(s) it primarily probes.

---

## Open questions for Brian to resolve

1. **Are these the right 5 modes, or is one of them not actually a concern?**
   (e.g. maybe M2 skill-level isn't important if your audience is uniformly 4.0+)
2. **Is there a 6th mode missing?** Common candidates: misuse of spin info,
   ignoring the 3-shot rally structure, recommending a shot for the partner
   instead of "you," failing on edge cases (ball just inside the kitchen line, etc.)
3. **Priority weighting** — are all 5 modes equal, or is one of them the
   primary thing you want to catch? (This shapes scenario distribution.)

---

## Definition of done for this file

- [ ] Each mode has a description, example, why-it-matters, and detection mechanism
- [ ] Brian has reviewed and either approved or rewritten each mode
- [ ] No mode is decorative — each one has a concrete detection layer attached
- [ ] File committed to git before Phase 1 (checkpoint commit) runs
