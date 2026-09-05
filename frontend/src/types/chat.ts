export type ChatRole = 'user' | 'assistant'

export type ChatSource = {
  id: string
  label: string
}

export type ChatUsage = {
  tokens: number
  prompt_tokens: number
  completion_tokens: number
}

export type ChatFeedback = 'up' | 'down'

export type ChatMessage = {
  id: string
  role: ChatRole
  time: string
  text: string
  pending?: boolean
  strengths?: string[]
  gaps?: string[]
  sources?: ChatSource[]
  usage?: ChatUsage
}

export type ChatAskPayload = {
  question: string
  resume_id: string | null
  job_ids: string[]
  conversation_id: string | null
  stream: boolean
  temperature: number
  top_p: number
  max_tokens: number
  system_prompt: string
  web_search: boolean
  model: string
}

export type ChatDoneEvent = {
  type: 'chat.done'
  conversation_id: string | null
  text: string
  citations: ChatSource[]
  strengths: string[]
  gaps: string[]
  usage?: ChatUsage
}

export type ChatSocketEvent =
  | { type: 'chat.status'; status: string }
  | { type: 'chat.token'; text: string }
  | { type: 'chat.error'; detail: string }
  | ChatDoneEvent

export type ConversationSummary = {
  id: string
  title: string
  updated_at: string | null
}

export type ConversationMessage = {
  id: string
  role: ChatRole
  content: string
  citations: ChatSource[]
  extra: {
    strengths?: string[]
    gaps?: string[]
    usage?: ChatUsage
  } | null
  created_at: string | null
}

export type ConversationDetail = ConversationSummary & {
  resume_id?: string | null
  job_ids?: string[]
  messages: ConversationMessage[]
}
