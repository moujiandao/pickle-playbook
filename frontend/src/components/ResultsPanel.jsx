import CorrectionControls from './CorrectionControls'

const panelStyle = {
  background: '#1c2530',
  borderRadius: 12,
  padding: '18px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
  border: '1px solid rgba(255,255,255,0.06)',
}

const BUBBLE_WIDTH = 220

export default function ResultsPanel({ result, error, warning, gameState }) {
  if (error) {
    return (
      <div
        style={{
          ...panelStyle,
          border: '1px solid rgba(239,100,97,0.4)',
          background: 'rgba(239,100,97,0.08)',
        }}
        role="alert"
      >
        <h3
          style={{
            margin: '0 0 8px 0',
            fontFamily: "'DM Mono', monospace",
            fontSize: 12,
            fontWeight: 700,
            color: '#ef6461',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
          }}
        >
          Analyze Failed
        </h3>
        <div
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 12,
            color: 'rgba(255,255,255,0.7)',
            lineHeight: 1.5,
            wordBreak: 'break-word',
          }}
        >
          {error}
        </div>
      </div>
    )
  }

  if (!result || result.length === 0) return null

  const top = result[0]

  return (
    <div style={panelStyle}>
      {warning && (
        <div
          style={{
            border: '1px solid rgba(245,158,11,0.4)',
            background: 'rgba(245,158,11,0.08)',
            borderRadius: 8,
            padding: '10px 14px',
            fontFamily: "'DM Mono', monospace",
            fontSize: 12,
            color: '#f59e0b',
            lineHeight: 1.5,
          }}
          role="alert"
        >
          {warning}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 11,
            fontWeight: 800,
            color: '#f59e0b',
          }}
        >
          #1
        </span>
        <span
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 16,
            fontWeight: 700,
            color: '#e8e4dd',
          }}
        >
          {top.name}
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: 11.5,
          color: 'rgba(255,255,255,0.45)',
          lineHeight: 1.5,
          fontFamily: "'DM Mono', monospace",
          fontStyle: 'italic',
        }}
      >
        {top.why}
      </p>
      <div
        style={{
          marginTop: 4,
          overflowX: 'auto',
          overflowY: 'hidden',
          paddingBottom: 6,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexWrap: 'nowrap',
            alignItems: 'stretch',
            gap: 6,
            minWidth: 'min-content',
          }}
        >
          {top.rally.map((step, i) => {
            const isYou = step.who === 'You' || step.who === 'Your Partner' || step.who === 'Partner'
            const accent = isYou ? '#48bfe3' : '#ef6461'
            const bg = isYou ? 'rgba(72,191,227,0.08)' : 'rgba(239,100,97,0.07)'
            const border = isYou ? 'rgba(72,191,227,0.25)' : 'rgba(239,100,97,0.25)'
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                <div
                  style={{
                    width: BUBBLE_WIDTH,
                    background: bg,
                    border: `1px solid ${border}`,
                    borderRadius: 10,
                    padding: '10px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <div
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 9,
                        fontWeight: 800,
                        fontFamily: "'DM Mono', monospace",
                        background: `${accent}33`,
                        color: accent,
                        border: `1.5px solid ${accent}66`,
                        flexShrink: 0,
                      }}
                    >
                      {step.shot}
                    </div>
                    <div
                      style={{
                        fontSize: 9.5,
                        fontWeight: 700,
                        fontFamily: "'DM Mono', monospace",
                        color: accent,
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                      }}
                    >
                      {step.who}
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: 11.5,
                      color: 'rgba(255,255,255,0.75)',
                      lineHeight: 1.4,
                      fontFamily: "'Outfit', sans-serif",
                    }}
                  >
                    {step.action}
                  </div>
                  <div
                    style={{
                      fontSize: 10.5,
                      color: 'rgba(255,255,255,0.4)',
                      lineHeight: 1.4,
                      fontFamily: "'DM Mono', monospace",
                    }}
                  >
                    {'->'} {step.result}
                  </div>
                </div>
                {i < top.rally.length - 1 && (
                  <div
                    aria-hidden="true"
                    style={{
                      flexShrink: 0,
                      width: 22,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'rgba(245,158,11,0.6)',
                      fontSize: 18,
                      fontWeight: 700,
                      fontFamily: "'DM Mono', monospace",
                    }}
                  >
                    →
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {gameState && (
        <CorrectionControls recommendation={top} gameState={gameState} />
      )}
    </div>
  )
}
