'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

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
  author?: string
  licence?: string
  published_at?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function KnowledgeDetail() {
  const params = useParams()
  const id = params.id as string
  const [item, setItem] = useState<KnowledgeItem | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchItem = async () => {
      try {
        const response = await fetch(`${API_URL}/knowledge/${id}`)
        if (response.ok) {
          const data = await response.json()
          setItem(data)
        }
      } catch (error) {
        console.error('Error fetching item:', error)
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchItem()
    }
  }, [id])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass glass-noise rounded-2xl p-6">
              <div className="skeleton h-8 w-2/3 mb-4" />
              <div className="skeleton h-4 w-full mb-2" />
              <div className="skeleton h-4 w-5/6" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="glass glass-noise rounded-2xl p-12 text-center">
          <h1 className="text-2xl font-bold mb-4 text-slate-800">Item not found</h1>
          <Link href="/" className="text-primary-600 hover:text-primary-700 font-medium">
            ← Back to Search
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link href="/" className="text-primary-600 hover:text-primary-700 mb-6 inline-block font-medium">
        ← Back to Search
      </Link>

      <article className="glass glass-noise rounded-2xl p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-800 mb-4">{item.title}</h1>
          
          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {item.source_name} →
            </a>
            {item.author && <span>By {item.author}</span>}
            {item.published_at && (
              <span>Published {new Date(item.published_at).toLocaleDateString()}</span>
            )}
            {item.licence && <span>License: {item.licence}</span>}
          </div>
        </div>

        {item.summary && (
          <div className="mb-6 p-4 glass rounded-xl border-l-4 border-primary-500">
            <p className="text-slate-700">{item.summary}</p>
          </div>
        )}

        <div className="flex flex-wrap gap-2 mb-6">
          {item.primary_language && (
            <span className="px-3 py-1 bg-primary-100/50 text-primary-800 text-sm font-medium rounded-lg border border-primary-200/50">
              {item.primary_language}
            </span>
          )}
          {item.framework && (
            <span className="px-3 py-1 bg-green-100/50 text-green-800 text-sm font-medium rounded-lg border border-green-200/50">
              {item.framework}
            </span>
          )}
          {item.tags.map((tag) => (
            <span key={tag} className="px-3 py-1 bg-slate-100/50 text-slate-700 text-sm font-medium rounded-lg border border-slate-200/50">
              {tag}
            </span>
          ))}
        </div>

        {item.body_text && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-slate-800">Content</h2>
            <div className="prose max-w-none">
              <p className="whitespace-pre-wrap text-slate-700 leading-relaxed">{item.body_text}</p>
            </div>
          </div>
        )}

        {item.code_snippets && item.code_snippets.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-slate-800">
              Code Snippets ({item.code_snippets.length})
            </h2>
            <div className="space-y-6">
              {item.code_snippets.map((snippet, index) => (
                <div key={index} className="border border-white/20 rounded-xl overflow-hidden glass">
                  <div className="bg-white/10 px-4 py-3 flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">
                      {snippet.language.toUpperCase()}
                    </span>
                    {snippet.context && (
                      <span className="text-xs text-slate-500">{snippet.context}</span>
                    )}
                  </div>
                  <div className="bg-slate-900/80 backdrop-blur-sm text-slate-100 p-4 overflow-x-auto">
                    <pre className="text-sm">
                      <code>{snippet.code}</code>
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </article>
    </div>
  )
}
