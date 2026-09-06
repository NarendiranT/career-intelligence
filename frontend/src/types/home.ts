import type { ApiDocument } from './document'

export type { DocumentStatus } from './document'

export type HomeDocument = ApiDocument

export type HomeConversation = {
  id: string
  title: string
  updated_at: string | null
  bookmarked?: boolean
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
  saved_results: HomeConversation[]
}
