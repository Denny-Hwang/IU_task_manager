import streamlit as st
from streamlit_echarts import st_echarts
from datetime import date, timedelta
import json
import os
import io
import html as html_mod
import unicodedata

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
        "color_alpha": "rgba(220,38,38,0.3)",
        "fill": "FFCCCC",
        "label": "Do First",
        "sub": "긴급 & 중요",
        "emoji": "🔴",
    },
    "delegate": {
        "bg": "rgba(249,115,22,0.10)",
        "color": "#EA580C",
        "color_alpha": "rgba(234,88,12,0.3)",
        "fill": "FFE0CC",
        "label": "Delegate",
        "sub": "긴급 & 덜 중요",
        "emoji": "🟠",
    },
    "schedule": {
        "bg": "rgba(59,130,246,0.10)",
        "color": "#2563EB",
        "color_alpha": "rgba(37,99,235,0.3)",
        "fill": "CCE0FF",
        "label": "Schedule",
        "sub": "덜 긴급 & 중요",
        "emoji": "🔵",
    },
    "eliminate": {
        "bg": "rgba(34,197,94,0.10)",
        "color": "#16A34A",
        "color_alpha": "rgba(22,163,74,0.3)",
        "fill": "CCFFCC",
        "label": "Eliminate",
        "sub": "덜 긴급 & 덜 중요",
        "emoji": "🟢",
    },
}


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
    """Map deadline to urgency 1-10. Closer deadline = higher urgency."""
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


# ─── Text Helpers ──────────────────────────────────────────────────────────────
def _display_width(s):
    """Calculate display width considering CJK double-width chars."""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def _truncate(s, max_w):
    """Truncate string to max display width, adding ellipsis if needed."""
    w = 0
    for i, ch in enumerate(s):
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if w + cw > max_w:
            return s[:i] + "…"
        w += cw
    return s


def format_block_label(name, deadline_str):
    """Format task name + D-day to fit inside chart block (2 lines, \\n separated)."""
    MAX_WIDTH = 12

    days = (date.fromisoformat(deadline_str) - date.today()).days
    d_text = f"D-{days}" if days >= 0 else f"D+{abs(days)}"

    name_w = _display_width(name)
    if name_w <= MAX_WIDTH:
        return f"{name}\n{d_text}"

    # Find the best space-break that balances both lines
    candidates = []
    for i, ch in enumerate(name):
        if ch == " " and 0 < i < len(name) - 1:
            lw = _display_width(name[:i])
            rw = _display_width(name[i + 1:])
            if lw <= MAX_WIDTH:
                candidates.append((i, abs(lw - rw)))

    if candidates:
        # On tie, prefer later break (longer line1, more natural)
        best_break = min(candidates, key=lambda x: (x[1], -x[0]))[0]
        line1 = name[:best_break]
        line2 = name[best_break + 1:]
        if _display_width(line2) > MAX_WIDTH:
            line2 = _truncate(line2, MAX_WIDTH - 1)
        return f"{line1}\n{line2}"

    # No good space break — hard truncate
    line1 = _truncate(name, MAX_WIDTH)
    return f"{line1}\n{d_text}"


# ─── Example Tasks ─────────────────────────────────────────────────────────────
def generate_example_tasks():
    today = date.today()
    examples = [
        {
            "name": "서버 장애 대응",
            "description": "프로덕션 서버 긴급 복구 — CPU 사용률 95% 초과 알림 발생. 즉시 원인 분석 및 조치 필요.",
            "importance": 9,
            "deadline": (today + timedelta(days=1)).isoformat(),
            "color": "#E74C3C",
        },
        {
            "name": "클라이언트 미팅 준비",
            "description": "목요일 클라이언트 프레젠테이션 자료 준비. 제안서 및 데모 시나리오 완성.",
            "importance": 8,
            "deadline": (today + timedelta(days=3)).isoformat(),
            "color": "#C0392B",
        },
        {
            "name": "이메일 회신",
            "description": "팀장님 이메일 및 협업 부서 문의 회신. 단순 확인/전달 업무.",
            "importance": 3,
            "deadline": (today + timedelta(days=2)).isoformat(),
            "color": "#F39C12",
        },
        {
            "name": "비용 정산서 제출",
            "description": "지난달 출장비 및 경비 정산서를 경영지원팀에 제출.",
            "importance": 4,
            "deadline": (today + timedelta(days=4)).isoformat(),
            "color": "#E67E22",
        },
        {
            "name": "신규 기능 설계",
            "description": "Q2 로드맵 핵심 기능 아키텍처 설계 문서 작성. 기술 스택 선정 포함.",
            "importance": 9,
            "deadline": (today + timedelta(days=21)).isoformat(),
            "color": "#3498DB",
        },
        {
            "name": "기술 부채 정리",
            "description": "레거시 코드 리팩토링 및 테스트 커버리지 개선 계획 수립.",
            "importance": 7,
            "deadline": (today + timedelta(days=18)).isoformat(),
            "color": "#2980B9",
        },
        {
            "name": "사무용품 정리",
            "description": "책상 정리 및 불필요한 문서 폐기. 시간 날 때 처리.",
            "importance": 2,
            "deadline": (today + timedelta(days=25)).isoformat(),
            "color": "#2ECC71",
        },
        {
            "name": "뉴스레터 구독 정리",
            "description": "안 읽는 뉴스레터 구독 취소 및 정보 채널 정리.",
            "importance": 1,
            "deadline": (today + timedelta(days=28)).isoformat(),
            "color": "#1ABC9C",
        },
    ]
    for t in examples:
        t["urgency"] = calc_urgency(t["deadline"])
    return examples


