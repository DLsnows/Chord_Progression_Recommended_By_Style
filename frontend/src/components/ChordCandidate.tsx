/** Single chord candidate card with piano roll thumbnail. */

import PianoRoll from './PianoRoll';
import type { ChordCandidate as ChordCandidateType } from '../types';

interface ChordCandidateProps {
  candidate: ChordCandidateType;
  onSelect: (candidate: ChordCandidateType) => void;
}

function ChordCandidate({ candidate, onSelect }: ChordCandidateProps) {
  const rootMidi = candidate.root_pc + 48; // C3 = MIDI 48

  return (
    <button
      onClick={() => onSelect(candidate)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        width: '100%',
        padding: '10px 14px',
        border: '1px solid #333',
        borderRadius: '8px',
        background: '#16213e',
        color: '#e0e0e0',
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      <div style={{ minWidth: '120px' }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#e94560' }}>
          {candidate.chord_name}
        </div>
        <div style={{ fontSize: '0.8rem', color: '#999', marginTop: 2 }}>
          {candidate.quality} | score: {candidate.score.toFixed(4)}
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <PianoRoll
          activeNotes={candidate.midi_notes}
          rootNote={rootMidi}
          scale={0.4}
        />
      </div>
    </button>
  );
}

export default ChordCandidate;
