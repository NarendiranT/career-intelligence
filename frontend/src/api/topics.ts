import { apiFetch } from './client'
import type { InterviewTopic, InterviewTopicDetail } from '@/types/interview'

export function listTopics(): Promise<InterviewTopic[]> {
  return apiFetch<InterviewTopic[]>('/v1/topics')
}

export function getTopic(id: string): Promise<InterviewTopicDetail> {
  return apiFetch<InterviewTopicDetail>(`/v1/topics/${id}`)
}

export function deleteTopic(id: string): Promise<void> {
  return apiFetch<void>(`/v1/topics/${id}`, { method: 'DELETE' })
}
