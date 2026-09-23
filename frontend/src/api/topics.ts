import { apiFetch } from './client'
import type { InterviewTopic } from '@/types/interview'

export function listTopics(): Promise<InterviewTopic[]> {
  return apiFetch<InterviewTopic[]>('/v1/topics')
}
