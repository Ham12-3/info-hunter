'use client'

import './globals.css'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import dynamic from 'next/dynamic'

// Lazy load heavy components for better initial performance
const PageTransition = dynamic(() => import('@/components/PageTransition'), { 
  ssr: false,
  loading: () => null 
})
const KineticGlyphBackground = dynamic(() => import('@/components/KineticGlyphBackground'), { 
  ssr: false,
  loading: () => null 
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <html lang="en">
      <head>
        <title>Info Hunter - Programming Knowledge Search</title>
        <meta name="description" content="Search and discover programming knowledge and code snippets" />
      </head>
      <body className="min-h-screen relative">
        {/* Kinetic Glyph Background - lazy loaded and reduced density for performance */}
        <KineticGlyphBackground className="opacity-30 z-0" density={60} />
        
        <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/40 border-b border-white/20 relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-8">
                <Link href="/" className="flex items-center gap-2 px-2 py-2 group">
                  <svg className="w-6 h-6 text-primary-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                  <span className="text-xl font-bold text-slate-800">Info Hunter</span>
                </Link>
                <div className="hidden sm:flex sm:gap-1">
                  <Link
                    href="/"
                    className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all ${
                      pathname === '/'
                        ? 'text-primary-600 bg-white/40'
                        : 'text-slate-700 hover:text-primary-600 hover:bg-white/30'
                    }`}
                  >
                    Search
                  </Link>
                  <Link
                    href="/saved-searches"
                    className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all ${
                      pathname === '/saved-searches'
                        ? 'text-primary-600 bg-white/40'
                        : 'text-slate-600 hover:text-primary-600 hover:bg-white/30'
                    }`}
                  >
                    Saved Searches
                  </Link>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <button className="p-2 text-slate-600 hover:text-primary-600 hover:bg-white/30 rounded-lg transition-all">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
                <button className="p-2 text-slate-600 hover:text-primary-600 hover:bg-white/30 rounded-lg transition-all">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </nav>
        <main className="relative z-10">
          <PageTransition>{children}</PageTransition>
        </main>
      </body>
    </html>
  )
}

