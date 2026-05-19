import { NET_Y, KITCHEN, describeBallZone, SKILL_LEVELS } from '../constants'

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

export default function ControlPanel({ mySide, setMySide, players, ball, setBall, onAnalyze, isAnalyzing, onSave, scenarioCount, skillLevel, setSkillLevel, handedness, setHandedness, showAllZones, setShowAllZones }) {
  const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN
  const fmt = (n) => n.toFixed(1).padStart(4, ' ')
  const meKey = mySide === 'left' ? 'my_left' : 'my_right'
  const partnerKey = mySide === 'left' ? 'my_right' : 'my_left'
  const handRows = [
    { key: meKey, label: 'ME' },
    { key: partnerKey, label: 'PARTNER' },
    { key: 'opp_left', label: 'OPP L' },
    { key: 'opp_right', label: 'OPP R' },
  ]
  const coordRows = players
    ? [
        { label: `ME (${mySide[0].toUpperCase()})`, pos: players[meKey], color: '#f59e0b' },
        { label: `PARTNER (${mySide === 'left' ? 'R' : 'L'})`, pos: players[partnerKey], color: '#48bfe3' },
        { label: 'OPP L', pos: players.opp_left, color: 'rgba(255,255,255,0.55)' },
        { label: 'OPP R', pos: players.opp_right, color: 'rgba(255,255,255,0.55)' },
      ]
    : []
  return (
    <div style={panelStyle}>
      <div>
        <label style={st.label}>SKILL LEVEL</label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {SKILL_LEVELS.map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSkillLevel(lvl)}
              style={{ ...st.btn, ...(skillLevel === lvl ? st.active : {}) }}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>
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
      {setShowAllZones && (
        <div>
          <label style={st.label}>PLAYER ATTACKABLE ZONES DISPLAY</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { label: 'ON', val: true },
              { label: 'OFF', val: false },
            ].map(({ label, val }) => (
              <button
                key={label}
                onClick={() => setShowAllZones(val)}
                style={{ ...st.btn, ...(showAllZones === val ? st.active : {}) }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
      {handedness && setHandedness && (
        <div>
          <label style={st.label}>HANDEDNESS</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {handRows.map((row) => (
              <div key={row.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: 10,
                    color: 'rgba(255,255,255,0.55)',
                    width: 64,
                    letterSpacing: '0.5px',
                  }}
                >
                  {row.label}
                </span>
                <div style={{ display: 'flex', gap: 6, flex: 1 }}>
                  {['right', 'left'].map((h) => (
                    <button
                      key={h}
                      onClick={() => setHandedness({ ...handedness, [row.key]: h })}
                      style={{
                        ...st.btn,
                        padding: '5px 8px',
                        fontSize: 11,
                        ...(handedness[row.key] === h ? st.active : {}),
                      }}
                    >
                      {h === 'right' ? 'R' : 'L'}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
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
        <div style={{ color: 'rgba(255,255,255,0.55)', fontWeight: 600, letterSpacing: '1px', marginBottom: 4 }}>
          POSITIONS (ft)
        </div>
        {coordRows.map((row) => (
          <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', color: row.color }}>
            <span>{row.label}</span>
            <span>({fmt(row.pos.x)}, {fmt(row.pos.y)})</span>
          </div>
        ))}
        <div
          style={{
            borderTop: '1px solid rgba(255,255,255,0.08)',
            margin: '6px 0',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fbbf24' }}>
          <span>BALL</span>
          <span>({fmt(ball.x)}, {fmt(ball.y)})</span>
        </div>
        <div style={{ marginTop: 2 }}>
          {ball.height} · {ball.speed}
          {inK && ball.spin ? ` · ${ball.spin}` : ''} · {describeBallZone(ball.y)}
        </div>
      </div>
      <button
        onClick={onAnalyze}
        disabled={isAnalyzing || !skillLevel}
        style={{ ...st.analyze, opacity: isAnalyzing || !skillLevel ? 0.6 : 1 }}
      >
        {!skillLevel ? 'Select Skill Level' : isAnalyzing ? 'Analyzing...' : 'What Shot Should I Hit?'}
      </button>
      <button onClick={onSave} style={st.save}>
        Save Scenario {scenarioCount > 0 ? `(${scenarioCount})` : ''}
      </button>
    </div>
  )
}
