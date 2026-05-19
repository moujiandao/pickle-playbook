import { useState, useEffect, useRef } from 'react'
import Court3D from './components/Court3D'
import ControlPanel from './components/ControlPanel'
import ResultsPanel from './components/ResultsPanel'
import ScenarioList from './components/ScenarioList'
import { useDrag } from './hooks/useDrag'
import { useAnalyze } from './hooks/useAnalyze'
import { useScenarios } from './hooks/useScenarios'
import { INITIAL_PLAYERS, INITIAL_BALL, NET_Y, KITCHEN, COURT_W, describeBallZone } from './constants'
import { courtToScreen } from './lib/courtProjection'

export default function App() {
  const [mySide, setMySide] = useState('left')
  const [players, setPlayers] = useState(INITIAL_PLAYERS)
  const [ball, setBall] = useState(INITIAL_BALL)
  const [toast, setToast] = useState(false)
  const [skillLevel, setSkillLevel] = useState(null)
  const [handedness, setHandedness] = useState({
    my_left: 'right',
    my_right: 'right',
    opp_left: 'right',
    opp_right: 'right',
  })
  const [showAllZones, setShowAllZones] = useState(false)

  const { dragging, onPointerDown, svgContainerRef } = useDrag(setPlayers, setBall)
  const { result, setResult, isAnalyzing, error, warning, analyze } = useAnalyze()
  const { scenarios, saveScenario, deleteScenario } = useScenarios()
  const [reachError, setReachError] = useState(null)

  // Clear spin when ball leaves kitchen zone
  useEffect(() => {
    const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN
    if (!inK && ball.spin) setBall((b) => ({ ...b, spin: null }))
  }, [ball.y, ball.spin])

  function handleAnalyze() {
    if (!skillLevel) return
    const meKey = mySide === 'left' ? 'my_left' : 'my_right'
    const me = players[meKey]
    // Screen-space ellipse check — matches the dashed ring drawn in StickFigure
    // exactly (same rx, same ry-multiplier), so the gate aligns with what the
    // user sees instead of being a strict circle of the smaller rx dimension.
    const [meSx, meSy] = courtToScreen(me.x, me.y)
    const [ballSx, ballSy] = courtToScreen(ball.x, ball.y)
    const [courtLx] = courtToScreen(0, me.y)
    const [courtRx] = courtToScreen(COURT_W, me.y)
    const reachRx = (courtRx - courtLx) / 6
    const reachRy = reachRx * 0.338688 * 1.3 // mirrors wedgeRyVal * 1.3 in StickFigure
    const dxs = ballSx - meSx
    const dys = ballSy - meSy
    const inside = (dxs * dxs) / (reachRx * reachRx) + (dys * dys) / (reachRy * reachRy) <= 1
    if (!inside) {
      setReachError('You are not within reach of the ball!')
      setResult(null)
      return
    }
    setReachError(null)
    analyze(players, ball, mySide, skillLevel)
  }

  function handleSave() {
    const name = `${describeBallZone(ball.y)} · ${ball.height} ${ball.speed}${ball.spin ? ` · ${ball.spin}` : ''}`
    saveScenario({
      name,
      state: { players: { ...players }, ball: { ...ball }, mySide, skillLevel, result },
    })
    setToast(true)
    setTimeout(() => setToast(false), 2000)
  }

  function handleLoad(sc) {
    setPlayers(sc.state.players)
    setBall(sc.state.ball)
    setMySide(sc.state.mySide)
    setSkillLevel(sc.state.skillLevel || null)
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
              handedness={handedness}
              showAllZones={showAllZones}
            />
          </div>
          <ResultsPanel
            result={result}
            error={reachError || error}
            warning={warning}
            gameState={{ my_side: mySide, players, ball }}
          />
        </div>

        <div style={{ flex: '1 1 280px', minWidth: 280, maxWidth: 340, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ControlPanel
            mySide={mySide}
            setMySide={setMySide}
            players={players}
            ball={ball}
            setBall={setBall}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            onSave={handleSave}
            scenarioCount={scenarios.length}
            skillLevel={skillLevel}
            setSkillLevel={setSkillLevel}
            handedness={handedness}
            setHandedness={setHandedness}
            showAllZones={showAllZones}
            setShowAllZones={setShowAllZones}
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
