"""FastAPI application entry point for the chord recommendation system."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import SESSION_DB_PATH, DATA_DIR, TRANSITIONS_DIR
from .data.loader import load_chord_vocabulary, download_chord_mapping
from .data.transitions import load_style_index
from .engine import StyleMatcher, Recommender, SessionManager


# ---------------------------------------------------------------------------
# Global state (set during lifespan)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data and initialize engines on startup."""
    print("=" * 50)
    print("Initializing chord recommendation system...")

    # 1. Load chord vocabulary
    csv_path = download_chord_mapping()
    chord_map, chord_vocab = load_chord_vocabulary(csv_path)
    chord_to_idx = {name: i for i, name in enumerate(chord_vocab)}
    print(f"  Chord vocabulary: {len(chord_vocab)} chords")

    # 2. Load style index
    try:
        style_index = load_style_index()
        print(f"  Style index: {len(style_index)} groups")
    except FileNotFoundError:
        print("  WARNING: style_index.json not found. Run build_matrices.py first.")
        style_index = {}

    # 3. Initialize engines
    matcher = StyleMatcher(style_index)
    recommender = Recommender(chord_vocab, chord_map, TRANSITIONS_DIR)
    session_manager = SessionManager(SESSION_DB_PATH)
    print("  Engines initialized")

    # Attach to app state
    app.state.chord_map = chord_map
    app.state.chord_vocab = chord_vocab
    app.state.chord_to_idx = chord_to_idx
    app.state.style_index = style_index
    app.state.matcher = matcher
    app.state.recommender = recommender
    app.state.session_manager = session_manager

    print("=" * 50)
    print("Ready. Visit http://localhost:8000 to open the app")

    yield  # app runs here

    # Shutdown (nothing to clean up)
    print("Shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Chord Progression Recommendation API",
        description="Style-aware chord progression recommendations with session persistence and branching.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Serve frontend static files in production (when dist/ exists)
    _serve_frontend(app)

    return app


def _serve_frontend(app: FastAPI) -> None:
    """Mount frontend static files if the dist directory exists."""
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if not frontend_dist.exists():
        return

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        path = frontend_dist / "favicon.svg"
        return FileResponse(path) if path.exists() else FileResponse(frontend_dist / "index.html")


app = create_app()


# ---------------------------------------------------------------------------
# Direct runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
