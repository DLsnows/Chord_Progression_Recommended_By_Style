import { useState } from 'react';
import type { BranchInfo, ChordSelectionItem } from '../types';
import s from './BranchNav.module.css';

interface Props {
  branches: BranchInfo[];
  activeBranchId: string | null;
  chords: ChordSelectionItem[];
  onCreateBranch: (forkPosition: number, label: string) => void;
  onSwitchBranch: (branchId: string) => void;
  onRenameBranch: (branchId: string, label: string) => void;
  onDeleteBranch: (branchId: string) => void;
}

function BranchNav({
  branches, activeBranchId, chords,
  onCreateBranch, onSwitchBranch, onRenameBranch, onDeleteBranch,
}: Props) {
  const [forkAt, setForkAt] = useState(0);
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
    <div className={s.wrapper}>
      <div className={s.tabs}>
        {branches.map((b) => {
          const isActive = b.id === activeBranchId;
          return (
            <div
              key={b.id}
              className={isActive ? s.tabActive : s.tab}
              onClick={() => { if (!isActive) onSwitchBranch(b.id); }}
            >
              {editingId === b.id ? (
                <input
                  className={s.editInput}
                  value={editLabel}
                  onChange={(e) => setEditLabel(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleRename(b.id); }}
                  onBlur={() => handleRename(b.id)}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className={isActive ? s.tabLabelActive : s.tabLabel}>
                  {b.label || `Branch ${b.id.slice(0, 6)}`}
                </span>
              )}
              <span className={s.tabCount}>({b.chords?.length ?? 0})</span>

              {!editingId && (
                <>
                  <button
                    className={s.iconBtnMuted}
                    onClick={(e) => { e.stopPropagation(); setEditingId(b.id); setEditLabel(b.label); }}
                    title="Rename"
                  >
                    &#9998;
                  </button>
                  {branches.length > 1 && (
                    <button
                      className={s.iconBtnDanger}
                      onClick={(e) => { e.stopPropagation(); onDeleteBranch(b.id); }}
                      title="Delete"
                    >
                      &#10005;
                    </button>
                  )}
                </>
              )}
            </div>
          );
        })}

        <button className={s.forkBtn} onClick={() => setShowFork(!showFork)}>
          + Fork
        </button>
      </div>

      {showFork && (
        <div className={s.forkForm}>
          <label className={s.forkLabel}>Fork after chord #</label>
          <select
            className={s.forkSelect}
            value={forkAt}
            onChange={(e) => setForkAt(Number(e.target.value))}
          >
            <option value={0}>0 (start over)</option>
            {chords.map((c) => (
              <option key={c.position} value={c.position}>
                {c.position} ({c.chord_name})
              </option>
            ))}
          </select>
          <input
            className={s.forkInput}
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="Branch label"
            onKeyDown={(e) => { if (e.key === 'Enter') handleFork(); }}
          />
          <button
            className={s.forkCreateBtn}
            onClick={handleFork}
            disabled={!newLabel.trim()}
          >
            Create
          </button>
        </div>
      )}
    </div>
  );
}

export default BranchNav;
