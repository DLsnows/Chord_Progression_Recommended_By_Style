// ---------------------------------------------------------------------------
// Chord data
// ---------------------------------------------------------------------------

export interface ChordCandidate {
  chord_idx: number;
  chord_name: string;
  score: number;
  root_pc: number;
  quality: string;
  semitone_intervals: number[];
  midi_notes: number[];
  binary_vector: number[];
}

export interface ChordDetail {
  name: string;
  root_pc: number;
  root_name: string;
  quality: string;
  semitone_intervals: number[];
  binary_vector: number[];
  midi_notes_c3: number[];
  midi_notes_c4: number[];
  midi_notes_c5: number[];
}

// ---------------------------------------------------------------------------
// Style search
// ---------------------------------------------------------------------------

export interface StyleMatch {
  key: string;
  genre_tag: string;
  decade: number;
  section: string;
  score: number;
  sample_count: number;
  total_bigrams: number;
}

export interface StyleSearchResponse {
  query: string;
  results: StyleMatch[];
}

export interface StyleListResponse {
  genre_tags: string[];
  main_genres: string[];
  decades: number[];
  sections: string[];
}

// ---------------------------------------------------------------------------
// Session & branches
// ---------------------------------------------------------------------------

export interface ChordSelectionItem {
  position: number;
  chord_name: string;
  chord_idx: number;
  candidates: ChordCandidate[];
  selected_at: string;
}

export interface BranchInfo {
  id: string;
  label: string;
  fork_position: number;
  parent_branch_id: string | null;
  created_at: string;
  chords: ChordSelectionItem[];
}

export interface SessionState {
  id: string;
  style_genre_tag: string;
  style_decade: number;
  style_section: string;
  active_branch_id: string;
  branches: BranchInfo[];
  created_at: string;
  updated_at: string;
}

export interface SessionSummary {
  id: string;
  style_genre_tag: string;
  style_decade: number;
  style_section: string;
  chord_count: number;
  branch_count: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// API request/response pairs
// ---------------------------------------------------------------------------

export interface CreateSessionRequest {
  style_key: string;
}

export interface CreateSessionResponse {
  session: SessionState;
  candidates: ChordCandidate[];
}

export interface SelectChordRequest {
  chord_idx: number;
  chord_name: string;
  branch_id?: string;
}

export interface SelectChordResponse {
  position: number;
  chord_name: string;
  chord_idx: number;
  candidates: ChordCandidate[];
  total_selected: number;
}

export interface UndoChordResponse {
  undone: {
    position: number;
    chord_name: string;
    chord_idx: number;
  } | null;
  candidates: ChordCandidate[];
}

export interface CreateBranchRequest {
  fork_position: number;
  label: string;
}

export interface RenameBranchRequest {
  label: string;
}

export interface BranchActionResponse {
  session: SessionState;
}

// ---------------------------------------------------------------------------
// UI state
// ---------------------------------------------------------------------------

export type AppPhase = 'IDLE' | 'MATCHING' | 'RECOMMENDING' | 'DONE';

export interface UIState {
  phase: AppPhase;
  matches: StyleMatch[];
  candidates: ChordCandidate[];
  session: SessionState | null;
  isLoading: boolean;
  error: string | null;
}
