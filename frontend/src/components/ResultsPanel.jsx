// ResultsPanel — 3-shot rally display with per-card correction controls.

import CorrectionControls from './CorrectionControls'

// Renders a single rally shot row
function RallyShot({ shot }) {
  const whoColor = shot.who.toLowerCase().includes('opp')
    ? 'text-red-400'
    : 'text-blue-400'
  return (
    <li className="flex gap-2 text-xs leading-snug">
      <span className="shrink-0 w-4 h-4 rounded-full bg-slate-700 text-slate-400 flex items-center justify-center text-[10px] font-bold mt-0.5">
        {shot.shot}
      </span>
      <div>
        <span className={`font-semibold ${whoColor}`}>{shot.who}: </span>
        <span className="text-slate-300">{shot.action}</span>
        {shot.result && (
          <span className="text-slate-500"> — {shot.result}</span>
        )}
      </div>
    </li>
  )
}

// A single recommendation card
function RecommendationCard({ rec, index, gameState }) {
  const accentColors = [
    'border-l-blue-500',
    'border-l-emerald-500',
    'border-l-amber-500',
  ]
  const accent = accentColors[index % accentColors.length]

  return (
    <div
      className={`rounded-lg bg-slate-800/60 border border-slate-700 border-l-2 ${accent} p-3`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <h3 className="text-sm font-semibold text-slate-100 leading-tight">
          {rec.name}
        </h3>
        <span className="shrink-0 text-[10px] text-slate-500 font-mono mt-0.5">
          #{index + 1}
        </span>
      </div>

      {/* Why */}
      <p className="text-xs text-slate-400 mb-3 leading-relaxed">{rec.why}</p>

      {/* Rally sequence */}
      <ul className="space-y-1.5">
        {rec.rally.map((shot) => (
          <RallyShot key={shot.shot} shot={shot} />
        ))}
      </ul>

      {/* Correction controls — only rendered when gameState is available */}
      {gameState && (
        <CorrectionControls recommendation={rec} gameState={gameState} />
      )}
    </div>
  )
}

// Empty / loading states
function EmptyState() {
  return (
    <p className="text-slate-500 text-sm text-center py-4">
      Position players and click Analyze to see recommendations.
    </p>
  )
}

function LoadingState() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-24 rounded-lg bg-slate-800/40 border border-slate-700 animate-pulse"
        />
      ))}
    </div>
  )
}

export default function ResultsPanel({ recommendations = [], gameState = null, loading = false }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <h2 className="text-sm font-semibold mb-3 text-slate-300">
        Shot Recommendations
        {recommendations.length > 0 && (
          <span className="ml-2 text-xs font-normal text-slate-500">
            {recommendations.length} option{recommendations.length !== 1 ? 's' : ''}
          </span>
        )}
      </h2>

      {loading ? (
        <LoadingState />
      ) : recommendations.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec, i) => (
            <RecommendationCard
              key={`${rec.name}-${i}`}
              rec={rec}
              index={i}
              gameState={gameState}
            />
          ))}
        </div>
      )}
    </div>
  )
}
