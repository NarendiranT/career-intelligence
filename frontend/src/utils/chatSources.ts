import type { ChatSource } from '@/types/chat'
import type { ApiDocument } from '@/types/document'

const RESUME_ALIASES = new Set(['resume', 'resume profile', 'cv'])
const JOB_ALIASES = new Set(['job', 'jd', 'job profile', 'job description'])
const CORNER_CITE_RE = /【[^】]*】/g
const SQUARE_FILE_RE = /\[[^[\]]+\.(?:pdf|docx?|txt)\]/gi

export type ChatSourceContext = {
  documents: ApiDocument[]
  resumeId?: string
  jobIds?: string[]
}

export function stripInlineCitations(text: string): string {
  return text
    .replace(CORNER_CITE_RE, '')
    .replace(SQUARE_FILE_RE, '')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/ +([,.;:])/g, '$1')
    .trim()
}

function basename(value: string): string {
  return value.split(/[/\\]/).pop()?.trim() || value.trim()
}

function aliasKey(value: string): string {
  return basename(value).toLowerCase()
}

export function sourceFileName(source: ChatSource, ctx: ChatSourceContext): string {
  const resolved = resolveSourceDocument(source, ctx)
  if (resolved) return basename(resolved.filename)
  const label = (source.label || source.id).trim()
  return basename(label) || label
}

export function resolveSourceDocument(source: ChatSource, ctx: ChatSourceContext): ApiDocument | null {
  const docs = ctx.documents
  const raw = source.id?.trim() || ''
  const byId = raw ? docs.find((doc) => doc.id === raw) : undefined
  if (byId) return byId

  const candidates = [source.label, source.id].map((value) => aliasKey(value || '')).filter(Boolean)
  for (const key of candidates) {
    const byName = docs.find((doc) => aliasKey(doc.filename) === key)
    if (byName) return byName
  }

  const key = candidates[0] || ''
  if (RESUME_ALIASES.has(key)) {
    return docs.find((doc) => doc.id === ctx.resumeId) || docs.find((doc) => doc.doc_type !== 'job') || null
  }
  if (JOB_ALIASES.has(key)) {
    const selected = (ctx.jobIds || []).map((id) => docs.find((doc) => doc.id === id)).filter(Boolean) as ApiDocument[]
    if (selected.length === 1) return selected[0]
    if (selected.length > 1) return selected[0]
    const jobs = docs.filter((doc) => doc.doc_type === 'job')
    return jobs[0] || null
  }
  return null
}