# ─── Export: Excel with Gantt & Milestones ─────────────────────────────────────
def build_excel(tasks):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    # ── Sheet 1: Task Summary ──────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Tasks"
    headers1 = ["Task Name", "Description", "Importance", "Urgency", "Deadline", "D-Day", "Quadrant"]
    for j, h in enumerate(headers1, 1):
        cell = ws1.cell(1, j, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    for i, task in enumerate(tasks, 2):
        qi = quadrant_info(task["importance"], task["urgency"])
        days_left = (date.fromisoformat(task["deadline"]) - date.today()).days
        d_text = f"D-{days_left}" if days_left >= 0 else f"D+{abs(days_left)}"
        row = [
            task["name"],
            task.get("description", ""),
            task["importance"],
            round(task["urgency"], 1),
            task["deadline"],
            d_text,
            f"{qi['emoji']} {qi['label']}",
        ]
        for j, val in enumerate(row, 1):
            cell = ws1.cell(i, j, val)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=(j == 2))

    ws1.column_dimensions["A"].width = 22
    ws1.column_dimensions["B"].width = 40
    ws1.column_dimensions["C"].width = 12
    ws1.column_dimensions["D"].width = 10
    ws1.column_dimensions["E"].width = 14
    ws1.column_dimensions["F"].width = 10
    ws1.column_dimensions["G"].width = 16

    # ── Sheet 2: Gantt Chart ───────────────────────────────────────────────────
    ws2 = wb.create_sheet("Gantt Chart")

    today = date.today()
    if tasks:
        deadlines = [date.fromisoformat(t["deadline"]) for t in tasks]
        max_dl = max(deadlines)
        end_date = max(max_dl, today) + timedelta(days=3)
    else:
        end_date = today + timedelta(days=30)

    date_range = []
    cur = today
    while cur <= end_date:
        date_range.append(cur)
        cur += timedelta(days=1)

    fixed_headers = ["Task", "Quadrant", "Deadline"]
    for j, h in enumerate(fixed_headers, 1):
        cell = ws2.cell(1, j, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    from openpyxl.utils import get_column_letter

    today_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    for j, d in enumerate(date_range):
        col = j + 4
        cell = ws2.cell(1, col, d.strftime("%m/%d"))
        cell.font = Font(bold=(d == today), size=9, color="FFFFFF" if d != today else "000000")
        cell.fill = header_fill if d != today else today_fill
        cell.alignment = Alignment(horizontal="center", text_rotation=90)
        cell.border = thin_border
        ws2.column_dimensions[get_column_letter(col)].width = 5

    ws2.column_dimensions["A"].width = 22
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 12

    sorted_gantt = sorted(tasks, key=lambda t: t["deadline"])
    for i, task in enumerate(sorted_gantt, 2):
        qk = quadrant_key(task["importance"], task["urgency"])
        qi = QUADRANT_META[qk]
        fill = PatternFill(start_color=qi["fill"], end_color=qi["fill"], fill_type="solid")
        dl = date.fromisoformat(task["deadline"])

        ws2.cell(i, 1, task["name"]).border = thin_border
        ws2.cell(i, 2, qi["label"]).border = thin_border
        ws2.cell(i, 3, task["deadline"]).border = thin_border

        for j, d in enumerate(date_range):
            col = j + 4
            cell = ws2.cell(i, col)
            cell.border = thin_border
            if d <= dl:
                cell.fill = fill
            if d == dl:
                cell.value = "▶"
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal="center")
            if d == today:
                cell.border = Border(
                    left=Side(style="medium", color="FF8C00"),
                    right=Side(style="medium", color="FF8C00"),
                    top=Side(style="thin", color="CCCCCC"),
                    bottom=Side(style="thin", color="CCCCCC"),
                )

    # ── Sheet 3: Milestones ────────────────────────────────────────────────────
    ws3 = wb.create_sheet("Milestones")
    headers3 = ["#", "Milestone", "Deadline", "D-Day", "Status", "Importance", "Urgency", "Quadrant"]
    for j, h in enumerate(headers3, 1):
        cell = ws3.cell(1, j, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    sorted_ms = sorted(tasks, key=lambda t: t["deadline"])
    status_fills = {
        "overdue": PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"),
        "today": PatternFill(start_color="FFE0CC", end_color="FFE0CC", fill_type="solid"),
        "week": PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"),
        "upcoming": PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid"),
    }
    for i, task in enumerate(sorted_ms, 2):
        qi = quadrant_info(task["importance"], task["urgency"])
        days_left = (date.fromisoformat(task["deadline"]) - today).days
        d_text = f"D-{days_left}" if days_left >= 0 else f"D+{abs(days_left)}"

        if days_left < 0:
            status, sfill = "Overdue", status_fills["overdue"]
        elif days_left == 0:
            status, sfill = "Due Today", status_fills["today"]
        elif days_left <= 7:
            status, sfill = "This Week", status_fills["week"]
        else:
            status, sfill = "Upcoming", status_fills["upcoming"]

        row = [i - 1, task["name"], task["deadline"], d_text, status,
               task["importance"], round(task["urgency"], 1), f"{qi['emoji']} {qi['label']}"]
        for j, val in enumerate(row, 1):
            cell = ws3.cell(i, j, val)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")
            if j == 5:
                cell.fill = sfill

    ws3.column_dimensions["A"].width = 5
    ws3.column_dimensions["B"].width = 22
    ws3.column_dimensions["C"].width = 14
    ws3.column_dimensions["D"].width = 10
    ws3.column_dimensions["E"].width = 14
    ws3.column_dimensions["F"].width = 12
    ws3.column_dimensions["G"].width = 10
    ws3.column_dimensions["H"].width = 16

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def build_chart_html(chart_option):
    """Generate standalone ECharts HTML page from chart option dict."""
    option_json = json.dumps(chart_option, ensure_ascii=False).replace("</", "<\\/")
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Quadrant Task Manager</title>\n'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>\n'
        '<style>\n'
        '  body { margin:0; padding:0; background:#fff; }\n'
        '  #chart { width:100vw; height:100vh; }\n'
        '</style>\n'
        '</head>\n'
        '<body>\n'
        '<div id="chart"></div>\n'
        '<script>\n'
        '  var chart = echarts.init(document.getElementById("chart"));\n'
        f'  chart.setOption({option_json});\n'
        '  window.addEventListener("resize", function() { chart.resize(); });\n'
        '</script>\n'
        '</body>\n'
        '</html>'
    )


