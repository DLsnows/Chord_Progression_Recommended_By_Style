/** State machine hook: orchestrates the recommendation UI flow with API calls. */

import { useState, useCallback } from 'react';
import type {
  StyleMatch,
  ChordCandidate,
  ChordSelectionItem,
  SessionState,
  AppPhase,
  UIState,
} from '../types';
import * as api from '../api/client';

const initialState: UIState = {
  phase: 'IDLE' as AppPhase,
  matches: [],
  candidates: [],
  session: null,
  musicality: 0,
  isLoading: false,
  error: null,
};

interface Actions {
  submitStyle: (query: string) => Promise<void>;
  startSession: (match: StyleMatch) => Promise<void>;
  selectChord: (candidate: ChordCandidate) => Promise<void>;
  undo: () => Promise<void>;
  finish: () => void;
  restart: () => void;
  loadSession: (sessionId: string) => Promise<void>;
  createBranch: (forkPosition: number, label: string) => Promise<void>;
  switchBranch: (branchId: string) => Promise<void>;
  renameBranch: (branchId: string, label: string) => Promise<void>;
  deleteBranch: (branchId: string) => Promise<void>;
  updateMusicality: (value: number) => Promise<void>;
}

export function useRecommendation(): { state: UIState; actions: Actions } {
  const [state, setState] = useState<UIState>(initialState);

  // ---- helpers ----

  const activeBranch = (s: SessionState | null) =>
    s?.branches?.find((b) => b.id === s.active_branch_id) ?? null;

  // ---- style search ----

  const submitStyle = useCallback(async (query: string) => {
    setState((s) => ({ ...s, phase: 'MATCHING', isLoading: true, error: null, matches: [] }));
    try {
      const result = await api.searchStyles(query);
      setState((s) => ({
        ...s,
        phase: 'MATCHING',
        isLoading: false,
        matches: result.results,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Search failed';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, []);

  // ---- start session ----

  const startSession = useCallback(async (match: StyleMatch) => {
    const { musicality } = state as { musicality: number };
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await api.createSession({ style_key: match.key, musicality });
      setState((s) => ({
        ...s,
        phase: 'RECOMMENDING',
        isLoading: false,
        session: result.session,
        candidates: result.candidates,
        matches: [],
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create session';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, [state]);

  // ---- select chord ----

  const selectChord = useCallback(async (candidate: ChordCandidate) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, isLoading: true, error: null }));

    const branchId = currentSession.active_branch_id;

    // Optimistic update: add chord to local state
    const position = (activeBranch(currentSession)?.chords.length ?? 0) + 1;

    // Ensure the selected chord is in the candidates list so SequenceDisplay
    // can look up its midi_notes for piano roll rendering and playback.
    const candidatesWithSelection = state.candidates.some(
      (c) => c.chord_idx === candidate.chord_idx
    )
      ? state.candidates
      : [...state.candidates, candidate];

    const optimisticSelection: ChordSelectionItem = {
      position,
      chord_name: candidate.chord_name,
      chord_idx: candidate.chord_idx,
      candidates: candidatesWithSelection,
      selected_at: new Date().toISOString(),
    };

    const updatedBranches = currentSession.branches.map((b) =>
      b.id === branchId ? { ...b, chords: [...b.chords, optimisticSelection] } : b
    );

    setState((s) => ({
      ...s,
      session: { ...currentSession, branches: updatedBranches },
      candidates: [],
    }));

    try {
      const result = await api.selectChord(currentSession.id, {
        chord_idx: candidate.chord_idx,
        chord_name: candidate.chord_name,
        branch_id: branchId,
      });

      // Re-fetch session for authoritative state
      const refreshed = await api.getSession(currentSession.id);
      setState((s) => ({
        ...s,
        isLoading: false,
        session: refreshed,
        candidates: result.candidates,
      }));
    } catch (err: unknown) {
      // Rollback optimistic update: re-fetch authoritative session state
      const msg = err instanceof Error ? err.message : 'Selection failed';
      try {
        const refreshed = await api.getSession(currentSession.id);
        setState((s) => ({ ...s, isLoading: false, session: refreshed, error: msg }));
      } catch {
        setState((s) => ({ ...s, isLoading: false, error: msg }));
      }
    }
  }, [state]);

  // ---- undo ----

  const undo = useCallback(async () => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await api.undoChord(currentSession.id);
      const refreshed = await api.getSession(currentSession.id);
      setState((s) => ({
        ...s,
        isLoading: false,
        session: refreshed,
        candidates: result.candidates,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Undo failed';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, [state]);

  // ---- finish ----

  const finish = useCallback(() => {
    setState((s) => ({ ...s, phase: 'DONE' }));
  }, []);

  // ---- restart ----

  const restart = useCallback(() => {
    setState(initialState);
  }, []);

  // ---- load session (history) ----

  const loadSession = useCallback(async (sessionId: string) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await api.resumeSession(sessionId);
      setState((s) => ({
        ...s,
        phase: 'RECOMMENDING',
        isLoading: false,
        session: result.session,
        candidates: result.candidates,
        musicality: result.session.musicality ?? 0,
        matches: [],
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load session';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, []);

  // ---- branch operations ----

  const createBranch = useCallback(async (forkPosition: number, label: string) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await api.createBranch(currentSession.id, {
        fork_position: forkPosition,
        label,
      });
      setState((s) => ({
        ...s,
        isLoading: false,
        session: result.session,
        candidates: result.candidates,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Branch creation failed';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, [state]);

  const switchBranch = useCallback(async (branchId: string) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await api.switchBranch(currentSession.id, branchId);
      setState((s) => ({
        ...s,
        isLoading: false,
        session: result.session,
        candidates: result.candidates,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Branch switch failed';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, [state]);

  const renameBranch = useCallback(async (branchId: string, label: string) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, error: null }));
    try {
      const result = await api.renameBranch(currentSession.id, branchId, label);
      setState((s) => ({ ...s, session: result.session }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Rename failed';
      setState((s) => ({ ...s, error: msg }));
    }
  }, [state]);

  const deleteBranch = useCallback(async (branchId: string) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, error: null }));
    try {
      const result = await api.deleteBranch(currentSession.id, branchId);
      setState((s) => ({ ...s, session: result.session }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Delete branch failed';
      setState((s) => ({ ...s, error: msg }));
    }
  }, [state]);

  const updateMusicality = useCallback(async (value: number) => {
    const { session: currentSession } = state as { session: SessionState | null };
    if (!currentSession) return;

    setState((s) => ({ ...s, musicality: value, isLoading: true, error: null }));
    try {
      const result = await api.updateMusicality(currentSession.id, { musicality: value });
      setState((s) => ({
        ...s,
        isLoading: false,
        session: result.session,
        candidates: result.candidates,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update musicality';
      setState((s) => ({ ...s, isLoading: false, error: msg }));
    }
  }, [state]);

  return {
    state,
    actions: {
      submitStyle,
      startSession,
      selectChord,
      undo,
      finish,
      restart,
      loadSession,
      createBranch,
      switchBranch,
      renameBranch,
      deleteBranch,
      updateMusicality,
    },
  };
}
