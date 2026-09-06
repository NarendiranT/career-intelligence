import { apiFetch } from './client'
import type { SkillsSummary } from '@/types/skills'

export function fetchSkillsSummary(): Promise<SkillsSummary> {
  return apiFetch<SkillsSummary>('/v1/skills')
}
