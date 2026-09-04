export type UploadedDoc = {
  id: string
  name: string
  sizeLabel: string
  uploadedLabel: string
  status: 'uploaded'
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${Math.round(kb)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

export const MAX_FILE_BYTES = 10 * 1024 * 1024
export const ACCEPTED_TYPES = '.pdf,.doc,.docx,.txt'
export const ACCEPTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt']

export function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext)) && file.size <= MAX_FILE_BYTES
}

export function toUploadedDoc(file: File): UploadedDoc {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
    name: file.name,
    sizeLabel: formatBytes(file.size),
    uploadedLabel: 'Uploaded just now',
    status: 'uploaded',
  }
}
