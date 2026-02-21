import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta
import json
import os

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quadrant Task Manager",
    page_icon="📊",
    layout="wide",
)

# ─── Constants ─────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks_data.json")

QUADRANT_META = {
    "do_first": {
        "bg": "rgba(239,68,68,0.10)",
        "color": "#DC2626",
        "label": "Do First",
        "sub": "긴급 & 중요",
        "emoji": "🔴",
    },
    "delegate": {
        "bg": "rgba(249,115,22,0.10)",
        "color": "#EA580C",
        "label": "Delegate",
        "sub": "긴급 & 덜 중요",
        "emoji": "🟠",
    },
    "schedule": {
        "bg": "rgba(59,130,246,0.10)",
        "color": "#2563EB",
        "label": "Schedule",
        "sub": "덜 긴급 & 중요",
        "emoji": "🔵",
    },
    "eliminate": {
        "bg": "rgba(34,197,94,0.10)",
        "color": "#16A34A",
        "label": "Eliminate",
        "sub": "덜 긴급 & 덜 중요",
        "emoji": "🟢",
    },
}

PRESET_COLORS = [
    "#4A90D9",
    "#E74C3C",
    "#2ECC71",
    "#F39C12",
    "#9B59B6",
    "#1ABC9C",
    "#E67E22",
    "#34495E",
]


# ─── Data Helpers ──────────────────────────────────────────────────────────────
def load_tasks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def calc_urgency(deadline_str: str) -> float:
    """Map deadline → urgency on a 1‑10 scale.

    0 days left  → 10  (most urgent)
    30+ days left → 1   (least urgent)
    Linear interpolation in between.
    """
    days = (date.fromisoformat(deadline_str) - date.today()).days
    if days <= 0:
        return 10.0
    if days >= 30:
        return 1.0
    return round(10.0 - days * 9.0 / 30.0, 1)


def quadrant_key(importance: float, urgency: float) -> str:
    if importance > 5 and urgency > 5:
        return "do_first"
    if importance <= 5 and urgency > 5:
        return "delegate"
    if importance > 5 and urgency <= 5:
        return "schedule"
    return "eliminate"


def quadrant_info(importance, urgency):
    return QUADRANT_META[quadrant_key(importance, urgency)]


# ─── Session State ─────────────────────────────────────────────────────────────
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# Recalculate urgency every render (deadlines shift daily)
for _t in st.session_state.tasks:
    _t["urgency"] = calc_urgency(_t["deadline"])


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("➕ New Task")

    with st.form("add_task_form", clear_on_submit=True):
        name = st.text_input("Task Name")
        desc = st.text_area("Description", height=80)
        importance = st.slider("Importance (중요도)", 1, 10, 5)
        deadline = st.date_input(
            "Deadline (기한)",
            value=date.today() + timedelta(days=7),
        )
        color = st.color_picker("Block Color", "#4A90D9")
        submitted = st.form_submit_button("Add Task", use_container_width=True)

        if submitted:
            if name.strip():
                st.session_state.tasks.append(
                    {
                        "name": name.strip(),
                        "description": desc,
                        "importance": importance,
                        "deadline": deadline.isoformat(),
                        "urgency": calc_urgency(deadline.isoformat()),
                        "color": color,
                    }
                )
                save_tasks(st.session_state.tasks)
                st.rerun()
            else:
                st.error("Task name is required.")

    # ── Task list ──────────────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"📋 Tasks ({len(st.session_state.tasks)})")

    for i, task in enumerate(st.session_state.tasks):
        qi = quadrant_info(task["importance"], task["urgency"])
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"{qi['emoji']} **{task['name']}**")
            days_left = (date.fromisoformat(task["deadline"]) - date.today()).days
            due_text = f"D-{days_left}" if days_left >= 0 else f"D+{abs(days_left)}"
            st.caption(
                f"Imp {task['importance']} · Urg {task['urgency']:.1f} · "
                f"{task['deadline']} ({due_text})"
            )
        with c2:
            if st.button("🗑", key=f"del_{i}", help="Delete"):
                st.session_state.tasks.pop(i)
                save_tasks(st.session_state.tasks)
                st.rerun()


# ─── Main Area ─────────────────────────────────────────────────────────────────
st.title("📊 Quadrant Task Manager")
st.caption(
    "Importance (중요도) × Urgency (긴급도) · "
    "Click a task block to view details"
)

