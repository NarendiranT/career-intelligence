import { apiFetch } from './client'
import type { HomeSummary } from '@/types/home'

export function fetchHomeSummary(): Promise<HomeSummary> {
  return apiFetch<HomeSummary>('/v1/home')
}
