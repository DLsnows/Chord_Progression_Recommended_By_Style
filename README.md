# Chord Progression Recommender

Interactive chord progression recommendation based on musical style. Enter a natural language query like "jazz ballad 1960s verse" — the system recommends chords one at a time using a weighted n-gram model trained on ~680,000 compositions.

## Architecture

- **Backend**: Python / FastAPI / Pydantic v2 / scipy sparse matrices / SQLite
- **Frontend**: React 19 / TypeScript / Vite / SVG piano roll / Tone.js MIDI playback
- **Data**: [Chordonomicon](https://huggingface.co/datasets/ailsntua/Chordonomicon) via HuggingFace — 57,523 style groups, 95M chord bigrams

## Quick Start

### 一键启动 (推荐)

```powershell
powershell -ExecutionPolicy Bypass -File start.ps1
```

脚本会自动启动后端 (port 8000) 和前端 (port 5173)，按任意键停止。

### 首次搭建

首次使用需先构建数据集（约 90 分钟，只需运行一次）：

```bash
cd backend
.\.venv\Scripts\python.exe scripts\download_data.py   # 下载和弦映射表 + 数据集
.\.venv\Scripts\python.exe scripts\build_matrices.py  # 构建转移矩阵 (587 MB)
```

前端依赖：

```bash
cd frontend
npm install
```

### 手动启动

```bash
# 终端 1 — 后端
cd backend
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000

# 终端 2 — 前端
cd frontend
npm run dev
```

## Usage

1. Open http://localhost:5173 with the backend running
2. Type a style query: `jazz ballad 1960s verse`, `rock 1970s chorus`, etc.
3. Pick a matching style from the ranked results
4. Click a chord card to select it, or click the ♪ button to preview its sound
5. Continue selecting chords to build your progression
6. Use **Play All** to hear the full sequence, **Undo** to go back, **Fork** to try alternate paths
7. Click **Finish** to compare all branches side by side

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/styles/search` | NL style query → ranked matches |
| GET | `/api/v1/styles` | All available genre/decade/section dimensions |
| POST | `/api/v1/sessions` | Start a recommendation session |
| GET | `/api/v1/sessions` | List recent sessions |
| GET | `/api/v1/sessions/{id}` | Full session state with all branches |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/sessions/{id}/select` | Pick a chord → get next 5 candidates |
| POST | `/api/v1/sessions/{id}/undo` | Undo last pick |
| POST | `/api/v1/sessions/{id}/branches` | Fork a new branch at position N |
| PUT | `/api/v1/sessions/{id}/branches/{bid}` | Switch active branch |
| GET | `/api/v1/chords/{name}` | Chord detail (MIDI notes, intervals, vector) |

## Key Design Decisions

- **Dual-factor recommendation** (alpha=0.85): chord transition probability + independent root-motion probability
- **Transposition augmentation**: 12-key augmentation with Gaussian distance weighting (sigma=3.85, range 1.0–0.30)
- **Three-tier style fallback**: exact tag match → same genre/section (all decades) → global
- **Sparse transition matrices**: scipy CSR via parquet (587 MB for 57K groups vs. multi-GB dense)
- **SQLite session persistence**: multi-branch selection trees for A/B progression comparison
