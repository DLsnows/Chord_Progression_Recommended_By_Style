/** Selected chord sequence display with undo/finish controls. */

import PianoRoll from './PianoRoll';
import type { ChordSelectionItem, ChordCandidate } from '../types';

interface SequenceDisplayProps {
  chords: ChordSelectionItem[];
  onUndo: () => void;
  onFinish: () => void;
}

function SequenceDisplay({ chords, onUndo, onFinish }: SequenceDisplayProps) {
  if (chords.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#999', textAlign: 'center' }}>
        Select your first chord to begin the progression.
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <h3 style={{ margin: 0, color: '#e0e0e0', fontSize: '1rem', flex: 1 }}>
          Your Progression ({chords.length} chord{chords.length !== 1 ? 's' : ''})
        </h3>
        <button
          onClick={onUndo}
          disabled={chords.length === 0}
          style={{
            padding: '6px 16px',
            border: '1px solid #555',
            borderRadius: '4px',
            background: '#16213e',
            color: '#e0e0e0',
            cursor: chords.length > 0 ? 'pointer' : 'not-allowed',
          }}
        >
          Undo
        </button>
        <button
          onClick={onFinish}
          style={{
            padding: '6px 16px',
            border: 'none',
            borderRadius: '4px',
            background: '#e94560',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          Finish
        </button>
      </div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {chords.map((item) => {
          // Reconstruct MIDI notes for display from the first candidate that matches
          const chosen = item.candidates?.find(
            (c: ChordCandidate) => c.chord_idx === item.chord_idx
          );
          const midiNotes = chosen?.midi_notes ?? [];
          const rootMidi = chosen ? chosen.root_pc + 48 : undefined;

          return (
            <div
              key={`${item.position}-${item.chord_name}`}
              style={{
                padding: '8px 10px',
                border: '1px solid #333',
                borderRadius: '6px',
                background: '#16213e',
                textAlign: 'center',
                minWidth: '100px',
              }}
            >
              <div style={{ fontWeight: 600, color: '#e94560', marginBottom: 4 }}>
                {item.chord_name}
              </div>
              <PianoRoll activeNotes={midiNotes} rootNote={rootMidi} scale={0.3} />
              <div style={{ fontSize: '0.7rem', color: '#666', marginTop: 4 }}>
                #{item.position}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SequenceDisplay;
