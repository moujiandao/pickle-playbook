const panelStyle = {
  background: '#1c2530',
  borderRadius: 12,
  padding: '18px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: 16,
  border: '1px solid rgba(255,255,255,0.06)',
}

export default function ResultsPanel({ result, error }) {
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
  if (!result) return null
  return (
    <div style={panelStyle}>
      <h3
        style={{
          margin: '0 0 14px 0',
          fontFamily: "'DM Mono', monospace",
          fontSize: 12,
          fontWeight: 700,
          color: '#f59e0b',
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
        }}
      >
        Shot Recommendations
      </h3>
      {result.map((shot, i) => (
        <div
          key={i}
          style={{
            padding: '14px 16px',
            marginBottom: 12,
            background: i === 0 ? 'rgba(245,158,11,0.06)' : 'rgba(255,255,255,0.015)',
            borderRadius: 10,
            borderLeft: `3px solid ${i === 0 ? '#f59e0b' : 'rgba(255,255,255,0.06)'}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span
              style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: 11,
                fontWeight: 800,
                color: i === 0 ? '#f59e0b' : 'rgba(255,255,255,0.25)',
                minWidth: 22,
              }}
            >
              #{i + 1}
            </span>
            <span
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: 15,
                fontWeight: 700,
                color: '#e8e4dd',
              }}
            >
              {shot.name}
            </span>
          </div>
          <p
            style={{
              margin: '0 0 10px 30px',
              fontSize: 12,
              color: 'rgba(255,255,255,0.4)',
              lineHeight: 1.5,
              fontFamily: "'DM Mono', monospace",
              fontStyle: 'italic',
            }}
          >
            {shot.why}
          </p>
          <div style={{ marginLeft: 30 }}>
            {shot.rally.map((step, j) => {
              const isYou = step.who === 'You' || step.who === 'Your Partner'
              return (
                <div key={j} style={{ display: 'flex', gap: 10 }}>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      minWidth: 24,
                    }}
                  >
                    <div
                      style={{
                        width: 20,
                        height: 20,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 9.5,
                        fontWeight: 800,
                        fontFamily: "'DM Mono', monospace",
                        background: isYou ? 'rgba(72,191,227,0.2)' : 'rgba(239,100,97,0.2)',
                        color: isYou ? '#48bfe3' : '#ef6461',
                        border: `1.5px solid ${isYou ? 'rgba(72,191,227,0.4)' : 'rgba(239,100,97,0.4)'}`,
                        flexShrink: 0,
                      }}
                    >
                      {step.shot}
                    </div>
                    {j < shot.rally.length - 1 && (
                      <div style={{ width: 1.5, height: 22, background: 'rgba(255,255,255,0.08)' }} />
                    )}
                  </div>
                  <div style={{ paddingBottom: j < shot.rally.length - 1 ? 5 : 0, flex: 1 }}>
                    <div
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        fontFamily: "'DM Mono', monospace",
                        color: isYou ? '#48bfe3' : '#ef6461',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        marginBottom: 2,
                      }}
                    >
                      {step.who}
                    </div>
                    <div
                      style={{
                        fontSize: 12.5,
                        color: 'rgba(255,255,255,0.6)',
                        lineHeight: 1.5,
                        fontFamily: "'Outfit', sans-serif",
                      }}
                    >
                      {step.action}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: 'rgba(255,255,255,0.3)',
                        lineHeight: 1.4,
                        fontFamily: "'DM Mono', monospace",
                        marginTop: 2,
                      }}
                    >
                      {'->'} {step.result}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
