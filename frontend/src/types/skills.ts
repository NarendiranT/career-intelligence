export type SkillItem = {
  name: string
  proficiency: number
}

export type SkillCategory = {
  name: string
  skills: SkillItem[]
}

export type SkillActivity = {
  kind: string
  label: string
  detail: string
  created_at: string | null
}

export type SkillsSummary = {
  resume_count: number
  total_skills: number
  skill_summary: string
  insights: string[]
  categories: SkillCategory[]
  recent_activity: SkillActivity[]
}

export const PROFICIENCY_LEGEND = [
  { stars: 5, label: 'Expert' },
  { stars: 4, label: 'Advanced' },
  { stars: 3, label: 'Intermediate' },
  { stars: 2, label: 'Beginner' },
  { stars: 1, label: 'Familiar' },
] as const
