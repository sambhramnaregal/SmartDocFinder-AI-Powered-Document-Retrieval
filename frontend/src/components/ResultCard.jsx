import React from 'react'
import { ExplanationPanel } from './ExplanationPanel'

export function ResultCard({ result, expanded, onToggle }) {
  const { doc_id, category, preview, score, reason, overlap_keywords } = result

  return (
    <article className="group bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-lg shadow-black/40 hover:shadow-indigo-900/40 hover:border-indigo-500/60 transition-all duration-150">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 truncate max-w-[16rem] sm:max-w-none">
            {doc_id}
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Category:{' '}
            <span className="inline-flex items-center rounded-full bg-slate-800/80 px-2 py-0.5 text-[11px] font-medium text-slate-200">
              {category || 'unknown'}
            </span>
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400">Score</span>
          <div className="mt-1 flex items-center gap-2">
            <div className="w-20 h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-cyan-400"
                style={{ width: `${Math.min(score * 100, 100).toFixed(0)}%` }}
              />
            </div>
            <span className="text-xs font-mono text-slate-200">
              {score.toFixed(3)}
            </span>
          </div>
        </div>
      </header>

      <p className="mt-3 text-sm text-slate-200 leading-relaxed">
        {preview}
      </p>

      {overlap_keywords?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {overlap_keywords.slice(0, 6).map((kw) => (
            <span
              key={kw}
              className="px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/40 text-[11px] uppercase tracking-wide text-indigo-200"
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      <p className="mt-2 text-xs text-slate-400 italic">{reason}</p>

      <button
        type="button"
        onClick={onToggle}
        className="mt-3 text-xs font-medium text-indigo-300 hover:text-indigo-200 inline-flex items-center gap-1"
      >
        <span>{expanded ? 'Hide ranking details' : 'Show ranking details'}</span>
        <span className="text-[10px]">
          {expanded ? '▴' : '▾'}
        </span>
      </button>

      {expanded && (
        <div className="mt-3 border-t border-slate-800 pt-3">
          <ExplanationPanel result={result} />
        </div>
      )}
    </article>
  )
}


