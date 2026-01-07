'use client'

import { useState, useEffect } from 'react'
import GlassButton from '@/components/GlassButton'

interface SavedSearch {
  id: string
  name: string
  query?: string
  source_type?: string
  primary_language?: string
  framework?: string
  tags: string[]
  created_at: string
  updated_at: string
  last_run_at?: string
  match_count: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SavedSearches() {
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    query: '',
    source_type: '',
    primary_language: '',
    framework: '',
    tags: '',
  })

  useEffect(() => {
    fetchSearches()
  }, [])

  const fetchSearches = async () => {
    try {
      const response = await fetch(`${API_URL}/saved-searches`)
      if (response.ok) {
        const data = await response.json()
        setSearches(data)
      }
    } catch (error) {
      console.error('Error fetching saved searches:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const tagsArray = formData.tags.split(',').map(t => t.trim()).filter(t => t)
      const payload = {
        name: formData.name,
        query: formData.query || undefined,
        source_type: formData.source_type || undefined,
        primary_language: formData.primary_language || undefined,
        framework: formData.framework || undefined,
        tags: tagsArray,
      }

      const response = await fetch(`${API_URL}/saved-searches`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        setFormData({
          name: '',
          query: '',
          source_type: '',
          primary_language: '',
          framework: '',
          tags: '',
        })
        setShowForm(false)
        fetchSearches()
      }
    } catch (error) {
      console.error('Error creating saved search:', error)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass glass-noise rounded-2xl p-6">
              <div className="skeleton h-6 w-2/3 mb-3" />
              <div className="skeleton h-4 w-full mb-2" />
              <div className="skeleton h-4 w-5/6" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-slate-800">Saved Searches</h1>
        <GlassButton onClick={() => setShowForm(!showForm)} variant="secondary">
          {showForm ? 'Cancel' : '+ New Saved Search'}
        </GlassButton>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="glass glass-noise rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">Create New Saved Search</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Query
              </label>
              <input
                type="text"
                value={formData.query}
                onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Source Type
              </label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              >
                <option value="">All</option>
                <option value="github">GitHub</option>
                <option value="stackexchange">Stack Exchange</option>
                <option value="rss">RSS</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Primary Language
              </label>
              <input
                type="text"
                value={formData.primary_language}
                onChange={(e) => setFormData({ ...formData, primary_language: e.target.value })}
                placeholder="e.g., Python, JavaScript"
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Framework
              </label>
              <input
                type="text"
                value={formData.framework}
                onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
                placeholder="e.g., React, Django"
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="tag1, tag2, tag3"
                className="w-full px-4 py-3 glass rounded-xl border border-white/20 text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-400/50"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <GlassButton type="submit">
              Create Saved Search
            </GlassButton>
          </div>
        </form>
      )}

      {searches.length === 0 ? (
        <div className="glass glass-noise rounded-2xl p-12 text-center">
          <p className="text-slate-600 text-lg">No saved searches yet. Create one to get started!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {searches.map((search) => (
            <div key={search.id} className="glass glass-noise rounded-2xl p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold text-slate-800">{search.name}</h2>
                <span className="text-sm text-slate-600 font-medium">
                  {search.match_count} matches
                </span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                {search.query && (
                  <div>
                    <span className="font-medium text-slate-700">Query:</span>
                    <span className="ml-2 text-slate-600">{search.query}</span>
                  </div>
                )}
                {search.source_type && (
                  <div>
                    <span className="font-medium text-slate-700">Source:</span>
                    <span className="ml-2 text-slate-600">{search.source_type}</span>
                  </div>
                )}
                {search.primary_language && (
                  <div>
                    <span className="font-medium text-slate-700">Language:</span>
                    <span className="ml-2 text-slate-600">{search.primary_language}</span>
                  </div>
                )}
                {search.framework && (
                  <div>
                    <span className="font-medium text-slate-700">Framework:</span>
                    <span className="ml-2 text-slate-600">{search.framework}</span>
                  </div>
                )}
              </div>

              {search.tags.length > 0 && (
                <div className="mt-4">
                  <div className="flex flex-wrap gap-2">
                    {search.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-slate-100/50 text-slate-700 text-xs font-medium rounded-lg border border-slate-200/50"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 text-xs text-slate-500">
                Created: {new Date(search.created_at).toLocaleString()}
                {search.last_run_at && (
                  <> | Last run: {new Date(search.last_run_at).toLocaleString()}</>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
