import { apiFetch } from './client'
import type { ConversationDetail, ConversationSummary } from '@/types/chat'

export function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>('/v1/conversations')
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/v1/conversations/${id}`)
}
