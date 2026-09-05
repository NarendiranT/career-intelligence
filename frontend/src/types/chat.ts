export type ChatRole = 'user' | 'assistant'

export type ChatSource = {
  id: string
  label: string
}

export type ChatMessage = {
  id: string
  role: ChatRole
  time: string
  text: string
  strengths?: string[]
  gaps?: string[]
  sources?: ChatSource[]
}

export type LibraryDoc = {
  id: string
  name: string
  kind: 'resume' | 'job'
  sizeLabel: string
  status: 'processed'
}

export const documentLibrary: LibraryDoc[] = [
  { id: 'resume-1', name: 'John_Doe_Resume.pdf', kind: 'resume', sizeLabel: '245 KB', status: 'processed' },
  { id: 'resume-2', name: 'software-engineer-resume.pdf', kind: 'resume', sizeLabel: '198 KB', status: 'processed' },
  { id: 'job-1', name: 'Senior AI Engineer - Acme Corp.pdf', kind: 'job', sizeLabel: '312 KB', status: 'processed' },
  { id: 'job-2', name: 'ML Engineer - TechCo.pdf', kind: 'job', sizeLabel: '428 KB', status: 'processed' },
  { id: 'job-3', name: 'GenAI Platform Engineer - InnovateAI.pdf', kind: 'job', sizeLabel: '276 KB', status: 'processed' },
]
