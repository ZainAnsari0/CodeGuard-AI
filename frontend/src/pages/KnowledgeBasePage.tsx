import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import { useKBArticles, useKBArticle, useKBCategories } from '../hooks/useKnowledgeBase'
import { BookOpen, Search, ChevronRight, ArrowLeft, Code, ShieldCheck } from 'lucide-react'

export function KnowledgeBasePage() {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<string | undefined>(undefined)

  if (selectedSlug) {
    return <ArticleDetail slug={selectedSlug} onBack={() => setSelectedSlug(null)} />
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <BookOpen className="w-6 h-6" /> Knowledge Base
        </h1>
        <p className="text-text-secondary mt-1">Learn about security vulnerabilities and best practices</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text" placeholder="Search articles..." value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10 w-full"
          />
        </div>
        <CategoryFilter selected={category} onSelect={setCategory} />
      </div>

      <ArticleList search={search} category={category} onSelect={setSelectedSlug} />
    </div>
  )
}

function CategoryFilter({ selected, onSelect }: { selected: string | undefined; onSelect: (c: string | undefined) => void }) {
  const { data: categories } = useKBCategories()
  return (
    <select value={selected || ''} onChange={e => onSelect(e.target.value || undefined)} className="input-field w-auto">
      <option value="">All Categories</option>
      {categories?.map(cat => <option key={cat} value={cat}>{cat}</option>)}
    </select>
  )
}

function ArticleList({ search, category, onSelect }: { search: string; category?: string; onSelect: (slug: string) => void }) {
  const { data, isLoading } = useKBArticles(category, search || undefined)

  if (isLoading) return <div className="glass-card p-8 text-center text-text-secondary">Loading articles...</div>
  if (!data?.articles?.length) return <div className="glass-card p-8 text-center text-text-secondary">No articles found</div>

  const categoryColors: Record<string, string> = {
    injection: 'bg-red-500/20 text-red-400',
    xss: 'bg-orange-500/20 text-orange-400',
    auth: 'bg-purple-500/20 text-purple-400',
    crypto: 'bg-blue-500/20 text-blue-400',
    config: 'bg-yellow-500/20 text-yellow-400',
    general: 'bg-surface-3 text-text-muted',
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {data.articles.map(article => (
        <div
          key={article.id}
          className="glass-card p-5 hover:border-primary/40 transition-colors cursor-pointer group"
          onClick={() => onSelect(article.slug)}
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors line-clamp-2">{article.title}</h3>
            <ChevronRight className="w-4 h-4 text-text-muted shrink-0 mt-1" />
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span className={`px-2 py-0.5 rounded ${categoryColors[article.category] || categoryColors.general}`}>{article.category}</span>
            {article.cwe_ids && <span>CWE-{article.cwe_ids}</span>}
            <span>{article.view_count} views</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function ArticleDetail({ slug, onBack }: { slug: string; onBack: () => void }) {
  const { data: article, isLoading } = useKBArticle(slug)

  if (isLoading) return <div className="glass-card p-8 text-center text-text-secondary">Loading article...</div>
  if (!article) return <div className="glass-card p-8 text-center text-text-secondary">Article not found</div>

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <button onClick={onBack} className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Knowledge Base
      </button>

      <div>
        <h1 className="text-2xl font-bold text-text-primary">{article.title}</h1>
        <div className="flex items-center gap-3 mt-2 text-sm text-text-muted">
          <span>{article.category}</span>
          {article.cwe_ids && <span>CWE-{article.cwe_ids}</span>}
          {article.owasp_category && <span>{article.owasp_category}</span>}
          <span>{article.view_count} views</span>
        </div>
      </div>

      <div className="glass-card p-6 prose prose-invert max-w-none">
        <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{article.content_markdown}</ReactMarkdown>
      </div>

      {article.vulnerable_example && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-red-400 mb-3 flex items-center gap-2">
            <Code className="w-5 h-5" /> Vulnerable Code
          </h3>
          <pre className="bg-surface-1 p-4 rounded-lg overflow-x-auto text-sm text-red-300">
            <code>{article.vulnerable_example}</code>
          </pre>
        </div>
      )}

      {article.safe_example && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-green-400 mb-3 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5" /> Secure Code
          </h3>
          <pre className="bg-surface-1 p-4 rounded-lg overflow-x-auto text-sm text-green-300">
            <code>{article.safe_example}</code>
          </pre>
        </div>
      )}
    </div>
  )
}