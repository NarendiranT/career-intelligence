import { apiFetch } from './client'
import type { ApiDocument } from '@/types/document'

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
