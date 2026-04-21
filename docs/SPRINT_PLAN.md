# Pickle Playbook — Intelligence Upgrade Sprint Plan

> **Goal:** Transform Pickle Playbook from "LLM-with-a-court-visual" into a hybrid retrieval + empirical policy system with eval-driven improvement loops.
>
> **North star (one-liner):** For the parameters selected, the app tells the user their highest percentage shot and the likely sequence of events that will follow — with calibrated confidence backed by pro-match data and coach wisdom.

---

## Architecture at a glance

```
┌─────────────────────────────────────────────────────────────────┐
│  INGESTION PIPELINE (offline, batch)                            │
│  YouTube URL → yt-dlp → Whisper → pose/ball tracker             │
│           → LLM fuses (transcript + state) → scenario_card      │
│           → embed + insert into pgvector                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RECOMMENDATION ENGINE (online, per request)                    │
│  state → retrieve scenario_cards (hybrid: vector + FTS)         │
│        → LLM proposes shots w/ reasoning grounded in retrieval  │
│        → empirical scorer assigns %  (from logged outcomes)     │
│        → tree search expands 3 levels                           │
│        → return ranked recommendations                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FEEDBACK LOOP                                                  │
│  user verdict (good/off/edit) → logged with full state          │
│  edits → added back to retrieval index as high-weight examples  │
│  nightly: recompute empirical shot-success table                │
│  weekly: run golden eval set → check regression                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sprint overview

| Sprint | Focus | Duration | Shippable output |
|--------|-------|----------|------------------|
| **Sprint 0** | Eval foundation | 1 week | Golden eval set + regression harness |
| **Sprint 1** | Feedback logging | 1 week | Every recommendation logged with outcomes |
| **Sprint 2** | Video ingestion → scenario cards | 1-2 weeks | Structured retrieval index built from 20+ coaching videos |
| **Sprint 3** | Hybrid recommendation engine | 1-2 weeks | LLM + empirical scorer, calibrated percentages |
| **Sprint 4** | Tree search for rally prediction | 1 week | Proper MCTS-lite expansion of 3-shot trees |
| **Sprint 5** | Calibration & continuous learning | 1 week | Nightly jobs, calibration dashboard, DPO-ready data |

---

# Sprint 0 — Eval foundation

**Why first:** You can't improve what you don't measure. Every sprint after this will need the harness built here. This is also the sprint that will make your portfolio story — "I built calibrated evals before I built the fancy stuff" is exactly what FDE interviewers want to hear.

## Learning framing (since this is your first eval work)

An eval is just a **test that runs your LLM system against known scenarios and scores the output**. Three things make it different from unit tests:

1. **Output isn't deterministic** — same input can give different answers, so you score against rubrics, not exact strings
2. **Ground truth is opinion** — "best shot" isn't objectively true like `2+2=4`, so you need multiple expert answers or clear rubrics
3. **You run them on every change** — prompt edits, model swaps, retrieval tweaks all need regression checks

## Tasks

### 0.1 Build the golden scenario set (50 scenarios)

Create `evals/golden_scenarios.jsonl`. Each line is one scenario:

```json
{
  "id": "gold_001",
  "state": {
    "skill_level": 4.0,
    "me_position": "left_kitchen",
    "partner_position": "right_kitchen",
    "opp_left_position": "left_baseline",
    "opp_right_position": "right_baseline",
    "ball_position": {"x": 10.0, "y": 33.0},
    "ball_height": "mid",
    "ball_speed": "slow",
    "zone": "baseline"
  },
  "expert_answer": {
    "primary_shot": "third_shot_drop",
    "acceptable_alternatives": ["third_shot_drive"],
    "reasoning_must_mention": ["kitchen", "advance", "time"],
    "expected_sequence": [
      "drop lands in kitchen",
      "opponent dinks back",
      "you advance to kitchen"
    ]
  },
  "source": "Ben Johns YouTube 'Third Shot Fundamentals' 4:12",
  "difficulty": "obvious"
}
```

**How to generate these without burning out:**

- Start with 10 "obvious" scenarios you already know the answer to (third-shot situations, clear put-aways, classic defensive positions)
- Grab 20 from watching 2-3 coaching videos and pausing at teaching moments — you get scenarios + expert answers + sources in one pass
- Generate 20 adversarial/edge cases with Claude: ask it to give you 20 scenarios where the "obvious" shot is wrong
- Tag each with difficulty: `obvious | typical | tricky | adversarial`

**Target distribution:** 20% obvious, 50% typical, 20% tricky, 10% adversarial. The tricky+adversarial scenarios are where you'll see the biggest wins from upgrades.

### 0.2 Build the eval runner

Create `evals/run_eval.py`:

```python
# Pseudocode structure
import json
from pathlib import Path
from your_app import get_recommendation  # your current function

