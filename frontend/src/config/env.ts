export function isDowntime(): boolean {
  const raw = String(import.meta.env.VITE_DOWNTIME ?? '').trim().toLowerCase()
  return raw === 'true' || raw === '1' || raw === 'yes' || raw === 'on'
}
