/** Branch navigation — tabs for viewing/creating/switching branches. */

import { useState } from 'react';
import type { BranchInfo, ChordSelectionItem } from '../types';

interface BranchNavProps {
  branches: BranchInfo[];
  activeBranchId: string | null;
  chords: ChordSelectionItem[];
  onCreateBranch: (forkPosition: number, label: string) => void;
  onSwitchBranch: (branchId: string) => void;
  onRenameBranch: (branchId: string, label: string) => void;
  onDeleteBranch: (branchId: string) => void;
}

function BranchNav({
  branches,
  activeBranchId,
  chords,
  onCreateBranch,
  onSwitchBranch,
  onRenameBranch,
  onDeleteBranch,
}: BranchNavProps) {
  const [forkAt, setForkAt] = useState<number>(0);
  const [newLabel, setNewLabel] = useState('');
  const [showFork, setShowFork] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState('');

  if (branches.length === 0) return null;

  function handleFork() {
    if (newLabel.trim()) {
      onCreateBranch(forkAt, newLabel.trim());
      setNewLabel('');
      setShowFork(false);
    }
  }

  function handleRename(branchId: string) {
    if (editLabel.trim()) {
      onRenameBranch(branchId, editLabel.trim());
      setEditingId(null);
      setEditLabel('');
    }
  }

  return (
    <div style={{ marginBottom: '1rem' }}>
      {/* Branch tabs */}
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
        {branches.map((b) => {
          const isActive = b.id === activeBranchId;
          return (
            <div
              key={b.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                border: `2px solid ${isActive ? '#e94560' : '#333'}`,
                borderRadius: '6px',
                background: isActive ? '#16213e' : '#1a1a2e',
                cursor: isActive ? 'default' : 'pointer',
              }}
              onClick={() => { if (!isActive) onSwitchBranch(b.id); }}
            >
              {editingId === b.id ? (
                <input
                  value={editLabel}
                  onChange={(e) => setEditLabel(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleRename(b.id); }}
                  onBlur={() => handleRename(b.id)}
                  autoFocus
                  style={{ width: '80px', fontSize: '0.8rem', background: '#16213e', color: '#e0e0e0', border: '1px solid #555' }}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span style={{ fontSize: '0.85rem', color: isActive ? '#e94560' : '#ccc' }}>
                  {b.label || `Branch ${b.id.slice(0, 6)}`}
                </span>
              )}
              <span style={{ fontSize: '0.7rem', color: '#666' }}>
                ({b.chords?.length ?? 0})
              </span>
              {!editingId && (
                <>
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditingId(b.id); setEditLabel(b.label); }}
                    title="Rename"
                    style={{ background: 'none', border: 'none', color: '#999', cursor: 'pointer', fontSize: '0.7rem', padding: 0 }}
                  >
                    ✏
                  </button>
                  {branches.length > 1 && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDeleteBranch(b.id); }}
                      title="Delete"
                      style={{ background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: '0.7rem', padding: 0 }}
                    >
                      ✕
                    </button>
                  )}
                </>
              )}
            </div>
          );
        })}

        {/* Fork button */}
        <button
          onClick={() => setShowFork(!showFork)}
          style={{
            padding: '4px 10px',
            border: '1px dashed #555',
            borderRadius: '6px',
            background: 'transparent',
            color: '#999',
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          + Fork
        </button>
      </div>

      {/* Fork form */}
      {showFork && (
        <div style={{ marginTop: '8px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <label style={{ color: '#999', fontSize: '0.85rem' }}>Fork after chord #</label>
          <select
            value={forkAt}
            onChange={(e) => setForkAt(Number(e.target.value))}
            style={{ background: '#16213e', color: '#e0e0e0', border: '1px solid #333', borderRadius: '4px', padding: '3px 8px' }}
          >
            <option value={0}>0 (start over)</option>
            {chords.map((c) => (
              <option key={c.position} value={c.position}>
                {c.position} ({c.chord_name})
              </option>
            ))}
          </select>
          <input
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="Branch label"
            onKeyDown={(e) => { if (e.key === 'Enter') handleFork(); }}
            style={{ background: '#16213e', color: '#e0e0e0', border: '1px solid #333', borderRadius: '4px', padding: '3px 8px', fontSize: '0.85rem' }}
          />
          <button
            onClick={handleFork}
            disabled={!newLabel.trim()}
            style={{
              padding: '3px 12px',
              border: 'none',
              borderRadius: '4px',
              background: '#e94560',
              color: '#fff',
              cursor: newLabel.trim() ? 'pointer' : 'not-allowed',
              fontSize: '0.85rem',
            }}
          >
            Create
          </button>
        </div>
      )}
    </div>
  );
}

export default BranchNav;
