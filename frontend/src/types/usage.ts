export type UsageRange = '7d' | '30d' | '90d'

export type UsageFeatureId = 'chat' | 'interview' | 'documents'

export type UsageFeature = {
  id: UsageFeatureId
  label: string
  tokens: number
  percent: number
  activity_count: number
}

export type UsageDaily = {
  date: string
  chat: number
  interview: number
  documents: number
}

export type UsageActivity = {
  id: string
  created_at: string
  feature: UsageFeatureId
  tokens: number
  details: string
}

export type UsageByEvent = {
  event_type: string
  tokens: number
  count: number
}

export type UsageActivities = {
  start: string
  end: string
  activities: UsageActivity[]
}

export type UsageSummary = {
  range: UsageRange
  days: number
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  event_count: number
  range_tokens: number
  previous_range_tokens: number
  delta_percent: number
  by_event_type: UsageByEvent[]
  features: UsageFeature[]
  daily: UsageDaily[]
  recent: UsageActivity[]
}
