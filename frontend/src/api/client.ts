/** Typed fetch wrapper for the chord recommendation API. */

import type {
  StyleSearchResponse,
  StyleListResponse,
  ChordDetail,
  CreateSessionRequest,
  CreateSessionResponse,
  SelectChordRequest,
  SelectChordResponse,
  UndoChordResponse,
  CreateBranchRequest,
  SessionState,
  SessionSummary,
  BranchActionResponse,
  UpdateMusicalityRequest,
  UpdateMusicalityResponse,
} from '../types';

const BASE_URL = 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail ?? res.statusText);
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as unknown as T;
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

export function searchStyles(query: string): Promise<StyleSearchResponse> {
  return request<StyleSearchResponse>('/styles/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

export function listStyles(): Promise<StyleListResponse> {
  return request<StyleListResponse>('/styles');
}

// ---------------------------------------------------------------------------
// Chords
// ---------------------------------------------------------------------------

export function getChord(name: string): Promise<ChordDetail> {
  return request<ChordDetail>(`/chords/${encodeURIComponent(name)}`);
}

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

export function createSession(body: CreateSessionRequest): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>('/sessions', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function listSessions(limit: number = 20, offset: number = 0): Promise<{ sessions: SessionSummary[] }> {
  return request(`/sessions?limit=${limit}&offset=${offset}`);
}

export function getSession(sessionId: string): Promise<SessionState> {
  return request<SessionState>(`/sessions/${sessionId}`);
}

export function resumeSession(sessionId: string): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>(`/sessions/${sessionId}/resume`, {
    method: 'POST',
  });
}

export function deleteSession(sessionId: string): Promise<void> {
  return request<void>(`/sessions/${sessionId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Chord selection
// ---------------------------------------------------------------------------

export function selectChord(
  sessionId: string,
  body: SelectChordRequest,
): Promise<SelectChordResponse> {
  return request<SelectChordResponse>(`/sessions/${sessionId}/select`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function undoChord(sessionId: string): Promise<UndoChordResponse> {
  return request<UndoChordResponse>(`/sessions/${sessionId}/undo`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// Branches
// ---------------------------------------------------------------------------

export function createBranch(
  sessionId: string,
  body: CreateBranchRequest,
): Promise<BranchActionResponse> {
  return request<BranchActionResponse>(`/sessions/${sessionId}/branches`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function listBranches(sessionId: string): Promise<BranchActionResponse> {
  return request<BranchActionResponse>(`/sessions/${sessionId}/branches`);
}

export function switchBranch(sessionId: string, branchId: string): Promise<BranchActionResponse> {
  return request<BranchActionResponse>(`/sessions/${sessionId}/branches/${branchId}`, {
    method: 'PUT',
  });
}

export function renameBranch(
  sessionId: string,
  branchId: string,
  label: string,
): Promise<BranchActionResponse> {
  return request<BranchActionResponse>(`/sessions/${sessionId}/branches/${branchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ label }),
  });
}

export function deleteBranch(sessionId: string, branchId: string): Promise<BranchActionResponse> {
  return request<BranchActionResponse>(`/sessions/${sessionId}/branches/${branchId}`, {
    method: 'DELETE',
  });
}

// ---------------------------------------------------------------------------
// Musicality
// ---------------------------------------------------------------------------

export function updateMusicality(
  sessionId: string,
  body: UpdateMusicalityRequest,
): Promise<UpdateMusicalityResponse> {
  return request<UpdateMusicalityResponse>(`/sessions/${sessionId}/musicality`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}
