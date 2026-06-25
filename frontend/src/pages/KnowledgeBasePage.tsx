import { useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import { useKBArticles, useKBArticle, useKBCategories } from '../hooks/useKnowledgeBase'
import {
  BookOpen, Search, ChevronRight, ArrowLeft, Code, ShieldCheck,
  Eye, ExternalLink, Shield, X
} from 'lucide-react'

/* ─── Severity color mapping for category badges ─── */
const CATEGORY_COLORS: Record<string, { bar: string; badge: string; text: string }> = {
  injection: { bar: 'border-l-red-500', badge: 'badge-critical', text: 'text-red-400' },
  xss: { bar: 'border-l-orange-500', badge: 'badge-high', text: 'text-orange-400' },
  auth: { bar: 'border-l-accent-500', badge: 'badge-medium', text: 'text-accent-400' },
  crypto: { bar: 'border-l-brand-400', badge: 'badge-low', text: 'text-brand-400' },
  config: { bar: 'border-l-yellow-500', badge: 'badge-medium', text: 'text-yellow-400' },
  general: { bar: 'border-l-text-muted', badge: 'badge-info', text: 'text-text-muted' },
}

function getCategoryStyle(category: string) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.general
}

/* ═══════════════════════════════════════════════════════
   Main Knowledge Base Page — Split Panel Layout
   ═══════════════════════════════════════════════════════ */

export function KnowledgeBasePage() {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<string | undefined>(undefined)

  return (
    <div className="h-[calc(100vh-var(--spacing-header))] flex animate-fade-in">
      {/* ─── Left Panel (1/3) — Article List ─── */}
      <aside className="w-[380px] shrink-0 border-r border-border-default flex flex-col bg-surface-lowest/50">
        {/* Search & Filter */}
        <div className="p-4 border-b border-border-default space-y-3">
          <h1 className="text-headline-sm font-semibold text-text-primary flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" />
            Knowledge Base
          </h1>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search articles..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-glow pl-10 w-full text-body-sm rounded-lg py-2"
            />
          </div>
          <CategoryFilter selected={category} onSelect={setCategory} />
        </div>

        {/* Scrollable Article Cards */}
        <div className="flex-1 overflow-y-auto">
          <ArticleList
            search={search}
            category={category}
            selectedSlug={selectedSlug}
            onSelect={setSelectedSlug}
          />
        </div>
      </aside>

      {/* ─── Right Panel (2/3) — Content ─── */}
      <main className="flex-1 overflow-y-auto">
        {selectedSlug ? (
          <ArticleDetail slug={selectedSlug} onBack={() => setSelectedSlug(null)} />
        ) : (
          <EmptyState />
        )}
      </main>
    </div>
  )
}

/* ─── Category Filter ─── */

function CategoryFilter({ selected, onSelect }: { selected: string | undefined; onSelect: (c: string | undefined) => void }) {
  const { data: categories } = useKBCategories()
  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        onClick={() => onSelect(undefined)}
        className={`px-2.5 py-1 rounded-md text-label-sm transition-all ${
          !selected
            ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
            : 'bg-surface-high text-text-muted hover:text-text-secondary border border-transparent'
        }`}
      >
        All
      </button>
      {categories?.map(cat => {
        const style = getCategoryStyle(cat)
        return (
          <button
            key={cat}
            onClick={() => onSelect(selected === cat ? undefined : cat)}
            className={`px-2.5 py-1 rounded-md text-label-sm transition-all ${
              selected === cat
                ? `${style.badge} border`
                : 'bg-surface-high text-text-muted hover:text-text-secondary border border-transparent'
            }`}
          >
            {cat}
          </button>
        )
      })}
    </div>
  )
}

/* ─── Article List with left color bar ─── */

