import { useState, useEffect } from 'react';
import type { SessionSummary } from '../types';
import * as api from '../api/client';
import s from './SessionHistory.module.css';

interface Props {
  onResume: (sessionId: string) => void;
  onBack: () => void;
}

function SessionHistory({ onResume, onBack }: Props) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchSessions() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.listSessions();
      setSessions(result.sessions);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSessions();
  }, []);

  async function handleDelete(sessionId: string) {
    if (!window.confirm('Delete this session?')) return;
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
  }

  const genreLabel = (tag: string) => tag.replace(/^__main__/, '');

  return (
    <div className={s.wrapper}>
      <div className={s.headerRow}>
        <h2 className={s.title}>Session History</h2>
        <button className={s.backBtn} onClick={onBack}>Back to Search</button>
      </div>

      {error && <div className={s.error}>{error}</div>}

      {loading && <div className={s.empty}>Loading...</div>}

      {!loading && !error && sessions.length === 0 && (
        <div className={s.empty}>No past sessions. Start a new search to create one.</div>
      )}

      {sessions.map((sess) => (
        <div key={sess.id} className={s.card}>
          <div className={s.cardBody}>
            <div className={s.cardHeader}>
              <span className={s.genreLabel}>{genreLabel(sess.style_genre_tag)}</span>
              <span className={s.cardMeta}>
                {sess.style_decade}s &middot; {sess.style_section}
              </span>
            </div>
            <div className={s.cardDetails}>
              {sess.chord_count} chord{sess.chord_count !== 1 ? 's' : ''} &middot;{' '}
              {sess.branch_count} branch{sess.branch_count !== 1 ? 'es' : ''} &middot;{' '}
              {formatDate(sess.updated_at)}
            </div>
          </div>
          <div className={s.cardActions}>
            <button className={s.resumeBtn} onClick={() => onResume(sess.id)}>
              Resume
            </button>
            <button className={s.deleteBtn} onClick={() => handleDelete(sess.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default SessionHistory;
