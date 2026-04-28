"""Pydantic request/response models for the recommendation API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class StyleSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, examples=["jazz ballad 1960s verse"])


class CreateSessionRequest(BaseModel):
    style_key: str = Field(
        ..., description="Style group key from style_index (e.g. 'ballad|1960|verse')"
    )
    musicality: float = Field(0.0, ge=0.0, le=1.0, description="Musicality bias: 0=normal, 1=prefer complex chords")


class SelectChordRequest(BaseModel):
    chord_idx: int = Field(..., ge=0)
    chord_name: str = Field(..., min_length=1)
    branch_id: str | None = Field(
        None, description="Branch to select into; uses active branch if omitted"
    )


class CreateBranchRequest(BaseModel):
    fork_position: int = Field(..., ge=0, description="Fork after this many chords selected")
    label: str = Field("", max_length=100)


class RenameBranchRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Response models — chord candidates
# ---------------------------------------------------------------------------

class MidiNoteInfo(BaseModel):
    note_name: str
    midi_number: int
    octave: int


class ChordCandidate(BaseModel):
    chord_idx: int
    chord_name: str
    score: float
    root_pc: int
    quality: str
    semitone_intervals: list[int]
    midi_notes: list[int]
    binary_vector: list[int]

    model_config = {"json_schema_extra": {
        "example": {
            "chord_idx": 310,
            "chord_name": "Amin7",
            "score": 0.8532,
            "root_pc": 9,
            "quality": "min7",
            "semitone_intervals": [0, 3, 7, 10],
            "midi_notes": [57, 60, 64, 67],
            "binary_vector": [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
        }
    }}


# ---------------------------------------------------------------------------
# Response models — styles
# ---------------------------------------------------------------------------

class StyleMatch(BaseModel):
    key: str
    genre_tag: str
    decade: int
    section: str
    score: float
    sample_count: int
    total_bigrams: int


class StyleSearchResponse(BaseModel):
    query: str
    results: list[StyleMatch]


# ---------------------------------------------------------------------------
# Response models — sessions
# ---------------------------------------------------------------------------

class ChordSelectionItem(BaseModel):
    position: int
    chord_name: str
    chord_idx: int
    candidates: list[dict[str, Any]]  # snapshot of the candidates shown
    selected_at: str


class BranchInfo(BaseModel):
    id: str
    label: str
    fork_position: int
    parent_branch_id: str | None
    created_at: str
    chords: list[ChordSelectionItem]


class SessionState(BaseModel):
    id: str
    style_genre_tag: str
    style_decade: int
    style_section: str
    active_branch_id: str
    musicality: float
    branches: list[BranchInfo]
    created_at: str
    updated_at: str


class SessionSummary(BaseModel):
    id: str
    style_genre_tag: str
    style_decade: int
    style_section: str
    chord_count: int
    branch_count: int
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]


# ---------------------------------------------------------------------------
# Response models — chord selection result
# ---------------------------------------------------------------------------

class SelectChordResponse(BaseModel):
    position: int
    chord_name: str
    chord_idx: int
    candidates: list[ChordCandidate]  # next 5 candidates
    total_selected: int


class UndoChordResponse(BaseModel):
    undone: SelectChordResponse | None
    candidates: list[ChordCandidate]  # re-ranked candidates for the new last position


class CreateSessionResponse(BaseModel):
    session: SessionState
    candidates: list[ChordCandidate]


class ResumeSessionResponse(BaseModel):
    session: SessionState
    candidates: list[ChordCandidate]


class CreateBranchResponse(BaseModel):
    session: SessionState
    candidates: list[ChordCandidate] = []


# ---------------------------------------------------------------------------
# Response models — chord detail
# ---------------------------------------------------------------------------

class ChordDetail(BaseModel):
    chord_idx: int
    name: str
    root_pc: int
    root_name: str
    quality: str
    semitone_intervals: list[int]
    binary_vector: list[int]
    midi_notes_c3: list[int]
    midi_notes_c4: list[int]
    midi_notes_c5: list[int]


# ---------------------------------------------------------------------------
# Musicality
# ---------------------------------------------------------------------------

class UpdateMusicalityRequest(BaseModel):
    musicality: float = Field(..., ge=0.0, le=1.0)


class UpdateMusicalityResponse(BaseModel):
    session: SessionState
    candidates: list[ChordCandidate]