# ─── Session State ─────────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    existing = load_tasks()
    if existing:
        st.session_state.tasks = existing
        st.session_state.demo_mode = False
    else:
        st.session_state.tasks = generate_example_tasks()
        st.session_state.demo_mode = True

# Recalculate urgency every render
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
                if st.session_state.demo_mode:
                    st.session_state.demo_mode = False
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
                if "selected_task_idx" in st.session_state:
                    del st.session_state["selected_task_idx"]
                save_tasks(st.session_state.tasks)
                st.rerun()

    # ── Reset Section ──────────────────────────────────────────────────────────
    st.divider()
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🗑️ Clear All", use_container_width=True, help="Delete all tasks"):
            st.session_state.tasks = []
            st.session_state.demo_mode = False
            if "selected_task_idx" in st.session_state:
                del st.session_state["selected_task_idx"]
            save_tasks([])
            st.rerun()
    with rc2:
        if st.button("📦 Load Examples", use_container_width=True, help="Load example tasks"):
            st.session_state.tasks = generate_example_tasks()
            st.session_state.demo_mode = True
            if "selected_task_idx" in st.session_state:
                del st.session_state["selected_task_idx"]
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()


# ─── Main Area ─────────────────────────────────────────────────────────────────
st.title("📊 Quadrant Task Manager")
st.caption(
    "Importance (중요도) × Urgency (긴급도) · "
    "블록을 탭/클릭하면 상세 정보가 표시됩니다"
)

