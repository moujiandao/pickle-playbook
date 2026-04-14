import { useState } from 'react'

const panelStyle = {
  background: '#1c2530',
  borderRadius: 12,
  padding: '18px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: 16,
  border: '1px solid rgba(255,255,255,0.06)',
}

export default function ScenarioList({ scenarios, onLoad, onDelete }) {
  const [open, setOpen] = useState(false)
  if (!scenarios.length) return null
  return (
    <div style={panelStyle}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: 'none',
          border: 'none',
          color: 'rgba(255,255,255,0.5)',
          fontFamily: "'DM Mono', monospace",
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          padding: 0,
          width: '100%',
          textAlign: 'left',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <span>SAVED SCENARIOS ({scenarios.length})</span>
        <span style={{ fontSize: 16 }}>{open ? '-' : '+'}</span>
      </button>
      {open && (
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 10px',
                borderRadius: 6,
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.05)',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#e8e4dd',
                    fontFamily: "'Outfit', sans-serif",
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {sc.name}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: 'rgba(255,255,255,0.3)',
                    fontFamily: "'DM Mono', monospace",
                  }}
                >
                  {new Date(sc.timestamp).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={() => onLoad(sc)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 4,
                  border: '1px solid rgba(72,191,227,0.3)',
                  background: 'rgba(72,191,227,0.1)',
                  color: '#48bfe3',
                  fontSize: 10,
                  fontFamily: "'DM Mono', monospace",
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Load
              </button>
              <button
                onClick={() => onDelete(sc.id)}
                style={{
                  padding: '4px 8px',
                  borderRadius: 4,
                  border: '1px solid rgba(239,100,97,0.3)',
                  background: 'rgba(239,100,97,0.1)',
                  color: '#ef6461',
                  fontSize: 10,
                  fontFamily: "'DM Mono', monospace",
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                x
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
