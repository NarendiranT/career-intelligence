export type DocumentStatus = 'uploaded' | 'processing' | 'processed' | 'failed'

export type HomeDocument = {
  id: string
  filename: string
  doc_type: 'resume' | 'job' | null
  status: DocumentStatus
  mime: string | null
  size: number | null
  error_message: string | null
  created_at: string | null
}

export type HomeConversation = {
  id: string
  title: string
  updated_at: string | null
}

export type HomeStats = {
  resume_count: number
  job_count: number
  insight_count: number
  saved_result_count: number
}

export type HomeSummary = {
  documents: HomeDocument[]
  stats: HomeStats
  conversations: HomeConversation[]
}