# ── Demo Mode Banner ───────────────────────────────────────────────────────────
if st.session_state.demo_mode:
    with st.container(border=True):
        st.markdown(
            "#### 🎯 예제 모드\n"
            "현재 **예제 Task**들이 표시되어 있습니다. "
            "차트의 블록을 클릭해보고, 각 사분면의 의미를 확인해보세요!\n\n"
            "| 사분면 | 의미 | 기준 |\n"
            "|:---:|:---:|:---:|\n"
            "| 🔴 **Do First** | 즉시 처리 | 긴급 + 중요 |\n"
            "| 🟠 **Delegate** | 위임 가능 | 긴급 + 덜 중요 |\n"
            "| 🔵 **Schedule** | 일정 계획 | 덜 긴급 + 중요 |\n"
            "| 🟢 **Eliminate** | 제거 고려 | 덜 긴급 + 덜 중요 |\n\n"
            "💡 **Urgency**(긴급도)는 **Deadline**(기한)으로부터 자동 계산됩니다. "
            "(D-0 → 10, D-30+ → 1)"
        )
        bc1, bc2, _ = st.columns([1, 1, 3])
        with bc1:
            if st.button("🚀 **새로 시작하기**", use_container_width=True, type="primary"):
                st.session_state.tasks = []
                st.session_state.demo_mode = False
                save_tasks([])
                st.rerun()
        with bc2:
            if st.button("✏️ 예제에 이어서 작업", use_container_width=True):
                st.session_state.demo_mode = False
                save_tasks(st.session_state.tasks)
                st.rerun()

# ── Build ECharts ──────────────────────────────────────────────────────────────
tasks = st.session_state.tasks

# Prepare scatter data for task blocks
scatter_data = []
for t in tasks:
    qi = quadrant_info(t["importance"], t["urgency"])
    label_text = format_block_label(t["name"], t["deadline"])
    days_left = (date.fromisoformat(t["deadline"]) - date.today()).days
    d_text = f"D-{days_left}" if days_left >= 0 else f"D+{abs(days_left)}"
    safe_name = html_mod.escape(t["name"])

    scatter_data.append({
        "value": [t["importance"], t["urgency"]],
        "name": (
            f"<b>{safe_name}</b><br/>"
            f"Importance: {t['importance']}/10 · "
            f"Urgency: {t['urgency']:.1f}/10<br/>"
            f"Deadline: {t['deadline']} ({d_text})<br/>"
            f"{qi['emoji']} {qi['label']}"
        ),
        "itemStyle": {
            "color": t.get("color", "#4A90D9"),
            "borderColor": "#fff",
            "borderWidth": 2,
            "opacity": 0.9,
        },
        "label": {
            "show": True,
            "position": "inside",
            "formatter": label_text,
            "color": "#fff",
            "fontSize": 10,
            "fontWeight": "bold",
            "lineHeight": 14,
            "width": 72,
            "overflow": "truncate",
        },
    })

# Quadrant background label data (markPoint)
q_label_data = []
_positions = {
    "do_first": [7.75, 7.75],
    "delegate": [2.5, 7.75],
    "schedule": [7.75, 2.5],
    "eliminate": [2.5, 2.5],
}
for qk, coord in _positions.items():
    qm = QUADRANT_META[qk]
    q_label_data.append({
        "coord": coord,
        "symbol": "none",
        "label": {
            "show": True,
            "formatter": f"{qm['label']}\n{qm['sub']}",
            "color": qm["color_alpha"],
            "fontSize": 14,
            "fontWeight": "bold",
            "lineHeight": 20,
        },
    })

# Quadrant background area data (markArea)
mark_area_data = [
    [{"xAxis": 5, "yAxis": 5, "itemStyle": {"color": QUADRANT_META["do_first"]["bg"], "borderWidth": 0}},
     {"xAxis": 10.5, "yAxis": 10.5}],
    [{"xAxis": 0, "yAxis": 5, "itemStyle": {"color": QUADRANT_META["delegate"]["bg"], "borderWidth": 0}},
     {"xAxis": 5, "yAxis": 10.5}],
    [{"xAxis": 5, "yAxis": 0, "itemStyle": {"color": QUADRANT_META["schedule"]["bg"], "borderWidth": 0}},
     {"xAxis": 10.5, "yAxis": 5}],
    [{"xAxis": 0, "yAxis": 0, "itemStyle": {"color": QUADRANT_META["eliminate"]["bg"], "borderWidth": 0}},
     {"xAxis": 5, "yAxis": 5}],
]

