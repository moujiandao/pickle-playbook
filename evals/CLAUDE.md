## Eval harness operating principles

This directory is Pickle Playbook's eval harness. It already exists and works. 
Read these rules before changing anything in here.

### What this harness is

- Failure-mode taxonomy: M1, M4, M5 in failure_modes.md (the rubric framework).
  Numbering has gaps because old M2 and M3 were retired in round 2 (2026-05-13);
  surviving modes keep their original IDs so archived eval runs stay readable.
- Golden set: golden_scenarios.jsonl, hand-curated, tagged by failure mode
- Two eval tracks:
  - Deterministic checks for M1, M5 (cheap, exact, gate-able)
  - LLM-as-judge for M4 (subjective, needs calibration)
- Harness: run_eval.py wires golden set → app → checks + judges → report
- Visualization: streamlit_app.py for inspection

### Before changing anything in evals/

Ask in this order. Stop at the first yes.

1. **Is there a failure I've seen in production traces that this harness misses?**
   If yes: the fix is a new golden case, possibly a new check or judge dimension. 
   Not a rewrite. Add the case, watch it fail, then decide what mechanism catches it.

2. **Is the harness producing wrong verdicts (false pass / false fail)?**
   If yes: this is a calibration problem, not a structural one. Measure it 
   (TPR/TNR or kappa against my labels) before changing the judge or rubric. 
   Don't tune by vibes.

3. **Has the rubric drifted from what production actually does wrong?**
   If yes: re-open-code 30+ recent traces. Update failure_modes.md. The golden 
   set and judges follow from the taxonomy, not the other way around.

4. **Do I just not understand what's in here anymore?**
   If yes: the fix is reading + a comprehension pass, not deletion. Walk the 
   code with me. Update inline docs. Don't rewrite for clarity — refactor 
   conservatively.

5. **Is the structure actually wrong (not just unfamiliar)?**
   Only this justifies deletion. And even then: commit first, branch, 
   rewrite on the branch, compare results on the same golden set before 
   merging. "Cleaner" is not a result.

### Anti-patterns to flag, hard

If I propose any of these, stop me and quote the rule:

- **Framework-mood**: "let's restart / rewrite from scratch / nuke and rebuild" 
  without a named failure mode the current harness can't catch. → Refuse. 
  Make me name the failure first.
- **Elaborate harness, thin golden set**: adding judge dimensions, scoring 
  layers, or CI tiers when the golden set is still <30 examples. → Add cases first.
- **Tuning judges without measurement**: changing rubric prompts because 
  "the verdict felt off." → Demand labeled examples first, then kappa/TPR/TNR.
- **Deleting working scaffolding because it feels cleaner**: see framework-mood. 
  Same rule.
- **Adding a new failure mode without trace evidence**: M6 doesn't exist 
  until I show you ≥3 production traces exhibiting it.
- **Skipping the commit step**: any session that touches evals/ starts with 
  `git status` and committing or stashing pending work before changes.

### The standing questions for any change

Before writing code in this directory, answer:

1. What failure mode is this change about? (M1, M4, M5 — or named new one)
2. Where's the trace evidence? (production trace IDs or "I made it up")
3. What's the smallest thing that would close the gap? (new golden case? 
   new check? rubric tweak? full new judge?)
4. How will I know it worked? (concrete metric: TPR went from X to Y, 
   N new golden cases pass, etc.)

If I can't answer all four, I'm not ready to change the code. Push back.

### When evolving the harness

- Concrete before abstract: don't generalize until ≥2 cases share structure
- Deterministic before judge: if a failure can be caught by a deterministic 
  check, prefer that. Judges are for what regex can't reach.
- Narrow binary judges: each judge answers one yes/no question. If I propose 
  a 5-point Likert or a multi-criterion judge, ask why it can't be split.
- Calibrate before deploying: new judge → label 30 examples myself → measure 
  kappa vs my labels → ship only when ≥0.6.
- Golden set grows from production, not imagination: new cases come from 
  real traces, then get distilled. Synthetic cases are a smell unless 
  filling a known coverage gap.

### CI/regression rules

- A judge change that drops kappa is a regression. Block it.
- A code change that makes a previously-passing golden case fail is a 
  regression. Investigate before "fixing" the case.
- New golden cases shouldn't be added in the same commit as the change 
  they test — add them first on main, watch them fail, then ship the fix.

### Working session protocol

When I start an eval session, the opening sequence is:

1. `git status` — surface uncommitted state
2. State the failure mode or question driving today's work
3. Look at the relevant evidence (traces, prior eval runs, current verdicts)
4. Then propose the smallest change

If I skip steps 1–3, remind me.

### What "bulletproof" actually means here

Not: every possible failure mode is covered. That's a fantasy.
Yes: every failure mode I've seen in production has a golden case, the 
golden case is gated in CI, and I have measured judge agreement on the 
subjective ones. Coverage of *known* failures, calibrated. The rest is 
discovered by online metrics + sampling, not by imagination.