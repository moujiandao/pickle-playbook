"""Streamlit court visualizer for golden scenarios + eval results.

Run:
    streamlit run evals/viz/streamlit_app.py

Reads:
    evals/golden_scenarios.jsonl   (required)
    evals/results/*.json           (optional, user picks via sidebar)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).resolve().parent
_EVALS_DIR = _HERE.parent
_SCENARIOS_PATH = _EVALS_DIR / "golden_scenarios.jsonl"
_RESULTS_DIR = _EVALS_DIR / "results"

# ── court layout (duplicated from run_eval.py; court geometry is physical,
# won't drift, and importing run_eval triggers its backend-heavy imports) ──

_ZONE_Y_MY = {"kitchen": 29.0, "transition": 35.0, "baseline": 40.0}
_ZONE_Y_OPP = {"kitchen": 15.0, "transition": 9.0, "baseline": 4.0}
_SIDE_X = {"left": 5.0, "right": 15.0}
_COURT_W = 20.0
_COURT_L = 44.0
_NET_Y = 22.0
_KITCHEN_NEAR_Y = 29.0
_KITCHEN_FAR_Y = 15.0

_QUADRANT_COLORS = {
    "right_shot_good_reasoning": "#22c55e",  # green
    "right_shot_bad_reasoning":  "#eab308",  # yellow
    "wrong_shot_good_reasoning": "#ef4444",  # red (dangerous — judge rationalizing)
    "wrong_shot_bad_reasoning":  "#6b7280",  # gray
    "no_judge":                  "#94a3b8",  # slate
}

_DIFFICULTY_COLORS = {
    "obvious":     "#22c55e",
    "typical":     "#3b82f6",
    "tricky":      "#a855f7",
    "adversarial": "#ef4444",
}


def _pos_xy(pos_str: str, team: str) -> tuple[float, float]:
    """Translate 'left_kitchen' + 'my'|'opp' → (x, y) in feet.

    Returns court center (10, 22) for unrecognized zone/side strings so a
    malformed scenario row shows a visible off-placement instead of crashing.
    """
    parts = pos_str.split("_", 1)
    if len(parts) != 2:
        return _COURT_W / 2, _NET_Y
    side, zone = parts
    y_map = _ZONE_Y_MY if team == "my" else _ZONE_Y_OPP
    x = _SIDE_X.get(side)
    y = y_map.get(zone)
    if x is None or y is None:
        return _COURT_W / 2, _NET_Y
    return x, y


# ── data loading ───────────────────────────────────────────────────────────

@st.cache_data
def load_scenarios() -> list[dict]:
    out = []
    with _SCENARIOS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


@st.cache_data
def load_results(path: str) -> dict:
    """Return {'summary': {...}, 'by_id': {scenario_id: result}}."""
    data = json.loads(Path(path).read_text())
    return {
        "summary": data.get("summary", {}),
        "by_id": {r["scenario_id"]: r for r in data.get("results", [])},
    }


def list_result_files() -> list[str]:
    if not _RESULTS_DIR.exists():
        return []
    return sorted(str(p) for p in _RESULTS_DIR.glob("*.json"))


# ── triage notes (sidecar) ─────────────────────────────────────────────────
# Notes live next to the results file as `{stem}.notes.json`. Per-results-file
# scoping means a re-run starts with a clean slate (judge verdicts reset);
# scenario-level observations like "ambiguous" are easy enough to re-flag.

_TRIAGE_ACTIONS = [
    "keep",
    "retire",
    "rewrite_context",
    "relabel_shot",
    "expand_acceptable",
    "ambiguous",
]
_JUDGE_VERDICTS = ["correct", "wrong_pass", "wrong_fail", "unclear"]
_SYSTEM_SIGNALS = ["prompt_issue", "retrieval_issue", "model_capability", "none"]
_PRIORITIES = ["high", "med", "low"]
_BLANK = "—"


def _notes_path(results_path: str | None) -> Path | None:
    if not results_path:
        return None
    return Path(results_path).with_suffix(".notes.json")


def load_notes(notes_path: Path | None) -> dict:
    if notes_path is None or not notes_path.exists():
        return {}
    try:
        return json.loads(notes_path.read_text())
    except json.JSONDecodeError:
        return {}


def save_notes(notes_path: Path, notes: dict) -> None:
    notes_path.write_text(json.dumps(notes, indent=2, sort_keys=True))


def _idx(options: list[str], value: str | None) -> int:
    """Selectbox index for [_BLANK, *options] given a possibly-missing value."""
    if value in options:
        return options.index(value) + 1
    return 0


def build_triage_report(
    scenarios: list[dict], notes: dict, results: dict | None
) -> str:
    by_id = (results or {}).get("by_id", {})
    by_action: dict[str, list[tuple[dict, dict]]] = {}
    for s in scenarios:
        n = notes.get(s["id"])
        if not n:
            continue
        action = n.get("scenario_action") or "(unspecified)"
        by_action.setdefault(action, []).append((s, n))
    if not by_action:
        return "# Triage report\n\n_No scenarios annotated yet._\n"
    lines = ["# Triage report", ""]
    total = sum(len(v) for v in by_action.values())
    lines.append(f"**{total} annotated** across {len(by_action)} action group(s).\n")
    for action in sorted(by_action):
        items = by_action[action]
        lines.append(f"## {action} ({len(items)})\n")
        for s, n in items:
            r = by_id.get(s["id"], {})
            pri = n.get("priority") or "?"
            jv = n.get("judge_verdict") or "—"
            ss = n.get("system_signal") or "—"
            lines.append(
                f"- [ ] **{s['id']}** ({s.get('difficulty', '?')}, "
                f"pri={pri}, judge={jv}, system={ss})"
            )
            lines.append(
                f"  - expected: `{s['expert_answer']['primary_shot']}` · "
                f"predicted: `{r.get('predicted_shot', '—')}`"
            )
            note = (n.get("note") or "").strip()
            if note:
                for ln in note.splitlines():
                    lines.append(f"  - {ln}")
            if updated := n.get("updated_at"):
                lines.append(f"  - _updated: {updated}_")
        lines.append("")
    return "\n".join(lines)


# ── court drawing ──────────────────────────────────────────────────────────

def _court_shapes() -> list[dict]:
    """Plotly shape dicts for court lines + kitchen + net.

    All shapes use layer='below' so the scatter traces (ball + player
    markers) render on top; otherwise the filled court rectangle would hide
    every dot.
    """
    return [
        dict(type="rect", x0=0, y0=0, x1=_COURT_W, y1=_COURT_L,
             line=dict(color="white", width=3), fillcolor="#1E93D6",
             layer="below"),
        dict(type="line", x0=0, y0=_NET_Y, x1=_COURT_W, y1=_NET_Y,
             line=dict(color="white", width=5), layer="below"),
        dict(type="line", x0=0, y0=_KITCHEN_FAR_Y, x1=_COURT_W, y1=_KITCHEN_FAR_Y,
             line=dict(color="white", width=2, dash="dash"), layer="below"),
        dict(type="line", x0=0, y0=_KITCHEN_NEAR_Y, x1=_COURT_W, y1=_KITCHEN_NEAR_Y,
             line=dict(color="white", width=2, dash="dash"), layer="below"),
        dict(type="line", x0=_COURT_W / 2, y0=0, x1=_COURT_W / 2, y1=_KITCHEN_FAR_Y,
             line=dict(color="white", width=1), layer="below"),
        dict(type="line", x0=_COURT_W / 2, y0=_KITCHEN_NEAR_Y, x1=_COURT_W / 2, y1=_COURT_L,
             line=dict(color="white", width=1), layer="below"),
    ]


def _add_coordinate_hover(fig: go.Figure) -> None:
    """Invisible grid of points so hovering anywhere on the court shows x/y in feet."""
    xs, ys = [], []
    x = 0.0
    while x <= _COURT_W:
        y = 0.0
        while y <= _COURT_L:
            xs.append(round(x, 1))
            ys.append(round(y, 1))
            y += 0.5
        x += 0.5
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)"),
        hovertemplate="x: %{x:.1f} ft<br>y: %{y:.1f} ft<extra></extra>",
        showlegend=False,
        name="",
    ))


def _base_fig(height: int = 700) -> go.Figure:
    fig = go.Figure()
    _add_coordinate_hover(fig)
    fig.update_layout(
        xaxis=dict(range=[-1, _COURT_W + 1], showgrid=False, zeroline=False,
                   showticklabels=False, scaleanchor="y", scaleratio=1),
        # Reverse y manually (range=[high, low]) so opp side is at top;
        # using autorange="reversed" silently disables the explicit range.
        yaxis=dict(range=[_COURT_L + 1, -1], autorange=False,
                   showgrid=False, zeroline=False, showticklabels=False),
        shapes=_court_shapes(),
        plot_bgcolor="#f1f5f9",
        paper_bgcolor="#f1f5f9",
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(bgcolor="white", bordercolor="#cbd5e1", borderwidth=1),
    )
    return fig


def _annotate_zones(fig: go.Figure) -> None:
    """Small zone labels so the court is readable at a glance."""
    labels = [
        ("OPP baseline", 10, 2.5),
        ("OPP transition", 10, 11.5),
        ("OPP kitchen", 10, 18.5),
        ("YOUR kitchen", 10, 25.5),
        ("YOUR transition", 10, 32.5),
        ("YOUR baseline", 10, 42.5),
    ]
    for text, x, y in labels:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                           font=dict(size=9, color="rgba(255,255,255,0.55)"))


def render_overview(scenarios: list[dict], results: dict | None) -> go.Figure:
    """All filtered ball positions on one court, colored by quadrant or difficulty."""
    fig = _base_fig(height=750)
    _annotate_zones(fig)

    if not scenarios:
        return fig

    by_id = (results or {}).get("by_id", {})
    color_by_quadrant = results is not None

    groups: dict[str, list[dict]] = {}
    for s in scenarios:
        if color_by_quadrant:
            r = by_id.get(s["id"])
            key = (r.get("quadrant") if r else None) or "no_judge"
        else:
            key = s.get("difficulty", "unknown")
        groups.setdefault(key, []).append(s)

    color_map = _QUADRANT_COLORS if color_by_quadrant else _DIFFICULTY_COLORS

    for key in sorted(groups):
        items = groups[key]
        xs = [s["state"]["ball_position"]["x"] for s in items]
        ys = [s["state"]["ball_position"]["y"] for s in items]
        hover = []
        for s in items:
            r = by_id.get(s["id"], {}) if color_by_quadrant else {}
            primary = s["expert_answer"]["primary_shot"]
            lines = [
                f"<b>{s['id']}</b> — {s.get('difficulty', '?')}",
                f"Expected: {primary}",
                f"Ball: {s['state']['ball_height']} / {s['state']['ball_speed']}",
            ]
            if color_by_quadrant and r:
                lines.append(f"Predicted: {r.get('predicted_shot', '—')}")
                lines.append(f"Shot match: {r.get('shot_match')}")
            hover.append("<br>".join(lines))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            name=f"{key} ({len(items)})",
            marker=dict(size=14, color=color_map.get(key, "#888"),
                        line=dict(color="white", width=1.5)),
            hovertext=hover, hoverinfo="text",
        ))

    title = "Ball positions" + (" — colored by quadrant" if color_by_quadrant else " — colored by difficulty")
    fig.update_layout(title=title)
    return fig


def render_detail(scenario: dict) -> go.Figure:
    """Single scenario: 4 players + ball at actual positions."""
    fig = _base_fig(height=700)
    _annotate_zones(fig)
    state = scenario["state"]

    me_x, me_y = _pos_xy(state["me_position"], "my")
    p_x, p_y = _pos_xy(state["partner_position"], "my")
    ol_x, ol_y = _pos_xy(state["opp_left_position"], "opp")
    or_x, or_y = _pos_xy(state["opp_right_position"], "opp")

    fig.add_trace(go.Scatter(
        x=[me_x, p_x], y=[me_y, p_y],
        mode="markers+text",
        name="My team",
        text=["ME", "P"],
        textposition="middle center",
        textfont=dict(color="white", size=11, family="Arial Black"),
        marker=dict(size=36, color="#F5A623", line=dict(color="white", width=2)),
        hovertext=[f"ME: {state['me_position']}",
                   f"Partner: {state['partner_position']}"],
        hoverinfo="text",
    ))

    fig.add_trace(go.Scatter(
        x=[ol_x, or_x], y=[ol_y, or_y],
        mode="markers+text",
        name="Opponents",
        text=["OL", "OR"],
        textposition="middle center",
        textfont=dict(color="white", size=11, family="Arial Black"),
        marker=dict(size=36, color="#E74C3C", line=dict(color="white", width=2)),
        hovertext=[f"Opp L: {state['opp_left_position']}",
                   f"Opp R: {state['opp_right_position']}"],
        hoverinfo="text",
    ))

    bp = state["ball_position"]
    size_by_height = {"low": 12, "mid": 18, "high": 26}
    fig.add_trace(go.Scatter(
        x=[bp["x"]], y=[bp["y"]],
        mode="markers", name="Ball",
        marker=dict(size=size_by_height.get(state["ball_height"], 16),
                    color="#C8E636",
                    line=dict(color="black", width=2)),
        hovertext=(
            f"Ball: ({bp['x']}, {bp['y']})<br>"
            f"Height: {state['ball_height']}<br>"
            f"Speed: {state['ball_speed']}"
            + (f"<br>Spin: {state.get('ball_spin')}" if state.get('ball_spin') else "")
        ),
        hoverinfo="text",
    ))

    fig.update_layout(title=f"{scenario['id']} — {scenario.get('difficulty', '?')}")
    return fig


def _scenarios_to_df(
    scenarios: list[dict], results: dict | None, notes: dict
) -> pd.DataFrame:
    """One row per scenario; left columns read-only, right columns editable."""
    by_id = (results or {}).get("by_id", {})
    rows = []
    for s in scenarios:
        sid = s["id"]
        r = by_id.get(sid, {})
        n = notes.get(sid, {})
        rows.append({
            "id": sid,
            "difficulty": s.get("difficulty", "?"),
            "expected": s["expert_answer"]["primary_shot"],
            "predicted": r.get("predicted_shot") or "",
            "shot_match": bool(r.get("shot_match")) if r else False,
            "judge_verdict": n.get("judge_verdict") or "",
            "scenario_action": n.get("scenario_action") or "",
            "system_signal": n.get("system_signal") or "",
            "priority": n.get("priority") or "",
            "note": n.get("note") or "",
        })
    return pd.DataFrame(rows)


_TRIAGE_KEYS = ("judge_verdict", "scenario_action", "system_signal", "priority", "note")


def _row_entry(row: pd.Series) -> dict:
    """Convert one DataFrame row into a triage entry dict (no timestamp)."""
    return {
        "judge_verdict": row["judge_verdict"] or None,
        "scenario_action": row["scenario_action"] or None,
        "system_signal": row["system_signal"] or None,
        "priority": row["priority"] or None,
        "note": (row["note"] or "").strip(),
    }


def _entry_is_empty(entry: dict) -> bool:
    return not any(entry.get(k) for k in _TRIAGE_KEYS)


def _entries_equal(a: dict, b: dict) -> bool:
    """Compare triage payload, ignoring updated_at."""
    return {k: (a or {}).get(k) for k in _TRIAGE_KEYS} == {
        k: (b or {}).get(k) for k in _TRIAGE_KEYS
    }


def apply_bulk_edits(edited: pd.DataFrame, notes: dict) -> int:
    """Apply rows from the editor onto `notes` in-place. Returns change count.

    A row whose triage fields are all empty *clears* the existing note for
    that scenario; otherwise it overwrites with a fresh updated_at.
    """
    changed = 0
    now = datetime.now().isoformat(timespec="seconds")
    for _, row in edited.iterrows():
        sid = row["id"]
        new_entry = _row_entry(row)
        existing = notes.get(sid)
        if _entry_is_empty(new_entry):
            if existing is not None:
                del notes[sid]
                changed += 1
            continue
        if existing is not None and _entries_equal(existing, new_entry):
            continue
        new_entry["updated_at"] = now
        notes[sid] = new_entry
        changed += 1
    return changed


def render_bulk_triage(
    scenarios: list[dict],
    results: dict | None,
    notes_path: Path | None,
    notes: dict,
) -> None:
    """Spreadsheet-style table for triaging many scenarios at once."""
    if notes_path is None:
        st.info("Load an eval results file (sidebar) to enable bulk triage.")
        return
    if not scenarios:
        st.info("No scenarios match the current filters.")
        return

    st.caption(
        f"**{len(scenarios)}** scenarios · sort by clicking column headers · "
        "edit cells inline · empty all triage fields on a row to *clear* that note."
    )

    df = _scenarios_to_df(scenarios, results, notes)
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        height=min(600, 56 + 36 * len(df)),
        column_config={
            "id": st.column_config.TextColumn("id", disabled=True, width="small"),
            "difficulty": st.column_config.TextColumn(
                "difficulty", disabled=True, width="small"
            ),
            "expected": st.column_config.TextColumn(
                "expected", disabled=True, width="medium"
            ),
            "predicted": st.column_config.TextColumn(
                "predicted", disabled=True, width="medium"
            ),
            "shot_match": st.column_config.CheckboxColumn(
                "shot_match", disabled=True, width="small"
            ),
            "judge_verdict": st.column_config.SelectboxColumn(
                "judge_verdict",
                options=[""] + _JUDGE_VERDICTS,
                width="medium",
                help="correct / wrong_pass (FP) / wrong_fail (FN) / unclear",
            ),
            "scenario_action": st.column_config.SelectboxColumn(
                "scenario_action",
                options=[""] + _TRIAGE_ACTIONS,
                width="medium",
            ),
            "system_signal": st.column_config.SelectboxColumn(
                "system_signal",
                options=[""] + _SYSTEM_SIGNALS,
                width="medium",
            ),
            "priority": st.column_config.SelectboxColumn(
                "priority",
                options=[""] + _PRIORITIES,
                width="small",
            ),
            "note": st.column_config.TextColumn("note", width="large"),
        },
        key="bulk_triage_editor",
    )

    cols = st.columns([1, 1, 4])
    with cols[0]:
        save = st.button("💾 Save all changes", type="primary", use_container_width=True)
    with cols[1]:
        revert = st.button("↩︎ Discard edits", use_container_width=True)

    if save:
        changed = apply_bulk_edits(edited, notes)
        if changed:
            save_notes(notes_path, notes)
            st.success(f"Saved {changed} change(s) to `{notes_path.name}`.")
            st.rerun()
        else:
            st.info("No changes detected.")
    if revert:
        # Drop the editor's session-state slot so it re-initialises from disk.
        st.session_state.pop("bulk_triage_editor", None)
        st.rerun()


def render_triage_panel(
    scenario: dict,
    result: dict | None,
    notes_path: Path | None,
    all_notes: dict,
) -> None:
    """Annotation form for one scenario; persists to the sidecar notes file."""
    if notes_path is None:
        st.info("Load an eval results file (sidebar) to enable triage notes.")
        return
    sid = scenario["id"]
    existing = all_notes.get(sid, {})

    st.subheader("📝 Triage")
    if existing:
        st.caption(f"_Last updated: {existing.get('updated_at', '?')}_")
    else:
        st.caption("_No annotations yet for this scenario._")

    with st.form(key=f"triage_{sid}"):
        c1, c2, c3 = st.columns(3)
        with c1:
            jv = st.selectbox(
                "Judge verdict",
                [_BLANK] + _JUDGE_VERDICTS,
                index=_idx(_JUDGE_VERDICTS, existing.get("judge_verdict")),
                help=(
                    "correct = judge agreed with reality. "
                    "wrong_pass = judge said pass, output bad (FP). "
                    "wrong_fail = judge said fail, output ok (FN)."
                ),
            )
        with c2:
            sa = st.selectbox(
                "Scenario action",
                [_BLANK] + _TRIAGE_ACTIONS,
                index=_idx(_TRIAGE_ACTIONS, existing.get("scenario_action")),
                help="What needs to happen to the scenario itself.",
            )
        with c3:
            pr = st.selectbox(
                "Priority",
                [_BLANK] + _PRIORITIES,
                index=_idx(_PRIORITIES, existing.get("priority")),
            )
        ss = st.selectbox(
            "System signal",
            [_BLANK] + _SYSTEM_SIGNALS,
            index=_idx(_SYSTEM_SIGNALS, existing.get("system_signal")),
            help="What this failure tells you about prompt / retrieval / model.",
        )
        note = st.text_area(
            "Note (hypothesis, context, what to fix)",
            value=existing.get("note", ""),
            height=140,
            placeholder=(
                "e.g. 'judge accepted Deep Drop Shot but expected third_shot_drop "
                "— shot family taxonomy may be too strict'"
            ),
        )
        col_a, col_b = st.columns(2)
        with col_a:
            saved = st.form_submit_button(
                "💾 Save triage", use_container_width=True, type="primary"
            )
        with col_b:
            cleared = st.form_submit_button(
                "🗑 Clear triage", use_container_width=True,
                help="Remove all triage data for this scenario",
            )

    if saved:
        entry = {
            "judge_verdict": None if jv == _BLANK else jv,
            "scenario_action": None if sa == _BLANK else sa,
            "priority": None if pr == _BLANK else pr,
            "system_signal": None if ss == _BLANK else ss,
            "note": note.strip(),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        all_notes[sid] = entry
        save_notes(notes_path, all_notes)
        st.success(f"Saved triage for `{sid}`.")
        st.rerun()
    elif cleared:
        if sid in all_notes:
            del all_notes[sid]
            save_notes(notes_path, all_notes)
            st.success(f"Cleared triage for `{sid}`.")
            st.rerun()
        else:
            st.info("Nothing to clear.")


# ── app ────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="Pickle Playbook Eval Viz", layout="wide")
    st.title("Pickle Playbook — Golden Scenario Explorer")

    scenarios = load_scenarios()

    # ── sidebar: results picker + filters ──────────────────────────────────
    st.sidebar.header("Data")
    result_files = list_result_files()
    options = ["(none)"] + result_files
    selected = st.sidebar.selectbox(
        "Eval results (optional)",
        options=options,
        format_func=lambda p: "(none)" if p == "(none)" else Path(p).name,
    )
    results = None
    if selected != "(none)":
        results = load_results(selected)
        summ = results["summary"]
        st.sidebar.caption(f"**{summ.get('total', '?')}** scenarios scored")
        if "overall_pass_rate" in summ:
            st.sidebar.caption(f"overall_pass_rate: **{summ['overall_pass_rate']}**")
        if "shot_match_rate" in summ:
            st.sidebar.caption(f"shot_match_rate: **{summ['shot_match_rate']}**")
        if "judge_pass_rate" in summ:
            st.sidebar.caption(f"judge_pass_rate: **{summ['judge_pass_rate']}**")

    st.sidebar.header("Filters")
    difficulties = sorted({s["difficulty"] for s in scenarios})
    skill_levels = sorted({str(s["state"]["skill_level"]) for s in scenarios})
    primary_shots = sorted({s["expert_answer"]["primary_shot"] for s in scenarios})
    heights = sorted({s["state"]["ball_height"] for s in scenarios})
    speeds = sorted({s["state"]["ball_speed"] for s in scenarios})

    sel_diff = st.sidebar.multiselect("Difficulty", difficulties, default=difficulties)
    sel_skill = st.sidebar.multiselect("Skill level", skill_levels, default=skill_levels)
    sel_height = st.sidebar.multiselect("Ball height", heights, default=heights)
    sel_speed = st.sidebar.multiselect("Ball speed", speeds, default=speeds)
    sel_shot = st.sidebar.multiselect("Primary shot", primary_shots, default=primary_shots)

    failure_modes = sorted({m for s in scenarios for m in s.get("failure_modes", [])})
    sel_modes: list[str] | None = None
    if failure_modes:
        sel_modes = st.sidebar.multiselect(
            "Failure modes", failure_modes, default=failure_modes,
            help="v2 schema. Scenarios may probe one or more modes (M1-M5).",
        )

    sel_quadrant: list[str] | None = None
    if results:
        quadrants = sorted({(r.get("quadrant") or "no_judge") for r in results["by_id"].values()})
        sel_quadrant = st.sidebar.multiselect("Quadrant", quadrants, default=quadrants)
        only_fails = st.sidebar.checkbox("Only failing scenarios", value=False)
    else:
        only_fails = False

    # ── sidebar: triage ────────────────────────────────────────────────────
    st.sidebar.header("Triage")
    notes_path = _notes_path(selected if selected != "(none)" else None)
    notes = load_notes(notes_path)
    flagged_only = False
    sel_triage_action = "any"
    sel_triage_priority = "any"
    if notes_path is not None:
        st.sidebar.caption(
            f"Notes: `{notes_path.name}`  ·  **{len(notes)}** annotated"
        )
        flagged_only = st.sidebar.checkbox("Only annotated scenarios", value=False)
        sel_triage_action = st.sidebar.selectbox(
            "Filter: scenario action", ["any"] + _TRIAGE_ACTIONS, index=0,
        )
        sel_triage_priority = st.sidebar.selectbox(
            "Filter: priority", ["any"] + _PRIORITIES, index=0,
        )
        if notes:
            report = build_triage_report(scenarios, notes, results)
            st.sidebar.download_button(
                "📥 Download triage report (.md)",
                data=report,
                file_name=f"{notes_path.stem}.report.md",
                mime="text/markdown",
            )
    else:
        st.sidebar.caption("Load a results file to enable triage.")

    def keep(s: dict) -> bool:
        if s["difficulty"] not in sel_diff:
            return False
        if str(s["state"]["skill_level"]) not in sel_skill:
            return False
        if s["state"]["ball_height"] not in sel_height:
            return False
        if s["state"]["ball_speed"] not in sel_speed:
            return False
        if s["expert_answer"]["primary_shot"] not in sel_shot:
            return False
        if sel_modes is not None and set(sel_modes) != set(failure_modes):
            # User has narrowed the mode filter — exclude scenarios outside it.
            # When all modes are selected (default), pass through scenarios that
            # lack the failure_modes field (e.g. legacy v1 rows).
            modes = s.get("failure_modes", [])
            if not modes or not any(m in sel_modes for m in modes):
                return False
        if results is not None:
            r = results["by_id"].get(s["id"])
            q = (r.get("quadrant") if r else None) or "no_judge"
            if sel_quadrant is not None and q not in sel_quadrant:
                return False
            if only_fails:
                if r is None:
                    # Unscored scenarios aren't failures; exclude from "only fails".
                    return False
                passed = r.get("overall_pass")
                if passed is None:
                    passed = r.get("shot_match")
                if passed:
                    return False
        if notes_path is not None:
            n = notes.get(s["id"])
            if flagged_only and not n:
                return False
            if sel_triage_action != "any":
                if not n or n.get("scenario_action") != sel_triage_action:
                    return False
            if sel_triage_priority != "any":
                if not n or n.get("priority") != sel_triage_priority:
                    return False
        return True

    filtered = [s for s in scenarios if keep(s)]

    # ── tabs ───────────────────────────────────────────────────────────────
    tab_overview, tab_bulk, tab_detail = st.tabs(["Overview", "Bulk triage", "Detail"])

    with tab_overview:
        st.markdown(f"**{len(filtered)}** of {len(scenarios)} scenarios shown")
        if not filtered:
            st.info("No scenarios match the current filters.")
        else:
            fig = render_overview(filtered, results)
            st.plotly_chart(fig, use_container_width=True)

            if results is not None:
                counts: dict[str, int] = {}
                for s in filtered:
                    r = results["by_id"].get(s["id"])
                    q = (r.get("quadrant") if r else None) or "no_judge"
                    counts[q] = counts.get(q, 0) + 1
                st.markdown("**Quadrant breakdown (filtered)**")
                cols = st.columns(max(len(counts), 1))
                for col, (q, n) in zip(cols, sorted(counts.items())):
                    col.metric(q, n)

    with tab_bulk:
        render_bulk_triage(filtered, results, notes_path, notes)

    with tab_detail:
        if not filtered:
            st.info("No scenarios match the current filters.")
            return

        ids = [s["id"] for s in filtered]
        selected_id = st.selectbox("Scenario", ids)
        scenario = next(s for s in filtered if s["id"] == selected_id)
        result = (results or {}).get("by_id", {}).get(selected_id)

        col_plot, col_info = st.columns([3, 2])
        with col_plot:
            st.plotly_chart(render_detail(scenario), use_container_width=True)
        with col_info:
            st.subheader("Expert answer")
            exp = scenario["expert_answer"]
            st.markdown(f"**Primary:** `{exp['primary_shot']}`")
            alts = exp.get("acceptable_alternatives") or []
            st.caption("Alternatives: " + (", ".join(f"`{a}`" for a in alts) if alts else "—"))
            must = exp.get("reasoning_must_mention") or []
            st.caption("Must mention: " + (", ".join(must) if must else "—"))
            if exp.get("expected_sequence"):
                with st.expander("Expected sequence"):
                    for i, step in enumerate(exp["expected_sequence"], 1):
                        st.write(f"{i}. {step}")
            if scenario.get("source"):
                st.caption(f"Source: _{scenario['source']}_")

            if result:
                st.subheader("Model result")
                overall = result.get("overall_pass")
                if overall is None:
                    overall = result.get("shot_match")
                badge = "✅" if overall else "❌"
                st.markdown(
                    f"**Predicted:** `{result.get('predicted_shot', '—')}` {badge}"
                )
                st.caption(
                    f"Family: `{result.get('predicted_family', '—')}`  ·  "
                    f"shot_match: **{result.get('shot_match')}**  ·  "
                    f"reasoning_coverage: **{result.get('reasoning_coverage', '—')}**"
                )

                # v2 deterministic checks (M2 advanced shot, M5 tactical mode).
                # Render only when the underlying fields are present so v1
                # results files don't show empty rows.
                m2_violation = result.get("m2_advanced_shot_violation")
                m5_match = result.get("m5_tactical_mode_match")
                if m2_violation is not None or m5_match is not None:
                    parts = []
                    if m2_violation is not None:
                        m2_label = "❌ M2 advanced-shot for sub-4.0" if m2_violation else "M2 ✓"
                        parts.append(f"**{m2_label}**")
                    if m5_match is not None:
                        m5_label = "M5 ✓" if m5_match else "❌ M5 posture mismatch"
                        parts.append(f"**{m5_label}**")
                    if parts:
                        st.caption("Deterministic: " + "  ·  ".join(parts))

                pred_posture = result.get("predicted_posture")
                exp_postures = result.get("expected_postures")
                exp_mode = result.get("expected_tactical_mode")
                if any(v is not None for v in (pred_posture, exp_postures, exp_mode)):
                    st.caption(
                        f"Posture: predicted=`{pred_posture or '—'}`  ·  "
                        f"expected=`{', '.join(exp_postures) if exp_postures else '—'}`  ·  "
                        f"state→mode=`{exp_mode or '—'}`"
                    )

                if mentions := result.get("mentions"):
                    st.caption("Mentions: " + ", ".join(
                        f"{k}={'✓' if v else '✗'}" for k, v in mentions.items()
                    ))
                if warning := result.get("warning"):
                    st.warning(warning)

                if judge := result.get("judge"):
                    st.subheader("Judge")
                    # v2 has state_use + ball_state_reading; v1 has the
                    # strategic_soundness/reasoning_quality/specificity trio.
                    if "state_use" in judge or "ball_state_reading" in judge:
                        jcols = st.columns(2)
                        jcols[0].metric("M3 state_use", judge.get("state_use"))
                        jcols[1].metric("M4 ball_state_reading", judge.get("ball_state_reading"))
                        st.caption(
                            f"M3 passed: **{judge.get('m3_passed')}**  ·  "
                            f"M4 passed: **{judge.get('m4_passed')}**  ·  "
                            f"quadrant: **{result.get('quadrant', '—')}**  ·  "
                            f"model: `{judge.get('model', '?')}`"
                        )
                    else:
                        # v1 archive results — render legacy fields
                        jcols = st.columns(3)
                        jcols[0].metric("Strategic", judge.get("strategic_soundness"))
                        jcols[1].metric("Reasoning", judge.get("reasoning_quality"))
                        jcols[2].metric("Specific", judge.get("specificity"))
                        st.caption(
                            f"skill_level_feasible: **{judge.get('skill_level_feasible')}**  ·  "
                            f"quadrant: **{result.get('quadrant', '—')}**  ·  "
                            f"model: `{judge.get('model', '?')}`"
                        )
                    if jnotes := judge.get("notes"):
                        st.info(jnotes)

        st.divider()
        render_triage_panel(scenario, result, notes_path, notes)


if __name__ == "__main__":
    main()
