import streamlit as st
import plotly.graph_objects as go
from runner import stream_single
from config import CODER, REVIEWER

DEFAULT_TASK = "Write a Python function that calculates the average of a list."


st.set_page_config(
    page_title="Multi agent Workflow Failure Detection",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 12px;
    height: 3.2rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s ease-in-out;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.35);
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    padding: 18px;
    border-radius: 16px;
}

div[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    overflow: hidden;
}

.main-title {
    font-size: 3.2rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.sub-title {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-bottom: 1.2rem;
}

.section-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 1rem 1.2rem;
}

.sidebar-title {
    font-size: 1.2rem;
    font-weight: 700;
    margin-top: 1rem;
    margin-bottom: 0.8rem;
}

.flag-pill {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    background: rgba(99,102,241,0.18);
    border: 1px solid rgba(99,102,241,0.35);
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

</style>
""", unsafe_allow_html=True)



st.markdown('<div class="main-title">Multi agent Workflow Failure Detection</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Detects inefficient multi agent workflow patterns and measures token savings in real time.</div>',
    unsafe_allow_html=True
)
st.divider()

with st.sidebar:

    st.markdown("## About")

    st.write(
        """
This project monitors multi-agent LLM workflows and detects inefficient looping behaviour in real time.

Instead of using expensive LLM evaluators or judges, the system relies on lightweight runtime signals such as repetition, stagnation, escalation, latency consistency, rejection cycles, and retry failures.

The goal is to stop workflows early once they begin wasting tokens without meaningful progress.
"""
    )

    st.markdown("## Detection Signals")

    st.markdown('<div class="flag-pill">repeat</div>', unsafe_allow_html=True)
    st.caption("The latest response is identical to the previous one.")

    st.markdown('<div class="flag-pill">stagnation</div>', unsafe_allow_html=True)
    st.caption("Agent responses become increasingly similar across turns.")

    st.markdown('<div class="flag-pill">latency</div>', unsafe_allow_html=True)
    st.caption("Response times stabilize across iterations, suggesting repetitive execution behaviour.")

    st.markdown('<div class="flag-pill">open_loop</div>', unsafe_allow_html=True)
    st.caption("The reviewer repeatedly asks unresolved follow-up questions while the coder keeps agreeing.")

    st.markdown('<div class="flag-pill">rejection_loop</div>', unsafe_allow_html=True)
    st.caption("The reviewer repeatedly rejects or requests small corrective refinements.")

    st.markdown('<div class="flag-pill">escalation</div>', unsafe_allow_html=True)
    st.caption("Token usage grows rapidly across turns, indicating runaway refinement.")

    st.markdown('<div class="flag-pill">error_loop</div>', unsafe_allow_html=True)
    st.caption("The workflow repeatedly encounters retries, API failures, or execution errors.")

    st.markdown("## Feed Indicators")

    st.write(
        """
- Green entries represent coder responses.
- Blue entries represent reviewer responses.
- Tags appearing in the **Baseline workflow** column indicate signals that would normally trigger an early stop.
- Red status messages indicate the detector terminated the workflow.
"""
    )

    st.markdown("## Benchmark Goal")

    st.write(
        """
The benchmark compares a normal multi-agent workflow against a protected workflow using the detector.

The primary objective is reducing unnecessary turns and token consumption while preserving useful progress.
"""
    )
with st.expander("Configure prompts", expanded=True):
    task_prompt = st.text_area("Task prompt", value=DEFAULT_TASK, height=68)
    pc, pr = st.columns(2)
    with pc:
        coder_prompt = st.text_area("Coder system prompt", value=CODER, height=140)
    with pr:
        reviewer_prompt = st.text_area("Reviewer system prompt", value=REVIEWER, height=140)

run_clicked = st.button("Run benchmark", type="primary", use_container_width=True)


def build_feed_md(rows: list) -> str:
    """
    Builds a markdown string for the live feed.
    Each row = one completed agent turn.
    """
    parts = []
    for row in rows:
        msg       = row["message"]
        sender    = msg["sender"]
        turn      = msg.get("turn", "?")
        tokens    = msg.get("tokens", 0) or 0
        latency   = msg.get("latency", 0) or 0
        new_flags = row.get("new_flags", [])
        deadlock  = row.get("deadlock", False)

        
        preview = (
            msg["content"][:90]
            .replace("\n", " ")
            .replace("`", "'")
            .strip()
        )

        if deadlock:
            icon      = "🔴"
            flag_note = f"&nbsp;&nbsp;← **loop_detector fired: {', '.join(new_flags or row['flags'])}**"
        elif sender == "coder":
            icon      = "🟢"
            flag_note = f"&nbsp;&nbsp;`{', '.join(new_flags)}`" if new_flags else ""
        else:
            icon      = "🔵"
            flag_note = f"&nbsp;&nbsp;`{', '.join(new_flags)}`" if new_flags else ""

        parts.append(
            f"{icon} **{sender.upper()}** &nbsp;·&nbsp; turn {turn} "
            f"&nbsp;·&nbsp; {tokens:,} tokens &nbsp;·&nbsp; {latency:.1f}s"
            f"{flag_note}  \n"
            f"<sub>{preview}…</sub>"
        )

    return "\n\n---\n\n".join(parts)



if run_clicked:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Without loop_detector")
        status1 = st.empty()
        feed1   = st.empty()

    with col2:
        st.subheader("With loop_detector")
        status2 = st.empty()
        feed2   = st.empty()


    status1.info("Running…")
    rows1 = []

    for event in stream_single(task_prompt, coder_prompt, reviewer_prompt, use_sentinel=False):
        rows1.append(event)
        feed1.markdown(build_feed_md(rows1), unsafe_allow_html=True)

    total_tokens_1 = rows1[-1]["total_tokens"] if rows1 else 0
    turns_1        = rows1[-1]["iteration"]    if rows1 else 0
    status1.success(f"Complete — {turns_1} turns · {total_tokens_1:,} tokens")

    
    status2.info("Running…")
    rows2 = []

    for event in stream_single(task_prompt, coder_prompt, reviewer_prompt, use_sentinel=True):
        rows2.append(event)
        feed2.markdown(build_feed_md(rows2), unsafe_allow_html=True)
        if event["deadlock"]:
            break  

    total_tokens_2 = rows2[-1]["total_tokens"] if rows2 else 0
    turns_2        = rows2[-1]["iteration"]    if rows2 else 0
    deadlock_flags = rows2[-1]["flags"]        if rows2 else []
    detected       = rows2[-1]["deadlock"]     if rows2 else False

    if detected:
        status2.error(
            f"Loop detected, stopped at turn {turns_2} · "
            f"{total_tokens_2:,} tokens · flags: {', '.join(deadlock_flags)}"
        )
    else:
        status2.success(f"Complete,  {turns_2} turns · {total_tokens_2:,} tokens")


    st.divider()
    st.markdown("## Benchmark Results")

    tokens_saved = total_tokens_1 - total_tokens_2
    turns_saved  = turns_1 - turns_2
    pct_saved    = (tokens_saved / total_tokens_1 * 100) if total_tokens_1 > 0 else 0

    st.markdown(
        f"""
    <div class="section-card">
    <h3 style="margin-top:0;">Token Reduction</h3>
    <h1 style="margin-bottom:0.2rem;">{pct_saved:.0f}%</h1>
    <p style="color:#94a3b8;">
    Saved {tokens_saved:,} tokens across {turns_saved} turns by stopping inefficient workflow patterns early.
    </p>
    </div>
    """,
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Turns saved",      f"{turns_saved}",    f"{turns_1} → {turns_2}")
    m2.metric("Tokens saved",     f"{tokens_saved:,}", f"{pct_saved:.0f}% reduction")
    m3.metric("Without detector", f"{total_tokens_1:,} tokens")
    m4.metric("With detector",    f"{total_tokens_2:,} tokens")

    st.write("")

    
    def tokens_by_turn(rows):
        return {r["message"]["turn"]: r["message"].get("tokens", 0) or 0 for r in rows}

    max_turn = max(
        max((r["message"]["turn"] for r in rows1), default=0),
        max((r["message"]["turn"] for r in rows2), default=0),
    )
    x_labels = [f"Turn {t}" for t in range(1, max_turn + 1)]
    t1 = tokens_by_turn(rows1)
    t2 = tokens_by_turn(rows2)

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name="Without detector",
        x=x_labels,
        y=[t1.get(t, 0) for t in range(1, max_turn + 1)],
        marker_color="#ef4444",
    ))
    fig1.add_trace(go.Bar(
        name="With detector",
        x=x_labels,
        y=[t2.get(t, 0) for t in range(1, max_turn + 1)],
        marker_color="#22c55e",
    ))
    fig1.update_layout(
        barmode="group",
        title="Tokens consumed per turn",
        xaxis_title="Turn",
        yaxis_title="Tokens",
        height=340,
        margin=dict(t=48, b=40, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig1, use_container_width=True)

    
    def reviewer_rows(rows):
        turn = 0
        out  = []
        for r in rows:
            if r["message"]["sender"] == "reviewer":
                turn += 1
                out.append({"reviewer_turn": turn, "tokens": r["message"].get("tokens", 0) or 0})
        return out

    rev1 = reviewer_rows(rows1)
    rev2 = reviewer_rows(rows2)

    if rev1 or rev2:
        fig2 = go.Figure()
        if rev1:
            fig2.add_trace(go.Scatter(
                name="Without detector",
                x=[r["reviewer_turn"] for r in rev1],
                y=[r["tokens"]        for r in rev1],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=8),
            ))
        if rev2:
            fig2.add_trace(go.Scatter(
                name="With detector",
                x=[r["reviewer_turn"] for r in rev2],
                y=[r["tokens"]        for r in rev2],
                mode="lines+markers",
                line=dict(color="#22c55e", width=2),
                marker=dict(size=8),
            ))
        fig2.update_layout(
            title="Reviewer response size over turns — escalation signal",
            xaxis_title="Reviewer turn",
            yaxis_title="Tokens",
            height=300,
            margin=dict(t=48, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig2, use_container_width=True)