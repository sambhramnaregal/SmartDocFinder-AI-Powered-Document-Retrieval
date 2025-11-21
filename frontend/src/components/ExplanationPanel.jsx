import React from 'react'

export function ExplanationPanel({ result }) {
  const { cosine_sim, overlap_ratio, len_score } = result

  const metrics = [
    { label: 'Cosine similarity', value: cosine_sim },
    { label: 'Keyword overlap', value: overlap_ratio },
    { label: 'Length normalization', value: len_score },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] text-xs">
      <div className="space-y-2">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="flex justify-between mb-1">
              <span className="text-slate-300">{m.label}</span>
              <span className="font-mono text-slate-200">{m.value.toFixed(3)}</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300"
                style={{ width: `${Math.min(m.value * 100, 100).toFixed(0)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-2 sm:mt-0 text-slate-300 leading-relaxed">
        <p className="mb-1 font-semibold text-slate-100">How this was ranked</p>
        <p>
          The final score is a weighted combination of semantic similarity (cosine
          between embeddings), exact keyword overlap ratio, and a small boost for
          concise documents. This gives results that are both semantically relevant
          and interpretable.
        </p>
      </div>
    </div>
  )
}


