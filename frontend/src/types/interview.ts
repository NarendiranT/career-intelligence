export type InterviewMode = 'practice' | 'mock'
export type ResponseStyle = 'detailed' | 'concise' | 'socratic'
export type Difficulty = 'easy' | 'medium' | 'hard'

export type InterviewTopic = {
  id: string
  label: string
  slug?: string
  conversation_id?: string | null
  created_at?: string | null
  question_count?: number
}

export type InterviewTopicDetail = InterviewTopic & {
  context?: Record<string, unknown> | null
  resume_id?: string | null
  job_ids?: string[]
}

export type InterviewTable = {
  headers: string[]
  rows: string[][]
}

export type InterviewCodeBlock = {
  language: string
  content: string
}

export type InterviewMessage = {
  id: string
  role: 'user' | 'assistant'
  time: string
  text: string
  pending?: boolean
  table?: InterviewTable
  code?: InterviewCodeBlock
}

export function interviewSystemPrompt(options: {
  topicLabel: string
  mode: InterviewMode
  responseStyle: ResponseStyle
  difficulty: Difficulty
  includeCode: boolean
  followUps: boolean
  bestPractices: boolean
}): string {
  const role = options.mode === 'mock' ? 'mock interviewer' : 'practice coach'
  const style =
    options.responseStyle === 'concise'
      ? 'concise'
      : options.responseStyle === 'socratic'
        ? 'socratic (hints first)'
        : 'detailed'
  const lines = [
    `You are a ${role} for "${options.topicLabel}" at ${options.difficulty} difficulty.`,
    `Response style: ${style}.`,
    options.includeCode ? 'Include short code examples when they help.' : 'Do not include code.',
    options.followUps
      ? 'End with 1–2 follow-up interview questions.'
      : 'No follow-up questions.',
    options.bestPractices
      ? 'Call out one interviewer best practice.'
      : 'Skip best practices.',
    'Stay on this topic. Use the candidate resume/job context when it is present.',
  ]
  return lines.join('\n')
}

export function temperatureForDifficulty(difficulty: Difficulty): number {
  if (difficulty === 'easy') return 0.4
  if (difficulty === 'hard') return 0.9
  return 0.7
}

export function formatQuestionCount(count: number | undefined): string {
  const n = Math.max(0, Math.floor(Number(count) || 0))
  return n > 99 ? '99+' : String(n)
}

export function questionCountLabel(count: number | undefined): string {
  const n = Math.max(0, Math.floor(Number(count) || 0))
  if (n > 99) return 'More than 99 questions practiced'
  if (n === 1) return '1 question practiced'
  return `${n} questions practiced`
}
