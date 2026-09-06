export type RichTable = {
  headers: string[]
  rows: string[][]
}

export type RichCode = {
  language: string
  content: string
}

export type InlineSegment =
  | { type: 'text'; value: string }
  | { type: 'bold'; value: string }
  | { type: 'italic'; value: string }
  | { type: 'code'; value: string }

export type RichBlock =
  | { type: 'heading'; level: 1 | 2 | 3; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'list'; ordered: boolean; items: string[] }
  | { type: 'table'; headers: string[]; rows: string[][] }
  | { type: 'code'; language: string; content: string }
  | { type: 'quote'; text: string }

const INLINE_RE = /(`[^`]+`)|(\*\*[^*]+\*\*)|(__[^_]+__)|(\*[^*]+\*)|(_[^_]+_)/

export function parseInline(text: string): InlineSegment[] {
  const segments: InlineSegment[] = []
  let rest = text
  while (rest) {
    const match = INLINE_RE.exec(rest)
    if (!match || match.index === undefined) {
      segments.push({ type: 'text', value: rest })
      break
    }
    if (match.index > 0) {
      segments.push({ type: 'text', value: rest.slice(0, match.index) })
    }
    const token = match[0]
    if (token.startsWith('`')) {
      segments.push({ type: 'code', value: token.slice(1, -1) })
    } else if (token.startsWith('**') || token.startsWith('__')) {
      segments.push({ type: 'bold', value: token.slice(2, -2) })
    } else {
      segments.push({ type: 'italic', value: token.slice(1, -1) })
    }
    rest = rest.slice(match.index + token.length)
  }
  return segments
}

function isFence(line: string): { language: string } | null {
  const match = line.trim().match(/^(`{3,}|~{3,})(\w+)?\s*$/)
  if (!match) return null
  return { language: match[2] || 'text' }
}

function isTableSeparator(line: string): boolean {
  const trimmed = line.trim()
  if (!trimmed.includes('-')) return false
  const cells = splitRow(trimmed)
  return cells.length >= 2 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.replace(/\s/g, '')))
}

function looksLikeTableRow(line: string): boolean {
  const trimmed = line.trim()
  if (!trimmed.includes('|')) return false
  return splitRow(trimmed).length >= 2
}

function splitRow(line: string): string[] {
  let value = line.trim()
  if (value.startsWith('|')) value = value.slice(1)
  if (value.endsWith('|')) value = value.slice(0, -1)
  return value.split('|').map((cell) => cell.trim())
}

function heading(line: string): { level: 1 | 2 | 3; text: string } | null {
  const match = line.trim().match(/^(#{1,3})\s+(.+)$/)
  if (!match) return null
  return { level: match[1].length as 1 | 2 | 3, text: match[2].trim() }
}

function listItem(line: string): { ordered: boolean; text: string } | null {
  const bullet = line.match(/^\s*[-*+]\s+(.+)$/)
  if (bullet) return { ordered: false, text: bullet[1] }
  const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/)
  if (numbered) return { ordered: true, text: numbered[1] }
  return null
}

function quoteLine(line: string): string | null {
  const match = line.match(/^\s*>\s?(.*)$/)
  return match ? match[1] : null
}

function pushParagraph(blocks: RichBlock[], lines: string[]): void {
  const text = lines.join('\n').trim()
  if (text) blocks.push({ type: 'paragraph', text })
}

export function parseRichText(text: string, options?: { allowUnclosedFence?: boolean }): RichBlock[] {
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const blocks: RichBlock[] = []
  let i = 0
  let paragraph: string[] = []

  const flushParagraph = () => {
    pushParagraph(blocks, paragraph)
    paragraph = []
  }

  while (i < lines.length) {
    const line = lines[i]
    const fence = isFence(line)
    if (fence) {
      flushParagraph()
      const body: string[] = []
      i += 1
      while (i < lines.length && !isFence(lines[i])) {
        body.push(lines[i])
        i += 1
      }
      if (i < lines.length) i += 1
      else if (!options?.allowUnclosedFence && !body.length) {
        paragraph.push(line)
        continue
      }
      blocks.push({ type: 'code', language: fence.language, content: body.join('\n') })
      continue
    }

    if (looksLikeTableRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      flushParagraph()
      const headers = splitRow(line)
      i += 2
      const rows: string[][] = []
      while (i < lines.length && looksLikeTableRow(lines[i]) && !isTableSeparator(lines[i])) {
        const cells = splitRow(lines[i])
        while (cells.length < headers.length) cells.push('')
        rows.push(cells.slice(0, Math.max(headers.length, cells.length)))
        i += 1
      }
      blocks.push({ type: 'table', headers, rows })
      continue
    }

    const title = heading(line)
    if (title) {
      flushParagraph()
      blocks.push({ type: 'heading', ...title })
      i += 1
      continue
    }

    const quoted = quoteLine(line)
    if (quoted !== null) {
      flushParagraph()
      const parts = [quoted]
      i += 1
      while (i < lines.length) {
        const next = quoteLine(lines[i])
        if (next === null) break
        parts.push(next)
        i += 1
      }
      const quote = parts.join('\n').trim()
      if (quote) blocks.push({ type: 'quote', text: quote })
      continue
    }

    const item = listItem(line)
    if (item) {
      flushParagraph()
      const items = [item.text]
      const ordered = item.ordered
      i += 1
      while (i < lines.length) {
        const next = listItem(lines[i])
        if (!next || next.ordered !== ordered) break
        items.push(next.text)
        i += 1
      }
      blocks.push({ type: 'list', ordered, items })
      continue
    }

    if (!line.trim()) {
      flushParagraph()
      i += 1
      continue
    }

    paragraph.push(line)
    i += 1
  }

  flushParagraph()
  return blocks
}

export function normalizeTable(raw: unknown): RichTable | undefined {
  if (!raw || typeof raw !== 'object') return undefined
  const value = raw as { headers?: unknown; rows?: unknown }
  const headers = Array.isArray(value.headers) ? value.headers.map((cell) => String(cell)) : []
  const rows = Array.isArray(value.rows)
    ? value.rows.map((row) => (Array.isArray(row) ? row.map((cell) => String(cell)) : [String(row)]))
    : []
  if (!headers.length && !rows.length) return undefined
  return { headers, rows }
}

export function normalizeCode(raw: unknown): RichCode | undefined {
  if (!raw || typeof raw !== 'object') return undefined
  const value = raw as { language?: unknown; content?: unknown }
  const content = String(value.content ?? '')
  if (!content.trim()) return undefined
  return { language: String(value.language ?? 'text') || 'text', content }
}

export function mergeRichBlocks(
  text: string,
  extras?: { table?: unknown; code?: unknown; pending?: boolean },
): RichBlock[] {
  const blocks = parseRichText(text, { allowUnclosedFence: Boolean(extras?.pending) })
  const hasTable = blocks.some((block) => block.type === 'table')
  const hasCode = blocks.some((block) => block.type === 'code')
  const table = normalizeTable(extras?.table)
  const code = normalizeCode(extras?.code)
  if (table && !hasTable) blocks.push({ type: 'table', ...table })
  if (code && !hasCode) blocks.push({ type: 'code', ...code })
  return blocks
}
