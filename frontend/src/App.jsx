import Court3D from './components/Court3D'
import ControlPanel from './components/ControlPanel'
import ResultsPanel from './components/ResultsPanel'
import ScenarioList from './components/ScenarioList'

function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">Pickle Playbook</h1>
        <p className="text-slate-400">Interactive pickleball strategy visualizer</p>
      </header>
      <main className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <section>
          <Court3D />
        </section>
        <aside className="space-y-4">
          <ControlPanel />
          <ResultsPanel />
          <ScenarioList />
        </aside>
      </main>
    </div>
  )
}

export default App
