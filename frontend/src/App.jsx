import { Component, useRef } from 'react'
import Court3D from './components/Court3D'
import ControlPanel from './components/ControlPanel'
import ResultsPanel from './components/ResultsPanel'
import ScenarioList from './components/ScenarioList'
import { useAnalyze } from './hooks/useAnalyze'

// Default center-court game state used until ControlPanel is wired up
const DEFAULT_GAME_STATE = {
  my_side: 'left',
  players: {
    my_left:   { x: 5.0,  y: 37.0 },
    my_right:  { x: 15.0, y: 37.0 },
    opp_left:  { x: 5.0,  y: 7.0 },
    opp_right: { x: 15.0, y: 7.0 },
  },
  ball: { x: 10.0, y: 33.0, height: 'mid', speed: 'slow', spin: null },
}

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(err) {
    return { hasError: true, message: err.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 text-slate-100 p-6 flex items-center justify-center">
          <div className="text-center space-y-3">
            <p className="text-red-400 font-semibold">Something went wrong</p>
            <p className="text-slate-400 text-sm">{this.state.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, message: '' })}
              className="text-xs px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
            >
              Reload
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function AppContent() {
  const { analyze, loading, error, recommendations } = useAnalyze()
  // Hold latest game state so onRetry can replay the same call
  const lastGameState = useRef(DEFAULT_GAME_STATE)

  function handleAnalyze() {
    lastGameState.current = DEFAULT_GAME_STATE
    analyze(DEFAULT_GAME_STATE)
  }

  function handleRetry() {
    analyze(lastGameState.current)
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <header className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pickle Playbook</h1>
          <p className="text-slate-400">Interactive pickleball strategy visualizer</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="mt-1 px-4 py-2 rounded bg-green-700 hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold transition-colors"
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </header>
      <main className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <section>
          <Court3D />
        </section>
        <aside className="space-y-4">
          <ControlPanel />
          <ResultsPanel
            recommendations={recommendations}
            loading={loading}
            error={error}
            onRetry={handleRetry}
          />
          <ScenarioList />
        </aside>
      </main>
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  )
}

export default App
