'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import axios from 'axios'
import GlassButton from '@/components/GlassButton'
import { ResultsList, ResultCard } from '@/components/ResultsMotion'

interface CodeSnippet {
  language: string
  code: string
  context: string
}

interface KnowledgeItem {
  id: string
  title: string
  summary?: string
  source_name: string
  source_url: string
  primary_language?: string
  framework?: string
  tags: string[]
  code_snippets: CodeSnippet[]
  body_text: string
  highlight?: {
    title?: string[]
    body_text?: string[]
    'code_snippets.code'?: string[]
  }
}

interface SearchResults {
  items: KnowledgeItem[]
  total: number
  page: number
  size: number
  total_pages: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [query, setQuery] = useState('')
  const [sourceType, setSourceType] = useState('')
  const [language, setLanguage] = useState('')
  const [framework, setFramework] = useState('')
  const [results, setResults] = useState<SearchResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  
  // Ask feature state
  const [askQuestion, setAskQuestion] = useState('')
  const [askResult, setAskResult] = useState<{
    answer: string
    confidence: number
    citations: Array<{ number: number; title: string; source_url: string; source_name: string }>
  } | null>(null)
  const [askLoading, setAskLoading] = useState(false)
  const [showAsk, setShowAsk] = useState(false)

  const search = useCallback(async (pageNum: number = 1) => {
    if (!query.trim() && !sourceType && !language && !framework) {
      return
    }

    setLoading(true)
    try {
      const params = new URLSearchParams({
        q: query || '',
        page: pageNum.toString(),
        size: '20',
      })

      if (sourceType) params.append('source_type', sourceType)
      if (language) params.append('primary_language', language)
      if (framework) params.append('framework', framework)

      const response = await fetch(`${API_URL}/search?${params.toString()}`)
      const data = await response.json()
      setResults(data)
      setPage(pageNum)
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setLoading(false)
    }
  }, [query, sourceType, language, framework])

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    search(1)
  }, [search])

  const handleAsk = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!askQuestion.trim()) return

    setAskLoading(true)
    setAskResult(null)
    
    try {
      const response = await axios.post(`${API_URL}/ask`, {
        question: askQuestion,
        top_k: 5,
        semantic: true
      })
      setAskResult(response.data)
    } catch (error: any) {
      console.error('Ask error:', error)
      setAskResult({
        answer: error.response?.data?.detail || 'An error occurred while generating an answer.',
        confidence: 0,
        citations: []
      })
    } finally {
      setAskLoading(false)
    }
  }, [askQuestion])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Section */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-slate-800 mb-3">Search Programming Knowledge</h1>
        <p className="text-lg text-slate-600">Find the best answers from across the web</p>
      </div>

      {/* Prominent Ask Info Hunter Button */}
      <div className="mb-8 flex justify-center">
        <button
          onClick={() => setShowAsk(!showAsk)}
          className="glass glass-noise rounded-2xl px-8 py-4 flex items-center gap-3 text-lg font-semibold text-slate-800 hover:bg-white/20 transition-all"
        >
          <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Ask Info Hunter
        </button>
      </div>

      {/* Ask Info Hunter Panel */}
      {showAsk && (
        <div className="glass glass-noise rounded-2xl p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <h2 className="text-xl font-semibold text-slate-800">Ask Info Hunter</h2>
          </div>
          
          <form onSubmit={handleAsk} className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={askQuestion}
                onChange={(e) => setAskQuestion(e.target.value)}
                placeholder="Ask a programming question..."
                className="flex-1 px-4 py-3 glass glass-noise rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
              <GlassButton type="submit" loading={askLoading}>
                Ask
              </GlassButton>
            </div>
          </form>

          {askResult && (
            <div className="mt-6 border-t border-white/20 pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Answer</h3>
                <span className="text-sm text-slate-600">
                  Confidence: {(askResult.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="prose max-w-none mb-6">
                <div 
                  className="text-slate-700 whitespace-pre-line"
                  dangerouslySetInnerHTML={{ 
                    __html: askResult.answer.replace(/\n/g, '<br/>').replace(/\[(\d+)\]/g, '<sup class="text-primary-600 font-medium">[$1]</sup>')
                  }}
                />
              </div>
              
              {askResult.citations && askResult.citations.length > 0 && (
                <div className="border-t border-white/20 pt-4">
                  <h4 className="font-semibold mb-2 text-slate-800">Sources</h4>
                  <ol className="list-decimal list-inside space-y-2">
                    {askResult.citations.map((citation) => (
                      <li key={citation.number} className="text-sm text-slate-700">
                        <a
                          href={citation.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 hover:underline"
                        >
                          {citation.number}. {citation.title} ({citation.source_name})
                        </a>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="glass glass-noise rounded-2xl p-6 mb-8">
        <h2 className="text-xl font-semibold text-slate-800 mb-4">Refined Search</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-slate-700 mb-2">
              Search Query
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search terms..."
              className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
            />
          </div>
          <div>
            <label htmlFor="sourceType" className="block text-sm font-medium text-slate-700 mb-2">
              Source Type
            </label>
            <select
              id="sourceType"
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
            >
              <option value="">All</option>
              <option value="github">GitHub</option>
              <option value="stackexchange">Stack Exchange</option>
              <option value="rss">RSS Feeds</option>
            </select>
          </div>
          <div>
            <label htmlFor="language" className="block text-sm font-medium text-slate-700 mb-2">
              Language
            </label>
            <input
              type="text"
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="e.g., Python, JavaScript"
              className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
            />
          </div>
          <div>
            <label htmlFor="framework" className="block text-sm font-medium text-slate-700 mb-2">
              Framework
            </label>
            <input
              type="text"
              id="framework"
              value={framework}
              onChange={(e) => setFramework(e.target.value)}
              placeholder="e.g., React, Django"
              className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
            />
          </div>
        </div>
        <div className="flex justify-center">
          <GlassButton type="submit" loading={loading} className="px-8">
            Search
          </GlassButton>
        </div>
      </form>

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass glass-noise rounded-2xl p-6">
              <div className="skeleton h-6 w-2/3 mb-3" />
              <div className="skeleton h-4 w-full mb-2" />
              <div className="skeleton h-4 w-5/6" />
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div>
          <div className="mb-6 text-slate-700 font-medium">
            {results.total} Result{results.total !== 1 ? 's' : ''} Found
          </div>

          <ResultsList>
            <div className="space-y-6">
              {results.items.map((item) => (
                <ResultCard key={item.id}>
                  <div className="glass glass-noise rounded-2xl p-6">
                    <div className="flex items-start justify-between mb-3">
                      <Link href={`/knowledge/${item.id}`} className="flex-1">
                        <h2 className="text-xl font-semibold text-slate-800 hover:text-primary-600 transition-colors">
                          {item.highlight?.title ? (
                            <span dangerouslySetInnerHTML={{ __html: item.highlight.title[0] }} />
                          ) : (
                            item.title
                          )}
                        </h2>
                      </Link>
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-4 text-sm text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {item.source_name} →
                      </a>
                    </div>

                    {item.summary && (
                      <p className="text-slate-600 mb-3">{item.summary}</p>
                    )}

                    {item.highlight?.body_text && (
                      <div className="mb-3 text-slate-700">
                        {item.highlight.body_text.map((fragment, idx) => (
                          <p key={idx} dangerouslySetInnerHTML={{ __html: fragment }} />
                        ))}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2 mb-3">
                      {item.primary_language && (
                        <span className="px-3 py-1 bg-primary-100/50 text-primary-800 text-xs font-medium rounded-lg border border-primary-200/50">
                          {item.primary_language}
                        </span>
                      )}
                      {item.framework && (
                        <span className="px-3 py-1 bg-green-100/50 text-green-800 text-xs font-medium rounded-lg border border-green-200/50">
                          {item.framework}
                        </span>
                      )}
                      {item.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="px-3 py-1 bg-slate-100/50 text-slate-700 text-xs font-medium rounded-lg border border-slate-200/50">
                          {tag}
                        </span>
                      ))}
                    </div>

                    {item.code_snippets && item.code_snippets.length > 0 && (
                      <div className="mt-4">
                        <div className="bg-slate-900/80 backdrop-blur-sm text-slate-100 p-4 rounded-xl overflow-x-auto border border-slate-700/50">
                          <pre className="text-sm">
                            <code>{item.code_snippets[0].code.substring(0, 200)}...</code>
                          </pre>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                          {item.code_snippets.length} code snippet{item.code_snippets.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    )}

                    <Link
                      href={`/knowledge/${item.id}`}
                      className="inline-block mt-4 text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      View Details →
                    </Link>
                  </div>
                </ResultCard>
              ))}
            </div>
          </ResultsList>

          {/* Pagination */}
          {results.total_pages > 1 && (
            <div className="mt-8 flex justify-center gap-2">
              <GlassButton
                onClick={() => search(page - 1)}
                disabled={page === 1 || loading}
                variant="secondary"
              >
                Previous
              </GlassButton>
              <span className="px-4 py-3 text-slate-700">
                {page} of {results.total_pages}
              </span>
              <GlassButton
                onClick={() => search(page + 1)}
                disabled={page >= results.total_pages || loading}
                variant="secondary"
              >
                Next
              </GlassButton>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
