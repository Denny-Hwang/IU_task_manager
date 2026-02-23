# 📊 Quadrant Task Manager

Eisenhower Matrix 기반의 인터랙티브 Task 관리 앱입니다.
**Importance(중요도)** × **Urgency(긴급도)** 4사분면에 Task를 배치하고, 클릭하여 상세 정보를 확인할 수 있습니다.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 주요 기능

### 4사분면 차트
| 사분면 | 기준 | 의미 |
|:---:|:---:|:---:|
| 🔴 **Do First** | 긴급 + 중요 | 즉시 처리 |
| 🟠 **Delegate** | 긴급 + 덜 중요 | 위임 가능 |
| 🔵 **Schedule** | 덜 긴급 + 중요 | 일정 계획 |
| 🟢 **Eliminate** | 덜 긴급 + 덜 중요 | 제거 고려 |

- **X축**: Importance (중요도, 1~10 수동 입력)
- **Y축**: Urgency (긴급도, 1~10 Deadline으로부터 자동 계산)
  - D-0 → 10 (최대 긴급) / D-30+ → 1 (최소 긴급)

### 인터랙티브 UI
- Task 블록을 **클릭**하면 하단에 상세 정보 패널 표시
- **Hover**로 Task 요약 확인
- 사이드바에서 Task 추가/삭제

### 예제 모드 (Demo Mode)
- 첫 실행 시 8개 예제 Task가 4사분면에 배치되어 사용법을 안내
- **새로 시작하기** — 예제 삭제 후 빈 상태로 시작
- **예제에 이어서 작업** — 예제를 유지하며 내 Task 추가

### Export
| 포맷 | 설명 |
|:---:|:---|
| 📊 **Excel (.xlsx)** | Task Summary + Gantt Chart (일별 타임라인) + Milestones (기한순 상태별 정리) |
| 📸 **PNG** | 4사분면 차트를 고해상도 이미지로 저장 |
| 🌐 **HTML** | 인터랙티브 Plotly 차트를 HTML 파일로 저장 |

## 기술 스택

- [Streamlit](https://streamlit.io/) — UI 프레임워크
- [Plotly](https://plotly.com/python/) — 인터랙티브 차트
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel 내보내기
- [Kaleido](https://github.com/nicholasgasior/kaleido) — 차트 이미지 변환
