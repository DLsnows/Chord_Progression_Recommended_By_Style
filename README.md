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
7. Adjust the **Musicality** slider to control the trade-off between standard triads and complex chords
8. Type a custom chord name (e.g., `Cmaj7`, `Amin`) to add chords not in the AI recommendations
9. Click **Finish** to compare all branches side by side
10. Access **History** to resume or delete past sessions

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
| GET | `/api/v1/chords/{name}` | Chord detail with chord_idx (MIDI notes, intervals, vector) |
| POST | `/api/v1/sessions/{id}/resume` | Resume past session with current candidates |
| PATCH | `/api/v1/sessions/{id}/musicality` | Update musicality bias (0.0–1.0) and regenerate candidates |

## Key Design Decisions

- **Dual-factor recommendation** (alpha=0.85): chord transition probability + independent root-motion probability
- **Transposition augmentation**: 12-key augmentation with Gaussian distance weighting (sigma=3.85, range 1.0–0.30)
- **Three-tier style fallback**: exact tag match → same genre/section (all decades) → global
- **Sparse transition matrices**: scipy CSR via parquet (587 MB for 57K groups vs. multi-GB dense)
- **SQLite session persistence**: multi-branch selection trees for A/B progression comparison

## Recent Changes (April 2026)

### Custom Chord Input
- Users can type any chord name from the database as a 6th option alongside AI recommendations
- Automatic flat→sharp conversion (Db→Cs, Eb→Ds, etc.) and quality alias normalization
- Lookup validates against the chord vocabulary before allowing selection

### Expanded Initial Options
- First chord selection now shows up to **50 candidates** (was 5), giving more key variety
- Fallback chord list expanded from 9 to 33 chords covering all 12 roots

### Musicality Parameter
- Adjustable slider (0.0–1.0) controlling the trade-off between major/minor triads and complex chords
- Higher values penalize basic triads and boost extended chords (7ths, 9ths, dim, aug, sus)
- Session-persisted — musicality setting is saved and restored when resuming a session

### Bug Fix: Multi-Word Genre Search
- Style queries with multi-word genre tags (e.g., "cool jazz", "alternative metal") now match correctly via n-gram tokenization
