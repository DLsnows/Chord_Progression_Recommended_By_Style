"""REST API routes for the chord recommendation system."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .schemas import (
    ChordCandidate,
    ChordDetail,
    ChordSelectionItem,
    CreateBranchRequest,
    CreateBranchResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    RenameBranchRequest,
    SelectChordRequest,
    SelectChordResponse,
    SessionListResponse,
    SessionState,
    SessionSummary,
    StyleMatch,
    StyleSearchRequest,
    StyleSearchResponse,
    UndoChordResponse,
)

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def _get_matcher(request: Request):
    return request.app.state.matcher


def _get_recommender(request: Request):
    return request.app.state.recommender


def _get_sessions(request: Request):
    return request.app.state.session_manager


def _get_chord_map(request: Request):
    return request.app.state.chord_map


def _get_chord_vocab(request: Request):
    return request.app.state.chord_vocab


def _get_chord_to_idx(request: Request):
    return request.app.state.chord_to_idx


# ---------------------------------------------------------------------------
# Style search
# ---------------------------------------------------------------------------

@router.post("/styles/search", response_model=StyleSearchResponse)
def search_styles(body: StyleSearchRequest, request: Request) -> dict[str, Any]:
    matcher = _get_matcher(request)
    results = matcher.search(body.query)
    return {
        "query": body.query,
        "results": [StyleMatch(**r) for r in results],
    }


@router.get("/styles")
def list_styles(request: Request) -> dict[str, Any]:
    """List available dimensions: genre tags, decades, sections."""
    matcher = _get_matcher(request)
    return {
        "genre_tags": sorted(matcher.all_sub_tags),
        "main_genres": sorted(matcher.all_main_genres),
        "decades": sorted(matcher.all_decades),
        "sections": sorted(matcher.all_sections),
    }


# ---------------------------------------------------------------------------
# Chord detail
# ---------------------------------------------------------------------------

@router.get("/chords/{name}", response_model=ChordDetail)
def get_chord(name: str, request: Request) -> dict[str, Any]:
    chord_map = _get_chord_map(request)
    info = chord_map.get(name)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Chord not found: {name}")
    return {
        "name": info.name,
        "root_pc": info.root_pc,
        "root_name": info.root_name,
        "quality": info.quality,
        "semitone_intervals": info.semitone_intervals,
        "binary_vector": info.binary_vector,
        "midi_notes_c3": info.to_midi_notes(3),
        "midi_notes_c4": info.to_midi_notes(4),
        "midi_notes_c5": info.to_midi_notes(5),
    }


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
def create_session(body: CreateSessionRequest, request: Request) -> dict[str, Any]:
    sessions = _get_sessions(request)
    recommender = _get_recommender(request)
    chord_map = _get_chord_map(request)
    chord_vocab = _get_chord_vocab(request)

    # Look up style group from matcher's index
    matcher = _get_matcher(request)
    style_group = matcher.style_index.get(body.style_key)
    if style_group is None:
        raise HTTPException(status_code=404, detail=f"Style not found: {body.style_key}")

    session = sessions.create_session(style_group)

    # Cold-start recommendations
    active_branch = _get_active_branch(session)
    selected_indices = [s["chord_idx"] for s in active_branch.get("chords", [])]
    candidates = recommender.recommend(style_group, selected_indices)

    return {
        "session": _build_session_state(session),
        "candidates": _build_candidates(candidates, chord_map),
    }


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    request: Request, limit: int = 20, offset: int = 0
) -> dict[str, Any]:
    sessions = _get_sessions(request)
    rows = sessions.list_sessions(limit, offset)
    summaries: list[dict[str, Any]] = []
    for r in rows:
        # Count chords in active branch
        full = sessions.get_session(r["id"])
        active_branch = None
        for br in full["branches"]:
            if br["id"] == full["active_branch_id"]:
                active_branch = br
                break
        summaries.append({
            "id": r["id"],
            "style_genre_tag": r["style_genre_tag"],
            "style_decade": r["style_decade"],
            "style_section": r["style_section"],
            "chord_count": len(active_branch["chords"]) if active_branch else 0,
            "branch_count": len(full["branches"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return {"sessions": [SessionSummary(**s) for s in summaries]}


@router.get("/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str, request: Request) -> dict[str, Any]:
    sessions = _get_sessions(request)
    try:
        return _build_session_state(sessions.get_session(session_id))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, request: Request) -> None:
    sessions = _get_sessions(request)
    if not sessions.delete_session(session_id):
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")


# ---------------------------------------------------------------------------
# Chord selection within a session
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/select", response_model=SelectChordResponse)
def select_chord(
    session_id: str, body: SelectChordRequest, request: Request
) -> dict[str, Any]:
    sessions = _get_sessions(request)
    recommender = _get_recommender(request)
    matcher = _get_matcher(request)
    chord_map = _get_chord_map(request)

    try:
        session = sessions.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    branch_id = body.branch_id or session["active_branch_id"]
    active_branch = _find_branch(session, branch_id)
    if active_branch is None:
        raise HTTPException(status_code=404, detail=f"Branch not found: {branch_id}")

    # Get style group for this session
    style_key = f"{session['style_genre_tag']}|{session['style_decade']}|{session['style_section']}"
    style_group = matcher.style_index.get(style_key)
    if style_group is None:
        raise HTTPException(status_code=404, detail="Style group no longer available")

    # Get current selected indices
    selected_indices = [s["chord_idx"] for s in active_branch["chords"]]

    # Generate this round's candidates (same as what will be shown)
    current_candidates = recommender.recommend(style_group, selected_indices)

    # Record the selection
    session["style_starting_probs"] = style_group.get("starting_probs", {})
    result = sessions.select_chord(
        session_id, branch_id, body.chord_idx, body.chord_name, current_candidates
    )

    # Generate next round's candidates
    next_indices = selected_indices + [body.chord_idx]
    next_candidates = recommender.recommend(style_group, next_indices)

    return {
        "position": int(result["position"]),
        "chord_name": result["chord_name"],
        "chord_idx": int(result["chord_idx"]),
        "candidates": _build_candidates(next_candidates, chord_map),
        "total_selected": len(next_indices),
    }


@router.post("/sessions/{session_id}/undo", response_model=UndoChordResponse)
def undo_chord(session_id: str, request: Request) -> dict[str, Any]:
    sessions = _get_sessions(request)
    recommender = _get_recommender(request)
    matcher = _get_matcher(request)
    chord_map = _get_chord_map(request)

    try:
        session = sessions.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    branch_id = session["active_branch_id"]
    active_branch = _find_branch(session, branch_id)
    if active_branch is None:
        raise HTTPException(status_code=404, detail="No active branch")

    undone = sessions.undo_chord(session_id, branch_id)

    # Re-rank candidates for the new position
    style_key = f"{session['style_genre_tag']}|{session['style_decade']}|{session['style_section']}"
    style_group = matcher.style_index.get(style_key)
    if style_group is None:
        raise HTTPException(status_code=404, detail="Style group no longer available")

    # Refresh session after undo
    session = sessions.get_session(session_id)
    active_branch = _find_branch(session, branch_id)
    selected_indices = [s["chord_idx"] for s in active_branch["chords"]] if active_branch else []
    candidates = recommender.recommend(style_group, selected_indices)

    undone_resp = None
    if undone:
        undone_resp = SelectChordResponse(
            position=undone["position"],
            chord_name=undone["chord_name"],
            chord_idx=undone["chord_idx"],
            candidates=[],  # candidates that were shown are gone
            total_selected=len(selected_indices),
        )

    return {
        "undone": undone_resp,
        "candidates": _build_candidates(candidates, chord_map),
    }


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/branches",
    response_model=CreateBranchResponse,
    status_code=201,
)
def create_branch(
    session_id: str, body: CreateBranchRequest, request: Request
) -> dict[str, Any]:
    sessions = _get_sessions(request)
    try:
        session = sessions.create_branch(session_id, body.fork_position, body.label)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"session": _build_session_state(session)}


@router.get("/sessions/{session_id}/branches")
def list_branches(session_id: str, request: Request) -> list[dict[str, Any]]:
    sessions = _get_sessions(request)
    try:
        session = sessions.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return [
        {
            "id": br["id"],
            "label": br["label"],
            "fork_position": br["fork_position"],
            "parent_branch_id": br.get("parent_branch_id"),
            "chord_count": len(br.get("chords", [])),
            "created_at": br["created_at"],
        }
        for br in session["branches"]
    ]


@router.put("/sessions/{session_id}/branches/{branch_id}")
def switch_branch(session_id: str, branch_id: str, request: Request) -> dict[str, Any]:
    sessions = _get_sessions(request)
    try:
        session = sessions.switch_branch(session_id, branch_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"session": _build_session_state(session)}


@router.patch("/sessions/{session_id}/branches/{branch_id}")
def rename_branch(
    session_id: str, branch_id: str, body: RenameBranchRequest, request: Request
) -> dict[str, Any]:
    sessions = _get_sessions(request)
    try:
        session = sessions.rename_branch(session_id, branch_id, body.label)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"session": _build_session_state(session)}


@router.delete(
    "/sessions/{session_id}/branches/{branch_id}", status_code=200
)
def delete_branch(session_id: str, branch_id: str, request: Request) -> dict[str, Any]:
    sessions = _get_sessions(request)
    try:
        session = sessions.delete_branch(session_id, branch_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"session": _build_session_state(session)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_branch(session: dict, branch_id: str) -> dict | None:
    for br in session.get("branches", []):
        if br["id"] == branch_id:
            return br
    return None


def _get_active_branch(session: dict) -> dict | None:
    return _find_branch(session, session.get("active_branch_id", ""))


def _build_session_state(session: dict) -> dict[str, Any]:
    return {
        "id": session["id"],
        "style_genre_tag": session["style_genre_tag"],
        "style_decade": session["style_decade"],
        "style_section": session["style_section"],
        "active_branch_id": session["active_branch_id"],
        "branches": [
            {
                "id": br["id"],
                "label": br["label"],
                "fork_position": br["fork_position"],
                "parent_branch_id": br.get("parent_branch_id"),
                "created_at": br["created_at"],
                "chords": [
                    ChordSelectionItem(**c) for c in br.get("chords", [])
                ],
            }
            for br in session.get("branches", [])
        ],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
    }


def _build_candidates(
    candidates: list[dict[str, Any]], chord_map: dict
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in candidates:
        info = c.get("chord_info") or chord_map.get(c["chord_name"])
        if info is None:
            continue
        result.append({
            "chord_idx": c["chord_idx"],
            "chord_name": c["chord_name"],
            "score": c["score"],
            "root_pc": info.root_pc,
            "quality": info.quality,
            "semitone_intervals": info.semitone_intervals,
            "midi_notes": info.to_midi_notes(4),
            "binary_vector": info.binary_vector,
        })
    return [ChordCandidate(**r) for r in result]
