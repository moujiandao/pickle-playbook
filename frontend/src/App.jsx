import { useState, useEffect, useRef } from 'react'
import Court3D from './components/Court3D'
import ControlPanel from './components/ControlPanel'
import ResultsPanel from './components/ResultsPanel'
import ScenarioList from './components/ScenarioList'
import { useDrag } from './hooks/useDrag'
import { useAnalyze } from './hooks/useAnalyze'
import { useScenarios } from './hooks/useScenarios'
import { INITIAL_PLAYERS, INITIAL_BALL, NET_Y, KITCHEN, COURT_W, describeBallZone } from './constants'

export default function App() {
  const [mySide, setMySide] = useState('left')
  const [players, setPlayers] = useState(INITIAL_PLAYERS)
  const [ball, setBall] = useState(INITIAL_BALL)
  const [toast, setToast] = useState(false)

  const { dragging, onPointerDown, svgContainerRef } = useDrag(setPlayers, setBall)
  const { result, setResult, isAnalyzing, error, analyze } = useAnalyze()
  const { scenarios, saveScenario, deleteScenario } = useScenarios()
  const [reachError, setReachError] = useState(null)

  // Clear spin when ball leaves kitchen zone
  useEffect(() => {
    const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN
    if (!inK && ball.spin) setBall((b) => ({ ...b, spin: null }))
  }, [ball.y, ball.spin])

  function handleAnalyze() {
    const meKey = mySide === 'left' ? 'my_left' : 'my_right'
    const me = players[meKey]
    const dx = ball.x - me.x
    const dy = ball.y - me.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist > COURT_W / 3) {
      setReachError("You can't reach the ball!")
      setResult(null)
      return
    }
    setReachError(null)
    analyze(players, ball, mySide)
  }

  function handleSave() {
    const name = `${describeBallZone(ball.y)} · ${ball.height} ${ball.speed}${ball.spin ? ` · ${ball.spin}` : ''}`
    saveScenario({
      name,
      state: { players: { ...players }, ball: { ...ball }, mySide, result },
    })
    setToast(true)
    setTimeout(() => setToast(false), 2000)
  }

  function handleLoad(sc) {
    setPlayers(sc.state.players)
    setBall(sc.state.ball)
    setMySide(sc.state.mySide)
    setResult(sc.state.result || null)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0e1117',
        color: '#e8e4dd',
        fontFamily: "'Outfit', sans-serif",
        padding: '20px 12px',
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=DM+Mono:wght@400;500&display=swap"
        rel="stylesheet"
      />

      {toast && (
        <div
          style={{
            position: 'fixed',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#f59e0b',
            color: '#1a1a1a',
            padding: '10px 24px',
            borderRadius: 8,
            fontFamily: "'DM Mono', monospace",
            fontSize: 13,
            fontWeight: 700,
            zIndex: 100,
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          }}
        >
          Scenario saved!
        </div>
      )}

      <div style={{ maxWidth: 1150, margin: '0 auto 16px', textAlign: 'center' }}>
        <h1
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 20,
            fontWeight: 800,
            letterSpacing: '2px',
            margin: 0,
            color: '#f59e0b',
            textTransform: 'uppercase',
          }}
        >
          Pickle Playbook
        </h1>
        <p
          style={{
            fontSize: 12,
            color: 'rgba(255,255,255,0.3)',
            margin: '5px 0 0',
            fontFamily: "'DM Mono', monospace",
          }}
        >
          Drag players & ball → set parameters → get 3-shot rally analysis
        </p>
      </div>

      {/* Responsive layout: side-by-side on desktop, stacked on mobile */}
      <div
        style={{
          maxWidth: 1150,
          margin: '0 auto',
          display: 'flex',
          gap: 18,
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'flex-start',
        }}
      >
        <div
          style={{
            flexShrink: 0,
            width: '100%',
            maxWidth: 800,
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          <div
            ref={svgContainerRef}
            style={{
              borderRadius: 10,
              overflow: 'hidden',
            }}
          >
            <Court3D
              players={players}
              ball={ball}
              mySide={mySide}
              dragging={dragging}
              onPointerDown={onPointerDown}
            />
          </div>
          <ResultsPanel
            result={result}
            error={reachError || error}
            gameState={{ my_side: mySide, players, ball }}
          />
        </div>

        <div style={{ flex: '1 1 280px', minWidth: 280, maxWidth: 340, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ControlPanel
            mySide={mySide}
            setMySide={setMySide}
            ball={ball}
            setBall={setBall}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            onSave={handleSave}
            scenarioCount={scenarios.length}
          />
          <ScenarioList
            scenarios={scenarios}
            onLoad={handleLoad}
            onDelete={deleteScenario}
          />
        </div>
      </div>
    </div>
  )
}
