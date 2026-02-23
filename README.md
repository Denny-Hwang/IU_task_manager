# Quadrant Task Manager

An interactive Eisenhower Matrix task manager built with **Streamlit** and **ECharts**.
Place tasks on a 4-quadrant chart by **Importance** × **Urgency**, then tap/click any block to see full details.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

### 4-Quadrant Chart (ECharts)
| Quadrant | Criteria | Meaning |
|:---:|:---:|:---:|
| Do First | Urgent + Important | Handle immediately |
| Delegate | Urgent + Less important | Can be delegated |
| Schedule | Less urgent + Important | Plan ahead |
| Eliminate | Less urgent + Less important | Consider removing |

- **X-axis**: Importance (1–10, manual input)
- **Y-axis**: Urgency (1–10, auto-calculated from deadline)
  - D-0 → 10 (most urgent) / D-30+ → 1 (least urgent)

### Mobile-First Design
- **ECharts** — lightweight, touch-friendly charting (replaced Plotly)
- **Tap to view** — tap any task block to see full details below the chart
- **Pinch to zoom** — native touch zoom via ECharts dataZoom
- **Reset view** — toolbar button restores the original viewport after panning/zooming
- **CJK-aware labels** — smart 2-line text wrapping that respects double-width characters

### Demo Mode
- 8 example tasks pre-loaded across all 4 quadrants
- **Start fresh** — clear examples and begin with an empty chart
- **Continue with examples** — keep the examples and add your own tasks

### Export
| Format | Description |
|:---:|:---|
| Excel (.xlsx) | Task Summary + Gantt Chart (daily timeline) + Milestones (sorted by deadline) |
| HTML | Interactive ECharts chart as a standalone web page |
| PNG | Use the chart toolbar's save-as-image button (built into the chart) |

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [ECharts](https://echarts.apache.org/) via [streamlit-echarts](https://github.com/andfanilo/streamlit-echarts) — interactive chart
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel export
