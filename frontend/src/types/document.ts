export type DocumentStatus = 'uploaded' | 'processing' | 'processed' | 'failed'

export type ApiDocument = {
  id: string
  filename: string
  doc_type: 'resume' | 'job' | null
  status: DocumentStatus
  mime: string | null
  size: number | null
  error_message: string | null
  created_at: string | null
}
