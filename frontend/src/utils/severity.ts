/**
 * Shared severity constants and utilities.
 * Single source of truth for severity color mappings, badge classes, and language detection.
 */

// Tailwind text-color classes for severity levels
export const SEVERITY_COLORS: Record<string, string> = {
  critical: 'text-severity-critical',
  high: 'text-severity-high',
  medium: 'text-severity-medium',
  low: 'text-brand-400',
  info: 'text-text-muted',
}

// Tailwind bg-color classes for severity bars/charts
export const SEVERITY_BG_COLORS: Record<string, string> = {
  critical: 'bg-severity-critical',
  high: 'bg-severity-high',
  medium: 'bg-severity-medium',
  low: 'bg-brand-400',
  info: 'bg-text-muted',
}

// CSS badge class names for severity levels
export const SEVERITY_BADGE_CLASSES: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
}

// Hex colors for chart rendering
export const SEVERITY_HEX_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
}

const LANGUAGE_MAP: Record<string, string> = {
  py: 'python',
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  java: 'java',
  go: 'go',
  rs: 'rust',
  c: 'c',
  cpp: 'cpp',
  h: 'c',
  swift: 'swift',
}

export function getLanguageFromFilename(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  return LANGUAGE_MAP[ext] || 'plaintext'
}