function ArticleList({
  search,
  category,
  selectedSlug,
  onSelect,
}: {
  search: string
  category?: string
  selectedSlug: string | null
  onSelect: (slug: string) => void
}) {
  const { data, isLoading } = useKBArticles(category, search || undefined)

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <p className="text-label-sm text-text-muted">Loading articles...</p>
      </div>
    )
  }

  if (!data?.articles?.length) {
    return (
      <div className="p-6 text-center">
        <BookOpen className="w-8 h-8 text-text-muted mx-auto mb-2" />
        <p className="text-body-sm text-text-secondary">No articles found</p>
      </div>
    )
  }

  return (
    <div className="p-2 space-y-1">
      {data.articles.map(article => {
        const style = getCategoryStyle(article.category)
        const isSelected = selectedSlug === article.slug
        return (
          <button
            key={article.id}
            onClick={() => onSelect(article.slug)}
            className={`w-full text-left p-3 rounded-lg border-l-[3px] transition-all group relative ${
              isSelected
                ? `${style.bar} bg-surface-high/80 border-b border-r border-t border-border-default`
                : `${style.bar} hover:bg-surface-high/40 border-b border-r border-t border-transparent hover:border-border-default`
            }`}
          >
            <h3 className="text-body-sm font-semibold text-text-primary group-hover:text-brand-400 transition-colors line-clamp-2 mb-1.5">
              {article.title}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`${style.badge} px-1.5 py-0.5 rounded text-[10px] font-mono font-medium uppercase`}>
                {article.category}
              </span>
              {article.cwe_ids && (
                <span className="text-[10px] font-mono text-text-muted bg-surface-high px-1.5 py-0.5 rounded">
                  CWE-{article.cwe_ids}
                </span>
              )}
              {article.owasp_category && (
                <span className="text-[10px] font-mono text-accent-400 bg-accent-500/10 px-1.5 py-0.5 rounded">
                  OWASP
                </span>
              )}
              <span className="text-[10px] text-text-muted flex items-center gap-0.5 ml-auto">
                <Eye className="w-3 h-3" /> {article.view_count}
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}

/* ─── Empty State with animate-ping ─── */

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="relative inline-flex">
          <div className="absolute inset-0 rounded-full bg-brand-400/20 animate-ping" />
          <div className="relative w-16 h-16 rounded-full bg-surface-high flex items-center justify-center border border-border-default">
            <BookOpen className="w-7 h-7 text-brand-400" />
          </div>
        </div>
        <div>
          <h3 className="text-headline-sm font-semibold text-text-primary">Select an Article</h3>
          <p className="text-body-sm text-text-secondary mt-1">Choose an article from the list to read</p>
        </div>
      </div>
    </div>
  )
}

/* ─── Article Detail View ─── */

function ArticleDetail({ slug, onBack }: { slug: string; onBack: () => void }) {
  const { data: article, isLoading } = useKBArticle(slug)

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!article) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="glass-panel p-8 text-center">
          <p className="text-text-secondary">Article not found</p>
        </div>
      </div>
    )
  }

  const style = getCategoryStyle(article.category)

  return (
    <div className="animate-fade-in">
      {/* Breadcrumb */}
      <div className="sticky top-0 z-10 bg-surface-dim/80 backdrop-blur-xl border-b border-border-default px-6 py-3">
        <div className="flex items-center gap-2 text-label-sm">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-text-muted hover:text-brand-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Knowledge Base
          </button>
          <ChevronRight className="w-3 h-3 text-text-muted" />
          <span className="text-text-secondary">{article.category}</span>
          <ChevronRight className="w-3 h-3 text-text-muted" />
          <span className="text-text-primary truncate max-w-[300px]">{article.title}</span>
        </div>
      </div>

      <div className="flex">
        {/* Main Content */}
        <div className="flex-1 min-w-0 p-6 space-y-6">
          {/* Article Header */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`${style.badge} px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase`}>
                {article.category}
              </span>
              {article.owasp_category && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-accent-500/15 text-accent-400 border border-accent-500/20">
                  OWASP: {article.owasp_category}
                </span>
              )}
              {article.cwe_ids && (
                <a
                  href={`https://cwe.mitre.org/data/definitions/${article.cwe_ids}.html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-surface-high text-brand-400 hover:bg-brand-500/10 transition-colors"
                >
                  CWE-{article.cwe_ids}
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}
              <span className="text-[10px] text-text-muted flex items-center gap-0.5 ml-auto">
                <Eye className="w-3 h-3" /> {article.view_count} views
              </span>
            </div>
            <h1 className="text-display-lg font-bold text-text-primary tracking-tight">{article.title}</h1>
          </div>

          {/* Content — glass-panel sections */}
          <div className="glass-panel p-6 prose prose-invert max-w-none">
            <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{article.content_markdown}</ReactMarkdown>
          </div>

          {/* Vulnerable Code */}
          {article.vulnerable_example && (
            <div className="glass-panel overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border-default bg-severity-critical/5">
                <Code className="w-4 h-4 text-severity-critical" />
                <h3 className="text-label-md font-semibold text-severity-critical">Vulnerable Code</h3>
              </div>
              <pre className="p-4 overflow-x-auto text-code-block code-vulnerable">
                <code>{article.vulnerable_example}</code>
              </pre>
            </div>
          )}

          {/* Secure Code */}
          {article.safe_example && (
            <div className="glass-panel overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border-default bg-success/5">
                <ShieldCheck className="w-4 h-4 text-success" />
                <h3 className="text-label-md font-semibold text-success">Secure Code</h3>
              </div>
              <pre className="p-4 overflow-x-auto text-code-block code-secure">
                <code>{article.safe_example}</code>
              </pre>
            </div>
          )}
        </div>

        {/* Sidebar — Code Examples Quick Access */}
        {(article.vulnerable_example || article.safe_example) && (
          <aside className="w-[280px] shrink-0 border-l border-border-default p-4 space-y-4 hidden xl:block">
            <h3 className="text-label-md font-semibold text-text-secondary uppercase tracking-wider">Quick Reference</h3>

            {article.cwe_ids && (
              <div className="glass-panel p-3 space-y-1">
                <p className="text-label-sm text-text-muted">CWE ID</p>
                <a
                  href={`https://cwe.mitre.org/data/definitions/${article.cwe_ids}.html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-label-md text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1"
                >
                  CWE-{article.cwe_ids}
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}

            {article.owasp_category && (
              <div className="glass-panel p-3 space-y-1">
                <p className="text-label-sm text-text-muted">OWASP Category</p>
                <p className="text-label-md text-accent-400">{article.owasp_category}</p>
              </div>
            )}

            {article.vulnerable_example && (
              <div className="glass-panel p-3 space-y-2">
                <p className="text-label-sm text-text-muted flex items-center gap-1">
                  <Code className="w-3 h-3 text-severity-critical" /> Vulnerable Pattern
                </p>
                <pre className="text-[10px] font-mono text-severity-critical/80 overflow-x-auto bg-bg-primary rounded p-2 max-h-32 overflow-y-auto">
                  {article.vulnerable_example.slice(0, 200)}{article.vulnerable_example.length > 200 ? '...' : ''}
                </pre>
              </div>
            )}

            {article.safe_example && (
              <div className="glass-panel p-3 space-y-2">
                <p className="text-label-sm text-text-muted flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-success" /> Secure Pattern
                </p>
                <pre className="text-[10px] font-mono text-success/80 overflow-x-auto bg-bg-primary rounded p-2 max-h-32 overflow-y-auto">
                  {article.safe_example.slice(0, 200)}{article.safe_example.length > 200 ? '...' : ''}
                </pre>
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}