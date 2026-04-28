import { useState } from 'react';
import { useRecommendation } from './hooks/useRecommendation';
import ErrorBoundary from './components/ErrorBoundary';
import StyleInput from './components/StyleInput';
import ChordSelector from './components/ChordSelector';
import SequenceDisplay from './components/SequenceDisplay';
import BranchNav from './components/BranchNav';
import SessionHistory from './components/SessionHistory';
import s from './App.module.css';

function App() {
  const { state, actions } = useRecommendation();
  const [showHistory, setShowHistory] = useState(false);

  const branches = state.session?.branches ?? [];
  const activeBranchId = state.session?.active_branch_id ?? null;
  const activeBranch = branches.find((b) => b.id === activeBranchId);
  const sequence = activeBranch?.chords ?? [];

  function handleRestart() {
    if (window.confirm('Start a new search? Current progress will be saved in history.')) {
      actions.restart();
    }
  }

  function handleResume(sessionId: string) {
    setShowHistory(false);
    actions.loadSession(sessionId);
  }

  return (
    <ErrorBoundary>
      <div className={s.app}>
      <header className={s.header}>
        <h1>Chord Progression Recommender</h1>
        {state.session && (
          <span className={s.styleMeta}>
            {state.session.style_genre_tag.replace(/^__main__/, '')}
            {' · '}{state.session.style_decade}s
            {' · '}{state.session.style_section}
          </span>
        )}
        <div className={s.headerActions}>
          {(state.phase === 'IDLE' || state.phase === 'MATCHING') && !showHistory && (
            <button className={s.headerBtn} onClick={() => setShowHistory(true)}>
              History
            </button>
          )}
          {state.phase === 'RECOMMENDING' && (
            <button className={s.headerBtn} onClick={handleRestart}>
              New Search
            </button>
          )}
        </div>
      </header>

      <main className={s.main}>
        {showHistory && (state.phase === 'IDLE' || state.phase === 'MATCHING') && (
          <SessionHistory
            onResume={handleResume}
            onBack={() => setShowHistory(false)}
          />
        )}

        {!showHistory && (state.phase === 'IDLE' || state.phase === 'MATCHING') && (
          <StyleInput
            matches={state.matches}
            isLoading={state.isLoading}
            error={state.error}
            onSubmit={(query) => { actions.submitStyle(query); }}
            onSelectMatch={(match) => { actions.startSession(match); }}
          />
        )}

        {state.phase === 'RECOMMENDING' && (
          <>
            <BranchNav
              branches={branches}
              activeBranchId={activeBranchId}
              chords={sequence}
              onCreateBranch={actions.createBranch}
              onSwitchBranch={actions.switchBranch}
              onRenameBranch={actions.renameBranch}
              onDeleteBranch={actions.deleteBranch}
            />
            <SequenceDisplay
              chords={sequence}
              onUndo={actions.undo}
              onFinish={actions.finish}
            />
            <ChordSelector
              candidates={state.candidates}
              isLoading={state.isLoading}
              error={state.error}
              onSelect={(c) => { actions.selectChord(c); }}
            />
          </>
        )}

        {state.phase === 'DONE' && state.session && (
          <div>
            {state.session.branches.map((b) => (
              <div key={b.id} className={s.doneSection}>
                <h3 className={s.doneHeading}>
                  {b.label || 'main'} ({b.chords.length} chords)
                </h3>
                <SequenceDisplay chords={b.chords} readonly onUndo={() => {}} onFinish={() => {}} />
              </div>
            ))}
            <div style={{ display: 'flex', gap: '10px', marginTop: '1.5rem' }}>
              <button className={s.restartBtn} onClick={actions.restart}>
                Start New
              </button>
              <button className={s.headerBtn} onClick={() => { setShowHistory(true); actions.restart(); }}>
                View History
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
    </ErrorBoundary>
  );
}

export default App;
