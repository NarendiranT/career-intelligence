export type InterviewMode = 'practice' | 'mock'
export type ResponseStyle = 'detailed' | 'concise' | 'socratic'
export type Difficulty = 'easy' | 'medium' | 'hard'

export type InterviewTopic = {
  id: string
  label: string
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
  table?: InterviewTable
  code?: InterviewCodeBlock
}

export const interviewTopics: InterviewTopic[] = [
  { id: 'python', label: 'Python' },
  { id: 'fastapi', label: 'FastAPI' },
  { id: 'django', label: 'Django' },
  { id: 'sql', label: 'SQL' },
  { id: 'aws', label: 'AWS' },
  { id: 'genai', label: 'Generative AI / LLMs' },
  { id: 'rag', label: 'RAG' },
  { id: 'langchain', label: 'LangChain & LangGraph' },
  { id: 'system-design', label: 'System Design' },
  { id: 'dsa', label: 'Data Structures & Algorithms' },
  { id: 'patterns', label: 'Design Patterns' },
  { id: 'devops', label: 'Docker & DevOps' },
  { id: 'behavioral', label: 'Behavioral Questions' },
]