def load_scenarios(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]

def score_scenario(scenario, prediction):
    """Return dict with pass/fail per rubric + overall score."""
    expected = scenario["expert_answer"]
    pred_shot = prediction["primary_shot"]

    shot_match = (
        pred_shot == expected["primary_shot"]
        or pred_shot in expected.get("acceptable_alternatives", [])
    )

    reasoning = prediction.get("reasoning", "").lower()
    mentions = {
        term: term.lower() in reasoning
        for term in expected["reasoning_must_mention"]
    }

    return {
        "scenario_id": scenario["id"],
        "difficulty": scenario["difficulty"],
        "shot_match": shot_match,
        "reasoning_coverage": sum(mentions.values()) / len(mentions),
        "mentions": mentions,
    }

def run(scenarios_path, output_path):
    scenarios = load_scenarios(scenarios_path)
    results = []
    for s in scenarios:
        pred = get_recommendation(s["state"])
        results.append(score_scenario(s, pred))

    # Aggregate
    overall_pass_rate = sum(r["shot_match"] for r in results) / len(results)
    by_difficulty = {}
    for r in results:
        by_difficulty.setdefault(r["difficulty"], []).append(r["shot_match"])

    summary = {
        "overall_pass_rate": overall_pass_rate,
        "by_difficulty": {
            k: sum(v) / len(v) for k, v in by_difficulty.items()
        },
        "avg_reasoning_coverage": sum(
            r["reasoning_coverage"] for r in results
        ) / len(results),
    }
    Path(output_path).write_text(json.dumps(
        {"summary": summary, "results": results}, indent=2
    ))
    print(json.dumps(summary, indent=2))
```

**Run it:** `python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/baseline.json`

This is your **baseline**. Every sprint from now on, you re-run this and compare.

### 0.3 Add the LLM-as-judge for reasoning quality

Pure string matching on "mentions kitchen" isn't enough. Add a second scorer that uses Claude to evaluate the reasoning holistically:

```python
def llm_judge(scenario, prediction):
    prompt = f"""You are evaluating a pickleball shot recommendation.

Scenario: {json.dumps(scenario['state'])}
Expert says the best shot is: {scenario['expert_answer']['primary_shot']}
Expert reasoning should mention: {scenario['expert_answer']['reasoning_must_mention']}

The model recommended: {prediction['primary_shot']}
The model's reasoning: {prediction['reasoning']}

Score on a 1-5 scale:
- strategic_soundness: Is the shot choice strategically defensible?
- reasoning_quality: Does the reasoning demonstrate real pickleball understanding?
- specificity: Is it specific to this scenario, or generic advice?

Return JSON only: {{"strategic_soundness": N, "reasoning_quality": N, "specificity": N, "notes": "..."}}"""

    # Call Claude API, parse JSON
    return judge_result
```

**Cost note:** judging 50 scenarios per run costs ~$0.50 with Claude Sonnet. Budget accordingly — you'll run this weekly at most in Sprint 0-1, daily once automated.

### 0.4 Set up regression gate in CI

Add a GitHub Action (or Render pre-deploy hook) that runs evals and **fails the build if pass rate drops by more than 5% from main**:

```yaml
# .github/workflows/eval.yml
name: Eval Regression Check
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evals
        run: python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/pr.json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Compare to baseline
        run: python evals/check_regression.py evals/results/baseline.json evals/results/pr.json --max-drop 0.05
