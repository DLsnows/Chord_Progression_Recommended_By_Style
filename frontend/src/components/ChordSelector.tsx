import { useState } from 'react';
import PianoRoll from './PianoRoll';
import type { ChordCandidate as Candidate } from '../types';
import * as api from '../api/client';
import ChordCandidate from './ChordCandidate';
import { audioEngine } from '../utils/audioEngine';
import s from './ChordSelector.module.css';

interface Props {
  candidates: Candidate[];
  isLoading: boolean;
  error: string | null;
  onSelect: (candidate: Candidate) => void;
}

const FLAT_TO_SHARP: Record<string, string> = {
  Db: 'Cs', Eb: 'Ds', Gb: 'Fs', Ab: 'Gs', Bb: 'As',
};

function normalizeChordInput(raw: string): string {
  let name = raw.trim();
  if (name.length < 1) return name;
  // Capitalize first letter
  name = name.charAt(0).toUpperCase() + name.slice(1);
  // Flat → sharp conversion
  for (const [flat, sharp] of Object.entries(FLAT_TO_SHARP)) {
    if (name.startsWith(flat)) {
      name = sharp + name.slice(flat.length);
      break;
    }
  }
  return name;
}

function ChordSelector({ candidates, isLoading, error, onSelect }: Props) {
  const [customChord, setCustomChord] = useState('');
  const [customError, setCustomError] = useState<string | null>(null);
  const [customValidating, setCustomValidating] = useState(false);
  const [validatedCandidate, setValidatedCandidate] = useState<Candidate | null>(null);
  const [previewPlaying, setPreviewPlaying] = useState(false);

  async function handleCustomSubmit(e: React.FormEvent) {
    e.preventDefault();
    const normalized = normalizeChordInput(customChord);
    if (!normalized) return;

    setCustomValidating(true);
    setCustomError(null);
    setValidatedCandidate(null);

    try {
      const detail = await api.getChord(normalized);
      const candidate: Candidate = {
        chord_idx: detail.chord_idx,
        chord_name: detail.name,
        score: 0, // custom chord has no AI score
        root_pc: detail.root_pc,
        quality: detail.quality,
        semitone_intervals: detail.semitone_intervals,
        midi_notes: detail.root_pc >= 7 ? detail.midi_notes_c3 : detail.midi_notes_c4,
        binary_vector: detail.binary_vector,
      };
      setValidatedCandidate(candidate);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Chord not found';
      setCustomError(msg);
    } finally {
      setCustomValidating(false);
    }
  }

  function handleSelectValidated() {
    if (validatedCandidate) {
      onSelect(validatedCandidate);
      setCustomChord('');
      setValidatedCandidate(null);
      setCustomError(null);
    }
  }

  async function handlePreviewPlay(e: React.MouseEvent) {
    e.stopPropagation();
    if (!validatedCandidate) return;
    try {
      await audioEngine.init();
      setPreviewPlaying(true);
      audioEngine.playChord(validatedCandidate.midi_notes);
      setTimeout(() => setPreviewPlaying(false), 700);
    } catch {
      setPreviewPlaying(false);
    }
  }

  if (error) {
    return <div className={s.stateError}><p>Error: {error}</p></div>;
  }

  if (isLoading) {
    return <div className={s.stateMuted}><p>Generating recommendations...</p></div>;
  }

  return (
    <div className={s.container}>
      <h3 className={s.heading}>Choose the next chord</h3>
      {candidates && candidates.length > 0 ? (
        candidates.map((c) => (
          <ChordCandidate key={c.chord_idx} candidate={c} onSelect={onSelect} />
        ))
      ) : (
        <p className={s.stateMuted}>No candidates available.</p>
      )}

      {/* Custom chord input — 6th option */}
      <div className={s.customDivider}>
        <span>or enter a custom chord</span>
      </div>

      <form className={s.customRow} onSubmit={handleCustomSubmit}>
        <input
          className={s.customInput}
          type="text"
          placeholder="e.g., Cmaj7, Amin, G7, Ddim7"
          value={customChord}
          onChange={(e) => {
            setCustomChord(e.target.value);
            setCustomError(null);
            setValidatedCandidate(null);
          }}
        />
        <button
          className={s.customBtn}
          type="submit"
          disabled={customValidating || !customChord.trim()}
        >
          {customValidating ? '...' : 'Look up'}
        </button>
      </form>

      {customError && <div className={s.customError}>{customError}</div>}

      {validatedCandidate && (
        <div className={s.customResult}>
          <div className={s.customResultInfo}>
            <span className={s.customResultName}>{validatedCandidate.chord_name}</span>
            <span className={s.customResultQuality}>{validatedCandidate.quality}</span>
          </div>
          <div className={s.customResultPiano}>
            <PianoRoll
              activeNotes={validatedCandidate.midi_notes}
              rootNote={validatedCandidate.root_pc + 48}
              scale={0.35}
            />
          </div>
          <span
            className={`${s.customPlayBtn} ${previewPlaying ? s.customPlayBtnActive : ''}`}
            onClick={handlePreviewPlay}
            role="button"
            tabIndex={0}
            title="Preview chord"
          >
            {previewPlaying ? '■' : '♪'}
          </span>
          <button className={s.customSelectBtn} onClick={handleSelectValidated}>
            Select
          </button>
        </div>
      )}

      <div className={s.customHint}>
        Format: Root + Quality. Use sharps (Cs, Fs) not flats.
      </div>
    </div>
  );
}

export default ChordSelector;
