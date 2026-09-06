import { apiFetch } from './client'
import type { UsageActivities, UsageRange, UsageSummary } from '@/types/usage'

export function fetchUsageSummary(range: UsageRange = '30d'): Promise<UsageSummary> {
  return apiFetch<UsageSummary>(`/v1/usage?range=${range}`)
}

export function fetchUsageActivities(start: string, end: string): Promise<UsageActivities> {
  const params = new URLSearchParams({ start, end })
  return apiFetch<UsageActivities>(`/v1/usage/activities?${params}`)
}
