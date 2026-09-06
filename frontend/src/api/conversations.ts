import { apiFetch } from './client'
import type { ConversationDetail, ConversationSummary } from '@/types/chat'

export function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>('/v1/conversations')
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/v1/conversations/${id}`)
}

export function bookmarkConversation(id: string, bookmarked: boolean): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`/v1/conversations/${id}`, {
    method: 'PATCH',
    json: { bookmarked },
  })
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch<void>(`/v1/conversations/${id}`, { method: 'DELETE' })
}

export function clearConversationMessages(id: string): Promise<void> {
  return apiFetch<void>(`/v1/conversations/${id}/messages`, { method: 'DELETE' })
}
