import { useRecommendation } from './hooks/useRecommendation';
import StyleInput from './components/StyleInput';
import ChordSelector from './components/ChordSelector';
import SequenceDisplay from './components/SequenceDisplay';
import BranchNav from './components/BranchNav';
import styles from './App.module.css';

function App() {
  const { state, actions } = useRecommendation();

  const branches = state.session?.branches ?? [];
  const activeBranchId = state.session?.active_branch_id ?? null;
  const activeBranch = branches.find((b) => b.id === activeBranchId);
  const sequence = activeBranch?.chords ?? [];

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>Chord Progression Recommender</h1>
        {state.session && (
          <span style={{ color: '#999', fontSize: '0.85rem' }}>
            {state.session.style_genre_tag.replace(/^__main__/, '')}
            {' '}&middot;{' '}{state.session.style_decade}s
            {' '}&middot;{' '}{state.session.style_section}
          </span>
        )}
      </header>

      <main className={styles.main}>
        {(state.phase === 'IDLE' || state.phase === 'MATCHING') && (
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

        {state.phase === 'DONE' && (
          <div>
            {state.session && (
              <>
                {state.session.branches.map((b) => (
                  <div key={b.id} style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ color: '#e94560', margin: '0 0 8px' }}>
                      {b.label || 'main'} ({b.chords.length} chords)
                    </h3>
                    <SequenceDisplay
                      chords={b.chords}
                      onUndo={() => {}}
                      onFinish={() => {}}
                    />
                  </div>
                ))}
              </>
            )}
            <button
              onClick={actions.restart}
              style={{
                padding: '10px 24px',
                border: 'none',
                borderRadius: '6px',
                background: '#e94560',
                color: '#fff',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '1rem',
              }}
            >
              Start New
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