```

### 0.5 Sprint 0 definition of done

- [ ] 50 golden scenarios in `evals/golden_scenarios.jsonl`, distribution-balanced
- [ ] `run_eval.py` runs end-to-end and produces a JSON summary
- [ ] LLM-as-judge integrated
- [ ] Baseline score recorded in `evals/results/baseline.json` and committed
- [ ] CI gate fails if pass rate drops >5%
- [ ] README section explaining how to run evals locally

**First-time eval gotchas to watch for:**
- You'll find your current system scores way lower than expected. **This is normal and good.** It means the eval is catching real issues.
- Don't tune the prompt to game the eval. If you find a scenario the system fails, fix the system, not the rubric.
- Keep scenarios immutable once written. Version them (`golden_v1.jsonl`, `golden_v2.jsonl`) if you need to evolve them.

---

# Sprint 1 — Feedback logging

**Why second:** The eval harness measures quality against fixed scenarios. The feedback log measures quality in the wild. Together they're your two quality signals. Also: every day you don't have this logging, real user feedback is being thrown away.

## Tasks

### 1.1 Schema design

Add a `recommendations` table in Supabase:

```sql
CREATE TABLE recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT now(),
  user_id UUID REFERENCES auth.users(id),

  -- Input state (everything the UI captured)
  state JSONB NOT NULL,

  -- What the model returned
  primary_shot TEXT NOT NULL,
  reasoning TEXT,
  rally_tree JSONB,
  retrieved_card_ids UUID[],  -- which scenario cards were retrieved
  model_version TEXT,          -- e.g. "claude-sonnet-4.6_prompt_v3"
  confidence_pct INT,          -- percentage the model assigned

  -- User feedback
  verdict TEXT CHECK (verdict IN ('good', 'off', 'edited', NULL)),
  verdict_at TIMESTAMPTZ,
  edited_shot TEXT,
  edited_reasoning TEXT,
  edited_rally_tree JSONB,

  -- For calibration
  actual_outcome TEXT  -- if user reports what actually happened
);

CREATE INDEX idx_rec_user_created ON recommendations(user_id, created_at DESC);
CREATE INDEX idx_rec_verdict ON recommendations(verdict) WHERE verdict IS NOT NULL;
CREATE INDEX idx_rec_shot ON recommendations(primary_shot);
```

### 1.2 Wire up logging in the recommendation flow

Every call to `/api/recommend` should insert a row **before returning**. Every click on Good/Off/Edit should update that row by ID.

Critical: your current UI already has Good/Off/Edit buttons but (I'm guessing) they don't persist anywhere. Make them persist.

### 1.3 Edit capture UI

When a user clicks Edit, open a modal that lets them change:
- Primary shot (dropdown of shot types)
- Reasoning (freetext)
- Sequence (the 3 rally steps)

On save, update the recommendation row with the edit. This edited version is **gold data** — it's a human correction tied to a specific state, which is exactly what you need for Sprint 5 learning.

### 1.4 Admin view for reviewing feedback

Build a simple `/admin/feedback` page that shows:
- Recent recommendations with their verdicts
- Filter by verdict=off or verdict=edited
- Side-by-side: original vs. edit

This becomes your daily/weekly review loop. Scanning 20 edits a week tells you more about system quality than any automated metric.

### 1.5 Sprint 1 definition of done

- [ ] `recommendations` table created in Supabase
- [ ] Every recommendation request logged with full state + output
- [ ] Good/Off/Edit buttons persist verdict to DB
- [ ] Edit modal captures structured edits
- [ ] Admin feedback view shows recent verdicts with filter

---

# Sprint 2 — Video ingestion → scenario cards

**Why now:** You have eval + logging infrastructure. Now you can safely improve the retrieval layer and *know* if it helped (eval pass rate goes up, or it doesn't).

## Key insight
Raw transcripts are near-useless for retrieval. What you want in your index are **state-tagged principles** — structured cards that pair "what the court looked like" with "what the coach said to do." This is the differentiated move vs. every other "we RAG'd some docs" app.

## Tasks

### 2.1 Set up the ingestion repo structure

```
pickle-playbook/
  ingestion/
    download.py          # yt-dlp wrapper
    transcribe.py        # Whisper
    extract_state.py     # MediaPipe / ball tracking
    fuse.py              # LLM turns (transcript + state) → scenario_cards
    embed_and_store.py   # pgvector insert
    run_pipeline.py      # orchestrator for one video
    sources.jsonl        # list of videos to ingest
