import { useState, useCallback } from 'react';
import PianoRoll from './PianoRoll';
import type { ChordSelectionItem, ChordCandidate } from '../types';
import { audioEngine } from '../utils/audioEngine';
import s from './SequenceDisplay.module.css';

interface Props {
  chords: ChordSelectionItem[];
  onUndo: () => void;
  onFinish: () => void;
  readonly?: boolean;
}

function SequenceDisplay({ chords, onUndo, onFinish, readonly = false }: Props) {
  const [playingAll, setPlayingAll] = useState(false);
  const [soloIdx, setSoloIdx] = useState<number | null>(null);

  const chordNotes: number[][] = chords.map((item) => {
    const chosen = item.candidates?.find(
      (c: ChordCandidate) => c.chord_idx === item.chord_idx
    );
    return chosen?.midi_notes ?? [];
  });

  const handlePlayAll = useCallback(async () => {
    if (playingAll) {
      audioEngine.stop();
      audioEngine.onEnd = null;
      setPlayingAll(false);
      return;
    }
    await audioEngine.init();
    setPlayingAll(true);
    audioEngine.onEnd = () => setPlayingAll(false);
    audioEngine.playProgression(chordNotes);
  }, [playingAll, chordNotes]);

  async function handleSolo(midiNotes: number[], idx: number) {
    await audioEngine.init();
    setSoloIdx(idx);
    audioEngine.playChord(midiNotes);
    setTimeout(() => setSoloIdx(null), 700);
  }

  if (chords.length === 0) {
    return <div className={s.empty}>Select your first chord to begin.</div>;
  }

  return (
    <div className={s.wrapper}>
      <div className={s.header}>
        <h3 className={s.heading}>
          Your Progression ({chords.length} chord{chords.length !== 1 ? 's' : ''})
        </h3>
        <button className={playingAll ? s.playAllBtnActive : s.playAllBtn} onClick={handlePlayAll}>
          {playingAll ? '■ Stop' : '♪ Play All'}
        </button>
        {!readonly && (
          <>
            <button className={s.undoBtn} onClick={onUndo} disabled={chords.length === 0}>
              Undo
            </button>
            <button className={s.finishBtn} onClick={onFinish}>
              Finish
            </button>
          </>
        )}
      </div>
      <div className={s.chordList}>
        {chords.map((item, idx) => {
          const chosen = item.candidates?.find(
            (c: ChordCandidate) => c.chord_idx === item.chord_idx
          );
          const midiNotes = chosen?.midi_notes ?? [];
          const rootMidi = chosen ? chosen.root_pc + 48 : undefined;

          return (
            <div key={`${item.position}-${item.chord_name}`} className={s.chordChip}>
              <div className={s.chipName}>{item.chord_name}</div>
              <PianoRoll activeNotes={midiNotes} rootNote={rootMidi} scale={0.3} />
              <div className={s.chipPos}>#{item.position}</div>
              <span
                className={`${s.chipPlayBtn} ${soloIdx === idx ? s.chipPlayBtnActive : ''}`}
                onClick={(e) => { e.stopPropagation(); handleSolo(midiNotes, idx); }}
                role="button"
                tabIndex={0}
                title="Play chord"
              >
                {soloIdx === idx ? '■' : '♪'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SequenceDisplay;
