import { Shield } from 'lucide-react'

export function Footer() {
  return (
    <footer className="shrink-0 border-t border-border-default bg-bg-secondary/50">
      <div className="px-4 md:px-6 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-text-muted">
          <Shield className="w-3.5 h-3.5 text-brand-500" />
          <span className="text-xs">&copy; 2026 CodeGuard AI</span>
        </div>
        <span className="text-[11px] text-text-muted">v1.0.0</span>
      </div>
    </footer>
  )
}