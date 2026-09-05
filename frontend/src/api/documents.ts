import { apiFetch } from './client'
import { readToken } from './token'
import type { ApiDocument } from '@/types/document'

function apiBase(): string {
  return String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

export function listDocuments(): Promise<ApiDocument[]> {
  return apiFetch<ApiDocument[]>('/v1/documents')
}

export function uploadDocument(file: File, docType: 'resume' | 'job'): Promise<ApiDocument> {
  const body = new FormData()
  body.append('file', file)
  body.append('doc_type', docType)
  return apiFetch<ApiDocument>('/v1/documents', {
    method: 'POST',
    body,
    timeoutMs: 120_000,
  })
}

export function deleteDocument(id: string): Promise<void> {
  return apiFetch<void>(`/v1/documents/${id}`, { method: 'DELETE' })
}

export async function fetchDocumentFile(id: string): Promise<{ blob: Blob; filename: string; mime: string }> {
  const token = readToken()
  const headers = new Headers()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${apiBase()}/v1/documents/${id}/file`, { headers })
  if (!response.ok) {
    throw new Error(response.status === 404 ? 'Document file was not found.' : 'Could not open the document.')
  }
  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') || ''
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^\";]+)/i)
  const filename = match?.[1] ? decodeURIComponent(match[1].replace(/"/g, '')) : 'document'
  const mime = blob.type || response.headers.get('content-type') || 'application/octet-stream'
  return { blob, filename, mime }
}
