import { NET_Y, KITCHEN, describeBallZone } from '../constants'

const panelStyle = {
  background: '#1c2530',
  borderRadius: 12,
  padding: '18px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: 16,
  border: '1px solid rgba(255,255,255,0.06)',
}

const st = {
  label: {
    display: 'block',
    fontFamily: "'DM Mono', monospace",
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '1.5px',
    color: 'rgba(255,255,255,0.4)',
    textTransform: 'uppercase',
    marginBottom: 7,
  },
  btn: {
    flex: 1,
    padding: '8px 10px',
    borderRadius: 6,
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(255,255,255,0.03)',
    color: 'rgba(255,255,255,0.45)',
    fontFamily: "'DM Mono', monospace",
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  active: {
    background: 'rgba(245,158,11,0.15)',
    borderColor: '#f59e0b',
    color: '#f59e0b',
    fontWeight: 700,
  },
  analyze: {
    width: '100%',
    padding: '13px 18px',
    borderRadius: 8,
    border: 'none',
    background: 'linear-gradient(135deg, #f59e0b, #d97706)',
    color: '#1a1a1a',
    fontFamily: "'DM Mono', monospace",
    fontSize: 13,
    fontWeight: 800,
    letterSpacing: '0.5px',
    cursor: 'pointer',
    textTransform: 'uppercase',
  },
  save: {
    width: '100%',
    padding: '10px 18px',
    borderRadius: 8,
    border: '1px solid rgba(72,191,227,0.3)',
    background: 'rgba(72,191,227,0.08)',
    color: '#48bfe3',
    fontFamily: "'DM Mono', monospace",
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
}

export default function ControlPanel({ mySide, setMySide, ball, setBall, onAnalyze, isAnalyzing, onSave, scenarioCount }) {
  const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN
  return (
    <div style={panelStyle}>
      <div>
        <label style={st.label}>I AM</label>
        <div style={{ display: 'flex', gap: 8 }}>
          {['left', 'right'].map((s) => (
            <button
              key={s}
              onClick={() => setMySide(s)}
              style={{ ...st.btn, ...(mySide === s ? st.active : {}) }}
            >
              {s === 'left' ? 'Left Side' : 'Right Side'}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label style={st.label}>BALL HEIGHT</label>
        <div style={{ display: 'flex', gap: 8 }}>
          {['low', 'mid', 'high'].map((h) => (
            <button
              key={h}
              onClick={() => setBall((b) => ({ ...b, height: h }))}
              style={{ ...st.btn, ...(ball.height === h ? st.active : {}) }}
            >
              {h.charAt(0).toUpperCase() + h.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label style={st.label}>BALL SPEED</label>
        <div style={{ display: 'flex', gap: 8 }}>
          {['slow', 'fast'].map((s) => (
            <button
              key={s}
              onClick={() => setBall((b) => ({ ...b, speed: s }))}
              style={{ ...st.btn, ...(ball.speed === s ? st.active : {}) }}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>
      {inK && (
        <div>
          <label style={st.label}>
            SPIN <span style={{ color: '#f59e0b', fontWeight: 400 }}>(kitchen)</span>
          </label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['topspin', 'flat', 'slice'].map((sp) => (
              <button
                key={sp}
                onClick={() => setBall((b) => ({ ...b, spin: sp }))}
                style={{ ...st.btn, ...(ball.spin === sp ? st.active : {}) }}
              >
                {sp.charAt(0).toUpperCase() + sp.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}
      <div
        style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 8,
          padding: '10px 14px',
          fontSize: 11,
          fontFamily: "'DM Mono', monospace",
          color: 'rgba(255,255,255,0.4)',
          lineHeight: 1.7,
        }}
      >
        Ball: ({ball.x.toFixed(1)}ft, {ball.y.toFixed(1)}ft) · {ball.height} · {ball.speed}
        {inK && ball.spin ? ` · ${ball.spin}` : ''}
        <br />
        Zone: {describeBallZone(ball.y)}
      </div>
      <button
        onClick={onAnalyze}
        disabled={isAnalyzing}
        style={{ ...st.analyze, opacity: isAnalyzing ? 0.6 : 1 }}
      >
        {isAnalyzing ? 'Analyzing...' : 'What Shot Should I Hit?'}
      </button>
      <button onClick={onSave} style={st.save}>
        Save Scenario {scenarioCount > 0 ? `(${scenarioCount})` : ''}
      </button>
    </div>
  )
}