```

### 2.2 Download + transcribe

```python
# ingestion/download.py
import subprocess, json
from pathlib import Path

def download(youtube_url, out_dir="ingestion/raw"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "yt-dlp",
        "-f", "bestvideo[height<=720]+bestaudio/best",
        "-o", f"{out}/%(id)s.%(ext)s",
        "--write-info-json",
        youtube_url
    ], check=True)

# ingestion/transcribe.py
import whisper
model = whisper.load_model("base")  # or "small" for better accuracy

def transcribe(video_path):
    result = model.transcribe(str(video_path), word_timestamps=True)
    # Returns: {"segments": [{"start": float, "end": float, "text": str}, ...]}
    return result
```

**Install:** `pip install yt-dlp openai-whisper`. Whisper needs ffmpeg (`brew install ffmpeg`).

### 2.3 Extract court state from video

This is the hard part. You already know MediaPipe from swing-coach-mvp — reuse that muscle. For now, keep it simple:

- Sample 1 frame per second
- Run pose estimation to find 4 players
- Run a ball detector (you can start with a simple color-based tracker for the neon green ball, upgrade to a trained model later)
- Project 2D positions to court coordinates using known court landmarks

Output: `{timestamp: 12.5, players: [{x, y}, {x, y}, ...], ball: {x, y, height_estimate}}`

**Reality check:** for Sprint 2 v1, it's OK if this works 60% of the time. Flag low-confidence frames and skip them in the fuse step.

### 2.4 Fuse transcript + state → scenario cards

This is where the magic happens. For each transcript segment, find the court state at that timestamp, then ask Claude to extract a scenario card:

```python
FUSE_PROMPT = """You are a pickleball coach translating video moments into structured strategy cards.

TRANSCRIPT SEGMENT ({start}-{end}s):
"{text}"

COURT STATE AT {mid_time}s:
{state_json}

Extract ONE scenario card if this moment teaches a specific strategic principle.
Return null if the segment is filler, introduction, or not strategy-focused.

Return JSON matching this schema:
{{
  "state_pattern": {{
    "my_side": "kitchen|transition|baseline",
    "their_side": "kitchen|transition|baseline",
    "ball_zone": "kitchen|mid|baseline",
    "ball_height": "low|mid|high",
    "skill_context": "3.0|3.5|4.0|4.5|5.0|any"
  }},
  "principle": "one sentence, imperative mood",
  "reasoning": "why this works, 2-3 sentences",
  "shot_type": "drop|drive|dink|lob|volley|reset|roll|speedup",
  "confidence": "high|medium|low",
  "source_quote": "short verbatim quote from transcript"
}}

Return ONLY the JSON object or the literal word `null`."""
```

**Cost math:** 1 hour of coaching video ≈ 200 transcript segments ≈ 200 LLM calls ≈ $1-2 with Sonnet. Ingesting 20 hours of video costs ~$30. Budget accordingly.

### 2.5 Embed and store

```python
# ingestion/embed_and_store.py
from openai import OpenAI
import psycopg2

def embed(text):
    client = OpenAI()
    return client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    ).data[0].embedding

def store_card(card, video_id, timestamp):
    embedding_text = f"{card['principle']} {card['reasoning']}"
    emb = embed(embedding_text)

    # Insert into pgvector table
    # You already have pgvector set up; add a new table or extend existing
