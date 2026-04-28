import { useState } from 'react';
import PianoRoll from './PianoRoll';
import type { ChordCandidate as Candidate } from '../types';
import { audioEngine } from '../utils/audioEngine';
import s from './ChordCandidate.module.css';

interface Props {
  candidate: Candidate;
  onSelect: (candidate: Candidate) => void;
}

function ChordCandidate({ candidate, onSelect }: Props) {
  const [playing, setPlaying] = useState(false);
  const rootMidi = candidate.root_pc + 48;

  async function handlePlay(e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await audioEngine.init();
      setPlaying(true);
      audioEngine.playChord(candidate.midi_notes);
      setTimeout(() => setPlaying(false), 700);
    } catch {
      setPlaying(false);
    }
  }

  return (
    <button className={s.card} onClick={() => onSelect(candidate)}>
      <div className={s.info}>
        <div className={s.chordName}>{candidate.chord_name}</div>
        <div className={s.quality}>{candidate.quality} | score: {candidate.score.toFixed(4)}</div>
      </div>
      <div className={s.pianoWrap}>
        <PianoRoll activeNotes={candidate.midi_notes} rootNote={rootMidi} scale={0.4} />
      </div>
      <span
        className={`${s.playBtn} ${playing ? s.playBtnActive : ''}`}
        onClick={handlePlay}
        role="button"
        tabIndex={0}
        title="Preview chord"
      >
        {playing ? '■' : '♪'}
      </span>
    </button>
  );
}

export default ChordCandidate;
