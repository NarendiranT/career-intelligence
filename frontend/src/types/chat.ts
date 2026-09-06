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
  validated?: boolean
  topics?: ChatTopic[]
}

export type ChatAskPayload = {
  question: string
  resume_id?: string | null
  job_ids?: string[]
  conversation_id?: string | null
  stream?: boolean
  temperature?: number
  top_p?: number
  max_tokens?: number
  system_prompt?: string
  model?: string
  channel?: 'assistant' | 'interview' | 'extract_topics'
  topic_id?: string | null
  source_conversation_id?: string | null
  source_message_id?: string | null
}

export type ChatTopic = {
  id: string
  label: string
  slug?: string
  conversation_id?: string | null
  question_count?: number
}

export type ChatTable = {
  headers: string[]
  rows: string[][]
}

export type ChatCode = {
  language: string
  content: string
}

export type ChatDoneEvent = {
  type: 'chat.done'
  conversation_id: string | null
  text: string
  citations: ChatSource[]
  strengths: string[]
  gaps: string[]
  usage?: ChatUsage
  channel?: string
  topic_id?: string | null
  topics?: ChatTopic[]
  table?: ChatTable | null
  code?: ChatCode | null
  validated?: boolean
  message_id?: string | null
  topics_existing?: boolean
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
  bookmarked?: boolean
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
    table?: ChatTable
    code?: ChatCode
    validated?: boolean
    topics?: ChatTopic[]
  } | null
  created_at: string | null
}

export type ConversationDetail = ConversationSummary & {
  resume_id?: string | null
  job_ids?: string[]
  messages: ConversationMessage[]
}
