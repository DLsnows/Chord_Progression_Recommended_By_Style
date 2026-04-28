import type { ChordCandidate as Candidate } from '../types';
import ChordCandidate from './ChordCandidate';
import s from './ChordSelector.module.css';

interface Props {
  candidates: Candidate[];
  isLoading: boolean;
  error: string | null;
  onSelect: (candidate: Candidate) => void;
}

function ChordSelector({ candidates, isLoading, error, onSelect }: Props) {
  if (error) {
    return <div className={s.stateError}><p>Error: {error}</p></div>;
  }

  if (isLoading) {
    return <div className={s.stateMuted}><p>Generating recommendations...</p></div>;
  }

  if (!candidates || candidates.length === 0) {
    return <div className={s.stateMuted}><p>No candidates available.</p></div>;
  }

  return (
    <div className={s.container}>
      <h3 className={s.heading}>Choose the next chord</h3>
      {candidates.map((c) => (
        <ChordCandidate key={c.chord_idx} candidate={c} onSelect={onSelect} />
      ))}
    </div>
  );
}

export default ChordSelector;
