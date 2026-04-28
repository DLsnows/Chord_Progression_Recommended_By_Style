import { useState } from 'react';
import type { StyleMatch } from '../types';
import s from './StyleInput.module.css';

interface Props {
  matches: StyleMatch[];
  isLoading: boolean;
  error: string | null;
  onSubmit: (query: string) => void;
  onSelectMatch: (match: StyleMatch) => void;
}

function StyleInput({ matches, isLoading, error, onSubmit, onSelectMatch }: Props) {
  const [query, setQuery] = useState('');

  function handleSubmit() {
    const trimmed = query.trim();
    if (trimmed) onSubmit(trimmed);
  }

  return (
    <div className={s.wrapper}>
      <div className={s.searchRow}>
        <input
          type="text"
          className={s.input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
          placeholder="e.g. jazz ballad 1960s verse"
        />
        <button
          className={s.searchBtn}
          onClick={handleSubmit}
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className={s.error}>{error}</div>}

      {!isLoading && !error && query.trim() && matches.length === 0 && (
        <div className={s.empty}>No matching styles found. Try a different query.</div>
      )}

      {matches.length > 0 && (
        <div className={s.results}>
          <p className={s.resultsLabel}>Select a style to start:</p>
          {matches.slice(0, 10).map((m) => (
            <button key={m.key} className={s.matchBtn} onClick={() => onSelectMatch(m)}>
              <span>
                <span className={s.matchTag}>{m.genre_tag.replace(/^__main__/, '')}</span>
                <span className={s.matchSection}> — {m.section}</span>
              </span>
              <span className={s.matchMeta}>
                {m.decade}s | {m.sample_count} samples | score: {m.score.toFixed(3)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default StyleInput;
