export function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`h-4 rounded bg-bg-tertiary animate-shimmer ${className}`} />
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="glass-card p-5 space-y-3">
      <SkeletonLine className="w-2/3" />
      {Array.from({ length: lines - 1 }).map((_, i) => (
        <SkeletonLine key={i} className={i === lines - 2 ? 'w-1/2' : 'w-full'} />
      ))}
    </div>
  )
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="glass-card overflow-hidden">
      <div className="border-b border-border-default px-5 py-3 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonLine key={i} className="flex-1 h-3" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="border-b border-border-default/50 px-5 py-3 flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <SkeletonLine key={c} className="flex-1 h-3" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonStatCard() {
  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-lg bg-bg-tertiary animate-shimmer" />
        <SkeletonLine className="w-10 h-4" />
      </div>
      <SkeletonLine className="w-16 h-7 mb-1" />
      <SkeletonLine className="w-24 h-3" />
    </div>
  )
}