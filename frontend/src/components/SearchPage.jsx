import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { ResultCard } from './ResultCard'

// Prefer VITE_API_BASE_URL when provided; fall back to Render backend URL in production,
// and localhost for local development.

// const API_BASE =
//   import.meta.env.VITE_API_BASE_URL ||
//   (import.meta.env.DEV
//     ? 'http://localhost:8000'
//     : 'https://smartdocfinder-ai-powered-document.onrender.com')

const API_BASE ='https://smartdocfinder-ai-powered-document.onrender.com'

const SAMPLE_QUERIES = [
  'quantum physics basics',
  'neural networks for image recognition',
  'hockey teams and recent games',
  'computer graphics rendering',
]

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState(null)
  const [stats, setStats] = useState(null)
  const [topK, setTopK] = useState(5)

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await axios.get(`${API_BASE}/stats`)
        setStats(res.data)
      } catch (err) {
        // Stats are optional; fail silently in UI.
        console.warn('Failed to load stats', err)
      }
    }
    fetchStats()
  }, [])

  async function runSearch(text) {
    const q = text.trim()
    if (!q) return

    setError('')
    setLoading(true)
    setResults([])

    try {
      const res = await axios.post(`${API_BASE}/search`, {
        query: q,
        top_k: topK,
      })
      setResults(res.data.results || [])
    } catch (err) {
      console.error(err)
      setError('Search failed – please check that the SmartDocFinder backend is reachable.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(e) {
    e.preventDefault()
    await runSearch(query)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex flex-col">
      <header className="py-6 border-b border-slate-800/80 backdrop-blur">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4">
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">
            <span className="text-indigo-400">SmartDocFinder</span> – AI-Powered Document Retrieval
          </h1>
          <span className="hidden sm:inline text-xs text-slate-400">
            Multi-document semantic search with explanations
          </span>
        </div>
      </header>

      <main className="flex-1 flex justify-center px-4">
        <div className="w-full max-w-6xl mt-10 grid gap-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,2fr)]">
          {/* Left: description, stats, and sample queries */}
          <section className="space-y-6">
            <div>
              <h2 className="text-lg sm:text-xl font-semibold text-slate-50">
                Welcome to <span className="text-indigo-400">SmartDocFinder</span>
              </h2>
              <p className="mt-2 text-sm text-slate-300 leading-relaxed">
                An AI-powered semantic search engine over your document collection.
                Type a natural-language question and SmartDocFinder will retrieve the
                most relevant documents, explain why they matched, and highlight
                overlapping keywords.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 px-3 py-3">
                <p className="text-slate-400">Indexed documents</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">
                  {stats ? stats.documents : '—'}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  From the 20 Newsgroups text dataset (train split)
                </p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 px-3 py-3">
                <p className="text-slate-400">Cached embeddings</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">
                  {stats ? stats.embeddings : '—'}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  Stored locally in SQLite & FAISS for fast reuse
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 px-3 py-3 space-y-3 text-xs">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-slate-300 font-semibold">Search controls</p>
                  <p className="text-slate-500 mt-0.5">
                    Adjust how many top results you want to inspect.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400">top_k</span>
                  <input
                    type="range"
                    min={3}
                    max={15}
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="w-28 accent-indigo-500"
                  />
                  <span className="text-xs font-mono text-slate-100 w-6 text-right">
                    {topK}
                  </span>
                </div>
              </div>

              <div>
                <p className="text-slate-300 font-semibold mb-1">Try a sample query</p>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_QUERIES.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => {
                        setQuery(q)
                        runSearch(q)
                      }}
                      className="px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-200 border border-slate-700/80"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Right: search bar and results */}
          <section>
            <form
              onSubmit={handleSearch}
              className="bg-slate-900/80 border border-slate-800 rounded-3xl shadow-xl shadow-black/40 px-4 sm:px-6 py-3 flex items-center gap-3 backdrop-blur"
            >
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search across your documents…"
                className="flex-1 bg-transparent outline-none text-base sm:text-lg placeholder:text-slate-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 rounded-full bg-indigo-500 hover:bg-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed text-sm sm:text-base font-medium shadow-md shadow-indigo-900/40 transition-colors"
              >
                {loading ? 'Searching…' : 'Search'}
              </button>
            </form>

            {error && (
              <p className="mt-3 text-sm text-rose-400 bg-rose-950/40 border border-rose-800/60 rounded-xl px-3 py-2">
                {error}
              </p>
            )}

            <div className="mt-6 mb-10 space-y-3">
              {results.length === 0 && !loading && !error && (
                <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 px-4 py-5 text-sm text-slate-400">
                  <p className="font-semibold text-slate-200 mb-1">Ready when you are.</p>
                  <p>
                    Start by typing a topic you care about (e.g. "quantum physics" or
                    "hockey teams"). SmartDocFinder will search across all indexed
                    documents from the 20 Newsgroups dataset and explain why each
                    result is relevant.
                  </p>
                </div>
              )}

              {results.map((r) => (
                <ResultCard
                  key={r.doc_id}
                  result={r}
                  expanded={expandedId === r.doc_id}
                  onToggle={() =>
                    setExpandedId((prev) => (prev === r.doc_id ? null : r.doc_id))
                  }
                />
              ))}

              {loading && (
                <p className="text-xs text-slate-500">Searching embeddings and ranking results…</p>
              )}
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 py-3 text-xs text-slate-500 text-center">
        Embedding search • FAISS • FastAPI • React + Tailwind
      </footer>
    </div>
  )
}


