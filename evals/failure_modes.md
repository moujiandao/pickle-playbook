# Eval Failure Modes — Pickle Playbook

> This file is the contamination guard. We write down what the eval must catch
> *before* writing scenarios or the judge prompt. Every scenario in
> `golden_scenarios.jsonl` and every dimension in `llm_judge.py` should trace
> back to one of the modes below. If a future change can't cite a mode here,
> the eval is drifting.

**Status:** Round 1 reviewed by Brian on 2026-04-28.
Changes from Claude's draft:
- Old M3 (generic advice) and old M5 (position-blind) **merged** into M3
  (state-blind reasoning) — they were the same root cause: not using the state.
- M2 detection mechanism **sharpened** — instead of a fuzzy judge call,
  check whether the recommended shot is on an explicit "advanced shot" list
  (4.0+ required). Sub-4.0 + advanced shot = automatic M2 fail.
- Added M5 (wrong tactical mode — offense vs defense).

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

## M2 — Skill-level overreach (recommends an advanced shot to a sub-4.0 player)

**Description:** Model recommends a shot that's on the "advanced shot" list (requires 4.0+ skill to execute reliably) when the player's stated skill level is below 4.0.

**Concrete example:** State says `skill_level: 3.5`. Ball is wide on the right side at the kitchen line. Model recommends an Erne or a topspin roll — both are 4.0+ shots. Right answer for a 3.5 is a sustainable cross-court dink.

**Why it matters:** A coaching system that ignores skill level is giving advice for the wrong player. A 3.5 trying to hit Ernes will fault into the kitchen ten times out of ten.

**Detection mechanism:** Deterministic — a binary check. Maintain an explicit `ADVANCED_SHOTS` set in `shot_taxonomy.py` (or equivalent) listing shots that require 4.0+:
- All `specialty` family (around-the-post, Erne, inside-out)
- Topspin variants in `roll` family
- `cut_angle_volley`, `roll_volley`, `drop_volley` (offensive volleys with finesse)
- Any shot string containing "topspin", "spin", "Erne", "ATP", "around the post"

If `scenario.skill_level < 4.0` AND `predicted_shot ∈ ADVANCED_SHOTS` → M2 fail. If `scenario.skill_level >= 4.0` → M2 always passes (any shot is feasible at that level for purposes of this check).

This replaces v1's fuzzy `skill_level_feasible` Likert with a crisp deterministic gate. The judge can still flag *strategic* skill mismatches (e.g. a 5.0 move suggested to a 3.5 in spirit), but the binary advanced-shot check is the floor.

---

## M3 — State-blind reasoning (generic advice OR ignores positions)

> **Merged from old M3 (generic advice) + old M5 (position-blind).** Both were
> the same root cause: the model didn't use the state. The merged mode covers
> any failure where the recommendation/reasoning would be identical if the
> state were swapped for a different one.

**Description:** Model's reasoning is vague enough that swapping the game state for a different scenario wouldn't change the recommendation. The "Why" doesn't reference ball height, ball position, ball speed, partner position, or opponent positions — it could fit any pickleball scene.

**Concrete examples:**
- *Generic flavor:* Ball low at the kitchen against opponents both at the kitchen line. Model says "Keep the ball low and play patient pickleball." That sentence works for ~80% of all kitchen scenarios.
- *Position-blind flavor:* Opponents are stacked on the left side of the court (both at left_kitchen and left_transition); the right side is open. Model recommends a cross-court dink without noting that the cross-court is well-covered. Same advice would be given if both opponents were centered.

**Why it matters:** This is the failure that's most expensive to ship. The system *sounds* like coaching but isn't actually using the inputs. Users get the warm fuzzy of getting an answer without any actual signal.

**Detection mechanism:**
- LLM judge Likert dimension — `specificity` / `state_use` (1–5 with anchors). The judge is asked: does the reasoning reference at least 2 specific state cues (ball height/speed/position/player positions)?
- Reinforced deterministically by `reasoning_must_mention` keywords on each scenario (state-specific words like "open right side", "partner at kitchen", "high ball").

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

**Detection mechanism:**
- Each scenario has a `tactical_mode` tag: `offensive` / `defensive` / `neutral` (rally maintenance / setup shots).
- Each shot family or specific shot has a default posture in `shot_taxonomy.py` (e.g. `attack_volley` → offensive, `reset` → defensive, `dink` → neutral, `drop` → context-dependent so the judge handles).
- Deterministic check: if scenario.tactical_mode ≠ predicted_shot.posture → M5 fail.
- The judge handles ambiguous cases (e.g. third-shot drop is neutral / setup, but in a panic situation it's defensive).

---

## Coverage matrix (to fill out during Phase 3)

| Failure mode | # scenarios | Difficulty mix |
|---|---|---|
| M1 wrong shot family | TBD | TBD |
| M2 skill-level overreach (advanced shot for sub-4.0) | TBD | TBD |
| M3 state-blind reasoning | TBD | TBD |
| M4 misreads ball state | TBD | TBD |
| M5 wrong tactical mode | TBD | TBD |

Target: 4–5 scenarios per mode, ~20 total. Scenarios may probe multiple
modes; the `failure_modes` field on each scenario lists every mode it
primarily probes.

---

## Open questions still to resolve

1. **Priority weighting** — are all 5 modes equal, or is one the primary
   thing to catch? (Influences scenario distribution and judge pass criterion.)
2. **`tactical_mode` tagging** — for the M5 deterministic check we need a
   posture tag on each scenario. Three values: `offensive` / `defensive` /
   `neutral`. We'll add this as a new field during scenario writing.
3. **Where does the `ADVANCED_SHOTS` list live?** Probably `shot_taxonomy.py`
   alongside the families. To be confirmed during Phase 4.

---

## Definition of done for this file

- [x] Each mode has a description, example, why-it-matters, and detection mechanism
- [x] Brian has reviewed and made round-1 revisions (M3+M5 merge, M2 sharpening, M5 added)
- [x] No mode is decorative — each one has a concrete detection layer attached
- [ ] Final priority/weighting decision (open question 1)