# ── Build Plotly Figure ────────────────────────────────────────────────────────
fig = go.Figure()

# Quadrant backgrounds
_qdefs = [
    # (x0, y0, x1, y1, key)
    (5, 5, 10.5, 10.5, "do_first"),
    (0, 5, 5, 10.5, "delegate"),
    (5, 0, 10.5, 5, "schedule"),
    (0, 0, 5, 5, "eliminate"),
]
for x0, y0, x1, y1, qk in _qdefs:
    qm = QUADRANT_META[qk]
    fig.add_shape(
        type="rect",
        x0=x0, y0=y0, x1=x1, y1=y1,
        fillcolor=qm["bg"],
        line=dict(width=0),
        layer="below",
    )
    fig.add_annotation(
        x=(x0 + x1) / 2,
        y=(y0 + y1) / 2,
        text=f"<b>{qm['label']}</b><br><span style='font-size:11px'>{qm['sub']}</span>",
        showarrow=False,
        font=dict(size=16, color=qm["color"]),
        opacity=0.3,
    )

# Dividers
fig.add_hline(y=5, line=dict(color="rgba(0,0,0,0.15)", width=2, dash="dot"))
fig.add_vline(x=5, line=dict(color="rgba(0,0,0,0.15)", width=2, dash="dot"))

# Task markers
tasks = st.session_state.tasks
if tasks:
    fig.add_trace(
        go.Scatter(
            x=[t["importance"] for t in tasks],
            y=[t["urgency"] for t in tasks],
            mode="markers+text",
            marker=dict(
                size=40,
                color=[t.get("color", "#4A90D9") for t in tasks],
                symbol="square",
                line=dict(width=2, color="white"),
                opacity=0.88,
            ),
            text=[
                t["name"][: 10] + ("…" if len(t["name"]) > 10 else "")
                for t in tasks
            ],
            textposition="middle center",
            textfont=dict(size=10, color="white", family="Arial Black"),
            hovertemplate=[
                f"<b>{t['name']}</b><br>"
                f"Importance: {t['importance']}/10<br>"
                f"Urgency: {t['urgency']:.1f}/10<br>"
                f"Deadline: {t['deadline']}<extra></extra>"
                for t in tasks
            ],
            showlegend=False,
        )
    )

fig.update_layout(
    xaxis=dict(
        title=dict(text="Importance (중요도) →", font=dict(size=14)),
        range=[-0.3, 11],
        dtick=1,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.04)",
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Urgency (긴급도) →", font=dict(size=14)),
        range=[-0.3, 11],
        dtick=1,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.04)",
        zeroline=False,
    ),
    height=650,
    margin=dict(l=60, r=30, t=30, b=60),
    plot_bgcolor="white",
    paper_bgcolor="white",
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#ccc"),
    dragmode="pan",
)

# Render with click detection
event = st.plotly_chart(
    fig,
    width="stretch",
    on_select="rerun",
    selection_mode="points",
    key="quadrant_chart",
)

# ── Task Detail Panel (on click) ──────────────────────────────────────────────
if tasks and event and event.selection and event.selection.points:
    pt = event.selection.points[0]
    idx = pt.get("point_index", pt.get("point_number", -1))

    if 0 <= idx < len(tasks):
        task = tasks[idx]
        qi = quadrant_info(task["importance"], task["urgency"])
        days_left = (date.fromisoformat(task["deadline"]) - date.today()).days

        st.divider()
        st.subheader(f"{qi['emoji']} {task['name']}")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Importance", f"{task['importance']} / 10")
        with c2:
            st.metric("Urgency", f"{task['urgency']:.1f} / 10")
        with c3:
            if days_left >= 0:
                st.metric("D‑Day", task["deadline"], delta=f"D-{days_left}")
            else:
                st.metric(
                    "D‑Day",
                    task["deadline"],
                    delta=f"{abs(days_left)}일 초과",
                    delta_color="inverse",
                )
        with c4:
            st.metric("Quadrant", f"{qi['label']}")

        if task.get("description"):
            st.info(task["description"])
        else:
            st.caption("No description.")

elif not tasks:
    st.info("👈 사이드바에서 첫 번째 Task를 추가해보세요!")
