import { useRecommendation } from './hooks/useRecommendation';
import ErrorBoundary from './components/ErrorBoundary';
import StyleInput from './components/StyleInput';
import ChordSelector from './components/ChordSelector';
import SequenceDisplay from './components/SequenceDisplay';
import BranchNav from './components/BranchNav';
import s from './App.module.css';

function App() {
  const { state, actions } = useRecommendation();

  const branches = state.session?.branches ?? [];
  const activeBranchId = state.session?.active_branch_id ?? null;
  const activeBranch = branches.find((b) => b.id === activeBranchId);
  const sequence = activeBranch?.chords ?? [];

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
      </header>

      <main className={s.main}>
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
            <button className={s.restartBtn} onClick={actions.restart}>
              Start New
            </button>
          </div>
        )}
      </main>
    </div>
    </ErrorBoundary>
  );
}

export default App;
