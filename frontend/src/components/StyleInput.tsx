/** Style search input with match results display. */

import { useState } from 'react';
import type { StyleMatch } from '../types';

interface StyleInputProps {
  matches: StyleMatch[];
  isLoading: boolean;
  error: string | null;
  onSubmit: (query: string) => void;
  onSelectMatch: (match: StyleMatch) => void;
}

function StyleInput({ matches, isLoading, error, onSubmit, onSelectMatch }: StyleInputProps) {
  const [query, setQuery] = useState('');

  function handleSubmit() {
    const trimmed = query.trim();
    if (trimmed) {
      onSubmit(trimmed);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
          placeholder="e.g. jazz ballad 1960s verse"
          style={{
            flex: 1,
            padding: '10px 14px',
            border: '1px solid #333',
            borderRadius: '6px',
            background: '#16213e',
            color: '#e0e0e0',
            fontSize: '1rem',
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={isLoading || !query.trim()}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: '6px',
            background: '#e94560',
            color: '#fff',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontWeight: 600,
          }}
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div style={{ color: '#e94560', fontSize: '0.9rem' }}>{error}</div>
      )}

      {matches.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <p style={{ color: '#999', fontSize: '0.9rem', margin: 0 }}>
            Select a style to start:
          </p>
          {matches.slice(0, 10).map((m) => (
            <button
              key={m.key}
              onClick={() => onSelectMatch(m)}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 14px',
                border: '1px solid #333',
                borderRadius: '6px',
                background: '#16213e',
                color: '#e0e0e0',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span>
                <span style={{ color: '#e94560', fontWeight: 600 }}>
                  {m.genre_tag.replace(/^__main__/, '')}
                </span>
                <span style={{ color: '#999' }}> — {m.section}</span>
              </span>
              <span style={{ color: '#666', fontSize: '0.8rem' }}>
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