```

Table:
```sql
CREATE TABLE scenario_cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  state_pattern JSONB NOT NULL,
  principle TEXT NOT NULL,
  reasoning TEXT NOT NULL,
  shot_type TEXT NOT NULL,
  confidence TEXT,
  source_video_id TEXT,
  source_timestamp FLOAT,
  source_quote TEXT,
  embedding VECTOR(1536),
  weight FLOAT DEFAULT 1.0,  -- boosted for user-verified cards later
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON scenario_cards USING ivfflat (embedding vector_cosine_ops);
```

### 2.6 Seed the index with 20 videos

Curate a `sources.jsonl` of 20 good coaching videos. Suggested mix:
- 5 from Ben Johns / Anna Leigh Waters clinics (elite strategy)
- 5 from PrimeTime Pickleball or Enhance Pickleball (channel-grade breakdowns)
- 5 pro match broadcasts with commentary (real shot outcomes)
- 5 from coaches targeting 3.5-4.0 skill level (your user base)

Run the pipeline. Expect ~500-1500 scenario cards.

### 2.7 Hybrid retrieval

Query-time retrieval should do **both** semantic search AND structured filtering:

```python
def retrieve(state, k=5):
    query_text = format_state_as_query(state)
    query_emb = embed(query_text)

    # Semantic: vector similarity
    semantic = db.query("""
        SELECT *, 1 - (embedding <=> %s) AS sim
        FROM scenario_cards
        WHERE state_pattern @> %s  -- JSONB contains filter
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (query_emb, filter_json(state), query_emb, k * 3))

    # Structured: exact state pattern match (boost these)
    # Then rerank with RRF or just merge by weighted score
    return merge_and_rank(semantic, k)
```

You already know RRF from claude-bridge — same pattern here.

### 2.8 Wire retrieval into the recommendation prompt

Update your `/api/recommend` endpoint:

```python
def get_recommendation(state):
    cards = retrieve(state, k=5)
    cards_text = "\n\n".join(
        f"PRINCIPLE: {c['principle']}\nWHY: {c['reasoning']}\nSHOT: {c['shot_type']}"
        for c in cards
    )

    prompt = f"""Given this pickleball scenario: {json.dumps(state)}

Relevant strategic principles from pro coaches:
{cards_text}

Recommend the highest-percentage shot. Return JSON: {{...}}"""
    # Call Claude, parse, return
```

### 2.9 Run eval, compare to baseline

This is the payoff. Run `python evals/run_eval.py` again. Your pass rate should go up — if it didn't, the retrieval isn't helping and you need to debug (usually: bad state-pattern filtering, or chunks too generic).

### 2.10 Sprint 2 definition of done

- [ ] Ingestion pipeline runs end-to-end on a single video
- [ ] 20 videos ingested, ~500+ scenario cards in Supabase
- [ ] Hybrid retrieval (vector + JSONB filter) working
- [ ] Recommendation endpoint uses retrieved cards in prompt
- [ ] Eval pass rate improved over Sprint 0 baseline (target: +15pp)
- [ ] Ingestion is idempotent (re-running doesn't duplicate)

---

# Sprint 3 — Hybrid recommendation engine (LLM + empirical scorer)

**Why now:** LLMs hallucinate percentages. To say "this is a 72% shot" with a straight face, you need data.

## Tasks

### 3.1 Build the empirical shot-success table

From your `recommendations` table (Sprint 1) plus ingested pro-match outcomes, aggregate:

```sql
CREATE MATERIALIZED VIEW shot_success_stats AS
SELECT
  state->>'zone' AS zone,
  state->>'ball_height' AS ball_height,
  state->>'ball_speed' AS ball_speed,
  (state->>'skill_level')::float AS skill_level,
  primary_shot,
  COUNT(*) AS n_attempts,
  SUM(CASE WHEN verdict = 'good' THEN 1 ELSE 0 END)::float / COUNT(*) AS success_rate
FROM recommendations
WHERE verdict IS NOT NULL
GROUP BY 1,2,3,4,5
HAVING COUNT(*) >= 5;
```

Refresh nightly. In early days this table is sparse — that's fine, fall back to LLM-only confidence when n < 5.

### 3.2 Augment with pro-match data

In Sprint 2 you ingested pro broadcasts. Extract **shot outcomes** from these (did the rally continue? was it a winner? error?) and add synthetic rows to `shot_success_stats` with `source='pro_match'`. This gives you prior data before your user base generates enough.

### 3.3 Rewrite the confidence calculation

```python
def score_shot(shot, state):
    key = discretize_state(state) + (shot,)
    empirical = lookup_shot_success(key)  # returns (rate, n) or None

    if empirical and empirical["n"] >= 20:
        # Strong empirical prior
        return {"confidence": empirical["rate"], "source": "empirical", "n": empirical["n"]}
    elif empirical and empirical["n"] >= 5:
        # Weak prior, blend with LLM estimate
        llm_est = llm_estimate_confidence(shot, state)
        blend = 0.5 * empirical["rate"] + 0.5 * llm_est
        return {"confidence": blend, "source": "blended", "n": empirical["n"]}
    else:
        # Fall back to LLM
        return {"confidence": llm_estimate_confidence(shot, state), "source": "llm"}
```

### 3.4 Show confidence source in UI

Don't just show "72%". Show **where the number came from**:
- "72% — based on 43 logged outcomes"
- "~65% — estimated by model (no match data yet)"
- "68% — blended: 12 logged + model"

This is honest and it's a differentiator. No other pickleball app does this.

### 3.5 Calibration tracking

Add to your eval harness: when you say a shot is 70%, check across all 70%-confidence recommendations whether outcomes actually matched. Plot a calibration curve (predicted % on x-axis, actual success rate on y-axis; perfect calibration is the diagonal).

```python
# evals/calibration.py
def calibration_curve(recommendations):
    buckets = {i: [] for i in range(0, 100, 10)}
    for r in recommendations:
        if r["verdict"] is None:
            continue
        bucket = (r["confidence_pct"] // 10) * 10
        buckets[bucket].append(1 if r["verdict"] == "good" else 0)

    return {
        b: {"predicted": b + 5, "actual": sum(v) / len(v) if v else None, "n": len(v)}
        for b, v in buckets.items()
    }
```

Target: predicted and actual should be within 10pp across buckets.

### 3.6 Sprint 3 definition of done

- [ ] `shot_success_stats` materialized view refreshing nightly
- [ ] Pro-match outcomes seeded into stats
- [ ] `score_shot` uses empirical → blended → LLM fallback logic
- [ ] UI displays confidence source transparently
- [ ] Calibration curve computed and tracked
- [ ] Eval pass rate up another +5pp from Sprint 2

---

# Sprint 4 — Tree search for rally prediction

**Why now:** Your 3-shot sequence is probably one monolithic LLM call right now. That drifts because the LLM commits to opponent responses without really thinking about the distribution.

## Tasks

### 4.1 Reframe as tree expansion

```python
def expand_rally(state, depth=3, branching=2):
    """
    MCTS-lite: at each level, LLM proposes top-2 most likely responses
    with probabilities, we keep top branches by joint probability.
    """
    root = {"state": state, "shot": None, "prob": 1.0, "children": []}

    def expand(node, remaining_depth):
        if remaining_depth == 0:
            return
        candidates = llm_propose_responses(node["state"], n=branching)
        # candidates: [{"shot": "...", "new_state": {...}, "prob": 0.6}, ...]
        for c in candidates:
            child = {**c, "children": []}
            node["children"].append(child)
            expand(child, remaining_depth - 1)

    expand(root, depth)
    return root
```

### 4.2 Prompt for response proposals

```python
RESPOND_PROMPT = """Current pickleball state: {state}
Last shot hit: {last_shot}

What are the 2 most likely responses by the opponent? For each:
- shot type
- resulting state (positions, ball position/height/speed)
- probability (0-1)

Ground your probabilities in these retrieved principles:
{retrieved_cards}

Return JSON array."""
```

### 4.3 Collapse tree into UI-friendly sequence

The UI currently shows a linear 3-step sequence. Extract the highest-probability path from the tree:

```python
def most_likely_path(tree):
    path = [tree]
    node = tree
    while node["children"]:
        node = max(node["children"], key=lambda c: c["prob"])
        path.append(node)
    return path
```

But also: **show branching when probabilities are close**. If the top two responses are both ~40%, don't pretend there's one answer. Show both branches.

### 4.4 Add "what if opponent does X" interactivity

Let users click a node in the tree to expand an alternative branch. This is both a UX win and a way to generate more scenario data (every user exploration is a labeled training pair).

### 4.5 Sprint 4 definition of done

- [ ] Tree search replaces monolithic 3-shot generation
- [ ] Probabilities on every branch
- [ ] UI shows primary path + alternative branches when close
- [ ] User can expand alternative branches interactively
- [ ] Eval scenarios updated to include expected-sequence checks against tree paths

---

# Sprint 5 — Calibration & continuous learning

**Why last:** This is the "gets better over time" promise. But it only works if Sprints 0-4 are solid, because learning amplifies whatever's in the system — good or bad.

## Tasks

### 5.1 Turn edits into retrievable cards

Every user `edit` in the `recommendations` table → a new scenario_card with `weight=2.0` (boosted above ingested cards):

```python
def promote_edit_to_card(rec):
    card = {
        "state_pattern": extract_pattern(rec["state"]),
        "principle": rec["edited_reasoning"].split(".")[0],
        "reasoning": rec["edited_reasoning"],
        "shot_type": rec["edited_shot"],
        "source_video_id": None,
        "source_quote": f"User correction on {rec['created_at']}",
        "weight": 2.0,
    }
    embedding = embed(f"{card['principle']} {card['reasoning']}")
    insert_card(card, embedding)
```

Run this nightly. Suddenly the system is learning from its own corrections.

### 5.2 Weekly regression eval in CI

Now that you have volume, run evals weekly as a cron job. Post results to a Slack channel or email:

```
Week of 2026-04-20 eval:
  Overall: 76% (↑2pp from last week)
  Obvious: 95% | Typical: 78% | Tricky: 62% | Adversarial: 41%
  Calibration error: 8.2pp (target <10)
  New cards added from edits: 34
```

### 5.3 DPO data collection (optional stretch)

For every `(original_recommendation, edited_recommendation)` pair in your DB, you have a preference pair: "chosen = edit, rejected = original." This is literally DPO training data. You don't need to fine-tune yet, but **collect and version it** starting now. In 6 months you'll have thousands of pairs and can run a small DPO fine-tune of a Haiku-class model for fast/cheap inference.

Export script:
```python
def export_dpo_pairs(output_path):
    pairs = db.query("""
        SELECT state, primary_shot, reasoning, edited_shot, edited_reasoning
        FROM recommendations
        WHERE verdict = 'edited'
    """)
    with open(output_path, "w") as f:
        for p in pairs:
            f.write(json.dumps({
                "prompt": format_prompt(p["state"]),
                "chosen": f"{p['edited_shot']}: {p['edited_reasoning']}",
                "rejected": f"{p['primary_shot']}: {p['reasoning']}",
            }) + "\n")
```

### 5.4 Calibration dashboard

Add `/admin/calibration` showing:
- Calibration curve (predicted vs. actual)
- Eval pass rate over time
- Edit volume over time
- Top 10 scenarios where edits happen most (these are your system's weak spots)

### 5.5 Sprint 5 definition of done

- [ ] Nightly job promotes edits to weighted scenario cards
- [ ] Weekly eval regression posted to Slack/email
- [ ] DPO pair export script runs and produces valid JSONL
- [ ] Calibration dashboard live
- [ ] Documented playbook for "what to do when eval drops"

---

# After Sprint 5

You now have:
- A knowledge pipeline turning unstructured pickleball content into structured cards
- A hybrid engine grounding LLM recommendations in empirical data
- A feedback loop that turns every user edit into training signal
- Calibrated confidence scores nobody else in this space shows
- A regression harness preventing silent degradation
- DPO-ready data accumulating for eventual fine-tuning

**What I'd tackle next (v2):**
- Opponent modeling (opponent skill level + tendencies)
- Physics engine for mechanical predictions (ball trajectory, reaction time)
- User-uploaded match video → state extraction → "what should I have hit?" analysis
- Fine-tune a small model on DPO pairs once you have 5k+

---

# Execution notes for you specifically

- **Use claude-bridge** for cross-session memory on this work. Save a session memory after each sprint with the diff of decisions made.
- **Use git worktrees** for parallel work: one worktree for ingestion pipeline, one for eval harness, one for main app. You already do this.
- **Use the eval-audit skill** on your current state before Sprint 0 task 0.1 — it'll catch gaps I might have missed here.
- **Don't skip Sprint 0.** I know the impulse is "let me build the cool video pipeline first." Resist it. Everything downstream is better with evals in place.
- **Budget:** rough API spend through Sprint 2 is ~$50 (ingestion + eval runs). Sprint 3+ adds more as logging scales. Nothing crazy.
- **Portfolio angle:** write a blog post at the end of each sprint. "How I built calibrated pickleball recommendations" is a better FDE interview story than any of your other projects.