chart_option = {
    "backgroundColor": "#fff",
    "grid": {
        "left": 50,
        "right": 20,
        "top": 40,
        "bottom": 50,
        "containLabel": False,
    },
    "tooltip": {
        "trigger": "item",
        "formatter": "{b}",
        "backgroundColor": "rgba(255,255,255,0.96)",
        "borderColor": "#ddd",
        "textStyle": {"color": "#333", "fontSize": 13},
        "extraCssText": "box-shadow: 0 2px 8px rgba(0,0,0,0.12); max-width: 280px;",
    },
    "xAxis": {
        "name": "Importance →",
        "nameLocation": "middle",
        "nameGap": 28,
        "nameTextStyle": {"fontSize": 12, "color": "#888"},
        "min": 0,
        "max": 10.5,
        "interval": 1,
        "splitLine": {"lineStyle": {"color": "rgba(0,0,0,0.04)"}},
        "axisLine": {"lineStyle": {"color": "#ccc"}},
        "axisTick": {"lineStyle": {"color": "#ccc"}},
        "axisLabel": {"color": "#aaa", "fontSize": 11},
    },
    "yAxis": {
        "name": "Urgency →",
        "nameLocation": "middle",
        "nameGap": 35,
        "nameTextStyle": {"fontSize": 12, "color": "#888"},
        "min": 0,
        "max": 10.5,
        "interval": 1,
        "splitLine": {"lineStyle": {"color": "rgba(0,0,0,0.04)"}},
        "axisLine": {"lineStyle": {"color": "#ccc"}},
        "axisTick": {"lineStyle": {"color": "#ccc"}},
        "axisLabel": {"color": "#aaa", "fontSize": 11},
    },
    "toolbox": {
        "right": 12,
        "top": 5,
        "feature": {
            "restore": {"show": True, "title": "뷰 초기화"},
            "saveAsImage": {
                "show": True,
                "title": "이미지 저장",
                "pixelRatio": 2,
                "name": f"quadrant_chart_{date.today().isoformat()}",
            },
        },
        "iconStyle": {"borderColor": "#999"},
    },
    "dataZoom": [
        {"type": "inside", "xAxisIndex": 0},
        {"type": "inside", "yAxisIndex": 0},
    ],
    "series": [
        # Series 0: quadrant backgrounds, divider lines, quadrant labels (non-interactive)
        {
            "type": "scatter",
            "data": [],
            "silent": True,
            "z": 1,
            "markArea": {
                "silent": True,
                "data": mark_area_data,
            },
            "markLine": {
                "silent": True,
                "symbol": "none",
                "lineStyle": {"color": "rgba(0,0,0,0.15)", "width": 1.5, "type": "dashed"},
                "data": [{"xAxis": 5}, {"yAxis": 5}],
                "label": {"show": False},
            },
            "markPoint": {
                "silent": True,
                "data": q_label_data,
            },
        },
        # Series 1: task data points (interactive)
        {
            "type": "scatter",
            "symbol": "roundRect",
            "symbolSize": [80, 48],
            "data": scatter_data,
            "z": 2,
            "animationDuration": 500,
        },
    ],
}

# Render chart with click event detection
events = {
    "click": "function(params) { return (params.seriesIndex === 1 && params.dataIndex !== undefined) ? params.dataIndex : -1; }"
}
clicked = st_echarts(chart_option, events=events, height="600px", key="quadrant_chart")

# Store clicked task index in session state
if clicked is not None:
    try:
        idx = int(clicked)
        if 0 <= idx < len(tasks):
            st.session_state.selected_task_idx = idx
    except (TypeError, ValueError):
        pass

# ── Export Section ─────────────────────────────────────────────────────────────
if tasks:
    st.divider()
    st.subheader("📥 Export")
    ex1, ex2 = st.columns(2)

    with ex1:
        excel_buf = build_excel(tasks)
        st.download_button(
            "📊 Excel (Gantt + Milestones)",
            data=excel_buf,
            file_name=f"task_plan_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with ex2:
        html_str = build_chart_html(chart_option)
        st.download_button(
            "🌐 Interactive Chart (HTML)",
            data=html_str,
            file_name=f"quadrant_chart_{date.today().isoformat()}.html",
            mime="text/html",
            use_container_width=True,
        )

    st.caption("💡 차트 우측 상단 툴바의 📷 아이콘으로 PNG 이미지를 저장할 수 있습니다.")

# ── Task Detail Panel (on click/tap) ─────────────────────────────────────────
if tasks and "selected_task_idx" in st.session_state:
    idx = st.session_state.selected_task_idx
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
