// ResultsPanel — displays analyze recommendations with loading/error/empty states

export default function ResultsPanel({ recommendations = [], loading = false, error = null, onRetry }) {
  if (loading) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-4 space-y-3">
        <h2 className="text-sm font-semibold mb-2 text-slate-300">Results</h2>
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-20 rounded bg-slate-700 animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-slate-800 p-4">
        <h2 className="text-sm font-semibold mb-2 text-slate-300">Results</h2>
        <p className="text-red-400 text-sm mb-3">{error}</p>
        <button
          onClick={onRetry}
          className="text-xs px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  if (recommendations.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
        <h2 className="text-sm font-semibold mb-2 text-slate-300">Results</h2>
        <p className="text-slate-500 text-sm">
          Set up court positions and click Analyze to get recommendations.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4 space-y-4">
      <h2 className="text-sm font-semibold text-slate-300">Results</h2>
      {recommendations.map((rec, idx) => (
        <div key={idx} className="rounded border border-slate-700 bg-slate-900 p-3">
          <p className="font-semibold text-slate-100 text-sm">{rec.name}</p>
          <p className="text-slate-400 text-xs mt-0.5 mb-2">{rec.why}</p>
          <ol className="space-y-1.5">
            {rec.rally.map((step) => (
              <li key={step.shot} className="text-xs text-slate-300">
                <span className="text-slate-500 mr-1">#{step.shot}</span>
                <span className="font-medium">{step.who}:</span> {step.action}
                <span className="text-slate-500"> — {step.result}</span>
              </li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  )
}
