/** Displays 5 chord candidates with loading and error states. */

import type { ChordCandidate as ChordCandidateType } from '../types';
import ChordCandidate from './ChordCandidate';

interface ChordSelectorProps {
  candidates: ChordCandidateType[];
  isLoading: boolean;
  error: string | null;
  onSelect: (candidate: ChordCandidateType) => void;
}

function ChordSelector({ candidates, isLoading, error, onSelect }: ChordSelectorProps) {
  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#e94560' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>
        <p>Generating recommendations...</p>
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>
        <p>No candidates available. Select a style to begin.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <h3 style={{ margin: '0 0 8px', color: '#e0e0e0', fontSize: '1rem' }}>
        Choose the next chord
      </h3>
      {candidates.map((c) => (
        <ChordCandidate key={c.chord_idx} candidate={c} onSelect={onSelect} />
      ))}
    </div>
  );
}

export default ChordSelector;
